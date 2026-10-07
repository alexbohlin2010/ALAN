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
//
// Signal production (Owens, Meyer-Rochow & Yang 2018, A. ficta; human decisions AI_LOG Firefly narrative rounds
// 4b, 4f: scene "A + B", generic nm → RGB colours). Data: owens2018_results.json (documented, Table 1 p. 6).
// 3D: the eight LED peak wavelengths as dotted columns (the paper gives peak wavelengths only, no spectra); two
// males drawn as glowing clusters: left = dark base values, right = the beat's exposure. Each flashes at its
// Table 1 mean rate (peaks/min) with peak brightness ∝ its intensity ratio to dark. Display choices: flashes are
// evenly spaced (real flashes are irregular), ~0.2 s long (Methods: alarm flashes approx. 200 ms), colour =
// nm → RGB at the documented 565 nm bioluminescence peak; bright (10×) is shown by a denser column, not to scale.
// 2D strip (bottom left): Table 1 means ± SD per wavelength, dim (filled) and bright (ring), dashed line = dark
// base value; the current beat is highlighted. Displayed numbers are Table 1's printed text.
// Human changes, AI_LOG Firefly tabs review round 6j: bright (10×) beats only, no dark beat, no big number; strip at
// the top right above the card, as wide as the card; flashes shown 2.5× faster than Table 1 (SIGNAL_SPEED, both males,
// so their ratio is kept; display only, the strip and labels keep the printed values).
//
// Mate-finding (Kivelä et al. 2023, Lampyris noctiluca; human decisions AI_LOG Firefly tabs rounds 5a-5b, review
// round 6o: "dark vs lit pair", laid out like Signal production). Data: kivela2023.json. Left = control (no light),
// right = the beat's treatment (blue, white, yellow, red). Each side: that treatment's traps as green points (the
// dummy females, LED 562 nm, documented) scattered in a ball (trap j has the same place on both sides; positions are
// display only), and each trap's trapped males (measured count) flying in to a small swarm above it (motion and swarm
// shape: display only). The lit treatment's column stands at its Table 1 peak (white drawn white: display choice).
// Under each side and in the strip: Table 3 share of dummy females with ≥ 1 male (printed text).
//
// One continuous scene (human, round 5b): signal (Owens 2018), fireflies (Owens & Lewis 2021) and glow (Kivelä) sit
// in depth bands along the shared nm axis (BANDS, z offsets); moving between these steps keeps the camera (it
// glides) and leaves the other bands faint.
// Signal production ↔ Female response (human: "the flash travels", AI_LOG Firefly tabs review round 6g): one
// yellow-green flash leaves the right-hand Signal male, travels back through depth to the Female response female and
// she answers; the camera rides with it. Back plays it in reverse. The travelling flash is a display device, not data
// (the two studies use different species).
// Female response ↔ Mate-finding (human: "the answer becomes the lure", round 6o): the female's reply glow travels
// back to the Mate-finding band, splits into the dummy females of both sides, then the males fly in. Display device,
// not data (Kivelä's females are glow-worms, which glow rather than answer, and the dummies are LEDs).
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
// Generic wavelength → RGB (display choice, human 4f): D. Bruton (1996), "Approximate RGB values for visible
// wavelengths" — piecewise linear hue, intensity fall-off below 420 and above 700 nm, gamma 0.8.
function nmRGB(w) {
  const [r, g, b] = w < 440 ? [(440 - w) / 60, 0, 1] : w < 490 ? [0, (w - 440) / 50, 1] : w < 510 ? [0, 1, (510 - w) / 20]
    : w < 580 ? [(w - 510) / 70, 1, 0] : w < 645 ? [1, (645 - w) / 65, 0] : [1, 0, 0];
  const f = w < 420 ? 0.3 + 0.7 * (w - 380) / 40 : w > 700 ? 0.3 + 0.7 * (780 - w) / 80 : 1;
  return new THREE.Color(...[r, g, b].map(c => (c * f) ** 0.8));
}
const css = c => `rgb(${[c.r, c.g, c.b].map(v => Math.round(v * 255)).join(',')})`;
export const nmCss = nm => css(nmRGB(nm));   // same colours for 2D overlays (impacts.js site glow)
const BANDS = { signal: 0, fireflies: -7, glow: -14 };   // depth offsets of the continuous firefly scene
const FAINT = 0.05;                                       // opacity of the other bands' points
const BIO_NM = 565;   // A. ficta bioluminescence peak (Owens 2018 p. 3, documented)
const SIGNAL_SPEED = 2.5;   // display speed-up of the Signal flashes (human, round 6j); not data
const SVG = 'http://www.w3.org/2000/svg';

const vertexShader = `
  attribute vec3 aColor;
  attribute float aSize;
  uniform float uScale;
  uniform float uSize;
  uniform float uOpacity;
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vColor = aColor;
    vAlpha = uOpacity;
    gl_PointSize = clamp(aSize * uSize * uScale * (15.0 / -mv.z), 1.0, 9.0 * uSize * uScale);
    gl_Position = projectionMatrix * mv;
  }`;
// uGain / uSize: shared brightness and point-size gains (1 = as before); raised on the three firefly tabs (human,
// AI_LOG Firefly tabs review round 6q: "too dark"). uGain scales alpha (capped at 1) and colour (rescaled so the
// largest channel is at most 1, so hues, e.g. wavelength colours, do not shift), so dim and halo points brighten most. The other bands' FAINT level is divided by the gain, so they stay as faint as before.
const fragmentShader = `
  precision highp float;
  uniform float uGain;
  varying vec3 vColor;
  varying float vAlpha;
  void main() {
    float r = length(gl_PointCoord - vec2(0.5));
    float core = 1.0 - smoothstep(0.06, 0.23, r);
    float glow = (1.0 - smoothstep(0.13, 0.5, r)) * 0.58;
    float a = max(core, glow) * vAlpha;
    if (a <= 0.003) discard;
    vec3 c = vColor * uGain;
    c /= max(1.0, max(c.r, max(c.g, c.b)));   // brighter but the same hue (no channel clipped)
    gl_FragColor = vec4(c, min(1.0, a * uGain));
  }`;
const GAIN = { value: 1 }, SIZE = { value: 1 }, BAND_GAIN = 2.2, BAND_SIZE = 1.3;   // agent choices, tuned by eye

