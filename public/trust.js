(() => {
  const $ = (s) => document.querySelector(s);
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const POINT = { compare: "Deck against form", gates: "Stage, sector and round gates", verify: "Source check", rules: "Score caps", recommend: "GO or NO-GO",
    overlap_verdict: "Overlap rules", overlap: "Portfolio overlap", facts: "Fact copying", read: "Full read", search_rule: "Search stop rule" };

  async function api(path, body) {
    const res = await fetch(path, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({ error: "The app is not responding." }));
    if (res.status === 401 && data.login) { location.replace("/login.html"); throw new Error("Sign in first."); }
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  const kstatus = (k) => k.status === "held" ? '<span class="ok">✓ Held</span>' : k.status === "broken" ? '<span class="bad">✕ Broken</span>'
    : k.status.startsWith("not fully") ? `<span class="warn">▲ ${esc(k.status.replace("not fully tested", "Not fully tested"))}</span>`
    : k.status.startsWith("not built") ? `<span class="muted">${esc(k.status.replace("not built yet: ", "Not built yet · "))}</span>` : '<span class="warn">▲ No cases yet</span>';

  function draw(t) {
    const r = t.run, b = t.backtest, a = t.audit;
    if (!r) { $("#report").innerHTML = '<p class="muted">No eval run yet. Run the harness: python3 evals/harness.py</p>'; return; }
    const sev = ["Critical", "High", "Low"].map((s) => { const v = r.by_severity[s]; return `<tr><td>${s}</td><td class="r">${v.pass}</td><td class="r">${v.fail + v.error}</td></tr>`; }).join("");
    const pts = Object.entries(r.by_point).map(([p, v]) => `<tr><td>${esc(POINT[p] || p)}</td><td class="r">${v.passed} of ${v.total}</td></tr>`).join("");
    const kills = Object.entries(r.kill_criteria).map(([id, k]) => `<tr><td class="nw"><strong>${id}</strong></td><td>${esc(k.text)}</td><td class="r">${k.cases}</td><td class="nw">${kstatus(k)}</td></tr>`).join("");
    const sc = r.self_checks;
    const fails = r.failures.length ? `<ul class="reasons">${r.failures.map((f) => `<li><span><strong>${esc(f.id)}</strong> · ${esc(f.severity)}${f.kill ? " · " + esc(f.kill) : ""} · ${esc(f.partition)}</span><span class="muted small">${esc(f.detail)}</span></li>`).join("")}</ul>` : '<p class="ok">✓ No failures in the last run.</p>';
    const judge = r.judge.used ? `${esc(r.judge.provider)} graded ${r.judge.judged} reads against their rubric; ${r.judge.judge_failed} did not hold.${r.judge.same_family ? " The judge is Claude Opus: same family as the model that writes reads (your choice), so the person's audit is the independent check." : ""}` : '<span class="warn">▲ Not run yet: no judge-model key. Soft checks (does the read reason correctly) are untested.</span>';
    const human = a ? `${a.graded} results graded blind by a person; judge and person agreed on ${a.agree} of ${a.compared}.${a.mismatches.length ? " Mismatches are logged." : ""}` : '<span class="warn">▲ Not done yet: python3 evals/audit.py</span>';
    let bt = '<p class="muted">Backtest not run yet.</p>';
    if (b) bt = `<p>Benchmark chosen on the 6 build memos: <strong>${b.benchmark}</strong> (agrees with ${esc(b.build_agree)}). On the 6 held-out memos the thesis never saw: agrees with <strong>${esc(b.held_out_agree)}</strong> (invested caught ${esc(b.held_out_invested_caught)}, passes caught ${esc(b.held_out_passed_caught)}).</p>
      <div class="scroll" tabindex="0" role="region" aria-label="Backtest"><table><thead><tr><th>Memo</th><th>Set</th><th>Actual</th><th class="r">Score</th><th>Tool</th><th>Match</th></tr></thead><tbody>
      ${b.rows.map((x) => `<tr><td>${esc(x.company)}</td><td>${x.set === "build" ? "Build" : "Held out"}</td><td>${x.actual === "INVESTED" ? "Invested" : "Passed"}</td><td class="r">${x.total}</td><td>${esc(x.call)}${x.gates.length ? ` <span class="muted small">${esc(x.gates.join(", "))}</span>` : ""}</td><td>${x.agrees ? '<span class="ok">✓</span>' : '<span class="bad">✕ Miss</span>'}</td></tr>`).join("")}</tbody></table></div>
      <p class="warn">▲ The live benchmark is still ${t.benchmark} (${esc(t.benchmark_status)}). Memo-based applications are thinner than real decks and score 20 to 30 points lower, so ${b.benchmark} cannot be applied to real applications as is.</p>
      <ul class="muted small">${b.caveats.map((c) => `<li>${esc(c)}</li>`).join("")}<li>${esc(b.leak_check)}</li></ul>`;
    $("#report").innerHTML = `
      <section class="panel"><h2>Last run</h2><p>${r.passed} of ${r.total} cases passed · ${esc(r.run_at.replace("T", " "))}</p>
        <div class="two"><div class="scroll" tabindex="0" role="region" aria-label="By severity"><table><thead><tr><th>Severity</th><th class="r">Passed</th><th class="r">Failed</th></tr></thead><tbody>${sev}</tbody></table></div>
        <div class="scroll" tabindex="0" role="region" aria-label="By decision point"><table><thead><tr><th>Decision point</th><th class="r">Passed</th></tr></thead><tbody>${pts}</tbody></table></div></div></section>
      <section class="panel"><h2>Kill criteria</h2><p class="muted">Any one of these failing stops the tool being used.</p>
        <div class="scroll" tabindex="0" role="region" aria-label="Kill criteria"><table><thead><tr><th>ID</th><th>Criterion</th><th class="r">Cases</th><th>Status</th></tr></thead><tbody>${kills}</tbody></table></div></section>
      <section class="panel"><h2>Backtest on past memos</h2>${bt}</section>
      <section class="panel"><h2>Failures and causes</h2>${fails}</section>
      <section class="panel"><h2>Who checked the checker</h2><ul class="reasons">
        <li><span>Harness self-checks: forced wrong output caught ${esc(sc.forced_wrong_caught)} · same verdict twice ${esc(sc.same_verdict_twice)} · test built to fail ${sc.should_fail_failed ? "failed, as it should" : "PASSED (harness not checking)"}</span></li>
        <li><span>Judge model: ${judge}</span></li><li><span>Person: ${human}</span></li></ul></section>`;
  }

  api("/api/me").then((me) => { $("#signout").hidden = !me.login_required; }).catch(() => {});
  $("#signout").addEventListener("click", async () => { await api("/api/logout", {}).catch(() => {}); location.replace("/login.html"); });
  api("/api/trust").then(draw).catch((e) => { $("#report").innerHTML = `<p class="error" role="alert">${esc(e.message)}</p>`; });
})();
