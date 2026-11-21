"""Public search outside the deck: Tavily, with a loop cap and a stop rule per field and a recorded trail.
Stop rule: a field is done ("sufficient") once a result names the thing searched for (the company or the founder);
after the cap it is "not_found", which the scorer treats as unknown, never as absent."""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

from checks import _NoRedirect, _UA
from store import STORE

PER_FIELD, PER_APP = 2, 6  # loop cap: queries per field, and per application
CACHE_DAYS = 7
NEVER = ["linkedin.com"]  # login wall: excluded by the brief


def _search(query):
    key = "q" + hashlib.sha256(query.encode()).hexdigest()[:32]
    hit = STORE.get("tavily", key)
    if hit and time.time() - hit["at"] < CACHE_DAYS * 86400:
        return hit["results"]
    body = {"query": query, "search_depth": "basic", "max_results": 5, "exclude_domains": NEVER, "include_published_date": True}
    request = urllib.request.Request("https://api.tavily.com/search", json.dumps(body).encode(), dict(
        _UA, **{"Authorization": "Bearer " + os.environ["TAVILY_API_KEY"], "Content-Type": "application/json"}))
    with urllib.request.build_opener(_NoRedirect).open(request, timeout=20) as response:
        results = [{k: r.get(k) for k in ("title", "url", "content", "published_date")} for r in json.load(response).get("results", [])]
    STORE.put("tavily", key, {"at": time.time(), "query": query, "results": results})
    return results


def _names(text, name):
    return re.search(r"\b%s\b" % re.escape(name.lower()), (text or "").lower()) is not None


def fields(app):
    """What to look for, per the source map: the company, then each founder with the company."""
    form = app["form_text"]
    founders = re.findall(r"Founder \d+ ([A-Z][a-z]+(?: [A-Z][a-z]+)+),", form)
    city = (re.search(r"Location ([A-Z][a-z]+)", form) or [None, None])[1]
    # "also": a result counts only if it names one of these too, so a namesake is never taken for the applicant
    out = [{"field": "company", "target": app["company"], "also": founders + ([city] if city else []),
            "queries": ['"%s" startup India' % app["company"], '"%s" %s' % (app["company"], app["sector_label"])]}]
    for f in founders[:2]:
        out.append({"field": "founder: " + f, "target": f, "also": [app["company"]],
                    "queries": ['"%s" "%s"' % (f, app["company"]), '"%s" founder' % f]})
    return out


def about(result, field):
    text = (result.get("title") or "") + " " + (result.get("content") or "")
    return _names(text, field["target"]) and any(_names(text, a) for a in field["also"])


def gather(app):
    """Returns (evidence, trail). Evidence items get ids E1..En for the scorer to cite."""
    trail, evidence, used = [], [], 0
    if not os.environ.get("TAVILY_API_KEY"):
        return [], [{"field": f["field"], "query": None, "stop_reason": "no_key"} for f in fields(app)]
    for f in fields(app):
        for attempt, q in enumerate(f["queries"][:PER_FIELD], 1):
            if used >= PER_APP:
                trail.append({"field": f["field"], "query": q, "attempt": attempt, "stop_reason": "cap"})
                break
            used += 1
            try:
                results = _search(q)
            except urllib.error.HTTPError as e:
                trail.append({"field": f["field"], "query": q, "attempt": attempt, "stop_reason": "error HTTP %d" % e.code})
                break
            except Exception as e:
                trail.append({"field": f["field"], "query": q, "attempt": attempt, "stop_reason": "error " + type(e).__name__})
                break
            named = [r for r in results if about(r, f)]
            for r in named:
                if not any(e["url"] == r["url"] for e in evidence):
                    evidence.append(dict(r, id="E%d" % (len(evidence) + 1), field=f["field"]))
            done = bool(named)
            trail.append({"field": f["field"], "query": q, "attempt": attempt, "results": len(results),
                          "stop_reason": "sufficient" if done else ("not_found" if attempt == PER_FIELD else "next_query")})
            if done:
                break
    return evidence, trail
