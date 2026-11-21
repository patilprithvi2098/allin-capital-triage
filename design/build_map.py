# Builds components-map.html (SVG with HTML text) for rendering to PNG.
from html import escape
W, H = 2360, 1270
C = {"people": "#2B6CB0", "ai": "#1E7A4A", "system": "#6B6E70", "human": "#B3261E"}
TAG = {"people": "PEOPLE", "ai": "AI", "system": "DATA AND SYSTEMS", "human": "HUMAN TAKES OVER"}
parts = []

def node(x, y, w, h, kind, title, body, tag=True):
    col = C[kind]
    t = f'<div class="tag" style="color:{col}">{TAG[kind]}</div>' if tag else ''
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#F8F6F1" stroke="{col}" stroke-width="4"/>'
        f'<foreignObject x="{x}" y="{y}" width="{w}" height="{h}"><div xmlns="http://www.w3.org/1999/xhtml" class="n">{t}'
        f'<div class="t">{escape(title)}</div><div class="b">{escape(body)}</div></div></foreignObject>')

def arrow(pts, n, bx, by, dashed=False, label=None, lx=None, ly=None):
    d = "M " + " L ".join(f"{px} {py}" for px, py in pts)
    dash = ' stroke-dasharray="10 8"' if dashed else ''
    parts.append(f'<path d="{d}" fill="none" stroke="#18191A" stroke-width="3"{dash} marker-end="url(#ah)"/>')
    parts.append(f'<circle cx="{bx}" cy="{by}" r="16" fill="#18191A"/>'
                 f'<text x="{bx}" y="{by+6}" text-anchor="middle" class="num">{n}</text>')
    if label:
        parts.append(f'<text x="{lx}" y="{ly}" class="lab">{escape(label)}</text>')

# column headers
for x, s in [(40, "1  INTAKE"), (420, "2  GATHER"), (800, "3  JUDGE"), (1610, "4  REVIEW"), (1990, "5  ACT")]:
    parts.append(f'<text x="{x}" y="118" class="col">{s}</text>')

# column 1
node(40, 150, 330, 140, "people", "Applicants", "Public form or warm intro from the Fund I network. Deck text and form answers.")
node(40, 320, 330, 110, "people", "Riya loads the weekly batch", "The whole week's pile in one run.")
node(40, 460, 330, 180, "system", "Intake and checks", "Parse deck and form. Code compares numbers, team and funding between the two. Checks sector and stage labels. Rules, no model.")
node(40, 680, 330, 120, "people", "Riya logs her own call first", "Take call or Pass, locked before she can see the tool's read.")
# column 2
node(420, 150, 330, 230, "system", "Source fetchers", "Fund site and portfolio, press and web search (Tavily), company site, regulator pages, competitor search. Loop cap and stop rule per field. Not Found is recorded. No LinkedIn.")
node(420, 420, 330, 140, "system", "Evidence store", "Supabase Postgres: applications, claims, sources, Not Found, Riya's call.")
node(420, 600, 330, 150, "system", "Thesis store", "Written and Observed thesis, versioned. Built from public sources and the 12 memos. Kushal approves.")

# AI section
parts.append('<rect x="800" y="130" width="760" height="630" rx="4" fill="#EEF4EF" stroke="#1E7A4A" stroke-width="4"/>')
parts.append('<text x="820" y="168" class="aititle">AI SECTION: every point where the model uses judgment</text>')
parts.append('<text x="820" y="196" class="aisub">Claude generates. A different model judges in the evals. Each point has its own test cases.</text>')
chips = ["Thesis reconstruction", "Sector fit against the label", "Founder quality from evidence", "Path to market",
         "Does the source support the claim", "Is a deck-vs-form gap material", "Competitor definition applied",
         "Missing data: founder or search", "Portfolio overlap by what it does", "Take call, Pass or Hold",
         "Does a past correction match", "Email draft", "Founder reply: yes, no, other time"]
