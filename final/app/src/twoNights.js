// Two measured nights: Philadelphia (City) and Cherry Springs (Rural) night spectra in one 3D space, split by a
// draggable divider (Philadelphia left). Human decisions: handoff 2026-10-04_two-nights-spectra.md and AI_LOG
// "Firefly narrative" round 3c (own module, `nights: true` story key, OrbitControls + CSS3DRenderer from three's
// examples folder, no surrounding text panels, axis and unit labels kept).
// Reproduces the "3D Spectrum" Physical (log) view of Linda's philadelphia-spectral-space draft: point shader,
// geometry, colours, scene, camera, controls and axis frame from src/scene/SpectralPoints.tsx, SceneCanvas.tsx,
// particles.ts, cameras.ts; focused spectrum auto-scans the 240 spectra in a 90 s loop (timePlayback.ts).
// Both sites share the focus index (both have 240 spectra).
//
// Data (dev server, /spectra/ = data/derived/spectra/, pipeline/spectra/01_night_spectra.py):
//   spectra_meta.json  wavelengths (280–840 nm, 2 nm), shared log10 display limits (inferred), units
//   philadelphia.json, cherry_springs.json  240 × 281 irradiance, W m⁻² nm⁻¹ (measured; null = NaN in source)
//   species_curves.json  six species' response curves on the same grid (pipeline/spectra/02_species_curves.py;
//                        human night `inferred` from CIE V′(λ); animal curves provisional, no label: human, round 7j)
//
// Species perceptions (human, AI_LOG Firefly tabs review round 7j; story key `nights: 'species'`): the draft's
// "Interpretive" receptor cloud (SpectralPoints.tsx receptor layer, particles.ts deterministicCloudPosition), both
// sites behind the same divider. Each (time, wavelength) cell of a site's 240 spectra is one point per receptor, at
// the same stable pseudo-random cloud place for every receptor and both sites (position encodes neither wavelength,
// time nor place); brightness, size and opacity = log-normalised S(t,λ) × R(λ) (same display limits as the physical
// view), one layer per receptor in its draft channel colour (channel identifiers, not perceived colours). Species
// change every 1.5 s (human): human night, rock pigeon, Carolina sphinx, Big Dipper firefly, bronze ground beetle,
// bobolink. Arriving from Two measured nights the measured points fade while each receptor layer rises from its
// contribution height into the cloud; axes and labels fade (positions no longer mean wavelength or time).
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { CSS3DRenderer, CSS3DObject } from 'three/examples/jsm/renderers/CSS3DRenderer.js';

const SITES = [{ id: 'philadelphia', name: 'Philadelphia', side: 1 }, { id: 'cherry_springs', name: 'Cherry Springs', side: -1 }];
const SCAN_MS = 90000;   // draft TIME_SCAN_CYCLE_MS
const CAMERA = { position: [17, 11, 20], target: [0, 3.2, 0], fov: 44 };   // draft CAMERA_PRESETS.default
// Local firefly ↔ Two measured nights (human: "two points, two halves", AI_LOG Firefly tabs review round 7f): the two
// Spitschan sites glow on the globe (impacts.js); the glows lift off and slide to their halves (Philadelphia left,
// Cherry Springs right, so they cross: Philadelphia lies east of Cherry Springs), then each half opens out of its glow
// and the divider and names appear. Back plays it in reverse. Display device, not data; timings: agent choices.
const T_WAIT = 1800, T_SLIDE = 800, T_OPEN = 1400, T_CLOSE = 900;
// Divider sweep (human, AI_LOG Firefly tabs review round 7g): after the view opens the divider moves on its own from
// the middle to the left edge, across to the right edge and back, looping; dragging the handle stops it until the step
// is entered again. Period and range (edges at 2 % / 98 % so the handle stays on screen): agent choices.
const SWEEP_MS = 16000, SWEEP_HALF = 0.48;
// Two measured nights: the divider sweeps once instead of looping (human, AI_LOG "Amber highlight" step 4: "go from
// left to right once (cherry springs to philly)"): from where it is to the left edge (Cherry Springs fills the view),
// hold, then across to the right edge (Philadelphia fills it) and stop; onSweep(true) then revealed the card's second
// part (main.js). Now stepped by beats (BEATS below). Species perceptions keeps the loop. Durations: agent choices.
// The divider rests EDGE_PX from the screen edge during the hold and at the end, visible and draggable (human, AI_LOG
// "Amber highlight" step 5: "keep draggable divider please, not hidden"): the menu and the card sit 16 px in from the
// edges (style.css), so line and handle stay clear of them; the handle shows as a half-circle tab. 2 px: agent choice.
const ONCE = { toLeft: 1500, hold: 4000, across: 7000 }, EDGE_PX = 2;
// Beats (human, AI_LOG Firefly flow step 4, option S1: "arrows should guide us from Cherry springs --> philadelphia -->
// firefly wavelength .. and only on firefly wavelength, should the firefly study text appear"): instead of the timed
// sweep, ← → and the nav arrows step three beats. 0: the divider moves to the left edge (Cherry Springs fills the view,
// ONCE.toLeft); 1: it sweeps across to the right edge (Philadelphia, ONCE.across); 2: the Firefly window narrows the
// spectrum (WINDOW.move). onBeat(k) shows the step's line k: on arrival for 0, at the end of the sweep for 1, once the
// window has narrowed for 2. Going back reverses each move. Arriving back from Species perceptions: last beat.
// ONCE.hold no longer used. Timings as before (agent choices).
// Fourth beat (human, AI_LOG Firefly flow step 10, W1): 2 = the window narrows and the firefly-eye line shows; 3 = the
// window stays and the study line shows.
// OPEN = beats before the sweep, all with the divider at the left edge; line k = beat k. 1 in AI_LOG Impacts firefly-first
// step 6 (the Perception question as an opening beat), 0 again since step 7 (Perception reinstated).
const OPEN = 0, BEATS = 4 + OPEN;
// While the divider sweeps, the view also turns slowly about its vertical axis (human, round 7h): OrbitControls
// autoRotate, one turn per 60 s / ROTATE_SPEED = 240 s, i.e. 1.5° per second (agent choice; 0.5 = 3°/s looked too fast at
// 1000 × 575); it stops with the sweep.
const ROTATE_SPEED = 0.25;
// The amber band slab (570–615 nm, "Amber highlight" step 2) was replaced by two sensitivity blocks (human, AI_LOG
// "Species perceptions" step 11), which are now removed in favour of the species window below (AI_LOG
// "Story review" step 8; human: "remove the two boxes highlight").
const ease = t => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
// Species window (AI_LOG "Story review" steps 7–8; human: a toggle panel "for both human and fireflies, in both phil
// and cherry spring", "No auto window"; then "the animation should be inverse ... the spectrum should shrink from the
// full to the window for that species"): on Two measured nights a panel (bottom left) holds one button per species; a
// click shrinks the visible range from the full 280–840 nm to that species' half-max band on both halves over `move`
// (the other measured points dimmed to WINDOW.dim) and it stays; the same button again grows it back to full; the
// other button moves the window to its band (agent choices for the last two).
// Bands = each curve's samples ≥ 0.5 (data/derived/spectra/sensitivity_bands.json, pipeline/spectra/04_sensitivity_bands.py):
// human night, CIE scotopic V′(λ), 454–548 nm (`inferred`); firefly, P. pyralis female (Lall & Worthy 2000; provisional
// curve, no label), 530–600 nm. Edges half a grid step outside (pad). Button words, move time, dim level, pad: agent choices.
const WINDOW = { move: 2000, dim: 0.04, pad: 1,
  bands: [{ id: 'human', name: 'Human', lo: 454, hi: 548 }, { id: 'firefly', name: 'Firefly', lo: 530, hi: 600 }] };

