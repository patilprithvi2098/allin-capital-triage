"""Phase 2: two logins with their own permissions, thesis versions with Kushal's approval, memo hold-out, overlap gate,
whole-batch run. No paid calls: reads are faked."""
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
os.environ["RIYA_PASSWORD"], os.environ["KUSHAL_PASSWORD"] = "riya-test-pw", "kushal-test-pw"  # test values only
os.environ.pop("DATABASE_URL", None)
import store  # noqa: E402

store.STORE.root = Path(tempfile.mkdtemp())
import httpd  # noqa: E402
import read  # noqa: E402
import thesis  # noqa: E402


class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(httpd.Handler, directory=str(httpd.WEB)))
        cls.port = cls.srv.server_address[1]
        httpd.ALLOWED_HOSTS.add("127.0.0.1:%d" % cls.port)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def call(self, path, body=None, cookie=None):
        h = {"Content-Type": "application/json"}
        if cookie:
            h["Cookie"] = cookie
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path), None if body is None else json.dumps(body).encode(), h)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r), r.headers.get("Set-Cookie")
        except urllib.error.HTTPError as e:
            return e.code, json.load(e), None

    def login(self, role, pw):
        code, data, cookie = self.call("/api/login", {"role": role, "password": pw})
        return code, cookie.split(";")[0] if cookie else None

    def test_wrong_password_and_wrong_role_refused(self):
        self.assertEqual(self.login("riya", "kushal-test-pw")[0], 401)
        self.assertEqual(self.login("admin", "riya-test-pw")[0], 401)
        self.assertEqual(self.call("/api/applications")[0], 401)

    def test_roles_get_only_their_actions(self):
        _, riya = self.login("riya", "riya-test-pw")
        _, kushal = self.login("kushal", "kushal-test-pw")
        self.assertEqual(self.call("/api/me", cookie=riya)[1]["role"], "riya")
        self.assertEqual(self.call("/api/me", cookie=kushal)[1]["role"], "kushal")
        self.assertEqual(self.call("/api/decision", {"id": "earnwise", "call": "go"}, kushal)[0], 403)
        self.assertEqual(self.call("/api/batch", {}, kushal)[0], 403)
        self.assertEqual(self.call("/api/read", {"id": "earnwise"}, kushal)[0], 403)
        self.assertEqual(self.call("/api/thesis/approve", {"n": 1}, riya)[0], 403)
        self.assertEqual(self.call("/api/outcomes", cookie=kushal)[0], 200)

    def test_forged_cookie_refused(self):
        _, riya = self.login("riya", "riya-test-pw")
        forged = riya.replace("aic_session=riya.", "aic_session=kushal.")
        self.assertEqual(self.call("/api/me", cookie=forged)[0], 401)

    def test_kushal_approves_a_waiting_version_once(self):
        store.STORE.put("thesis", "v1", dict(thesis.V0, version="v1", n=1, status="waiting for approval",
                                              criteria=[dict(c, written=c["good"], observed=[], gap="") for c in thesis.V0["criteria"]]))
        _, kushal = self.login("kushal", "kushal-test-pw")
        self.assertEqual(thesis.current()["version"], "v0-draft")
        code, data, _ = self.call("/api/thesis/approve", {"n": 1}, kushal)
        self.assertEqual((code, data["version"]), (200, "v1"))
        self.assertEqual(thesis.current()["version"], "v1")
        self.assertEqual(self.call("/api/thesis/approve", {"n": 1}, kushal)[0], 409)  # already approved
        self.assertEqual(self.call("/api/thesis/approve", {"n": "1"}, kushal)[0], 409)

    def test_batch_reads_all_ten_and_records_failures(self):
        calls = []

        def fake_run(app_id):
            calls.append(app_id)
            if app_id == "pumpwise":
                raise read.claude.ClaudeError("The Claude API was busy (HTTP 529) on 3 tries.")
            return {"id": app_id, "recommendation": "NO-GO", "total": 40, "gates": []}
        real = read.run
        read.run = fake_run
        try:
            _, riya = self.login("riya", "riya-test-pw")
            self.assertEqual(self.call("/api/batch", {}, riya)[0], 202)
            for _ in range(100):
                if self.call("/api/batch", cookie=riya)[1]["state"] == "done":
                    break
                time.sleep(0.05)
            b = self.call("/api/batch", cookie=riya)[1]
        finally:
            read.run = real
        self.assertEqual((b["done"], b["total"]), (10, 10))
        self.assertEqual(len(calls), 10)
        self.assertEqual([e["id"] for e in b["errors"]], ["pumpwise"])
        rows = {r["id"]: r for r in self.call("/api/outcomes", cookie=riya)[1]["rows"]}
        self.assertEqual(rows["earnwise"]["recommendation"], "NO-GO")
        self.assertIsNone(rows["pumpwise"]["recommendation"])  # failed read is not shown as a result


class Thesis(unittest.TestCase):
    def test_held_out_memos_never_build_the_thesis(self):
        names = [m["name"] for m in thesis.build_memos()]
        self.assertEqual(len(names), 6)
        for held in thesis.HELD_OUT.values():
            self.assertFalse(any(held.split()[0] in n for n in names), held)
        self.assertEqual(sorted(m["decision"] for m in thesis.build_memos()), ["INVESTED"] * 3 + ["PASSED"] * 3)

    def test_overlap_gate_needs_a_listed_company(self):
        g = read.overlap_gate({"verdict": "overlap", "company": "meetrecord", "reason": "Both summarise sales calls."})
        self.assertEqual(g[0]["gate"], "portfolio overlap")
        self.assertIn("MeetRecord:", g[0]["quote"])
        self.assertEqual(read.overlap_gate({"verdict": "overlap", "company": "Gong", "reason": "x"}), [])
        self.assertEqual(read.overlap_gate({"verdict": "adjacent", "company": "MeetRecord", "reason": "x"}), [])
        self.assertEqual(len(read.adjacent_note({"verdict": "adjacent", "company": "Mailmodo", "reason": "x"})), 1)

    def test_overlap_verdict_rules(self):
        c = lambda name, p, b, w: {"company": name, "same_problem": p, "same_buyer": b, "same_workflow": w, "reason": "r"}
        self.assertEqual(read.overlap_verdict([c("MeetRecord", True, True, False)])["verdict"], "overlap")
        self.assertEqual(read.overlap_verdict([c("MeetRecord", True, False, True)])["verdict"], "overlap")
        self.assertEqual(read.overlap_verdict([c("MeetRecord", True, False, False)])["verdict"], "none")
        self.assertEqual(read.overlap_verdict([c("Mailmodo", False, True, True)])["verdict"], "adjacent")
        self.assertEqual(read.overlap_verdict([c("Jai Kisan", False, True, False)])["verdict"], "none")
        self.assertEqual(read.overlap_verdict([c("Gong", True, True, True)])["verdict"], "none")  # not on the list
        v = read.overlap_verdict([c("Mailmodo", False, True, True), c("MeetRecord", True, True, True)])
        self.assertEqual((v["verdict"], v["company"]), ("overlap", "MeetRecord"))  # a real conflict wins over adjacent


if __name__ == "__main__":
    unittest.main()
