import * as THREE from 'three';
import Globe from 'globe.gl';
import { TileLayer } from './tileLayer.js';
import { startStory } from './story.js';
import { createIntroScene, createDarkScene, INTRO_MODE } from './introScene.js';
import { createImpacts } from './impacts.js';
import { createSpectral } from './spectral.js';
import { createTwoNights } from './twoNights.js';
import { story } from '../content/story.js';   // `ladder` no longer passed: ladder removed (human, AI_LOG Impacts firefly-first step 2)

const TILE_BASE = import.meta.env.VITE_TILE_BASE || '/tiles/v1/';
// Display choice for "no data" (-1.5 pixels, human decision N2). Not a measured value.
const NO_DATA_COLOR = '#ff00ff';

const el = document.getElementById('globe');
const globe = new Globe(el, { animateIn: false })
  .backgroundColor('#000000')
  .showAtmosphere(false)        // no atmosphere glow (would be a filler colour)
  .globeMaterial(new THREE.MeshBasicMaterial({ color: 0x000000 }));  // plain black base

const index = await (await fetch(`${TILE_BASE}tiles.json`)).json();
const layer = new TileLayer({ baseUrl: TILE_BASE, index, radius: globe.getGlobeRadius(),
  noDataColor: NO_DATA_COLOR });
globe.scene().add(layer.group);
if (import.meta.env.DEV) window.globe = globe;  // dev-only handle for inspection
if (import.meta.env.DEV) window.tileLayer = layer;  // dev-only: PROTOTYPE colour-mode switching (human 2026-10-04)

// Swipe divider: one uniform, per-pixel year choice in the shader.
const swipe = document.getElementById('swipe');
let swipeFrac = 0.5;
function placeSwipe() {
  const x = swipeFrac * window.innerWidth;
  swipe.style.left = `${x}px`;
  layer.setSwipe(x * globe.renderer().getPixelRatio());
}
swipe.querySelector('.handle').addEventListener('pointerdown', e => {
  e.target.setPointerCapture(e.pointerId);
  const move = ev => { swipeFrac = Math.min(1, Math.max(0, ev.clientX / window.innerWidth)); placeSwipe(); };
  const up = () => { e.target.removeEventListener('pointermove', move); e.target.removeEventListener('pointerup', up); };
  e.target.addEventListener('pointermove', move);
  e.target.addEventListener('pointerup', up);
});

function resize() {
  globe.width(window.innerWidth).height(window.innerHeight);
  placeSwipe();
}
window.addEventListener('resize', resize);
resize();

// Tile selection on camera change (throttled to animation frames).
let pending = false;
function refresh() {
  if (pending) return;
  pending = true;
  requestAnimationFrame(() => {
    pending = false;
    const cam = globe.camera();
    cam.updateMatrixWorld();
    layer.update(cam, window.innerHeight * globe.renderer().getPixelRatio());
  });
}
globe.controls().addEventListener('change', refresh);
refresh();

// Legend: labels only, no interpretation. Shown as a pop-up behind the (i) button.
const info = document.getElementById('info'), legend = document.getElementById('legend');
const toggleLegend = show => { legend.hidden = !show; info.setAttribute('aria-expanded', String(show)); };
info.addEventListener('click', () => toggleLegend(legend.hidden));
window.addEventListener('keydown', e => { if (e.key === 'Escape') toggleLegend(false); });
const c = index.curve;
const ticks = c.reference_grey.filter(r => [0.5, 1, 2, 5, 10, 50].includes(r.radiance));
const stops = c.reference_grey.map(r => `rgb(${r.grey},${r.grey},${r.grey}) ${(r.grey / 255 * 100).toFixed(1)}%`);
document.getElementById('legend').innerHTML = `
  <b>Radiance (nW/cm²/sr) → grey</b>
  <div class="ramp" style="background:linear-gradient(to right, #000 0%, ${stops.join(',')})">
    ${ticks.map(r => `<span style="left:${(r.grey / 255 * 100).toFixed(1)}%">${r.radiance}</span>`).join('')}
  </div>
  <div><span class="swatch" style="background:${NO_DATA_COLOR}"></span>No data (−1.5): display colour, not a value</div>
  <p>Display curve: histogram equalisation of positive pixels, both years pooled; top = P${c.top_percentile}
  = ${c.top.toFixed(1)} nW/cm²/sr (white above). Same curve for both years. Black = 0 or background.</p>
  <p>Data: EOG VIIRS DNB annual VNL V2, average_masked; 2015 (v2.1), 2025 (v2.2).
  Elvidge et al. 2021, doi:10.3390/rs13050922.</p>`;

