# Philadelphia Spectral Perception 3D — Conversation Reference

## 1. Current project decision

Use **only the Philadelphia–Cherry Springs spectral irradiance dataset**.

Treat the two measurement sites as two separate experiences:

1. **Philadelphia urban site**
2. **Cherry Springs dark-rural site**

They must never be overlaid or mixed into one 3D space. A site selector may switch between two independently instantiated scenes, with the same visual grammar and controls.

## 2. Explicitly excluded sources

Do not use data from Hong Kong, Houston TEMPO, Madrid, New York City, Barcelona, ISS city photographs, ACTION Street Spectra, or Globe at Night.

Earlier dataset checks established that:

- Madrid's public files contain broadband SQM/TESS observations and AstMon B/V/R photometric bands, not downloadable continuous SAND spectra.
- Houston TEMPO provides useful mapped spectra, but the analyzed Houston observations are from 2024 and are not part of the current project.
- Hong Kong is also excluded despite providing ground-based spectra.

These notes are historical context only. They are not invitations to combine those datasets with the current project.

## 3. Verified Philadelphia–Cherry Springs dataset facts

- Physical quantity: calibrated **absolute downwelling spectral irradiance**.
- Spectral range: **280–840 nm**.
- Wavelength grid: **1 nm**.
- Temporal sampling: approximately **one spectrum per minute**.
- Collection period: **June–July 2014**.
- Usable spectra:
  - Philadelphia: approximately **3,199**.
  - Cherry Springs: approximately **3,192**.
- Measurement geometry: cosine-weighted collection over nearly the upper hemisphere, representing light arriving on a horizontal surface.
- Core comparison: urban Philadelphia versus dark-rural Cherry Springs.

The implementation must inspect the actual dataset files and schema before writing parsers. Do not assume column names, timestamp formats, missing-value codes, or exact physical units without reading the files and accompanying metadata.

## 4. Scientific boundary that must remain visible

The dataset has dimensions resembling **time × wavelength × irradiance**. It does **not** contain measured 3D coordinates for lamps, streets, animals, or individual light sources. It also does not resolve the arrival direction of each spectral component.

Therefore:

- The 3D particle field is an **abstract spectral/perceptual space**, not a reconstructed map of Philadelphia or Cherry Springs.
- Animal height, gaze direction, and flight paths are interaction and narrative devices.
- Camera position alone must not be presented as changing the measured exposure.
- The scientifically grounded species difference comes from weighting the same physical spectrum by species-specific spectral sensitivity curves.
- Do not claim that the data proves behavioral, ecological, or health effects.

## 5. Core visual concept

Create a navigable black 3D environment with:

- A pure or near-black background.
- Very subtle gray 3D axes and grid lines.
- A clean, frontal default 3D perspective: perspective projection, level horizon, no Dutch angle, and an axis-aligned/isometric-like composition.
- Minimal typography and restrained interface chrome.
- Luminous particles rendered with additive glow, while retaining enough contrast to perceive depth.

The experience has two connected representations.

### A. Physical Spectrum mode

First show the measured spectrum as a 3D spectral field or spectral curtain.

Recommended data-space axes:

- X = wavelength (280–840 nm)
- Y = irradiance, preferably with a documented linear/log toggle or a carefully labeled log transform
- Z = time or selected-spectrum index

Color encoding:

- Approximately 380–700 nm may use an approximate visible-spectrum-to-sRGB mapping.
- UV below the visible range and NIR above the visible range cannot be shown as literal human-visible colors. Use clearly labeled false-color encoding, such as special hue plus texture/halo treatment.
- Never imply that the screen literally reproduces ultraviolet, infrared, or another species' subjective color experience.

### B. Species Perception mode

Morph the spectral representation into a cloud of colored luminous points while preserving point identity and dataset provenance.

For organism `o`, calculate a receptor-weighted response from the physical spectrum:

`Q_o = integral S(lambda) * R_o(lambda) d(lambda)`

For multiple receptor channels, calculate one response per receptor and map those responses into an explicitly labeled false-color display.

Important interpretation:

- The underlying sample and particle identity remain the same across species.
- Visibility, opacity, brightness, apparent color, and potentially the number of visible particles may change by species.
- Different species must not see identical output unless their configured response curves genuinely produce similar results.
- The display represents receptor-weighted sensitivity, not an exact simulation of subjective animal vision.

## 6. Species viewpoints and cameras

Every selectable organism has a dedicated camera preset and a corresponding marker in the default scene.

Minimum viewpoints:

### Human

- Camera approximately 5 ft / 1.52 m above the conceptual ground plane.
- Mostly horizontal gaze into the particle field.
- Human photopic sensitivity or cone-based response must be loaded from a documented curve, not invented silently.

