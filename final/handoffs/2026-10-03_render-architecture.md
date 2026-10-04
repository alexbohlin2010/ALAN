# Handoff: render architecture decided (one-globe swipe, three.js), ready for prototype

Written 2026-10-03 at the end of the architecture session. Facts and human decisions only. The full conversation record is in `AI_LOG.md` (entries "Tiling task, step 0" through "step 4"). Read `RULES.md` and the previous handoff `2026-10-02_radiance-raw-collected.md` first. Raw-data facts there still hold.

## Goal (human's words, summarised)
A web app that will be **published**. The globe is a storytelling object: a **prelude button** runs a ~15 s intro on "light through time", then lands on the modern **2015 vs 2025 swipe comparison**. Small datasets are added later as the story goes on (context/intro → urgency → exposition from research). Current focus is **foundational architecture for efficient rendering**, not content. No Madrid/city/CCT content now.

## Decisions the human made
1. **One globe, one renderer.** Two globe instances (the old `globe_v2` approach) were rejected as too demanding.
2. **Swipe = per-pixel in the shader.** The divider position is one uniform; pixels left of it show one year and pixels right of it show the other. No re-tiling or reloading on drag. Encoding both years in one tile (e.g. 2015 in R, 2025 in G) was described; the exact tile encoding is still open (B3 below).
3. **three.js, "in-between" integration:** globe.gl kept for camera, controls and future data layers (points/arcs/labels). Its own globe imagery is turned off. Our own tile mesh + swipe shader is added to its scene via the public `.scene()` accessor. No patching of globe.gl internals (that is what made `globe_v2` fragile).
4. **Time axis can be just two years** (2015, 2025) for this phase.
5. **First prototype uses real tiles** made from the two raw files. **No dummy/test data** in the repo (human: avoid bloat and confusing future agents).
6. **Prototype lives in the repo** (layout not yet chosen, see B9).
7. **Colour/CCT estimation is a later task.** Radiance is shown as neutral greyscale. If any filler colour is ever used, it must be labelled as a display choice per RULES.
8. The human **approved adding a dependency** for the web app and asked which is more efficient and deployable (see "Answer given" below; the human should confirm the exact list).

## Answer given to the human (agent's answer to a direct question; confirm before acting)
- Asked "which is more efficient and deployable": the agent answered **Node + npm + Vite** (plain JS, no UI framework). Facts given: globe.gl and our tile mesh must share **one three.js instance** (mixing globe.gl's CDN UMD bundle, which carries its own three.js, with a separately loaded three.js risks duplicate instances); npm gives pinned versions in a lockfile; Vite outputs a static `dist/` deployable to any static host. Node is **not installed** on this machine (installing it, e.g. `brew install node`, is itself a dependency step).
- Proposed package list (not yet confirmed by the human): `three`, `globe.gl`, `vite` (dev). Versions to be pinned at install time.

## Facts gathered this session
- Earlier apps (agent-built; audited read-only, not reused):
  - `../Linda/visual tests/earth-after-dark/`: one 432-line HTML page; whole-world 8192 px WebP per year (~5 km/px); cross-fade slider over 13 years; patches globe.gl internals; no script that made the images.
  - `../Alexander/globe_v2/`: Web Mercator XYZ tiles z0–9, lossless WebP, 88,362 files / 422 MB committed to git; swipe = two globe.gl instances clipped with CSS; heavy patching of globe.gl tile-engine internals; tone curve stacked in tiler and shader; aurora fill; 16 MB JSON loaded at startup. Patterns noted as sound: one fixed scale across years, linear-domain averaging before tone curve, tile-existence bitmask to skip empty tiles, versioned tile URLs for cache busting.
- globe.gl's built-in tile engine uses Web Mercator XYZ (~±85°); data covers 75N–65S. (To be re-checked against current docs; we are not using its tile engine anyway.)
- Native resolution ~463 m at the equator. 256 px Web Mercator tiles: z8 ≈ 611 m/px at the equator, ≈ 305 m/px at 60°; z9 is finer than native everywhere.
- Environment: GDAL 3.13.3 with `gdal2tiles`, `gdal_calc`, COG/PNG/WEBP drivers. GDAL PMTiles here is vector-only. Homebrew `/opt/homebrew/bin/python3.14` has GDAL + numpy 2.5.3; the `python3` first on PATH (python.org 3.14) has neither. No Node/npm.
- Same brightness scale for both years was explained as the same radiance → grey mapping (so real growth shows as brighter). Per-year scaling would add display-made change (e.g. scaling to each year's max: 99,290 vs 83,972).
- VIIRS DNB is panchromatic (~500–900 nm) and under-detects the blue part of white LEDs; sodium → LED can read as dimming. Relevant to the later colour task.
- −1.5 pixels: 35,995 (2015) vs 1,977 (2025). Shown as black, they could look like change that isn't light. v2.1 (2015) vs v2.2 (2025) processing also differs.

## Still open (human decides; present short options, then wait)
- **Dependencies:** confirm Node + Vite + `three` + `globe.gl` (versions pinned).
- **B2 max zoom:** z8 vs z9 (does the story go down to city scale?).
- **B3 tile encoding:** both years 8-bit in one tile with the curve applied when tiling, vs 16-bit radiance with the curve in the shader (live tuning). Format: PNG vs lossless WebP. Never lossy.
- **B4 radiance → brightness curve:** linear clip / log `log(1+v/k)/log(1+max/k)` / histogram-based. One curve for both years, chosen by the human from labelled previews.
- **B5 negatives:** show as 0 / −1.5 as "no data" (excluded from comparison), other negatives 0 / all negatives "no data".
- **B6 very bright pixels:** saturate at curve top / percentile top / mask flares (needs another dataset; out of scope).
- **B7 low-zoom summarising:** mean of linear radiance then curve / max / `gdal2tiles` averaging after curve.
- **B8 pipeline tooling:** GDAL CLI chain vs Python script (GDAL + numpy). Python env: Homebrew python directly vs a venv.
- **B9 repo layout:** e.g. `final/app/`, `final/pipeline/radiance/`, `final/data/derived/`, generated tiles outside git. Not chosen.
- **A4 tile hosting for publication:** object storage vs PMTiles (needs own loader) vs other. Can be deferred if the tile base URL is configurable.
- **Git handling** of tiles and raw files: still deferred.
- **Separate value product** for future layers needing radiance values (instead of reading display tiles): not decided.
- **Prelude/story mechanics** (button-run sequence, where story text lives): not needed for the first prototype; not decided.
- Earlier open items from the 2026-10-02 handoff (licence, `value_counts.py`, audits) are unchanged.

## The next task
Build the first prototype in the repo: one globe (globe.gl + our own three.js tile mesh in its scene), real tiles from the two raw EOG files, and a per-pixel swipe between 2015 and 2025. Before writing code, get the human's choices on the open items above that the prototype needs (dependencies, B2–B9). Every transformation is a script in the repo; raw files are read-only; log each step in `AI_LOG.md`; RULES §3 audits apply to the generated tiles.
