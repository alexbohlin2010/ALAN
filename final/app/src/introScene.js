// PROTOTYPE intro scene (human: option B, intro scene task 2026-10-04), behind the URL switch ?intro=sunrise.
// Sequence: dark, barely visible globe -> a sun rises behind it (glow on the limb) -> the night lights fade in.
// Added to globe.gl's scene via .scene() (like the tile layer) and removed when the intro ends, so later
// steps are unchanged. Glow colours, sun position and timings are display choices, not data.
import * as THREE from 'three';

// Default since 2026-10-04 (human: "bring the sunrise intro into the primary app"); ?intro=css gives the old CSS intro.
export const INTRO_MODE = new URLSearchParams(location.search).get('intro') ?? 'sunrise';

// Timeline in ms (prototype values, open for the human), in music time (ms from the start of the recording).
// Text and lights fade lengths come from the story step's timing (app/content/story.js: textIn, textOut, lightsIn).
// Measured in the browser (narrow pitch bands, AI_LOG intro scene task step 9; earlier loudness-only readings in
// steps 5-8 mislabelled a low-register swell at ~3.6 s as the trumpet): first trumpet call C 12.0 s, G 14.0 s,
// high C 16.0 s; chord 20.0 s (E major -> E-flat minor to ~25 s); timpani strokes ~24.0-28.9 s; second trumpet
// call from ~29.0 s (human: "the horn comes in at almost 29s").
// Human decisions (steps 5-9): lights fade in with the chord; the text is precisely timed and fades only when the
// sun appears; the sun rises after the text; the music plays through the drum sequence after full light and
// stops before the next horn; shorter formless start; whole sequence about 25 s or less.
// Human (step 10): music starts 10 s in (formless ~2 s); cut 0.05 s earlier (28.88-28.98 s, a trace of horn was
// audible); a "Use keys to navigate" hint before the text; a mute button (top right) instead of a second Begin.
// Agent sync choices: text in on the first trumpet C; the sun's core clears the limb on the high C (text fade starts
// on that frame); hint 10.2-11.8 s. Click -> silence ~19 s.
const T = { start: 10000, fadeIn: 600, ring: 600, hint: 10200, hintOff: 13800, hintFade: 300, text: 16000,
  sunAppear: 16000, lights: 20000, glowOut: 3500, musicEnd: 28850, musicOut: 1500 };   // human (steps 12-13): 0.05 s earlier twice more
