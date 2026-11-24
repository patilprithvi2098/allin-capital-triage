"""Decision tables for the decision points checked in code, one case per equivalence partition (lecture 7 format).
Writes evals/cases/<point>.json. Run: python3 evals/make_code_cases.py"""
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "evals" / "cases"
APPS = {a["id"]: a for a in json.loads((ROOT / "case" / "applications.json").read_text())}
SS, GK = APPS["stocksathi"], APPS["grainkind"]
CASES = []


def case(point, partition, inp, expected, check, severity, kill=None):
    CASES.append({"id": "%s-%03d" % (point.upper().replace("_", ""), sum(c["point"] == point for c in CASES) + 1), "point": point,
                  "partition": partition, "input": inp, "expected": expected,
                  "assertion": {"kind": "hard", "check": check}, "severity": severity, "kill": kill})


eq = lambda path, value: {"op": "equals", "path": path, "value": value}  # noqa: E731

# ---------- deck vs form comparison
for part, key, d, f, want, sev in [
    ("same count", "customers", "38 retailers onboarded", "38 retailers", "matches", "Low"),
    ("count differs over 5%", "customers", "38 retailers onboarded", "42 retailers onboarded", "differs", "High"),
    ("count within 5%", "customers", "100 stores", "103 stores", "matches", "High"),
    ("count just over 5%", "customers", "100 stores", "106 stores", "differs", "High"),
    ("lakh vs number", "revenue", "INR 3.8 L in October", "INR 380,000 in October", "matches", "High"),
    ("lakh vs crore same", "raise", "INR 0.5 Cr", "INR 50 lakh", "matches", "High"),
    ("crore differs", "raise", "INR 2 Cr", "INR 3 Cr", "differs", "High"),
    ("thousands with K", "cac", "INR 2K", "INR 2,000", "matches", "Low"),
    ("under-bound vs exact higher", "cac", "INR 2,860 blended CAC, October", "Under INR 2,000 per store", "differs", "Critical"),
    ("different periods", "revenue", "INR 3.8 L GMV in October", "INR 9 lakh in the last three months", "different periods", "High"),
    ("same period differs", "revenue", "INR 4 L monthly revenue", "INR 6 L monthly revenue", "differs", "High"),
    ("monthly vs annual", "revenue", "INR 10 L monthly", "INR 1.2 Cr annual", "different periods", "High"),
    ("only in deck", "valuation", "INR 12 Cr post-money", "", "only in deck", "Low"),
    ("only in form", "valuation", "", "INR 12 Cr post-money", "only in form", "Low"),
    ("neither", "valuation", "", "", None, "Low"),
    ("city vs city and state", "location", "Hyderabad", "Hyderabad, Telangana", "matches", "Low"),
    ("different cities", "location", "Pune", "Bengaluru", "differs", "High"),
    ("text contradiction", "funding_of_credit", "Funded from our own capital", "Provided through our NBFC partner", "differs", "Critical"),
    ("same text different case", "funding_of_credit", "Own capital", "own capital", "matches", "Low"),
    ("rupee symbol vs INR", "raise", "₹2 Cr", "INR 2 Cr", "matches", "Low"),
    ("decimal crore", "valuation", "INR 12.5 Cr", "INR 12 Cr", "matches", "High"),
    ("decimal crore differs", "valuation", "INR 15 Cr", "INR 12 Cr", "differs", "High"),
    ("team size words", "team_size", "4 people", "4 (2 founders, 2 field agents)", "matches", "Low"),
    ("team size differs", "team_size", "6 people", "4 (2 founders, 2 field agents)", "differs", "High"),
    ("repeat as fraction", "repeat_customers", "22 of 38", "22 of whom have ordered more than once", "matches", "Low"),
    ("repeat differs", "repeat_customers", "30 of 38", "22 of whom have ordered more than once", "differs", "High"),
    ("percent same", "repeat_customers", "41% repeat", "41 percent repeat", "matches", "Low"),
    ("percent differs", "repeat_customers", "41% repeat", "25% repeat", "differs", "High"),
    ("million vs lakh", "revenue", "INR 1 M monthly", "INR 10 lakh monthly", "matches", "High"),
]:
    case("compare", part, {"key": key, "deck": d, "form": f}, "status: %s" % want, eq("status", want), sev)

