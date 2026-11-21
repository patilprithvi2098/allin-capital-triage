import math
ns = {}
exec(open('build_v2.py').read(), ns)
ns['css'] += '''
.tag2{display:inline-block;font-size:12px;font-weight:600;letter-spacing:.04em;padding:2px 8px;border-radius:4px;background:#FFF3C4;color:#5a3a00;border:1px solid #8A5A00;margin-left:8px;vertical-align:middle}
.money{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:14px}.money .card .v{font-family:'Space Grotesk';font-weight:700;font-size:32px}
.money .src{font-size:12px}.dash{display:grid;grid-template-columns:420px 1fr;gap:20px;margin-top:20px;align-items:start}
.leg{list-style:none;margin:12px 0 0;padding:0}.leg li{display:grid;grid-template-columns:14px 1fr auto auto;gap:10px;align-items:center;padding:5px 0;border-bottom:1px solid var(--stone);font-size:14px}
.leg i{width:12px;height:12px;border-radius:3px;display:block}.leg .r{font-variant-numeric:tabular-nums;text-align:right}
.drop td{background:#F2F5FF}.drop .box{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:18px;padding:6px 2px}
.drop h4{margin:0 0 4px;font-family:'Space Grotesk';font-size:14px}.caret{color:var(--mut);margin-right:6px}td.nw,th.nw{white-space:nowrap}
'''
ns['WM'] = '<div class="watermark">ROUGH MOCKUP. Applicant facts from the real decks and forms.</div>'
page = ns['page']; KT = ['Outcomes', 'Portfolio', 'Thesis', 'Trust report']

# ---- Outcomes with a drop-down brief open
def rec(v): return f'<span class="{"ok" if v.upper()=="GO" else "bad"}">{"✓" if v.upper()=="GO" else "✕"} {v}</span>'
rows = [('EarnWise','GO','Go','','Email sent'),('Talkbook','NO-GO','No-go','','Not contacted'),('Settlr','NO-GO','No-go','','Not contacted'),
        ('StockSathi','NO-GO','Go','The CAC gap is founder-time accounting; distribution background fits.','Draft not sent'),('GrainKind','GO','Go','','Booked Thu 26 Nov')]
tb = ''
for n,a,b,w,m in rows:
    tb += f'<tr><td><span class="caret">{"▾" if n=="StockSathi" else "▸"}</span><b>{n}</b></td><td>{rec(a)}</td><td>{rec(b)}</td><td class="{"ok" if a.upper()==b.upper() else "warn"}">{"Agrees" if a.upper()==b.upper() else "▲ Disagrees"}</td><td>{w or "<span class=mu>none</span>"}</td><td>{m}</td></tr>'
    if n == 'StockSathi':
        tb += '''<tr class="drop"><td colspan="6"><div class="box">
<div><h4>What it does</h4>B2B restocking app with 7 to 14 day credit for small-town kirana stores. Live in Karimnagar; 42 retailers, 22 reorder weekly. Raising ₹2 Cr at ₹12 Cr post. Warm intro from a Fund I founder.</div>
<div><h4>Founders</h4>Aarav Deshmukh (CEO): 8 years in FMCG distribution.<br>Pooja Nair (CTO): 5 years at a payments company; built the credit rules.</div>
<div><h4>Tool's call: NO-GO, 58 of 65</h4>Why no: deck and form disagree on three numbers; lends without NBFC registration.<br>Why yes: distribution operator; 22 of 38 stores reorder.</div></div></td></tr>'''
k1 = f'''<h1 style="font-size:30px">This week's outcomes</h1><div class="sub" style="color:var(--mut)">Read-only. Click a company to open its brief.</div>
<div class="sec"><table><tr><th>COMPANY</th><th>TOOL</th><th>RIYA</th><th>MATCH</th><th>RIYA'S REASON</th><th>MEETING</th></tr>{tb}</table><div class="note">Showing 5 of 10.</div></div>'''
open('kushal-1b-outcomes-open.html','w').write(page('Kushal outcomes','Kushal',KT,'Outcomes',k1))

# ---- Portfolio
sectors = [('Fintech',28,'#0047FF'),('Deeptech',22,'#eb6834'),('Consumer tech',19,'#1baf7a'),('Consumer brands',14,'#eda100'),('B2B SaaS',11,'#e87ba4'),('Other',6,'#008300')]
total = 92.0
cx, cy, R, r = 150, 150, 120, 74
a0, segs = -math.pi/2, ''
for name, pct, col in sectors:
    a1 = a0 + 2*math.pi*pct/100
    gap = 0.012  # 2px surface gap between slices
    s0, s1 = a0+gap, a1-gap
    large = 1 if (s1-s0) > math.pi else 0
    p = lambda ang, rad: (cx+rad*math.cos(ang), cy+rad*math.sin(ang))
    (x0,y0),(x1,y1),(x2,y2),(x3,y3) = p(s0,R),p(s1,R),p(s1,r),p(s0,r)
    segs += f'<path d="M{x0:.1f} {y0:.1f} A{R} {R} 0 {large} 1 {x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f} A{r} {r} 0 {large} 0 {x3:.1f} {y3:.1f} Z" fill="{col}"><title>{name}: {pct}% · ₹{total*pct/100:.1f} Cr</title></path>'
    if pct >= 11:
        mx, my = p((a0+a1)/2, (R+r)/2)
        segs += f'<text x="{mx:.0f}" y="{my+5:.0f}" text-anchor="middle" style="font:700 14px Inter;fill:#fff">{pct}%</text>'
    a0 = a1
