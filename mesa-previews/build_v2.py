import re
css = re.search(r'<style>(.*?)</style>', open('screen1-quantum.html').read(), re.S).group(1)
css += '''
.mail{background:var(--card);border:1px solid var(--stone);border-radius:4px;padding:16px 20px}
.mail .row{display:flex;gap:12px;padding:6px 0;border-bottom:1px solid var(--stone)}.mail .row b{width:70px;color:var(--mut);font-weight:500}
.test{background:var(--carbon);color:var(--alab);padding:8px 14px;border-radius:4px;font-size:14px;display:flex;gap:10px;align-items:center}
.test i{width:12px;height:12px;background:var(--acc-t);display:inline-block}
.card{background:var(--card);border:1px solid var(--stone);border-radius:4px;padding:14px 18px}
.pill{display:inline-block;padding:1px 8px;border:1px solid currentColor;border-radius:4px;font-size:12px;font-weight:600}
.nav{display:flex;gap:6px;margin-left:36px}.nav span{padding:8px 14px;color:var(--mutd);font-size:15px;border-bottom:3px solid transparent}
.nav span.on{color:var(--alab);border-bottom-color:var(--acc-t);font-weight:600}
.role{margin-left:auto;display:flex;gap:10px;align-items:center;color:var(--mutd);font-size:14px}
.role b{color:var(--alab);border:1px solid #3a3d42;border-radius:4px;padding:3px 10px}
.verdict{display:flex;gap:28px;align-items:flex-end;flex-wrap:wrap}
.yn{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}
.yn .card{border-top:3px solid var(--stone)}.yn .yes{border-top-color:var(--ok)}.yn .no{border-top-color:var(--bad)}
.yn ul{margin:8px 0 0;padding-left:18px}.yn li{margin:6px 0}.src{color:var(--mut);font-size:13px}
.dec{background:var(--card);border:1px solid var(--stone);border-radius:4px;padding:18px 20px;margin-top:22px}
.dec textarea,.field{width:100%;font:inherit;border:1px solid var(--stone);border-radius:4px;padding:10px 12px;background:#fff;color:var(--carbon)}
.dec .row2{display:flex;gap:12px;margin-bottom:12px}.b.go{background:var(--ok);border-color:var(--ok);color:#fff}.b.no{background:var(--bad);border-color:var(--bad);color:#fff}
.page{padding:24px 32px 40px}.tl{list-style:none;margin:0;padding:0}.tl li{padding:10px 0 10px 18px;border-left:2px solid var(--stone);position:relative}
.tl li::before{content:"";position:absolute;left:-6px;top:15px;width:10px;height:10px;border-radius:50%;background:var(--stone)}
.tl li.now::before{background:var(--cyan)}.kpis{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-top:16px}
.kpis .card .v{font-family:'Space Grotesk';font-weight:700;font-size:34px}
'''
FONT = '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">'
WM = '<div class="watermark">ROUGH MOCKUP after the mentor review. Company facts from the real decks and forms; scores, benchmark, dates and replies are illustrative.</div>'
def page(title, who, tabs, active, body, wrap=True):
    nav = ''.join(f'<span class="{"on" if t==active else ""}">{t}</span>' for t in tabs)
    inner = body if not wrap else f'<div class="page">{WM}{body}</div>'
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>{FONT}<style>{css}</style></head><body>
<div class="top"><div class="sq"></div><div class="t">All In Capital triage</div><div class="nav">{nav}</div><div class="role">Signed in as <b>{who}</b></div></div>{inner}</body></html>'''
RT = ['Decisions', 'Email drafts', 'Scheduling']
KT = ['Outcomes', 'Thesis', 'Trust report']
apps = [('EarnWise','Fintech · ₹2 Cr','ok','GO'),('Talkbook','Consumer tech · ₹2 Cr','bad','NO-GO'),('Settlr','Fintech · Series A','bad','NO-GO'),('CareCorner','Healthcare · ₹3 Cr','bad','NO-GO'),('Yatrika','Consumer tech · ₹1.2 Cr','bad','NO-GO'),('RentRoute','Fintech · ₹1.8 Cr','bad','NO-GO'),('CAPilot','Fintech · ₹1.5 Cr','ok','GO'),('GrainKind','Consumer brands · ₹2.5 Cr','ok','GO'),('Pumpwise','Deeptech · ₹2.2 Cr','ok','GO'),('StockSathi','Consumer tech · ₹2 Cr','bad','NO-GO')]
lst = ''.join(f'<div class="it{" sel" if n=="StockSathi" else ""}"><div class="n">{n} <span class="chip {c}">{"✓" if v=="GO" else "✕"} {v}</span></div><div class="s">{s}</div></div>' for n,s,c,v in apps)

r1 = f'''<div class="wrap"><div class="list"><h3>THIS WEEK'S BATCH · 6 TO DECIDE</h3>{lst}</div><div class="main">{WM}
<div class="head"><h1>StockSathi</h1><div class="sub">B2B restocking app with short-term credit for small-town kirana stores · Consumer tech (as selected) · Pre-seed · Raising ₹2 Cr · Warm intro, Fund I network</div></div>
<div class="ban" style="grid-template-columns:1.2fr 1fr 1.3fr"><div><div class="lab">RECOMMENDATION</div><div class="big">✕ NO-GO</div><div style="color:var(--mutd);margin-top:6px">Below the benchmark: three numbers disagree and credit risk is unclear</div></div>
<div><div class="lab">SCORE AGAINST BENCHMARK</div><div class="scr">58<small> / 100 · benchmark 65</small></div><div style="color:var(--mutd)">Confidence: Low · 2 facts Not Found</div></div>
<div><div class="lab">PORTFOLIO OVERLAP</div><div style="font-size:18px;margin-top:6px;color:var(--alab)">None found among 22 listed companies</div><div style="color:var(--mutd)">The public list is partial</div></div></div>
<div class="yn"><div class="card yes"><b class="ok">Why yes</b><ul>
<li>Founder ran a regional sales team at a large FMCG distributor for 8 years <span class="src">· Form, Founders</span></li>
<li>22 of 38 stores have ordered more than once <span class="src">· Deck, slide 5</span></li>
<li>Small-town, vernacular focus that metro B2B marketplaces lack <span class="src">· Deck, slide 9</span></li></ul></div>
<div class="card no"><b class="bad">Why no</b><ul>
<li>Deck and form disagree on retailers, CAC and how credit is funded <span class="src">· Deck slides 5 to 8 vs Form</span></li>
<li>Lends with first-loss risk while not registered as an NBFC <span class="src">· Form, Credit</span></li>
<li>Founder background could not be checked outside the application <span class="src">· Tavily search, 0 matches</span></li></ul></div></div>
<div class="sec"><h2>Score by criterion</h2><table><tr><th>CRITERION</th><th class="r">POINTS</th><th>WHY</th><th>SOURCE</th></tr>
<tr><td><b>Founder quality</b></td><td class="r">15 / 25</td><td>Distribution operator, first-time founders; capped because background is Not Found</td><td class="src">Form · Tavily</td></tr>
<tr><td><b>Path to market</b></td><td class="r">12 / 20</td><td>Two field agents in one town; credit route unclear</td><td class="src">Deck 7 · Form</td></tr>
<tr><td><b>Evidence quality</b></td><td class="r">8 / 20</td><td>Three numbers differ between deck and form</td><td class="src">Deck · Form</td></tr>
<tr><td><b>Defensibility</b></td><td class="r">9 / 15</td><td>Small-town focus; large marketplaces named as competitors</td><td class="src">Deck 9 · Tavily</td></tr>
<tr><td><b>Sector fit</b></td><td class="r">7 / 10</td><td>Labelled consumer tech; works as B2B commerce plus credit</td><td class="src">Form · Deck</td></tr>
<tr><td><b>Capital fit</b></td><td class="r">7 / 10</td><td>₹2 Cr ask; 40% goes to a credit book</td><td class="src">Deck 11 · Form</td></tr></table></div>
<div class="sec"><h2>Evidence and where deck and form disagree</h2><table><tr><th>ITEM</th><th>DECK</th><th>FORM</th><th>OUTSIDE SOURCE</th><th>STATUS</th></tr>
<tr><td>Retailers onboarded</td><td class="r">38</td><td class="r">42</td><td>none</td><td class="warn">▲ Disagree</td></tr>
<tr><td>CAC per store</td><td class="r">₹2,860</td><td class="r">under ₹2,000</td><td>none</td><td class="warn">▲ Disagree</td></tr>
<tr><td>Credit funding</td><td>Own capital for now</td><td>NBFC partner, first-loss ours</td><td>none</td><td class="warn">▲ Disagree</td></tr>
<tr><td>NBFC registration</td><td>not stated</td><td>Not registered</td><td><a href="#">RBI NBFC list</a></td><td class="ok">✓ Consistent</td></tr>
<tr><td>Founder background</td><td>8 years FMCG distribution</td><td>Same</td><td>Tavily: 0 matches</td><td class="mu">Not Found</td></tr></table></div>
<div class="dec"><h2 style="font-size:20px;margin-bottom:12px">Your call</h2><div class="row2"><button class="b go">✓ Go: take the call</button><button class="b no">✕ No-go: reject</button></div>
<label for="why" style="font-size:14px;font-weight:600">Reason <span class="mu" style="font-weight:400">(required if your call differs from NO-GO)</span></label>
<textarea id="why" rows="3" placeholder="For example: the CAC gap is founder-time accounting, and the distribution background is exactly what this needs."></textarea>
<div class="note">A Go opens the email draft automatically. A disagreement and its reason teach later reads.</div></div>
</div></div>'''
open('riya-1-decision.html','w').write(page('Riya decision','Riya',RT,'Decisions',r1,wrap=False))

r2 = '''<h1 style="font-size:30px">Email draft · Pumpwise</h1><div class="sub" style="color:var(--mut)">Opened automatically because the call is Go. Edit anything, then send. The agent takes over from there.</div>
<div class="test" style="margin-top:16px"><i></i> TEST MODE: the email goes only to your own address, not to the founder.</div>
<div style="display:grid;grid-template-columns:1.4fr 1fr;gap:24px;margin-top:18px;align-items:start"><div class="mail">
<div class="row"><b>To</b>karthik@pumpwise.example <span class="mu">(test: redirected to you)</span></div>
<div style="margin-top:12px"><label style="font-size:13px;color:var(--mut)">Subject</label><input class="field" value="30 minutes to talk about Pumpwise?"></div>
<div style="margin-top:12px"><label style="font-size:13px;color:var(--mut)">Email</label><textarea class="field" rows="13">Hi Karthik,

