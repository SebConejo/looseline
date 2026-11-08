(() => {
  const NS = "http://www.w3.org/2000/svg";
  const EASE = {
    linear: (x) => x,
    in: (x) => x * x * x,
    out: (x) => 1 - Math.pow(1 - x, 3),
    inOut: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    back: (x) => (x <= 0 ? 0 : 1 + 2.9 * Math.pow(x - 1, 3) + 1.9 * Math.pow(x - 1, 2)),
  };

  function track(keys, t, fallback) {
    if (!keys || !keys.length) return fallback;
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [t1, v1, ease] = keys[i];
      if (t <= t1) {
        const [t0, v0] = keys[i - 1];
        if (ease === "step") return v0;
        const x = (t - t0) / (t1 - t0 || 1);
        return v0 + (v1 - v0) * (EASE[ease] || EASE.inOut)(x);
      }
    }
    return keys[keys.length - 1][1];
  }

  function stepTrack(keys, t, fallback) {
    if (!keys || !keys.length) return fallback;
    let value = keys[0][1];
    for (const [at, v] of keys) if (t >= at) value = v;
    return value;
  }

  function stateOf(layer, t) {
    const tr = layer.track || {};
    const s = track(tr.scale, t, 1);
    let y = track(tr.y, t, 0);
    if (layer.float) {
      const f = layer.float;
      y += (f.amp || 6) * Math.sin(((t - (f.phase || 0)) / (f.period || 1200)) * Math.PI * 2) * track(f.weight, t, 1);
    }
    return {
      x: track(tr.x, t, 0),
      y,
      sx: s * track(tr.sx, t, 1),
      sy: s * track(tr.sy, t, 1),
      rotate: track(tr.rotate, t, 0),
      opacity: track(tr.opacity, t, 1),
      pose: stepTrack(layer.pose, t, 1),
      reveal: layer.reveal ? track(layer.reveal.track, t, 1) : 1,
    };
  }

  function transformOf(layer, st) {
    const [ox, oy] = layer.origin || [0, 0];
    return `translate(${(st.x + ox).toFixed(2)} ${(st.y + oy).toFixed(2)}) rotate(${st.rotate.toFixed(2)}) scale(${st.sx.toFixed(4)} ${st.sy.toFixed(4)}) translate(${-ox} ${-oy})`;
  }

  function el(name, attrs = {}, parent) {
    const node = document.createElementNS(NS, name);
    for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
    if (parent) parent.appendChild(node);
    return node;
  }

  let uid = 0;
  function mount(host, scene) {
    const id = `ink${uid++}`;
    const [W, H] = scene.size;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": scene.title || "" });
    const defs = el("defs", {}, svg);
    const boil = scene.boil || {};
    const seeds = [1, 7, 13];
    seeds.forEach((seed, i) => {
      const f = el("filter", { id: `${id}-b${i}`, x: "-5%", y: "-5%", width: "110%", height: "110%" }, defs);
      el("feTurbulence", { type: "fractalNoise", baseFrequency: boil.freq ?? 0.02, numOctaves: 2, seed }, f);
      el("feDisplacementMap", { in: "SourceGraphic", scale: boil.scale ?? 4, xChannelSelector: "R", yChannelSelector: "G" }, f);
    });
    const parts = scene.layers.map((layer, li) => {
      const outer = el("g", {}, svg);
      let holder = outer;
      let reveal = null;
      if (layer.reveal) {
        const r = layer.reveal;
        const mask = el("mask", { id: `${id}-m${li}`, maskUnits: "userSpaceOnUse", x: 0, y: 0, width: W, height: H }, defs);
        let grad;
        if (r.type === "bloom") {
          grad = el("radialGradient", { id: `${id}-g${li}`, gradientUnits: "userSpaceOnUse", cx: r.cx, cy: r.cy, r: 1 }, defs);
          el("stop", { offset: 0.75, "stop-color": "#fff" }, grad);
          el("stop", { offset: 1, "stop-color": "#000" }, grad);
        } else {
          grad = el("linearGradient", { id: `${id}-g${li}`, gradientUnits: "userSpaceOnUse" }, defs);
          el("stop", { offset: 0.85, "stop-color": "#fff" }, grad);
          el("stop", { offset: 1, "stop-color": "#000" }, grad);
        }
        el("rect", { width: W, height: H, fill: `url(#${id}-g${li})` }, mask);
        holder = el("g", { mask: `url(#${id}-m${li})` }, outer);
        reveal = { r, grad };
      }
      const srcs = layer.poses || [layer.src];
      const images = srcs.map((src) =>
        el("image", { href: src, x: layer.x ?? 0, y: layer.y ?? 0, width: layer.w ?? W, height: layer.h ?? H, preserveAspectRatio: "none" }, holder),
      );
      return { layer, outer, images, reveal };
    });
    host.appendChild(svg);

    function render(t, frame) {
      for (const p of parts) {
        const st = stateOf(p.layer, t);
        p.outer.setAttribute("transform", transformOf(p.layer, st));
        p.outer.setAttribute("opacity", st.opacity < 0.01 ? "0" : st.opacity.toFixed(3));
        p.images.forEach((img, k) => {
          img.setAttribute("opacity", k + 1 === st.pose ? "1" : "0");
          if (p.layer.boil && frame >= 0) img.setAttribute("filter", `url(#${id}-b${frame % 3})`);
          else img.removeAttribute("filter");
        });
        if (p.reveal) {
          const { r, grad } = p.reveal;
          const v = Math.max(0.0005, st.reveal);
          if (r.type === "bloom") grad.setAttribute("r", (1 + v * r.radius).toFixed(1));
          else {
            const dir = r.dir || "down";
            const len = dir === "down" || dir === "up" ? H : W;
            const reach = (1 + v * len * 1.18).toFixed(1);
            const flip = dir === "up" || dir === "left";
            const a = flip ? len : 0;
            const b = flip ? len - reach : reach;
            const vertical = dir === "down" || dir === "up";
            grad.setAttribute("x1", vertical ? 0 : a);
            grad.setAttribute("x2", vertical ? 0 : b);
            grad.setAttribute("y1", vertical ? a : 0);
            grad.setAttribute("y2", vertical ? b : 0);
          }
        }
      }
    }
    return { svg, render };
  }

  function corners(layer, st) {
    const b = layer.bbox;
    if (!b) return null;
    const [ox, oy] = layer.origin || [0, 0];
    const rad = (st.rotate * Math.PI) / 180, c = Math.cos(rad), s = Math.sin(rad);
    return [[b[0], b[1]], [b[2], b[1]], [b[0], b[3]], [b[2], b[3]]].map(([px, py]) => {
      const ux = (px - ox) * st.sx, uy = (py - oy) * st.sy;
      return [ox + st.x + ux * c - uy * s, oy + st.y + ux * s + uy * c];
    });
  }

  function check(scene) {
    const problems = [];
    const [W, H] = scene.size;
    const fps = scene.fps || 10;
    const step = 1000 / fps;
    if (fps !== 10 && fps !== 12) problems.push(`frame rate is ${fps}, the style asks for 10, or 12 for a flipbook`);
    const seen = new Set();
    for (const layer of scene.layers) {
      if (!layer.bbox) problems.push(`${layer.id}: no bbox, the frame check cannot run`);
      for (let t = 0; t <= scene.loop; t += step) {
        const st = stateOf(layer, t);
        if (st.opacity < 0.05 || Math.abs(st.sx * st.sy) < 0.01) continue;
        const pts = corners(layer, st);
        if (!pts) break;
        const out = pts.some(([x, y]) => x < -1 || y < -1 || x > W + 1 || y > H + 1);
        const key = `${layer.id}-out`;
        if (out && !seen.has(key) && !layer.offstage) {
          seen.add(key);
          problems.push(`${layer.id}: leaves the canvas at ${Math.round(t)} ms`);
        }
      }
      const a = stateOf(layer, 0), b = stateOf(layer, scene.loop);
      const visible = (s) => s.opacity >= 0.05 && Math.abs(s.sx * s.sy) >= 0.01;
      const differs =
        visible(a) !== visible(b) ||
        (visible(a) && (Math.abs(a.x - b.x) > 1 || Math.abs(a.y - b.y) > 1 || Math.abs(a.sx - b.sx) > 0.01 || Math.abs(a.sy - b.sy) > 0.01 || a.pose !== b.pose || Math.abs(a.opacity - b.opacity) > 0.05));
      if (differs) problems.push(`${layer.id}: the loop jumps (state at ${scene.loop} ms differs from 0 ms)`);
      if (layer.poses && layer.pose) {
        for (const [, p] of layer.pose) if (p < 1 || p > layer.poses.length) problems.push(`${layer.id}: pose ${p} does not exist`);
      }
    }
    const washes = scene.layers.filter((l) => l.kind === "wash").length;
    if (washes > 2) problems.push(`${washes} watercolor layers, the style allows at most 2 per drawing`);
    const moving = scene.layers.some((l) => (l.poses && l.poses.length > 1) || Object.keys(l.track || {}).some((k) => k !== "opacity"));
    if (!moving) problems.push("nothing moves: the animation only fades or reveals, the style asks for real motion");
    return problems;
  }

  function play(host, scene) {
    const params = new URLSearchParams(location.search);
    const fps = scene.fps || 10;
    const step = 1000 / fps;
    if (params.has("check")) {
      const problems = check(scene);
      const pre = document.createElement("pre");
      pre.id = "ink-report";
      pre.textContent = JSON.stringify({ title: scene.title, problems });
      document.body.appendChild(pre);
      return;
    }
    if (params.has("sheet")) {
      const times = params.get("sheet").split(",").map(Number);
      host.classList.add("sheet");
      times.forEach((t, i) => {
        const cell = document.createElement("div");
        cell.className = "cell";
        host.appendChild(cell);
        const m = mount(cell, scene);
        m.render(t, Math.round(t / step));
        const label = document.createElement("span");
        label.textContent = `${t} ms`;
        cell.appendChild(label);
      });
      return;
    }
    const m = mount(host, scene);
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (params.has("t")) {
      const t = Number(params.get("t"));
      m.render(t, Math.round(t / step));
      return;
    }
    if (reduced) {
      m.render(scene.still ?? scene.loop / 2, -1);
      return;
    }
    const begin = performance.now();
    let last = -1;
    const tick = (now) => {
      const frame = Math.floor((now - begin) / step);
      if (frame !== last) {
        last = frame;
        m.render((frame * step) % scene.loop, frame);
      }
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  window.INK = { play, check, track, stateOf };
})();
