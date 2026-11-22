"""Phase 4: corrections are stored from disagreements, matched with a reason, applied in code with a 5-point cap,
the most recent wins a conflict, and a rejected match is undone and never reapplied. No paid calls: the model is faked."""
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
os.environ["RIYA_PASSWORD"] = os.environ["KUSHAL_PASSWORD"] = ""
os.environ.pop("DATABASE_URL", None)
import store  # noqa: E402

store.STORE.root = Path(tempfile.mkdtemp())
import corrections  # noqa: E402
import httpd  # noqa: E402

READ = {"id": "stocksathi", "company": "StockSathi", "sector_label": "Consumer tech", "stage": "Pre-seed",
        "what_it_does": "B2B restocking app with credit for kirana stores", "recommendation": "NO-GO", "total": 57, "gates": [],
        "criteria": [{"key": k, "points": p, "max": m, "why": "w", "confidence": "low", "claims": [], "missing": [], "rules": []}
                     for k, p, m in [("founder_quality", 17, 25), ("path_to_market", 10, 20), ("evidence_quality", 10, 20),
                                     ("defensibility", 6, 15), ("sector_fit", 8, 10), ("capital_fit", 6, 10)]]}
DECISION = {"id": "stocksathi", "call": "go", "reason": "CAC gap is founder-time accounting; distribution background fits.", "by": "riya"}


def fake_worth(points=4, direction="up", worth=True, criterion="path_to_market"):
    return lambda system, user, schema: {"worth_storing": worth, "why_not": "" if worth else "only about this founder",
                                         "criterion": criterion, "direction": direction, "points": points,
                                         "lesson": "Founder-time CAC in field-led B2B distribution is not a real cost problem.",
                                         "applies_when": "field-sales-led B2B distribution to small retailers"}


def match(n, delta, criterion="path_to_market", at="2026-11-20T10:00:00"):
    return {"n": n, "criterion": criterion, "delta": delta, "lesson": "l%d" % n, "company": "X", "at": at, "similar_because": "s"}


class Corrections(unittest.TestCase):
    def setUp(self):
        for f in (store.STORE.root / "corrections").glob("*.json") if (store.STORE.root / "corrections").exists() else []:
            f.unlink()

    def test_disagreement_becomes_a_capped_correction(self):
        c = corrections.create(DECISION, READ, ask=fake_worth(points=9))
        self.assertEqual((c["n"], c["criterion"], c["delta"]), (1, "path_to_market", 5))  # 9 asked, capped at 5
        self.assertTrue(c["worth_storing"])
        self.assertEqual(c["from"], "stocksathi")

    def test_company_specific_reason_is_not_reused(self):
        corrections.create(DECISION, READ, ask=fake_worth(worth=False))
        app = {"id": "other", "form_text": "f", "deck_text": "d"}
        self.assertEqual(corrections.relevant(app, ask=lambda *a: self.fail("no model call for nothing to match")), [])

    def test_never_matched_to_its_own_company(self):
        corrections.create(DECISION, READ, ask=fake_worth())
        own = {"id": "stocksathi", "form_text": "f", "deck_text": "d"}
        self.assertEqual(corrections.relevant(own, ask=lambda *a: self.fail("no call")), [])

    def test_match_carries_its_reason(self):
        corrections.create(DECISION, READ, ask=fake_worth())
        app = {"id": "kiranakart", "form_text": "B2B app for kirana stores", "deck_text": "field agents"}
        got = corrections.relevant(app, ask=lambda s, u, sch: {"matches": [{"id": 1, "applies": True, "similar_because": "similar because both sell to kiranas via field agents"}]})
        self.assertEqual(got[0]["similar_because"][:15], "similar because")

    def test_apply_cap_and_bounds(self):
        crit, applied = corrections.apply(READ["criteria"], [match(1, 4), match(2, 4, at="2026-11-21T10:00:00")])
        ptm = next(c for c in crit if c["key"] == "path_to_market")
        self.assertEqual((ptm["points_before"], ptm["points"]), (10, 15))  # 4 + 4 capped at 5
        self.assertEqual(len(applied), 2)
        crit, _ = corrections.apply(READ["criteria"], [match(3, 5, criterion="sector_fit")])
        self.assertEqual(next(c for c in crit if c["key"] == "sector_fit")["points"], 10)  # never over max

    def test_conflict_most_recent_wins(self):
        crit, applied = corrections.apply(READ["criteria"], [match(1, 4, at="2026-11-20T10:00:00"), match(2, -3, at="2026-11-21T10:00:00")])
        self.assertEqual(next(c for c in crit if c["key"] == "path_to_market")["points"], 7)
        self.assertEqual([a["n"] for a in applied], [2])

    def test_untouched_criteria_unchanged(self):
        crit, _ = corrections.apply(READ["criteria"], [match(1, 3)])
        self.assertEqual([c["points"] for c in crit if c["key"] != "path_to_market"], [17, 10, 6, 8, 6])
        self.assertNotIn("points_before", next(c for c in crit if c["key"] == "founder_quality"))


class RejectApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(httpd.Handler, directory=str(httpd.WEB)))
        cls.port = cls.srv.server_address[1]
        httpd.ALLOWED_HOSTS.add("127.0.0.1:%d" % cls.port)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def post(self, path, body):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, path), json.dumps(body).encode(), {"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def test_reject_undoes_the_move_and_blocks_rematch(self):
        c = corrections.create(DECISION, READ, ask=fake_worth(points=5))
        crit, applied = corrections.apply([dict(x) for x in READ["criteria"]], [dict(c, similar_because="similar because x")])
        r = dict(READ, id="yatrika", company="Yatrika", criteria=crit, corrections_applied=applied, total=sum(x["points"] for x in crit))
        store.STORE.put("reads", "yatrika", r)
        self.assertEqual(r["total"], 62)
        code, data = self.post("/api/correction/reject", {"id": "yatrika", "n": c["n"]})
        self.assertEqual(code, 200)
        self.assertEqual(data["read"]["total"], 57)
        self.assertEqual(data["read"]["corrections_applied"], [])
        self.assertIn("yatrika", store.STORE.get("corrections", "c%d" % c["n"])["rejected_by"])
        app = {"id": "yatrika", "form_text": "f", "deck_text": "d"}
        self.assertEqual(corrections.relevant(app, ask=lambda *a: self.fail("rejected: never matched again")), [])
        self.assertEqual(self.post("/api/correction/reject", {"id": "yatrika", "n": c["n"]})[0], 409)  # already undone

    def test_disagreeing_decision_starts_learning(self):
        made, real = [], httpd.corrections.create
        httpd.corrections.create = lambda decision, saved, ask=None: made.append(decision["reason"])
        self.addCleanup(setattr, httpd.corrections, "create", real)
        store.STORE.put("reads", "grainkind", dict(READ, id="grainkind", recommendation="NO-GO"))
        code, data = self.post("/api/decision", {"id": "grainkind", "call": "go", "reason": "Repeat rate is strong for a millet brand."})
        self.assertTrue(data["learning"])
        for _ in range(50):
            if made:
                break
            time.sleep(0.02)
        self.assertEqual(made, ["Repeat rate is strong for a millet brand."])
        code, data = self.post("/api/decision", {"id": "grainkind", "call": "nogo"})  # agreeing: nothing to learn
        self.assertFalse(data["learning"])


if __name__ == "__main__":
    unittest.main()