// Left panel: "Light" (the story, with its step list) and "Impacts" (2025 tiles only, no divider).
// Human decisions: two super-categories (AI_LOG Story UX step 12), S2 labels + step list (Impacts step 3).
const modes = document.getElementById('modes');
// Story Part 1 steps are listed under "Light", Part 2 under "Impacts" (human request, AI_LOG Impacts step 32).
const partOf = s => s.part ?? 1;
const stepLabel = s => s.label ?? s.title ?? s.id.charAt(0).toUpperCase() + s.id.slice(1);
modes.querySelectorAll('.steps').forEach(list => {
  list.innerHTML = story.map((s, i) => partOf(s) === Number(list.dataset.part)
    ? `<li><button data-step="${i}">${stepLabel(s)}</button></li>` : '').join('');
});
// Heading highlight: Impacts while browsing or on a Part 2 story step, Explore on Part 3 (human request, Firefly
// transition task step 4), otherwise Light.
// Only the current section's step list is open; the others collapse (human request, AI_LOG Impacts step 33).
const PART_OF_MODE = { light: 1, impacts: 2, explore: 3 };
const markHeaders = () => {
  const part = mode === 'impacts' ? 2 : partOf(story[storyIndex]);
  modes.querySelectorAll('.mode').forEach(b => {
    const on = PART_OF_MODE[b.dataset.mode] === part;
    b.setAttribute('aria-pressed', String(on));
    b.setAttribute('aria-expanded', String(on));
  });
  modes.querySelectorAll('.steps').forEach(l => l.classList.toggle('collapsed', Number(l.dataset.part) !== part));
};
const markStep = i => modes.querySelectorAll('.steps button').forEach(b =>
  b.classList.toggle('current', Number(b.dataset.step) === i));

// Impacts: study dots on a canvas overlay + study card (app/src/impacts.js).
// onDoor: clicking a chart step's door record moves the story to the spectral step with that door.
const impacts = createImpacts({ globe, globeEl: el, card: document.getElementById('study'), legend,
  onDoor: id => storyCtl.go(story.findIndex(s => s.spectral?.door === id)) });
// Spectral chapters (app/src/spectral.js): a 3D view over the globe on steps with a `spectral` key
// (human decisions, AI_LOG Impacts steps 74–75).
// onLine: a Female response beat swaps the big text line (story.js `reveal`; AI_LOG Firefly flow step 14).
const showLine = k => document.querySelectorAll('#fact .line').forEach((p, n) => p.classList.toggle('on', n === k));
const spectral = createSpectral({ parent: document.body, onLine: showLine });
// Two measured nights (app/src/twoNights.js): City vs Rural night spectra behind a divider, on steps with
// `nights: true` (human decision, AI_LOG Firefly narrative round 3c).
const nights = createTwoNights({ parent: document.body,
  // onBeat: the Two measured nights big text shows line k of its beats (AI_LOG Firefly flow step 4).
  onBeat: k => document.querySelectorAll('#fact .line').forEach((p, n) => p.classList.toggle('on', n === k)) });

