"""Kushal's Portfolio screen: fictional companies with invented figures (case/portfolio_sample.json says so), health
rules in code, and a simulator that moves the figures with the calendar so the screen stays current."""
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

SEED = json.loads((Path(__file__).resolve().parent.parent / "case" / "portfolio_sample.json").read_text())
TOP_SECTORS = 5  # a donut past five slices is unreadable; the rest is Other


def health(runway_months, growth_3m, days_since_update, burn_to_revenue):
    """(band, reasons). At risk beats Watch beats Healthy; reasons name every rule the band tripped."""
    risk = [r for ok, r in (
        (runway_months < 6, "Runway %.1f months (under 6)" % runway_months),
        (days_since_update > 60, "No update for %d days (over 60)" % days_since_update),
        (growth_3m < -10, "Revenue %+.0f%% over 3 months (worse than -10%%)" % growth_3m)) if ok]
    if risk:
        return "At risk", risk
    watch = [r for ok, r in (
        (runway_months < 12, "Runway %.1f months (under 12)" % runway_months),
        (days_since_update > 30, "No update for %d days (over 30)" % days_since_update),
        (growth_3m < 5, "Revenue %+.0f%% over 3 months (under 5%%)" % growth_3m),
        (burn_to_revenue > 3, "Burn %.1f× monthly revenue (over 3×)" % burn_to_revenue)) if ok]
    if watch:
        return "Watch", watch
    return "Healthy", ["Runway %.0f months, revenue %+.0f%% over 3 months, updated %d days ago" % (runway_months, growth_3m, days_since_update)]


def _wiggle(name, month):
    """Same small move for the same company and month, so figures change with time but never flicker on reload."""
    h = int(hashlib.sha256(("%s|%d" % (name, month)).encode()).hexdigest()[:8], 16)
    return (h / 0xFFFFFFFF - 0.5) * 0.06  # within ±3%


def _company(c, today, base):
    months = (today - base).days / 30.44
    m_now = today.year * 12 + today.month
    series = [round(c["rev_lakh"] * (1 + c["growth"]) ** (months - k) * (1 + _wiggle(c["name"], m_now - k)), 1) for k in range(11, -1, -1)]
    cash = max(c["cash_cr"] - c["burn_lakh"] * months / 100, 0)
    runway = cash * 100 / c["burn_lakh"]
    growth_3m = (series[-1] / series[-4] - 1) * 100
    if c.get("silent_since"):
        days = (today - date.fromisoformat(c["silent_since"])).days
    else:
        days = ((today - base).days + c["offset"]) % c["cadence"]
    band, reasons = health(runway, growth_3m, days, c["burn_lakh"] / series[-1])
    multiple = c["current_post_cr"] / c["entry_post_cr"]  # shortcut: ignores dilution from later rounds; fine at pre-seed
    return {"name": c["name"], "sector": c["sector"], "what": c["what"], "founders": c["founders"], "note": c["note"],
            "invested_on": c["invested_on"], "invested_cr": c["invested_cr"], "value_cr": round(c["invested_cr"] * multiple, 2),
            "multiple": round(multiple, 2), "revenue_lakh": series, "growth_3m": round(growth_3m, 1), "runway_months": round(runway, 1),
            "burn_lakh": c["burn_lakh"], "days_since_update": days, "health": band, "reasons": reasons}


def view(today=None):
    today = today or datetime.now(timezone.utc).date()
    base = date.fromisoformat(SEED["as_of"])
    cos = [_company(c, today, base) for c in SEED["companies"]]
    invested = sum(c["invested_cr"] for c in cos)
    f, pub = SEED["fund"], SEED["public"]
    incoming = pub["committed_cr"] - invested - f["cash_cr"] - f["fees_cr"]  # capital committed but not yet called
    reserve = invested * f["reserve_share"]
    by = {}
    for c in cos:
        by[c["sector"]] = by.get(c["sector"], 0) + c["invested_cr"]
    ranked = sorted(by.items(), key=lambda kv: -kv[1])
    sectors = [{"sector": s, "invested_cr": round(v, 2)} for s, v in ranked[:TOP_SECTORS]]
    rest = ranked[TOP_SECTORS:]
    if rest:
        sectors.append({"sector": "Other", "invested_cr": round(sum(v for _, v in rest), 2), "includes": [s for s, _ in rest]})
    for s in sectors:
        s["share"] = round(s["invested_cr"] / invested * 100, 1)
    return {"as_of": today.isoformat(), "public": pub,
            "money": {"invested_cr": round(invested, 2), "cash_cr": f["cash_cr"], "incoming_cr": round(incoming, 2),
                      "free_cr": round(f["cash_cr"] + incoming - reserve, 2), "reserve_cr": round(reserve, 2)},
            "sectors": sectors, "companies": cos,
            "counts": {b: sum(c["health"] == b for c in cos) for b in ("Healthy", "Watch", "At risk")}}
