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
