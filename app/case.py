"""The case data: 10 applications (deck text + form) extracted once by scripts/extract_case.py."""
import json
import re
from pathlib import Path

CASE = Path(__file__).resolve().parent.parent / "case"


def applications():
    return json.loads((CASE / "applications.json").read_text())


def summary():
    """What the batch list needs; deck and form text stay on the server until a read asks for them."""
    return [{k: a[k] for k in ("id", "company", "sector_label", "stage", "raise", "source")} for a in applications()]


_FOUNDER = re.compile(r"Founder(?: \d)?\s+((?:Dr\. )?[A-Z][a-z]*(?: [A-Z][a-z]*)*)(?:,\s*([A-Za-z ]+?))?(?=[.]|\s+LinkedIn|\s+linkedin|$)")


def founders(app):
    """[(name, role or None)] from the form's Founders section, e.g. ("Dr. Lakshmi Reddy", "CEO")."""
    return [(m[1], m[2]) for m in _FOUNDER.finditer(" ".join(app["form_text"].split()))]


def _site(app):
    m = re.search(r"Website\s+(?:https?://)?(?:www\.)?([a-z0-9.-]+\.[a-z]{2,})", app["form_text"], re.I)
    return m.group(1).lower() if m else None


def duplicates(app, others=None):
    """Other applications that look like the same company: same name (ignoring case and spaces), same website or a founder in common."""
    norm = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())  # noqa: E731
    mine = {f[0].lower() for f in founders(app)}
    out = []
    for o in (others if others is not None else applications()):
        if o["id"] == app["id"]:
            continue
        why = ("same name" if norm(o["company"]) == norm(app["company"]) else
               "same website" if _site(o) and _site(o) == _site(app) else
               "same founder" if mine & {f[0].lower() for f in founders(o)} else None)
        if why:
            out.append((o["company"], why))
    return out

