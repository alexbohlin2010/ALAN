import * as THREE from 'three';
import Globe from 'globe.gl';
import { TileLayer } from './tileLayer.js';
import { startStory, revealLine } from './story.js';
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
  layer.moved();   // 4-sample shading while the camera moves (tileLayer.js MOVE_AA)
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
    // Fading in (panRun), the guide just fades in at its rest place with the screen it belongs to.
    const p = prev.spectral?.chapter === 'fireflies' && !panKind ? spectral.femaleAt() : null;
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
// Fades (human, AI_LOG Experience refinement step 19: the sideways pan (P2) tried and cancelled, "I'd rather to fade
// out and in ... not necessarily dissolve"): Response fades out, then Impact's question fades in; Impact's question fades
// out, then Spectra fades in; back the same in reverse. Impact sits on plain black (`black: true`; human: no globe or
// glow behind it), a backdrop over the globe for that step and for the fades either side of it. The old text fades as a
// frozen copy (ghost). Display only; FADE_OUT / FADE_IN: agent choices.
const FADE_OUT = 600, FADE_IN = 900;
const backdrop = document.body.appendChild(Object.assign(document.createElement('div'), { id: 'pan-backdrop', hidden: true }));
let panKind = null, panTimer = 0, panAnims = [], ghost = null;
const panEls = ids => ids.map(id => document.getElementById(id)).filter(Boolean);
const SPECTRAL_EL = ['spectral-canvas', 'spectral-labels', 'spectral-number', 'spectral-toggle', 'spectral-caption'];
const nightsEls = () => [...panEls(['nights-canvas', 'nights-labels', 'nights-divider', 'nights-window', 'nights-species']),
  ...document.querySelectorAll('.nights-site')];
