"""Local server for All In Capital triage. Run: python3 app/httpd.py  (then open http://127.0.0.1:8331)"""
import hmac
import json
import os
import socket
import threading
import time
import traceback
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import checks

checks.load_env()  # before store is imported: it picks files or Supabase from DATABASE_URL

import auth  # noqa: E402
import case  # noqa: E402
import read  # noqa: E402
import thesis  # noqa: E402
import evalpoints  # noqa: E402
import corrections  # noqa: E402
import outreach  # noqa: E402
import portfolio  # noqa: E402
from store import STORE  # noqa: E402

WEB = Path(__file__).resolve().parent.parent / "public"
HOST, PORT = "127.0.0.1", int(os.environ.get("PORT") or 8331)  # loopback only: this app holds credentials
MAX_BODY = 40_000  # eval inputs carry a dummy deck and form
# DNS rebinding: every request must name this server in Host, and a browser Origin, when sent, must match.
ALLOWED_HOSTS = {"%s:%d" % (HOST, PORT), "localhost:%d" % PORT}
ALLOWED_ORIGINS = {"http://" + h for h in ALLOWED_HOSTS}
ON_VERCEL = bool(os.environ.get("VERCEL"))
OPEN_ROUTES = {"/api/login", "/api/logout", "/api/cron"}  # the timer brings CRON_SECRET instead of a cookie
# Who may call what; anything not listed is open to both signed-in roles.
ROLE_ONLY = {("POST", "/api/read"): "riya", ("POST", "/api/decision"): "riya", ("POST", "/api/batch"): "riya",
             ("POST", "/api/setup-check"): "riya", ("POST", "/api/thesis/approve"): "kushal", ("POST", "/api/eval"): "riya", ("POST", "/api/correction/reject"): "riya", ("POST", "/api/outreach/send"): "riya"}
BATCH = {"state": "idle", "done": 0, "total": 0, "current": None, "errors": []}
IDS = {a["id"] for a in case.applications()}
JOBS, JOBS_LOCK = {}, threading.Lock()  # id -> {"state": "running" | "error", "error": text}; finished reads live in STORE
MAX_REASON = 500


def background(work):
    if ON_VERCEL:
        work()
    else:
        threading.Thread(target=work, daemon=True).start()


def start_read(app_id):
    """Slow work runs in a thread the page polls; a second click while running starts nothing."""
    with JOBS_LOCK:
        if JOBS.get(app_id, {}).get("state") == "running":
            return False
        JOBS[app_id] = {"state": "running"}

    def work():
        try:
            save_read(read.run(app_id))
            with JOBS_LOCK:
                JOBS.pop(app_id, None)
        except Exception as e:  # the type and our own words only: never a key or a raw upstream body
            traceback.print_exc()
            msg = str(e) if isinstance(e, read.claude.ClaudeError) else "The read stopped (%s)." % type(e).__name__
            with JOBS_LOCK:
                JOBS[app_id] = {"state": "error", "error": msg + " Nothing was saved; run it again."}
    background(work)
    return True


def save_read(r):
    STORE.put("reads", r["id"], r)
    corrections.record_use(r.get("corrections_applied", []), r["id"])


def learn_from(decision, saved):
    """Feedback loop 1: a disagreement with a reason becomes a correction, in the background (one model call)."""
    def work():
        try:
            if not any(c["from"] == decision["id"] and c["reason"] == decision["reason"] for c in corrections.all_corrections()):
                corrections.create(decision, saved)
        except Exception:
            traceback.print_exc()  # the decision itself is already saved; a failed correction is logged, not lost silently
    background(work)


def draft_for(app_id, saved):
    """A final Go writes the email draft in the background (calendar read plus one model call)."""
    def work():
        try:
            existing = STORE.get("outreach", app_id)
            if existing and existing["status"] != "withdrawn":
                return
            app = next(a for a in case.applications() if a["id"] == app_id)
            outreach.create_draft(app, saved)
        except Exception:
            traceback.print_exc()
    background(work)


