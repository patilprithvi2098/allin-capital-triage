(() => {
  const $ = (s) => document.querySelector(s);
  const CRIT = { founder_quality: "Founder quality", path_to_market: "Path to market", evidence_quality: "Evidence quality",
    defensibility: "Defensibility", sector_fit: "Sector fit", capital_fit: "Capital fit" };
  const FACT = { customers: "Customers", repeat_customers: "Repeat customers", revenue: "Revenue or GMV", cac: "Acquisition cost",
    raise: "Raise", valuation: "Valuation", team_size: "Team size", funding_of_credit: "How credit is funded", location: "Location", investors: "Existing investors" };
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const inr = (t) => esc(String(t || "").replace(/INR /g, "₹"));
  let apps = [], current = null, poll = null, busy = false;

  async function api(path, body) {
    const res = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({ error: "The app is not responding." }));
    if (res.status === 401 && data.login) { location.replace("/login.html"); throw new Error("Sign in first."); }
    if (!res.ok) { const e = new Error(data.error || "Something went wrong."); e.field = data.field; throw e; }
    return data;
  }

  // ---------- batch list
  const chip = (a) => a.decision ? `<span class="chip">${a.decision === "go" ? "✓ You: Go" : "✕ You: No-go"}</span>`
    : a.recommendation ? `<span class="chip">Tool: ${esc(a.recommendation)}</span>` : "";
  function drawList() {
    $("#apps").innerHTML = apps.map((a) => `<li><button type="button" class="app" data-id="${esc(a.id)}"${a.id === current ? ' aria-current="true"' : ""}>
      <span class="app-h">${esc(a.company)}</span><span class="app-p">${esc(a.sector_label)} · ${esc(a.stage)} · ${inr(a.raise)}</span>${chip(a)}</button></li>`).join("");
  }
  function loadList() {
    return api("/api/applications").then((d) => { $("#testbar").hidden = !d.test_mode; apps = d.applications; drawList(); })
      .catch((e) => { $("#apps").innerHTML = `<li class="error" role="alert">${esc(e.message)}</li>`; });
  }
  $("#apps").addEventListener("click", (ev) => { const b = ev.target.closest(".app"); if (b) open(b.dataset.id); });

  // ---------- one application
  async function open(id) {
    clearTimeout(poll); current = id; drawList();
    const a = apps.find((x) => x.id === id);
    $("#view").innerHTML = `<h1>${esc(a.company)}</h1><p class="muted">Loading…</p>`;
    try { show(a, await api("/api/read?id=" + encodeURIComponent(id))); }
    catch (e) { $("#view").innerHTML = `<h1>${esc(a.company)}</h1><p class="error" role="alert">${esc(e.message)}</p>`; }
    $("#main").focus(); // on phone the read sits under the list: bring it into view
  }

  function show(a, st) {
    if (a.id !== current) return;
    if (st.state === "done") return drawRead(st.read, st.decision);
    const head = `<h1>${esc(a.company)}</h1><p class="meta">${esc(a.sector_label)} · ${esc(a.stage)} · ${inr(a.raise)}</p>`;
    if (st.state === "running") {
      $("#view").innerHTML = head + `<div class="panel" role="status"><strong>Reading…</strong> Checking deck against form, searching, scoring. About 30 seconds.</div>`;
      poll = setTimeout(async () => { try { show(a, await api("/api/read?id=" + encodeURIComponent(a.id))); } catch (e) { show(a, { state: "error", error: e.message }); } }, 2500);
      return;
    }
    $("#view").innerHTML = head + (st.state === "error" ? `<p class="error" role="alert">${esc(st.error)}</p>` : `<p class="muted">Not read yet.</p>`) +
      `<button class="btn primary" id="run" type="button">${st.state === "error" ? "Run the read again" : "Run the read"}</button>`;
    $("#run").addEventListener("click", () => runRead(a));
  }

  async function runRead(a) {
    const b = $("#run"); if (!b || b.disabled) return;
    b.disabled = true; b.textContent = "Starting…";
    show(a, { state: "running" }); // on Vercel the answer is the finished read itself, after about 30 seconds
    try { const d = await api("/api/read", { id: a.id }); show(a, d.state === "done" || d.state === "error" ? d : { state: "running" }); }
    catch (e) { show(a, { state: "error", error: e.message }); }
  }

  const src = (x, r) => {
    if (x.source === "portfolio") return `<span class="src">Portfolio · <a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">fund's portfolio page</a></span> <q>${esc(x.quote)}</q>`;
    if (x.source === "web") {
      const e = (r.evidence || []).find((v) => v.id === x.evidence_id);
      return `<span class="src">Web · ${e ? (/^https?:\/\//i.test(e.url || "") ? `<a href="${esc(e.url)}" target="_blank" rel="noopener noreferrer">${esc(e.title || e.url)}</a>` : esc(e.title || e.url)) : esc(x.evidence_id)}</span> <q>${esc(x.quote)}</q>`;
    }
    return `<span class="src">${x.source === "deck" ? "Deck" : "Form"}</span> <q>${esc(x.quote)}</q>`;
  };
  const reasons = (list, r) => list.length ? `<ul class="reasons">${list.map((x) => `<li><span>${esc(x.text)}</span>${src(x, r)}</li>`).join("")}</ul>` : `<p class="muted">None with a checkable source.</p>`;
  const status = (s) => s === "differs" ? `<span class="warn">▲ Differs</span>` : s === "matches" ? `<span class="ok">✓ Matches</span>` : `<span class="muted">${esc(s)}</span>`;

  function drawRead(r, decision) {
    const searched = r.trail.every((t) => t.stop_reason === "no_key") ? "Web search not run: no Tavily key yet. Outside facts are unfindable, so founder and evidence scores are capped."
      : `Web search: ${r.trail.filter((t) => t.query).length} queries, ${r.evidence.length} sources kept, searched ${esc(r.searched_at)}.`;
    $("#view").innerHTML = `
      <h1>${esc(r.company)}</h1>
      <p class="what">${esc(r.what_it_does)}</p>
      <p class="meta">Sector it picked: ${esc(r.sector_label)} · ${esc(r.stage)} · Raising ${inr(r.raise)} · ${esc(r.source)}</p>
      <section class="band" aria-label="Recommendation">
        <div><div class="label-d">Tool recommends</div><div class="verdict">${r.recommendation === "GO" ? "✓ GO" : "✕ NO-GO"}</div></div>
        <div><div class="label-d">Score</div><div class="num">${r.total}<span> / 100</span></div><div class="small-d">Benchmark ${r.benchmark} (provisional)</div></div>
        <div><div class="label-d">Confidence</div><div class="num">${esc(r.confidence)}</div><div class="small-d">${r.dropped_claims ? r.dropped_claims + " unsourced claims removed" : "Every claim sourced"}</div></div>
      </section>
      ${(r.notes || []).map((n) => `<p class="warn" role="note">▲ ${esc(n)}</p>`).join("") || (r.injection_seen ? `<p class="warn" role="alert">▲ The deck or form contains text that tries to instruct the reader. It was ignored.</p>` : "")}
      ${(r.corrections_applied || []).map((a) => `<section class="panel corr" aria-label="Correction ${a.n} applied">
        <p><strong>Correction #${a.n} applied</strong> · ${esc(CRIT[a.criterion] || a.criterion)} ${a.moved >= 0 ? "+" : ""}${a.moved} · learned from ${esc(a.from)}</p>
        <p class="small">${esc(a.lesson)}</p><p class="small muted">${esc(a.similar_because)}</p>
        <button class="link" type="button" data-reject="${a.n}">Doesn't apply here</button></section>`).join("")}
      <div class="yesno">
        <section class="panel"><h2>Why yes</h2>${reasons(r.why_yes, r)}</section>
        <section class="panel"><h2>Why no</h2>${reasons(r.why_no, r)}${r.portfolio_note ? `<p class="muted small">${esc(r.portfolio_note)}</p>` : ""}</section>
      </div>
      <section class="panel"><h2>Score by criterion</h2>
        <div class="scroll" tabindex="0" role="region" aria-label="Score by criterion"><table class="crit"><thead><tr><th>Criterion</th><th class="r">Points</th><th>Why</th><th>Source</th><th>Confidence</th></tr></thead><tbody>
        ${r.criteria.map((c) => `<tr><td class="c-name">${esc(CRIT[c.key] || c.key)}</td><td class="r nw c-pts">${c.points} / ${c.max}${c.points_before != null && c.points_before !== c.points ? `<div class="muted small">was ${c.points_before}</div>` : ""}</td><td class="c-why">${esc(c.why)}${c.rules.length ? `<div class="muted small">${esc(c.rules.join("; "))}</div>` : ""}${c.missing.length ? `<div class="muted small">Missing: ${c.missing.map((m) => esc(m.item) + (m.kind === "unfindable" ? " (not found outside the deck)" : " (founder did not say)")).join("; ")}</div>` : ""}</td><td>${c.claims.slice(0, 2).map((x) => `<div>${src(x, r)}</div>`).join("") || '<span class="muted">none</span>'}</td><td class="c-conf" data-label="Confidence">${esc(c.confidence)}</td></tr>`).join("")}
        </tbody></table></div></section>
      <section class="panel"><h2>Deck against form</h2>
        <div class="scroll" tabindex="0" role="region" aria-label="Deck against form"><table class="facts"><thead><tr><th>Fact</th><th>Deck</th><th>Form</th><th>Status</th></tr></thead><tbody>
        ${r.facts.map((f) => `<tr><td class="f-name">${esc(FACT[f.key] || f.key)}</td><td data-label="Deck">${inr(f.deck) || '<span class="muted">not stated</span>'}</td><td data-label="Form">${inr(f.form) || '<span class="muted">not stated</span>'}</td><td class="f-st">${status(f.status)}${f.status === "differs" ? `<div class="small ${f.material ? "warn" : "muted"}">${f.material ? "Material" : "Minor"}${f.why ? ": " + esc(f.why) : ""}</div>` : ""}</td></tr>`).join("")}
        </tbody></table></div>
        <p class="muted small">${searched}</p></section>
      <section class="panel decide" aria-labelledby="dec-h"><h2 id="dec-h">Your call</h2>
        <p class="muted">The tool only recommends. Nothing happens until you choose.</p>
        <div class="row"><button class="btn" type="button" data-call="go">Go: take the call</button><button class="btn" type="button" data-call="nogo">No-go: reject</button></div>
        <label for="reason">Reason <span class="muted">(required when your call differs from the tool's)</span></label>
        <textarea id="reason" maxlength="500" rows="2">${esc(decision?.reason || "")}</textarea>
        <p id="dec-msg" aria-live="polite">${decision ? saved(decision) : ""}</p>
      </section>
      <p class="muted small">Read ${esc(r.created_at.replace("T", " "))} · thesis ${esc(r.thesis_version)} · ${esc(r.seconds)} s · $${esc(r.cost_usd)} · <button class="link" id="rerun" type="button">Run the read again</button></p>`;
    document.querySelectorAll("[data-call]").forEach((b) => b.addEventListener("click", () => decide(r, b.dataset.call)));
    Motion.reveal($("#view")); Motion.beams($("#view")); document.querySelectorAll("#view .band").forEach(Motion.ambient);
    document.querySelectorAll("[data-reject]").forEach((b) => b.addEventListener("click", async () => {
      if (b.disabled) return;
      b.disabled = true; b.textContent = "Undoing…";
      try { const d = await api("/api/correction/reject", { id: r.id, n: Number(b.dataset.reject) }); drawRead(d.read, decision);
        $("#dec-msg").innerHTML = `<span class="ok">✓ Correction #${esc(b.dataset.reject)} removed from this read; it won't be matched to ${esc(r.company)} again.</span>`; }
      catch (e) { b.disabled = false; b.textContent = "Doesn't apply here"; b.insertAdjacentHTML("afterend", `<span class="error" role="alert"> ${esc(e.message)}</span>`); }
    }));
    $("#rerun").addEventListener("click", async () => { try { await api("/api/read", { id: r.id }); show(apps.find((x) => x.id === r.id), { state: "running" }); } catch (e) { $("#dec-msg").innerHTML = `<span class="error" role="alert">${esc(e.message)}</span>`; } });
  }

  const saved = (d) => `<span class="ok">✓ Saved: ${d.call === "go" ? "Go" : "No-go"}${d.disagrees ? " (differs from the tool; your reason becomes a correction for similar companies)" : ""}.</span>`;

  async function decide(r, call) {
    if (busy) return;
    const reason = $("#reason").value.trim(), differs = (call === "go") !== (r.recommendation === "GO");
    if (differs && !reason) {
      $("#dec-msg").innerHTML = `<span class="error" role="alert">Your call differs from the tool's. Say why in one line.</span>`;
      $("#reason").setAttribute("aria-invalid", "true"); $("#reason").focus(); return;
    }
    busy = true; document.querySelectorAll("[data-call]").forEach((b) => (b.disabled = true));
    try {
      const d = await api("/api/decision", { id: r.id, call, reason });
      $("#reason").removeAttribute("aria-invalid");
      $("#dec-msg").innerHTML = saved(d.decision);
      const a = apps.find((x) => x.id === r.id); if (a) { a.decision = call; drawList(); }
    } catch (e) { $("#dec-msg").innerHTML = `<span class="error" role="alert">${esc(e.message)}</span>`; }
    finally { busy = false; document.querySelectorAll("[data-call]").forEach((b) => (b.disabled = false)); }
  }

  // ---------- whole batch in one run
  // On Vercel the page runs the batch: one read per request, in order, the same progress as the server-side run
  async function batchInPage(ids) {
    const b = { state: "running", done: 0, total: ids.length, current: null, errors: [] };
    for (const id of ids) {
      b.current = (apps.find((x) => x.id === id) || {}).company || id;
      batchState(b, true);
      let stop = false;
      try { const d = await api("/api/read", { id }); if (d.state === "error") { b.errors.push({ id, company: b.current, error: d.error }); stop = /out of credit|key was refused/.test(d.error); } }
      catch (e) { b.errors.push({ id, company: b.current, error: e.message }); }
      b.done += 1;
      if (stop) break; // no credit or a refused key: the next read would fail the same way
    }
    b.state = "done"; b.current = null;
    batchState(b, true);
  }

  let hero = null;
  async function batchState(b, local) {
    const btn = $("#batch");
    if (b.state === "running") {
      if (!hero) { $("#hero").hidden = false; hero = Motion.hero($("#hero")); Motion.ambient($("#hero")); }
      hero.update(b, apps.map((x) => x.company));
      btn.disabled = true; btn.textContent = "Reading…";
      $("#batch-msg").textContent = `Read ${b.done} of ${b.total}${b.current ? " · now " + b.current : ""}`;
      if (!local) setTimeout(async () => { try { batchState(await api("/api/batch")); } catch (e) { $("#batch-msg").textContent = e.message; } }, 3000);
    } else {
      if (hero) { hero.stop(); hero = null; $("#hero").hidden = true; $("#hero").innerHTML = ""; }
      btn.disabled = false; btn.textContent = b.state === "done" ? "Read all 10 again" : "Read all 10";
      if (b.state === "done") {
        const why = [...new Set(b.errors.map((e) => e.error).filter((t) => t.startsWith("Not read")))].join(" ");
        $("#batch-msg").textContent = `Read ${b.done - b.errors.length} of ${b.total}.` + (b.errors.length ? ` Stopped: ${b.errors.map((e) => e.company).join(", ")} (open it to run again).` : "") + (why ? " " + why : "");
        await loadList(); if (current) open(current);
      }
    }
  }
  $("#batch").addEventListener("click", async () => {
    const btn = $("#batch"); if (btn.disabled) return;
    btn.disabled = true; btn.textContent = "Starting…";
    try { const d = await api("/api/batch", {}); if (d.client) await batchInPage(d.ids); else batchState(d.batch); }
    catch (e) { $("#batch-msg").innerHTML = `<span class="error" role="alert">${esc(e.message)}</span>`; btn.disabled = false; btn.textContent = "Read all 10"; }
  });

  // ---------- who is signed in
  { const d = new Date(); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); // this week's Monday
    $("#who").textContent = "Riya · Week of " + d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }); }
  api("/api/me").then((me) => {
    if (me.role === "kushal") return location.replace("/kushal.html");
    $("#signout").hidden = !me.login_required;
  }).catch(() => {});
  $("#signout").addEventListener("click", async () => { await api("/api/logout", {}).catch(() => {}); location.replace("/login.html"); });

  loadList().then(() => api("/api/batch")).then((b) => { if (b.state === "running") batchState(b); }).catch(() => {});
})();
