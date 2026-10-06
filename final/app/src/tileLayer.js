// Our own tile mesh for the native-pyramid radiance tiles (see tiles.json and
// pipeline/radiance/05_build_tiles.py). Added to globe.gl's scene via .scene().
// Each tile holds both years: R = grey 2015, G = grey 2025, B = flags.
// The swipe shader picks the year per screen pixel from one uniform.
import * as THREE from 'three';

const DEG = Math.PI / 180;
const MAX_LOADING = 12;
const MAX_CACHED = 600;
const FALLBACK_STEPS = 3;  // fallback texels are 8x the target's
// Levels coarser than the finest one levelFor finds: texels at the target level were 0.55–0.91 device px at the story's
// views and shimmered when the camera moved (NearestFilter, no mipmaps; AI_LOG Experience refinement step 1). 1 = one
// level coarser, ~2x texel size (human trial, step 2: "easy to undo"); 0 = as before. Back to 0 (human, step 7: "The
// original was more beautiful").
const LEVEL_BIAS = 0;
// Shimmer while the camera moves (human, AI_LOG Experience refinement step 8, option B): while it moves, each pixel
// averages 4 samples inside its footprint (rotated grid) instead of one; when it stops, back to one sample (sharp).
// uAA eases between the two: up in AA_IN ms, down in AA_OUT ms, after AA_IDLE ms without camera change. Timings: agent
// choices. MOVE_AA = false turns it off.
const MOVE_AA = true, AA_IDLE = 150, AA_IN = 120, AA_OUT = 600;

// Same convention as globe.gl / three-globe polar2Cartesian.
function toXYZ(lat, lng, r) {
  const phi = (90 - lat) * DEG, theta = (90 - lng) * DEG;
  return new THREE.Vector3(r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta));
}

const vertexShader = /* glsl */`
  attribute vec2 lonlat;
  varying vec2 vUv;
  varying vec2 vLonLat;
  void main() {
    vUv = uv;
    vLonLat = lonlat;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }`;