// onLine(k): a beat's `line` (index into the step's big-text lines) is shown in place of the others (main.js;
// AI_LOG Firefly flow step 14).
export function createSpectral({ parent, onLine = null }) {
  const canvas = Object.assign(document.createElement('canvas'), { id: 'spectral-canvas', hidden: true });
  const labels = Object.assign(document.createElement('div'), { id: 'spectral-labels', hidden: true });
  const number = Object.assign(document.createElement('div'), { id: 'spectral-number', hidden: true });
  // Beat toggle (top right) for chapters with `manual: true`: one button per beat, no auto-advance (human request,
  // Firefly transition task step 3). Button names = the lamp names used in the scene; no lamp = 'dark'.
  const toggle = Object.assign(document.createElement('nav'), { id: 'spectral-toggle', hidden: true });
  toggle.setAttribute('aria-label', 'Light states');
  // Signal production: Table 1 strip (SVG), shown only in that chapter.
  const strip = Object.assign(document.createElement('div'), { id: 'spectral-strip', hidden: true });
  // Beat `caption`: large text bottom centre, fades in on that beat, out on any other (human, AI_LOG Fireflies step 6).
  const caption = Object.assign(document.createElement('p'), { id: 'spectral-caption' });
  parent.append(canvas, labels, number, toggle, strip, caption);
  toggle.addEventListener('click', e => { const b = e.target.closest('button'); if (b) goBeat(Number(b.dataset.beat)); });
  strip.addEventListener('click', e => { const m = e.target.closest('[data-beat]'); if (m) goBeat(Number(m.dataset.beat)); });

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
  // Door transition (human: option B + click, Firefly transition task step 2): the view grows out of a chart dot
  // (dir 1) or shrinks back into it (dir −1): a circle clip around the dot widens while the canvas scales up
  // about it. { dir, x, y, t, ms, done } or null. Labels and the number wait until it is open.
  let trans = null;
  let manualBeat = 0;   // the shown beat when the chapter is manual
  const OPEN_MS = 1300, CLOSE_MS = 900, DOOR_R = 6;
  // Glow transition (human: "point becomes the scene", AI_LOG Firefly tabs review round 6b): from a site's glow on the
  // globe (impacts.js) the scene opens through a soft circle around it, and the two Signal males start gathered,
  // bright, under the glow, then move apart to their places; the reverse on the way back. { style: 'glow', dir, at
  // (→ {x, y} or null), t, ms, done, m }. Delay and durations: agent choices, timed to the globe zoom (story.js fly 2200).
  const GLOW_DELAY = 1100, GLOW_OPEN_MS = 2000, GLOW_CLOSE_MS = 1500;
  // Flash travel between the Signal and Female response bands: { dir (1 = signal → fireflies), t, ms } or null.
  // flashes = the head + fading trail (built in build()). Duration, arc, trail and camera path: agent choices.
  let travel = null, flashes = [];
  const TRAVEL_MS = 2600, TRAIL = 6;

  const loaded = Promise.all(['spectra_299', 'perception_299', 'spectra_278', 'owens2018_results', 'kivela2023'].map(f =>
    fetch(`/impacts/${f}.json`).then(r => r.json()))).then(([f, p, m, o, k]) => { data = { f, p, m, o, k }; build(); });

  // ── building blocks ──────────────────────────────────────────────────────
  function points(list) {  // list of [x, y, z, colour, size]
    const pos = new Float32Array(list.length * 3), col = new Float32Array(list.length * 3), size = new Float32Array(list.length);
    list.forEach(([px, py, pz, c, s], i) => { pos.set([px, py, pz], i * 3); col.set([c.r, c.g, c.b], i * 3); size[i] = s; });
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aColor', new THREE.BufferAttribute(col, 3));
    g.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
    const m = new THREE.ShaderMaterial({ vertexShader, fragmentShader, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, uniforms: { uScale: { value: scale }, uOpacity: { value: 0 }, uGain: GAIN, uSize: SIZE } });
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
  function column(nm, height, z0, z1, colour, dz = 0.5, size = 1.1) {
    const list = [];
    for (let z = z0; z >= z1; z -= dz) for (let y = 0; y <= height; y += 0.08) list.push([x(nm), y, z, colour, size]);
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

  // One side of the Mate-finding pair (round 6o). Capacities: 60 dummy females, 260 males (data maxima per treatment:
  // 60 traps, 209 males). fill(traps): females at fixed places in a ball (r 0.95) around c, trap j always at the same
  // place; each trap's males start far out in random directions and fly in (staggered) to a swarm above it.
  // wait = true: the females sit gathered at the travel's landing point, hidden, until land(origin) splits them out.
  function glowSide(c, FEMALE, MALE) {
    const fem = points(Array.from({ length: 60 }, () => [0, 0, 0, FEMALE, 3.8]));
    const mal = points(Array.from({ length: 260 }, () => [0, 0, 0, MALE, 1.4]));
    const sd = { c, fem, mal, nF: 0, nM: 0, fEnd: new Float32Array(180), mEnd: new Float32Array(780),
      mFrom: new Float32Array(780), mDelay: new Float32Array(260), t: 0, split: null, splitT: 0, done: true };
    const ball = (i, seed, r0) => {
      const r = r0 * Math.cbrt(hash(i, seed)), u = 2 * hash(i, seed + 1) - 1, a = 2 * Math.PI * hash(i, seed + 2), q = Math.sqrt(1 - u * u);
      return [r * q * Math.cos(a), r * u, r * q * Math.sin(a)];
    };
    sd.fill = (traps, now, wait = false) => {
      sd.nF = traps.length; sd.nM = 0;
      traps.forEach((tr, j) => {
        const [fx, fy, fz] = ball(j, 61, 0.95);
        sd.fEnd.set([c.x + fx, c.y + fy, c.z + fz], j * 3);
        for (let i = 0; i < tr.males && sd.nM < 260; i++, sd.nM++) {
          const m = sd.nM, [ox, oy, oz] = ball(j * 31 + i, 71, 0.14), [dx, dy, dz] = ball(m, 81, 1), d = Math.hypot(dx, dy, dz) || 1;
          const far = 2.2 + 1.8 * hash(m, 84);
          sd.mEnd.set([c.x + fx + ox, c.y + fy + 0.1 + Math.abs(oy), c.z + fz + oz], m * 3);
          sd.mFrom.set([sd.mEnd[m * 3] + dx / d * far, sd.mEnd[m * 3 + 1] + Math.abs(dy / d) * far, sd.mEnd[m * 3 + 2] + dz / d * far], m * 3);
          sd.mDelay[m] = hash(m, 85) * 1300;
        }
      });
      fem.geometry.setDrawRange(0, sd.nF); mal.geometry.setDrawRange(0, sd.nM);
      sd.split = wait ? 'pending' : null; sd.t = wait ? Infinity : now; sd.done = false;
      const fp = fem.geometry.attributes.position;
      for (let j = 0; j < sd.nF; j++) fp.setXYZ(j, ...(wait ? [0, -1e4, 0] : sd.fEnd.subarray(j * 3, j * 3 + 3)));
      fp.needsUpdate = true;
      sd.tick(now);
    };
    sd.land = (origin, now) => { sd.split = origin.clone(); sd.splitT = now; sd.t = now + 600; sd.done = false; };
    sd.tick = now => {
      if (sd.done) return;
      let busy = false;
      if (sd.split && sd.split !== 'pending') {
        const k = Math.min(1, (now - sd.splitT) / 1000), e = ease(k), fp = fem.geometry.attributes.position;
        for (let j = 0; j < sd.nF; j++) fp.setXYZ(j, sd.split.x + (sd.fEnd[j * 3] - sd.split.x) * e,
          sd.split.y + (sd.fEnd[j * 3 + 1] - sd.split.y) * e, sd.split.z + (sd.fEnd[j * 3 + 2] - sd.split.z) * e);
        fp.needsUpdate = true;
        if (k < 1) busy = true;
      }
      const mp = mal.geometry.attributes.position;
      for (let m = 0; m < sd.nM; m++) {
        const k = Math.min(1, Math.max(0, (now - sd.t - sd.mDelay[m]) / 1100)), e = ease(k);
        if (!(now - sd.t - sd.mDelay[m] > 0)) { mp.setXYZ(m, 0, -1e4, 0); busy = true; continue; }
        mp.setXYZ(m, ...[0, 1, 2].map(a => sd.mFrom[m * 3 + a] + (sd.mEnd[m * 3 + a] - sd.mFrom[m * 3 + a]) * e));
        if (k < 1) busy = true;
      }
      mp.needsUpdate = true;
      sd.done = !busy;
    };
    return sd;
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
      F.tags[n].val = F.tags[n].el.appendChild(Object.assign(document.createElement('span'), { className: 'val' }));
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
    F.femaleC = new THREE.Vector3(1.4, H + 2.2, -1.8);   // female cluster centre (dialogue), flash travel end
    chapters.fireflies = F;
    // Travelling flash: a small bright ball (head) and TRAIL fainter copies behind it.
    flashes = Array.from({ length: TRAIL }, (_, j) => points(Array.from({ length: 60 - j * 8 }, (_, i) => {
      const r = 0.22 * Math.cbrt(hash(i, 51 + j)), u = 2 * hash(i, 52 + j) - 1, a = 2 * Math.PI * hash(i, 53 + j);
      const q = Math.sqrt(1 - u * u);
      return [r * q * Math.cos(a), r * u, r * q * Math.sin(a), FLASH, 4 - j * 0.45];
    })));
    scene.add(...flashes);

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

    // Signal production (Owens 2018): one dotted column per LED peak wavelength (a denser one for bright),
    // two male clusters above (left: dark base values; right: the beat's exposure).
    const rows = data.o.table1.rows, base = data.o.statements.baseline_table1;
    const S = { group: new THREE.Group(), cols: {}, dense: {}, tags: {}, rows, base,
      nms: [...new Set(rows.map(r => r.wavelength_nm))],
      row: (nm, e) => rows.find(r => r.wavelength_nm === nm && r.exposure === e),
      rate: [base.flash_frequency.value, base.flash_frequency.value], amp: [1, 1], phase: [0, 0], last: 0 };
    S.nms.forEach(nm => {
      S.cols[nm] = column(nm, H, 0.3, -0.7, nmRGB(nm), 0.5, 1.8);
      S.dense[nm] = column(nm, H, 0.3, -0.7, nmRGB(nm), 0.1, 1.8);
      S.group.add(S.cols[nm], S.dense[nm]);
      S.tags[nm] = tag(`${nm} nm`, new THREE.Vector3(x(nm), H + 0.25, 0.3), 'signal', 'row');
    });
    const BIO = nmRGB(BIO_NM);
    S.males = [-1.6, 1.6].map((dx, k) => points(Array.from({ length: 160 }, (_, i) => {   // points in a ball, r 0.5
      const r = 0.5 * Math.cbrt(hash(i, 31 + k)), u = 2 * hash(i, 32 + k) - 1, a = 2 * Math.PI * hash(i, 33 + k);
      const q = Math.sqrt(1 - u * u);
      return [dx + r * q * Math.cos(a), H + 2 + r * u, -0.3 + r * q * Math.sin(a), BIO, 2 + hash(i, 34 + k) * 2.2];
    })));
    S.maleC = [-1.6, 1.6].map(dx => new THREE.Vector3(dx, H + 2, -0.3));   // ball centres (glow transition)
    S.group.add(...S.males, floor(0.5, -0.9));
    tag('dark', new THREE.Vector3(-1.6, H + 2.8, -0.3), 'signal', 'sym');
    S.lit = tag('dark', new THREE.Vector3(1.6, H + 2.8, -0.3), 'signal', 'sym');
    // View shifted to +x and pulled back so the males and columns sit left of the strip + card (human, AI_LOG Firefly
    // tabs review round 6k; was pos (-0.6, 4.4, 15), target (0.3, 2.6, -0.3)). Amounts: agent choices.
    S.view = { pos: new THREE.Vector3(0.7, 4.5, 17.5), target: new THREE.Vector3(1.6, 2.6, -0.3), sway: 0.8 };
    chapters.signal = S;

    // Mate-finding (Kivelä 2023): control (left) vs the beat's treatment (right), centred where the Signal males are.
    const K = data.k;
    const G = { group: new THREE.Group(), cols: {}, t1: K.paper.table1.rows, t3: K.paper.table3.rows,
      traps: t => K.traps.filter(r => r.treatment === t), mid: new THREE.Vector3(0, H + 2, -0.3), fresh: true };
    const FEMALE = nmRGB(562), MALE = new THREE.Color(0.95, 0.92, 0.82);
    G.sides = [-1.6, 1.6].map(dx => glowSide(new THREE.Vector3(dx, H + 2, -0.3), FEMALE, MALE));
    G.sides.forEach(sd => G.group.add(sd.fem, sd.mal));
    G.t1.filter(r => r.peak_nm).forEach(r => {
      G.cols[r.treatment] = column(r.peak_nm, H, 0.3, -0.7, r.treatment === 'white' ? new THREE.Color(1, 1, 1) : nmRGB(r.peak_nm), 0.25, 1.8);
      G.group.add(G.cols[r.treatment]);
    });
    G.group.add(floor(0.5, -0.9));
    G.top = G.sides.map((sd, k) => tag(k ? '' : 'dark (control)', sd.c.clone().add(new THREE.Vector3(0, 1.05, 0)), 'glow', 'sym'));
    G.pct = G.sides.map(sd => tag('', sd.c.clone().add(new THREE.Vector3(0, -1.1, 0)), 'glow', 'sym'));
    // Same framing as Signal production (round 6k), so the pair sits left of the strip and card.
    G.view = { pos: new THREE.Vector3(0.7, 4.5, 17.5), target: new THREE.Vector3(1.6, 2.6, -0.3), sway: 0.8 };
    chapters.glow = G;

    Object.values(chapters).forEach(c => { c.group.visible = false; scene.add(c.group); });
    for (const ch of ['fireflies', 'mice', 'signal', 'glow']) {
      [400, 500, 600, 700].forEach(nm => tag(String(nm), new THREE.Vector3(x(nm), -0.2, 0.5), ch, 'tick'));
    }
    // Continuous scene: move each band (group, its tags, its views) back by its depth offset.
    Object.entries(BANDS).forEach(([ch, dz]) => {
      const c = chapters[ch];
      c.group.position.z = dz;
      tags.filter(t => t.chapter === ch).forEach(t => { t.pos.z += dz; });
      [c.view, ...Object.values(c.views || {})].forEach(v => { v.pos.z += dz; v.target.z += dz; });
    });
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

  // Beat `values` ({ lamp: text }, fireflies): once the view is open and after SPLIT_HOLD, the big value fades and one
  // copy per lamp flies from it to that lamp's row tag, where it stays (human, AI_LOG Experience refinement step 17,
  // option A). split = { b, t (start time, set once the door is open) } or null. Timings: agent choices.
  const SPLIT_HOLD = 1200, SPLIT_MS = 900;
  let split = null;
  function clearSplit() {
    split = null;
    labels.querySelectorAll('.fly, .val .head').forEach(e => e.remove());
    number.classList.remove('split');
  }
  function runSplit() {
    const F = chapters.fireflies, src = number.querySelector('.value'), rg = document.createRange();
    rg.selectNodeContents(src);
    const r0 = rg.getBoundingClientRect();   // the text itself (.value is a block as wide as the label)
    const base = labels.getBoundingClientRect(), s0 = parseFloat(getComputedStyle(src).fontSize) / 12;
    number.classList.add('split');   // the range and its grey label fade (AI_LOG Experience refinement step 18)
    const keys = Object.keys(split.b.values);
    // `valuesLabel`: flies from the grey label to sit above the topmost value, as the values' axis label (human, step 18).
    const lab = number.querySelector('.label'), shown = keys.filter(n => !F.tags[n].el.hidden && F.tags[n].val.offsetWidth);
    if (split.b.valuesLabel && lab && shown.length) {
      const top = shown.reduce((a, n) => (F.tags[n].val.getBoundingClientRect().top < F.tags[a].val.getBoundingClientRect().top ? n : a));
      const head = F.tags[top].val.appendChild(Object.assign(document.createElement('span'), { className: 'head', textContent: split.b.valuesLabel }));
      const rl = lab.getBoundingClientRect(), rh = head.getBoundingClientRect();
      const fly = labels.appendChild(Object.assign(document.createElement('div'), { className: 'fly head', textContent: split.b.valuesLabel }));
      fly.animate([{ transform: `translate(${rl.left + (rl.width - rh.width) / 2 - base.left}px, ${rl.top - base.top}px)`, opacity: 0.3 },
        { transform: `translate(${rh.left - base.left}px, ${rh.top - base.top}px)`, opacity: 1 }], { duration: SPLIT_MS, easing: 'ease-in-out' })
        .onfinish = () => { fly.remove(); head.classList.add('shown'); };
    }   // story order (low → high), so the copies start spread across the range
    keys.forEach((n, j) => {
      const val = F.tags[n].val, r1 = val.getBoundingClientRect();
      if (F.tags[n].el.hidden || !r1.width) { val.classList.add('shown'); return; }
      const fly = Object.assign(document.createElement('div'), { className: 'fly', textContent: split.b.values[n] });
      labels.append(fly);
      // Start size: the range's, or smaller so the copies fit side by side across the range's width.
      const s = Math.min(s0, r0.width / keys.length / val.offsetWidth);
      const a = `translate(${r0.left + r0.width * (j + 0.5) / keys.length - base.left - val.offsetWidth * s / 2}px, ` +
        `${r0.top + (r0.height - val.offsetHeight * s) / 2 - base.top}px) scale(${s})`;
      const z = `translate(${r1.left - base.left}px, ${r1.top - base.top}px) scale(1)`;
      fly.animate([{ transform: a, opacity: 0.2 }, { transform: z, opacity: 1 }], { duration: SPLIT_MS, easing: 'ease-in-out' })
        .onfinish = () => { fly.remove(); val.classList.add('shown'); };
    });
    split = null;
  }

  function enterBeat(b) {
    clearSplit();
    showNumber(b);
    if (current.manual) onLine?.(b?.line ?? 0);
    if (b?.caption) caption.textContent = b.caption;
    caption.classList.toggle('on', Boolean(b?.caption));
    if (current.chapter === 'fireflies') {
      const F = chapters.fireflies;
      fadeTo(F.eye, 0.45);
      fadeTo(F.flash, 0.5);
      fadeTo(F.talk.male, 0.06); fadeTo(F.talk.female, 0.05);
      // `lamps`: several lamps lit on one beat (AI_LOG Firefly flow step 12); else the one `lamp`.
      const lit = b.lamps ?? (b.lamp ? [b.lamp] : []);
      LAMPS.forEach(n => {
        const on = lit.includes(n);
        fadeTo(F.lamps[n], on ? 0.9 : lit.length ? 0.07 : 0);
        fadeTo(F.seen[n], on ? 1 : 0);
        F.tags[n].el.classList.toggle('on', on);
        F.tags[n].val.textContent = b.values?.[n] ?? '';
        F.tags[n].val.classList.remove('shown');
        F.lamps[n].scale.y = F.seen[n].scale.y = 1;
      });
      if (b.values) split = { b, t: null };
      if (b.brighter) {  // F-C: the lamp grows to ten times the photons (documented: dim × 10 = bright)
        const grow = [F.lamps[b.lamp], F.seen[b.lamp]];
        fades.push({ t: performance.now() + 600, ms: 2200, tick: k => grow.forEach(o => { o.scale.y = 1 + 9 * k; }) });
      }
    } else if (current.chapter === 'signal') {
      // Beat = { nm, exposure } from story.js, or {} for dark. Numbers: Table 1 (rows' printed text) and its footnote.
      const S = chapters.signal, r = b.nm ? S.row(b.nm, b.exposure) : null;
      S.nms.forEach(nm => {
        const on = b.nm === nm;
        fadeTo(S.cols[nm], on ? 0.95 : b.nm ? 0.1 : 0.22);
        fadeTo(S.dense[nm], on && b.exposure === 'bright' ? 0.75 : 0);
        S.tags[nm].el.classList.toggle('on', on);
      });
      S.rate[1] = r ? r.flash_frequency.mean : S.base.flash_frequency.value;
      S.amp[1] = r ? r.flash_intensity.ratio_to_dark : 1;
      S.lit.el.textContent = r ? `${b.nm} nm · ${b.exposure}` : 'dark';
      showNumber(null);   // no big number on this tab (human, round 6j)
    } else if (current.chapter === 'glow') {
      // Beat = { treatment }: right side = its traps, its column lit. Control (left) refills on entering the chapter.
      // Arriving from Female response, both sides wait for the travelling glow to land (land() then splits them out).
      const G = chapters.glow, t = b.treatment, now = performance.now(), wait = travel?.pair === 'fg' && travel.dir > 0;
      const share = tr => G.t3.find(r => r.treatment === tr).printed.split(' ')[3];
      Object.entries(G.cols).forEach(([k, p]) => fadeTo(p, k === t ? 0.9 : 0));
      if (G.fresh) { G.sides[0].fill(G.traps('control'), now, wait); G.fresh = false; }
      G.sides[1].fill(G.traps(t), now, wait);
      G.sides.forEach(sd => { fadeTo(sd.fem, wait ? 0 : 1, 300); fadeTo(sd.mal, 0.85, 300); });
      G.top[1].el.textContent = `${t} · ${G.t1.find(r => r.treatment === t).peak_nm} nm`;
      G.pct[0].el.textContent = `${share('control')} % with ≥ 1 male`;
      G.pct[1].el.textContent = `${share(t)} % with ≥ 1 male`;
      showNumber(null);   // values in the strip and under each side (round 6o)
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

  // Signal production: each male flashes `rate` times per minute (evenly spaced; the phase carries over when the
  // rate changes), ~0.2 s per flash, peak opacity ∝ `amp` (intensity ratio to dark; dark = 1).
  function animateSignal(now) {
    const S = chapters.signal, dt = S.last ? Math.min(0.1, (now - S.last) / 1000) : 0;
    S.last = now;
    S.males.forEach((m, k) => {
      const rate = S.rate[k] * SIGNAL_SPEED;   // flashes per minute as shown
      S.phase[k] = (S.phase[k] + dt * rate / 60) % 1;
      const since = S.phase[k] * 60 / rate;   // seconds since this male's last flash
      op(m).value = 0.14 + 0.4 * S.amp[k] * Math.exp(-(((since - 0.1) / 0.06) ** 2));
    });
  }

  // Strip position (human, round 6j): right-aligned with the story card, just above it, and as wide as it.
  function placeStrip() {
    const card = document.getElementById('card');
    if (strip.hidden || !card || card.hidden) return;
    const r = card.getBoundingClientRect();
    strip.style.width = `${r.width}px`;
    strip.style.bottom = `${window.innerHeight - r.top + 8}px`;
  }
  // Signal production strip: Table 1 means ± SD (counts; peaks/min) per wavelength, dim filled, bright ring;
  // dashed line = dark base value. Click a mark to go to its beat.
  function renderStrip() {
    strip.hidden = current?.chapter !== 'signal' && current?.chapter !== 'glow';
    if (strip.hidden) return;
    if (current.chapter === 'glow') { renderGlowStrip(); return; }
    const S = chapters.signal, cur = current.beats[manualBeat] || {};
    const beatOf = (nm, e) => current.beats.findIndex(b => b.nm === nm && b.exposure === e);
    const rows = S.rows.filter(r => beatOf(r.wavelength_nm, r.exposure) >= 0);   // bright only (round 6j)
    const W = 330, L = 58, PH = 58, slot = (W - L - 6) / S.nms.length;
    let s = '';
    [['flash_intensity', 'flash intensity (counts)', 1], ['flash_frequency', 'flash frequency (peaks/min)', 5]]
      .forEach(([key, title, sdTok], pi) => {
        const top = 16 + pi * (PH + 30), dark = S.base[key].value;
        const max = Math.max(...rows.map(r => r[key].mean + r[key].sd));
        const y = v => top + PH - Math.max(0, v) / max * PH;
        s += `<text class="title" x="0" y="${top - 5}">${title}</text>` +
          `<line class="axis" x1="${L - 4}" x2="${W}" y1="${y(0)}" y2="${y(0)}"/>` +
          `<line class="dark" x1="${L - 4}" x2="${W}" y1="${y(dark)}" y2="${y(dark)}"/>` +
          `<text class="tick" x="${L - 8}" y="${y(dark) + 3}">dark ${dark}</text>` +
          `<text class="tick" x="${L - 8}" y="${y(0) + 3}">0</text>`;
        rows.forEach(r => {
          const t = r.printed.split(' '), v = r[key], on = cur.nm === r.wavelength_nm && cur.exposure === r.exposure;
          const cx = L + slot * (S.nms.indexOf(r.wavelength_nm) + 0.5);
          const c = css(nmRGB(r.wavelength_nm)), unit = pi ? 'peaks/min' : 'counts';
          s += `<g class="m${on ? ' on' : ''}" data-beat="${beatOf(r.wavelength_nm, r.exposure)}">` +
            `<title>${r.wavelength_nm} nm · ${r.exposure}: ${t[sdTok]} ${t[sdTok + 1]} ${unit} (× ${t[sdTok + 2]} of dark), ` +
            `p = ${t[sdTok + 3]}</title>` +
            `<rect x="${cx - 5}" y="${top - 2}" width="10" height="${PH + 4}" fill="transparent"/>` +
            `<line x1="${cx}" x2="${cx}" y1="${y(v.mean - v.sd)}" y2="${y(v.mean + v.sd)}" stroke="${c}"/>` +
            `<circle cx="${cx}" cy="${y(v.mean)}" r="${on ? 4.5 : 3}" stroke="${c}" ` +
            `fill="${c}"/></g>`;
        });
      });
    const yb = 16 + 2 * (PH + 30) - 22;
    S.nms.forEach((nm, i) => { s += `<text class="nm" x="${L + slot * (i + 0.5)}" y="${yb}">${nm}</text>`; });
    s += `<text class="tick" x="${L - 8}" y="${yb}">nm</text>`;
    s += `<text class="legend" x="0" y="${yb + 16}">bright 10× · bars ± SD · Owens et al. 2018, Table 1</text>`;
    strip.innerHTML = `<svg viewBox="0 0 ${W} ${yb + 20}">${s}</svg>`;
    placeStrip();
  }

  // Mate-finding strip (round 6o): Table 3 share of dummy females with ≥ 1 male per lit treatment (printed text),
  // dashed line = control. Click a mark to go to its beat.
  function renderGlowStrip() {
    const G = chapters.glow, cur = current.beats[manualBeat] || {};
    const W = 330, L = 58, PH = 70, top = 16, slot = (W - L - 6) / current.beats.length;
    const y = v => top + PH - v / 100 * PH, row = t => G.t3.find(r => r.treatment === t);
    const ctl = row('control');
    let s = `<text class="title" x="0" y="${top - 5}">dummy females with ≥ 1 male (%)</text>` +
      `<line class="axis" x1="${L - 4}" x2="${W}" y1="${y(0)}" y2="${y(0)}"/>` +
      `<line class="dark" x1="${L - 4}" x2="${W}" y1="${y(ctl.success_percent)}" y2="${y(ctl.success_percent)}"/>` +
      `<text class="tick" x="${L - 8}" y="${y(ctl.success_percent) + 3}">dark ${ctl.printed.split(' ')[3]}</text>` +
      `<text class="tick" x="${L - 8}" y="${y(0) + 3}">0</text>`;
    current.beats.forEach((b, i) => {
      const r = row(b.treatment), nm = G.t1.find(q => q.treatment === b.treatment).peak_nm, on = cur.treatment === b.treatment;
      const cx = L + slot * (i + 0.5), c = b.treatment === 'white' ? '#fff' : css(nmRGB(nm)), v = r.printed.split(' ')[3];
      s += `<g class="m${on ? ' on' : ''}" data-beat="${i}"><title>${b.treatment} ${nm} nm: ${v} % ` +
        `(${r.n_at_least_one} of ${r.n_zero + r.n_at_least_one})</title>` +
        `<rect x="${cx - 12}" y="${top - 2}" width="24" height="${PH + 4}" fill="transparent"/>` +
        `<line x1="${cx}" x2="${cx}" y1="${y(0)}" y2="${y(r.success_percent)}" stroke="${c}"/>` +
        `<circle cx="${cx}" cy="${y(r.success_percent)}" r="${on ? 4.5 : 3}" stroke="${c}" fill="${c}"/>` +
        `<text class="nm" x="${cx}" y="${y(r.success_percent) - 8}">${v}</text></g>` +
        `<text class="nm" x="${cx}" y="${top + PH + 14}">${b.treatment} ${nm}</text>`;
    });
    s += `<text class="legend" x="0" y="${top + PH + 32}">dashed = no light (control) · Kivelä et al. 2023, Table 3</text>`;
    strip.innerHTML = `<svg viewBox="0 0 ${W} ${top + PH + 36}">${s}</svg>`;
    placeStrip();
  }

  function plain() {
    canvas.style.transform = canvas.style.transformOrigin = canvas.style.clipPath = '';
    canvas.style.maskImage = canvas.style.webkitMaskImage = canvas.style.opacity = '';
    labels.style.visibility = number.style.visibility = toggle.style.visibility = strip.style.visibility = '';
    chapters.signal?.males.forEach(p => { p.position.set(0, 0, 0); });
    chapters.glow?.sides.forEach(sd => [sd.fem, sd.mal].forEach(p => { p.position.set(0, 0, 0); p.scale.setScalar(1); }));
  }
  function door(now) {
    if (!trans) return;
    if (trans.style === 'glow') { glowDoor(now); return; }
    const { x: dx, y: dy } = trans, w = window.innerWidth, h = window.innerHeight;
    const k0 = Math.min(1, Math.max(0, (now - trans.t) / trans.ms)), k = ease(trans.dir > 0 ? k0 : 1 - k0);
    // `flat`: the circle only widens, the scene is not scaled (study sites; AI_LOG Experience refinement step 17).
    const R = Math.hypot(Math.max(dx, w - dx), Math.max(dy, h - dy)), rs = DOOR_R + (R - DOOR_R) * k, sc = trans.flat ? 1 : 0.3 + 0.7 * k;
    canvas.style.transformOrigin = `${dx}px ${dy}px`;
    canvas.style.transform = `scale(${sc})`;
    canvas.style.clipPath = `circle(${rs / sc}px at ${dx}px ${dy}px)`;
    labels.style.visibility = number.style.visibility = toggle.style.visibility = 'hidden';
    if (k0 >= 1) { const t = trans; trans = null; plain(); t.done?.(); }
  }
  function glowDoor(now) {
    const w = window.innerWidth, h = window.innerHeight, at = trans.at?.() ?? { x: w / 2, y: h / 2 };
    const k0 = Math.min(1, Math.max(0, (now - trans.t) / trans.ms)), k = trans.dir > 0 ? k0 : 1 - k0;
    const r = Math.hypot(Math.max(at.x, w - at.x), Math.max(at.y, h - at.y)) * ease(k), soft = 80 + 0.3 * r;
    canvas.style.maskImage = canvas.style.webkitMaskImage =
      `radial-gradient(circle at ${at.x}px ${at.y}px, #000 ${r}px, transparent ${r + soft}px)`;
    canvas.style.opacity = String(Math.min(1, 2.5 * k));
    labels.style.visibility = number.style.visibility = toggle.style.visibility = strip.style.visibility = 'hidden';
    Object.assign(trans, { x: at.x, y: at.y, m: ease(Math.min(1, Math.max(0, (k - 0.3) / 0.7))) });
    if (k0 >= 1) { const t = trans; trans = null; plain(); t.done?.(); }
  }
  // Signal males during a glow transition: m = 0 both gathered at the point under the glow (on their own depth
  // plane) and bright, standing in for the glow; m = 1 at their places, flashing as usual. Runs after the camera
  // update (so the point is projected correctly) and after animateSignal (whose opacity it raises while gathered).
  const ray = new THREE.Vector3(), under = new THREE.Vector3();
  // Mate-finding ↔ Local firefly (human: "scene closes into the point", AI_LOG Firefly tabs review round 7d): the same
  // for both sides of the pair: each side's dummy females and males shrink (scale 0.12 at m = 0) towards the point
  // under the glow, the females bright. Display device, not data (scale and brightness: agent choices).
  const toUnder = (group, zLocal) => {
    camera.updateMatrixWorld();
    ray.set(trans.x / canvas.clientWidth * 2 - 1, 1 - trans.y / canvas.clientHeight * 2, 0.5).unproject(camera)
      .sub(camera.position).normalize();
    const zc = group.position.z + zLocal;
    under.copy(camera.position).addScaledVector(ray, (zc - camera.position.z) / ray.z);
    return group.worldToLocal(under);
  };
  function gatherMales() {
    if (trans?.style !== 'glow' || trans.m == null) return;
    if (current?.chapter === 'signal') {
      const S = chapters.signal;
      toUnder(S.group, S.maleC[0].z);
      S.males.forEach((p, k) => {
        p.position.copy(under).lerp(S.maleC[k], trans.m).sub(S.maleC[k]);
        op(p).value = Math.max(op(p).value, 0.9 * (1 - trans.m));
      });
    } else if (current?.chapter === 'glow') {
      const G = chapters.glow, sc = 0.12 + 0.88 * trans.m;
      toUnder(G.group, G.mid.z);
      G.sides.forEach(sd => [sd.fem, sd.mal].forEach(p => {
        p.scale.setScalar(sc);
        p.position.copy(under).lerp(sd.c, trans.m).addScaledVector(sd.c, -sc);
        if (p === sd.fem) op(p).value = Math.max(op(p).value, 0.9 * (1 - trans.m));
      }));
    }
  }
  // Flash travel: path from the right Signal male to the Female response female (world coordinates, slight arc), the
  // camera between the two chapter views, pulled in behind the flash mid-way. Forward: the female answers on arrival
  // (the dialogue clock is set so her reply falls just after landing). Returns true while travelling.
  const pA = new THREE.Vector3(), pB = new THREE.Vector3(), pT = new THREE.Vector3(), chase = new THREE.Vector3();
  const BEHIND = new THREE.Vector3(-0.4, 0.7, 4.2);   // camera offset from the flash at mid-path
  const flashAt = (k, out) => out.copy(pA).lerp(pB, k).setY(out.y + 0.9 * Math.sin(Math.PI * k));
  // pair 'sf' = Signal male → Female response female; 'fg' = Female response female → Mate-finding pair centre.
  // dir 1 = in story order, −1 = back. A/B = start/end chapters (their views frame the camera path).
  function startTravel(pair, dir, now) {
    const S = chapters.signal, F = chapters.fireflies, G = chapters.glow;
    const [a, b] = pair === 'sf' ? [S, F] : [F, G];
    if (pair === 'sf') { pA.copy(S.maleC[1]).add(S.group.position); pB.copy(F.femaleC).add(F.group.position); }
    else { pA.copy(F.femaleC).add(F.group.position); pB.copy(G.mid).add(G.group.position); }
    travel = { pair, dir, t: now, ms: TRAVEL_MS, vA: a.view, vB: b.view };
    labels.style.visibility = number.style.visibility = toggle.style.visibility = strip.style.visibility = 'hidden';
  }
  function endTravel() {
    travel = null;
    flashes.forEach(f => { op(f).value = 0; });
    labels.style.visibility = number.style.visibility = toggle.style.visibility = strip.style.visibility = '';
  }
  function moveTravel(now) {
    const k0 = Math.min(1, (now - travel.t) / travel.ms), k = ease(travel.dir > 0 ? k0 : 1 - k0);
    flashes.forEach((f, j) => {
      const kj = Math.min(1, Math.max(0, k - travel.dir * j * 0.04));
      flashAt(kj, f.position);
      op(f).value = (1 - j / TRAIL) * Math.min(1, k0 / 0.08, (1 - k0) / 0.12);
    });
    const A = travel.vA, B = travel.vB, mid = Math.sin(Math.PI * k);
    flashAt(k, pT);
    chase.copy(pT).add(BEHIND);
    cam.pos.copy(A.pos).lerp(B.pos, k).lerp(chase, 0.6 * mid);
    cam.target.copy(A.target).lerp(B.target, k).lerp(pT, 0.75 * mid);
    cam.t = now;
    if (k0 < 1) return true;
    // Landing on the Female response female (forward from Signal, or back from Mate-finding): her reply (cycle phase
    // 0.6) comes ~60 ms after. Landing in Mate-finding: the glow splits into both sides' dummy females.
    if ((travel.pair === 'sf') === (travel.dir > 0)) t0 = now - 0.55 * 1200;
    else if (travel.pair === 'fg') {
      const G = chapters.glow;
      G.sides.forEach(sd => { sd.land(G.mid, now); fadeTo(sd.fem, 1, 250); });
    }
    endTravel();
    return false;
  }
  function hideNow() {
    if (travel) endTravel();
    trans = null; plain(); clearSplit();
    canvas.hidden = labels.hidden = number.hidden = toggle.hidden = strip.hidden = true; running = false; current = null;
    caption.classList.remove('on');
  }
  function renderToggle() {
    toggle.hidden = !current?.manual;
    if (toggle.hidden) return;
    if (current.chapter === 'signal') {   // one button per beat (wavelength; bright 10× only, round 6j)
      toggle.innerHTML = current.beats.map((b, i) =>
        `<button data-beat="${i}" aria-pressed="${i === manualBeat}">${b.nm ?? 'dark'}</button>`).join('');
      return;
    }
    toggle.innerHTML = current.beats.map((b, i) =>
      `<button data-beat="${i}" aria-pressed="${i === manualBeat}">${b.button ?? (b.treatment && b.treatment !== 'control'
        ? b.treatment : b.lamp ? LAMP_NAME[b.lamp] : 'dark')}</button>`).join('');   // `button`: the beat's own word
  }
  function goBeat(i) {
    if (!current?.manual || i < 0 || i >= current.beats.length) return false;
    manualBeat = i;
    renderToggle();
    renderStrip();
    return true;
  }

  // ── loop ─────────────────────────────────────────────────────────────────
  const v = new THREE.Vector3();
  function frame(now) {
    if (!running) return;
    door(now);
    if (!running) return;   // a closing door just finished
    const ms = current.every ?? 4200, i = current.manual ? manualBeat : Math.floor((now - t0) / ms) % current.beats.length;
    if (i !== beatIndex) { beatIndex = i; enterBeat(current.beats[i]); }
    fades = fades.filter(f => {
      const k = Math.min(1, Math.max(0, (now - f.t) / f.ms));
      if (f.tick) f.tick(ease(k)); else op(f.p).value = f.from + (f.to - f.from) * ease(k);
      return k < 1;
    });
    if (current.chapter === 'fireflies' && travel?.pair === 'sf' && travel.dir > 0) {   // waiting for the flash: dialogue at rest
      const F = chapters.fireflies;
      op(F.talk.male).value = 0.14; op(F.talk.female).value = 0.12; op(F.talk.signal).value = 0;
    } else if (current.chapter === 'fireflies') animateDialogue(now);
    else if (current.chapter === 'signal') animateSignal(now);
    else if (current.chapter === 'glow') chapters.glow.sides.forEach(sd => sd.tick(now));
    else if (current.chapter === 'mice') Object.values(chapters.mice.dials).forEach(d => d.tick(now));
    // A beat may name a closer view (`view` key → chapter.views); the camera eases towards it.
    const ch = chapters[current.chapter], vw = ch.views?.[current.beats[beatIndex]?.view] || ch.view;
    if (!cam) cam = { pos: vw.pos.clone(), target: vw.target.clone(), t: now };
    if (!(travel && moveTravel(now))) {
      const k = 1 - Math.exp(-(now - cam.t) / 450);  // time-based, so throttled frames still arrive
      cam.t = now; cam.pos.lerp(vw.pos, k); cam.target.lerp(vw.target, k);
    }
    camera.position.set(cam.pos.x + Math.sin(now / 9000) * (vw.sway ?? 1.2), cam.pos.y, cam.pos.z);
    camera.lookAt(cam.target);
    gatherMales();
    renderer.render(scene, camera);
    const w = canvas.clientWidth, h = canvas.clientHeight;
    tags.forEach(t => {
      t.el.hidden = t.chapter !== current.chapter || t.el.classList.contains('off') ||
        (t.el.classList.contains('row') && !t.el.classList.contains('on'));
      if (t.el.hidden) return;
      v.copy(t.pos).project(camera);
      t.el.style.transform = `translate(${(v.x + 1) / 2 * w}px, ${(1 - v.y) / 2 * h}px)`;
    });
    if (split && !trans && !travel) { split.t ??= now + SPLIT_HOLD; if (now >= split.t) runSplit(); }
    requestAnimationFrame(frame);
  }

  function resize() {
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  window.addEventListener('resize', placeStrip);
  resize();

  return {
    // Screen position of the Female response female (dialogue cluster centre) while that chapter shows, else null.
    // For the firefly guide in main.js (ladder plan phase 4; AI_LOG "Story review" steps 7–8).
    femaleAt() {
      const F = chapters.fireflies;
      if (!running || current?.chapter !== 'fireflies' || !F?.femaleC) return null;
      const v = F.femaleC.clone().add(F.group.position).project(camera);
      return { x: (v.x + 1) / 2 * window.innerWidth, y: (1 - v.y) / 2 * window.innerHeight };
    },
    // st = a story step's `spectral` key ({ chapter, beats, every }), or null to hide the view.
    // from = {x, y}: grow out of that screen point; to = {x, y}: shrink into it, then hide. onDone: when finished.
    // glow = () => {x, y} (a site's glow on the globe): open out of it after GLOW_DELAY, or (st = null) close into it.
    // beat: 'last' starts a manual chapter on its last beat (arriving backwards).
    async set(st, { from = null, to = null, glow = null, onDone = null, beat = 0, fly = 2200, dive = 0, flat = false } = {}) {
      if (!st) {
        const done = () => { hideNow(); onDone?.(); };
        if (glow && running && current) { trans = { style: 'glow', dir: -1, at: glow, t: performance.now(), ms: GLOW_CLOSE_MS, done }; door(trans.t); }
        else if (to && running && current) trans = { dir: -1, x: to.x, y: to.y, t: performance.now(), ms: CLOSE_MS, done, flat };
        else { hideNow(); if (glow) onDone?.(); }   // nothing open: the globe side still needs its end state
        return;
      }
      // Between two steps of the continuous firefly scene (BANDS) the view glides instead of restarting.
      const cont = running && current && current !== st && BANDS[current.chapter] != null && BANDS[st.chapter] != null;
      const pair = cont && `${current.chapter}>${st.chapter}`;
      if (travel) endTravel();
      current = st;
      trans = null; plain();
      await loaded;
      if (current !== st) return;  // the step changed while the data was loading
      const band = BANDS[st.chapter] != null;
      GAIN.value = band ? BAND_GAIN : 1; SIZE.value = band ? BAND_SIZE : 1;
      Object.entries(chapters).forEach(([k, c]) => { c.group.visible = k === st.chapter || (band && BANDS[k] != null); });
      if (!cont) Object.values(chapters).forEach(c => c.group.traverse(o => { if (o.isPoints) op(o).value = 0; }));
      tags.forEach(t => t.el.classList.remove('on'));
      fades = [];
      if (st.chapter !== 'fireflies') [chapters.fireflies.lamps, chapters.fireflies.seen]   // undo a ×10 amber lamp
        .forEach(o => Object.values(o).forEach(p => { p.scale.y = 1; }));
      if (band) Object.keys(BANDS).filter(k => k !== st.chapter)
        .forEach(k => chapters[k].group.traverse(o => { if (o.isPoints) fadeTo(o, FAINT / BAND_GAIN, 1200); }));
      beatIndex = -1;
      manualBeat = beat === 'last' ? st.beats.length - 1 : 0;
      renderToggle();
      renderStrip();
      if (!cont) cam = null;  // snap to the first view on entering a step (glide within the continuous scene)
      t0 = performance.now();
      const PAIRS = { 'signal>fireflies': ['sf', 1], 'fireflies>signal': ['sf', -1], 'fireflies>glow': ['fg', 1], 'glow>fireflies': ['fg', -1] };
      if (st.chapter === 'glow') chapters.glow.fresh = true;   // control side refills (and its males fly in) on entry
      if (PAIRS[pair]) startTravel(...PAIRS[pair], t0);
      // A door with `dive` (the camera flight, ms; study site, main.js) waits and opens over the glow timings scaled to
      // the dive (AI_LOG Impacts firefly-first step 8); without it, at once over OPEN_MS as before.
      if (from && dive) { const k = dive / 2200;
        trans = { dir: 1, x: from.x, y: from.y, t: t0 + GLOW_DELAY * k, ms: GLOW_OPEN_MS * k, done: onDone }; door(t0); }
      else if (from) { trans = { dir: 1, x: from.x, y: from.y, t: t0, ms: OPEN_MS, done: onDone, flat }; door(t0); }
      // `fly`: the step's camera flight; the opening scales with it (timings were set for 2200; AI_LOG Impacts firefly-first
      // step 8, slower dive into Female response).
      else if (glow) { const k = fly / 2200;
        trans = { style: 'glow', dir: 1, at: glow, t: t0 + GLOW_DELAY * k, ms: GLOW_OPEN_MS * k, done: onDone }; door(t0); }
      canvas.hidden = labels.hidden = false;
      if (!running) { running = true; requestAnimationFrame(frame); }
    },
    // Manual chapters: move one beat; false at either end (or when not manual), so the caller can change step.
    step(delta) { return !trans && !travel && goBeat(manualBeat + delta); },
  };
}
