"""What the eval harness calls over HTTP (POST /api/eval): one decision point at a time, on test input.
Nothing here saves a read or a decision. Web search stays off unless a case asks for it (dummy companies are unfindable)."""
import read
import tavily

NO_SEARCH = lambda a: ([], [{"field": "company", "query": None, "stop_reason": "off for evals"}])  # noqa: E731
APP_FIELDS = ("company", "sector_label", "stage", "raise", "deck_text", "form_text")


def _app(inp):
    if not all(isinstance(inp.get(k), str) for k in APP_FIELDS):
        raise ValueError("input needs %s as text" % ", ".join(APP_FIELDS))
    return dict({k: inp[k] for k in APP_FIELDS}, id="eval", source=inp.get("source", "Public application form."))


def _scored(inp):
    """A model answer supplied by the test, so the code rules are tested without a model call."""
    base = {k: m for k, m in read.MAX.items()}
    crit = []
    for key, mx in base.items():
        c = (inp.get("criteria") or {}).get(key, {})
        crit.append({"key": key, "points": c.get("points", mx), "confidence": c.get("confidence", "high"), "why": "test",
                     "claims": c.get("claims", []), "missing": c.get("missing", [])})
    if inp.get("drop_criterion"):
        crit = [c for c in crit if c["key"] != inp["drop_criterion"]]
    return {"criteria": crit, "differences": [], "why_yes": [], "why_no": [], "injection_seen": False}


def run(point, inp):
    if point == "compare":
        return {"status": read.compare(inp.get("deck", ""), inp.get("form", ""), inp.get("key", ""))}
    if point == "gates":
        app = {"stage": inp.get("stage", ""), "sector_label": inp.get("sector_label", ""), "raise": inp.get("raise", "")}
        app["form_text"] = "Sector (as selected) %s Stage (as selected) %s Amount raising %s" % (app["sector_label"], app["stage"], app["raise"])
        return {"gates": [g["gate"] for g in read.gates(app)]}
    if point == "verify":
        app = {"deck_text": inp.get("deck_text", ""), "form_text": inp.get("form_text", "")}
        return {"kept": read.verify(inp["claim"], app, inp.get("evidence", []))}
    if point == "rules":
        app = {"deck_text": inp.get("deck_text", ""), "form_text": inp.get("form_text", "")}
        crit, dropped = read.apply_rules(_scored(inp), app, inp.get("evidence", []))
        return {"criteria": crit, "dropped": dropped}
    if point == "recommend":
        total, b = inp["total"], read.THESIS["benchmark"]
        if isinstance(total, str):  # "B", "B-1", "B+1": relative to whatever the benchmark is now
            total = b + int(total[1:] or 0)
        return {"recommendation": read.recommend(total, [{"gate": g} for g in inp.get("gates", [])]), "benchmark": b}
    if point == "search_rule":  # does this search result count as being about the company or founder?
        return {"counts": tavily.about(inp["result"], inp["field"])}
    if point == "apply_corrections":  # the code rules: cap, bounds, conflict
        crit, applied = read.corrections.apply(inp["criteria"], inp["matches"])
        return {"criteria": crit, "applied": [a["n"] for a in applied]}
    if point == "correction_worth":  # would this disagreement become a reusable correction?
        out = read.claude.ask_json(read.claude.SONNET, read.corrections.WORTH_SYSTEM,
              "Company: %s. What it does: %s\nTool recommended %s.\nAssociate's call: %s\n<reason>%s</reason>" % (
                  inp["company"], inp["what_it_does"], inp["tool"], inp["call"], inp["reason"]), read.corrections.WORTH_SCHEMA, effort="low")
        return {"worth_storing": out["worth_storing"], "criterion": out["criterion"], "direction": out["direction"]}
    if point == "correction_match":  # does a given correction apply to this application?
        c = dict(inp["correction"], n=1, worth_storing=True, rejected_by=[], **{"from": "elsewhere"})
        out = read.claude.ask_json(read.claude.SONNET, read.corrections.MATCH_SYSTEM,
                                   "Corrections:\n#1 [%s]: %s Applies when: %s\n\n<form>\n%s\n</form>" % (c["criterion"], c["lesson"], c["applies_when"], inp["form_text"]),
                                   read.corrections.MATCH_SCHEMA, effort="low")
        m = next((x for x in out["matches"] if x["id"] == 1), {"applies": False, "similar_because": ""})
        return {"applies": m["applies"], "why": m["similar_because"]}
    if point == "overlap_verdict":
        return read.overlap_verdict(inp["candidates"])
    if point == "overlap":
        app = _app(inp)
        cands = read.overlap_check(app)
        return dict(read.overlap_verdict(cands), candidates=cands)
    if point == "facts":
        return {"facts": read.extract_facts(_app(inp))}
    if point == "read":
        app = _app(inp)
        skip = [x for x in inp.get("exclude_portfolio", []) if isinstance(x, str)]
        return read.run_app(app, gather=tavily.gather if inp.get("search") else NO_SEARCH,
                            overlaps=lambda a: read.overlap_check(a, exclude=skip),
                            learned=(lambda a: []) if inp.get("no_corrections") else read.corrections.relevant)
    raise ValueError("unknown decision point")
