(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  let busy = false;

  async function api(path, body) {
    const res = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({ error: "The app is not responding." }));
    if (res.status === 401 && data.login) { location.replace("/login.html"); throw new Error("Sign in first."); }
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  const call = (v) => v === "GO" || v === "go" ? '<span class="ok">✓ Go</span>' : v ? '<span class="bad">✕ No-go</span>' : '<span class="muted">not yet</span>';

  function drawRows(rows) {
    const reasons = (xs) => xs.length ? `<ul class="reasons">${xs.map((x) => `<li><span>${esc(x.text)}</span>${x.source ? `<span class="src">${esc(x.source)}</span>` : ""}</li>`).join("")}</ul>` : '<p class="muted small">None with a checkable source.</p>';
    $("#rows").innerHTML = rows.map((r, i) => `<tr>
      <td><button class="link exp" type="button" aria-expanded="false" aria-controls="ob${i}">${esc(r.company)}</button><div class="muted small">${esc(r.sector_label)} · ${esc(r.stage)}</div></td>
      <td class="nw">${call(r.recommendation)}${r.total != null ? ` <span class="muted">${r.total}</span>` : ""}${r.gates && r.gates.length ? `<div class="muted small">${esc(r.gates.join(", "))}</div>` : ""}</td>
      <td class="nw">${call(r.riya)}</td>
      <td class="nw">${r.agrees == null ? '<span class="muted">—</span>' : r.agrees ? '<span class="ok">✓ Agrees</span>' : '<span class="warn">▲ Disagrees</span>'}</td>
      <td>${r.reason ? esc(r.reason) : '<span class="muted">none</span>'}</td>
      <td class="nw">${esc(r.meeting)}</td></tr>
      <tr class="brief" id="ob${i}" hidden><td colspan="6"><div class="brief-in">
        <p><strong>${r.what_it_does ? esc(r.what_it_does) : "Not read yet."}</strong></p>
        <dl class="facts"><dt>Stage and raise</dt><dd>${esc(r.stage)} · ${esc(r.raise)}</dd><dt>Founders</dt><dd>${esc((r.founders || []).join(", ")) || '<span class="muted">not given</span>'}</dd>
        <dt>Recommendation</dt><dd>${r.recommendation ? `${call(r.recommendation)} · ${r.total} against a benchmark of ${r.benchmark}` : '<span class="muted">not read yet</span>'}</dd></dl>
        ${r.recommendation ? `<div class="yesno"><div><h3 class="h3">Why yes</h3>${reasons(r.why_yes || [])}</div><div><h3 class="h3">Why no</h3>${reasons(r.why_no || [])}</div></div>` : ""}
      </div></td></tr>`).join("");
    document.querySelectorAll("#rows .exp").forEach((b) => b.addEventListener("click", () => {
      const open = b.getAttribute("aria-expanded") !== "true";
      b.setAttribute("aria-expanded", String(open));
      document.getElementById(b.getAttribute("aria-controls")).hidden = !open;
    }));
  }

  function drawThesis(t) {
    const waiting = t.versions.filter((v) => v.status === "waiting for approval");
    const head = `<p>Reads now use <strong>${esc(t.current)}</strong>${t.current.startsWith("v0") ? " (the public wording only; no version approved yet)" : ""}.</p>`;
    if (!waiting.length) { $("#thesis").innerHTML = head + '<p class="muted">Nothing waiting for your approval.</p>'; return; }
    const v = waiting[waiting.length - 1];
    $("#thesis").innerHTML = head + `
      <h3 class="h3">${esc(v.version)}: waiting for your approval</h3>
      <p class="muted small">Drafted from ${v.built_from.length} past memos (${esc(v.built_from.join(", "))}). Held out for the backtest: ${esc(v.held_out.join(", "))}.</p>
      <div class="scroll" tabindex="0" role="region" aria-label="Written against observed thesis"><table class="thesis"><thead><tr><th>Criterion</th><th>Written (public wording)</th><th>Observed (what the memos show)</th><th>Gap</th></tr></thead><tbody>
      ${v.criteria.map((c) => `<tr><td class="nw"><strong>${esc(c.name)}</strong><div class="muted small">${c.max} points</div></td><td>${esc(c.written)}</td>
        <td>${c.observed.map((o) => `<div class="obs">${esc(o.text)}<div class="small"><span class="src">Memo · ${esc(o.memo_name)}</span> <q>${esc(o.quote)}</q></div></div>`).join("") || '<span class="muted">nothing observed</span>'}</td>
        <td>${esc(c.gap)}</td></tr>`).join("")}
      </tbody></table></div>
      <button class="btn primary" id="approve" type="button" data-n="${v.n}">Approve ${esc(v.version)}</button>
      <p id="th-msg" aria-live="polite"></p>`;
    $("#approve").addEventListener("click", approve);
  }

  const CRIT = { founder_quality: "Founder quality", path_to_market: "Path to market", evidence_quality: "Evidence quality",
    defensibility: "Defensibility", sector_fit: "Sector fit", capital_fit: "Capital fit" };
  function drawCorrections(cs) {
    if (!cs.length) { $("#corr").innerHTML = '<p class="muted">No corrections yet. They appear when Riya disagrees with a recommendation and says why.</p>'; return; }
    $("#corr").innerHTML = `<div class="scroll" tabindex="0" role="region" aria-label="Corrections log"><table class="outcomes"><thead><tr><th>#</th><th>From</th><th>Riya's reason</th><th>Lesson</th><th>Change</th><th>Used on</th></tr></thead><tbody>
      ${cs.map((c) => `<tr><td>${c.n}</td><td>${esc(c.company)}</td><td>${esc(c.reason)}</td>
        <td>${c.worth_storing ? esc(c.lesson) + `<div class="muted small">Applies when: ${esc(c.applies_when)}</div>` : `<span class="muted">Not reused: ${esc(c.why_not)}</span>`}</td>
        <td class="nw">${c.worth_storing ? `${esc(CRIT[c.criterion] || c.criterion)} ${c.delta > 0 ? "+" : ""}${c.delta}` : "—"}</td>
        <td>${c.applied_to.length ? esc(c.applied_to.join(", ")) : '<span class="muted">not yet</span>'}${c.rejected_by.length ? `<div class="muted small">Rejected on ${esc(c.rejected_by.join(", "))}</div>` : ""}</td></tr>`).join("")}
      </tbody></table></div><p class="muted small">Each correction moves one score by at most 5 points; Riya can reject a match on any read.</p>`;
  }

  async function approve(ev) {
    const b = ev.currentTarget; if (busy) return;
    busy = true; b.disabled = true; b.textContent = "Approving…";
    try {
      const d = await api("/api/thesis/approve", { n: Number(b.dataset.n) });
      await load();
      $("#thesis").insertAdjacentHTML("afterbegin", `<p class="ok" role="status">✓ ${esc(d.version)} approved. New reads use it.</p>`);
    } catch (e) {
      $("#th-msg").innerHTML = `<span class="error" role="alert">${esc(e.message)}</span>`;
      b.disabled = false; b.textContent = "Approve";
    } finally { busy = false; }
  }

  async function load() {
    try { const d = await api("/api/outcomes"); drawRows(d.rows); drawThesis(d.thesis); drawCorrections(d.corrections || []); }
    catch (e) { $("#rows").innerHTML = `<tr><td colspan="6" class="error" role="alert">${esc(e.message)}</td></tr>`; }
  }

  api("/api/me").then((me) => {
    if (me.role !== "kushal" && me.login_required) return location.replace("/");
    $("#signout").hidden = !me.login_required;
  }).catch(() => {});
  $("#signout").addEventListener("click", async () => { await api("/api/logout", {}).catch(() => {}); location.replace("/login.html"); });
  load();
})();