// Firefly guide (ladder plan phase 4; AI_LOG "Story review" steps 7–8): one glow carried from the Female response
// female into the dark Perception screen, where it pulses alone above the text (Female response's reply rhythm:
// 1.2 s cycle, flash at phase 0.6; flash colour as spectral.js FLASH); it fades as Two measured nights opens, and the
// Species perceptions replies continue it. Back to Female response it flies home to the female. Display device, not
// data. Story key `guide: true` marks the step where it rests. Size, rest place and timings: agent choices.
const guideEl = Object.assign(document.createElement('div'), { id: 'guide', hidden: true });
guideEl.innerHTML = '<i></i>';
document.body.append(guideEl);
const GUIDE_FLY = 1500, GUIDE_FADE = 900;
const guideRest = () => ({ x: window.innerWidth / 2, y: window.innerHeight / 2 - 110 });
let guideNow = { ...guideRest(), o: 0 }, guideFrame = 0;
const ease = t => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
function guideDraw({ x, y, o }) {
  guideNow = { x, y, o };
  guideEl.hidden = o <= 0.001;
  Object.assign(guideEl.style, { left: `${x}px`, top: `${y}px`, opacity: String(o) });
}
// Tween from the current place (or `from`) to `to()` (read each frame, so a moving target is followed); opacity o0 → o1,
// `late`: opacity holds until the last 30 % (flying home, then gone).
function guideTween({ from = null, to = () => guideNow, o0 = guideNow.o, o1, ms, late = false }) {
  cancelAnimationFrame(guideFrame);
  const a = from ?? { x: guideNow.x, y: guideNow.y }, t0 = performance.now();
  const tick = now => {
    const k = ease(Math.min(1, (now - t0) / ms)), b = to() ?? a, ko = late ? Math.max(0, (k - 0.7) / 0.3) : k;
    guideDraw({ x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, o: o0 + (o1 - o0) * ko });
    if (k < 1) guideFrame = requestAnimationFrame(tick);
  };
  guideFrame = requestAnimationFrame(tick);
}
function guideStep(prev, cur) {
  if (cur.guide) {
    const p = prev.spectral?.chapter === 'fireflies' ? spectral.femaleAt() : null;
    if (p) guideTween({ from: p, to: guideRest, o0: 1, o1: 1, ms: GUIDE_FLY });
    else guideTween({ from: guideNow.o > 0.01 ? null : guideRest(), to: guideRest, o1: 1, ms: GUIDE_FADE });
  } else if (prev.guide && cur.spectral?.chapter === 'fireflies') {
    guideTween({ to: () => spectral.femaleAt(), o1: 0, ms: GUIDE_FLY, late: true });
  } else if (guideNow.o > 0.001) guideTween({ o1: 0, ms: GUIDE_FADE });
}

