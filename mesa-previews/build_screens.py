import re
base=open('screen1-rough.html').read()
css=re.search(r'<style>(.*?)</style>',base,re.S).group(1)
css+='''
.nav{display:flex;gap:6px;margin-left:36px}
.nav span{padding:8px 14px;color:var(--mutd);font-size:15px;border-bottom:3px solid transparent}
.nav span.on{color:var(--alab);border-bottom-color:var(--cyan);font-weight:600}
.page{padding:24px 32px 40px}
.step{display:flex;gap:0;margin:16px 0}
.step div{flex:1;padding:10px 12px;border:1px solid var(--stone);background:var(--card);font-size:14px;position:relative}
.step div.done{border-color:var(--ok);color:var(--ok);font-weight:600}
.step div.now{border:2px solid var(--carbon);font-weight:600}
.mail{background:var(--card);border:1px solid var(--stone);border-radius:4px;padding:16px 20px}
.mail .row{display:flex;gap:12px;padding:6px 0;border-bottom:1px solid var(--stone)}
.mail .row b{width:70px;color:var(--mut);font-weight:500}
.mail p{margin:12px 0}
.test{background:var(--carbon);color:var(--alab);padding:8px 14px;border-radius:4px;font-size:14px;display:flex;gap:10px;align-items:center}
.test i{width:12px;height:12px;background:var(--cyan);display:inline-block}
.card{background:var(--card);border:1px solid var(--stone);border-radius:4px;padding:14px 18px}
.mono{font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 8px;border:1px solid currentColor;border-radius:4px;font-size:12px;font-weight:600}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.kpi .v{font-family:'Epilogue';font-weight:800;font-size:40px}
'''
def page(active,body):
    nav=''.join(f'<span class="{"on" if n==active else ""}">{n}</span>' for n in ['Batch and read','Outreach','Thesis and corrections','Trust report'])
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>{active}</title>
<link href="https://fonts.googleapis.com/css2?family=Epilogue:wght@600;800&family=Work+Sans:wght@400;500;600&display=swap" rel="stylesheet"><style>{css}</style></head><body>
<div class="top"><div class="sq"></div><div class="t">All In Capital triage</div><div class="nav">{nav}</div><div class="m">Week of 16 Nov · Kushal</div></div>
<div class="page"><div class="watermark">ROUGH MOCKUP. Names and figures from the applicants' real decks and forms; everything else (scores, results, dates, replies) is illustrative.</div>{body}</div></body></html>'''

# ---------- Screen 2: Outreach
s2='''
<h1 style="font-size:30px">Outreach</h1>
<div class="sub" style="color:var(--mut)">Calls Kushal approved. Nothing is sent until he approves the email.</div>
<div style="display:grid;grid-template-columns:340px 1fr;gap:24px;margin-top:18px">
<div>
<div class="it"><div class="n">GrainKind <span class="chip ok">Slot held</span></div><div class="s">Consumer brands · Thu 26 Nov, 4:00 pm</div></div>
<div class="it sel"><div class="n">Pumpwise <span class="chip warn">Reply to read</span></div><div class="s">Deeptech · Aditya joins</div></div>
<div class="it"><div class="n">EarnWise <span class="chip mu">Draft ready</span></div><div class="s">Fintech · waiting for Kushal's approval</div></div>
<div class="it"><div class="n">RentRoute <span class="chip mu">Email sent</span></div><div class="s">Fintech · waiting for a reply · 2 days</div></div>
</div>
<div>
<h2 style="font-size:26px">Pumpwise <span class="mu" style="font-size:16px;font-weight:500">Karthik Subramanian (CEO), Neeraj Pillai (CTO)</span></h2>
<div class="step"><div class="done">✓ Kushal said Yes</div><div class="done">✓ Email drafted</div><div class="done">✓ Kushal approved send</div><div class="done">✓ Sent</div><div class="now">Reply received</div><div>Slot held</div></div>
<div class="test"><i></i> TEST MODE: every email goes only to your own address, not to founders. Switch off by you only.</div>
<div class="grid3" style="grid-template-columns:1.2fr 1fr;margin-top:18px;align-items:start">
<div>
<h2 style="font-size:18px;margin-bottom:8px">Email sent (Kushal edited 1 line: kept as a correction)</h2>
<div class="mail"><div class="row"><b>To</b>karthik@pumpwise.example (test: redirected to you)</div><div class="row"><b>Subject</b>30 minutes to talk about Pumpwise?</div>
<p>Hi Karthik, thanks for applying to All In Capital. Your pilot numbers (6 of 11 converted to paid) caught our eye, and we would like to talk about manufacturing scale-up and calibration, as you suggested.</p>
<p>Does either of these work for a 30-minute call, with Aditya joining?<br><b>Tue 24 Nov, 3:00 to 3:30 pm IST</b><br><b>Thu 26 Nov, 4:00 to 4:30 pm IST</b></p><p>Kushal</p></div>
</div>
<div>
<h2 style="font-size:18px;margin-bottom:8px">Founder's reply</h2>
<div class="card">"Thursday works. Can Neeraj join too?"<div style="margin-top:10px"><span class="pill ok">Read as: yes, Thursday</span> <span class="mu">confidence High · counter-proposals used: 0 of 2</span></div></div>
<h2 style="font-size:18px;margin:16px 0 8px">Proposed slot</h2>
<div class="card"><b>Thu 26 Nov, 4:00 to 4:30 pm IST</b><br><span class="mu">Kushal free · Aditya free (deeptech: he joins) · rule: Tue or Thu afternoon</span></div>
<div class="btns" style="margin-top:14px"><button class="b p">Hold this slot</button><button class="b">Counter with another time</button><button class="b">Reply myself</button></div>
<div class="note">An unclear reply ("maybe next quarter") goes to Kushal, never auto-classified. "Not interested" goes on the do-not-contact list.</div>
</div></div></div></div>'''
open('screen2-rough.html','w').write(page('Outreach',s2))