# ---------- gates (stage, sector label, round size)
for part, stage, sector, rais, want, sev in [
    ("pre-seed fintech small", "Pre-seed", "Fintech", "INR 2 Cr", [], "Low"),
    ("seed deeptech", "Seed", "Deeptech", "INR 5 Cr", [], "Low"),
    ("consumer brands", "Pre-seed", "Consumer brands", "INR 2.5 Cr", [], "Low"),
    ("consumer tech", "Pre-seed", "Consumer tech", "INR 1.2 Cr", [], "Low"),
    ("series A", "Series A", "Fintech", "INR 10 Cr", ["stage"], "Critical"),
    ("series B", "Series B", "Fintech", "INR 12 Cr", ["stage"], "Critical"),
    ("series A big round", "Series A", "Fintech", "INR 30 Cr", ["stage", "cheque size"], "Critical"),
    ("growth stage", "Growth", "Consumer tech", "INR 5 Cr", ["stage"], "High"),
    ("stage missing", "", "Fintech", "INR 2 Cr", ["stage"], "High"),
    ("healthcare", "Pre-seed", "Other (Healthcare)", "INR 3 Cr", ["outside the areas"], "Critical"),
    ("edtech", "Pre-seed", "Other (Edtech)", "INR 2 Cr", ["outside the areas"], "Critical"),
    ("B2B SaaS label", "Seed", "B2B SaaS", "INR 4 Cr", ["outside the areas"], "High"),
    ("sector missing", "Pre-seed", "", "INR 2 Cr", ["outside the areas"], "High"),
    ("round at limit", "Seed", "Fintech", "INR 15 Cr", [], "High"),
    ("round just over limit", "Seed", "Fintech", "INR 15.5 Cr", ["cheque size"], "High"),
    ("round in lakh", "Pre-seed", "Fintech", "INR 80 lakh", [], "Low"),
    ("round missing", "Pre-seed", "Fintech", "", [], "High"),
    ("every gate", "Series B", "Other (Healthcare)", "INR 40 Cr", ["stage", "outside the areas", "cheque size"], "Critical"),
    ("tiny round", "Pre-seed", "Deeptech", "INR 50 lakh", [], "Low"),
    ("seed big but allowed", "Seed", "Consumer brands", "INR 12 Cr", [], "Low"),
]:
    case("gates", part, {"stage": stage, "sector_label": sector, "raise": rais}, "gates: %s" % (want or "none"),
         {"op": "set_equals", "path": "gates", "value": want}, sev)

# ---------- source check (K2): a claim survives only if its quote is in the source it names
rng = random.Random(7)


def real_quote(text, words=8):
    w = text.split()
    i = rng.randrange(0, len(w) - words)
    return " ".join(w[i:i + words])


EV = [{"id": "E1", "title": "Kirana tech in Telangana", "url": "https://news.example/k", "content": "StockSathi works with stores in Karimnagar and plans two more towns."}]
for i in range(6):
    q = real_quote(SS["deck_text"])
    case("verify", "real deck quote %d" % (i + 1), {"deck_text": SS["deck_text"], "form_text": SS["form_text"], "claim": {"source": "deck", "quote": q, "evidence_id": ""}},
         "kept", eq("kept", True), "High", "K2")
for i in range(4):
    q = real_quote(SS["form_text"])
    case("verify", "real form quote %d" % (i + 1), {"deck_text": SS["deck_text"], "form_text": SS["form_text"], "claim": {"source": "form", "quote": q, "evidence_id": ""}},
         "kept", eq("kept", True), "High", "K2")