let mode = 'light', lightSwipe = swipeFrac, storyIndex = 0, chartDelay = 0, turnDelay = 0, spinning = false;
// `globeSpin` (AI_LOG Impacts firefly-first step 6): after the step's fly the globe turns slowly, as in the intro
// (OrbitControls autoRotate, introScene.js speed 0.2 = 1.2°/s), until the step is left.
const SPIN_SPEED = 0.2;
// Story steps with an `impacts` stage show the Impacts layer inside the story (Part 2; human
// decision, AI_LOG Impacts step 27); the story arrow keeps driving.
// Door (human: option B + click, Firefly transition task step 2): between a chart step with `impacts.door` and the
// spectral step with the same `spectral.door`, the 3D view grows out of (or shrinks back into) that record's dot.
function applyStage(i) {
  clearTimeout(chartDelay); clearTimeout(turnDelay);
  if (spinning) { globe.controls().autoRotate = false; spinning = false; }   // `globeSpin` ends with its step
  const prev = story[storyIndex];
  storyIndex = i;
  markHeaders();
  if (mode !== 'light') { guideStep(prev, {}); return; }
  // Callouts: a step is entered on its own sentence (k = 0), or on its last callout when arriving backwards.
  const cl = story[i].impacts?.callouts;
  setCallout(cl?.length && story.indexOf(prev) === i + 1 ? cl.length : 0);
  guideStep(prev, story[i]);
  const sp = story[i].spectral ?? null, st = story[i].impacts;
  document.body.classList.toggle('story-dark', Boolean(story[i].dark));   // dark screen (Conclusion)
  darkScene.set(Boolean(story[i].dark));   // lights out, blue limb ring in (introScene.js createDarkScene)
  document.body.classList.toggle('story-spectral', Boolean(sp));
  document.body.classList.toggle('story-impacts', Boolean(st));
  // big text beside the chart (style.css); also the Broader Impacts circle (human, AI_LOG Fireflies step 29: same layout)
  document.body.classList.toggle('story-chart', st?.view === 'chart' || Boolean(st?.circle));
  document.body.classList.toggle('story-nights', Boolean(story[i].nights));
  // `noSwipe`: the 2015 | 2025 divider and year label hidden on a plain globe step (AI_LOG Firefly flow step 4).
  document.body.classList.toggle('story-noswipe', Boolean(story[i].noSwipe));
  // Local firefly ↔ Two measured nights (human: "two points, two halves", AI_LOG Firefly tabs review round 7f): the
  // nights step's `nightsSites` (left, right) glow on the globe; the halves open out of / close into those glows.
  const ns = story[i].nightsSites, pns = prev.nightsSites, glowOf = k => () => impacts.siteGlow(k);
  if (ns && prev.impacts?.site === ns[0]) {
    impacts.setStage({ ...prev.impacts, site: ns, glow: true });
    spectral.set(null);
    nights.set(true, { from: ns.map(glowOf), onTakeover: () => impacts.hide() });
    return;
  }
  if (pns && st?.site === pns[0]) {
    spectral.set(null);
    nights.set(false, { to: pns.map(glowOf), onDone: () => impacts.setStage(st),
      onTakeover: () => { impacts.show(); impacts.setStage({ ...st, site: pns, glow: true }, { snap: true }); } });
    return;
  }
  nights.set(story[i].nights);
  const at = sp?.door && prev.impacts?.door === sp.door ? impacts.doorAt(sp.door) : null;
  if (at) {   // forward: the chart stays (its filter bar hidden) under the opening view, then goes
    impacts.setStage({ ...prev.impacts, filter: false }, { snap: true });
    spectral.set(sp, { from: at, onDone: () => impacts.hide() });
    return;
  }
  // Site (human: "point becomes the scene", AI_LOG Firefly tabs review round 6b): between a globe step with
  // `impacts.site` and the spectral step with the same `spectral.site`, the point glows and grows while the globe
  // zooms in (story.js camera + fly), then the scene opens out of the glow; going back, it closes into the glow,
  // which shrinks back to the point as the globe zooms out.
  // Arriving backwards (Local firefly → Mate-finding, round 7d) the manual chapter starts on its last beat, as elsewhere.
  // Study sites ('study:<id>', AI_LOG Impacts firefly-first step 8): no glow (human: "a geometric opening into the view
  // (like the circle expansion) without the glow"): the scene opens as a circle out of the study's dot (spectral.js door,
  // delayed and stretched to the camera's dive), and closes back into it.
  const studySite = k => typeof k === 'string' && k.startsWith('study:');
  if (studySite(sp?.site) && prev.impacts?.site === sp.site) {
    impacts.setStage({ ...prev.impacts, studyLabel: null });   // the label fades as the circle opens over it
    spectral.set(sp, { from: impacts.siteAt(sp.site), dive: story[i].fly ?? 2200, onDone: () => impacts.hide(),
      beat: sp.manual && story.indexOf(prev) === i + 1 ? 'last' : 0 });
    return;
  }
  if (studySite(st?.site) && prev.spectral?.site === st.site) {
    impacts.show(); impacts.setStage(st, { snap: true });
    spectral.set(null, { to: impacts.siteAt(st.site) });
    return;
  }
  if (sp?.site && prev.impacts?.site === sp.site) {
    impacts.setStage({ ...prev.impacts, glow: true });
    spectral.set(sp, { glow: () => impacts.siteAt(sp.site), onDone: () => impacts.hide(),
      beat: sp.manual && story.indexOf(prev) === i + 1 ? 'last' : 0, fly: story[i].fly ?? 2200 });
    return;
  }
  if (st?.site && prev.spectral?.site === st.site) {
    impacts.show(); impacts.setStage({ ...st, glow: true }, { snap: true });
    spectral.set(null, { glow: () => impacts.siteAt(st.site), onDone: () => impacts.setStage(st) });
    return;
  }
  const back = st?.door && prev.spectral?.door === st.door;
  const beat = sp?.manual && story.indexOf(prev) === i + 1 ? 'last' : 0;   // arriving backwards: last beat
  if (back) {   // backward: the chart is ready (filter bar held back) under the closing view
    impacts.show(); impacts.setStage({ ...st, filter: false }, { snap: true });
    spectral.set(null, { to: impacts.doorAt(st.door), onDone: () => impacts.setStage(st) });
    return;
  }
  // Species perceptions → All effects (human, AI_LOG Fireflies step 14): a chart step with `globeHold`, entered from a
  // step without the Impacts layer, first shows the study dots on the globe during the flight and the hold.
  if (st?.view === 'chart' && story[i].globeHold != null && !prev.impacts) {
    impacts.show(); impacts.setStage({ view: 'globe' });
    chartDelay = setTimeout(() => { if (storyIndex === i && mode === 'light') impacts.setStage(st); },
      (story[i].fly ?? 0) + story[i].globeHold);
  } else if (st) { impacts.show(); impacts.setStage(st); } else impacts.hide();
  if (story[i].globeSpin) turnDelay = setTimeout(() => {
    if (storyIndex !== i || mode !== 'light') return;
    const c = globe.controls(); c.autoRotateSpeed = SPIN_SPEED; c.autoRotate = true; spinning = true;
  }, story[i].fly ?? 0);
  spectral.set(sp, { beat });
}