Thanks for applying to All In Capital. Your pilots caught our eye: 6 of 11 converted to paid, across 140 sensors.

We would like to talk about manufacturing scale-up and calibration, as you suggested. Does either of these work for 30 minutes, with Aditya joining?

Tue 24 Nov, 3:00 to 3:30 pm IST
Thu 26 Nov, 4:00 to 4:30 pm IST

Riya</textarea></div>
<div class="btns" style="margin-top:14px"><button class="b p">Send</button></div><div class="note">Your edits are saved and shape later drafts.</div></div>
<div><div class="card"><b>Slots from your calendar</b><br><span class="mu">Free in Google Calendar, Tue or Thu afternoon, 30 minutes</span><ul style="margin:10px 0 0;padding-left:18px"><li>Tue 24 Nov, 3:00 pm</li><li>Thu 26 Nov, 4:00 pm</li></ul></div>
<div class="card" style="margin-top:14px"><b>Who joins</b><br>Riya · Aditya (deeptech)</div>
<div class="card" style="margin-top:14px"><b>After you send</b><br><span class="mu">The agent reads the reply, follows up after 3 days of silence, offers new slots if asked, and books the meeting. You can watch it on Scheduling.</span></div></div></div>'''
open('riya-2-email.html','w').write(page('Riya email','Riya',RT,'Email drafts',r2))

r3 = '''<h1 style="font-size:30px">Scheduling</h1><div class="sub" style="color:var(--mut)">Read-only. The agent handles replies, follow-ups and booking. Nothing here needs you.</div>
<div class="sec"><table><tr><th>COMPANY</th><th>STATUS</th><th>LAST EVENT</th><th>AGENT'S NEXT STEP</th></tr>
<tr><td><b>GrainKind</b></td><td class="ok">✓ Booked</td><td>Founder confirmed Thu 26 Nov, 4:00 pm</td><td>None. On your calendar.</td></tr>
<tr style="background:#EEF2FF"><td><b>Pumpwise</b></td><td class="warn">▲ Counter-proposed</td><td>Founder asked for Friday</td><td>Offered Thu 3 Dec, 3:00 pm; waiting for reply</td></tr>
<tr><td><b>EarnWise</b></td><td class="mu">Email sent</td><td>Sent Tue 17 Nov</td><td>Follow up Fri 20 Nov if no reply</td></tr>
<tr><td><b>CAPilot</b></td><td class="mu">Follow-up sent</td><td>No reply for 3 days; follow-up sent 18 Nov</td><td>Follow up again Sat 21 Nov</td></tr></table></div>
<div class="sec"><h2>Pumpwise: email history</h2><ul class="tl">
<li><b>Sent</b> · Mon 16 Nov, 11:02 · "30 minutes to talk about Pumpwise?" with Tue 24 or Thu 26</li>
<li><b>Reply</b> · Tue 17 Nov, 09:40 · "Neither works, can we do a Friday?" <span class="pill warn">Read as: other time</span></li>
<li class="now"><b>Agent offered</b> · Tue 17 Nov, 09:41 · Thu 3 Dec, 3:00 pm (Fridays are outside the Tue/Thu rule; next free slot)</li></ul></div>'''
open('riya-3-scheduling.html','w').write(page('Riya scheduling','Riya',RT,'Scheduling',r3))

rows = [('EarnWise','GO','Go','✓','','Email sent'),('Talkbook','NO-GO','No-go','✓','','Not contacted'),('Settlr','NO-GO','No-go','✓','','Not contacted'),('CareCorner','NO-GO','No-go','✓','','Not contacted'),('Yatrika','NO-GO','Go','✕','Ten years running a travel agency is operating experience; 14% repeat in 7 months.','Email sent'),('RentRoute','NO-GO','No-go','✓','','Not contacted'),('CAPilot','GO','Go','✓','','Follow-up sent'),('GrainKind','GO','Go','✓','','Booked Thu 26 Nov'),('Pumpwise','GO','Go','✓','','Counter-proposed'),('StockSathi','NO-GO','Go','✕','The CAC gap is founder-time accounting; distribution background fits.','Draft not sent')]
def rec(v): return f'<span class="{"ok" if v.upper()=="GO" else "bad"}">{"✓" if v.upper()=="GO" else "✕"} {v}</span>'
tb = ''.join(f'<tr><td><b>{n}</b></td><td>{rec(a)}</td><td>{rec(b)}</td><td class="{"ok" if g=="✓" else "warn"}">{"Agrees" if g=="✓" else "▲ Disagrees"}</td><td>{w or "<span class=mu>none</span>"}</td><td>{m}</td></tr>' for n,a,b,g,w,m in rows)
k1 = f'''<h1 style="font-size:30px">This week's outcomes</h1><div class="sub" style="color:var(--mut)">Read-only. Riya decides; you see every outcome as it happens.</div>
<div class="kpis"><div class="card"><div class="lab">APPLICATIONS</div><div class="v">10</div></div><div class="card"><div class="lab">TOOL SAID GO</div><div class="v">4</div></div><div class="card"><div class="lab">RIYA SAID GO</div><div class="v">6</div></div><div class="card"><div class="lab">RIYA DISAGREED</div><div class="v warn">2</div></div><div class="card"><div class="lab">MEETINGS BOOKED</div><div class="v ok">1</div></div></div>
<div class="sec"><table><tr><th>COMPANY</th><th>TOOL</th><th>RIYA</th><th>MATCH</th><th>RIYA'S REASON</th><th>MEETING</th></tr>{tb}</table></div>
<div class="two"><div class="sec"><h2>Thesis waiting for you</h2><div class="card">Version 0.3: two observed-thesis lines changed after Riya's disagreements on founder experience.<div class="btns" style="margin-top:12px"><button class="b p">Review v0.3</button></div></div></div>
<div class="sec"><h2>Trust</h2><div class="card">Last eval run: 278 of 300 passed, 0 critical failures. Backtest: 5 held-out memos, 2 disagreements. <a href="#">Open the trust report</a></div></div></div>'''
open('kushal-1-outcomes.html','w').write(page('Kushal outcomes','Kushal',KT,'Outcomes',k1))
print('ok')
