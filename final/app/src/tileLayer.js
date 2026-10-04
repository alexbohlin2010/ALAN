// Our own tile mesh for the native-pyramid radiance tiles (see tiles.json and
// pipeline/radiance/05_build_tiles.py). Added to globe.gl's scene via .scene().
// Each tile holds both years: R = grey 2015, G = grey 2025, B = flags.
// The swipe shader picks the year per screen pixel from one uniform.
import * as THREE from 'three';

const DEG = Math.PI / 180;
const MAX_LOADING = 12;
const MAX_CACHED = 600;
const FALLBACK_STEPS = 3;  // fallback texels are 8x the target's

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
const RAMP_TINTS = [[1.0, 0.5529, 0.0838], [1.0, 0.8317, 0.649]];  // 2000 K, 4000 K
const RAMP_THRESHOLDS = [248, 219];  // grey levels, 2015, 2025
const RAMP_BLEND = 8;
const fragmentShader = /* glsl */`
  uniform sampler2D map;
  uniform float uSwipeX;      // divider position in device pixels
  uniform vec3 uNoDataColor;  // display choice for "no data" (-1.5), labelled in legend
  uniform vec3 uTints[2];     // display ramp tints: sodium, white
  uniform vec2 uThresh;       // grey threshold (0-1) per year: x = 2015, y = 2025
  uniform float uBlend;       // blend half-width (0-1)
  uniform sampler2D uGrid;    // regional thresholds + coverage (see GRID_URL)
  uniform vec4 uGridBox;      // west, north, east, south of the grid's outer cell edges
  varying vec2 vUv;
  varying vec2 vLonLat;
  void main() {
    vec3 t = texture2D(map, vUv).rgb;
    int flags = int(t.b * 255.0 + 0.5);
    if ((flags & 4) != 0) discard;                  // outside the raster
    bool early = gl_FragCoord.x < uSwipeX;          // left of divider = 2015
    float g = early ? t.r : t.g;
    bool noData = (flags & (early ? 1 : 2)) != 0;
    vec2 gu = vec2((vLonLat.x - uGridBox.x) / (uGridBox.z - uGridBox.x),
                   1.0 - (uGridBox.y - vLonLat.y) / (uGridBox.y - uGridBox.w));
    vec4 cell = (gu.x >= 0.0 && gu.x <= 1.0 && gu.y >= 0.0 && gu.y <= 1.0)
      ? texture2D(uGrid, gu) : vec4(0.0);
    float thr = mix(early ? uThresh.x : uThresh.y, early ? cell.r : cell.g, early ? cell.b : cell.a);
    float w = smoothstep(-uBlend, uBlend, g - thr);
    vec3 c = g * mix(uTints[0], uTints[1], w);
    gl_FragColor = vec4(noData ? uNoDataColor : c, 1.0);
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
    };
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
    const dist = camera.position.length() - this.radius;
    const screenPx = dist * 2 * Math.tan(camera.fov * DEG / 2) / heightPx;
    const nativeTexel = this.radius * this.ix.native_pixel_deg * DEG;
    const steps = Math.max(0, Math.floor(Math.log2(screenPx / nativeTexel)));
    return Math.max(0, this.ix.max_level - steps);
  }

  update(camera, heightPx) {
    this.frame++;
    const level = this.levelFor(camera, heightPx);
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