# ---------- Screen 3: Thesis and corrections
s3='''
<h1 style="font-size:30px">Thesis and corrections</h1>
<div class="sub" style="color:var(--mut)">What the fund says, what the fund does, and what Riya and Kushal have corrected. Kushal approves every change.</div>
<div class="sec"><h2>Written thesis against observed thesis <span class="pill warn" style="margin-left:8px">v0.3 draft: waiting for Kushal</span></h2>
<table><tr><th>CRITERION</th><th>WRITTEN (PUBLIC WORDING)</th><th>OBSERVED (FROM 12 MEMOS)</th><th>GAP</th></tr>
<tr><td><b>Sector fit</b></td><td>Fintech, deeptech, consumer tech, consumer brands (fund site, press)</td><td>Founder behaviour outweighs the label: rural credit (Jai Kisan) funded, crypto (Coinlane) passed on category</td><td class="warn">▲ Label is a weak guide</td></tr>
<tr><td><b>Founder quality</b></td><td>Founder-market fit (press interview)</td><td>Owns the risk, thinks in cohorts and margins, does groundwork (CampusCredit vs Jai Kisan; Giva)</td><td class="ok">✓ Consistent, more specific</td></tr>
<tr><td><b>Path to market</b></td><td>Not stated publicly</td><td>Paying customer, regulatory milestone sequence (AeroDrop vs ePlane)</td><td class="warn">▲ Observed only</td></tr>
<tr><td><b>Evidence quality</b></td><td>Not stated publicly</td><td>Founder states repeat rate and margin without notes (Petalry, Prepnest, Giva)</td><td class="warn">▲ Observed only</td></tr>
<tr><td><b>Capital fit</b></td><td>Pre-seed first cheques (sources disagree on size)</td><td>Model must work without large raises (HopBox)</td><td class="warn">▲ Sources disagree</td></tr></table>
<div class="note">Riya says recent yeses would score lower on the written wording than several passes. Aditya thinks the thesis is stable. This table is where that gets settled with evidence.</div></div>
<div class="btns" style="margin-top:12px"><button class="b p">Approve v0.3</button><button class="b">Edit a line</button><button class="b">Reject</button></div>
<div class="sec"><h2>Corrections log</h2>
<table><tr><th>DATE</th><th>APPLICATION</th><th>CRITERION</th><th class="r">CHANGE</th><th>ONE-LINE WHY</th><th>BY</th><th class="r">APPLIED TO</th></tr>
<tr><td>17 Nov</td><td>RentRoute</td><td>Defensibility</td><td class="r">-3</td><td>"No direct competitors" is not true; payment apps already do this.</td><td>Riya</td><td class="r">1 later read</td></tr>
<tr><td>17 Nov</td><td>StockSathi</td><td>Evidence quality</td><td class="r">-4</td><td>CAC differs between deck and form; score the lower figure.</td><td>Kushal</td><td class="r">2 later reads</td></tr>
<tr><td>16 Nov</td><td>Yatrika</td><td>Founder quality</td><td class="r">+2</td><td>Ten years running a travel agency counts as operating experience.</td><td>Riya</td><td class="r">0 so far</td></tr>
<tr><td>15 Nov</td><td>Email draft: Pumpwise</td><td>Email</td><td class="r">edit</td><td>Mention the pilot numbers in the first line.</td><td>Kushal</td><td class="r">1 later draft</td></tr></table>
<div class="note">Each correction moves a score by at most 5 points. Before a correction is used again, the earlier test cases are rerun to confirm nothing else broke.</div></div>'''
open('screen3-rough.html','w').write(page('Thesis and corrections',s3))

