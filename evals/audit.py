"""Blind human audit (lecture 7): a person grades a random 5 to 10 percent of the last run without seeing the harness's
verdict. Every disagreement with the harness or the judge is logged. Run in a terminal: python3 evals/audit.py"""
import json
import random
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "evals" / "results"


def show(r):
    inp = r["input"]
    print("\n" + "=" * 72)
    print("%s · %s · %s" % (r["id"], r["point"], r["partition"]))
    if "deck_text" in inp:
        print("Company: %s (%s, %s)" % (inp.get("company"), inp.get("sector_label"), inp.get("stage")))
        print(textwrap.fill("Form: " + inp.get("form_text", "")[:500], 100))
    else:
        print("Input: " + json.dumps(inp, ensure_ascii=False)[:500])
    print("Expected: " + r["expected"])
    out = r.get("full_output") or r.get("output") or {}
    brief = {k: out.get(k) for k in ("recommendation", "total", "gates", "verdict", "company", "status", "kept", "injection_seen", "counts") if k in out}
    print("Tool output: " + json.dumps(brief, ensure_ascii=False))
    if r["point"] == "read":
        for c in out.get("criteria", []):
            print("  %s %s/%s: %s" % (c["key"], c["points"], c["max"], c["why"][:140]))
        if r.get("assertion", {}).get("rubric"):
            print("Rubric: " + " | ".join(r["assertion"]["rubric"]))


def main():
    run = json.loads((RES / "latest.json").read_text())
    pool = [r for r in run["results"] if r["result"] in ("pass", "fail")]
    rng = random.Random(run["run_at"])
    ai = [r for r in pool if r["point"] in ("read", "overlap", "facts")]
    code = [r for r in pool if r not in ai]
    sample = rng.sample(ai, min(len(ai), max(3, round(len(ai) * 0.15)))) + rng.sample(code, min(len(code), max(2, round(len(code) * 0.05))))
    print("Grade %d results (about %d%% of %d). Type p if the tool's output is right for the expected behaviour, f if not, s to skip."
          % (len(sample), round(100 * len(sample) / len(pool)), len(pool)))
    graded = []
    for r in sample:
        show(r)
        ans = ""
        while ans not in ("p", "f", "s"):
            ans = input("Your grade [p/f/s]: ").strip().lower()[:1]
        if ans == "s":
            continue
        human = ans == "p"
        judge = r.get("judge", {}).get("pass") if isinstance(r.get("judge"), dict) else None
        graded.append({"id": r["id"], "point": r["point"], "human_pass": human, "harness_pass": r["result"] == "pass", "judge_pass": judge})
    judged = [g for g in graded if g["judge_pass"] is not None]
    out = {"run_at": run["run_at"], "graded": len(graded), "of": len(pool),
           "harness_agree": sum(g["human_pass"] == g["harness_pass"] for g in graded),
           "compared": len(judged), "agree": sum(g["human_pass"] == g["judge_pass"] for g in judged),
           "mismatches": [g for g in graded if g["human_pass"] != g["harness_pass"] or (g["judge_pass"] is not None and g["human_pass"] != g["judge_pass"])],
           "rows": graded}
    (RES / "audit.json").write_text(json.dumps(out, indent=1))
    print("\nSaved. You agreed with the harness on %d of %d; with the judge on %d of %d. Mismatches: %d."
          % (out["harness_agree"], len(graded), out["agree"], len(judged), len(out["mismatches"])))


if __name__ == "__main__":
    main()
