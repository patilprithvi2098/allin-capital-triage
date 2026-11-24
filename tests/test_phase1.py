"""Phase 1 rules decided in code: deck-vs-form comparison, quote checks, caps, gates, GO/NO-GO, and Riya's decision API.
No paid calls: the model and search are replaced by fakes."""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
os.environ["RIYA_PASSWORD"] = os.environ["KUSHAL_PASSWORD"] = ""  # open local mode; .env must not switch logins on
os.environ.pop("DATABASE_URL", None)
import store  # noqa: E402

store.STORE.root = Path(tempfile.mkdtemp())  # tests never touch real reads or decisions
import case  # noqa: E402
import httpd  # noqa: E402
import read  # noqa: E402

APPS = {a["id"]: a for a in case.applications()}


def claim(src, quote, text="claim", ev=""):
    return {"text": text, "source": src, "quote": quote, "evidence_id": ev}


def fake_scored(points=None, claims=None, missing=None, yes=(), no=(), injection=False):
    points = points or {}
    return {"criteria": [{"key": k, "points": points.get(k, m), "confidence": "high", "why": "w",
                          "claims": (claims or {}).get(k, []), "missing": (missing or {}).get(k, [])}
                         for k, m in read.MAX.items()],
            "differences": [], "why_yes": list(yes), "why_no": list(no), "injection_seen": injection}


class Rules(unittest.TestCase):
    def test_numbers_with_indian_units(self):
        self.assertEqual(read.number("INR 3.8 L GMV"), 380000)
        self.assertEqual(read.number("Under INR 2,000 per store"), 2000)
        self.assertEqual(read.number("INR 30 Cr"), 3e8)
        self.assertIsNone(read.number("none so far"))

    def test_compare(self):
        self.assertEqual(read.compare("38 retailers onboarded", "42 retailers onboarded", "customers"), "differs")
        self.assertEqual(read.compare("INR 2,860 blended CAC, October", "Under INR 2,000 per store", "cac"), "differs")
        self.assertEqual(read.compare("Raising INR 2 Cr", "INR 2 Cr", "raise"), "matches")
        self.assertEqual(read.compare("Hyderabad", "Hyderabad, Telangana", "location"), "matches")
        self.assertEqual(read.compare("INR 3.8 L in October", "INR 9 lakh in the last three months", "revenue"), "different periods")
        self.assertEqual(read.compare("", "INR 12 Cr post-money", "valuation"), "only in form")

    def test_quote_check_ignores_line_breaks_and_case(self):
        deck = APPS["stocksathi"]["deck_text"]
        self.assertTrue(read.quoted("losing half a day each time", deck))
        self.assertFalse(read.quoted("backed by Sequoia Capital", deck))
        self.assertFalse(read.quoted("a", deck))  # too short to prove anything

    def test_unsourced_claims_are_dropped_and_score_capped(self):
        app = APPS["stocksathi"]
        s = fake_scored(claims={"founder_quality": [claim("deck", "8 years in FMCG distribution"),
                                                    claim("deck", "ex-McKinsey partner, IIT topper")],
                                "path_to_market": [claim("web", "featured in YourStory", ev="E9")]})
        crit, dropped = read.apply_rules(s, app, [])
        by = {c["key"]: c for c in crit}
        self.assertEqual(dropped, 2)
        self.assertEqual(len(by["founder_quality"]["claims"]), 1)
        self.assertEqual(by["path_to_market"]["points"], int(20 * read.UNSOURCED_CAP))  # nothing checkable left
        self.assertEqual(by["path_to_market"]["confidence"], "low")

    def test_unfindable_caps_not_zeroes(self):
        app = APPS["stocksathi"]
        s = fake_scored(claims={"founder_quality": [claim("form", "Both full-time since April 2026")]},
                        missing={"founder_quality": [{"item": "founder background online", "kind": "unfindable"}]})
        fq = next(c for c in read.apply_rules(s, app, [])[0] if c["key"] == "founder_quality")
        self.assertEqual(fq["points"], int(25 * read.UNFINDABLE_CAP))
        self.assertGreater(fq["points"], 0)
        self.assertEqual(fq["confidence"], "medium")

    def test_points_clamped_and_missing_criterion_scores_zero(self):
        s = fake_scored(points={"sector_fit": 40}, claims={"sector_fit": [claim("form", "Sector (as selected) Consumer tech")]})
        s["criteria"] = [c for c in s["criteria"] if c["key"] != "defensibility"]
        by = {c["key"]: c for c in read.apply_rules(s, APPS["stocksathi"], [])[0]}
        self.assertEqual(by["sector_fit"]["points"], 10)
        self.assertEqual(by["defensibility"]["points"], 0)
        self.assertEqual(list(by), list(read.MAX))

    def test_web_claim_needs_quote_in_cited_result(self):
        ev = [{"id": "E1", "title": "StockSathi raises angel round", "url": "https://news.example/s", "content": "Hyderabad startup StockSathi raised INR 25 lakh."}]
        app = APPS["stocksathi"]
        self.assertTrue(read.verify(claim("web", "StockSathi raised INR 25 lakh", ev="E1"), app, ev))
        self.assertFalse(read.verify(claim("web", "StockSathi raised INR 25 lakh", ev="E2"), app, ev))
        self.assertFalse(read.verify(claim("web", "StockSathi raised INR 5 Cr", ev="E1"), app, ev))

    def test_gates(self):
        self.assertEqual(read.gates(APPS["stocksathi"]), [])
        self.assertEqual({g["gate"] for g in read.gates(APPS["settlr"])}, {"stage", "cheque size"})
        self.assertEqual([g["gate"] for g in read.gates(APPS["carecorner"])], ["outside the areas"])
        for a in ("settlr", "carecorner"):
            for g in read.gates(APPS[a]):
                self.assertTrue(read.quoted(g["quote"], APPS[a]["form_text"]))

    def test_search_ignores_namesakes(self):
        import tavily
        f = {f["field"]: f for f in tavily.fields(APPS["stocksathi"])}
        doctor = {"title": "Dr. Aarav Deshmukh, Orthopaedic Surgeon", "content": "Consultant at a Pune hospital."}
        real = {"title": "Kirana startup StockSathi", "content": "Founder Aarav Deshmukh says StockSathi serves Karimnagar."}
        self.assertFalse(tavily.about(doctor, f["founder: Aarav Deshmukh"]))
        self.assertTrue(tavily.about(real, f["founder: Aarav Deshmukh"]))
        self.assertTrue(tavily.about(real, f["company"]))
        self.assertFalse(tavily.about({"title": "StockSathi stock tips", "content": "Daily share market video"}, f["company"]))

    def test_absence_online_is_never_a_reason_against(self):  # K3
        app = APPS["stocksathi"]
        s = fake_scored()
        s["why_no"] = [claim("form", "Not registered as an NBFC", "Lending without NBFC registration"),
                       claim("form", "Both full-time since April 2026", "No independent web footprint to verify the team")]
        r = read.run("stocksathi", gather=lambda a: ([], []), extract=lambda a: [], scorer=lambda a, f, e, t: s, overlaps=lambda a: [], learned=lambda a: [])
        texts = [x["text"] for x in r["why_no"]]
        self.assertIn("Lending without NBFC registration", texts)
        self.assertNotIn("No independent web footprint to verify the team", texts)

    def test_recommendation(self):
        b = read.THESIS["benchmark"]
        self.assertEqual(read.recommend(b, []), "GO")
        self.assertEqual(read.recommend(b - 1, []), "NO-GO")
        self.assertEqual(read.recommend(100, [{"gate": "stage"}]), "NO-GO")

    def test_full_run_with_fakes_never_decides(self):
        r = read.run("settlr", gather=lambda a: ([], [{"field": "company", "query": None, "stop_reason": "no_key"}]),
                     extract=lambda a: [], scorer=lambda a, f, e, t: fake_scored(), overlaps=lambda a: [], learned=lambda a: [])
        self.assertEqual(r["recommendation"], "NO-GO")  # full marks, but the gates still stop it
        self.assertEqual(r["why_no"][0]["source"], "form")
        self.assertTrue(r["decision"].startswith("Not decided"))  # the tool never decides; Riya does
        self.assertIn("One-line", APPS["settlr"]["form_text"])
        self.assertTrue(r["what_it_does"])


class DecisionApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(httpd.Handler, directory=str(httpd.WEB)))
        cls.port = cls.srv.server_address[1]
        httpd.ALLOWED_HOSTS.add("127.0.0.1:%d" % cls.port)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        store.STORE.put("reads", "earnwise", {"id": "earnwise", "recommendation": "GO"})
        cls.learned = []
        httpd.corrections.create = lambda decision, saved, ask=None: cls.learned.append(decision["id"])  # never a real model call
        httpd.outreach.create_draft = lambda *a, **k: None  # never a real calendar read or model call

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def post(self, path, body):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path), json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def test_reason_required_only_when_disagreeing(self):
        self.assertEqual(self.post("/api/decision", {"id": "earnwise", "call": "nogo", "reason": "  "})[0], 400)
        code, d = self.post("/api/decision", {"id": "earnwise", "call": "go"})
        self.assertEqual(code, 200)
        self.assertFalse(d["decision"]["disagrees"])
        code, d = self.post("/api/decision", {"id": "earnwise", "call": "nogo", "reason": "Repeat rate is self-reported."})
        self.assertTrue(d["decision"]["disagrees"])

    def test_bad_input_refused(self):
        self.assertEqual(self.post("/api/decision", {"id": "earnwise", "call": "maybe"})[0], 400)
        self.assertEqual(self.post("/api/decision", {"id": "nope", "call": "go"})[0], 404)
        self.assertEqual(self.post("/api/decision", {"id": "earnwise", "call": "nogo", "reason": "x" * 501})[0], 400)
        self.assertEqual(self.post("/api/decision", {"id": "pumpwise", "call": "go"})[0], 409)  # no read yet
        self.assertEqual(self.post("/api/read", {"id": "../etc"})[0], 404)


if __name__ == "__main__":
    unittest.main()
