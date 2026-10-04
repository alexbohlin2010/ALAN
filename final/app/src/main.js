import * as THREE from 'three';
import Globe from 'globe.gl';
import { TileLayer } from './tileLayer.js';
import { startStory } from './story.js';
import { createIntroScene, INTRO_MODE } from './introScene.js';
import { createImpacts } from './impacts.js';
import { createSpectral } from './spectral.js';
import { createTwoNights } from './twoNights.js';
import { story } from '../content/story.js';

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
const spectral = createSpectral({ parent: document.body });
// Two measured nights (app/src/twoNights.js): City vs Rural night spectra behind a divider, on steps with
// `nights: true` (human decision, AI_LOG Firefly narrative round 3c).
const nights = createTwoNights({ parent: document.body });

let mode = 'light', lightSwipe = swipeFrac, storyIndex = 0;
// Story steps with an `impacts` stage show the Impacts layer inside the story (Part 2; human
// decision, AI_LOG Impacts step 27); the story arrow keeps driving.
// Door (human: option B + click, Firefly transition task step 2): between a chart step with `impacts.door` and the
// spectral step with the same `spectral.door`, the 3D view grows out of (or shrinks back into) that record's dot.
function applyStage(i) {
  const prev = story[storyIndex];
  storyIndex = i;
  markHeaders();
  if (mode !== 'light') return;
  const sp = story[i].spectral ?? null, st = story[i].impacts;
  document.body.classList.toggle('story-dark', Boolean(story[i].dark));   // dark screen (Conclusion)
  document.body.classList.toggle('story-spectral', Boolean(sp));
  document.body.classList.toggle('story-impacts', Boolean(st));
  document.body.classList.toggle('story-nights', Boolean(story[i].nights));
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
  if (sp?.site && prev.impacts?.site === sp.site) {
    impacts.setStage({ ...prev.impacts, glow: true });
    spectral.set(sp, { glow: () => impacts.siteAt(sp.site), onDone: () => impacts.hide() });
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
  if (st) { impacts.show(); impacts.setStage(st); } else impacts.hide();
  spectral.set(sp, { beat });
}

// On a manual spectral step, ← → step through its beats first (capture phase, before story.js's own keys);
// past either end they move the story as usual (human request, Firefly transition task step 3).
window.addEventListener('keydown', e => {
  if (mode !== 'light' || !story[storyIndex].spectral?.manual) return;
  const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
  if (d && spectral.step(d)) e.stopImmediatePropagation();
}, true);

// Story steps (content in app/content/story.js); sets the first camera view.
// PROTOTYPE: ?intro=sunrise swaps the CSS intro for a 3D sunrise scene (human: option B, intro scene task).
const intro = INTRO_MODE === 'sunrise' ? createIntroScene({ globe, layer }) : null;
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
    document.body.classList.remove('story-impacts', 'story-spectral', 'story-nights');
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