for part, src, quote, ev, want, sev in [
    ("quote across a line break", "deck", "losing half a day each time", "", True, "High"),
    ("quote in other case", "deck", "LOSING HALF A DAY EACH TIME", "", True, "Low"),
    ("number changed", "deck", "22 of 40 have ordered more than once", "", False, "Critical"),
    ("word inserted", "deck", "8 years in FMCG distribution and venture field operations", "", False, "Critical"),
    ("invented pedigree", "deck", "ex-McKinsey and IIT Bombay graduate", "", False, "Critical"),
    ("form quote cited as deck", "deck", "Not registered as an NBFC", "", False, "High"),
    ("deck quote cited as form", "form", "Order, get delivered, pay later", "", False, "High"),
    ("quote from another applicant", "deck", real_quote(GK["deck_text"]), "", False, "Critical"),
    ("too short", "deck", "a", "", False, "High"),
    ("empty quote", "form", "", "", False, "High"),
    ("unknown source kind", "linkedin", "8 years in FMCG distribution", "", False, "Critical"),
    ("web, right id and quote", "web", "works with stores in Karimnagar", "E1", True, "High"),
    ("web, id not fetched", "web", "works with stores in Karimnagar", "E4", False, "Critical"),
    ("web, quote not in result", "web", "StockSathi raised INR 10 Cr", "E1", False, "Critical"),
    ("web, no id", "web", "works with stores in Karimnagar", "", False, "Critical"),
    ("punctuation differs", "deck", "CAC = INR 40,000 field cost / 14 stores", "", True, "Low"),
    ("rupee symbol for INR", "deck", "₹2,860 blended CAC, October", "", True, "Low"),
]:
    case("verify", part, {"deck_text": SS["deck_text"], "form_text": SS["form_text"], "evidence": EV,
                          "claim": {"source": src, "quote": quote, "evidence_id": ev}}, "kept" if want else "dropped", eq("kept", want), sev, "K2")

# ---------- score rules: clamp, unsourced cap, unfindable cap (K3), founder-supplied, missing criterion
good = {"source": "form", "quote": "Both full-time since April 2026", "evidence_id": ""}
fake = {"source": "deck", "quote": "ex-Google engineer with two exits", "evidence_id": ""}
for part, crit, drop, check, exp, sev, kill in [
    ("full marks with a source", {"founder_quality": {"points": 25, "claims": [good]}}, None,
     eq("criteria.founder_quality.points", 25), "25 kept", "Low", None),
    ("over max", {"sector_fit": {"points": 40, "claims": [good]}}, None, eq("criteria.sector_fit.points", 10), "clamped to 10", "High", None),
    ("negative points", {"sector_fit": {"points": -5, "claims": [good]}}, None, eq("criteria.sector_fit.points", 0), "floored at 0", "High", None),
    ("no claims at all", {"path_to_market": {"points": 20, "claims": []}}, None, eq("criteria.path_to_market.points", 8), "capped at 8 (40%)", "High", None),
    ("only a fake claim", {"path_to_market": {"points": 20, "claims": [fake]}}, None, eq("criteria.path_to_market.points", 8), "fake dropped, capped at 8", "Critical", "K2"),
    ("fake claim counted as dropped", {"path_to_market": {"points": 20, "claims": [fake, good]}}, None, eq("dropped", 1), "1 dropped", "Critical", "K2"),
    ("unfindable fact", {"founder_quality": {"points": 25, "claims": [good], "missing": [{"item": "background", "kind": "unfindable"}]}}, None,
     eq("criteria.founder_quality.points", 17), "capped at 17, not zero", "Critical", "K3"),
    ("unfindable lowers confidence", {"founder_quality": {"points": 25, "confidence": "high", "claims": [good], "missing": [{"item": "background", "kind": "unfindable"}]}}, None,
     eq("criteria.founder_quality.confidence", "medium"), "confidence high to medium", "High", "K3"),
    ("unfindable never zeroes", {"founder_quality": {"points": 12, "claims": [good], "missing": [{"item": "background", "kind": "unfindable"}]}}, None,
     eq("criteria.founder_quality.points", 12), "12 kept (below the cap)", "Critical", "K3"),
    ("unfindable at low confidence stays low", {"founder_quality": {"points": 10, "confidence": "low", "claims": [good], "missing": [{"item": "x", "kind": "unfindable"}]}}, None,
     eq("criteria.founder_quality.confidence", "low"), "stays low", "Low", None),
    ("founder-supplied missing, model lowered it", {"evidence_quality": {"points": 9, "claims": [good], "missing": [{"item": "repeat rate", "kind": "founder_supplied"}]}}, None,
     eq("criteria.evidence_quality.points", 9), "model's lower score kept", "High", None),
    ("criterion missing from the answer", {}, "defensibility", eq("criteria.defensibility.points", 0), "scored 0 with a note, never full marks", "Critical", None),
    ("unsourced and unfindable", {"founder_quality": {"points": 25, "claims": [], "missing": [{"item": "x", "kind": "unfindable"}]}}, None,
     eq("criteria.founder_quality.points", 10), "both caps: 10", "High", "K3"),
]:
    inp = {"deck_text": SS["deck_text"], "form_text": SS["form_text"], "criteria": crit}
    if drop:
        inp["drop_criterion"] = drop
    case("rules", part, inp, exp, check, sev, kill)

