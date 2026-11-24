"""Phase 7: every failure triggered on purpose. No paid calls, no real email: tools are faked."""
import io
import os
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
os.environ.pop("DATABASE_URL", None)
os.environ.setdefault("OPERATOR_EMAIL", "operator@example.com")
import store  # noqa: E402

store.STORE.root = Path(tempfile.mkdtemp())
import httpd  # noqa: E402
import case  # noqa: E402
import claude  # noqa: E402
import outreach  # noqa: E402
import read  # noqa: E402
import tavily  # noqa: E402


def http_error(code, body=b""):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(body))


class FakeOpener:
    def __init__(self, err):
        self.err = err

    def open(self, *a, **k):
        raise self.err


class Claude(unittest.TestCase):
    def ask_with(self, err):
        real = claude.urllib.request.build_opener
        claude.urllib.request.build_opener = lambda *a: FakeOpener(err)
        try:
            claude.ask_json(claude.HAIKU, "s", "u", {"type": "object"})
        finally:
            claude.urllib.request.build_opener = real

    def test_out_of_credit_says_so_and_stops_the_batch(self):
        with self.assertRaises(claude.ClaudeError) as c:
            self.ask_with(http_error(400, b'{"error":{"message":"Your credit balance is too low to access the Anthropic API."}}'))
        self.assertIn("out of credit", str(c.exception))
        self.assertTrue(c.exception.stops_batch)

    def test_refused_key_says_so_and_stops_the_batch(self):
        with self.assertRaises(claude.ClaudeError) as c:
            self.ask_with(http_error(401))
        self.assertIn("key was refused", str(c.exception))
        self.assertTrue(c.exception.stops_batch)

    def test_other_refusal_does_not_stop_the_batch(self):
        with self.assertRaises(claude.ClaudeError) as c:
            self.ask_with(http_error(400, b'{"error":{"message":"bad schema"}}'))
        self.assertFalse(c.exception.stops_batch)


class Tavily(unittest.TestCase):
    APP = case.applications()[0]

    def setUp(self):
        os.environ["TAVILY_API_KEY"] = "test-key"
        tavily.PAUSE.update(until=0, why="")
        self.real = tavily._search

    def tearDown(self):
        tavily._search = self.real
        tavily.PAUSE.update(until=0, why="")

    def test_quota_pauses_search_for_every_application(self):
        calls = []

        def used_up(q):
            calls.append(q)
            raise http_error(432)
        tavily._search = used_up
        _, trail = tavily.gather(self.APP)
        self.assertEqual(len(calls), 1)  # stopped at the first refusal, no retry
        self.assertGreater(tavily.PAUSE["until"], time.time())
        _, trail2 = tavily.gather(case.applications()[1])
        self.assertEqual(len(calls), 1)  # the next application does not call Tavily at all
        self.assertTrue(all(t["stop_reason"].startswith("paused: Tavily limit reached") for t in trail2))

    def test_server_error_is_retried_once(self):
        seq = [http_error(502), [{"title": "x", "url": "https://u", "content": "c"}]]

        def flaky(q):
            v = seq.pop(0) if seq else []
            if isinstance(v, Exception):
                raise v
            return v
        tavily._search = flaky
        _, trail = tavily.gather(self.APP)
        self.assertNotIn("error HTTP 502", [t["stop_reason"] for t in trail])


class Batch(unittest.TestCase):
    def run_batch(self, fake):
        real = read.run
        read.run = fake
        try:
            self.assertTrue(httpd.start_batch())
            for _ in range(200):
                if httpd.BATCH["state"] == "done":
                    break
                time.sleep(0.02)
            return dict(httpd.BATCH)
        finally:
            read.run = real

    def test_cost_cap_stops_the_rest(self):
        os.environ["BATCH_COST_CAP_USD"] = "1"
        calls = []

        def costly(app_id):
            calls.append(app_id)
            claude.spent["usd"] += 0.4
            return {"id": app_id, "recommendation": "NO-GO", "total": 40, "gates": []}
        try:
            b = self.run_batch(costly)
        finally:
            os.environ.pop("BATCH_COST_CAP_USD")
        self.assertEqual(len(calls), 3)  # 0.4, 0.8, 1.2: the fourth would start over the cap
        self.assertEqual(b["done"], 10)
        self.assertEqual(len(b["errors"]), 7)
        self.assertIn("$1.00 cost cap", b["errors"][0]["error"])

    def test_no_credit_stops_the_rest_without_more_calls(self):
        calls = []

        def broke(app_id):
            calls.append(app_id)
            raise claude.ClaudeError("The Claude account is out of credit.", stops_batch=True)
        b = self.run_batch(broke)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(b["errors"]), 10)
        self.assertTrue(all("out of credit" in e["error"] for e in b["errors"]))