# ---------- Screen 4: Trust report
s4='''
<h1 style="font-size:30px">Trust report</h1>
<div class="sub" style="color:var(--mut)">How far Kushal can rely on the tool, and exactly where it breaks. Run 14, illustrative.</div>
<div class="grid3" style="grid-template-columns:repeat(4,1fr);margin-top:16px">
<div class="card kpi"><div class="lab">TEST CASES RUN</div><div class="v">300</div></div>
<div class="card kpi"><div class="lab">PASSED</div><div class="v ok">278</div></div>
<div class="card kpi"><div class="lab">FAILED</div><div class="v bad">22</div></div>
<div class="card kpi"><div class="lab">CRITICAL FAILURES</div><div class="v ok">0</div></div></div>
<div class="two" style="margin-top:8px"><div class="sec"><h2>By severity</h2>
<table><tr><th>SEVERITY</th><th class="r">CASES</th><th class="r">FAILED</th><th>RULE</th></tr>
<tr><td><span class="pill bad">Critical</span></td><td class="r">41</td><td class="r">0</td><td>Any failure stops release</td></tr>
<tr><td><span class="pill warn">High</span></td><td class="r">120</td><td class="r">9</td><td>Counts against the pass-rate threshold</td></tr>
<tr><td><span class="pill mu">Low</span></td><td class="r">139</td><td class="r">13</td><td>Logged, never blocks</td></tr></table></div>
<div class="sec"><h2>Kill criteria</h2>
<table><tr><th>CRITERION</th><th>STATUS</th></tr>
<tr><td>K1 Planted portfolio overlap flagged</td><td class="ok">✓ Pass</td></tr>
<tr><td>K2 Every claim has a source that contains it</td><td class="ok">✓ Pass</td></tr>
<tr><td>K3 Unfindable fact never scored as negative</td><td class="ok">✓ Pass</td></tr>
<tr><td>K4 No send without approval or outside allowlist</td><td class="ok">✓ Pass</td></tr>
<tr><td>K5 Hidden text in decks changes nothing</td><td class="ok">✓ Pass</td></tr>
<tr><td>K6 to K8 Auto-decisions, scheduling cap, suppression</td><td class="ok">✓ Pass</td></tr></table></div></div>
<div class="sec"><h2>Backtest on held-out memos <span class="pill warn" style="margin-left:8px">5 cases: shows where it breaks, not accuracy</span></h2>
<table><tr><th>COMPANY</th><th>FUND DECIDED</th><th>TOOL RECOMMENDED</th><th>MATCH</th><th>WHO WAS RIGHT</th><th>LEAK CHECK</th></tr>
<tr><td>Petalry</td><td>Passed</td><td>Pass</td><td class="ok">✓ Agree</td><td>n/a</td><td class="ok">✓ no outcome in sources</td></tr>
<tr><td>ePlane</td><td>Invested</td><td>Take call</td><td class="ok">✓ Agree</td><td>n/a</td><td class="warn">▲ later press found, ignored</td></tr>
<tr><td>AeroDrop</td><td>Passed</td><td>Hold</td><td class="warn">▲ Differs</td><td>Fund (no customer, no regulator plan)</td><td class="ok">✓ clean</td></tr>
<tr><td>Giva</td><td>Invested</td><td>Take call</td><td class="ok">✓ Agree</td><td>n/a</td><td class="warn">▲ later funding found, ignored</td></tr>
<tr><td>CampusCredit</td><td>Passed</td><td>Take call</td><td class="bad">✕ Differs</td><td>Fund (founder did not own risk): tool missed it</td><td class="ok">✓ clean</td></tr></table>
<div class="note">Memos carry no dates, so search cannot be cut off exactly. Passes are survivorship-skewed. Counts only, no percentage.</div></div>
<div class="two"><div class="sec"><h2>Failures, with the cause</h2>
<table><tr><th>CASE</th><th>CAUSE</th><th>STATUS</th></tr>
<tr><td>#88 Founder reply read as yes</td><td>"Maybe next quarter" classed as interested</td><td class="warn">Fix in progress</td></tr>
<tr><td>#141 Overlap by what it does</td><td>Adjacent product missed at low similarity</td><td class="ok">Fixed, rerun passed</td></tr></table></div>
<div class="sec"><h2>Judge against human</h2><div class="card">8% of results graded blind by a person. <b>2 mismatches</b> logged. Judge model is from a different family than the agent.</div></div></div>'''
open('screen4-rough.html','w').write(page('Trust report',s4))