function panOf(a, b) {
  if (b.black && a.spectral?.chapter === 'fireflies') return 'F1';   // Response → Impact
  if (a.black && b.spectral?.chapter === 'fireflies') return 'B1';
  if (a.black && b.nights === true) return 'F2';   // Impact → Spectra
  if (b.black && a.nights === true) return 'B2';
  return null;
}
function clearPan() {
  clearTimeout(panTimer);
  panAnims.forEach(a => a.cancel()); panAnims = [];
  ghost?.remove(); ghost = null;
}
// The current big text, frozen where it is (computed styles inlined, no Details button).
function ghostFact() {
  const f = document.getElementById('fact');
  if (f.hidden) return null;
  const g = f.cloneNode(true), src = [f, ...f.querySelectorAll('*')], dst = [g, ...g.querySelectorAll('*')];
  src.forEach((e, k) => {
    const cs = getComputedStyle(e);
    ['font', 'color', 'margin', 'textAlign', 'opacity', 'maxHeight', 'overflow', 'display', 'boxSizing']
      .forEach(p => { dst[k].style[p] = cs[p]; });
    dst[k].style.transition = dst[k].style.animation = 'none';
  });
  const r = f.getBoundingClientRect();
  g.removeAttribute('id');
  g.querySelectorAll('.more, .more-body').forEach(e => e.remove());
  Object.assign(g.style, { position: 'fixed', left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, right: 'auto',
    bottom: 'auto', transform: 'none', zIndex: '4', pointerEvents: 'none' });
  return document.body.appendChild(g);
}
// Before story.js replaces the text (onLeave): freeze the old text if this move fades.
function panLeave(i) {
  clearPan();
  panKind = mode === 'light' ? panOf(story[storyIndex], story[i]) : null;
  if (panKind) ghost = ghostFact();
  document.getElementById('fact').style.animation = '';   // after the copy (panRun may have turned it off)
}
function panRun(i) {
  const k = panKind, fact = document.getElementById('fact');
  panKind = null;   // only for this step change
  const black = mode === 'light' && Boolean(story[i].black);
  if (!k) { ghost?.remove(); ghost = null; backdrop.hidden = !black; return; }
  const out = e => e && panAnims.push(e.animate([{ opacity: 1 }, { opacity: 0 }], { duration: FADE_OUT, easing: 'ease', fill: 'forwards' }));
  const into = e => e && panAnims.push(e.animate([{ opacity: 0 }, { opacity: 1 }], { duration: FADE_IN, delay: FADE_OUT, easing: 'ease', fill: 'backwards' }));
  backdrop.hidden = false;
  if (k === 'F1') [...panEls(SPECTRAL_EL), ghost].forEach(out);
  if (k === 'B2') [...nightsEls(), ghost].forEach(out);
  if (k === 'F2' || k === 'B1') out(ghost);
  if (k === 'F1' || k === 'B2') fact.style.animation = 'none';   // instead of the dark screen's 2.5 s text fade-in
  [fact, ...(k === 'F2' ? nightsEls() : k === 'B1' ? panEls(SPECTRAL_EL) : [])].forEach(into);
  const at = storyIndex;
  panTimer = setTimeout(() => {
    if (k === 'F1' && storyIndex === at) spectral.set(null);   // held while it fades (applyStage)
    ghost?.remove(); ghost = null;
    panTimer = setTimeout(() => {
      panAnims.forEach(a => a.cancel()); panAnims = [];
      backdrop.hidden = !black;
    }, FADE_IN);
  }, FADE_OUT);
}
function applyStage(i) {
  if (!panKind) backdrop.hidden = !(mode === 'light' && story[i].black);   // also on paths that return early
  clearTimeout(chartDelay); clearTimeout(turnDelay); clearTimeout(autoTimer); clearTimeout(dotsFade);
  impactsCanvas().style.opacity = '';
  if (spinning) { globe.controls().autoRotate = false; spinning = false; }   // `globeSpin` ends with its step
  const prev = story[storyIndex];
  storyIndex = i;
  markHeaders();
  if (mode !== 'light') { guideStep(prev, {}); return; }
  // Callouts: a step is entered on its own sentence (k = 0), or on its last callout when arriving backwards.
  const nb = beatCount(story[i]);
  setCallout(nb && story.indexOf(prev) === i + 1 ? nb : 0);
  guideStep(prev, story[i]);
  const sp = story[i].spectral ?? null, st = story[i].impacts;
  // dark screen (Conclusion): lights out, blue limb ring in (introScene.js createDarkScene); from beat `darkFrom` (applyDark)
  applyDark();
  // `autoBeat` (Conclusion; human, AI_LOG Experience refinement step 5): arriving forward on beat 0, beat 1 follows on its own.
  if (story[i].autoBeat && calloutK === 0) autoTimer = setTimeout(() => {
    if (storyIndex === i && mode === 'light' && calloutK === 0) setCallout(1);
  }, story[i].autoBeat);
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
  // Perception → Firefly Populations (`cutFrom`): the view fades out over the globe, already at the eastern US (human,
  // AI_LOG Experience refinement step 18). Fade 1200 ms: agent choice.
  nights.set(story[i].nights, { fade: !story[i].nights && story[i].cutFrom === prev.id ? 1200 : 0, hold: panKind === 'B2' ? FADE_OUT : 0 });
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
    // No dive and no scaling (human, AI_LOG Experience refinement step 17): a dark circle grows out of the dot at once
    // (`dive` 0 unless the step has a `fly`; `flat`). Was dive: fly ?? 2200, scene scaled 0.3 → 1.
    spectral.set(sp, { from: impacts.siteAt(sp.site), dive: story[i].fly ?? 0, flat: true, onDone: () => impacts.hide(),
      beat: sp.manual && story.indexOf(prev) === i + 1 ? 'last' : 0 });
    return;
  }
  if (studySite(st?.site) && prev.spectral?.site === st.site) {
    impacts.show(); impacts.setStage(st, { snap: true });
    spectral.set(null, { to: impacts.siteAt(st.site), flat: true });
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
  } else if (st) { impacts.show(); impacts.setStage(st); }
  else if (prev.impacts?.circle && story[i].dark) {   // Biosphere Response → Conclusion: the dots fade out
    const c = impactsCanvas();
    c.style.transition = `opacity ${DOTS_FADE}ms ease`; c.style.opacity = '0';
    dotsFade = setTimeout(() => { impacts.hide(); c.style.opacity = c.style.transition = ''; }, DOTS_FADE);
  } else impacts.hide();
  if (story[i].globeSpin) turnDelay = setTimeout(() => {
    if (storyIndex !== i || mode !== 'light') return;
    const c = globe.controls(); c.autoRotateSpeed = SPIN_SPEED; c.autoRotate = true; spinning = true;
  }, story[i].fly ?? 0);
  if (panKind !== 'F1') spectral.set(sp, { beat });   // F1: Response stays on while it fades out (panRun hides it)
  panRun(i);
}

