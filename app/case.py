"""The case data: 10 applications (deck text + form) extracted once by scripts/extract_case.py."""
import json
from pathlib import Path

CASE = Path(__file__).resolve().parent.parent / "case"


def applications():
    return json.loads((CASE / "applications.json").read_text())


def summary():
    """What the batch list needs; deck and form text stay on the server until a read asks for them."""
    return [{k: a[k] for k in ("id", "company", "sector_label", "stage", "raise", "source")} for a in applications()]
