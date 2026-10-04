// Spectral chapters: two narrow 3D scenes (fireflies, study 299; mice, study 278) in the visual language of
// Linda's spectral-space work (glowing additive points, dark fog, faint floor, slow camera), rebuilt in plain
// three.js with few labels. Human decisions: AI_LOG Impacts steps 74–78 (F-A + F-C, M-B, after "Light type";
// Linda's look via option A; two chapters, beats loop automatically; perception layer = lamp × sensitivity).
// Point shader adapted from Linda Bohlin's philadelphia-spectral-space (scene/FireflyCommunication.tsx).
//
// Each chapter is one story step; its beats (and their documented numbers) come from the step's
// `spectral` key in app/content/story.js and loop.
//
// Data (dev server, /impacts/ = data/derived/impacts/):
//   spectra_299.json     five LED curves + P. scintillans sensitivity (inferred, Fig. 1 vectors)
//   perception_299.json  each LED × P. scintillans (inferred; null where sensitivity is not plotted)
//   spectra_278.json     two LED curves, mW m⁻² nm⁻¹ (inferred, S. Fig. 1 vectors)
// Single lines at documented peaks: firefly flash 567.47 nm (299, citing Hall et al. 2016); mouse
// melanopsin ≈480 nm (278). Firefly dialogue: replies shown on the documented share of cycles.
// Mouse dials: visual idea after Linda's body-clock scene (Alexander/globe_v2/body.html), with 278's numbers
// (human decision, AI_LOG Push task step 5).
// Lamp colours are the papers' figure colours; flash, eye and melanopsin colours are display choices.
import * as THREE from 'three';

const NM0 = 380, NM1 = 780, WIDTH = 10;
const x = nm => ((nm - NM0) / (NM1 - NM0) - 0.5) * WIDTH;
const ease = t => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
const hash = (i, s) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const pct = c => new THREE.Color(c.replace(/[\d.]+%/g, p => String(Math.round(parseFloat(p) * 2.55))));
const FLASH = new THREE.Color(0.72, 0.92, 0.25), EYE = new THREE.Color(0.85, 0.9, 1), MEL = new THREE.Color(0.45, 0.85, 1);
const H = 2.4;                 // height of 1.0 relative intensity (299)
const H278 = 2.4 / 0.6;        // 278 y axis 0–0.6 mW m⁻² nm⁻¹
const FLASH_NM = 567.47, MEL_NM = 480;
const LAMPS = ['cool_white', 'warm_white', 'blue', 'amber', 'red'];
const LAMP_NAME = { cool_white: 'cool white', warm_white: 'warm white', blue: 'blue', amber: 'amber', red: 'red',
  short: 'blue-rich', long: 'long-wavelength' };
const STROKE_278 = { short: 'rgb(0%, 61.961365%, 89.019775%)', long: 'rgb(89.804077%, 0%, 49.01886%)' };

const vertexShader = `
  attribute vec3 aColor;
  attribute float aSize;
  uniform float uScale;
  uniform float uOpacity;
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vColor = aColor;
    vAlpha = uOpacity;
    gl_PointSize = clamp(aSize * uScale * (15.0 / -mv.z), 1.0, 9.0 * uScale);
    gl_Position = projectionMatrix * mv;
  }`;
const fragmentShader = `
  precision highp float;
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    float r = length(gl_PointCoord - vec2(0.5));
    float core = 1.0 - smoothstep(0.06, 0.23, r);
    float glow = (1.0 - smoothstep(0.13, 0.5, r)) * 0.58;
    float a = max(core, glow) * vAlpha;
    if (a <= 0.003) discard;
    gl_FragColor = vec4(vColor, a);
  }`;