// Draft particles.ts wavelengthToRgb.
function wavelengthToRgb(nm) {
  if (nm < 380) return [0.46, 0.18, 0.9];
  if (nm > 700) return [0.05, 0.72, 0.78];
  let r = 0, g = 0, b = 0;
  if (nm < 440) { r = -(nm - 440) / 60; b = 1; }
  else if (nm < 490) { g = (nm - 440) / 50; b = 1; }
  else if (nm < 510) { g = 1; b = -(nm - 510) / 20; }
  else if (nm < 580) { r = (nm - 510) / 70; g = 1; }
  else if (nm < 645) { r = 1; g = -(nm - 645) / 65; }
  else r = 1;
  const edge = nm < 420 ? 0.35 + (nm - 380) / 100 : nm > 645 ? 0.35 + (700 - nm) / 100 : 1;
  return [r * edge, g * edge, b * edge];
}

// Draft SpectralPoints.tsx physical layer, log scale only (uScaleMix 0, uGhostMix 0, uLayerOpacity 1).
// Added: uSplit / uSide keep each site on its side of the divider (gl_FragCoord.x, drawing-buffer pixels).
const vertexShader = `
  attribute vec3 aColor;
  attribute float aStrength;
  attribute float aQuality;
  attribute float aBand;
  attribute float aTime;
  uniform float uTimeFocus;
  uniform float uPointScale;
  uniform float uLayer;
  uniform float uWinLo;
  uniform float uWinHi;
  uniform float uWinDim;
  varying vec3 vColor;
  varying float vAlpha;
  varying float vBand;
  varying float vHalo;
  void main() {
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    float focusSignal = 1.0 - smoothstep(0.0, 0.022, abs(aTime - uTimeFocus));
    float focus = 1.30 * (0.24 + 0.76 * focusSignal);
    float qualityAlpha = aQuality > 1.5 ? 0.08 : (aQuality > 0.5 ? 0.18 : 1.0);
    float inWin = smoothstep(uWinLo - 0.15, uWinLo, position.x) * (1.0 - smoothstep(uWinHi, uWinHi + 0.15, position.x));
    vColor = aColor;
    vAlpha = max(0.02, aStrength * focus * qualityAlpha) * uLayer * mix(uWinDim, 1.0, inWin);
    vBand = aBand;
    vHalo = 0.0;
    float focusSize = 0.92 + 0.16 * focusSignal;
    gl_PointSize = clamp((1.2 + aStrength * 5.1) * focusSize * uPointScale * (15.0 / -mvPosition.z), 1.0, 8.5 * uPointScale);
    gl_Position = projectionMatrix * mvPosition;
  }`;
const fragmentShader = `
  precision highp float;
  uniform float uSplit;
  uniform float uSide;
  varying vec3 vColor;
  varying float vAlpha;
  varying float vBand;
  varying float vHalo;
  void main() {
    if ((gl_FragCoord.x - uSplit) * uSide > 0.0) discard;
    vec2 p = gl_PointCoord - vec2(0.5);
    float radius = length(p);
    float shapeAlpha;
    if (vBand < 0.5) {
      shapeAlpha = 1.0 - smoothstep(0.30, 0.50, radius);
    } else if (vBand < 1.5) {   // UV ring; draft receptor layer: plus a glow for 'halo' (UV) channels
      float ring = 1.0 - smoothstep(0.07, 0.15, abs(radius - 0.31));
      shapeAlpha = max(ring, (1.0 - smoothstep(0.24, 0.50, radius)) * vHalo * 0.45);
    } else {
      shapeAlpha = 1.0 - smoothstep(0.32, 0.50, abs(p.x) + abs(p.y));
    }
    if (shapeAlpha <= 0.01 || vAlpha <= 0.002) discard;
    gl_FragColor = vec4(vColor, vAlpha * shapeAlpha);
  }`;

// Draft receptor layer (SpectralPoints.tsx receptorVertexShader), log scale, contribution view (uContributionMix as
// uContrib) and interpretive cloud (uInterpretiveMix as uCloud); per-layer colour as a uniform; aResp = the receptor's
// response at the cell's wavelength, used for the 'halo' (UV) glow as in the draft (aMeta.w).
const receptorVertexShader = `
  attribute float aStrength;
  attribute float aContrib;
  attribute float aResp;
  attribute vec3 aCloud;
  attribute float aQuality;
  attribute float aBand;
  attribute float aTime;
  uniform float uTimeFocus;
  uniform float uPointScale;
  uniform float uContrib;
  uniform float uCloud;
  uniform float uLayer;
  uniform float uChannels;
  uniform float uHaloOn;
  uniform float uMotionTime;
  uniform float uGain;
  uniform vec3 uColor;
  varying vec3 vColor;
  varying float vAlpha;
  varying float vBand;
  varying float vHalo;
  void main() {
    vec3 physical = vec3(position.x, aStrength * 9.0, position.z);
    vec3 contribution = vec3(position.x, aContrib * 9.0, position.z);
    vec3 transformed = mix(mix(physical, contribution, uContrib), aCloud, uCloud);
    transformed.y += sin(uMotionTime * 0.72 + aCloud.x * 0.47 + aCloud.z * 0.31) * 0.12 * uCloud;
    vec4 mvPosition = modelViewMatrix * vec4(transformed, 1.0);
    float focusSignal = 1.0 - smoothstep(0.0, 0.022, abs(aTime - uTimeFocus));
    float focus = 1.30 * (0.22 + 0.78 * focusSignal);
    float strength = mix(aStrength, aContrib, uContrib);
    float qualityAlpha = aQuality > 1.5 ? 0.08 : (aQuality > 0.5 ? 0.18 : 1.0);
    vColor = uColor;
    vAlpha = strength * focus * qualityAlpha * uChannels * uLayer * uGain;
    vBand = aBand;
    vHalo = aResp * uHaloOn;
    float focusSize = 0.92 + 0.16 * focusSignal;
    gl_PointSize = clamp((1.15 + strength * 5.6 + vHalo * 1.4) * focusSize * sqrt(uGain) * uPointScale * (15.0 / -mvPosition.z), 1.0, 9.0 * uPointScale);
    gl_Position = projectionMatrix * mvPosition;
  }`;
