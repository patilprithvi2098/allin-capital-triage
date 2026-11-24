"""What the eval harness calls over HTTP (POST /api/eval): one decision point at a time, on test input.
Nothing here saves a read or a decision. Web search stays off unless a case asks for it (dummy companies are unfindable)."""
import threading

import read
import tavily

_SWAP = threading.Lock()

NO_SEARCH = lambda a: ([], [{"field": "company", "query": None, "stop_reason": "off for evals"}])  # noqa: E731
APP_FIELDS = ("company", "sector_label", "stage", "raise", "deck_text", "form_text")


def _app(inp):
    if not all(isinstance(inp.get(k), str) for k in APP_FIELDS):
        raise ValueError("input needs %s as text" % ", ".join(APP_FIELDS))
    return dict({k: inp[k] for k in APP_FIELDS}, id="eval", source=inp.get("source", "Public application form."))


def _scored(inp):
    """A model answer supplied by the test, so the code rules are tested without a model call."""
    base = {k: m for k, m in read.MAX.items()}
    crit = []
    for key, mx in base.items():
        c = (inp.get("criteria") or {}).get(key, {})
        crit.append({"key": key, "points": c.get("points", mx), "confidence": c.get("confidence", "high"), "why": "test",
                     "claims": c.get("claims", []), "missing": c.get("missing", [])})
    if inp.get("drop_criterion"):
        crit = [c for c in crit if c["key"] != inp["drop_criterion"]]
    return {"criteria": crit, "differences": [], "why_yes": [], "why_no": [], "injection_seen": False}


def run(point, inp):
    if point == "compare":
        return {"status": read.compare(inp.get("deck", ""), inp.get("form", ""), inp.get("key", ""))}
    if point == "gates":
        app = {"stage": inp.get("stage", ""), "sector_label": inp.get("sector_label", ""), "raise": inp.get("raise", "")}
        app["form_text"] = "Sector (as selected) %s Stage (as selected) %s Amount raising %s" % (app["sector_label"], app["stage"], app["raise"])
        return {"gates": [g["gate"] for g in read.gates(app)]}
    if point == "verify":
        app = {"deck_text": inp.get("deck_text", ""), "form_text": inp.get("form_text", "")}
        return {"kept": read.verify(inp["claim"], app, inp.get("evidence", []))}
    if point == "rules":
        app = {"deck_text": inp.get("deck_text", ""), "form_text": inp.get("form_text", "")}
        crit, dropped = read.apply_rules(_scored(inp), app, inp.get("evidence", []))
        return {"criteria": crit, "dropped": dropped}
    if point == "recommend":
        total, b = inp["total"], read.THESIS["benchmark"]
        if isinstance(total, str):  # "B", "B-1", "B+1": relative to whatever the benchmark is now
            total = b + int(total[1:] or 0)
        return {"recommendation": read.recommend(total, [{"gate": g} for g in inp.get("gates", [])]), "benchmark": b}
    if point == "search_rule":  # does this search result count as being about the company or founder?
        return {"counts": tavily.about(inp["result"], inp["field"])}
    if point in ("schedule_decide", "schedule_tick", "route", "reply_classify"):
        if point == "reply_classify":
            return _outreach(point, inp)
        with _SWAP:  # these briefly swap process-wide settings (test mode, allowlist, a throwaway store): one at a time
            return _outreach(point, inp)
    if point == "apply_corrections":  # the code rules: cap, bounds, conflict
        crit, applied = read.corrections.apply(inp["criteria"], inp["matches"])
        return {"criteria": crit, "applied": [a["n"] for a in applied]}
    if point == "correction_worth":  # would this disagreement become a reusable correction?
        out = read.claude.ask_json(read.claude.SONNET, read.corrections.WORTH_SYSTEM,
              "Company: %s. What it does: %s\nTool recommended %s.\nAssociate's call: %s\n<reason>%s</reason>" % (
                  inp["company"], inp["what_it_does"], inp["tool"], inp["call"], inp["reason"]), read.corrections.WORTH_SCHEMA, effort="low")
        return {"worth_storing": out["worth_storing"], "criterion": out["criterion"], "direction": out["direction"]}
    if point == "correction_match":  # does a given correction apply to this application?
        c = dict(inp["correction"], n=1, worth_storing=True, rejected_by=[], **{"from": "elsewhere"})
        out = read.claude.ask_json(read.claude.SONNET, read.corrections.MATCH_SYSTEM,
                                   "Corrections:\n#1 [%s]: %s Applies when: %s\n\n<form>\n%s\n</form>" % (c["criterion"], c["lesson"], c["applies_when"], inp["form_text"]),
                                   read.corrections.MATCH_SCHEMA, effort="low")
        m = next((x for x in out["matches"] if x["id"] == 1), {"applies": False, "similar_because": ""})
        return {"applies": m["applies"], "why": m["similar_because"]}
    if point == "overlap_verdict":
        return read.overlap_verdict(inp["candidates"])
    if point == "overlap":
        app = _app(inp)
        cands = read.overlap_check(app)
        return dict(read.overlap_verdict(cands), candidates=cands)
    if point == "facts":
        return {"facts": read.extract_facts(_app(inp))}
    if point == "read":
        app = _app(inp)
        skip = [x for x in inp.get("exclude_portfolio", []) if isinstance(x, str)]
        return read.run_app(app, gather=tavily.gather if inp.get("search") else NO_SEARCH,
                            overlaps=lambda a: read.overlap_check(a, exclude=skip),
                            learned=(lambda a: []) if inp.get("no_corrections") else read.corrections.relevant)
    raise ValueError("unknown decision point")