for i, c in enumerate(chips):
    col, row = (0, i) if i < 7 else (1, i - 7)
    x = 820 + col * 365
    y = 220 + row * 76
    parts.append(f'<rect x="{x}" y="{y}" width="350" height="62" rx="4" fill="#F8F6F1" stroke="#1E7A4A" stroke-width="3"/>')
    parts.append(f'<text x="{x+14}" y="{y+37}" class="chip"><tspan class="chipn">{i+1:02d}</tspan>  {escape(c)}</text>')
node(800, 800, 700, 130, "system", "Scoring matrix (rules in code)", "Points per criterion, total 100, plus gates: portfolio overlap = Hold, outside the areas = flag, stage mismatch = flag. Weights and thresholds tuned by the backtest.")

# column 5
node(1610, 150, 330, 190, "system", "Review screen", "Recommendation, score, evidence per criterion, gaps, confidence, Riya's call, trust panel (held-out cases, disagreements, unverifiable parts).")
node(1610, 380, 330, 140, "people", "Riya: Agree or Correct", "Compares her locked call with the read. One line of why on every correction.")
node(1610, 610, 330, 190, "human", "Kushal reviews every outcome", "Yes, No or Hold on each. Nothing is auto-approved or auto-rejected. Hold is forced on: portfolio overlap, low confidence, stage mismatch.")
# column 6
node(1990, 150, 330, 130, "ai", "Email agent", "Drafts: we'd like to schedule a meeting, does this time work?")
node(1990, 320, 330, 100, "human", "Kushal approves send", "His edits are kept as corrections.")
node(1990, 460, 330, 170, "system", "Resend and calendar", "Sends the email. Proposes Tue or Thu 30-minute slots, Aditya for deeptech. Test mode: operator's address only.")
node(1990, 670, 330, 140, "ai", "Reply handling", "Reads the founder's reply: yes, no or another time. Proposes the next slot.")

# learn band
parts.append('<text x="40" y="992" class="col">6  LEARN AND PROVE</text>')
node(40, 1010, 1060, 150, "system", "Eval harness", "About 300 test cases across every AI point, including dummy companies. Backtest on held-out memos with the decision and reasoning stripped. A different model judges. Pass and fail report, then root cause, fix and rerun. Production only after it passes.")
node(1610, 1010, 710, 150, "system", "Corrections store (Supabase)", "Score and recommendation corrections and email-draft corrections, each with its one-line why. Retrieved for similar companies, capped, with a regression check on the earlier test cases.")

# arrows
arrow([(205,290),(205,320)], 1, 205, 305)
arrow([(205,430),(205,460)], 2, 205, 445)
arrow([(205,640),(205,680)], 3, 205, 660)
arrow([(370,500),(395,500),(395,265),(420,265)], 4, 395, 380)
arrow([(585,380),(585,420)], 5, 585, 400)
arrow([(750,490),(800,490)], 6, 775, 490)
arrow([(750,675),(800,675)], 7, 775, 675)
arrow([(1180,760),(1180,800)], 8, 1180, 780)
arrow([(1500,855),(1575,855),(1575,245),(1610,245)], 9, 1575, 550)
arrow([(205,800),(205,952),(1597,952),(1597,445),(1610,445)], 10, 380, 952, dashed=True, label="her call is locked until the read is shown", lx=410, ly=942)
arrow([(1775,340),(1775,380)], 11, 1775, 360)
arrow([(1775,520),(1775,610)], 12, 1775, 565)
arrow([(1940,705),(1965,705),(1965,215),(1990,215)], 13, 1965, 460)
arrow([(2155,280),(2155,320)], 14, 2155, 300)
arrow([(2155,420),(2155,460)], 15, 2155, 440)
arrow([(2155,630),(2155,670)], 16, 2155, 650)
arrow([(1990,745),(1940,745)], 17, 1965, 745)
arrow([(1775,800),(1775,1010)], 18, 1775, 900)
arrow([(1610,1060),(1555,1060),(1555,880),(1500,880)], 19, 1555, 1000, dashed=True)
arrow([(775,1010),(775,720),(800,720)], 20, 775, 850, dashed=True, label="tests every AI point", lx=788, ly=1002)
arrow([(950,1010),(950,930)], 21, 950, 975, dashed=True)
parts.append('<text x="975" y="980" class="lab">thresholds and trust numbers</text>')
parts.append('<text x="1010" y="905" class="lab" style="display:none"></text>')

