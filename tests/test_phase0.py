"""Phase 0: the case loads, the server refuses foreign hosts and non-JSON posts, and checks never leak keys."""
import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
os.environ["RIYA_PASSWORD"] = os.environ["KUSHAL_PASSWORD"] = ""  # open local mode; .env must not switch logins on
import case  # noqa: E402
import checks  # noqa: E402
import httpd  # noqa: E402


class Phase0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(httpd.Handler, directory=str(httpd.WEB)))
        cls.port = cls.srv.server_address[1]
        httpd.ALLOWED_HOSTS.add("127.0.0.1:%d" % cls.port)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def req(self, path, body=None, host=None, ctype="application/json"):
        r = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path), data=None if body is None else body.encode(),
                                   headers={"Content-Type": ctype, **({"Host": host} if host else {})})
        try:
            with urllib.request.urlopen(r, timeout=5) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def test_ten_applications_with_labels(self):
        apps = case.applications()
        self.assertEqual(len(apps), 10)
        for a in apps:
            self.assertTrue(a["deck_text"] and a["form_text"] and a["stage"] and a["sector_label"], a["company"])
        self.assertEqual({a["stage"] for a in apps if a["company"] == "Settlr"}, {"Series A"})

    def test_list_endpoint_hides_deck_text(self):
        code, d = self.req("/api/applications")
        self.assertEqual(code, 200)
        self.assertEqual(len(d["applications"]), 10)
        self.assertNotIn("deck_text", d["applications"][0])

    def test_foreign_host_refused(self):
        self.assertEqual(self.req("/api/applications", host="evil.example:8331")[0], 421)

    def test_post_must_be_json(self):
        self.assertEqual(self.req("/api/setup-check", "{}", ctype="text/plain")[0], 415)

    def test_missing_keys_named_not_shown(self):
        saved = {k: os.environ.pop(k, None) for k in ("TAVILY_API_KEY", "RESEND_API_KEY")}
        try:
            r = checks.check_tavily(), checks.check_resend()
            self.assertTrue(all(not x["ok"] and "Not set" in x["detail"] for x in r))
        finally:
            os.environ.update({k: v for k, v in saved.items() if v})

    def test_detail_never_contains_a_key(self):
        result = json.dumps(checks.run_all())
        for k in ("ANTHROPIC_API_KEY", "TAVILY_API_KEY", "RESEND_API_KEY", "JUDGE_API_KEY"):
            v = os.environ.get(k)
            if v:
                self.assertNotIn(v, result)


if __name__ == "__main__":
    unittest.main()