# ---------- recommendation: benchmark boundary and gates (K6: never decides, only recommends)
for part, total, gates, want, sev in [
    ("zero", 0, [], "NO-GO", "Low"), ("one below benchmark", "B-1", [], "NO-GO", "Critical"), ("at benchmark", "B", [], "GO", "Critical"),
    ("one above", "B+1", [], "GO", "High"), ("full marks", 100, [], "GO", "Low"), ("full marks, stage gate", 100, ["stage"], "NO-GO", "Critical"),
    ("full marks, overlap", 100, ["portfolio overlap"], "NO-GO", "Critical"), ("at benchmark, sector gate", "B", ["outside the areas"], "NO-GO", "Critical"),
    ("two gates", 90, ["stage", "cheque size"], "NO-GO", "High"),
]:
    case("recommend", part, {"total": total, "gates": gates}, want, eq("recommendation", want), sev, "K6" if gates else None)

# ---------- overlap rules (K1): code turns the three answers into a verdict
c = lambda n, p, b, w: {"company": n, "same_problem": p, "same_buyer": b, "same_workflow": w, "reason": "r"}  # noqa: E731
for part, cands, want, sev in [
    ("problem and buyer", [c("MeetRecord", True, True, False)], "overlap", "Critical"),
    ("problem and workflow", [c("MeetRecord", True, False, True)], "overlap", "Critical"),
    ("all three", [c("MeetRecord", True, True, True)], "overlap", "Critical"),
    ("problem only", [c("MeetRecord", True, False, False)], "none", "High"),
    ("buyer and workflow", [c("Mailmodo", False, True, True)], "adjacent", "High"),
    ("buyer only", [c("Jai Kisan", False, True, False)], "none", "Low"),
    ("workflow only", [c("Rocketlane", False, False, True)], "none", "Low"),
    ("nothing shared", [c("Giva", False, False, False)], "none", "Low"),
    ("company not on the list", [c("Gong", True, True, True)], "none", "High"),
    ("name in other case", [c("meetrecord", True, True, False)], "overlap", "Critical"),
    ("adjacent listed first, overlap second", [c("Mailmodo", False, True, True), c("MeetRecord", True, True, False)], "overlap", "Critical"),
    ("no candidates", [], "none", "Low"),
]:
    case("overlap_verdict", part, {"candidates": cands}, want, eq("verdict", want), sev, "K1" if want == "overlap" else None)

# ---------- more comparison partitions: renamed cities, numbers in words
for part, key, d, f, want, sev in [
    ("Bangalore vs Bengaluru", "location", "Bengaluru, Karnataka", "Bangalore, KA", "matches", "High"),
    ("Bombay vs Mumbai", "location", "Bombay", "Mumbai, Maharashtra", "matches", "High"),
    ("Gurgaon vs Gurugram", "location", "Gurgaon, Haryana", "Gurugram", "matches", "High"),
    ("same state different city", "location", "Pune, Maharashtra", "Nagpur, Maharashtra", "differs", "High"),
    ("number in words matches", "customers", "42 customers", "forty two", "matches", "High"),
    ("hyphenated words", "customers", "25 stores", "twenty-five stores", "matches", "High"),
    ("hundreds in words", "customers", "312 stores", "three hundred and twelve stores", "matches", "High"),
    ("words differ", "team_size", "15", "twelve", "differs", "High"),
    ("thousand in words", "customers", "2,000 users", "two thousand users", "matches", "Low"),
]:
    case("compare", part, {"key": key, "deck": d, "form": f}, "status: %s" % want, eq("status", want), sev)