# legend
lx, ly = 40, 1228
items = [("people", "People"), ("ai", "AI"), ("system", "Data and systems"), ("human", "Human takes over")]
x = lx
for k, s in items:
    parts.append(f'<rect x="{x}" y="{ly-16}" width="26" height="26" rx="3" fill="#F8F6F1" stroke="{C[k]}" stroke-width="4"/>')
    parts.append(f'<text x="{x+38}" y="{ly+5}" class="leg">{s}</text>')
    x += 38 + len(s) * 12 + 50
parts.append(f'<path d="M {x} {ly-3} L {x+60} {ly-3}" stroke="#18191A" stroke-width="3" stroke-dasharray="10 8"/>')
parts.append(f'<text x="{x+74}" y="{ly+5}" class="leg">Test and feedback path</text>')
x += 74 + 22*12 + 40
parts.append(f'<circle cx="{x+14}" cy="{ly-3}" r="14" fill="#18191A"/><text x="{x+14}" y="{ly+3}" text-anchor="middle" class="num">1</text>')
parts.append(f'<text x="{x+40}" y="{ly+5}" class="leg">Order of the flow</text>')

svg = "\n".join(parts)
html = f'''<!doctype html><html><head><meta charset="utf-8"><title>components map</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Epilogue:wght@600;800&family=Work+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;background:#EFECE6}}
.n{{box-sizing:border-box;padding:12px 16px;font-family:'Work Sans',sans-serif;color:#18191A;overflow:hidden;height:100%}}
.tag{{font-size:12px;font-weight:600;letter-spacing:.08em;margin-bottom:4px}}
.t{{font-family:'Epilogue',sans-serif;font-weight:800;font-size:21px;line-height:1.15;margin-bottom:5px}}
.b{{font-size:16.5px;line-height:1.35}}
.num{{font-family:'Epilogue',sans-serif;font-weight:800;font-size:16px;fill:#00F2FE}}
.col{{font-family:'Epilogue',sans-serif;font-weight:800;font-size:20px;letter-spacing:.06em;fill:#18191A}}
.lab{{font-family:'Work Sans',sans-serif;font-size:15px;font-weight:500;fill:#18191A}}
.leg{{font-family:'Work Sans',sans-serif;font-size:18px;fill:#18191A}}
.aititle{{font-family:'Epilogue',sans-serif;font-weight:800;font-size:21px;fill:#18191A}}
.aisub{{font-family:'Work Sans',sans-serif;font-size:16px;fill:#55585A}}
.chip{{font-family:'Work Sans',sans-serif;font-size:17px;font-weight:500;fill:#18191A}}
.chipn{{font-family:'Epilogue',sans-serif;font-weight:800;fill:#1E7A4A}}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><marker id="ah" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L12 6 L0 12 Z" fill="#18191A"/></marker></defs>
<rect width="{W}" height="{H}" fill="#EFECE6"/>
<rect width="{W}" height="80" fill="#18191A"/>
<rect x="40" y="26" width="28" height="28" fill="#00F2FE"/>
<text x="86" y="52" style="font-family:'Epilogue',sans-serif;font-weight:800;font-size:30px;fill:#EFECE6">All In Capital triage: components map</text>
<text x="{W-40}" y="50" text-anchor="end" style="font-family:'Work Sans',sans-serif;font-size:18px;fill:#A3A5A6">Applicants in, a sourced read out. Kushal decides.</text>
{svg}
</svg></body></html>'''
open("/Users/patilprithvi/AllInCapital/design/components-map.html", "w").write(html)
print("ok")