// No colour-space or tone-mapping includes: grey byte g is shown as g/255.
// Colour = display ramp (option B, human 2026-10-03), from pipeline/colour/09_display_ramp.py
// (data/derived/colour/display_ramp.json). Every lit pixel is grey x tint: sodium 2000 K
// below the year's grey threshold, white LED 4000 K above it, blended over +-RAMP_BLEND grey
// levels. Thresholds make the brightest pixels white so Iberia's white share per year equals
// the median photo white share (2015: 0.035 -> grey 248; 2025: 0.152 -> grey 219).
// Applied everywhere; outside Iberia it is a display choice only. Class bits in v2 B are ignored.
// Regional grid (human 2026-10-03, pipeline/colour/10_white_share_grid.py): where archive photos
// exist, each 0.25 deg cell has its own threshold from the local photo white share; it is blended
// with the year's threshold above by the cell's coverage (0 = no photos nearby).
// Texture: R = threshold 2015, G = threshold 2025, B = coverage 2015, A = coverage 2025.
// Global run (human 2026-10-03): the grid is a PNG with a JSON sidecar (extent, fallback
// thresholds). Once loaded, the year's thresholds become the global fallback from the sidecar.
const GRID_URL = '/colour/global_white_share_grid.json';
// Display choice, not data: the tints only set how lit pixels are drawn; radiance values and white shares are unchanged.
const RAMP_TINTS = [[1.0, 0.5529, 0.0838], [1.0, 0.8317, 0.649]];  // 2000 K, 4000 K (display_tints.json "ramp_white"; 4000 K, then 3000 K, 3200 K, back to 4000 K, human 2026-10-04)
const RAMP_THRESHOLDS = [248, 219];  // grey levels, 2015, 2025
const RAMP_BLEND = 8;
// Colour modes (human 2026-10-04, AI_LOG colour steps 64, 67): DEFAULT = place (B) with 1/20 deg blocks
// (human: "make B the default"). URL ?ramp= brightest (rule above) | place = B: a pixel block (1/20 deg, or 1/N deg with ?block=N) is white if a fixed hash of its
//   position < the cell's white share | blend = C: every pixel gets one tint mixed by the share.
// Share = mix(fallback share, cell share, coverage); cell shares from global_white_share_values.png.
const RAMP_BLOCKS = Number(new URLSearchParams(location.search).get('block')) || 20;  // blocks per degree (place mode), default 20 = ~5 km (human 2026-10-04)
const RAMP_MODE = { brightest: 0, place: 1, blend: 2 }[new URLSearchParams(location.search).get('ramp')] ?? 1;  // default place (B), human 2026-10-04
const fragmentShader = /* glsl */`
  uniform sampler2D map;
  uniform float uSwipeX;      // divider position in device pixels
  uniform vec3 uNoDataColor;  // display choice for "no data" (-1.5), labelled in legend
  uniform vec3 uTints[2];     // display ramp tints: sodium, white
  uniform vec2 uThresh;       // grey threshold (0-1) per year: x = 2015, y = 2025
  uniform float uBlend;       // blend half-width (0-1)
  uniform sampler2D uGrid;    // regional thresholds + coverage (see GRID_URL)
  uniform vec4 uGridBox;      // west, north, east, south of the grid's outer cell edges
  uniform sampler2D uShare;   // PROTOTYPE: R/G = cell white share 2015/2025
  uniform vec2 uFbShare;      // PROTOTYPE: fallback white share 2015/2025
  uniform float uMode;        // PROTOTYPE: 0 brightest, 1 place, 2 blend
  uniform float uBlocks;      // PROTOTYPE: place-mode blocks per degree
  uniform float uFade;        // 1 = normal; < 1 only during the ?intro=sunrise prototype (introScene.js)
  uniform float uAA;          // 0 = one sample, 1 = 4-sample average (camera moving; MOVE_AA)
  varying vec2 vUv;
  varying vec2 vLonLat;
  // One sample at uv / lon-lat ll; vec3(-1) = outside the raster.
  vec3 shade(vec2 uv, vec2 vLonLat) {
    vec3 t = texture2D(map, uv).rgb;
    int flags = int(t.b * 255.0 + 0.5);
    if ((flags & 4) != 0) return vec3(-1.0);       // outside the raster
    bool early = gl_FragCoord.x < uSwipeX;          // left of divider = 2015
    float g = early ? t.r : t.g;
    bool noData = (flags & (early ? 1 : 2)) != 0;
    vec2 gu = vec2((vLonLat.x - uGridBox.x) / (uGridBox.z - uGridBox.x),
                   1.0 - (uGridBox.y - vLonLat.y) / (uGridBox.y - uGridBox.w));
    vec4 cell = (gu.x >= 0.0 && gu.x <= 1.0 && gu.y >= 0.0 && gu.y <= 1.0)
      ? texture2D(uGrid, gu) : vec4(0.0);
    float thr = mix(early ? uThresh.x : uThresh.y, early ? cell.r : cell.g, early ? cell.b : cell.a);
    float w = smoothstep(-uBlend, uBlend, g - thr);
    if (uMode > 0.5) {
      vec4 sc = (gu.x >= 0.0 && gu.x <= 1.0 && gu.y >= 0.0 && gu.y <= 1.0) ? texture2D(uShare, gu) : vec4(0.0);
      float share = mix(early ? uFbShare.x : uFbShare.y, early ? sc.r : sc.g, early ? cell.b : cell.a);
      vec2 blk = floor(vLonLat * uBlocks);
      float h = fract(sin(dot(blk, vec2(12.9898, 78.233))) * 43758.5453);
      w = uMode < 1.5 ? step(h, share) : share;
    }
    vec3 c = g * mix(uTints[0], uTints[1], w);
    return (noData ? uNoDataColor : c) * uFade;
  }
  void main() {
    vec3 c0 = shade(vUv, vLonLat);
    if (c0.r < 0.0) discard;
    if (uAA < 0.001) { gl_FragColor = vec4(c0, 1.0); return; }
    vec2 dx = dFdx(vUv), dy = dFdy(vUv), lx = dFdx(vLonLat), ly = dFdy(vLonLat);
    vec3 acc = vec3(0.0); float n = 0.0;
    for (int i = 0; i < 4; i++) {
      vec2 o = i == 0 ? vec2(-0.125, -0.375) : i == 1 ? vec2(0.375, -0.125) : i == 2 ? vec2(0.125, 0.375) : vec2(-0.375, 0.125);
      vec3 c = shade(vUv + o.x * dx + o.y * dy, vLonLat + o.x * lx + o.y * ly);
      if (c.r >= 0.0) { acc += c; n += 1.0; }
    }
    gl_FragColor = vec4(mix(c0, acc / max(n, 1.0), uAA), 1.0);
  }`;

