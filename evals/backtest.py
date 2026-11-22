"""Backtest on the past deal memos.
1. prepare: each memo becomes a blind application (facts only: no decision, partner opinion, risks or reasoning), with a
   code check for leak words. Saved to evals/backtest/applications.json for a person to inspect.
2. run (over HTTP, like the harness): read all 12; choose the benchmark on the 6 BUILD memos (the score that best
   separates invested from passed), then measure it on the 6 HELD-OUT memos, which the thesis never saw.
Run: python3 evals/backtest.py prepare   then   python3 evals/backtest.py run     (about USD 0.60 in all)"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "evals" / "backtest"
sys.path.insert(0, str(ROOT / "evals"))
LEAK = re.compile(r"\b(invest(ed|ment)?|pass(ed)?|why we|our read|we would|decision|term sheet|backed|cheque|portfolio|concern|risk)\b", re.I)
SECTOR = [("deeptech", "Deeptech"), ("fintech", "Fintech"), ("consumer brand", "Consumer brands"), ("consumer tech", "Consumer tech")]


def prepare():
    sys.path.insert(0, str(ROOT / "app"))
    import checks
    checks.load_env()
    import claude
    import thesis
    schema = {"type": "object", "additionalProperties": False, "required": ["one_liner", "deck_text", "founders"], "properties": {
        "one_liner": {"type": "string"}, "deck_text": {"type": "string"},
        "founders": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["name", "role", "background"],
                                                "properties": {"name": {"type": "string"}, "role": {"type": "string"}, "background": {"type": "string"}}}}}}
    system = ("You turn an investor's internal memo into the application the founders would have sent before any meeting. Keep only facts the "
              "founders could state: what the company does, product, customers and numbers, team names, roles, years and past jobs. Remove every "
              "opinion, assessment, risk, concern, comparison and anything about the investor's decision, call, cheque or reasoning. Write deck_text "
              "as 80 to 150 words of plain slide text. Never use the words invest, pass, decision, portfolio, cheque, risk or concern.")
    apps = []
    for n, m in sorted(thesis.memos().items()):
        head = re.search(r"Sector: (.*?) \| Stage: (.*?) \| Source: (.*?) \| Decision", m["text"])
        sector_raw, stage_raw, source = head.groups()
        sector = next((lab for k, lab in SECTOR if k in sector_raw.lower()), "Other (%s)" % sector_raw.split(" (")[0])
        stage = "Seed" if stage_raw == "Early round" else stage_raw
        body = re.sub(r"\| Decision: \w+", "", m["text"])
        body = body.split("Why we")[0]  # the reasoning section never reaches the model
        got = claude.ask_json(claude.HAIKU, system, "<memo>\n%s\n</memo>" % body, schema, effort="low")
        founders = " ".join("Founder %d %s, %s Background: %s." % (i + 1, f["name"], f["role"], f["background"]) for i, f in enumerate(got["founders"]))
        form = ("One-line description %s Sector (as selected) %s Stage (as selected) %s Founders %s How did you hear about us? %s"
                % (got["one_liner"], sector, stage, founders, source))
        leaks = sorted({w.lower() for w in LEAK.findall(got["deck_text"] + " " + form)} if False else
                       {mm.group(0).lower() for mm in LEAK.finditer(got["deck_text"] + " " + form)})
        apps.append({"memo": n, "company": m["name"], "actual": m["decision"], "set": "build" if n in thesis.BUILD else "held_out",
                     "input": {"company": m["name"], "sector_label": sector, "stage": stage, "raise": "", "source": source,
                               "deck_text": got["deck_text"], "form_text": form, "exclude_portfolio": [m["name"], m["name"].replace("The ", "").replace(" Company", "")]},
                     "leak_words": leaks})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "applications.json").write_text(json.dumps(apps, indent=1, ensure_ascii=False))
    print("prepared %d; leak words found in: %s; USD %.3f" % (len(apps), [a["company"] for a in apps if a["leak_words"]] or "none", claude.spent["usd"]))


def best_threshold(rows):
    """The benchmark that agrees with the most past decisions; ties go to the middle of the tied range."""
    scores = sorted({r["total"] for r in rows})
    cands = sorted(set(scores + [s + 1 for s in scores]))
    agree = lambda t: sum((r["total"] >= t and not r["gates"]) == (r["actual"] == "INVESTED") for r in rows)  # noqa: E731
    top = max(agree(t) for t in cands)
    tied = [t for t in cands if agree(t) == top]
    return tied[len(tied) // 2], top


def run():
    from harness import App
    apps = json.loads((OUT / "applications.json").read_text())
    app = App()
    rows = []
    for a in apps:
        out = app.eval("read", a["input"])
        rows.append({k: a[k] for k in ("memo", "company", "actual", "set", "leak_words")} |
                    {"total": out["total"], "gates": out["gates"], "confidence": out["confidence"],
                     "criteria": {c["key"]: c["points"] for c in out["criteria"]}, "thesis_version": out["thesis_version"]})
        print(a["company"], a["actual"], out["total"], out["gates"])
    build = [r for r in rows if r["set"] == "build"]
    held = [r for r in rows if r["set"] == "held_out"]
    bench, build_agree = best_threshold(build)
    for r in rows:
        r["call"] = "GO" if r["total"] >= bench and not r["gates"] else "NO-GO"
        r["agrees"] = (r["call"] == "GO") == (r["actual"] == "INVESTED")
    result = {"benchmark": bench, "tuned_on": "6 build memos", "build_agree": "%d of %d" % (build_agree, len(build)),
              "held_out_agree": "%d of %d" % (sum(r["agrees"] for r in held), len(held)),
              "held_out_invested_caught": "%d of %d" % (sum(r["agrees"] for r in held if r["actual"] == "INVESTED"), sum(r["actual"] == "INVESTED" for r in held)),
              "held_out_passed_caught": "%d of %d" % (sum(r["agrees"] for r in held if r["actual"] == "PASSED"), sum(r["actual"] == "PASSED" for r in held)),
              "leak_check": "Each application was rewritten from its memo with the decision, partner opinions, risks and reasoning removed, then checked in code for words like invested, passed, decision, portfolio, cheque and risk; none were found.",
              "caveats": ["6 held-out cases is far too few to trust a rate; read these as counts, not percentages.",
                          "Memos were written after the call, so even with opinions removed the facts chosen can carry the verdict.",
                          "The 6 invested companies are now public and in the portfolio; web search stayed off and each was excluded from its own overlap check.",
                          "The passes are survivorship-skewed: we only see companies that reached a memo."],
              "rows": rows}
    (OUT / "result.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print({k: v for k, v in result.items() if k not in ("rows", "caveats", "leak_check")})


if __name__ == "__main__":
    {"prepare": prepare, "run": run}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
