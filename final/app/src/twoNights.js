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
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { CSS3DRenderer, CSS3DObject } from 'three/examples/jsm/renderers/CSS3DRenderer.js';

const SITES = [{ id: 'philadelphia', name: 'Philadelphia', side: 1 }, { id: 'cherry_springs', name: 'Cherry Springs', side: -1 }];
const SCAN_MS = 90000;   // draft TIME_SCAN_CYCLE_MS
const CAMERA = { position: [17, 11, 20], target: [0, 3.2, 0], fov: 44 };   // draft CAMERA_PRESETS.default

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
  varying vec3 vColor;
  varying float vAlpha;
  varying float vBand;
  void main() {
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    float focusSignal = 1.0 - smoothstep(0.0, 0.022, abs(aTime - uTimeFocus));
    float focus = 1.30 * (0.24 + 0.76 * focusSignal);
    float qualityAlpha = aQuality > 1.5 ? 0.08 : (aQuality > 0.5 ? 0.18 : 1.0);
    vColor = aColor;
    vAlpha = max(0.02, aStrength * focus * qualityAlpha);
    vBand = aBand;
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
  void main() {
    if ((gl_FragCoord.x - uSplit) * uSide > 0.0) discard;
    vec2 p = gl_PointCoord - vec2(0.5);
    float radius = length(p);
    float shapeAlpha;
    if (vBand < 0.5) {
      shapeAlpha = 1.0 - smoothstep(0.30, 0.50, radius);
    } else if (vBand < 1.5) {
      shapeAlpha = 1.0 - smoothstep(0.07, 0.15, abs(radius - 0.31));
    } else {
      shapeAlpha = 1.0 - smoothstep(0.32, 0.50, abs(p.x) + abs(p.y));
    }
    if (shapeAlpha <= 0.01 || vAlpha <= 0.002) discard;
    gl_FragColor = vec4(vColor, vAlpha * shapeAlpha);
  }`;

export function createTwoNights({ parent }) {
  const canvas = Object.assign(document.createElement('canvas'), { id: 'nights-canvas', hidden: true });
  const css = new CSS3DRenderer();
  css.domElement.id = 'nights-labels';
  css.domElement.hidden = true;
  const divider = Object.assign(document.createElement('div'), { id: 'nights-divider', hidden: true });
  divider.innerHTML = '<div class="line"></div><div class="handle" aria-label="Drag to compare the two sites"></div>';
  // Site names at the screen edges, like the globe's year labels (.year).
  const names = SITES.map(s => Object.assign(document.createElement('div'),
    { className: `nights-site ${s.side > 0 ? 'left' : 'right'}`, textContent: s.name, hidden: true }));
  parent.append(canvas, css.domElement, divider, ...names);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false });
  const pixelRatio = Math.min(window.devicePixelRatio, 1.5);   // draft Canvas dpr [1, 1.5]
  renderer.setPixelRatio(pixelRatio);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#030508');
  scene.fog = new THREE.Fog('#030508', 22, 52);
  const camera = new THREE.PerspectiveCamera(CAMERA.fov, 1, 0.05, 120);
  const controls = new OrbitControls(camera, canvas);
  Object.assign(controls, { enableDamping: true, dampingFactor: 0.08, minDistance: 13, maxDistance: 44,
    minPolarAngle: 0.35, maxPolarAngle: Math.PI / 2.05 });
  const resetCamera = () => {
    camera.position.set(...CAMERA.position);
    controls.target.set(...CAMERA.target);
    controls.update();
  };

  let split = 0.5, running = false, shown = false, t0 = 0, last = 0, timeIndex = 0, meta = null;
  const materials = [];
  let focusPlane = null, focusOutline = null, focusLabel = null;

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
    scene.add(lines(grid, '#242d39', 0.82));
    scene.add(lines([[[-12, 0, 8], [12, 0, 8]], [[-12, 0, 8], [-12, 9, 8]], [[-12, 0, -8], [-12, 0, 8]]], '#465364'));
    scene.add(lines([380, 700].map(nm => [[xOf(nm), 0, -8], [xOf(nm), 9, -8]]), '#566273', 0.55));
    focusPlane = new THREE.Mesh(new THREE.PlaneGeometry(24, 9), new THREE.MeshBasicMaterial({ color: '#ffffff',
      transparent: true, opacity: 0.2, side: THREE.DoubleSide, depthWrite: false }));
    focusPlane.position.set(0, 4.5, 0);
    focusOutline = lines([[[-12, 0, 0], [12, 0, 0]], [[12, 0, 0], [12, 9, 0]], [[12, 9, 0], [-12, 9, 0]],
      [[-12, 9, 0], [-12, 0, 0]]], '#dfe5ec', 0.22);
    scene.add(focusPlane, focusOutline);
    focusLabel = label('CURRENT SPECTRUM', [10.1, 9.35, 0]);
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

  // ── points (draft SpectralPoints.tsx geometry) ──────────────────────────
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
        uSplit: { value: 0 }, uSide: { value: site.side } } });
    const p = new THREE.Points(g, m);
    p.frustumCulled = false;
    scene.add(p);
    materials.push(m);
    return T;
  }

  let count = 240;
  let loaded = null;
  const load = () => loaded ??= Promise.all(['spectra_meta', ...SITES.map(s => s.id)].map(f =>
    fetch(`/spectra/${f}.json`).then(r => r.json()))).then(([m, ...docs]) => {
    meta = { wavelengths: m.wavelength_nm, floor: m.display_limits_log10.floor, ceil: m.display_limits_log10.ceil };
    buildFrame();
    count = Math.min(...SITES.map((s, k) => buildSite(s, docs[k])));
  });

  // ── divider (look of the globe's #swipe) ─────────────────────────────────
  function placeDivider() {
    divider.style.left = `${split * canvas.clientWidth}px`;
    materials.forEach(m => { m.uniforms.uSplit.value = split * canvas.clientWidth * pixelRatio; });
  }
  divider.querySelector('.handle').addEventListener('pointerdown', e => {
    e.target.setPointerCapture(e.pointerId);
    const move = ev => { split = Math.min(1, Math.max(0, ev.clientX / window.innerWidth)); placeDivider(); };
    const up = () => { e.target.removeEventListener('pointermove', move); e.target.removeEventListener('pointerup', up); };
    e.target.addEventListener('pointermove', move);
    e.target.addEventListener('pointerup', up);
  });

  // ── loop ─────────────────────────────────────────────────────────────────
  function frame(now) {
    if (!running) return;
    const delta = Math.min(0.1, (now - last) / 1000);
    last = now;
    timeIndex = Math.floor((now - t0) / (SCAN_MS / count)) % count;
    const focus = timeIndex / Math.max(1, count - 1), speed = Math.min(1, delta * 3.8);
    materials.forEach(m => { m.uniforms.uTimeFocus.value += (focus - m.uniforms.uTimeFocus.value) * speed; });
    const z = -8 + focus * 16;
    focusPlane.position.z = focusOutline.position.z = focusLabel.position.z = z;
    controls.update();
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
    // on = the story step has `nights: true`. Entering resets the camera, the divider and the scan.
    async set(on) {
      shown = Boolean(on);
      if (!shown) {
        running = false;
        canvas.hidden = css.domElement.hidden = divider.hidden = true;
        names.forEach(n => { n.hidden = true; });
        return;
      }
      await load();
      if (!shown || running) return;   // left the step while loading, or already showing
      canvas.hidden = css.domElement.hidden = divider.hidden = false;
      names.forEach(n => { n.hidden = false; });
      split = 0.5;
      resize();
      resetCamera();
      materials.forEach(m => { m.uniforms.uTimeFocus.value = 0; });
      t0 = last = performance.now();
      running = true;
      requestAnimationFrame(frame);
    },
  };
}