def _outreach(point, inp):
    """Decisions 6 to 8 on test input. Nothing is sent and nothing real is booked: mail, calendar and inbox are fakes."""
    import os
    import tempfile
    from datetime import timedelta
    import calendar_ics as cal
    import mailer
    import outreach
    from store import FileStore
    t0 = outreach.parse("2026-11-23T04:00:00Z")
    st = {"id": "evalco", "company": "EvalCo", "founder": "Asha", "founder_email": inp.get("founder_email", "asha@evalco.example"), "deeptech": False,
          "status": inp.get("status", "sent"), "slots": inp.get("slots", ["2026-11-26T09:00:00Z"]), "round": inp.get("round", 0),
          "followups": inp.get("followups", 0), "seen": [], "history": [], "sent": {"subject": "Call [AIC-evalco]", "body": "b"},
          "thread": "<t@x>", "sent_at": outreach.iso(t0), "last_contact": outreach.iso(t0 + timedelta(hours=inp.get("last_contact_hours", 0)))}
    now = t0 + timedelta(hours=inp.get("hours", 0))
    busy = [(outreach.parse(a), outreach.parse(b)) for a, b in inp.get("busy", [])]
    if point == "route":  # on a throwaway store: test suppressions never touch the real do-not-contact list
        old_env, real = dict(os.environ), mailer.STORE
        mailer.STORE = FileStore(tempfile.mkdtemp())
        os.environ["TEST_MODE"] = "1" if inp.get("test_mode", True) else "0"
        os.environ["ALLOWLIST"] = ",".join(inp.get("allowlist", []))
        try:
            for a in inp.get("suppressed", []):
                mailer.suppress(a, "eval")
            return {"to": mailer.route(inp["founder_email"]), "refused": False}
        except mailer.Refused as ex:
            return {"to": None, "refused": True, "why": str(ex)}
        finally:
            os.environ.clear()
            os.environ.update(old_env)
            mailer.STORE = real
    if point == "schedule_decide":
        verdict = inp.get("verdict")
        status, action, detail = outreach.decide(st, now, {"text": "reply"} if verdict else None, verdict, busy)
        return {"status": status, "action": action, "detail": detail}
    if point == "reply_classify":
        return outreach.classify(inp["reply"], st["slots"], "2026-11-23 Mon")
    # schedule_tick: one agent cycle with failing tools, on a throwaway store so nothing real changes
    real = outreach.STORE
    tmp = FileStore(tempfile.mkdtemp())
    outreach.STORE = mailer.STORE = tmp
    try:
        tmp.put("outreach", "evalco", st)
        attempts = {"calendar": 0, "send": 0}
        fail = inp.get("fail", "")

        def fetch_busy():
            attempts["calendar"] += 1
            if fail == "calendar_timeout":
                raise cal.CalendarTimeout("no answer twice")
            if fail == "calendar_permission":
                raise cal.CalendarPermission("403")
            return busy

        def send(*a, **k):
            attempts["send"] += 1
            if fail == "bad_address" or (fail == "book_permanent" and k.get("ics")):
                raise mailer.PermanentError("refused")
            return "<m@x>"
        saves = []

        def save(s):
            if fail == "record_after_booking" and s["status"] == "booked":
                raise IOError("store down")
            saves.append(s["status"])
            tmp.put("outreach", s["id"], s)
        reply = inp.get("reply")
        out = outreach.tick("evalco", now=now, read_replies=lambda s: [{"id": "<r@x>", "text": reply}] if reply else [],
                            classify_fn=lambda t, s: inp.get("verdict", {"kind": "ambiguous"}), fetch_busy=fetch_busy, send=send, save=save, book_event=False)
        return {"status": out["status"], "calendar_attempts": attempts["calendar"], "send_attempts": attempts["send"],
                "alerted": bool(tmp.all("alerts")), "suppressed": mailer.suppressed(st["founder_email"])}
    finally:
        outreach.STORE = mailer.STORE = real