export function createSpectral({ parent }) {
  const canvas = Object.assign(document.createElement('canvas'), { id: 'spectral-canvas', hidden: true });
  const labels = Object.assign(document.createElement('div'), { id: 'spectral-labels', hidden: true });
  const number = Object.assign(document.createElement('div'), { id: 'spectral-number', hidden: true });
  parent.append(canvas, labels, number);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
  const scale = Math.min(window.devicePixelRatio, 1.5);
  renderer.setPixelRatio(scale);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x030508);
  scene.fog = new THREE.Fog(0x030508, 16, 40);
  const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 120);

  const chapters = {};       // name → { group, view, ... }
  const tags = [];           // { el, pos, chapter }
  let data = null, current = null, running = false, t0 = 0, beatIndex = -1, fades = [], cam = null;

  const loaded = Promise.all(['spectra_299', 'perception_299', 'spectra_278'].map(f =>
    fetch(`/impacts/${f}.json`).then(r => r.json()))).then(([f, p, m]) => { data = { f, p, m }; build(); });

  // ── building blocks ──────────────────────────────────────────────────────
  function points(list) {  // list of [x, y, z, colour, size]
    const pos = new Float32Array(list.length * 3), col = new Float32Array(list.length * 3), size = new Float32Array(list.length);
    list.forEach(([px, py, pz, c, s], i) => { pos.set([px, py, pz], i * 3); col.set([c.r, c.g, c.b], i * 3); size[i] = s; });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aColor', new THREE.BufferAttribute(col, 3));
    g.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
    const m = new THREE.ShaderMaterial({ vertexShader, fragmentShader, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, uniforms: { uScale: { value: scale }, uOpacity: { value: 0 } } });
    const p = new THREE.Points(g, m);
    p.frustumCulled = false;
    return p;
  }

  // A curve as a glowing sheet: a bright edge on the curve, a sparse haze of points below it.
  // Null samples (no value in the source) are left out.
  function sheet(samples, height, z, colour, seed, haze = 18) {
    const list = [];
    samples.forEach(([nm, v], i) => {
      if (v == null) return;
      const y = Math.max(0, v) * height;
      list.push([x(nm), y, z, colour, 2.6]);
      const n = Math.round(y * haze);
      for (let j = 0; j < n; j++) list.push([x(nm) + (hash(i, seed + j) - 0.5) * 0.02, hash(i * 7 + j, seed) * y,
        z + (hash(j, i + seed) - 0.5) * 0.25, colour, 1.2]);
    });
    return points(list);
  }

  // Peak marker: a vertical dotted column at one wavelength across the rows' depth.
  function column(nm, height, z0, z1, colour) {
    const list = [];
    for (let z = z0; z >= z1; z -= 0.5) for (let y = 0; y <= height; y += 0.08) list.push([x(nm), y, z, colour, 1.1]);
    return points(list);
  }

  function floor(z0, z1) {
    const g = new THREE.Group(), m = new THREE.LineBasicMaterial({ color: 0x1c2430 });
    const line = (a, b) => g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([a, b]), m));
    for (const nm of [400, 500, 600, 700]) line(new THREE.Vector3(x(nm), 0, z0), new THREE.Vector3(x(nm), 0, z1));
    line(new THREE.Vector3(x(NM0), 0, z0), new THREE.Vector3(x(NM1), 0, z0));
    return g;
  }

  function tag(text, pos, chapter, cls = '') {
    const el = Object.assign(document.createElement('div'), { className: `tag ${cls}`, textContent: text });
    labels.append(el);
    const t = { el, pos, chapter };
    tags.push(t);
    return t;
  }

  // Firefly dialogue: male cluster flashes, a signal crosses, the female cluster answers (or not).
  function dialogue(cx, cy, cz) {
    const cluster = (dx, seed) => points(Array.from({ length: 160 }, (_, i) => [cx + dx + (hash(i, seed) - 0.5) * 0.9,
      cy + (hash(i, seed + 1) - 0.5) * 0.9, cz + (hash(i, seed + 2) - 0.5) * 0.6, FLASH, 1.4 + hash(i, seed + 3) * 1.6]));
    const male = cluster(-1.4, 11), female = cluster(1.4, 23);
    const signal = points(Array.from({ length: 8 }, (_, i) => [cx + i * 0.06 - 0.21, cy, cz, FLASH, 2.2]));
    const g = new THREE.Group();
    g.add(male, female, signal);
    return { group: g, male, female, signal };
  }

  // Mouse 24-hour dial (visual idea after Linda's body-clock scene: activity as moving particles over a
  // day/night cycle). ZT 0 (lights on) at the top, time runs clockwise, 12:12 light:dark (278 Methods).
  // Particles run through the 12 night hours (mice are active at night); their even density is a display
  // choice, not data. Documented values only change them: `supp` = share of activity removed inside the lit
  // window (masking, 1 h at ZT 14), `shift` = minutes the active band starts later (phase delay, CT 16 pulse).
  // The lamp is drawn as a tick just outside the ring, so the band itself shows the gap (human: option 2,
  // AI_LOG Push task step 8). `setDark(true)` = the constant-darkness (CT) dial of the clock test: no day half,
  // a dim tick at the onset before the pulse (CT 12) and a lamp-coloured tick at the onset after it.
  function mouseDial(cx, cy, cz, r, colour, seed) {
    const at = (h, rr = r) => { const a = h / 24 * 2 * Math.PI; return [cx + rr * Math.sin(a), cy + rr * Math.cos(a)]; };
    const DAY = new THREE.Color(0.8, 0.68, 0.45), NIGHT = new THREE.Color(0.3, 0.36, 0.46);
    const base = points(Array.from({ length: 144 }, (_, i) => [...at(i / 6), cz, i < 72 ? DAY : NIGHT, 1.9]));
    const radial = (h, c) => points(Array.from({ length: 9 }, (_, i) => [...at(h, r - 0.16 + i * 0.04), cz, c, 2.4]));
    const before = radial(12, new THREE.Color(0.75, 0.78, 0.82)), after = radial(12, colour);
    const N = 900, u = Array.from({ length: N }, (_, i) => hash(i, seed));
    const dr = u.map((_, i) => (hash(i, seed + 1) - 0.5) * 0.16);
    const tint = colour.clone().lerp(new THREE.Color(1, 1, 1), 0.35);
    const act = points(u.map((_, i) => [cx, cy, cz, tint, 1.3 + hash(i, seed + 2) * 1.3]));
    const lit = points(Array.from({ length: 90 }, (_, i) => [cx, cy, cz + (i % 3 - 1) * 0.04, colour, 3.0]));
    const g = new THREE.Group();
    g.add(base, act, lit, before, after);
    const st = { supp: 0, window: null, shift: 0 };
    return { group: g, base, act, lit, before, after, st,
      setWindow(h0, h1) {  // the lamp's window, as a tick outside the ring, in hours (null = none)
        st.window = h0 == null ? null : [h0, h1];
        if (h0 == null) return;
        const a = lit.geometry.attributes.position;
        for (let i = 0; i < a.count; i++) {
          const [px, py] = at(h0 + (h1 - h0) * Math.floor(i / 3) / (a.count / 3 - 1), r + 0.2 + (i % 3 - 1) * 0.035);
          a.setX(i, px); a.setY(i, py);
        }
        a.needsUpdate = true;
      },
      setDark(on) {  // constant darkness: the day half takes the night colour
        const c = base.geometry.attributes.aColor;
        for (let i = 0; i < 72; i++) c.setXYZ(i, ...(on ? NIGHT : DAY).toArray());
        c.needsUpdate = true;
      },
      tick(now) {  // particles move through the night band; inside the lit window, a `supp` share is removed
        const a = act.geometry.attributes.position, start = 12 + st.shift / 60;
        const t = after.geometry.attributes.position;
        for (let i = 0; i < t.count; i++) { const [px, py] = at(start, r - 0.16 + i * 0.04); t.setX(i, px); t.setY(i, py); }
        t.needsUpdate = true;
        for (let i = 0; i < N; i++) {
          const h = start + ((u[i] + now / 14000) % 1) * 12, hh = h % 24;
          const off = st.window && hh >= st.window[0] && hh < st.window[1] && hash(i, seed + 3) < st.supp;
          const [px, py] = off ? [cx, cy - 1e4] : at(h, r + dr[i]);
          a.setXYZ(i, px, py, cz + dr[i]);
        }
        a.needsUpdate = true;
      } };
  }

  function build() {
    // Fireflies (299): five rows; the eye (P. scintillans) as a canopy over all rows; flash column; dialogue.
    const F = { group: new THREE.Group(), lamps: {}, seen: {}, tags: {} };
    const zRow = i => -i * 0.9, zBack = zRow(LAMPS.length - 1) - 0.5;
    LAMPS.forEach((n, i) => {
      const c = data.f.curves[n];
      F.lamps[n] = sheet(c.samples, H, zRow(i), pct(c.line_colour), 100 + i);
      F.seen[n] = sheet(data.p.curves[n].samples, H, zRow(i) + 0.2, FLASH, 200 + i, 34);
      F.group.add(F.lamps[n], F.seen[n]);
      F.tags[n] = tag(LAMP_NAME[n], new THREE.Vector3(x(NM1) + 0.15, 0.1, zRow(i)), 'fireflies', 'row');
    });
    const eye = [];
    data.f.curves.p_scintillans.samples.forEach(([nm, v], i) => {
      if (i % 2 === 0) for (let z = 0.5; z >= zBack; z -= 0.45) eye.push([x(nm), Math.max(0, v) * H, z, EYE, i % 2 ? 0.9 : 1.3]);
    });
    F.eye = points(eye);
    F.flash = column(FLASH_NM, H * 1.05, 0.5, zBack, FLASH);
    F.talk = dialogue(0, H + 2.2, -1.8);
    F.group.add(F.eye, F.flash, F.talk.group, floor(0.5, zBack));
    tag('♂', new THREE.Vector3(-1.4, H + 2.95, -1.8), 'fireflies', 'sym');
    tag('♀', new THREE.Vector3(1.4, H + 2.95, -1.8), 'fireflies', 'sym');
    F.view = { pos: new THREE.Vector3(-1, 5.6, 19), target: new THREE.Vector3(0.9, 2.1, -1.8) };
    chapters.fireflies = F;

    // Mice (278): two rows; melanopsin column; one 24-hour dial per lamp (outer blue-rich, inner long-wavelength).
    const M = { group: new THREE.Group(), lamps: {}, tags: {}, dials: {} };
    ['short', 'long'].forEach((n, i) => {
      M.lamps[n] = sheet(data.m.curves[n].samples, H278, -i * 1.3, pct(STROKE_278[n]), 300 + i, 14);
      M.dials[n] = mouseDial(x(660), 4.7, 0, i ? 0.95 : 1.35, pct(STROKE_278[n]), 400 + i * 50);
      M.group.add(M.lamps[n], M.dials[n].group);
      M.tags[n] = tag(LAMP_NAME[n], new THREE.Vector3(x(NM1) + 0.15, 0.1, -i * 1.3), 'mice', 'row');
    });
    M.mel = column(MEL_NM, H278 * 0.6, 0.5, -1.8, MEL);
    M.group.add(M.mel, floor(0.5, -1.8));
    M.ld = [tag('day', new THREE.Vector3(x(660) + 1.75, 4.7, 0), 'mice', 'sym'),
      tag('night', new THREE.Vector3(x(660) - 2.05, 4.7, 0), 'mice', 'sym')];
    M.dd = [tag('constant darkness', new THREE.Vector3(x(660), 4.7 + 1.75, 0), 'mice', 'sym')];
    M.view = { pos: new THREE.Vector3(-1, 4.6, 17), target: new THREE.Vector3(0.9, 2.6, -0.6) };
    // Beat views (agent choices): `night` = the first night quarter (ZT 12–18) of both dials, close up;
    // `dial` = the whole dial, closer than the chapter view.
    M.views = { night: { pos: new THREE.Vector3(1.3, 3.85, 4.6), target: new THREE.Vector3(1.3, 3.85, 0), sway: 0.1 },
      dial: { pos: new THREE.Vector3(1.8, 4.6, 9.5), target: new THREE.Vector3(x(660), 4.7, 0), sway: 0.3 } };
    chapters.mice = M;

    Object.values(chapters).forEach(c => { c.group.visible = false; scene.add(c.group); });
    for (const ch of ['fireflies', 'mice']) {
      [400, 500, 600, 700].forEach(nm => tag(String(nm), new THREE.Vector3(x(nm), -0.2, 0.5), ch, 'tick'));
    }
  }

  // ── beats ────────────────────────────────────────────────────────────────
  const op = p => p.material.uniforms.uOpacity;
  function fadeTo(p, to, ms = 700) {
    fades = fades.filter(f => f.p !== p);
    fades.push({ p, from: op(p).value, to, t: performance.now(), ms });
  }
  function showNumber(b) {
    if (!b?.value) { number.hidden = true; return; }
    // `colours` (lamp keys) colour the parts of a "a vs b" value, or the whole value if there is one key.
    const parts = b.colours ? b.value.split(' vs ') : [b.value];
    const value = parts.map((p, i) => b.colours?.[i] ? `<span style="color:${STROKE_278[b.colours[i]]}">${p}</span>` : p)
      .join(' vs ');
    number.innerHTML = `<span class="value">${value}</span>${b.label ? `<span class="label">${b.label}</span>` : ''}`;
    number.hidden = false;
  }

  function enterBeat(b) {
    showNumber(b);
    if (current.chapter === 'fireflies') {
      const F = chapters.fireflies;
      fadeTo(F.eye, 0.45);
      fadeTo(F.flash, 0.5);
      fadeTo(F.talk.male, 0.06); fadeTo(F.talk.female, 0.05);
      LAMPS.forEach(n => {
        const on = b.lamp === n;
        fadeTo(F.lamps[n], on ? 0.9 : b.lamp ? 0.07 : 0);
        fadeTo(F.seen[n], on ? 1 : 0);
        F.tags[n].el.classList.toggle('on', on);
        F.lamps[n].scale.y = F.seen[n].scale.y = 1;
      });
      if (b.brighter) {  // F-C: the lamp grows to ten times the photons (documented: dim × 10 = bright)
        const grow = [F.lamps[b.lamp], F.seen[b.lamp]];
        fades.push({ t: performance.now() + 600, ms: 2200, tick: k => grow.forEach(o => { o.scale.y = 1 + 9 * k; }) });
      }
    } else {
      // Beats: 'lux' (both lamps, no light on the dials) → one lamp at a time: its dial's 1 h window at
      // ZT 14 lights and loses `supp` of its activity → 'clock': a 15 min pulse at CT 16 on both dials, then
      // each night band starts later by its documented delay (minutes).
      // 'dark' / 'clock' run on the constant-darkness dial (the clock test ran in DD, CT 12 = activity onset):
      // 'dark' shows the pulse and the onset before it; 'clock' then moves each onset later.
      const M = chapters.mice, clock = b.show === 'clock', dark = clock || b.show === 'dark';
      ['short', 'long'].forEach((n, i) => {
        const on = b.lamp === n || !b.lamp, d = M.dials[n];
        fadeTo(M.lamps[n], on ? 0.85 : 0.07);
        M.tags[n].el.classList.toggle('on', on);
        fadeTo(d.base, on ? 0.7 : 0.25); fadeTo(d.act, on ? 0.95 : 0.2);
        d.st.supp = 0; d.st.shift = 0;
        d.setDark(dark);
        d.setWindow(...(dark ? [16, 16.25] : b.lamp === n ? [14, 15] : [null]));
        fadeTo(d.lit, d.st.window ? 1 : 0, 400);
        fadeTo(d.before, dark ? 0.8 : 0, 400);
        fadeTo(d.after, clock ? 1 : 0, 400);
        if (b.lamp === n) fades.push({ t: performance.now() + 500, ms: 1500, tick: k => { d.st.supp = b.supp * k; } });
        if (clock) fades.push({ t: performance.now() + 900, ms: 2400, tick: k => { d.st.shift = b.minutes[i] * k; } });
      });
      M.ld.forEach(t => t.el.classList.toggle('off', dark));
      M.dd.forEach(t => t.el.classList.toggle('off', !dark));
      fadeTo(M.mel, b.show === 'lux' ? 0.12 : 0.75);
    }
  }

  // Firefly dialogue: 1.2 s cycles; male flash at 0.1, signal 0.2–0.5, female reply at 0.6 on the
  // documented share of cycles (cycle c replies if frac(c × 0.618…) < rate; rate from the beat).
  function animateDialogue(now) {
    const F = chapters.fireflies, b = current.beats[beatIndex] || {};
    const s = (now - t0) / 1200, c = Math.floor(s), ph = s - c;
    const pulse = at => Math.exp(-(((ph - at) / 0.07) ** 2));
    const replies = ((c * 0.6180339887) % 1) < (b.reply ?? 1);
    op(F.talk.male).value = 0.14 + 0.85 * pulse(0.1);
    op(F.talk.female).value = 0.12 + (replies ? 0.85 * pulse(0.6) : 0);
    op(F.talk.signal).value = ph > 0.18 && ph < 0.52 ? 0.6 : 0;
    F.talk.signal.position.x = Math.min(1, Math.max(0, (ph - 0.2) / 0.3)) * 1.8 - 0.9;
  }

  // ── loop ─────────────────────────────────────────────────────────────────
  const v = new THREE.Vector3();
  function frame(now) {
    if (!running) return;
    const ms = current.every ?? 4200, i = Math.floor((now - t0) / ms) % current.beats.length;
    if (i !== beatIndex) { beatIndex = i; enterBeat(current.beats[i]); }
    fades = fades.filter(f => {
      const k = Math.min(1, Math.max(0, (now - f.t) / f.ms));
      if (f.tick) f.tick(ease(k)); else op(f.p).value = f.from + (f.to - f.from) * ease(k);
      return k < 1;
    });
    if (current.chapter === 'fireflies') animateDialogue(now);
    else Object.values(chapters.mice.dials).forEach(d => d.tick(now));
    // A beat may name a closer view (`view` key → chapter.views); the camera eases towards it.
    const ch = chapters[current.chapter], vw = ch.views?.[current.beats[beatIndex]?.view] || ch.view;
    if (!cam) cam = { pos: vw.pos.clone(), target: vw.target.clone(), t: now };
    const k = 1 - Math.exp(-(now - cam.t) / 450);  // time-based, so throttled frames still arrive
    cam.t = now; cam.pos.lerp(vw.pos, k); cam.target.lerp(vw.target, k);
    camera.position.set(cam.pos.x + Math.sin(now / 9000) * (vw.sway ?? 1.2), cam.pos.y, cam.pos.z);
    camera.lookAt(cam.target);
    renderer.render(scene, camera);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    tags.forEach(t => {
      t.el.hidden = t.chapter !== current.chapter || t.el.classList.contains('off') ||
        (t.el.classList.contains('row') && !t.el.classList.contains('on'));
      if (t.el.hidden) return;
      v.copy(t.pos).project(camera);
      t.el.style.transform = `translate(${(v.x + 1) / 2 * w}px, ${(1 - v.y) / 2 * h}px)`;
    });
    requestAnimationFrame(frame);
  }

  function resize() {
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  return {
    // st = a story step's `spectral` key ({ chapter, beats, every }), or null to hide the view.
    async set(st) {
      current = st;
      if (!st) { canvas.hidden = labels.hidden = number.hidden = true; running = false; return; }
      await loaded;
      if (current !== st) return;  // the step changed while the data was loading
      Object.entries(chapters).forEach(([k, c]) => { c.group.visible = k === st.chapter; });
      Object.values(chapters).forEach(c => c.group.traverse(o => { if (o.isPoints) op(o).value = 0; }));
      tags.forEach(t => t.el.classList.remove('on'));
      fades = [];
      beatIndex = -1;
      cam = null;  // snap to the first view on entering a step
      t0 = performance.now();
      canvas.hidden = labels.hidden = false;
      if (!running) { running = true; requestAnimationFrame(frame); }
    },
  };
}