export class TileLayer {
  constructor({ baseUrl, index, radius, noDataColor }) {
    this.baseUrl = baseUrl;
    this.ix = index;
    this.radius = radius * 1.0005;  // just above the globe surface
    this.group = new THREE.Group();
    this.uniforms = {
      uSwipeX: { value: 0 },
      uNoDataColor: { value: new THREE.Color(noDataColor) },
      uTints: { value: RAMP_TINTS.map(([r, g, b]) => new THREE.Vector3(r, g, b)) },
      uThresh: { value: new THREE.Vector2(RAMP_THRESHOLDS[0] / 255, RAMP_THRESHOLDS[1] / 255) },
      uBlend: { value: RAMP_BLEND / 255 },
      uGrid: { value: new THREE.DataTexture(new Uint8Array(4), 1, 1) },
      uGridBox: { value: new THREE.Vector4(0, 1, 1, 0) },
      uShare: { value: new THREE.DataTexture(new Uint8Array(4), 1, 1) },
      uFbShare: { value: new THREE.Vector2(0, 0) },
      uMode: { value: RAMP_MODE },
      uBlocks: { value: RAMP_BLOCKS },
      uFade: { value: 1 },
      uAA: { value: 0 },
    };
    this.aaTarget = 0; this.aaLast = 0; this.aaTimer = 0; this.aaFrame = 0;
    // Flight cap (option D): level ≤ capLevel until capUntil (performance.now() ms); see capFlight.
    this.capLevel = Infinity; this.capUntil = 0;
    this.tiles = new Map();         // key -> { mesh, level, used }
    this.loading = new Set();
    this.queue = [];
    this.loader = new THREE.ImageBitmapLoader();
    this.loader.setOptions({ imageOrientation: 'flipY', premultiplyAlpha: 'none',
      colorSpaceConversion: 'none' });
    this.exists = index.levels.map(l => {
      const bytes = Uint8Array.from(atob(l.exists_bitmask_b64), c => c.charCodeAt(0));
      return { ...l, has: (x, y) => { const i = y * l.cols + x; return (bytes[i >> 3] >> (7 - (i & 7))) & 1; } };
    });
    this.frame = 0;
    this.loadGrid();
  }

  // Regional threshold grid; until it loads (or if missing) coverage is 0 everywhere.
  async loadGrid() {
    const r = await fetch(GRID_URL);
    if (!r.ok) return;
    const d = await r.json(), e = d.extent;
    // Same loader as the tiles: flipY (texture row 0 = south), no premultiplied alpha.
    const img = await this.loader.loadAsync(GRID_URL.replace(/[^/]+$/, d.png));
    const tex = new THREE.Texture(img);
    tex.magFilter = tex.minFilter = THREE.LinearFilter;
    tex.generateMipmaps = false;
    tex.premultiplyAlpha = false;
    tex.needsUpdate = true;
    this.uniforms.uGrid.value = tex;
    this.uniforms.uGridBox.value.set(e.west, e.north, e.east, e.south);
    this.uniforms.uThresh.value.set(d.epochs['2015'].fallback_grey_threshold / 255,
      d.epochs['2025'].fallback_grey_threshold / 255);
    if (d.share_png) {  // PROTOTYPE colour modes (loaded always so dev can switch uMode live)
      const s = new THREE.Texture(await this.loader.loadAsync(GRID_URL.replace(/[^/]+$/, d.share_png)));
      s.magFilter = s.minFilter = THREE.LinearFilter; s.generateMipmaps = false; s.premultiplyAlpha = false;
      s.needsUpdate = true;
      this.uniforms.uShare.value = s;
      this.uniforms.uFbShare.value.set(d.epochs['2015'].fallback_white_share, d.epochs['2025'].fallback_white_share);
    }
  }

  // Geographic bounds of a tile, clipped to the raster extent; plus matching UVs.
  bounds(level, x, y) {
    const { tile_size: T, origin_lon, origin_lat, native_pixel_deg: d, raster_width: W,
      raster_height: H, max_level } = this.ix;
    const span = T * d * 2 ** (max_level - level);
    const west = origin_lon + x * span, north = origin_lat - y * span;
    const east = Math.min(west + span, origin_lon + W * d);
    const south = Math.max(north - span, origin_lat - H * d);
    return { west, east, north, south, u1: (east - west) / span, v0: 1 - (north - south) / span };
  }