# ---------- gates: stage written differently by founders
for part, stage, want, sev in [
    ("lower case pre-seed", "pre-seed", [], "Critical"), ("pre seed with a space", "Pre seed", [], "Critical"),
    ("preseed one word", "Preseed", [], "High"), ("seed round", "Seed round", [], "High"), ("upper case SEED", "SEED", [], "High"),
    ("pre-series A", "Pre-Series A", ["stage"], "High"), ("series a lower case", "series a", ["stage"], "Critical"),
]:
    case("gates", part, {"stage": stage, "sector_label": "Fintech", "raise": "INR 2 Cr"}, "gates: %s" % (want or "none"),
         {"op": "set_equals", "path": "gates", "value": want}, sev)
for part, sector, want, sev in [("lower case fintech", "fintech", [], "Critical"), ("deep tech with a space", "Deep tech", [], "High"),
                                ("consumer-brands hyphen", "Consumer-brands", [], "High"), ("healthtech", "HealthTech", ["outside the areas"], "Critical")]:
    case("gates", part, {"stage": "Pre-seed", "sector_label": sector, "raise": "INR 2 Cr"}, "gates: %s" % (want or "none"),
         {"op": "set_equals", "path": "gates", "value": want}, sev)

# ---------- search stop rule: a result counts only if it is about this company or founder (namesakes never count)
F = {"target": "Aarav Deshmukh", "also": ["StockSathi"]}
C = {"target": "StockSathi", "also": ["Aarav Deshmukh", "Pooja Nair", "Hyderabad"]}
for part, field, title, content, want, sev in [
    ("founder and company named", F, "StockSathi founder Aarav Deshmukh on kirana credit", "", True, "High"),
    ("namesake doctor", F, "Dr. Aarav Deshmukh, orthopaedic surgeon", "Consultant at a Pune hospital.", False, "Critical"),
    ("namesake author", F, "Aarav Deshmukh, Author at Impressive Magazine", "Lifestyle writer.", False, "Critical"),
    ("company named only in content", F, "Kirana tech in Telangana", "Aarav Deshmukh started StockSathi in 2026.", True, "High"),
    ("company only, founder missing", F, "StockSathi raises angel round", "The Hyderabad startup", False, "High"),
    ("name split across words", F, "Aarav and Deshmukh families", "StockSathi", False, "Low"),
    ("company with its city", C, "StockSathi expands in Hyderabad", "", True, "High"),
    ("company with a founder", C, "Pooja Nair builds StockSathi", "", True, "High"),
    ("company name inside another word", C, "StockSathiPro trading signals", "Hyderabad", False, "High"),
    ("stock tips namesake", C, "StockSathi: daily stock tips", "Share market videos", False, "Critical"),
    ("case differs", C, "STOCKSATHI in HYDERABAD", "", True, "Low"),
    ("nothing named", C, "Kirana stores adopt UPI", "Small towns", False, "Low"),
]:
    case("search_rule", part, {"field": field, "result": {"title": title, "content": content}}, "counts" if want else "does not count",
         eq("counts", want), sev, "K3" if not want and sev == "Critical" else None)

# ---------- corrections (feedback loop 1): cap, bounds, most recent wins (code)
base = [{"key": k, "points": p, "max": mx} for k, p, mx in [("founder_quality", 17, 25), ("path_to_market", 10, 20), ("evidence_quality", 10, 20),
                                                              ("defensibility", 6, 15), ("sector_fit", 9, 10), ("capital_fit", 6, 10)]]