def agent_loop(every):
    """The scheduling agent runs on its own: one cycle for every open conversation, every `every` seconds."""
    while True:
        try:
            outreach.tick_all()
        except Exception:
            traceback.print_exc()
        time.sleep(every)


def start_batch():
    """Read the whole batch in one run, one application after another; a failure is recorded and the run moves on."""
    with JOBS_LOCK:
        if BATCH["state"] == "running":
            return False
        BATCH.update(state="running", done=0, total=len(IDS), current=None, errors=[])

    def work():
        spent0, cap, stop = read.claude.spent["usd"], float(os.environ.get("BATCH_COST_CAP_USD") or 5), None
        for a in case.applications():
            if stop is None and read.claude.spent["usd"] - spent0 >= cap:
                stop = "Not read: this batch reached its $%.2f cost cap. Read it on its own, or raise BATCH_COST_CAP_USD." % cap
            if stop:
                with JOBS_LOCK:
                    BATCH["errors"].append({"id": a["id"], "company": a["company"], "error": stop})
                    BATCH["done"] += 1
                continue
            with JOBS_LOCK:
                BATCH["current"] = a["company"]
                busy = JOBS.get(a["id"], {}).get("state") == "running"
                if not busy:
                    JOBS[a["id"]] = {"state": "running"}
            if not busy:
                try:
                    save_read(read.run(a["id"]))
                    with JOBS_LOCK:
                        JOBS.pop(a["id"], None)
                except Exception as e:
                    traceback.print_exc()
                    msg = str(e) if isinstance(e, read.claude.ClaudeError) else "The read stopped (%s)." % type(e).__name__
                    if getattr(e, "stops_batch", False):
                        stop = "Not read: " + msg
                    with JOBS_LOCK:
                        JOBS[a["id"]] = {"state": "error", "error": msg + " Nothing was saved; run it again."}
                        BATCH["errors"].append({"id": a["id"], "company": a["company"], "error": msg})
            with JOBS_LOCK:
                BATCH["done"] += 1
        with JOBS_LOCK:
            BATCH.update(state="done", current=None)
    background(work)
    return True


def outcomes():
    """Kushal's view: every application with the tool's call, Riya's call and whether they agree."""
    reads = {r["id"]: r for r in STORE.all("reads")}
    decisions = {d["id"]: d for d in STORE.all("decisions")}
    talks = {o["id"]: o for o in STORE.all("outreach")}
    apps = {a["id"]: a for a in case.applications()}
    top = lambda xs: [{"text": x["text"], "source": x.get("source")} for x in (xs or [])[:2]]  # noqa: E731
    rows = []
    for a in case.summary():
        r, d = reads.get(a["id"]), decisions.get(a["id"])
        rows.append(dict(a, recommendation=r and r["recommendation"], total=r and r["total"], gates=r and r["gates"],
                         riya=d and d["call"], reason=d and d["reason"], agrees=None if not (r and d) else not d["disagrees"],
                         meeting=meeting(talks.get(a["id"])), what_it_does=r and r.get("what_it_does"),
                         founders=["%s (%s)" % f if f[1] else f[0] for f in case.founders(apps[a["id"]])],
                         why_yes=top(r and r.get("why_yes")), why_no=top(r and r.get("why_no")), benchmark=r and r.get("benchmark")))
    return {"rows": rows, "thesis": thesis.listing(), "corrections": corrections.all_corrections()}


def meeting(o):
    """The meeting column in words, from the scheduling agent's record."""
    if not o or o["status"] == "withdrawn":
        return "Not contacted"
    if o["status"] == "booked":
        return "Booked " + outreach.cal.label(outreach.parse(o["booked"]))
    return {"draft": "Email drafted", "sent": "Email sent", "counter_proposed": "Times proposed", "needs_human": "Riya to reply",
            "escalated": "Riya took over", "timed_out": "No reply", "closed_not_interested": "Not interested",
            "skipped": "Not sent", "aborted": "Stopped"}.get(o["status"], o["status"])


