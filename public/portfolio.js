(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cr = (n) => "₹" + n.toFixed(1) + " Cr";
  const pct = (n) => (n > 0 ? "+" : "") + Math.round(n) + "%";
  // One cobalt ramp (DESIGN.md), ordered dark/light so neighbouring slices stay apart; Other is grey. Labels carry identity.
  const RAMP = [1, 2, 3, 4, 5].map((n) => `var(--chart-${n})`), OTHER = "var(--chart-other)";
  const ICON = { Healthy: ["ok", "✓"], Watch: ["warn", "▲"], "At risk": ["bad", "✕"] };

  async function api(path) {
    const res = await fetch(path);
    const data = await res.json().catch(() => ({ error: "The app is not responding." }));
    if (res.status === 401 && data.login) { location.replace("/login.html"); throw new Error("Sign in first."); }
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  function donut(sectors, total) {
    const R = 80, r = 52, cx = 100, cy = 100;
    let a = -Math.PI / 2;
    const arcs = sectors.map((s, i) => {
      const sweep = (s.share / 100) * Math.PI * 2, end = a + sweep, big = sweep > Math.PI ? 1 : 0;
      const p = (rad, ang) => `${(cx + rad * Math.cos(ang)).toFixed(2)} ${(cy + rad * Math.sin(ang)).toFixed(2)}`;
      const d = `M ${p(R, a)} A ${R} ${R} 0 ${big} 1 ${p(R, end)} L ${p(r, end)} A ${r} ${r} 0 ${big} 0 ${p(r, a)} Z`;
      a = end;
      const fill = s.sector === "Other" ? OTHER : RAMP[i];
      return `<path d="${d}" fill="${fill}" stroke="var(--surface-2)" stroke-width="2" data-i="${i}"><title>${esc(s.sector)}: ${cr(s.invested_cr)}, ${s.share}%</title></path>`;
    }).join("");
    const legend = sectors.map((s, i) => `<li data-i="${i}"><span class="sw" style="background:${s.sector === "Other" ? OTHER : RAMP[i]}" aria-hidden="true"></span>
      <span>${esc(s.sector)}${s.includes ? `<span class="muted small"> (${esc(s.includes.join(", "))})</span>` : ""}</span>
      <span class="r">${cr(s.invested_cr)}</span><span class="r muted">${s.share}%</span></li>`).join("");
    return `<div class="donut"><svg viewBox="0 0 200 200" width="200" height="200" role="img" aria-label="Invested by sector: ${esc(sectors.map((s) => s.sector + " " + s.share + "%").join(", "))}">${arcs}<circle cx="100" cy="100" r="80.5" fill="none" stroke="var(--border)"/><circle cx="100" cy="100" r="51.5" fill="none" stroke="var(--border)"/>
      <text x="100" y="96" text-anchor="middle" class="d-num">${cr(total)}</text><text x="100" y="116" text-anchor="middle" class="d-lab">invested</text></svg>
      <ul class="legend">${legend}</ul></div>`;
  }

  function spark(series) {
    const w = 96, h = 28, min = Math.min(...series), max = Math.max(...series), span = max - min || 1;
    const pts = series.map((v, i) => `${(i * (w - 4) / (series.length - 1) + 2).toFixed(1)},${(h - 3 - (v - min) / span * (h - 6)).toFixed(1)}`).join(" ");
    const last = pts.split(" ").pop().split(",");
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/><circle cx="${last[0]}" cy="${last[1]}" r="3" fill="var(--accent)" stroke="var(--surface-2)" stroke-width="2"/></svg>`;
  }

  const days = (n) => n === 0 ? "today" : n === 1 ? "1 day ago" : n + " days ago";
  const status = (h) => `<span class="${ICON[h][0]} nw">${ICON[h][1]} ${h}</span>`;

  function rows(cos) {
    return cos.map((c, i) => `<tr>
      <td><button class="link exp" type="button" aria-expanded="false" aria-controls="b${i}">${esc(c.name)}</button><div class="muted small">${esc(c.sector)}</div></td>
      <td class="r">${cr(c.invested_cr)}</td><td class="r">${cr(c.value_cr)}</td><td class="r">${c.multiple.toFixed(1)}×</td>
      <td class="nw">${spark(c.revenue_lakh)} <span class="sr-only">Revenue </span><span class="small-n">${pct(c.growth_3m)} 3 mo</span></td>
      <td class="r">${c.runway_months.toFixed(1)} mo</td>
      <td>${status(c.health)}<div class="muted small">${esc(c.reasons[0])}</div></td>
      <td class="nw">${days(c.days_since_update)}</td></tr>
      <tr class="brief" id="b${i}" hidden><td colspan="8"><div class="brief-in">
        <p><strong>${esc(c.what)}</strong></p>
        <dl class="facts"><dt>Founders</dt><dd>${esc(c.founders)}</dd><dt>Invested</dt><dd>${cr(c.invested_cr)} on ${esc(new Date(c.invested_on).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }))}</dd>
        <dt>Revenue</dt><dd>₹${c.revenue_lakh[11].toFixed(1)} lakh last month, ${pct(c.growth_3m)} over 3 months · burn ₹${c.burn_lakh} lakh a month</dd>
        <dt>Health</dt><dd>${status(c.health)}: ${esc(c.reasons.join("; "))}</dd><dt>Latest update</dt><dd>${esc(c.note)}</dd></dl></div></td></tr>`).join("");
  }

  function draw(v) {
    const m = v.money, n = v.counts;
    $("#asof").textContent = "Fund II: money, where it is invested, and how each company is doing. As of " +
      new Date(v.as_of).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) + ".";
    $("#pf").innerHTML = `
      <section class="band money" aria-label="Money">
        <div><div class="label-d">Total invested</div><div class="num">${cr(m.invested_cr)}</div><div class="small-d">${v.companies.length} companies</div></div>
        <div><div class="label-d">Cash in the bank</div><div class="num">${cr(m.cash_cr)}</div></div>
        <div><div class="label-d">Incoming capital</div><div class="num">${cr(m.incoming_cr)}</div><div class="small-d">committed, not yet called</div></div>
        <div><div class="label-d">Free to deploy</div><div class="verdict">${cr(m.free_cr)}</div><div class="small-d">after ${cr(m.reserve_cr)} kept for follow-ons</div></div>
      </section>
      <p class="muted small">${esc(v.public.text)} · <span class="src">${esc(v.public.source)}, ${esc(v.public.date)}</span></p>
      <div class="two">
        <section class="panel" aria-labelledby="sec-h"><h2 id="sec-h">Invested by sector</h2>${donut(v.sectors, m.invested_cr)}</section>
        <section class="panel" aria-labelledby="hl-h"><h2 id="hl-h">Company health</h2>
          <ul class="counts"><li>${status("Healthy")} <strong>${n.Healthy}</strong></li><li>${status("Watch")} <strong>${n.Watch}</strong></li><li>${status("At risk")} <strong>${n["At risk"]}</strong></li></ul>
          <p class="muted small">At risk: runway under 6 months, no update for over 60 days, or revenue down more than 10% over 3 months. Watch: runway under 12 months, no update for over 30 days, revenue up less than 5%, or burn over 3× revenue.</p>
        </section>
      </div>
      <section class="panel" aria-labelledby="co-h"><h2 id="co-h">Companies</h2>
        <div class="scroll" tabindex="0" role="region" aria-label="Portfolio companies"><table class="pf">
          <thead><tr><th>Company</th><th class="r">Invested</th><th class="r">Value now</th><th class="r">Multiple</th><th>Revenue, 12 months</th><th class="r">Runway</th><th>Health</th><th>Last update</th></tr></thead>
          <tbody>${rows(v.companies)}</tbody></table></div>
        <p class="muted small">Choose a company for its brief.</p>
      </section>`;
    Motion.reveal($(".band.money")); Motion.ambient($(".band.money"));
    document.querySelectorAll(".exp").forEach((b) => b.addEventListener("click", () => {
      const open = b.getAttribute("aria-expanded") !== "true";
      b.setAttribute("aria-expanded", String(open));
      document.getElementById(b.getAttribute("aria-controls")).hidden = !open;
    }));
    const hi = (i, on) => document.querySelectorAll(`[data-i="${i}"]`).forEach((el) => el.classList.toggle("hi", on));
    document.querySelectorAll(".donut [data-i]").forEach((el) => {
      el.addEventListener("mouseenter", () => hi(el.dataset.i, true));
      el.addEventListener("mouseleave", () => hi(el.dataset.i, false));
    });
  }

  api("/api/me").then((me) => {
    if (me.role !== "kushal" && me.login_required) return location.replace("/");
    $("#signout").hidden = !me.login_required;
  }).catch(() => {});
  $("#signout").addEventListener("click", async () => { await fetch("/api/logout", { method: "POST" }).catch(() => {}); location.replace("/login.html"); });
  api("/api/portfolio").then(draw).catch((e) => { $("#pf").innerHTML = `<p class="error" role="alert">${esc(e.message)}</p>`; });
})();
