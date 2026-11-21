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
    $("#rows").innerHTML = rows.map((r) => `<tr>
      <td><strong>${esc(r.company)}</strong><div class="muted small">${esc(r.sector_label)} · ${esc(r.stage)}</div></td>
      <td class="nw">${call(r.recommendation)}${r.total != null ? ` <span class="muted">${r.total}</span>` : ""}${r.gates && r.gates.length ? `<div class="muted small">${esc(r.gates.join(", "))}</div>` : ""}</td>
      <td class="nw">${call(r.riya)}</td>
      <td class="nw">${r.agrees == null ? '<span class="muted">—</span>' : r.agrees ? '<span class="ok">✓ Agrees</span>' : '<span class="warn">▲ Disagrees</span>'}</td>
      <td>${r.reason ? esc(r.reason) : '<span class="muted">none</span>'}</td>
      <td class="nw">${esc(r.meeting)}</td></tr>`).join("");
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
    try { const d = await api("/api/outcomes"); drawRows(d.rows); drawThesis(d.thesis); }
    catch (e) { $("#rows").innerHTML = `<tr><td colspan="6" class="error" role="alert">${esc(e.message)}</td></tr>`; }
  }

  api("/api/me").then((me) => {
    if (me.role !== "kushal" && me.login_required) return location.replace("/");
    $("#signout").hidden = !me.login_required;
  }).catch(() => {});
  $("#signout").addEventListener("click", async () => { await api("/api/logout", {}).catch(() => {}); location.replace("/login.html"); });
  load();
})();