// Draft receptors.ts RECEPTOR_CHANNEL_RGB (channel identifiers, not wavelength or perceived colours).
const CHANNEL_RGB = { r: [0.95, 0.39, 0.58], g: [0.20, 0.82, 0.74], b: [0.54, 0.48, 0.98], halo: [0.76, 0.46, 0.98],
  luma: [0.82, 0.87, 0.94], yellow: [0.95, 0.72, 0.21] };
const CLOUD_SEED = 37, SPECIES_MS = 1500;   // draft INTERPRETIVE_CLOUD_SEED; species cycle 1.5 s (human, round 7j)
// Species perceptions (story key `nights: 'pair'`): fixed divider in the middle (no sweep, no rotation, no cycling),
// same cloud as 'species'. Was Firefly | Human on Philadelphia only (human, AI_LOG "Species perceptions" steps 1–7);
// now firefly only (Photinus pyralis female response), Philadelphia (left) | Cherry Springs (right), each site's layer
// on its own half (human, AI_LOG "Story review" step 3: "firefly only, but the comparison is about philadelphia and
// cherry spring, keeping the existing visualization method").
const PAIR = ['big-dipper-firefly'];
// Display gain in 'pair' (human, AI_LOG "Story review" step 4: "both phil half and cherry spring half light dots needs
// to be brighter"): the same factor on both halves, alpha × PAIR_GAIN and point size × √PAIR_GAIN (alpha saturates at 1,
// so the brightest Philadelphia points gain less). Display only, not data. Eased like uLayer. Value: 2 (human, AI_LOG
// "Story review" step 5: "Lower to 2"; was 2.5, agent choice).
const PAIR_GAIN = 2;
// Female reply in each cloud (human, AI_LOG "Story review" step 5: put "the signal data visualization from female
// response" into the clouds, "Female reply only", "just use the same data you use in the 'female response' tab ...
// this species perceptions tab is just an interpretation, nothing needs to be very precise"). Interpretation, not
// data: spectral.js's Female response female cluster (dialogue(): 160 points in a 0.9 × 0.9 × 0.6 box, hash seed 23,
// sizes 1.4–3.0, flash colour FLASH; opacity 0.12 at rest, + 0.85 reply pulse at phase 0.6 of a 1.2 s cycle, width
// 0.07; firefly-tab gain 2.2 and size 1.3), drawn the same in both halves with additive blending over the cloud. It
// replies every cycle (Female response's dark share is 98.7 %; agent choice). Place: the middle of each half's part
// of the cloud (screen x in NDC ∓0.25 at the cloud centre's depth); REPLY_SCALE and REPLY_SIZE (world size and point
// size against this scene's farther camera): agent choices, by eye.
const REPLY = { n: 160, seed: 23, box: [0.9, 0.9, 0.6], colour: [0.72, 0.92, 0.25], rest: 0.12, pulse: 0.85, at: 0.6,
  width: 0.07, cycle: 1200, gain: 2.2, size: 1.3 };
const REPLY_SCALE = 2, REPLY_SIZE = 3, REPLY_X = [-0.25, 0.25];
const hash = (i, s) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };   // spectral.js
// spectral.js point shader (core + glow, gain without hue shift), plus the divider clip used here.
const replyVertexShader = `
  attribute float aSize;
  uniform float uScale;
  uniform float uOpacity;
  varying float vAlpha;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vAlpha = uOpacity;
    gl_PointSize = clamp(aSize * uScale * (15.0 / -mv.z), 1.0, 9.0 * uScale);
    gl_Position = projectionMatrix * mv;
  }`;
const replyFragmentShader = `
  precision highp float;
  uniform float uSplit;
  uniform float uSide;
  uniform float uGain;
  uniform vec3 uColor;
  varying float vAlpha;
  void main() {
    if ((gl_FragCoord.x - uSplit) * uSide > 0.0) discard;
    float r = length(gl_PointCoord - vec2(0.5));
    float core = 1.0 - smoothstep(0.06, 0.23, r);
    float glow = (1.0 - smoothstep(0.13, 0.5, r)) * 0.58;
    float a = max(core, glow) * vAlpha;
    if (a <= 0.003) discard;
    vec3 c = uColor * uGain;
    c /= max(1.0, max(c.r, max(c.g, c.b)));
    gl_FragColor = vec4(c, min(1.0, a * uGain));
  }`;
// Draft particles.ts hash01 and deterministicCloudPosition (stable place from the cell's identity and one seed).
function hash01(index, seed) {
  let v = (index + seed * 374761393) >>> 0;
  v = Math.imul(v ^ (v >>> 13), 1274126177);
  v = (v ^ (v >>> 16)) >>> 0;
  return v / 0xffffffff;
}
function cloudPosition(id, seed) {
  const angle = id * Math.PI * (3 - Math.sqrt(5)) + hash01(seed, 7) * Math.PI * 2;
  const vertical = hash01(id, seed + 11) * 2 - 1;
  const r0 = 1.8, r1 = 9.8, radius = Math.cbrt(r0 ** 3 + hash01(id, seed + 23) * (r1 ** 3 - r0 ** 3));
  const h = Math.sqrt(Math.max(0, 1 - vertical * vertical)) * radius;
  return [Math.cos(angle) * h, 4.25 + vertical * radius * 0.42, Math.sin(angle) * h * 0.72];
}