### Bird

- Elevated camera looking obliquely downward.
- If using a UV-sensitive bird model, support multiple receptor channels and label the chosen species/model.
- Do not use one generic “bird vision” curve without identifying it as a simplification.

### Ground insect

- Camera close to the ground and tilted upward toward the light field.
- Use a named insect or an explicitly labeled generic demonstration profile.

### Flying insect

- Camera attached to a smooth looping/orbiting flight path around the light field.
- Provide pause/resume and reduced-motion behavior.
- Movement should not change the spectral data unless an additional, explicitly modeled spatial attenuation system is introduced.

Camera transition requirements:

- Clicking an organism marker or UI control smoothly moves from the default camera to that organism's camera.
- The camera transition and the species spectral transformation should be synchronized but conceptually separate.
- Provide a persistent **Return to Default View** control.
- Preserve user orientation when switching sites only if it does not confuse the separation of the two worlds.

## 7. Recommended interaction sequence

1. Load the Philadelphia or Cherry Springs scene independently.
2. Begin at the clean default 3D perspective.
3. Show the physical wavelength field with wavelength legend and date/time controls.
4. Trigger a morph into the particle-based perceptual field.
5. Display organism markers/camera targets.
6. Select an organism.
7. Animate to its camera while applying its receptor-weighted rendering.
8. Allow comparison with another organism using the same physical spectrum and same particle identities.
9. Return to the default view or switch to the other site, loading a separate scene rather than overlaying data.

## 8. Data and transformation requirements

- Parse the two sites independently.
- Validate timestamps, wavelength columns, missing values, duplicated spectra, and quality flags.
- Preserve raw values separately from derived values.
- Resample species sensitivity curves to the dataset's 1 nm wavelength grid.
- Record the overlap between each receptor curve and 280–840 nm.
- Do not extrapolate sensitivity beyond available response-curve coverage without an explicit method and warning.
- Support selection of a timestamp or controlled aggregation over a clearly displayed interval.
- Use deterministic particle seeds so the same physical sample generates the same particle positions across species views.
- Apply species weighting to rendering attributes, not to random particle regeneration.
- Keep Philadelphia and Cherry Springs application state separate.

## 9. Organism-response data policy

Species response curves are auxiliary scientific inputs, not additional city-light datasets. They may be used, but must have source metadata including:

- Species or receptor name
- Wavelength unit
- Normalization method
- Citation/source
- Valid wavelength range
- Whether the curve represents a receptor, photopic sensitivity, behavioral action spectrum, or another quantity

If authoritative curves have not yet been supplied, the interface may use clearly labeled placeholder curves for development only. Placeholder outputs must say **Demonstration only — not a validated species model**.

## 10. Recommended local implementation stack

- Vite
- React
- TypeScript
- Three.js through `@react-three/fiber`
- `@react-three/drei` for camera controls and helpers
- Zustand or a similarly small state store
- GPU points/shader-based rendering for the luminous spectral particles
- Web Workers only if parsing or transformations cause visible UI blocking

Avoid adding a backend unless the actual file size or deployment constraints require one.

## 11. Accessibility and performance

- Keyboard-accessible species and site controls.
- Reduced-motion mode for camera flights and the flying-insect camera.
- Text and shape encodings must accompany color.
- Do not rely on hue alone for UV/NIR or receptor channels.
- Clamp device pixel ratio and use adaptive particle counts.
- Prefer GPU buffers/shaders over thousands of React DOM or mesh objects.
- Provide a clear loading/progress state for large data files.

## 12. Acceptance criteria

- Only Philadelphia–Cherry Springs light data are used.
- Philadelphia and Cherry Springs are separate spaces with no overlay.
- The default view is a restrained, frontal 3D perspective in a black environment.
- The first representation explains wavelength and physical spectral intensity.
- The second representation shows species-weighted luminous particles.
- The same sample and deterministic particle identities are preserved across species.
- Human, bird, ground-insect, and flying-insect views each have a camera preset.
- Species outputs differ according to documented response curves.
- UV/NIR and animal colors are labeled as false-color where appropriate.
- Camera position is not falsely presented as measured directional exposure.
- Raw measurements remain separate from derived perceptual metrics.
- The application makes no unsupported biological-impact claim.

## 13. Open decisions for the next conversation

Before final implementation, resolve:

1. Exact local paths and schemas of the Philadelphia and Cherry Springs files.
2. Exact physical units in the source metadata.
3. Which timestamps or aggregation interval should appear at launch.
4. Exact named species and authoritative receptor/action-spectrum files.
5. Whether the physical-spectrum scene uses all spectra, a sampled subset, or an aggregate envelope.
6. Whether receptor channels should map to RGB, a custom false-color basis, or small-multiple receptor views.
7. Whether camera markers should be literal animal icons, abstract glyphs, or text labels.