class Agent(unittest.TestCase):
    def test_stuck_agent_tells_the_operator_once(self):
        sent = []
        st = {"id": "evalco", "company": "EvalCo"}
        for _ in range(3):
            outreach.problem(st, claude.ClaudeError("The Claude API key was refused (HTTP 401)."), send=lambda *a, **k: sent.append(a) or "<m>")
        self.assertEqual(len(sent), 1)
        self.assertIn("key was refused", sent[0][2])
        self.assertTrue(any("stuck on EvalCo" in a["text"] for a in store.STORE.all("alerts")))


class Duplicates(unittest.TestCase):
    def app(self, id_, name, site, founder):
        return {"id": id_, "company": name, "form_text": "Website www.%s Founders Founder 1 %s, CEO." % (site, founder)}

    def test_same_name_site_or_founder(self):
        a = self.app("a", "Grain Kind", "grainkind.in", "Ritu Hegde")
        others = [a, self.app("b", "grainkind", "other.in", "X Y"), self.app("c", "Other", "grainkind.in", "P Q"),
                  self.app("d", "Third", "third.in", "Ritu Hegde"), self.app("e", "Unrelated", "u.in", "Sam Lee")]
        self.assertEqual(case.duplicates(a, others), [("grainkind", "same name"), ("Other", "same website"), ("Third", "same founder")])

    def test_the_real_batch_has_none(self):
        self.assertTrue(all(not case.duplicates(a) for a in case.applications()))


if __name__ == "__main__":
    unittest.main()


class SecurityFixes(unittest.TestCase):
    """Phase 8 audit leads, each fixed and pinned."""

    def test_replies_from_anyone_but_the_founder_are_ignored(self):
        import email.message
        import mailer

        def msg(frm, mid):
            m = email.message.EmailMessage()
            m["From"], m["Subject"], m["Message-ID"] = frm, "Re: hi [AIC-x]", mid
            m.set_content("Not interested.")
            return m.as_bytes()
        box = [msg("Mallory <mallory@attacker.example>", "<1@a>"), msg("Founder <Founder@Dummy.example>", "<2@b>")]

        class FakeImap:
            def login(self, *a): pass
            def select(self, *a, **k): pass
            def search(self, *a): return "OK", [b"1 2"]
            def fetch(self, n, _): return "OK", [(None, box[int(n) - 1])]
            def logout(self): pass
        os.environ.setdefault("GMAIL_APP_PASSWORD", "x")
        got = mailer.replies("[AIC-x]", imap_factory=FakeImap, sender="founder@dummy.example")
        self.assertEqual([r["id"] for r in got], ["<2@b>"])

    def test_proposed_times_follow_the_slot_rules(self):
        import calendar_ics as cal
        from datetime import datetime, timezone, timedelta
        now = datetime(2026, 11, 23, 4, 0, tzinfo=timezone.utc)  # Monday 09:30 IST
        tue_2pm = datetime(2026, 11, 24, 8, 30, tzinfo=timezone.utc)
        self.assertTrue(cal.allowed(tue_2pm, now))
        self.assertFalse(cal.allowed(tue_2pm - timedelta(hours=7), now))  # 7:30 IST: outside the afternoon
        self.assertFalse(cal.allowed(tue_2pm, now + timedelta(hours=10)))  # under 24 hours ahead
        self.assertFalse(cal.allowed(tue_2pm + timedelta(days=21), now))  # beyond two weeks

    def test_eval_route_leaves_environment_and_store_alone(self):
        import evalpoints
        import mailer
        before, real = dict(os.environ), mailer.STORE
        out = evalpoints.run("route", {"founder_email": "a@x.example", "test_mode": False, "allowlist": ["a@x.example"], "suppressed": ["b@x.example"]})
        self.assertEqual(out["to"], "a@x.example")
        self.assertEqual(dict(os.environ), before)
        self.assertIs(mailer.STORE, real)
        self.assertFalse(mailer.suppressed("b@x.example"))  # the eval's suppression never reached the real list

    def test_vercel_needs_a_session_secret_and_it_changes_the_key(self):
        import auth
        env = {"RIYA_PASSWORD": "r", "KUSHAL_PASSWORD": "k", "VERCEL": "1"}
        old = {k: os.environ.get(k) for k in list(env) + ["SESSION_SECRET"]}
        try:
            os.environ.update(env); os.environ.pop("SESSION_SECRET", None)
            self.assertFalse(auth.configured())
            a = auth._secret()
            os.environ["SESSION_SECRET"] = "s" * 40
            self.assertTrue(auth.configured())
            self.assertNotEqual(a, auth._secret())
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def test_non_web_links_are_dropped_from_search_results(self):
        import json as _j

        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): pass
        body = _j.dumps({"results": [{"title": "t", "url": "javascript:alert(1)", "content": "c"}, {"title": "t", "url": "https://ok.example", "content": "c"}]}).encode()
        real = tavily.urllib.request.build_opener
        tavily.urllib.request.build_opener = lambda *a: type("O", (), {"open": lambda self, *x, **k: Resp(body)})()
        os.environ["TAVILY_API_KEY"] = "test-key"
        try:
            got = tavily._search("unique query %f" % time.time())
        finally:
            tavily.urllib.request.build_opener = real
        self.assertEqual([r["url"] for r in got], ["https://ok.example"])
