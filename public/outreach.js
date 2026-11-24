(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const when = (iso) => iso ? new Date(iso).toLocaleString("en-IN", { weekday: "short", day: "numeric", month: "short", hour: "numeric", minute: "2-digit", timeZone: "Asia/Kolkata" }) + " IST" : "";
  const STATUS = { draft: "Draft", sent: "Sent, waiting", counter_proposed: "Counter-proposed", confirmed: "Confirmed", booked: "✓ Booked",
    needs_human: "▲ Needs you", escalated: "▲ Needs you", timed_out: "▲ No reply", closed_not_interested: "✕ Not interested", skipped: "▲ Skipped", aborted: "✕ Stopped" };
  const cls = (s) => s === "booked" ? "ok" : ["needs_human", "escalated", "timed_out", "skipped"].includes(s) ? "warn" : ["closed_not_interested", "aborted"].includes(s) ? "bad" : "";
  let busy = false;

  async function api(path, body) {
    const res = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({ error: "The app is not responding." }));
    if (res.status === 401 && data.login) { location.replace("/login.html"); throw new Error("Sign in first."); }
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  // ---------- Screen 2: drafts
  function drawDrafts(rows) {
    const drafts = rows.filter((o) => o.status === "draft");
    if (!drafts.length) { $("#drafts").innerHTML = '<p class="muted">No drafts waiting. Make a final Go on an application and its draft appears here within a minute.</p>'; return; }
    $("#drafts").innerHTML = drafts.map((o) => `<section class="panel draft" data-id="${esc(o.id)}" aria-labelledby="d-${esc(o.id)}">
      <h2 id="d-${esc(o.id)}">${esc(o.company)}</h2>
      <p class="muted small">To ${esc(o.founder)} &lt;${esc(o.founder_email || "no address found")}&gt;${o.deeptech ? " · Aditya joins (deeptech)" : ""}</p>
      <p class="small"><strong>Proposed slots:</strong> ${o.slots.map(when).map(esc).join(" · ") || '<span class="warn">none free in the next two weeks</span>'}</p>
      <label for="s-${esc(o.id)}">Subject</label><input id="s-${esc(o.id)}" class="field" maxlength="200" value="${esc(o.draft.subject)}">
      <label for="b-${esc(o.id)}">Message</label><textarea id="b-${esc(o.id)}" class="field" rows="9" maxlength="4000">${esc(o.draft.body)}</textarea>
      <button class="btn primary" type="button" data-send="${esc(o.id)}">Send</button>
      <p class="msg" aria-live="polite"></p></section>`).join("");
    document.querySelectorAll("[data-send]").forEach((b) => b.addEventListener("click", () => send(b.dataset.send, b)));
  }

  async function send(id, b) {
    if (busy) return;
    const box = b.closest(".draft"), msg = box.querySelector(".msg");
    const subject = $(`#s-${CSS.escape(id)}`).value.trim(), body = $(`#b-${CSS.escape(id)}`).value.trim();
    if (!subject || !body) { msg.innerHTML = '<span class="error" role="alert">Write a subject and a message before sending.</span>'; return; }
    busy = true; b.disabled = true; b.textContent = "Sending…";
    try {
      await api("/api/outreach/send", { id, subject, body });
      box.innerHTML = `<h2>${esc(box.querySelector("h2").textContent)}</h2><p class="ok" role="status">✓ Sent. The agent takes it from here; follow it on Scheduling.</p>`;
    } catch (e) { msg.innerHTML = `<span class="error" role="alert">${esc(e.message)}</span>`; b.disabled = false; b.textContent = "Send"; }
    finally { busy = false; }
  }

  // ---------- Screen 3: scheduling (read-only)
  function drawSchedule(rows, alerts) {
    const sent = rows.filter((o) => o.status !== "draft");
    if (!sent.length) { $("#sched").innerHTML = '<p class="muted">Nothing sent yet. Sent emails and the agent’s progress appear here.</p>'; return; }
    $("#sched").innerHTML = (alerts.length ? alerts.map((a) => `<p class="warn" role="alert">▲ ${esc(a.text)}</p>`).join("") : "") + `
      <section class="panel"><div class="scroll" tabindex="0" role="region" aria-label="Conversations"><table class="outcomes"><thead><tr><th>Company</th><th>Status</th><th>Next step</th><th class="r">Round</th><th>Sent</th></tr></thead><tbody>
      ${sent.map((o) => `<tr><td><button class="link" type="button" data-hist="${esc(o.id)}">${esc(o.company)}</button></td>
        <td class="nw ${cls(o.status)}">${esc(STATUS[o.status] || o.status)}${o.booked ? `<div class="small">${esc(when(o.booked))}</div>` : ""}</td>
        <td>${esc((o.next || {}).what || "")}${(o.next || {}).at ? `<div class="muted small">${esc(when(o.next.at))}</div>` : ""}</td>
        <td class="r">${o.round}</td><td class="nw">${esc(when(o.sent_at))}</td></tr>`).join("")}</tbody></table></div></section>
      <section class="panel" id="hist" aria-live="polite"><h2>Email history</h2><p class="muted">Choose a company to see every message and step.</p></section>`;
    document.querySelectorAll("[data-hist]").forEach((b) => b.addEventListener("click", () => {
      const o = sent.find((x) => x.id === b.dataset.hist);
      $("#hist").innerHTML = `<h2>Email history · ${esc(o.company)}</h2><ul class="reasons">${o.history.map((h) => `<li><span>${esc(h.text)}</span><span class="muted small">${esc(when(h.at))} · ${esc(h.kind)}</span></li>`).join("")}</ul>`;
    }));
  }

  async function load() {
    try {
      const d = await api("/api/outreach");
      $("#testbar").hidden = !d.test_mode;
      if ($("#drafts")) drawDrafts(d.outreach);
      if ($("#sched")) drawSchedule(d.outreach, d.alerts || []);
    } catch (e) { ($("#drafts") || $("#sched")).innerHTML = `<p class="error" role="alert">${esc(e.message)}</p>`; }
  }

  api("/api/me").then((me) => { if (me.role === "kushal") return location.replace("/kushal.html"); $("#signout").hidden = !me.login_required; }).catch(() => {});
  $("#signout").addEventListener("click", async () => { await api("/api/logout", {}).catch(() => {}); location.replace("/login.html"); });
  load();
})();
