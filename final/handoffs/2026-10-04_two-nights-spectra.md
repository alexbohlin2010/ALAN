# Handoff: "Two measured nights" (Philadelphia vs Cherry Springs spectra), before the build

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Firefly narrative" rounds 0a–2a.
Before: `2026-10-04_firefly-narrative-sources.md` (read it too). Read `RULES.md` first.

## Human decisions
- Workflow (human): 1) tab skeleton (done), 2) rebuild the spectrum comparison first (it already has a visual style),
  3) then fill the firefly tabs, using the existing visualisations as reference.
- Tab names accepted "for now". Story (22 steps), part 2 after "Light type": Signal production → Female response →
  Mate-finding → One communication problem → Local firefly → Two measured nights → Broader Impacts → Conclusion.
  Part 3: Explore all studies, then the old Fireflies (Owens & Lewis 2021) and Mice chapters, parked (may be removed later).
  New tabs are `[PLACEHOLDER]` cards (`app/content/story.js`, ids `signal-production` … `two-nights`).
- "Two measured nights" is rebuilt inside `final/app` (no React): the app's simple main-body style, **without the
  surrounding text panels** of the draft, keeping **exactly the draft's 3D light-dot effect** of its "3D Spectrum"
  (Physical) view.
- The two sites share one 3D space and are shown with a **draggable divider** (Philadelphia on one side, Cherry Springs
  on the other), same axes and units.
- Spectra: **all astronomical-night spectra** (sun < −18°), as the draft does (moon: see answers below).
- RULES.md has no visual-language section; the app's existing style is the reference.

## Data (raw, read-only, MANIFEST: `data/raw/spectra/MANIFEST.csv`)
- `data/raw/spectra/spitschan2016/{DRL,CSSP}_spectra.csv` + `_dataquality.csv`: Spitschan, Aguirre, Brainard & Sweeney
  2016, Sci. Rep. 6: 26756, doi:10.1038/srep26756 (CC BY 4.0; correction Sci Rep 7: 46930). Files = GitHub
  spitschan/IlluminationSpectraDataset `data/` at commit 1d2ecc69 (MIT), byte-identical (git blob SHA-1).
- DRL = City (Philadelphia), CSSP = Rural (Cherry Springs State Park). Transposed: columns = spectra (1/min); rows
  1–5 timestamp (`dd-MMM-yyyy HH:mm:ss`, no time zone), date/night id, solar elevation °, lunar elevation °, lunar
  illuminated fraction; rows 6–566 = 280–840 nm at 1 nm. Downwelling spectral irradiance, W·m⁻²·nm⁻¹ (radiance × π).
  Two OceanOptics USB2000+; saturated spectra discarded; negatives after dark subtraction set to 0 (paper Methods).
- Draft's audit (`Linda/visual tests/spatial/philadelphia-spectral-space/DATA_AUDIT.md`): DRL 3,199 spectra
  (2014-07-05 → 07-18), CSSP 3,192 (06-30 → 07-19); NaNs only at 280–359 nm; CSSP has 5.69 % zero cells.
- Paper Table 1, moon illuminated fraction per session: Rural 0.12–0.99, City 0.55–1.00.

## The draft's "3D Spectrum" Physical view (to reproduce)
Source: `Linda/visual tests/spatial/philadelphia-spectral-space/` — `scripts/preprocess.ts`, `src/scene/particles.ts`,
`src/scene/SpectralPoints.tsx` (physical layer only), `src/scene/SceneCanvas.tsx`, `src/scene/cameras.ts`.
- Selection (preprocess.ts): sun < −18°, then 240 spectra evenly sampled in source order
  (`indices[round(i*(n-1)/(239))]`); every 2nd wavelength (281 bins, 280–840 nm). Shared log₁₀ display limits over
  both sites' positive values: floor = floor(p1), ceil = ceil(p99).
- Geometry: x = −12…12 over wavelength index, z = −8…8 over spectrum index, y = normalised log₁₀ value × 9.
  NaN → quality 2 (alpha ×0.08), 0 → quality 1 (alpha ×0.18). Band shape: < 380 nm ring, > 700 nm diamond, else disc.
- Colour `wavelengthToRgb` (particles.ts); additive blending, depthWrite off; point size
  `clamp((1.2 + s*5.1) * focusSize * pxRatio * 15/−z, 1, 8.5*pxRatio)`; alpha `max(0.02, s*focus*quality)`; a time
  "focus" highlights the current spectrum (smoothstep width 0.022), auto-scanning all 240 in a 90 s loop.
- Scene: background #030508, fog (#030508, 22, 52), grid #242d39, camera position [17, 11, 20], target [0, 3.2, 0],
  fov 44, OrbitControls; axis labels (wavelength 280–840 nm, log₁₀ irradiance, time / spectrum index; UV / visible / NIR).
- The final app already depends on `three` 0.186.1 (no new dependency needed for this).
- The built draft can be viewed with `python3 -m http.server 5199` in its `dist/` folder.

## Facts about the final app (for wiring)
- Data is served in dev by `app/vite.config.js` middlewares (`/impacts`, `/colour` allow-list, `/tiles`); a new
  derived folder would need its own route. `final/.gitignore` ignores `data/derived/*` except listed app files
  (standing human decision: commit the small files the app reads).
- Existing 3D overlays: `app/src/spectral.js` (`createSpectral`), driven by `spectral:` keys on story steps.
- Pipeline scripts live in `pipeline/<topic>/NN_name.py` with a docstring (inputs, outputs, rules, labels); no
  `.venv` on this Mac (system `python3` works for stdlib scripts; `pipeline/impacts/xlsx.py` reads xlsx).
- Node v24.21.0 / npm 11.19.0 installed; app runs with `npm run dev` in `final/app` (port 5173).

## Answered by the human (same day, verbatim "1. yes. 2. keep 240 sample data. 3. don't need to consider the moon
## difference. 4. keep the door for now, we'll figure out later.")
- Q1 "which axis labels stay": "yes", i.e. keep the axis and unit labels in the view (no surrounding text panels).
- Q2: keep the draft's 240 sampled spectra per site (2 nm step).
- Q3: the moon difference does not need to be considered (overrides the earlier "disclosed" note).
- Q4: keep the "Light type" door (299-3 → parked Fireflies chapter, step 21) for now; to be decided later.

## Next steps (as agreed)
1. Pipeline script (e.g. `pipeline/spectra/01_night_spectra.py`): raw CSVs → per-site night spectra + metadata in
   `data/derived/spectra/`, labels `measured` (values) / `inferred` (selection, display limits), units written down.
   Then the audits of RULES §3.
2. Renderer in `final/app` for the `two-nights` step: the draft's physical point layer in plain three.js, both sites,
   divider.
