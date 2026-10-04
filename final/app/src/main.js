import * as THREE from 'three';
import Globe from 'globe.gl';
import { TileLayer } from './tileLayer.js';
import { startStory } from './story.js';
import { createImpacts } from './impacts.js';
import { createSpectral } from './spectral.js';
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
// Heading highlight: Impacts while browsing or on a Part 2 story step, otherwise Light.
// Only the current section's step list is open; the other collapses (human request, AI_LOG Impacts step 33).
const markHeaders = () => {
  const impactsOn = mode === 'impacts' || partOf(story[storyIndex]) === 2;
  modes.querySelectorAll('.mode').forEach(b => {
    const on = (b.dataset.mode === 'impacts') === impactsOn;
    b.setAttribute('aria-pressed', String(on));
    b.setAttribute('aria-expanded', String(on));
  });
  modes.querySelectorAll('.steps').forEach(l => l.classList.toggle('collapsed', (l.dataset.part === '2') !== impactsOn));
};
const markStep = i => modes.querySelectorAll('.steps button').forEach(b =>
  b.classList.toggle('current', Number(b.dataset.step) === i));

// Impacts: study dots on a canvas overlay + study card (app/src/impacts.js).
const impacts = createImpacts({ globe, globeEl: el, card: document.getElementById('study'), legend });
// Spectral chapters (app/src/spectral.js): a 3D view over the globe on steps with a `spectral` key
// (human decisions, AI_LOG Impacts steps 74–75).
const spectral = createSpectral({ parent: document.body });

let mode = 'light', lightSwipe = swipeFrac, storyIndex = 0;
// Story steps with an `impacts` stage show the Impacts layer inside the story (Part 2; human
// decision, AI_LOG Impacts step 27); the story arrow keeps driving.
function applyStage(i) {
  storyIndex = i;
  markHeaders();
  if (mode !== 'light') return;
  const sp = story[i].spectral ?? null;
  document.body.classList.toggle('story-spectral', Boolean(sp));
  spectral.set(sp);
  const st = story[i].impacts;
  document.body.classList.toggle('story-impacts', Boolean(st));
  if (st) { impacts.show(); impacts.setStage(st); } else impacts.hide();
}

// Story steps (content in app/content/story.js); sets the first camera view.
const storyCtl = startStory({ steps: story, globe, onStep: i => { markStep(i); applyStage(i); },
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
    document.body.classList.remove('story-impacts', 'story-spectral');
    spectral.set(null);
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
  // (Light → "Statistic", Impacts → "Ecosystems"; human requests, steps 33–34).
  const i = b.dataset.mode
    ? story.findIndex(s => s.kind !== 'intro' && partOf(s) === (b.dataset.mode === 'impacts' ? 2 : 1))
    : Number(b.dataset.step);
  setMode('light'); storyCtl.go(i);
});
document.body.dataset.mode = mode;
markHeaders();