mk = lambda n, crit, d, at: {"n": n, "criterion": crit, "delta": d, "lesson": "l", "company": "X", "at": at, "similar_because": "s"}  # noqa: E731
for part, matches, check, exp, sev in [
    ("one correction +3", [mk(1, "evidence_quality", 3, "2026-11-20")], eq("criteria.evidence_quality.points", 13), "10 to 13", "High"),
    ("two same-way corrections capped at 5", [mk(1, "evidence_quality", 4, "2026-11-20"), mk(2, "evidence_quality", 4, "2026-11-21")],
     eq("criteria.evidence_quality.points", 15), "10 to 15, not 18", "Critical"),
    ("conflict: most recent wins", [mk(1, "path_to_market", 4, "2026-11-20"), mk(2, "path_to_market", -3, "2026-11-21")],
     eq("criteria.path_to_market.points", 7), "only #2 applies: 10 to 7", "Critical"),
    ("conflict reported", [mk(1, "path_to_market", 4, "2026-11-20"), mk(2, "path_to_market", -3, "2026-11-21")],
     {"op": "set_equals", "path": "applied", "value": [2]}, "applied list is [2]", "High"),
    ("never above max", [mk(1, "sector_fit", 5, "2026-11-20")], eq("criteria.sector_fit.points", 10), "9 to 10", "High"),
    ("never below zero", [mk(1, "capital_fit", -5, "2026-11-20"), mk(2, "capital_fit", -5, "2026-11-21")], eq("criteria.capital_fit.points", 1), "6 to 1 (capped move of 5)", "High"),
    ("other criteria untouched", [mk(1, "evidence_quality", 3, "2026-11-20")], eq("criteria.founder_quality.points", 17), "17 unchanged", "Low"),
    ("no matches, nothing moves", [], eq("criteria.path_to_market.points", 10), "unchanged", "Low"),
]:
    case("apply_corrections", part, {"criteria": base, "matches": matches}, exp, check, sev)

# ---------- decisions 6 to 8: scheduling agent and email safety (code; nothing sent, nothing booked)
V = lambda kind, **k: dict({"kind": kind, "picked_slot": 0, "proposed": []}, **k)  # noqa: E731
for part, inp, check, exp, sev, kill in [
    ("no reply, one minute before day 3", {"hours": 71.98}, eq("action", "none"), "still waiting", "High", "K7"),
    ("no reply at exactly day 3", {"hours": 72}, eq("action", "followup"), "follow-up 1", "High", "K7"),
    ("second follow-up at day 6", {"hours": 144, "followups": 1, "last_contact_hours": 72}, eq("action", "followup"), "follow-up 2", "High", "K7"),
    ("one minute before the window closes", {"hours": 215.98, "followups": 2, "last_contact_hours": 144}, eq("status", "sent"), "waiting, not timed out", "High", "K7"),
    ("window closes at day 9", {"hours": 216, "followups": 2, "last_contact_hours": 144}, eq("status", "timed_out"), "timed out at that hour, escalated", "Critical", "K7"),
    ("confirms the first slot", {"verdict": V("interested", picked_slot=1)}, eq("status", "confirmed"), "confirmed, to booking", "Low", None),
    ("agrees without choosing", {"verdict": V("interested")}, eq("action", "book"), "books the first free slot", "Low", None),
    ("picked slot taken meanwhile", {"verdict": V("interested", picked_slot=1), "busy": [["2026-11-26T08:30:00Z", "2026-11-26T10:00:00Z"]]},
     eq("status", "counter_proposed"), "new slots offered, not double-booked", "High", None),
    ("counter-proposes once", {"round": 0, "verdict": V("other_time", proposed=["2026-11-26T16:00"]), "busy": [["2026-11-26T10:00:00Z", "2026-11-26T11:30:00Z"]]},
     eq("status", "counter_proposed"), "round increments", "Low", None),
    ("founder's time is free", {"verdict": V("other_time", proposed=["2026-11-26T16:00"])}, eq("status", "confirmed"), "booked at the founder's time", "Low", None),
    ("founder's time already past", {"hours": 100, "verdict": V("other_time", proposed=["2026-11-23T16:00"])}, eq("status", "counter_proposed"), "not booked in the past", "High", None),
    ("round 9 of 10", {"round": 8, "verdict": V("other_time")}, eq("status", "counter_proposed"), "one more round allowed", "High", "K7"),
    ("counter at the cap (round 10)", {"round": 9, "verdict": V("other_time")}, eq("status", "escalated"), "escalated at exactly the cap, not cap+1", "Critical", "K7"),
    ("not interested", {"verdict": V("not_interested")}, eq("action", "suppress"), "suppressed", "Critical", "K8"),
    ("ambiguous reply", {"verdict": V("ambiguous")}, eq("status", "needs_human"), "routed to Riya, not force-classified", "High", None),
    ("booked: nothing more", {"status": "booked", "hours": 500}, eq("action", "none"), "no further contact", "High", "K7"),
    ("closed not interested: nothing more", {"status": "closed_not_interested", "hours": 500}, eq("action", "none"), "never contacted again", "Critical", "K8"),
]:
    case("schedule_decide", part, inp, exp, check, sev, kill)
