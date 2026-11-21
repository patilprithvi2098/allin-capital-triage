"""Phase 2 eval cases (lecture 7 format) over the saved reads of the last whole-batch run, plus code checks.
Run after "Read all 10": python3 evals/run_phase2.py   (free: reads what is saved). Results: evals/results/phase2.md"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))
import checks  # noqa: E402

checks.load_env()
import case  # noqa: E402
import read  # noqa: E402
import thesis  # noqa: E402
from store import STORE  # noqa: E402

APPS = {a["id"]: a for a in case.applications()}
R = {r["id"]: r for r in STORE.all("reads")}


def quotes_real(r):
    app = APPS[r["id"]]
    claims = [x for c in r["criteria"] for x in c["claims"]] + r["why_yes"] + [x for x in r["why_no"] if x["source"] in ("deck", "form", "web")]
    return all(read.verify(x, app, r["evidence"]) for x in claims)


CASES = [
    ("P2-01", "portfolio overlap (K1)", "Talkbook (AI call summaries and CRM updates); MeetRecord in the portfolio; application never names it",
     "NO-GO with the MeetRecord overlap as a gate quoting the fund's portfolio line", "hard", "Critical",
     lambda: R["talkbook"]["recommendation"] == "NO-GO" and "portfolio overlap" in R["talkbook"]["gates"]
     and any(x.get("gate") == "portfolio overlap" and "MeetRecord" in x["quote"] for x in R["talkbook"]["why_no"])),
    ("P2-02", "gates", "Settlr, Series A, INR 30 Cr", "NO-GO; stage reason first, cheque reason also shown", "hard", "High",
     lambda: R["settlr"]["recommendation"] == "NO-GO" and R["settlr"]["why_no"][0].get("gate") == "stage" and "cheque size" in R["settlr"]["gates"]),
    ("P2-03", "gates", "CareCorner, Other (Healthcare)", "NO-GO with the outside-the-areas reason", "hard", "High",
     lambda: R["carecorner"]["recommendation"] == "NO-GO" and "outside the areas" in R["carecorner"]["gates"]),
    ("P2-04", "whole batch", "Read all 10 in one run", "10 saved reads, each with a recommendation", "hard", "High",
     lambda: set(R) >= set(APPS) and all(R[k]["recommendation"] in ("GO", "NO-GO") for k in APPS)),
    ("P2-05", "thesis versions", "Batch run after Kushal approved v1", "every read states it used v1", "hard", "High",
     lambda: all(R[k]["thesis_version"] == thesis.current()["version"] == "v1" for k in APPS)),
    ("P2-06", "source check (K2)", "All 10 saved reads", "every deck, form and web quote is found in its source", "hard", "Critical",
     lambda: all(quotes_real(R[k]) for k in APPS)),
    ("P2-07", "overlap false alarm", "The 9 applicants other than Talkbook", "no portfolio-overlap gate", "soft", "Low",
     lambda: all("portfolio overlap" not in R[k]["gates"] for k in APPS if k != "talkbook")),
    ("P2-08", "partial portfolio", "Every saved read", "states the portfolio list is partial", "hard", "High",
     lambda: all("65 to 80" in R[k].get("portfolio_note", "") for k in APPS)),
    ("P2-09", "hold-out (leak)", "The thesis built from memos", "built only from the 6 build memos; none of the 6 held-out memos", "hard", "Critical",
     lambda: set(thesis.current()["built_from"]) == set(thesis.BUILD.values()) and not set(thesis.current()["built_from"]) & set(thesis.HELD_OUT.values())),
    ("P2-10", "approval", "Thesis v1", "approved by Kushal before reads used it", "hard", "High",
     lambda: thesis.current()["status"] == "approved" and thesis.current()["approved_by"].startswith("kushal")),
]


def main():
    rows, failed = [], 0
    for cid, point, inp, exp, kind, sev, check in CASES:
        try:
            ok = bool(check())
        except Exception as e:
            ok = False
            print(cid, "error", type(e).__name__, e)
        failed += not ok
        rows.append((cid, point, inp, exp, kind, sev, "pass" if ok else "FAIL"))
        print(cid, "pass" if ok else "FAIL")
    out = ROOT / "evals" / "results"
    out.mkdir(parents=True, exist_ok=True)
    lines = ["# Phase 2 eval results (%s)" % time.strftime("%Y-%m-%d %H:%M"), "",
             "Checks the saved reads of the last whole-batch run. Overlap stability, measured separately: Talkbook flagged against MeetRecord 3 of 3 runs.", "",
             "| ID | Decision point | Input | Expected | Assertion | Severity | Result |", "|---|---|---|---|---|---|---|"]
    lines += ["| %s |" % " | ".join(r) for r in rows]
    (out / "phase2.md").write_text("\n".join(lines) + "\n")
    print("%d failed of %d" % (failed, len(rows)))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
