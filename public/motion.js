// DESIGN.md motion: one hero, four moments, one ambient. Ported from mesa-previews/motion-preview.html.
// Reduced motion: everything lands in its final state at once. Movement only, no fades. Never over tables or evidence.
window.Motion = (() => {
  const mq = matchMedia("(prefers-reduced-motion: reduce)");
  const rm = () => mq.matches;
  const phone = () => innerWidth < 640; // hero and ambient stay static on phones (DESIGN.md)
  const ease = (t) => 1 - Math.pow(1 - t, 3);
  function tween(ms, fn, done) {
    if (rm()) { fn(1); if (done) done(); return; }
    const t0 = performance.now();
    (function f(n) { const p = Math.max(0, Math.min(1, (n - t0) / ms)); fn(ease(p)); if (p < 1) requestAnimationFrame(f); else if (done) done(); })(t0);
  }

  // Moment 1: the verdict decrypts and the score counts up when a read is shown.
  function scramble(el, ms) {
    const final = el.textContent, ch = "01#/<>=+";
    if (rm() || !final) return;
    const t0 = performance.now();
    (function f(n) {
      const p = Math.max(0, Math.min(1, (n - t0) / ms)), k = Math.floor(p * final.length);
      el.textContent = [...final].map((c, i) => (i < k || c === " " ? c : ch[Math.floor(Math.random() * ch.length)])).join("");
      if (p < 1) requestAnimationFrame(f); else el.textContent = final;
    })(t0);
  }
  // Moment 2: a number counts up to its value (integers or one decimal; text around it is kept).
  function count(el, ms) {
    const m = el.firstChild && el.firstChild.nodeValue && el.firstChild.nodeValue.match(/^(\D*)(\d+(?:\.\d)?)(.*)$/s);
    if (!m) return;
    const [, pre, num, post] = m, to = parseFloat(num), dec = num.includes(".") ? 1 : 0;
    tween(ms, (p) => { el.firstChild.nodeValue = pre + (to * p).toFixed(dec) + post; });
  }
  function reveal(root) {
    root.querySelectorAll(".verdict").forEach((el) => scramble(el, 500));
    root.querySelectorAll(".num").forEach((el) => count(el, 700));
    root.querySelectorAll(".corr strong").forEach((el) => pulse(el));
  }

  // Moment 3: click a reason; a beam with a travelling dot runs from the claim to its source (CSS, 650 ms).
  function beams(root) {
    root.querySelectorAll(".reasons li").forEach((li) => {
      if (!li.querySelector(".src")) return;
      li.classList.add("traceable");
      li.addEventListener("click", (e) => {
        if (e.target.closest("a")) return;
        root.querySelectorAll(".reasons li.beam").forEach((x) => x !== li && x.classList.remove("beam"));
        li.classList.remove("beam"); void li.offsetWidth; li.classList.add("beam");
      });
    });
  }

  // Moment 4: a decision took effect. One pulse, or a snap into place.
  function pulse(el) { el.classList.remove("pulse"); void el.offsetWidth; el.classList.add("pulse"); }
  function snap(el) { el.classList.remove("snap"); void el.offsetWidth; el.classList.add("snap"); }

  // Hero: the batch run. Real progress: done applications sit at Review, the current one travels the stages, the rest wait.
  const STAGES = [["Intake", "rules"], ["Gather", "sources"], ["Judge", "AI"], ["Score", "matrix"], ["Review", "Riya"]];
  const X = [170, 335, 500, 665, 830]; // queue at x 40, done at x 900
  function hero(box) {
    const NS = "http://www.w3.org/2000/svg";
    box.innerHTML = `<svg viewBox="0 0 940 200" role="img" aria-label="Applications moving through five stages"></svg><p class="hero-prog" aria-hidden="true"></p>`;
    const svg = box.querySelector("svg"), prog = box.querySelector(".hero-prog");
    const el = (n, a, p) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); (p || svg).appendChild(e); return e; };
    const flow = el("path", { d: "M60 100 H900", class: "flow" });
    const nodes = STAGES.map((s, i) => {
      const g = el("g", { class: "node" });
      el("rect", { x: X[i] - 62, y: 64, width: 124, height: 72, rx: 4 }, g);
      el("text", { x: X[i], y: 97, "text-anchor": "middle" }, g).textContent = s[0];
      el("text", { x: X[i], y: 118, "text-anchor": "middle", class: "sub2" }, g).textContent = s[1];
      return g;
    });
    let dots = [], current = null, raf = 0;
    function update(b, names) {
      prog.innerHTML = `Read <b>${b.done}</b> of ${b.total}${b.current ? " · now " + b.current : ""}`;
      const fresh = !dots.length && names.length;
      if (fresh) dots = names.map((n) => { const g = el("g", { class: "dot" }); el("circle", { r: 11 }, g); el("text", { "text-anchor": "middle", y: 3.5 }, g).textContent = n.slice(0, 2); el("title", {}, g).textContent = n; return g; });
      dots.forEach((d, i) => {
        if (names[i] === b.current) return;
        const atEnd = i < b.done; // the batch reads in list order
        d.setAttribute("transform", `translate(${atEnd ? 900 : 40},${30 + i * 15})`);
      });
      flow.classList.toggle("go", b.state === "running" && !rm());
      if (b.current !== current || fresh) { current = b.current; travel(dots[names.indexOf(current)]); }
    }
    function travel(d) {
      cancelAnimationFrame(raf);
      if (!d) return;
      if (rm() || phone()) { d.setAttribute("transform", `translate(${X[2]},100)`); return; }
      const T = 3400, t0 = performance.now(), hit = new Set();
      (function f(n) {
        const p = ((n - t0) % T) / T, x = 60 + p * 840;
        d.setAttribute("transform", `translate(${x},100)`);
        X.forEach((nx, k) => { if (x >= nx - 62 && !hit.has(k)) { hit.add(k); nodes[k].classList.add("hit"); setTimeout(() => nodes[k].classList.remove("hit"), 420); } });
        if (p < 0.02) hit.clear();
        raf = requestAnimationFrame(f);
      })(t0);
    }
    return { update, stop: () => { cancelAnimationFrame(raf); flow.classList.remove("go"); } };
  }

  // Ambient: cobalt dot grid and linking lines on black bands only; paused when the tab is hidden; off on phones.
  function ambient(band) {
    if (rm() || phone() || band.querySelector("canvas.amb")) return;
    const c = document.createElement("canvas"); c.className = "amb"; c.setAttribute("aria-hidden", "true");
    band.prepend(c);
    const x = c.getContext("2d"); let w, h, pts = [], t = 0, run = !document.hidden;
    function size() {
      const r = c.getBoundingClientRect(), d = Math.min(2, devicePixelRatio || 1);
      w = c.width = r.width * d; h = c.height = r.height * d; x.setTransform(d, 0, 0, d, 0, 0); w /= d; h /= d;
      pts = [...Array(18)].map(() => ({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * 0.2, vy: (Math.random() - 0.5) * 0.2 }));
    }
    function draw() {
      if (!run || !c.isConnected) return;
      t += 0.016; x.clearRect(0, 0, w, h);
      for (let gx = 0; gx < w; gx += 34) for (let gy = 0; gy < h; gy += 34) { x.fillStyle = `rgba(122,152,255,${0.08 + 0.06 * Math.sin(t * 1.4 + gx * 0.02 + gy * 0.03)})`; x.fillRect(gx, gy, 2, 2); }
      pts.forEach((p) => { p.x = (p.x + p.vx + w) % w; p.y = (p.y + p.vy + h) % h; });
      for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
        const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
        if (d < 110) { x.strokeStyle = `rgba(0,71,255,${0.28 * (1 - d / 110)})`; x.beginPath(); x.moveTo(pts[i].x, pts[i].y); x.lineTo(pts[j].x, pts[j].y); x.stroke(); }
      }
      requestAnimationFrame(draw);
    }
    document.addEventListener("visibilitychange", () => { const was = run; run = !document.hidden; if (run && !was) draw(); });
    addEventListener("resize", size); size(); draw();
  }

  return { rm, tween, reveal, beams, pulse, snap, hero, ambient };
})();