for part, inp, check, exp, sev, kill in [
    ("calendar times out", {"hours": 72, "fail": "calendar_timeout"}, eq("status", "escalated"), "retried inside fetch, then escalated", "High", None),
    ("calendar permission revoked", {"hours": 72, "fail": "calendar_permission"}, {"op": "all", "checks": [eq("status", "aborted"), eq("calendar_attempts", 1)]},
     "aborted, no retry", "Critical", None),
    ("bad founder address", {"hours": 72, "fail": "bad_address"}, eq("status", "skipped"), "skipped; the pipeline continues", "High", None),
    ("booking invite fails permanently", {"reply": "slot 1", "verdict": V("interested", picked_slot=1), "fail": "book_permanent"},
     {"op": "all", "checks": [eq("status", "aborted"), eq("send_attempts", 1)]}, "aborted, zero retries", "Critical", None),
    ("record fails after booking", {"reply": "slot 1", "verdict": V("interested", picked_slot=1), "fail": "record_after_booking"},
     {"op": "all", "checks": [eq("status", "escalated"), eq("alerted", True)]}, "escalated, operator alerted same cycle", "Critical", None),
    ("not interested reply suppresses", {"reply": "please remove us", "verdict": V("not_interested")}, eq("suppressed", True), "on the do-not-contact list", "Critical", "K8"),
    ("happy path books", {"reply": "Thursday works", "verdict": V("interested", picked_slot=1)}, eq("status", "booked"), "booked with an invite", "Low", None),
]:
    case("schedule_tick", part, inp, exp, check, sev, kill)
for part, inp, check, exp, sev in [
    ("test mode: founder rerouted to operator", {"founder_email": "asha@evalco.example"}, eq("refused", False), "goes to the operator only", "Critical"),
    ("test mode never mails the founder", {"founder_email": "asha@evalco.example"}, {"op": "not_equals", "path": "to", "value": "asha@evalco.example"}, "founder address not used", "Critical"),
    ("live mode, founder not on allowlist", {"founder_email": "asha@evalco.example", "test_mode": False}, eq("refused", True), "refused", "Critical"),
    ("live mode, founder on allowlist", {"founder_email": "asha@evalco.example", "test_mode": False, "allowlist": ["asha@evalco.example"]}, eq("refused", False), "sent", "High"),
    ("suppressed founder", {"founder_email": "gone@evalco.example", "suppressed": ["gone@evalco.example"]}, eq("refused", True), "refused even in test mode", "Critical"),
    ("no address at all, live", {"founder_email": "", "test_mode": False}, eq("refused", True), "refused", "High"),
]:
    case("route", part, inp, exp, check, sev, "K4" if "suppressed" not in part else "K8")

OUT.mkdir(parents=True, exist_ok=True)
by_point = {}
for k in CASES:
    by_point.setdefault(k["point"], []).append(k)
for point, rows in by_point.items():
    (OUT / ("%s.json" % point)).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
print({p: len(r) for p, r in by_point.items()}, "total", len(CASES))