// Human (step 14): smoother close-out (static heard). The fades now run in Web Audio (a GainNode with a raised-cosine
// curve, sample-accurate) instead of stepping audio.volume once per frame; the music pauses only after silence.
// Close-out 27.35 -> 28.85 s (human, step 15: drag the fade out; agent choice 1.5 s, same end point).
// Human (step 11): cut 0.03 s earlier (28.85-28.95 s); the sun moves at a constant speed (one angular rate from
// the music start, through its appearance on the high C, until the glow has faded; constant on screen); hint with arrow-key icons near
// the bottom; mute button as an audio icon.
const HINT = 'Use keys to navigate';   // human's wording
// Human (2026-10-04): MacLeod recording (app/public/audio/MANIFEST.md, CC BY 3.0, credit required);
// the site opens with a "Begin / with audio" button; the globe turns from the intro until India.
const AUDIO_URL = '/audio/zarathustra_einleitung_macleod.ogg';
// Human (intro soundscape task 2026-10-04): after Begin, ~4 s of night crickets on the black screen before the
// music; the crickets play on at full level under the music and fade to nothing as the lights fade in (option A,
// "drowned out gradually"). Recording: KikeVilaplana, freesound 436528, CC0 (app/public/audio/MANIFEST.md).
// The music element already plays (silent) from T.start - PRE, so the music clock drives the whole pre-roll and
// the music is started inside the Begin click (autoplay rules). Cricket fade-in 0.5 s: agent choice.
const CRICKETS_URL = '/audio/436528__kikevilaplana__night-ambience-with-crickets.wav';
const PRE = 2000, CRICKETS_IN = 500;   // human (soundscape step 7): dark cricket screen 4 s -> 2 s
// Human (soundscape step 6): crickets fade out faster (agent value 3 s, was 6 s with the lights), from the moment the
// lights start (chord, T.lights); text in later (agent choice: the high C, 16.0 s; was the first trumpet C, 12.0 s)
// and out exactly when the lights come in; the sun sprite removed ("looks too fake"), the halo kept.
// Human (step 8): crickets gone by the time the lights hit, fading from halfway through the text (16.0-20.0 s):
// 18.0 -> 20.0 s, ending exactly at T.lights.
const CRICKETS_OUT = 2000, SHOW_SUN = false;
// Background hum in C (human, AI_LOG Copy editing step 8: "faded in after the intro"). Made in Web Audio, no file:
// the root C as two sines ±4 cents, its octave and double octave, optional fifth G, low-passed, optional slow
// breathing, plus soft brown noise. Values = the human's test-page settings (step 9: "Lower frequency will cause less
// stress"): volume 100%, C1 (32.7 Hz), warmth 2000 Hz, fifth 0%, breathing 0%, soft noise 50%. Step 10: volume 50%, soft noise 35%.
// Fades in over HUM_IN while the music fades out (agent choice), then plays on under the story; the mute covers it.
const HUM = { base: 32.703, cutoff: 2000, level: 0.175, breathe: 0.09, depth: 0, fifth: 0, noise: 0.175 }, HUM_IN = 3000;
const ROTATE_SPEED = 0.2;   // OrbitControls autoRotateSpeed: 6 x speed deg/s (frame-rate independent) = 1.2 deg/s
const SUN_END = new THREE.Vector3(0.62, 0.36, -0.7).normalize();  // view space: right, up, behind
// Sun direction at path fraction e (0 = straight behind the globe, 1 = SUN_END; e > 1 continues on the same arc):
// a rotation at one angular rate, so a linear e gives a constant speed.
const SUN_START = new THREE.Vector3(0, 0, -1);
const SUN_AXIS = new THREE.Vector3().crossVectors(SUN_START, SUN_END).normalize();
const SUN_ARC = SUN_START.angleTo(SUN_END);
const sunDir = (e, out) => out.copy(SUN_START).applyAxisAngle(SUN_AXIS, e * SUN_ARC);
const COLOR_NEAR = new THREE.Color(1.0, 0.72, 0.38);  // display choice: warm, near the sun
const COLOR_FAR = new THREE.Color(0.30, 0.42, 0.85);  // display choice: cool, rest of the limb

const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };

// Halo outside the limb: a back-side shell; each fragment's glow depends on how far its view ray
// passes above the globe's edge and on its angle to the sun direction (all in view space).
const haloVert = /* glsl */`
  varying vec3 vPos;
  void main() {
    vec4 p = modelViewMatrix * vec4(position, 1.0);
    vPos = p.xyz;
    gl_Position = projectionMatrix * p;
  }`;
const haloFrag = /* glsl */`
  uniform vec3 uCenter;   // globe centre, view space
  uniform float uR;       // globe radius
  uniform vec3 uSun;      // sun direction, view space (z < 0 = behind the globe)
  uniform float uBase;    // faint even ring (formless stage)
  uniform float uRise;    // sun-side glow strength
  uniform vec3 uNear;
  uniform vec3 uFar;
  varying vec3 vPos;
  void main() {
    vec3 d = normalize(vPos);
    vec3 off = d * dot(uCenter, d) - uCenter;     // closest approach of the view ray to the centre
    float b = length(off);
    float h = max(b - uR, 0.0) / uR;              // height above the limb, in globe radii
    vec2 dir = off.xy / max(b, 1e-5);
    float l = length(uSun.xy);
    float ang = l > 1e-4 ? dot(normalize(dir), uSun.xy / l) : 0.0;
    float focus = pow(0.5 + 0.5 * ang, mix(1.0, 10.0, l));
    float ring = uBase * exp(-h / 0.025);
    float glow = uRise * focus * (exp(-h / 0.02) + 0.45 * exp(-h / 0.12));
    vec3 c = ring * uFar + glow * mix(uFar, uNear, focus);
    gl_FragColor = vec4(c, 1.0);
  }`;