def trust():
    """The trust report: the last eval run, the backtest and the human audit, as saved by the harness scripts."""
    res = Path(__file__).resolve().parent.parent / "evals"
    load = lambda p: json.loads(p.read_text()) if p.exists() else None  # noqa: E731
    run, bt, audit = load(res / "results" / "latest.json"), load(res / "backtest" / "result.json"), load(res / "results" / "audit.json")
    if run:
        run = {k: v for k, v in run.items() if k != "results"}
    if bt:
        bt = dict(bt, rows=[{k: r[k] for k in ("company", "actual", "set", "total", "gates", "call", "agrees")} for r in bt["rows"]])
    return {"run": run, "backtest": bt, "audit": audit, "benchmark": read.THESIS["benchmark"], "benchmark_status": read.THESIS["benchmark_status"]}


def read_state(app_id):
    with JOBS_LOCK:
        job = dict(JOBS.get(app_id) or {})
    if job.get("state") == "running":
        return {"state": "running"}
    saved = STORE.get("reads", app_id)
    if saved:
        return {"state": "done", "read": saved, "decision": STORE.get("decisions", app_id)}
    return job or {"state": "none"}


class Handler(SimpleHTTPRequestHandler):
    timeout = 10  # a client that stalls mid-request releases its thread

    def _trusted(self):
        host, origin = self.headers.get("Host", "").lower(), self.headers.get("Origin")
        if ON_VERCEL:
            if origin is None or origin.lower() == "https://" + host:
                return True
            self._json(403, {"error": "Requests must come from this app."})
            return False
        if host in ALLOWED_HOSTS and (origin is None or origin.lower() in ALLOWED_ORIGINS):
            return True
        self._json(421 if host not in ALLOWED_HOSTS else 403, {"error": "Open the app at http://%s:%d." % (HOST, PORT)})
        return False

    def _signed_in(self):
        path = urlparse(self.path).path
        self.role = auth.role(self.headers.get("Cookie"))
        if not path.startswith("/api/") or path in OPEN_ROUTES:
            return True
        if auth.required() and not auth.configured():
            self._json(503, {"error": "Set RIYA_PASSWORD, KUSHAL_PASSWORD and SESSION_SECRET (in .env, or the Vercel project settings)."})
            return False
        if not self.role:
            self._json(401, {"error": "Sign in first.", "login": True})
            return False
        need = ROLE_ONLY.get((self.command, path))
        if need and need != self.role:
            self._json(403, {"error": "Only %s can do this." % need.capitalize()})
            return False
        return True

    def _json(self, code, payload, cookie=None):
        body = json.dumps(payload).encode()
        self.send_response(code)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")  # always recheck pages and scripts
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
        super().end_headers()

    def _safely(self, work):
        """An unexpected failure is answered in words; detail stays in the server log."""
        try:
            work()
        except (socket.timeout, ConnectionError):
            raise
        except Exception as e:
            traceback.print_exc()
            self._json(500, {"error": "The app hit an error (%s). Try again." % type(e).__name__})

    def do_GET(self):
        self._safely(self._get)

    def do_POST(self):
        self._safely(self._post)

    def _get(self):
        if not self._trusted() or not self._signed_in():
            return
        url = urlparse(self.path)
        if url.path == "/api/applications":
            done = {r["id"]: r["recommendation"] for r in STORE.all("reads")}
            decided = {d["id"]: d["call"] for d in STORE.all("decisions")}
            apps = [dict(a, recommendation=done.get(a["id"]), decision=decided.get(a["id"])) for a in case.summary()]
            return self._json(200, {"applications": apps, "test_mode": os.environ.get("TEST_MODE", "1") == "1"})
        if url.path == "/api/me":
            return self._json(200, {"role": self.role, "login_required": auth.required()})
        if url.path == "/api/cron":
            secret = os.environ.get("CRON_SECRET", "")
            given = self.headers.get("Authorization", "")
            if not secret or not hmac.compare_digest(given.encode(), ("Bearer " + secret).encode()):
                return self._json(401, {"error": "Not allowed."})
            outreach.tick_all()
            return self._json(200, {"ok": True})
        if url.path == "/api/batch":
            with JOBS_LOCK:
                batch = dict(BATCH, errors=list(BATCH["errors"]))
            return self._json(200, batch)
        if url.path == "/api/thesis":
            return self._json(200, thesis.listing())
        if url.path == "/api/trust":
            return self._json(200, trust())
        if url.path == "/api/outreach":
            rows = sorted(STORE.all("outreach"), key=lambda o: o.get("sent_at") or "~")
            return self._json(200, {"outreach": [o for o in rows if o["status"] != "withdrawn"], "test_mode": outreach.mailer.test_mode(),
                                    "alerts": STORE.all("alerts")})
        if url.path == "/api/corrections":
            return self._json(200, {"corrections": corrections.all_corrections()})
        if url.path == "/api/outcomes":
            return self._json(200, outcomes())
        if url.path == "/api/portfolio":
            return self._json(200, portfolio.view())
        if url.path == "/api/read":
            app_id = (parse_qs(url.query).get("id") or [""])[0]
            if app_id not in IDS:
                return self._json(404, {"error": "No such application."})
            return self._json(200, read_state(app_id))
        if self.path.startswith("/api/"):
            return self._json(404, {"error": "Not found."})
        super().do_GET()

    def _post(self):
        if not self._trusted() or not self._signed_in():
            return
        # JSON only: another website cannot send this content type without a preflight we never answer.
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self._json(415, {"error": "Send JSON."})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._json(400, {"error": "Bad request."})
        if length < 0 or length > MAX_BODY:
            return self._json(413 if length > 0 else 400, {"error": "Bad request."})
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._json(400, {"error": "Bad request."})
        if not isinstance(data, dict):
            return self._json(400, {"error": "Bad request."})
        if self.path == "/api/login":
            who = data.get("role")
            if who in auth.ROLES and auth.check_password(who, data.get("password")):
                return self._json(200, {"ok": True, "role": who}, cookie=auth.new_cookie(who, secure=ON_VERCEL))
            time.sleep(1)  # slows password guessing
            return self._json(401, {"error": "That password is not right."})
        if self.path == "/api/logout":
            return self._json(200, {"ok": True}, cookie=auth.clear_cookie(secure=ON_VERCEL))
        if self.path == "/api/read":
            if data.get("id") not in IDS:
                return self._json(404, {"error": "No such application."})
            started = start_read(data["id"])
            if ON_VERCEL:  # the read ran inside this request: answer with it (or its error) straight away
                return self._json(200, read_state(data["id"]))
            return self._json(202, {"state": "running", "started": started})
        if self.path == "/api/decision":
            return self._decide(data)
        if self.path == "/api/eval":  # the eval harness: local only, it can spend on model calls
            if ON_VERCEL:
                return self._json(404, {"error": "Not found."})
            try:
                return self._json(200, {"output": evalpoints.run(data.get("point"), data.get("input") or {})})
            except (ValueError, KeyError, TypeError) as e:
                return self._json(400, {"error": "Bad eval input (%s)." % e})
            except read.claude.ClaudeError as e:
                return self._json(502, {"error": str(e)})
        if self.path == "/api/correction/reject":
            saved, n = STORE.get("reads", data.get("id") if data.get("id") in IDS else ""), data.get("n")
            updated = corrections.reject(saved, n) if saved and isinstance(n, int) else None
            if not updated:
                return self._json(409, {"error": "That correction is not applied to this read."})
            updated["recommendation"] = read.recommend(updated["total"], [{"gate": g} for g in updated["gates"]])
            STORE.put("reads", updated["id"], updated)
            return self._json(200, {"ok": True, "read": updated})
        if self.path == "/api/outreach/send":
            app_id, subject, body = data.get("id"), data.get("subject"), data.get("body")
            if app_id not in IDS or not isinstance(subject, str) or not isinstance(body, str):
                return self._json(400, {"error": "Bad request."})
            subject, body = subject.strip(), body.strip()
            if not subject or not body:
                return self._json(400, {"error": "Write a subject and a message before sending."})
            if len(subject) > 200 or len(body) > 4000:
                return self._json(400, {"error": "Keep the subject under 200 and the message under 4,000 characters."})
            try:
                return self._json(200, {"ok": True, "outreach": outreach.send_first(app_id, subject, body)})
            except ValueError as e:
                return self._json(409, {"error": str(e)})
            except outreach.mailer.Refused as e:
                return self._json(409, {"error": "Not sent: %s" % e})
            except Exception as e:
                traceback.print_exc()
                return self._json(502, {"error": "The email could not be sent (%s). Nothing was marked as sent." % type(e).__name__})
        if self.path == "/api/batch":
            if ON_VERCEL:  # ten reads won't fit in one function call: the page reads them one by one instead
                return self._json(200, {"client": True, "ids": [a["id"] for a in case.applications()]})
            return self._json(202, {"started": start_batch(), "batch": dict(BATCH)})
        if self.path == "/api/thesis/approve":
            v = thesis.approve(data.get("n"), by=self.role) if isinstance(data.get("n"), int) else None
            if not v:
                return self._json(409, {"error": "That version is not waiting for approval."})
            return self._json(200, {"ok": True, "version": v["version"]})
        if self.path == "/api/setup-check":  # POST only: a stray link or image must not trigger key checks
            return self._json(200, checks.run_all())
        self._json(404, {"error": "Not found."})

    def _decide(self, data):
        """Riya's call: the only way a decision is made. A reason is required when she differs from the tool."""
        app_id, call, reason = data.get("id"), data.get("call"), data.get("reason") or ""
        if app_id not in IDS:
            return self._json(404, {"error": "No such application."})
        if call not in ("go", "nogo") or not isinstance(reason, str):
            return self._json(400, {"error": "Choose Go or No-go."})
        reason = reason.strip()
        if len(reason) > MAX_REASON:
            return self._json(400, {"error": "Keep the reason under %d characters." % MAX_REASON})
        saved = STORE.get("reads", app_id)
        if not saved:
            return self._json(409, {"error": "Run the read before deciding."})
        disagrees = (call == "go") != (saved["recommendation"] == "GO")
        if disagrees and not reason:
            return self._json(400, {"error": "Your call differs from the tool's. Say why in one line.", "field": "reason"})
        decision = {"id": app_id, "call": call, "reason": reason, "by": "riya", "tool": saved["recommendation"],
                    "disagrees": disagrees, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        STORE.put("decisions", app_id, decision)
        if disagrees:
            learn_from(decision, saved)
        if call == "go":
            draft_for(app_id, saved)
        else:  # a change of mind before sending withdraws the unsent draft
            o = STORE.get("outreach", app_id)
            if o and o["status"] == "draft":
                STORE.put("outreach", app_id, dict(o, status="withdrawn"))
        return self._json(200, {"ok": True, "decision": decision, "learning": disagrees})


if __name__ == "__main__":
    print("All In Capital triage on http://%s:%d" % (HOST, PORT))
    every = int(os.environ.get("AGENT_TICK_SECONDS") or 300)
    if every > 0:
        threading.Thread(target=agent_loop, args=(every,), daemon=True).start()
    ThreadingHTTPServer((HOST, PORT), partial(Handler, directory=str(WEB))).serve_forever()