// On a manual spectral step, ← → step through its beats first (capture phase, before story.js's own keys);
// past either end they move the story as usual (human request, Firefly transition task step 3).
// Two measured nights (AI_LOG Firefly flow step 4): ← → and the nav arrows step its beats first (twoNights.js beat);
// past either end they move the story.
const nightsBeat = d => mode === 'light' && story[storyIndex].nights === true && nights.beat(d);
// Callout beats (impacts.callouts; human, AI_LOG Effect dots and examples step 5): ← → and the nav arrows step through
// the step's callouts first (k = 0 is the step's own sentence, k = n its last quote); past either end they move the story.
let calloutK = 0;
let releaseTimer = 0;
const RELEASE_LINE = 1500;   // ms after the release beat starts (human: "1s earlier", AI_LOG Experience refinement step 25; was 2500)
// "Source" under a callout quote opens its study's card (human, AI_LOG Effect dots and examples step 9).
document.getElementById('fact').addEventListener('click', e => { if (e.target.closest('.source')) impacts.openCallout(); });
// `beats: true` (Conclusion; AI_LOG Conclusion step 6): the step's `reveal` lines are beats the same way, without quotes.
// `impacts.release` (Biosphere Response; human, AI_LOG Experience refinement step 23): one more beat after the last callout.
const beatCount = s => (s.impacts?.callouts?.length ?? 0) + (s.impacts?.release ? 1 : 0) || (s.beats ? s.reveal?.length ?? 0 : 0);
function setCallout(k) {
  const cl = mode === 'light' ? story[storyIndex].impacts?.callouts : null;
  calloutK = k;
  impacts.setCallout(cl, k);
  // `together: [k]`: beat k also keeps the line before it (Conclusion; human, AI_LOG Experience refinement step 5).
  const tog = story[storyIndex].together ?? [];
  // Release beat (impacts.release): the last quote stays (lk); the step's releaseLine, if any, comes in below it after
  // RELEASE_LINE ms, the quote not moving (human, AI_LOG Experience refinement step 25, P1).
  const fact = document.getElementById('fact'), rl = story[storyIndex].impacts?.releaseLine ? fact.querySelector('.line.below') : null;
  const ls = [...fact.querySelectorAll('.line')].filter(p => p !== rl), lk = Math.min(k, ls.length - 1);
  if (mode === 'light' && beatCount(story[storyIndex])) ls.forEach((p, n) =>
    p.classList.toggle('on', n === lk || (n === lk - 1 && tog.includes(lk))));
  clearTimeout(releaseTimer);
  if (rl && mode === 'light' && k > ls.length - 1) releaseTimer = setTimeout(() => revealLine(fact, rl), RELEASE_LINE);
  else if (rl?.classList.contains('on')) { rl.classList.remove('on'); fact.style.setProperty('--fact-top', ''); }
  // On a `beats` step, Details & sources shows on the last beat only (human, AI_LOG Conclusion step 8).
  const s = story[storyIndex];
  document.getElementById('fact').classList.toggle('details-off', mode === 'light' && Boolean(s.beats) && k < beatCount(s));
  if (mode === 'light') applyDark();
  anchorFact(k);
}
// `dark: true` steps: dark from beat `darkFrom` (default 0). `story-centre` centres the text for the whole step, lit or
// dark (AI_LOG Experience refinement step 5). On a `humFrom` step story.js leaves the hum to applyDark.
let autoTimer = 0, dotsFade = 0;
const DOTS_FADE = 1000;   // agent choice
const impactsCanvas = () => document.getElementById('impacts-canvas');
function applyDark() {
  const s = story[storyIndex], on = Boolean(s.dark) && calloutK >= (s.darkFrom ?? 0);
  document.body.classList.toggle('story-dark', on);
  document.body.classList.toggle('story-centre', Boolean(s.dark));
  darkScene.set(on);
  // `humFrom` (Conclusion; human, AI_LOG Experience refinement step 6): the hum plays on until this beat, then fades.
  if (s.humFrom != null) intro?.humFor({ part: s.part, humOff: mode === 'light' && calloutK >= s.humFrom });
}
// Line 0 anchored on a `together` step (human, AI_LOG Experience refinement step 6): #fact's top is fixed where line 0
// alone sits centred, so the next line comes in below it without the block re-centring. Text centred on the screen as
// before on the other beats (the anchor is held until their lines have swapped, 500 ms, style.css #fact .line).
let unanchor = 0;
function anchorFact(k) {
  const s = story[storyIndex], fact = document.getElementById('fact'), tog = s.together ?? [];
  clearTimeout(unanchor);
  if (mode === 'light' && tog.includes(k)) {
    // Height with line 0 alone: its text + 14 px bottom margin per line (#fact .big margin; collapsed lines keep theirs).
    const ls = fact.querySelectorAll('.line'), h0 = ls[0].scrollHeight + 14 * ls.length;
    fact.style.top = `${(window.innerHeight - h0) / 2}px`;
    fact.style.transform = 'translate(-50%, 0)';
  } else if (fact.style.top) unanchor = setTimeout(() => { fact.style.top = fact.style.transform = ''; }, 500);
}
const calloutBeat = d => {
  const n = mode === 'light' ? beatCount(story[storyIndex]) : 0, k = calloutK + d;
  if (!n || k < 0 || k > n) return false;
  clearTimeout(autoTimer);   // an arrow during the `autoBeat` wait takes over
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
// Story flights: no tile refinement on the way (tileLayer.js capFlight; AI_LOG Experience refinement step 8), then a
// refresh on arrival.
let flightEnd = 0;
function capFlight(i) {
  const s = story[i], ms = s.cutFrom && s.cutFrom === story[storyIndex]?.id ? 0 : s.fly ?? 0;   // storyIndex: still the previous step
  clearTimeout(flightEnd);
  if (!ms || !s.camera) return;
  const cam = globe.camera();
  cam.updateMatrixWorld();
  layer.capFlight(cam, window.innerHeight * globe.renderer().getPixelRatio(), s.camera.altitude, ms);
  flightEnd = setTimeout(refresh, ms + 50);
}
const storyCtl = startStory({ steps: story, globe, intro, onLeave: panLeave, onStep: i => { markStep(i); capFlight(i); applyStage(i); },
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
    document.body.classList.remove('story-impacts', 'story-spectral', 'story-nights', 'story-dark', 'story-centre', 'story-noswipe');
    clearTimeout(autoTimer); clearTimeout(dotsFade); impactsCanvas().style.opacity = '';
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