export function createTwoNights({ parent, onBeat = null }) {
  const canvas = Object.assign(document.createElement('canvas'), { id: 'nights-canvas', hidden: true });
  const css = new CSS3DRenderer();
  css.domElement.id = 'nights-labels';
  css.domElement.hidden = true;
  const divider = Object.assign(document.createElement('div'), { id: 'nights-divider', hidden: true });
  divider.innerHTML = '<div class="line"></div><div class="handle" aria-label="Drag to compare the two sites"></div>';
  // Site names at the screen edges, like the globe's year labels (.year).
  const names = SITES.map(s => Object.assign(document.createElement('div'),
    { className: `nights-site ${s.side > 0 ? 'left' : 'right'}`, textContent: s.name, hidden: true }));
  // Glows carried from the globe during the transition (same look as impacts.js drawSite at full glow).
  // Each carries its site name (as in the corner names), so the viewer sees which glow becomes which half.
  const glows = SITES.map(s => Object.assign(document.createElement('div'), { className: 'nights-glow', hidden: true,
    innerHTML: `<span>${s.name}</span>` }));
  // Species perceptions: the current species (name · scientific name, receptor channels in their colours).
  const speciesTag = Object.assign(document.createElement('div'), { id: 'nights-species', hidden: true });
  parent.append(canvas, css.domElement, divider, ...names, ...glows, speciesTag);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
  const pixelRatio = Math.min(window.devicePixelRatio, 1.5);   // draft Canvas dpr [1, 1.5]
  renderer.setPixelRatio(pixelRatio);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#030508');
  scene.fog = new THREE.Fog('#030508', 22, 52);
  const camera = new THREE.PerspectiveCamera(CAMERA.fov, 1, 0.05, 120);
  const controls = new OrbitControls(camera, canvas);
  Object.assign(controls, { enableDamping: true, dampingFactor: 0.08, minDistance: 13, maxDistance: 44,
    minPolarAngle: 0.35, maxPolarAngle: Math.PI / 2.05, autoRotateSpeed: ROTATE_SPEED });
  const resetCamera = () => {
    camera.position.set(...CAMERA.position);
    controls.target.set(...CAMERA.target);
    controls.update();
  };

  let split = 0.5, running = false, shown = false, t0 = 0, last = 0, timeIndex = 0, meta = null;
  // trans = { dir (1 open, −1 close), t, at: [() => glow | null] per site (left, right), from: [{x, y}], r, colours,
  // took (forward: the glows were taken over from the globe), onTakeover, onDone } or null.
  let trans = null;
  let sweep = null;   // { t0, once, from, to, ms, done } while the divider moves on its own, else null
  let beat = 0, beatTimer = 0;   // Two measured nights beat (see BEATS)
  // Species window: `sel` = the chosen band or null (full); `range` = the visible x range now; `win` = { from, to, t0 }
  // while the range moves (shrink to a band, move between bands, or grow back to full).
  const FULL = [-13, 13];
  let sel = null, range = FULL, win = null;
  const rangeOf = b => (b ? [xOf(b.lo - WINDOW.pad), xOf(b.hi + WINDOW.pad)] : FULL);
  function applyRange(r) {
    range = r;
    const full = r[0] <= FULL[0] && r[1] >= FULL[1];
    physicalMats.forEach(m => { m.uniforms.uWinLo.value = full ? -99 : r[0]; m.uniforms.uWinHi.value = full ? 99 : r[1]; });
  }
  function selectBand(b) {
    sel = b;
    win = { from: range, to: rangeOf(b), t0: performance.now() };
    renderPanel();
  }
  function stopWindow() { sel = null; win = null; applyRange(FULL); renderPanel(); }   // reset at once (leaving)
  function stepWindow(now) {
    const k = ease(Math.min(1, (now - win.t0) / WINDOW.move));
    applyRange([0, 1].map(n => win.from[n] + (win.to[n] - win.from[n]) * k));
    if (k >= 1) win = null;
  }
  // Panel: one button per band; the chosen one is pressed. Shown only on Two measured nights ('spectra', no transition).
  const panel = Object.assign(document.createElement('nav'), { id: 'nights-window', hidden: true });
  panel.setAttribute('aria-label', 'Show one species’ band');
  // "Full" first: back to the whole measured range (human: "a 'full' icon that allow users to go back to the original
  // spectrum", in front of Human and Firefly).
  panel.innerHTML = '<button data-band="full" aria-pressed="true">Full</button>' +
    WINDOW.bands.map(b => `<button data-band="${b.id}" aria-pressed="false">${b.name}</button>`).join('');
  panel.addEventListener('click', e => {
    const id = e.target.closest('button')?.dataset.band;
    if (id === 'full') { if (sel) selectBand(null); return; }
    const b = WINDOW.bands.find(x => x.id === id);
    if (b) selectBand(b === sel ? null : b);   // same button again: also back to the full spectrum
  });
  parent.append(panel);
  function renderPanel() {
    panel.querySelectorAll('button').forEach(el => el.setAttribute('aria-pressed', String((sel?.id ?? 'full') === el.dataset.band)));
  }
  const edge = side => (side < 0 ? EDGE_PX / canvas.clientWidth : 1 - EDGE_PX / canvas.clientWidth);
  function moveTo(to, ms, done = null) { sweep = { t0: performance.now(), once: true, from: split, to, ms, done }; }
  // Beat k (BEATS): moves the divider / window there from wherever they are; its line follows its cue.
  function goBeat(k) {
    clearTimeout(beatTimer);
    beat = k;
    if (k <= OPEN) { if (sel) selectBand(null); moveTo(edge(-1), ONCE.toLeft); onBeat?.(k); return; }
    if (k === OPEN + 1) {
      if (sel) selectBand(null);
      if (split >= edge(1) - 1e-3) { sweep = null; onBeat?.(k); return; }   // already there (back from the next beat)
      moveTo(edge(1), ONCE.across, () => onBeat?.(k));
      return;
    }
    // beats 2–3: the divider first finishes at the right edge (the rest of a running sweep, or from the middle when
    // arriving back from Species perceptions, in ONCE.toLeft), then the window narrows (unless it already has), then
    // the beat's line.
    const narrow = () => {
      if (beat < OPEN + 2) return;
      const done = () => { if (beat >= OPEN + 2 && shown && mode === 'spectra') onBeat?.(beat); };
      if (sel?.id === 'firefly' && !win) { done(); return; }
      selectBand(WINDOW.bands.find(b => b.id === 'firefly'));
      beatTimer = setTimeout(done, WINDOW.move);
    };
    if (split < edge(1) - 1e-3) moveTo(edge(1), ONCE.toLeft, narrow); else { sweep = null; narrow(); }
  }
  function startSweep(now) {
    if (mode === 'pair') { sweep = null; divider.classList.remove('parked'); return; }   // static divider
    if (mode !== 'species') { goBeat(0); return; }   // Two measured nights: beats
    // The loop starts at the divider's current place (phase from split = 0.5 − SWEEP_HALF · sin).
    const phase = Math.asin(Math.min(1, Math.max(-1, (0.5 - split) / SWEEP_HALF)));
    sweep = { t0: now - (phase / (2 * Math.PI)) * SWEEP_MS, once: false, from: split };
  }
  function sweepSplit(now) {
    const e = now - sweep.t0;
    if (!sweep.once) return 0.5 - SWEEP_HALF * Math.sin(2 * Math.PI * e / SWEEP_MS);
    const k = Math.min(1, e / sweep.ms), to = sweep.to, done = sweep.done;
    if (k >= 1) { sweep = null; done?.(); return to; }
    return sweep.from + (to - sweep.from) * ease(k);
  }
  const materials = [];
  // Species perceptions: mode 'spectra' | 'species'; mix = eased 0 → 1 towards the species cloud.
  let mode = 'spectra', mix = 0, species = [], speciesIndex = -1, speciesT0 = 0;
  const physicalMats = [], frameGroup = new THREE.Group();
  const replies = [];   // female reply clusters, one per site (left, right)
  scene.add(frameGroup);

  // ── axis frame (draft SceneCanvas.tsx ScientificFrame, log scale) ─────────
  function lines(segments, color, opacity = 1) {
    const g = new THREE.BufferGeometry().setFromPoints(segments.flat().map(p => new THREE.Vector3(...p)));
    return new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity }));
  }
  function label(text, position) {
    const el = Object.assign(document.createElement('span'), { className: 'axis-label', textContent: text });
    const o = new CSS3DObject(el);
    o.position.set(...position);
    o.scale.setScalar(10 / 400);   // drei <Html transform distanceFactor={10}>: 1 CSS px = 0.025 world units
    scene.add(o);
    return o;
  }
  const xOf = nm => -12 + ((nm - 280) / 560) * 24;
  function buildFrame() {
    const grid = [];
    for (const x of [-12, -6, 0, 6, 12]) grid.push([[x, 0, -8], [x, 0, 8]]);
    for (const z of [-8, -4, 0, 4, 8]) grid.push([[-12, 0, z], [12, 0, z]]);
    for (const y of [2.25, 4.5, 6.75, 9]) grid.push([[-12, y, 8], [12, y, 8]]);
    frameGroup.add(lines(grid, '#242d39', 0.82));
    frameGroup.add(lines([[[-12, 0, 8], [12, 0, 8]], [[-12, 0, 8], [-12, 9, 8]], [[-12, 0, -8], [-12, 0, 8]]], '#465364'));
    frameGroup.add(lines([380, 700].map(nm => [[xOf(nm), 0, -8], [xOf(nm), 9, -8]]), '#566273', 0.55));
    // The draft's "current spectrum" plane, outline and label removed (human, AI_LOG Firefly tabs review round 7g);
    // the focused spectrum is still highlighted in the points (uTimeFocus).
    for (const nm of [280, 380, 500, 620, 700, 840]) label(String(nm), [xOf(nm), -0.12, 8.2]);
    for (const tick of [0, 0.25, 0.5, 0.75, 1]) {
      const exponent = meta.floor + tick * (meta.ceil - meta.floor);
      label(`10^${exponent.toFixed(1)}`, [-12.55, tick * 9, 8]);
    }
    label('WAVELENGTH · 280–840 NM', [0, -0.35, 8.5]);
    // Unit added to the draft's label (human request, Firefly narrative round 3f); unit case kept (m = metre).
    label('HEIGHT · LOG₁₀ IRRADIANCE · W m⁻² nm⁻¹', [-13.45, 4.5, 8]);
    label('TIME / SPECTRUM INDEX', [-13, 0, 0]);
    label('UV', [-9.85, 0.2, -8]);
    label('VISIBLE', [1.15, 0.2, -8]);
    label('NIR', [9.1, 0.2, -8]);
  }

  // ── female reply (Species perceptions, 'pair') ──────────────────────────
  function buildReplies() {
    const [bx, by, bz] = REPLY.box, pos = new Float32Array(REPLY.n * 3), size = new Float32Array(REPLY.n);
    for (let i = 0; i < REPLY.n; i++) {
      pos.set([(hash(i, REPLY.seed) - 0.5) * bx, (hash(i, REPLY.seed + 1) - 0.5) * by, (hash(i, REPLY.seed + 2) - 0.5) * bz], i * 3);
      size[i] = 1.4 + hash(i, REPLY.seed + 3) * 1.6;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aSize', new THREE.BufferAttribute(size, 1));
    SITES.forEach(site => {
      const m = new THREE.ShaderMaterial({ vertexShader: replyVertexShader, fragmentShader: replyFragmentShader,
        transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms: {
          uScale: { value: pixelRatio * REPLY.size * REPLY_SIZE }, uOpacity: { value: 0 }, uGain: { value: REPLY.gain },
          uColor: { value: new THREE.Color(...REPLY.colour) }, uSplit: { value: 0 }, uSide: { value: site.side } } });
      const p = new THREE.Points(g, m);
      p.frustumCulled = false;
      p.visible = false;
      p.scale.setScalar(REPLY_SCALE);
      scene.add(p);
      replies.push(p);
    });
  }

  // ── points (draft SpectralPoints.tsx geometry) ──────────────────────────
  let cloud = null, zeros = null;
  function buildSite(site, doc) {
    const wl = meta.wavelengths, T = doc.irradiance.length, W = wl.length, n = T * W;
    const pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    const strength = new Float32Array(n), quality = new Float32Array(n), band = new Float32Array(n), time = new Float32Array(n);
    let i = 0;
    for (let t = 0; t < T; t++) {
      for (let w = 0; w < W; w++, i++) {
        const v = doc.irradiance[t][w];
        const s = v == null || !(v > 0) ? 0
          : Math.min(1, Math.max(0, (Math.log10(v) - meta.floor) / (meta.ceil - meta.floor)));
        pos.set([-12 + (w / Math.max(1, W - 1)) * 24, s * 9, -8 + (t / Math.max(1, T - 1)) * 16], i * 3);
        col.set(wavelengthToRgb(wl[w]), i * 3);
        strength[i] = s;
        quality[i] = v == null ? 2 : v === 0 ? 1 : 0;
        band[i] = wl[w] < 380 ? 1 : wl[w] > 700 ? 2 : 0;
        time[i] = t / Math.max(1, T - 1);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aColor', new THREE.BufferAttribute(col, 3));
    g.setAttribute('aStrength', new THREE.BufferAttribute(strength, 1));
    g.setAttribute('aQuality', new THREE.BufferAttribute(quality, 1));
    g.setAttribute('aBand', new THREE.BufferAttribute(band, 1));
    g.setAttribute('aTime', new THREE.BufferAttribute(time, 1));
    const m = new THREE.ShaderMaterial({ vertexShader, fragmentShader, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, uniforms: { uTimeFocus: { value: 0 }, uPointScale: { value: pixelRatio },
        uSplit: { value: 0 }, uSide: { value: site.side }, uLayer: { value: 1 },
        uWinLo: { value: -99 }, uWinHi: { value: 99 }, uWinDim: { value: WINDOW.dim } } });
    const p = new THREE.Points(g, m);
    p.frustumCulled = false;
    scene.add(p);
    materials.push(m);
    physicalMats.push(m);
    // Species layers for this site: one Points per receptor, sharing this site's position / quality / band / time
    // attributes and one cloud-position attribute (same for both sites: cell identity t × W + w, seed 37).
    cloud ??= new THREE.BufferAttribute(Float32Array.from({ length: n * 3 }, (_, j) => cloudPosition(Math.floor(j / 3), CLOUD_SEED)[j % 3]), 3);
    zeros ??= new THREE.BufferAttribute(new Float32Array(n), 1);
    const norm = v => (!(v > 0) ? 0 : Math.min(1, Math.max(0, (Math.log10(v) - meta.floor) / (meta.ceil - meta.floor))));
    species.forEach(sp => sp.receptors.forEach((rc, ri) => {
      const halo = rc.display_channel === 'halo', contrib = new Float32Array(n), resp = halo ? new Float32Array(n) : null;
      for (let t = 0, k = 0; t < T; t++) for (let w = 0; w < W; w++, k++) {
        const v = doc.irradiance[t][w], r = rc.response[w];
        contrib[k] = v == null || !(r > 0) ? 0 : norm(v * r);   // draft receptorContribution + normalizedSpectralValue
        if (halo) resp[k] = r;
      }
      const rg = new THREE.BufferGeometry();
      ['position', 'aStrength', 'aQuality', 'aBand', 'aTime'].forEach(a => rg.setAttribute(a, g.getAttribute(a)));
      rg.setAttribute('aCloud', cloud);
      rg.setAttribute('aContrib', new THREE.BufferAttribute(contrib, 1));
      rg.setAttribute('aResp', halo ? new THREE.BufferAttribute(resp, 1) : zeros);
      const rm = new THREE.ShaderMaterial({ vertexShader: receptorVertexShader, fragmentShader, transparent: true,
        depthWrite: false, blending: THREE.AdditiveBlending, uniforms: { uTimeFocus: { value: 0 },
          uPointScale: { value: pixelRatio }, uSplit: { value: 0 }, uSide: { value: site.side }, uContrib: { value: 0 },
          uCloud: { value: 0 }, uLayer: { value: 0 }, uChannels: { value: 1 / Math.sqrt(sp.receptors.length) },
          uHaloOn: { value: halo ? 1 : 0 }, uMotionTime: { value: 0 }, uGain: { value: 1 },
          uColor: { value: new THREE.Color(...CHANNEL_RGB[rc.display_channel]) } } });
      const rp = new THREE.Points(rg, rm);
      rp.frustumCulled = false;
      rp.visible = false;
      rp.userData.site = site;
      scene.add(rp);
      materials.push(rm);
      sp.layers.push(rp);
    }));
    return T;
  }

  let count = 240;
  let loaded = null;
  const load = () => loaded ??= Promise.all(['spectra_meta', 'species_curves', ...SITES.map(s => s.id)].map(f =>
    fetch(`/spectra/${f}.json`).then(r => r.json()))).then(([m, sc, ...docs]) => {
    meta = { wavelengths: m.wavelength_nm, floor: m.display_limits_log10.floor, ceil: m.display_limits_log10.ceil };
    if (sc.wavelength_nm.length !== meta.wavelengths.length) throw new Error('species_curves grid differs from spectra');
    buildFrame();
    buildReplies();
    species = sc.species.map(sp => ({ ...sp, layers: [] }));
    count = Math.min(...SITES.map((s, k) => buildSite(s, docs[k])));
  });

  // ── divider (look of the globe's #swipe) ─────────────────────────────────
  function placeDivider() {
    divider.style.left = `${split * canvas.clientWidth}px`;
    materials.forEach(m => { m.uniforms.uSplit.value = split * canvas.clientWidth * pixelRatio; });
    replies.forEach(p => { p.material.uniforms.uSplit.value = split * canvas.clientWidth * pixelRatio; });
    placeNames();
  }
  // Names straddle the top of the divider, 14 px either side (human, AI_LOG "Species perceptions" step 12: "should
  // straddle the divider line"); 'species' (Explore draft) keeps the CSS top-centre place. Agent choices: a name is
  // hidden while its half is too narrow for it (16 px screen margin), and stays clear of the mute button (right edge
  // at most W − 60 px), so at the end of the sweep "Philadelphia" sits just left of the button.
  const GAP = 14, MARGIN = 16, MUTE_CLEAR = 60;
  function placeNames() {
    const W = canvas.clientWidth, x = split * W;
    names.forEach((n, k) => {
      if (mode === 'species') { n.style.left = n.style.right = n.style.visibility = ''; return; }
      const w = n.offsetWidth;
      if (k === 0) {   // left of the divider
        n.style.right = `${Math.max(W - x + GAP, MUTE_CLEAR)}px`; n.style.left = 'auto';
        n.style.visibility = x - GAP - w < MARGIN ? 'hidden' : '';
      } else {
        n.style.left = `${x + GAP}px`; n.style.right = 'auto';
        n.style.visibility = x + GAP + w > W - MUTE_CLEAR ? 'hidden' : '';
      }
    });
  }
  // Cloud centre (draft cloud, y 4.25) for placing the female replies on screen.
  const cloudCentre = new THREE.Vector3(0, 4.25, 0), target = new THREE.Vector3();
  // Female reply: fades in with the cloud in 'pair' (second half of mix), out on leaving; pulses as in Female response.
  let replyK = 0;
  function placeReplies(now, delta) {
    const goal = mode === 'pair' ? Math.max(0, mix * 2 - 1) : 0;
    replyK += (goal - replyK) * (1 - Math.exp(-delta / 0.15));
    const ph = ((now - t0) / REPLY.cycle) % 1;
    const o = (REPLY.rest + REPLY.pulse * Math.exp(-(((ph - REPLY.at) / REPLY.width) ** 2))) * replyK;
    replies.forEach((p, k) => {
      target.copy(cloudCentre).project(camera);
      target.x = REPLY_X[k];
      target.unproject(camera);
      p.position.copy(target);
      p.material.uniforms.uOpacity.value = o;
      p.visible = o > 0.002;
    });
  }
  divider.querySelector('.handle').addEventListener('pointerdown', e => {
    if (sweep?.once && mode === 'spectra') onBeat?.(beat);   // the viewer takes over: show the beat's line now
    sweep = null;
    e.target.setPointerCapture(e.pointerId);
    const move = ev => { split = Math.min(1, Math.max(0, ev.clientX / window.innerWidth)); placeDivider(); };
    const up = () => { e.target.removeEventListener('pointermove', move); e.target.removeEventListener('pointerup', up); };
    e.target.addEventListener('pointermove', move);
    e.target.addEventListener('pointerup', up);
  });

  // ── transition (round 7f) ────────────────────────────────────────────────
  const centre = k => ({ x: (k ? (1 + split) / 2 : split / 2) * window.innerWidth, y: window.innerHeight / 2 });
  // Each half shows only inside a circle of radius rk around its centre; the two mask layers are kept to their halves.
  function mask(rs) {
    const W = window.innerWidth, sx = split * W, soft = 60;
    const m = rs.map((r, k) => { const c = centre(k);
      return r <= 0 ? 'linear-gradient(transparent, transparent)'
        : `radial-gradient(circle at ${c.x - (k ? sx : 0)}px ${c.y}px, #000 ${r}px, transparent ${r + soft}px)`; }).join(', ');
    for (const el of [canvas, css.domElement]) Object.assign(el.style, { maskImage: m, webkitMaskImage: m,
      maskSize: `${sx}px 100%, ${W - sx}px 100%`, webkitMaskSize: `${sx}px 100%, ${W - sx}px 100%`,
      maskPosition: `0 0, ${sx}px 0`, webkitMaskPosition: `0 0, ${sx}px 0`, maskRepeat: 'no-repeat', webkitMaskRepeat: 'no-repeat' });
  }
  function unmask() {
    for (const el of [canvas, css.domElement]) ['maskImage', 'webkitMaskImage', 'maskSize', 'webkitMaskSize', 'maskPosition',
      'webkitMaskPosition', 'maskRepeat', 'webkitMaskRepeat'].forEach(k => { el.style[k] = ''; });
  }
  function glowAt(k, p, r, o) {
    const g = glows[k];
    g.hidden = o <= 0.001;
    g.firstChild.style.top = `${1.7 * r}px`;
    Object.assign(g.style, { left: `${p.x - r}px`, top: `${p.y - r}px`, width: `${2 * r}px`, height: `${2 * r}px`, opacity: String(o),
      background: `radial-gradient(circle closest-side, #fffbe6 0%, ${trans.colours[k]} 18%, rgba(0,0,0,0) 100%)` });
  }
  const chrome = on => { divider.hidden = !on; names.forEach(n => { n.hidden = !on; }); if (on) placeNames(); };
  function endTrans() {
    trans = null; unmask(); glows.forEach(g => { g.hidden = true; });
  }
  // Returns false when the view should stop (closing finished).
  function moveTrans(now) {
    const W = window.innerWidth, H = window.innerHeight, full = Math.hypot(W / 4, H / 2) + 20, e = now - trans.t;
    const lerp = (a, b, k) => ({ x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k });
    if (trans.dir > 0) {
      if (e < T_WAIT) { mask([0, 0]); return true; }   // the globe's glows grow (impacts.js)
      if (!trans.took) {   // take the glows over from the globe
        trans.took = true;
        const g = trans.at.map((f, k) => f?.() ?? { ...centre(k), r: trans.r });
        trans.from = g.map(v => ({ x: v.x, y: v.y }));
        trans.r = g[0].r ?? trans.r;
        trans.onTakeover?.();
      }
      const ks = ease(Math.min(1, (e - T_WAIT) / T_SLIDE)), ko = ease(Math.min(1, Math.max(0, (e - T_WAIT - T_SLIDE) / T_OPEN)));
      trans.from.forEach((p, k) => glowAt(k, lerp(p, centre(k), ks), trans.r, 1 - ko));
      mask([0, 1].map(() => ko > 0 ? trans.r * 0.6 + (full - trans.r * 0.6) * ko : 0));
      if (ko >= 1) { const t = trans; endTrans(); chrome(true); startSweep(now); t.onDone?.(); }
      return true;
    }
    const kc = ease(Math.min(1, e / T_CLOSE)), ks = ease(Math.min(1, Math.max(0, (e - T_CLOSE) / T_SLIDE)));
    mask([0, 1].map(() => trans.r * 0.6 + (full - trans.r * 0.6) * (1 - kc)));
    trans.at.forEach((f, k) => { const g = f?.(); glowAt(k, g ? lerp(centre(k), g, ks) : centre(k), trans.r, g ? kc : kc * (1 - ks)); });
    if (ks < 1) return true;
    const t = trans;
    t.onTakeover?.();
    endTrans();
    hideNow();
    t.onDone?.();
    return false;
  }
  function hideNow() {
    running = false;
    canvas.hidden = css.domElement.hidden = speciesTag.hidden = true;
    chrome(false);
  }

  // ── species perceptions (round 7j) ───────────────────────────────────────
  // mix eases towards the mode (time constant 0.6 s): first half = receptor layers rise from the measured height to
  // their contribution height, second half = into the cloud; the measured points, axes and labels fade with it.
  // Species: one every SPECIES_MS from speciesT0, crossfading over ~0.15 s. Timings: agent choices.
  function speciesFrame(now, delta) {
    const goal = mode === 'spectra' ? 0 : 1;
    mix += (goal - mix) * (1 - Math.exp(-delta / 0.6));
    if (Math.abs(mix - goal) < 1e-3) mix = goal;
    physicalMats.forEach(m => { m.uniforms.uLayer.value = 1 - mix; });
    frameGroup.visible = mix < 0.999;
    frameGroup.children.forEach(l => { l.material.transparent = true; l.material.opacity = (l.userData.o ??= l.material.opacity) * (1 - mix); });
    css.domElement.style.opacity = String(1 - mix);
    if (mode === 'species') {
      const i = Math.floor((now - speciesT0) / SPECIES_MS) % species.length;
      if (i !== speciesIndex) { speciesIndex = i; renderSpecies(); }
    }
    speciesTag.hidden = mode !== 'species' || Boolean(trans);
    const kc = 1 - Math.exp(-delta / 0.15);
    species.forEach((sp, i) => sp.layers.forEach(p => {
      const u = p.material.uniforms;
      const target = (mode === 'pair' ? PAIR.includes(sp.id) : i === speciesIndex) ? mix : 0;
      u.uLayer.value += (target - u.uLayer.value) * kc;
      u.uGain.value += ((mode === 'pair' ? PAIR_GAIN : 1) - u.uGain.value) * kc;
      u.uContrib.value = Math.min(1, mix * 2);
      u.uCloud.value = Math.max(0, mix * 2 - 1);
      u.uMotionTime.value = now / 1000;
      p.visible = u.uLayer.value > 0.002;
    }));
  }
  function renderSpecies() {
    const sp = species[speciesIndex];
    const rgb = c => `rgb(${CHANNEL_RGB[c].map(v => Math.round(v * 255)).join(',')})`;
    speciesTag.innerHTML = `<div class="name">${sp.name} · <i>${sp.scientific_name}</i></div><div class="channels">` +
      sp.receptors.map(r => `<span style="color:${rgb(r.display_channel)}">${r.name}</span>`).join('') + '</div>';
  }

  // ── loop ─────────────────────────────────────────────────────────────────
  function frame(now) {
    if (!running) return;
    if (trans && !moveTrans(now)) return;
    const delta = Math.min(0.1, (now - last) / 1000);
    last = now;
    timeIndex = Math.floor((now - t0) / (SCAN_MS / count)) % count;
    const focus = timeIndex / Math.max(1, count - 1), speed = Math.min(1, delta * 3.8);
    materials.forEach(m => { m.uniforms.uTimeFocus.value += (focus - m.uniforms.uTimeFocus.value) * speed; });
    if (win && !trans) stepWindow(now);
    panel.hidden = !shown || mode !== 'spectra' || Boolean(trans) || mix > 0.01;
    if (sweep && !trans) { split = sweepSplit(now); placeDivider(); }
    else if (mode === 'pair' && !trans && split !== 0.5) {   // pair: the divider eases to the middle and stays
      split += (0.5 - split) * Math.min(1, delta * 4);
      if (Math.abs(split - 0.5) < 1e-4) split = 0.5;
      placeDivider();
    }
    speciesFrame(now, delta);
    controls.autoRotate = Boolean(sweep && !trans);
    controls.update(delta);
    placeReplies(now, delta);
    renderer.render(scene, camera);
    css.render(scene, camera);
    requestAnimationFrame(frame);
  }

  function resize() {
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    css.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    placeDivider();
  }
  window.addEventListener('resize', resize);

  return {
    // Two measured nights beats (main.js: ← → and the nav arrows): d = ±1. Returns false past either end, during a
    // transition or in another mode, so the story moves on as usual.
    beat(d) {
      if (!shown || !running || trans || mode !== 'spectra' || mix > 0.01) return false;
      const k = beat + d;
      if (k < 0 || k >= BEATS) return false;
      goBeat(k);
      return true;
    },
    // on = the story step's `nights` key: true (Two measured nights), 'species' (cycling species) or 'pair' (firefly, both sites). Entering
    // resets the camera, the divider and the scan; switching between the two while shown keeps them and morphs.
    // Transition (round 7f): from = [() => glow, () => glow] (impacts.siteGlow, left then right site): open out of
    // those glows; to = the same, on leaving: close into them. onTakeover: the glows pass from the globe to this view
    // (forward) or back (reverse); onDone: finished.
    async set(on, { from = null, to = null, onTakeover = null, onDone = null } = {}) {
      const colours = f => f.map(g => g?.()?.colour ?? '#ffffff');
      const closing = trans?.dir < 0;
      if (trans) endTrans();
      shown = Boolean(on);
      const want = on === 'species' || on === 'pair' ? on : 'spectra';
      const switched = shown && want !== mode;
      if (switched) { mode = want; speciesT0 = performance.now(); speciesIndex = -1; }
      if (shown) {   // handle hidden in 'pair' (fixed divider); names are the sites in every mode
        divider.querySelector('.handle').style.display = mode === 'pair' ? 'none' : '';
      }
      if (!shown) {
        sweep = null; clearTimeout(beatTimer); stopWindow(); panel.hidden = true;
        if (to && running) {
          trans = { dir: -1, t: performance.now(), at: to, r: 0.1 * Math.min(window.innerWidth, window.innerHeight) + 7,
            colours: colours(to), onTakeover, onDone };
          trans.r = to[0]?.()?.r ?? trans.r;
          chrome(false);
          return;
        }
        hideNow();
        return;
      }
      await load();
      if (!shown) return;   // left the step while loading
      if (running) {   // already showing: back again during a closing transition, or Two measured nights ↔ Species
        if (closing) { unmask(); chrome(true); }
        // each mode its own sweep (beats / loop); back from Species perceptions to Two measured nights: the last beat
        // (the Philadelphia line while the divider and window move; after story.js has drawn the step's text)
        if (switched && mode === 'spectra' && !closing) {
          sweep = null; goBeat(BEATS - 1);
          setTimeout(() => { if (beat === BEATS - 1) onBeat?.(OPEN + 1); }, 0);
          return;
        }
        if (closing || switched) { stopWindow(); startSweep(performance.now()); }
        return;
      }
      mix = mode === 'spectra' ? 0 : 1;   // a fresh entry starts in its own mode, first species first
      speciesT0 = performance.now(); speciesIndex = -1;
      canvas.hidden = css.domElement.hidden = false;
      chrome(!from);
      split = 0.5;
      if (from) {
        trans = { dir: 1, t: performance.now(), at: from, r: 0.1 * Math.min(window.innerWidth, window.innerHeight) + 7,
          colours: colours(from), took: false, onTakeover, onDone };
        mask([0, 0]);
      } else startSweep(performance.now());
      resize();
      resetCamera();
      materials.forEach(m => { m.uniforms.uTimeFocus.value = 0; });
      t0 = last = performance.now();
      running = true;
      requestAnimationFrame(frame);
    },
  };
}
