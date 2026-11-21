"""One-time: turn the case PDFs in data/source/ into case/applications.json and case/*.txt (run with a Python that has pypdf)."""
import json
import re
import sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "data" / "source", ROOT / "case"
COMPANIES = ["StockSathi", "EarnWise", "Talkbook", "Settlr", "CareCorner", "Yatrika", "RentRoute", "CAPilot", "GrainKind", "Pumpwise"]


def text(path):
    t = "\n".join((p.extract_text() or "").strip() for p in PdfReader(str(path)).pages).strip()
    if t.count("\n \n") > 100:  # one PDF puts every word on its own line; rejoin it into plain prose
        t = re.sub(r"\s+", " ", t)
    return t


NEXT = {"Sector (as selected)": "Stage", "Stage (as selected)": "Team size", "Amount raising": "Valuation",
        "How did you hear about us?": "Anything else"}


def field(form, name):
    m = re.search(r"^%s\s+(.+)$" % re.escape(name), form, re.M) or \
        re.search(r"%s\s+(.+?)\s+%s" % (re.escape(name), NEXT[name]), form)
    return m.group(1).strip() if m else ""


apps = []
for c in COMPANIES:
    deck, form = text(SRC / ("%s_Deck.pdf" % c)), text(SRC / ("%s_Form.pdf" % c))
    assert deck and form, c
    apps.append({"id": c.lower(), "company": c, "sector_label": field(form, "Sector (as selected)"),
                 "stage": field(form, "Stage (as selected)"), "raise": field(form, "Amount raising"),
                 "source": field(form, "How did you hear about us?"), "deck_text": deck, "form_text": form})
OUT.mkdir(exist_ok=True)
(OUT / "applications.json").write_text(json.dumps(apps, indent=1, ensure_ascii=False))
(OUT / "memos.txt").write_text(text(SRC / "Deal_Memos.pdf"))
(OUT / "notes.txt").write_text(text(SRC / "Partner_Meeting_Notes.pdf"))
print("\n".join("%-11s %-17s %-10s %-8s deck %5d chars, form %5d" % (a["company"], a["sector_label"], a["stage"], a["raise"], len(a["deck_text"]), len(a["form_text"])) for a in apps))