  makeGeometry(b) {
    const nx = Math.max(2, Math.ceil((b.east - b.west) / 2));
    const ny = Math.max(2, Math.ceil((b.north - b.south) / 2));
    const pos = [], uv = [], ll = [], idx = [];
    for (let j = 0; j <= ny; j++) {
      for (let i = 0; i <= nx; i++) {
        const lng = b.west + (b.east - b.west) * i / nx;
        const lat = b.north - (b.north - b.south) * j / ny;
        const p = toXYZ(lat, lng, this.radius);
        pos.push(p.x, p.y, p.z);
        uv.push(b.u1 * i / nx, 1 - (1 - b.v0) * j / ny);
        ll.push(lng, lat);
      }
    }
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const a = j * (nx + 1) + i, c = a + nx + 1;
        idx.push(a, c, a + 1, a + 1, c, c + 1);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setAttribute('lonlat', new THREE.Float32BufferAttribute(ll, 2));
    g.setIndex(idx);
    g.computeBoundingSphere();
    return g;
  }

  // Finest level whose texels are no smaller than one screen pixel at the view centre.
  levelFor(camera, heightPx) {
    return this.levelAt(camera.position.length() - this.radius, camera.fov, heightPx);
  }
  // The same for a camera `dist` above the tile surface with vertical field of view `fov` (degrees).
  levelAt(dist, fov, heightPx) {
    const screenPx = dist * 2 * Math.tan(fov * DEG / 2) / heightPx;
    const nativeTexel = this.radius * this.ix.native_pixel_deg * DEG;
    const steps = Math.max(0, Math.floor(Math.log2(screenPx / nativeTexel)));
    return Math.max(0, this.ix.max_level - steps - LEVEL_BIAS);
  }

  // No finer tiles mid-flight (human, AI_LOG Experience refinement step 8, option D): during a story flight of `ms` to a
  // camera `altitude` (globe radii above the surface), the level stays ≤ the coarser of the start and end levels, so it
  // never refines on the way (zooming in: the start level until arrival, then one refinement; zooming out: the end
  // level from the start). Never finer than levelFor, so a wide view never asks for fine tiles.
  capFlight(camera, heightPx, altitude, ms) {
    this.capLevel = Math.min(this.levelFor(camera, heightPx), this.levelAt(altitude * this.radius / 1.0005, camera.fov, heightPx));
    this.capUntil = performance.now() + ms;
  }

  // Camera moved (main.js refresh): 4-sample shading on, off again AA_IDLE ms after the last move (MOVE_AA).
  moved() {
    if (!MOVE_AA) return;
    this.aaTarget = 1;
    clearTimeout(this.aaTimer);
    this.aaTimer = setTimeout(() => { this.aaTarget = 0; this.easeAA(); }, AA_IDLE);
    this.easeAA();
  }
  easeAA() {
    if (this.aaFrame) return;
    this.aaLast = performance.now();
    const tick = now => {
      const u = this.uniforms.uAA, d = this.aaTarget - u.value, dt = now - this.aaLast;
      this.aaLast = now;
      u.value += Math.sign(d) * Math.min(Math.abs(d), dt / (d > 0 ? AA_IN : AA_OUT));
      this.aaFrame = u.value === this.aaTarget ? 0 : requestAnimationFrame(tick);
    };
    this.aaFrame = requestAnimationFrame(tick);
  }