donut = f'<svg viewBox="0 0 300 300" width="300" height="300" role="img" aria-label="Invested capital by sector">{segs}<text x="150" y="146" text-anchor="middle" style="font:700 26px Space Grotesk;fill:#0A0A0C">₹92 Cr</text><text x="150" y="168" text-anchor="middle" style="font:500 12px Inter;fill:#5A5F66">invested</text></svg>'
leg = ''.join(f'<li><i style="background:{c}"></i><span>{n}</span><span class="r">{p}%</span><span class="r">₹{total*p/100:.1f} Cr</span></li>' for n,p,c in sectors)

def spark(vals):
    w, h = 110, 30; mn, mx = min(vals), max(vals); rng = (mx-mn) or 1
    pts = ' '.join(f'{i*w/(len(vals)-1):.0f},{h-4-(v-mn)/rng*(h-8):.0f}' for i,v in enumerate(vals))
    lx, ly = pts.split()[-1].split(',')
    return f'<svg width="{w}" height="{h}" aria-hidden="true"><polyline points="{pts}" fill="none" stroke="#0A0A0C" stroke-width="2"/><circle cx="{lx}" cy="{ly}" r="3" fill="#0A0A0C"/></svg>'
port = [('Paisavaan','Fintech',4.2,13.8,[3,4,5,6,8,9],22,'ok','Healthy','Revenue up 12% QoQ; 22 months runway','2 days ago'),
        ('Tarangini Robotics','Deeptech',5.0,9.5,[1,1,2,2,3,3],14,'warn','Watch','Runway 14 months; pilots converting slower','9 days ago'),
        ('Silvermint Jewels','Consumer brands',3.1,7.4,[5,6,6,7,7,8],19,'ok','Healthy','Repeat rate 41%; profitable last quarter','5 days ago'),
        ('Krishiflow','Fintech',2.8,2.6,[6,6,5,5,4,4],7,'bad','At risk','Revenue down two quarters; 7 months runway','31 days ago'),
        ('Meghdoot Aero','Deeptech',6.0,6.0,[0,0,0,1,1,1],26,'ok','Healthy','Pre-revenue by plan; certification milestone met','12 days ago'),
        ('Docketly','B2B SaaS',2.4,4.1,[2,3,3,3,3,3],11,'warn','Watch','Growth flat 2 quarters; 11 months runway','18 days ago'),
        ('Raahi Fleet','Consumer tech',3.5,3.2,[4,4,3,3,3,2],8,'bad','At risk','No update in 67 days; runway 8 months','67 days ago')]
pt = ''.join(f'<tr><td><b>{n}</b></td><td>{s}</td><td class="r">₹{i:.1f} Cr</td><td class="r nw">₹{v:.1f} Cr</td><td class="r">{v/i:.1f}x</td><td>{spark(tr)}</td><td class="r">{rw} mo</td><td class="{c} nw">{"✓" if c=="ok" else "▲" if c=="warn" else "✕"} {h}</td><td>{why}</td><td class="mu nw">{u}</td></tr>' for n,s,i,v,tr,rw,c,h,why,u in port)
k2 = f'''<h1 style="font-size:30px">Portfolio</h1><div class="sub" style="color:var(--mut)">Fund money, where it sits, and how each company is doing.</div>
<div class="money">
<div class="card"><div class="lab">TOTAL INVESTED</div><div class="v">₹92 Cr</div><div class="src">Fund I, about $11 M deployed · public, as reported</div></div>
<div class="card"><div class="lab">CASH IN THE BANK</div><div class="v">₹61.4 Cr</div><div class="src">Fund II paid-in less investments</div></div>
<div class="card"><div class="lab">INCOMING CAPITAL</div><div class="v">₹115 Cr</div><div class="src">₹200 Cr target less ₹85 Cr first close · public, Mar 2025</div></div>
<div class="card"><div class="lab">FREE TO DEPLOY</div><div class="v" style="color:var(--cyan)">₹48.2 Cr</div><div class="src">Cash less follow-on reserve</div></div></div>
<div class="dash"><div class="card"><h2 style="font-size:18px">Invested capital by sector</h2><div style="display:flex;justify-content:center;margin-top:8px">{donut}</div><ul class="leg">{leg}</ul></div>
<div class="card"><h2 style="font-size:18px">Company health <span class="tag2">Updates every 30 s</span></h2>
<div class="note" style="margin:4px 0 10px">Rules: At risk if runway under 9 months, revenue down two quarters, or no update for 60 days. Watch if runway 9 to 15 months or growth flat. Healthy otherwise.</div>
<table><tr><th>COMPANY</th><th>SECTOR</th><th class="r">INVESTED</th><th class="r">VALUE NOW</th><th class="r">MULTIPLE</th><th>REVENUE, 6 QTRS</th><th class="r">RUNWAY</th><th>HEALTH</th><th>WHY</th><th>UPDATED</th></tr>{pt}</table>
<div class="note">Showing 7 companies.</div></div></div>'''
open('kushal-2-portfolio.html','w').write(page('Kushal portfolio','Kushal',KT,'Portfolio',k2))
print('ok')
