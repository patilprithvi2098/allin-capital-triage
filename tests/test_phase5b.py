"""Phase 5b: Kushal's portfolio. Health rules (each band and boundary), fictional names only, money that adds up."""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

import portfolio  # noqa: E402

H = portfolio.health
OK = dict(runway_months=18, growth_3m=20, days_since_update=10, burn_to_revenue=1)


def band(**kw):
    return H(**dict(OK, **kw))[0]


class Health(unittest.TestCase):
    def test_healthy(self):
        self.assertEqual(band(), "Healthy")

    def test_runway_boundaries(self):
        self.assertEqual([band(runway_months=x) for x in (5.9, 6, 11.9, 12)], ["At risk", "Watch", "Watch", "Healthy"])

    def test_update_boundaries(self):
        self.assertEqual([band(days_since_update=x) for x in (30, 31, 60, 61)], ["Healthy", "Watch", "Watch", "At risk"])

    def test_growth_boundaries(self):
        self.assertEqual([band(growth_3m=x) for x in (5, 4.9, -10, -10.1)], ["Healthy", "Watch", "Watch", "At risk"])

    def test_burn_boundary(self):
        self.assertEqual([band(burn_to_revenue=x) for x in (3, 3.1)], ["Healthy", "Watch"])

    def test_at_risk_wins_and_names_every_reason(self):
        b, reasons = H(runway_months=3, growth_3m=-20, days_since_update=90, burn_to_revenue=9)
        self.assertEqual((b, len(reasons)), ("At risk", 3))
        self.assertIn("Runway 3.0 months (under 6)", reasons)


class Data(unittest.TestCase):
    def test_names_are_fictional(self):
        real = {c["company"].lower() for c in json.loads((ROOT / "case" / "portfolio.json").read_text())["companies"]}
        apps = {a["company"].lower() for a in json.loads((ROOT / "case" / "applications.json").read_text())}
        names = {c["name"].lower() for c in portfolio.SEED["companies"]}
        self.assertFalse(names & real, "a fictional company shares a name with the real portfolio")
        self.assertFalse(names & apps)
        self.assertIn("Invented figures", portfolio.SEED["note"])

    def test_money_adds_up_to_the_public_commitment(self):
        v = portfolio.view(date(2026, 11, 24))
        m, f = v["money"], portfolio.SEED["fund"]
        self.assertAlmostEqual(m["invested_cr"] + m["cash_cr"] + m["incoming_cr"] + f["fees_cr"], portfolio.SEED["public"]["committed_cr"], places=1)
        self.assertGreater(m["incoming_cr"], 0)
        self.assertAlmostEqual(m["free_cr"], m["cash_cr"] + m["incoming_cr"] - m["reserve_cr"], places=1)

    def test_donut_is_top_five_plus_other(self):
        s = portfolio.view(date(2026, 11, 24))["sectors"]
        self.assertLessEqual(len(s), 6)
        self.assertEqual(s[-1]["sector"], "Other")
        self.assertAlmostEqual(sum(x["share"] for x in s), 100, delta=0.5)

    def test_simulator_moves_with_time_but_not_on_reload(self):
        a, b = portfolio.view(date(2026, 11, 24)), portfolio.view(date(2026, 11, 24))
        self.assertEqual(a, b)
        later = portfolio.view(date(2027, 1, 15))
        self.assertNotEqual([c["runway_months"] for c in a["companies"]], [c["runway_months"] for c in later["companies"]])
        self.assertTrue(all(c["runway_months"] >= 0 for c in portfolio.view(date(2030, 1, 1))["companies"]))

    def test_every_band_appears_today(self):
        self.assertTrue(all(portfolio.view(date(2026, 11, 24))["counts"].values()))


if __name__ == "__main__":
    unittest.main()