## 14. Ready-to-use Codex prompt

```text
You are implementing a local interactive scientific visualization. First inspect the repository and the supplied Philadelphia–Cherry Springs dataset files and metadata. Do not begin by inventing a schema. Report the actual file structure, units, timestamps, wavelength columns, missing values, quality flags, and approximate memory requirements, then make a concise implementation plan and proceed unless a scientifically material input is missing.

PROJECT SCOPE
- Use only the Philadelphia–Cherry Springs spectral irradiance dataset.
- Never use or fetch Hong Kong, Houston TEMPO, Madrid, NYC, Barcelona, ISS, ACTION Street Spectra, or Globe at Night data.
- Build two completely separate 3D scenes: Philadelphia and Cherry Springs. Never overlay or merge their measurements.
- The source data are calibrated absolute downwelling spectral irradiance over 280–840 nm on a 1 nm grid, sampled about once per minute during June–July 2014, with approximately 3,199 usable Philadelphia spectra and 3,192 usable Cherry Springs spectra. Verify every detail against the supplied files and metadata before relying on it.

SCIENTIFIC INTERPRETATION
- The dataset is time × wavelength × irradiance. It does not contain real 3D coordinates for lamps, animals, streets, or individual light sources, and it does not resolve incoming direction.
- Describe the 3D field as an abstract spectral/perceptual space, never as a reconstructed city map.
- Animal camera height, gaze, and motion are narrative/navigation devices. They do not independently change the measured spectrum.
- Ground species differences in documented receptor weighting: Q_o = integral S(lambda)R_o(lambda)d(lambda), or one integral per receptor channel.
- Preserve raw measurements separately from derived values.
- Never claim exact subjective animal color or biological impact.

EXPERIENCE
- Use a near-black background, very subtle gray 3D axes/grid, minimal UI, and luminous additive particles.
- Default camera: clean frontal/isometric-like perspective, level horizon, no Dutch tilt, perspective projection, looking toward the scene center. Include orbit, pan, and zoom with sensible limits.
- Start in Physical Spectrum mode. Recommended axes: X wavelength, Y irradiance with a clearly labeled linear/log treatment, Z time or selected-spectrum index.
- Map 380–700 nm to approximate visible sRGB. UV and NIR must use clearly labeled false-color plus a non-color cue such as texture, glyph, or halo.
- Provide a controlled morph into Species Perception mode, a 3D cloud of luminous points.
- Use deterministic particle identities and positions. When species change, do not regenerate a random cloud; modify particle brightness, opacity, visibility, and false color from the selected species' response curves.

CAMERAS AND INTERACTION
- Show selectable organism markers in the default view.
- Human camera: about 1.52 m / 5 ft above the conceptual ground, mostly horizontal gaze.
- Bird camera: elevated, oblique downward gaze; use a named species/model if UV-sensitive channels are shown.
- Ground-insect camera: near ground, looking upward.
- Flying-insect camera: smooth looping orbit around the light field, with pause/resume and reduced-motion fallback.
- Clicking an organism smoothly moves the camera and independently transitions the spectral rendering to that organism's receptor-weighted view.
- Include Return to Default View, site selector, physical/perception mode toggle, timestamp or interval control, wavelength/receptor legend, and concise methodology/info panel.

SPECIES DATA
- Read species response curves from configurable CSV/JSON inputs and resample them to the 1 nm light-data grid.
- Store source, species/receptor name, valid wavelength range, and normalization method.
- If authoritative curves are absent, do not silently invent them. Implement the interface and data adapter with explicitly labeled development-only placeholder curves: “Demonstration only — not a validated species model.”

TECHNICAL DIRECTION
- Prefer Vite + React + TypeScript + Three.js via @react-three/fiber and @react-three/drei, with a small state store such as Zustand.
- Use GPU point buffers/shaders; avoid one React component or mesh per particle.
- Keep site state independent and transformations deterministic.
- Add keyboard accessibility, reduced motion, loading states, responsive sizing, DPR limits, and performance fallbacks.
- Add focused tests for data parsing, wavelength alignment, integration, normalization, site separation, deterministic particles, and camera-state transitions.

DELIVERABLES
1. A concise README describing setup, controls, data provenance, transformations, limitations, and the difference between measured and derived values.
2. A runnable local application.
3. A clear data-adapter layer for both sites and configurable species curves.
4. Validation tests and a short verification report.

Before finishing, verify that Philadelphia and Cherry Springs never render together, that the same physical sample retains particle identity across species, that species differences come from response curves rather than arbitrary colors, and that camera viewpoint is not mislabeled as measured directional exposure.
```