// Thin crescent on the globe's own edge, on the sun side (front-side shell just above the surface).
const rimVert = /* glsl */`
  varying vec3 vN;
  varying vec3 vPos;
  void main() {
    vN = normalize(normalMatrix * normal);
    vec4 p = modelViewMatrix * vec4(position, 1.0);
    vPos = p.xyz;
    gl_Position = projectionMatrix * p;
  }`;
const rimFrag = /* glsl */`
  uniform vec3 uSun;
  uniform float uRise;
  uniform vec3 uNear;
  varying vec3 vN;
  varying vec3 vPos;
  void main() {
    float fres = pow(1.0 - max(dot(vN, -normalize(vPos)), 0.0), 5.0);
    float lit = smoothstep(-0.15, 0.45, dot(vN, uSun));
    gl_FragColor = vec4(uNear * fres * lit * uRise * 0.8, 1.0);
  }`;

function sunTexture() {   // radial gradient drawn in code (no image asset)
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d'), r = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  r.addColorStop(0, 'rgba(255,250,235,1)');
  r.addColorStop(0.08, 'rgba(255,230,180,0.9)');
  r.addColorStop(0.25, 'rgba(255,170,90,0.25)');
  r.addColorStop(1, 'rgba(255,120,40,0)');
  g.fillStyle = r;
  g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function createIntroScene({ globe, layer }) {
  const R = globe.getGlobeRadius();
  const additive = { transparent: true, depthWrite: false, blending: THREE.AdditiveBlending };
  const shared = { uSun: { value: new THREE.Vector3(0, 0, -1) }, uRise: { value: 0 },
    uNear: { value: COLOR_NEAR }, uFar: { value: COLOR_FAR } };
  const haloU = { ...shared, uCenter: { value: new THREE.Vector3() }, uR: { value: R }, uBase: { value: 0 } };
  const halo = new THREE.Mesh(new THREE.SphereGeometry(R * 1.35, 96, 64), new THREE.ShaderMaterial({
    uniforms: haloU, vertexShader: haloVert, fragmentShader: haloFrag, side: THREE.BackSide, ...additive }));
  const rim = new THREE.Mesh(new THREE.SphereGeometry(R * 1.002, 96, 64), new THREE.ShaderMaterial({
    uniforms: shared, vertexShader: rimVert, fragmentShader: rimFrag, ...additive }));
  const sun = new THREE.Sprite(new THREE.SpriteMaterial({ map: sunTexture(), ...additive, opacity: 0 }));
  sun.scale.setScalar(R * 1.6);
  halo.renderOrder = rim.renderOrder = sun.renderOrder = 100;   // after the tiles (renderOrder = level)
  const group = new THREE.Group();
  group.add(halo, rim);
  if (SHOW_SUN) group.add(sun);

  let raf = null, overlay = null, begun = false, fadeId = 0;
  let eAppear = 0.3;   // sun elevation at which its core clears the limb (still paces the glow)
  const audio = new Audio(AUDIO_URL);
  audio.preload = 'auto';
  const crickets = new Audio(CRICKETS_URL);
  crickets.preload = 'auto';
  let cricketGain = null, cricketsOff = false, cricketsId = 0;
  // Web Audio graph (built on the Begin click, a user gesture): element -> fade gain -> mute gain -> speakers.
  let ctx = null, fade = null, muteGain = null, muted = false, pauseAt = Infinity;
  function ensureGraph() {
    if (ctx) return;
    try {
      ctx = new AudioContext();
      fade = ctx.createGain();
      muteGain = ctx.createGain();
      muteGain.gain.value = muted ? 0 : 1;
      ctx.createMediaElementSource(audio).connect(fade).connect(muteGain).connect(ctx.destination);
      cricketGain = ctx.createGain();
      ctx.createMediaElementSource(crickets).connect(cricketGain).connect(muteGain);   // one mute for both
    } catch { ctx = null; }   // no Web Audio: plays without fades
    ctx?.resume();
  }
  // Hum graph (built once, silent until startHum): sines -> low-pass -> breathing gain -> humGain -> mute.
  let humGain = null;
  // Story steps with `humOff` (Conclusion) fade the hum out; other steps bring it back (human, AI_LOG Copy editing
  // step 11). Only acts once the hum has started; fade 2.5 s = the Conclusion's lights-out (DARK_MS; agent choice).
  let humOff = false;
  function humFor(step) {
    const off = Boolean(step.humOff);
    if (!humGain || off === humOff) return;
    humOff = off;
    if (off) ramp(0, DARK_MS, 0, undefined, humGain.gain); else startHum();
  }
  // Built on first use; later calls only fade it back in (after a replayed intro, human step 9).
  function startHum(delayMs = 0) {
    if (!ctx) return;
    if (humGain) { ramp(HUM.level, HUM_IN, delayMs, undefined, humGain.gain); return; }
    humGain = ctx.createGain();
    humGain.gain.value = 0;
    const filter = ctx.createBiquadFilter(), body = ctx.createGain(), lfo = ctx.createOscillator(), depth = ctx.createGain();
    filter.type = 'lowpass'; filter.frequency.value = HUM.cutoff; filter.Q.value = 0.5;
    lfo.frequency.value = HUM.breathe; depth.gain.value = HUM.depth;
    lfo.connect(depth).connect(body.gain); lfo.start();
    filter.connect(body).connect(humGain).connect(muteGain);
    for (const [ratio, gain, detune] of [[1, 0.5, -4], [1, 0.5, 4], [2, 0.25, 0], [4, 0.06, 0], [3, 0.22 * HUM.fifth, 0]]) {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.frequency.value = HUM.base * ratio; o.detune.value = detune; g.gain.value = gain;
      o.connect(g).connect(filter); o.start();
    }
    if (HUM.noise) {   // brown noise: integrated white noise, 4 s loop, low-passed at 400 Hz (as on the test page)
      const len = ctx.sampleRate * 4, buf = ctx.createBuffer(1, len, ctx.sampleRate), d = buf.getChannelData(0);
      for (let i = 0, last = 0; i < len; i++) { last = (last + 0.02 * (Math.random() * 2 - 1)) / 1.02; d[i] = last * 3.5; }
      const src = ctx.createBufferSource(), nf = ctx.createBiquadFilter(), ng = ctx.createGain();
      src.buffer = buf; src.loop = true; nf.type = 'lowpass'; nf.frequency.value = 400; ng.gain.value = HUM.noise;
      src.connect(nf).connect(ng).connect(humGain); src.start();
    }
    ramp(HUM.level, HUM_IN, delayMs, 0, humGain.gain);
    mute.hidden = false;   // the mute stays available while the hum plays
  }
  // Raised-cosine ramp of the fade gain from its current value to `to` over `ms`, starting `delayMs` from now.
  // `g` defaults to the music's fade gain (cricketGain.gain for the crickets).
  function ramp(to, ms, delayMs = 0, from, g = fade?.gain) {
    if (!ctx) return;
    from ??= g.value;
    const t = ctx.currentTime + Math.max(0, delayMs) / 1000;
    const curve = Float32Array.from({ length: 64 }, (_, i) => to + (from - to) * (0.5 + 0.5 * Math.cos(Math.PI * i / 63)));
    g.cancelScheduledValues(ctx.currentTime);
    g.setValueAtTime(from, ctx.currentTime);
    g.setValueCurveAtTime(curve, t, ms / 1000);
  }
  // Pause only after the fade has reached silence (checked on the music clock).
  const watchPause = () => {
    if (audio.paused || pauseAt === Infinity) return;
    if (audio.currentTime * 1000 >= pauseAt) { audio.pause(); pauseAt = Infinity; atPause?.(); atPause = null; }
    else requestAnimationFrame(watchPause);
  };
  // Called once when the music's tail has faded to silence (human, AI_LOG Copy editing step 8: the next step starts
  // on its own at the end of the music). Cleared when the music is faded out early (skip).
  let atPause = null, onEnd = null;
  if (import.meta.env.DEV) window.introAudio = audio;   // dev-only handle for inspection
  if (import.meta.env.DEV) window.introGain = () => fade?.gain.value;   // dev-only
  if (import.meta.env.DEV) window.introCrickets = () => [crickets.paused, crickets.currentTime, cricketGain?.gain.value];   // dev-only
  if (import.meta.env.DEV) window.introSun = sun;       // dev-only handle for inspection
  if (import.meta.env.DEV) window.introHum = () => [humGain?.gain.value, muted];   // dev-only
  // Clock: the music's own time while it plays (keeps the lights on the swell), else wall time.
  const clock = t0 => (begun && !audio.paused && audio.currentTime > 0 ? audio.currentTime * 1000
    : T.start - PRE + performance.now() - t0);
  const cam = globe.camera(), q = new THREE.Quaternion(), tmp = new THREE.Vector3();
  const hint = Object.assign(document.createElement('div'), { className: 'hint',
    innerHTML: `<kbd aria-label="Left arrow">←</kbd><kbd aria-label="Right arrow">→</kbd><span>${HINT}</span>` });
  // Mute button (top right): shown on the Begin screen and while the music plays; muting keeps the music clock
  // running, so unmuting comes back in sync.
  const mute = Object.assign(document.createElement('button'), { id: 'mute', hidden: true });
  // Speaker icon (inline SVG, no asset); waves when on, a cross when muted.
  const SPEAKER = '<path d="M3 9v6h4l5 4V5L7 9H3z" fill="currentColor"/>';
  const ICON_ON = SPEAKER + '<path d="M15.5 8.5a5 5 0 0 1 0 7M18 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>';
  const ICON_OFF = SPEAKER + '<path d="M16 9l5 6M21 9l-5 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>';
  const label = () => {
    mute.innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">${muted ? ICON_OFF : ICON_ON}</svg>`;
    mute.setAttribute('aria-label', muted ? 'Unmute audio' : 'Mute audio');
    mute.title = muted ? 'Unmute audio' : 'Mute audio';
    mute.setAttribute('aria-pressed', String(muted));
  };
  // Explore mutes the hum on arrival; the viewer can switch it back on (human, AI_LOG Copy editing step 9).
  function setMuted(m) {
    if (m === muted) return;
    muted = m;
    if (ctx) muteGain.gain.setTargetAtTime(muted ? 0 : 1, ctx.currentTime, 0.03);   // short smooth mute, no click
    else audio.muted = crickets.muted = muted;   // no Web Audio (frame() also keeps the music muted in the pre-roll)
    label();
  }
  mute.addEventListener('click', () => setMuted(!muted));
  audio.addEventListener('play', () => { mute.hidden = false; });
  audio.addEventListener('pause', () => { mute.hidden = !humGain; });
  label();

  function frame(t, step, text, done) {
    const tm = step.timing;
    // Sun elevation 0 (behind) .. 1: pre-dawn up to eAppear (core at the limb) on the high C, then higher.
    // Constant on-screen speed: distance along the projected path grows linearly from the music start and
    // reaches the appearance point (core at the limb) on the high C.
    const e = pathE(pathLen(eAppear) * Math.max(0, t - T.start) / (T.sunAppear - T.start));
    const out = 1 - smooth(T.lights + tm.lightsIn - T.glowOut, T.lights + tm.lightsIn, t);
    haloU.uBase.value = 0.18 * smooth(T.start, T.start + T.ring, t) * out;
    shared.uRise.value = (0.6 * smooth(T.start, T.sunAppear, t) + 0.4 * smooth(T.sunAppear, T.lights, t)) * out;
    const s = sunDir(e, shared.uSun.value);
    // Sun sprite far behind the globe along the sun direction; the globe hides it until it clears the edge.
    cam.updateMatrixWorld();
    haloU.uCenter.value.set(0, 0, 0).applyMatrix4(cam.matrixWorldInverse);
    cam.getWorldQuaternion(q);
    sun.position.copy(tmp.copy(s).applyQuaternion(q)).multiplyScalar(R * 4);
    sun.material.opacity = smooth(0.6 * eAppear, eAppear, e) * out;
    hint.style.opacity = Math.min(smooth(T.hint, T.hint + T.hintFade, t), 1 - smooth(T.hintOff - T.hintFade, T.hintOff, t));
    text.style.opacity = Math.min(smooth(T.text, T.text + tm.textIn, t), 1 - smooth(T.lights, T.lights + tm.textOut, t));
    // Human (soundscape step 7): lights rise at once from the chord (front-loaded ease-out, agent choice: cubic;
    // ~42% after 1 s) instead of the slow S-curve (~8% after 1 s); start and length unchanged.
    const lit = Math.min(1, Math.max(0, (t - T.lights) / tm.lightsIn));
    layer.uniforms.uFade.value = 1 - (1 - lit) ** 3;
    if (ctx && !cricketsOff && t >= T.lights - CRICKETS_OUT) {   // the lights drown the crickets out
      cricketsOff = true;
      ramp(0, Math.max(50, T.lights - t), 0, undefined, cricketGain.gain);
    }
    if (!ctx) {   // no Web Audio: music silent during the pre-roll; crickets drowned out by volume steps
      audio.muted = muted || t < T.start;
      crickets.volume = 1 - smooth(T.lights - CRICKETS_OUT, T.lights, t);
    }
    if (t >= T.lights + tm.lightsIn) { cancelAnimationFrame(raf); raf = null; stop(); tail(); done(); }
  }

  function play(step, { overlay: ov, text, done, end }) {
    stop();
    onEnd = end;
    if (humGain) ramp(0, 600, 0, undefined, humGain.gain);   // back to the intro: the hum fades out (human, step 9)
    overlay = ov;
    overlay.style.background = 'transparent';   // only the text layer; the scene shows through
    overlay.append(hint);
    hint.style.opacity = 0;
    overlay.style.transition = 'none';
    overlay.style.opacity = 1;
    text.style.transition = 'none';
    text.style.opacity = 0;
    layer.uniforms.uFade.value = 0;
    // Start east of the step's camera by the turn made before the lights, so the lights fade in on that view.
    globe.pointOfView({ ...step.camera, lng: step.camera.lng + 6 * ROTATE_SPEED * (T.lights - T.start + PRE) / 1000 }, 0);
    globe.scene().add(group);
    eAppear = appearElevation(R * (1 + step.camera.altitude));
    buildPath(R * (1 + step.camera.altitude));
    if (begun) {   // silent fallback if play() is refused
      fadeId++; pauseAt = Infinity; cricketsOff = false; cricketsId++;
      if (ctx) { fade.gain.cancelScheduledValues(ctx.currentTime); fade.gain.setValueAtTime(0, ctx.currentTime); }
      audio.currentTime = (T.start - PRE) / 1000;   // silent pre-roll on the music clock
      // Music fade-in scheduled from where the music actually is once it plays.
      const id = fadeId;   // skipped before play() resolved: no fade-in
      audio.play().then(() => { if (id === fadeId) ramp(1, T.fadeIn, T.start - audio.currentTime * 1000, 0); }).catch(() => {});
      crickets.currentTime = 0;
      if (ctx) ramp(1, CRICKETS_IN, 0, 0, cricketGain.gain); else crickets.volume = 1;
      crickets.play().catch(() => {});
    }
    const t0 = performance.now();
    const tick = () => { raf = requestAnimationFrame(tick); frame(clock(t0), step, text, done); };
    raf = requestAnimationFrame(tick);
  }

  // Is the sun sprite's bright core outside the globe's disk? (view-space angles; d = camera-centre distance)
  const CORE = 0.08 * 0.8;   // core radius / R: gradient stop 0.08 of the sprite's half-size (scale 1.6 R)
  function sunVisible(s, d) {
    const z = d - 4 * R * s.z, xy = 4 * R * Math.hypot(s.x, s.y);   // s.z < 0: further away than the centre
    return Math.atan2(xy, z) + Math.atan2(CORE * R, z) > Math.asin(R / d);
  }
  function appearElevation(d) {   // bisection on the same rule, so the core clears the limb exactly at T.sunAppear
    let lo = 0, hi = 1;
    for (let k = 0; k < 30; k++) {
      const m = (lo + hi) / 2, s = sunDir(m, tmp);
      if (sunVisible(s, d)) hi = m; else lo = m;
    }
    return hi;
  }

  // Projected sun path (view-space x/z, y/z of the sprite centre) sampled over e, with cumulative length, so e can
  // be looked up from a distance travelled on screen.
  const PATH_N = 600, PATH_MAX = 4, pathL = new Float32Array(PATH_N + 1);
  function buildPath(d) {
    let px = 0, py = 0;
    for (let i = 0; i <= PATH_N; i++) {
      const s = sunDir(i / PATH_N * PATH_MAX, tmp), z = d - 4 * R * s.z;
      const x = 4 * R * s.x / z, y = 4 * R * s.y / z;
      pathL[i] = i ? pathL[i - 1] + Math.hypot(x - px, y - py) : 0;
      px = x; py = y;
    }
  }
  const pathLen = e => { const f = Math.min(PATH_N, e / PATH_MAX * PATH_N), i = Math.floor(f);
    return i >= PATH_N ? pathL[PATH_N] : pathL[i] + (pathL[i + 1] - pathL[i]) * (f - i); };
  function pathE(len) {   // inverse of pathLen (binary search + linear interpolation)
    let lo = 0, hi = PATH_N;
    if (len >= pathL[PATH_N]) return PATH_MAX;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (pathL[m] <= len) lo = m; else hi = m; }
    return (lo + (len - pathL[lo]) / Math.max(1e-9, pathL[hi] - pathL[lo])) / PATH_N * PATH_MAX;
  }

  function fadeOutAudio(ms) {
    if (audio.paused) return;
    fadeId++;
    atPause = null;
    if (!ctx) { audio.pause(); return; }
    ramp(0, ms);
    pauseAt = audio.currentTime * 1000 + ms + 30;
    watchPause();
  }

  // After full light the music plays on through the timpani, then fades to silence before the next horn call;
  // the fade is scheduled once on the audio clock (offset from the music clock), then the music pauses.
  function tail() {
    if (audio.paused) return;
    const id = ++fadeId, lead = T.musicEnd - T.musicOut - audio.currentTime * 1000;
    if (ctx) ramp(0, T.musicOut, lead);
    startHum(lead);   // hum fades in as the music fades out
    atPause = onEnd;
    pauseAt = T.musicEnd + 30;
    if (id === fadeId) watchPause();
  }

  // Skipping out of a running intro fades the music quickly; the tail after full light is left to finish.
  function stop() {
    const running = raf !== null;
    if (raf) cancelAnimationFrame(raf);
    raf = null;
    if (running) { fadeOutAudio(600); startHum(); }   // skipped mid-intro: the hum still comes in
    if (!crickets.paused) {   // crickets: short fade, then pause (the id guards against a newer play())
      const id = cricketsId;
      if (ctx) ramp(0, 600, 0, undefined, cricketGain.gain); else crickets.volume = 0;
      setTimeout(() => { if (id === cricketsId) crickets.pause(); }, 650);
    }
    globe.scene().remove(group);
    layer.uniforms.uFade.value = 1;
    hint.remove();
    if (overlay) overlay.style.background = '';
    overlay = null;
  }

  // Begin screen: the first click (a user gesture) is what lets the browser play the music.
  function begin(onBegin) {
    layer.uniforms.uFade.value = 0;
    const el = document.createElement('div');
    el.id = 'begin';
    el.innerHTML = '<button>Begin<small>with audio</small></button>';
    document.body.append(el, mute);
    mute.hidden = false;
    el.querySelector('button').addEventListener('click', () => {
      ensureGraph();
      begun = true;
      el.remove();
      onBegin();
    }, { once: true });
  }

  // Rotation: on for steps before the first step with a camera flight (India); leaves the camera alone
  // while it is already turning, so Statistic does not snap back to the intro view.
  function spin(i, steps) {
    const firstFly = steps.findIndex(s => s.fly);
    const controls = globe.controls(), was = controls.autoRotate;
    controls.autoRotate = firstFly < 0 || i < firstFly;
    controls.autoRotateSpeed = ROTATE_SPEED;
    return was && controls.autoRotate && i > 0;   // true = keep the current camera
  }

  return { play, stop, begin, spin, setMuted, humFor };
}