  update(camera, heightPx) {
    this.frame++;
    const level = Math.min(this.levelFor(camera, heightPx), performance.now() < this.capUntil ? this.capLevel : Infinity);
    const camPos = camera.position, camLen = camPos.length();
    const horizon = Math.acos(Math.min(1, this.radius / camLen));
    const frustum = new THREE.Frustum().setFromProjectionMatrix(
      new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse));
    // Load a fallback level (FALLBACK_STEPS coarser) first, then the target level, so
    // tiles still loading show a nearby coarser tile rather than the level-0 backdrop.
    const fallback = Math.max(0, level - FALLBACK_STEPS);
    const wanted = [];
    for (const lv of fallback === level ? [level] : [fallback, level]) {
      const L = this.exists[lv];
      const span = this.ix.tile_size * this.ix.native_pixel_deg * 2 ** (this.ix.max_level - lv);
      for (let y = 0; y < L.rows; y++) {
        for (let x = 0; x < L.cols; x++) {
          const b = this.bounds(lv, x, y);
          const c = toXYZ((b.north + b.south) / 2, (b.west + b.east) / 2, this.radius);
          const angR = Math.min(Math.PI, span * DEG);  // generous angular radius
          if (c.angleTo(camPos) > horizon + angR) continue;
          const rad = Math.min(2 * this.radius, this.radius * span * DEG);
          if (!frustum.intersectsSphere(new THREE.Sphere(c, rad))) continue;
          const key = `${lv}/${x}/${y}`;
          if (L.has(x, y)) wanted.push({ key, level: lv, x, y, d: c.distanceTo(camPos) });
          else if (lv === level) this.markEmpty(key, lv, b);
        }
      }
    }
    wanted.sort((a, b) => a.level - b.level || a.d - b.d);  // fallback level first
    // Level 0 (one tile) is always kept as a last-resort backdrop; loaded first.
    for (let x = 0; x < this.exists[0].cols; x++) {
      if (this.exists[0].has(x, 0)) wanted.unshift({ key: `0/${x}/0`, level: 0, x, y: 0, d: 0 });
    }
    this.queue = wanted.filter(t => !this.tiles.has(t.key) && !this.loading.has(t.key));
    for (const t of wanted) { const e = this.tiles.get(t.key); if (e) e.used = this.frame; }
    // Show loaded tiles at or above (coarser than) the target level; finer ones hide.
    for (const e of this.tiles.values()) e.mesh.visible = e.level <= level;
    this.pump();
    this.evict();
  }

  // A tile skipped by the pipeline (measured 0 in both years) is drawn black at its
  // own level, so coarser backdrop tiles (block means) do not show through it.
  markEmpty(key, level, b) {
    const e = this.tiles.get(key);
    if (e) { e.used = this.frame; return; }
    if (!this.emptyMats) this.emptyMats = [];
    const mat = this.emptyMats[level] ??= new THREE.MeshBasicMaterial({ color: 0x000000,
      polygonOffset: true, polygonOffsetFactor: -level, polygonOffsetUnits: -4 * level });
    const mesh = new THREE.Mesh(this.makeGeometry(b), mat);
    mesh.renderOrder = level;
    this.group.add(mesh);
    this.tiles.set(key, { mesh, level, used: this.frame, empty: true });
  }

  pump() {
    while (this.loading.size < MAX_LOADING && this.queue.length) {
      const t = this.queue.shift();
      this.loading.add(t.key);
      this.loader.load(`${this.baseUrl}${t.key}.webp`, bitmap => {
        this.loading.delete(t.key);
        const tex = new THREE.Texture(bitmap);
        tex.colorSpace = THREE.NoColorSpace;
        tex.flipY = false;  // flipped by the ImageBitmap options
        tex.magFilter = tex.minFilter = THREE.NearestFilter;  // exact bytes, no blending of flags
        tex.generateMipmaps = false;
        tex.needsUpdate = true;
        const mat = new THREE.ShaderMaterial({
          uniforms: { ...this.uniforms, map: { value: tex } }, vertexShader, fragmentShader,
          polygonOffset: true, polygonOffsetFactor: -t.level, polygonOffsetUnits: -4 * t.level,
        });
        const mesh = new THREE.Mesh(this.makeGeometry(this.bounds(t.level, t.x, t.y)), mat);
        mesh.renderOrder = t.level;
        this.group.add(mesh);
        this.tiles.set(t.key, { mesh, level: t.level, used: this.frame });
        this.pump();
      }, undefined, () => { this.loading.delete(t.key); this.pump(); });
    }
  }

  evict() {
    if (this.tiles.size <= MAX_CACHED) return;
    const old = [...this.tiles.entries()].filter(([, e]) => e.level > 2)
      .sort((a, b) => a[1].used - b[1].used).slice(0, this.tiles.size - MAX_CACHED);
    for (const [key, e] of old) {
      this.group.remove(e.mesh);
      e.mesh.geometry.dispose();
      if (!e.empty) {
        e.mesh.material.uniforms.map.value.image.close?.();
        e.mesh.material.uniforms.map.value.dispose();
        e.mesh.material.dispose();
      }
      this.tiles.delete(key);
    }
  }

  setSwipe(xDevicePx) { this.uniforms.uSwipeX.value = xDevicePx; }
}