// On a manual spectral step, ← → step through its beats first (capture phase, before story.js's own keys);
// past either end they move the story as usual (human request, Firefly transition task step 3).
// Two measured nights (AI_LOG Firefly flow step 4): ← → and the nav arrows step its beats first (twoNights.js beat);
// past either end they move the story.
const nightsBeat = d => mode === 'light' && story[storyIndex].nights === true && nights.beat(d);
// Callout beats (impacts.callouts; human, AI_LOG Effect dots and examples step 5): ← → and the nav arrows step through
// the step's callouts first (k = 0 is the step's own sentence, k = n its last quote); past either end they move the story.
let calloutK = 0;
// "Source" under a callout quote opens its study's card (human, AI_LOG Effect dots and examples step 9).
document.getElementById('fact').addEventListener('click', e => { if (e.target.closest('.source')) impacts.openCallout(); });
function setCallout(k) {
  const cl = mode === 'light' ? story[storyIndex].impacts?.callouts : null;
  calloutK = k;
  impacts.setCallout(cl, k);
  if (cl?.length) document.querySelectorAll('#fact .line').forEach((p, n) => p.classList.toggle('on', n === k));
}
const calloutBeat = d => {
  const n = mode === 'light' ? story[storyIndex].impacts?.callouts?.length ?? 0 : 0, k = calloutK + d;
  if (!n || k < 0 || k > n) return false;
  setCallout(k);
  return true;
};
window.addEventListener('keydown', e => {
  if (e.target.id === 'volume') return;   // arrows on the volume slider (introScene.js) move only the slider
  const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
  if (d && (nightsBeat(d) || calloutBeat(d))) e.stopImmediatePropagation();
}, true);
document.getElementById('nav').addEventListener('click', e => {
  const d = e.target.closest('.next') ? 1 : e.target.closest('.back') ? -1 : 0;
  if (d && (nightsBeat(d) || calloutBeat(d))) e.stopPropagation();
}, true);
window.addEventListener('keydown', e => {
  if (e.target.id === 'volume') return;   // arrows on the volume slider (introScene.js) move only the slider
  if (mode !== 'light' || !story[storyIndex].spectral?.manual) return;
  const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
  if (d && spectral.step(d)) e.stopImmediatePropagation();
}, true);

// Story steps (content in app/content/story.js); sets the first camera view.
// PROTOTYPE: ?intro=sunrise swaps the CSS intro for a 3D sunrise scene (human: option B, intro scene task).
const intro = INTRO_MODE === 'sunrise' ? createIntroScene({ globe, layer }) : null;
const darkScene = createDarkScene({ globe, layer });
const storyCtl = startStory({ steps: story, globe, intro, onStep: i => { markStep(i); applyStage(i); },
  swipe: { get: () => swipeFrac, set: f => { swipeFrac = f; placeSwipe(); } } });

function setMode(m) {
  if (m === mode) return;
  mode = m;
  document.body.dataset.mode = m;
  markHeaders();
  if (m === 'impacts') {
    storyCtl.pause();
    lightSwipe = swipeFrac;
    swipeFrac = 0; placeSwipe();   // 0 = all 2025
    document.body.classList.remove('story-impacts', 'story-spectral', 'story-nights', 'story-dark', 'story-noswipe');
    darkScene.set(false);
    guideStep({}, {});
    spectral.set(null);
    nights.set(false);
    impacts.hide();
    impacts.show(); impacts.setStage(null);
  } else {
    impacts.hide();
    swipeFrac = lightSwipe; placeSwipe();
    storyCtl.resume();
    applyStage(storyIndex);
  }
}
modes.addEventListener('click', e => {
  const b = e.target.closest('button');
  if (!b) return;
  // A heading jumps to the first story step of its section, skipping the intro animation
  // (Light → "Statistic", Impacts → "Ecosystems", Explore → "Explore all studies"; human requests, steps 33–34).
  const i = b.dataset.mode
    ? story.findIndex(s => s.kind !== 'intro' && partOf(s) === PART_OF_MODE[b.dataset.mode])
    : Number(b.dataset.step);
  setMode('light'); storyCtl.go(i);
});
document.body.dataset.mode = mode;
markHeaders();