// Conclusion (human 2026-10-04, AI_LOG colour / design task step 7: "centered on the black globe, coming in as the
// artificial lights fade out ... bring the blue glow back"): set(true) fades the night lights out (tile uFade) and
// the intro's even blue limb ring (halo uBase, COLOR_FAR) in; set(false) reverses it. Display choices, not data:
// the radiance values are unchanged, only drawn at zero brightness. Duration and ring level are agent choices.
export const DARK_MS = 2500;
export function createDarkScene({ globe, layer }) {
  const R = globe.getGlobeRadius();
  const u = { uCenter: { value: new THREE.Vector3() }, uR: { value: R }, uBase: { value: 0 },
    uSun: { value: new THREE.Vector3(0, 0, -1) }, uRise: { value: 0 }, uNear: { value: COLOR_NEAR }, uFar: { value: COLOR_FAR } };
  const halo = new THREE.Mesh(new THREE.SphereGeometry(R * 1.35, 96, 64), new THREE.ShaderMaterial({
    uniforms: u, vertexShader: haloVert, fragmentShader: haloFrag, side: THREE.BackSide,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  halo.renderOrder = 100;   // after the tiles
  halo.onBeforeRender = (r, s, cam) => { cam.updateMatrixWorld(); u.uCenter.value.set(0, 0, 0).applyMatrix4(cam.matrixWorldInverse); };
  const RING = 0.18;   // same level as the intro's formless ring
  let level = 0, target = 0, raf = null, last = 0;
  function tick(now) {
    const dt = last ? now - last : 16;
    last = now;
    level += Math.sign(target - level) * Math.min(Math.abs(target - level), dt / DARK_MS);
    const k = smooth(0, 1, level);
    layer.uniforms.uFade.value = 1 - k;
    u.uBase.value = RING * k;
    if (level > 0 && !halo.parent) globe.scene().add(halo);
    if (level === target) {
      raf = null;
      if (level === 0) globe.scene().remove(halo);
      return;
    }
    raf = requestAnimationFrame(tick);
  }
  function set(on) {
    target = on ? 1 : 0;
    if (!raf && level !== target) { last = 0; raf = requestAnimationFrame(tick); }
  }
  return { set };
}
