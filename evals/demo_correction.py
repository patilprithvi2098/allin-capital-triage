"""Phase 4 proof: a correction learned from Riya's StockSathi disagreement changes the next similar read, and does not
touch an unrelated one. Talks to the app over HTTP like the harness. Run with the app up: python3 evals/demo_correction.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import App  # noqa: E402

SIMILAR = {"company": "Dukaan Setu", "sector_label": "Consumer tech", "stage": "Pre-seed", "raise": "INR 1.6 Cr",
           "deck_text": ("Dukaan Setu: next-day restocking for small-town general stores in Vidarbha. Owners order by voice in Marathi; partner "
                         "distributors deliver next morning. Traction: 57 stores onboarded in 5 months, 31 reorder every week, GMV INR 4.1 L in "
                         "September. Go-to-market: two field agents and the founders visit stores; 41 of 57 came through field visits. Blended "
                         "CAC INR 2,640 in September, counting the founders' own visit days at market salary. Team: Snehal Wankhede (CEO), 9 "
                         "years in FMCG distribution at a regional stockist; Kunal Bhoyar (CTO), 4 years building ordering software. Ask: INR 1.6 Cr "
                         "for 250 stores in 12 months."),
           "form_text": ("One-line description Voice-first restocking app for small-town general stores Sector (as selected) Consumer tech "
                         "Stage (as selected) Pre-seed Founders Founder 1 Snehal Wankhede, CEO Background: nine years in FMCG distribution at a "
                         "regional stockist. Founder 2 Kunal Bhoyar, CTO Background: four years building ordering software. Customers 57 stores "
                         "onboarded, 31 reorder weekly. Customer acquisition Field agents and founder visits. Our CAC is about INR 1,500 per "
                         "store (field agent cost only). Revenue Trade margin of about 4 percent. Amount raising INR 1.6 Cr Location Nagpur, "
                         "Maharashtra")}
UNRELATED = {"company": "Orbitra Labs", "sector_label": "Deeptech", "stage": "Seed", "raise": "INR 4 Cr",
             "deck_text": ("Orbitra Labs builds hyperspectral cameras for crop disease detection from drones. Two pilots with sugar mills in "
                           "Kolhapur; 1,840 acres scanned. Team: Dr. Meera Kulkarni (CEO), PhD optics; Ashwin Rao (CTO), 6 years in embedded "
                           "vision. Ask: INR 4 Cr for 10 paid pilots."),
             "form_text": ("One-line description Hyperspectral drone cameras for crop disease Sector (as selected) Deeptech Stage (as selected) "
                           "Seed Founders Founder 1 Meera Kulkarni, CEO Background: PhD in optics. Founder 2 Ashwin Rao, CTO Background: six years "
                           "in embedded vision. Customers 2 pilots with sugar mills. Amount raising INR 4 Cr Location Pune, Maharashtra")}


def main():
    app = App()
    out = app.eval("read", SIMILAR)
    print("SIMILAR (%s): %s %s/100" % (SIMILAR["company"], out["recommendation"], out["total"]))
    for a in out["corrections_applied"]:
        print("  Correction #%d applied: %s %+d  | %s" % (a["n"], a["criterion"], a["moved"], a["similar_because"][:160]))
    for c in out["criteria"]:
        if "points_before" in c:
            print("  %s: %s -> %s" % (c["key"], c["points_before"], c["points"]))
    print("  differences:", [(f["key"], f["status"]) for f in out["facts"] if f["status"] == "differs"])
    other = app.eval("read", UNRELATED)
    print("UNRELATED (%s): %s %s/100, corrections applied: %s" % (UNRELATED["company"], other["recommendation"], other["total"], other["corrections_applied"]))
    ok = bool(out["corrections_applied"]) and not other["corrections_applied"]
    Path(__file__).resolve().parent.joinpath("results", "phase4_demo.json").write_text(json.dumps({"similar": out, "unrelated": other, "ok": ok}, indent=1))
    print("PROOF:", "pass" if ok else "FAIL")


if __name__ == "__main__":
    main()
