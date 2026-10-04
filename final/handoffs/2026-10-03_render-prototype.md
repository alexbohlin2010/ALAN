# Handoff: first render prototype built (one globe, real tiles, per-pixel swipe)

Written 2026-10-03 at the end of the prototype session. Facts and human decisions only. The full record is in `AI_LOG.md` (entries "Render prototype, step 1" to "step 7"). Read `RULES.md` first. Earlier handoffs (`2026-10-02_radiance-raw-collected.md`, `2026-10-03_render-architecture.md`) still hold where not superseded here.

## Decisions the human made this session
- **D1:** Node via Homebrew (installed: Node v26.10.0, npm 11.19.1). Packages pinned exactly: `three@0.186.1`, `globe.gl@2.46.2`, `vite@8.3.2` (dev).
- **S1:** geographic tiles (EPSG:4326, the files' own CRS), no reprojection.
- **Tile grid: native pyramid.** This replaced "z8" once it turned out that z8 under S1 is not native. Tiles are 256×256 cut from the raster's own 15″ grid. Levels 0–9; level 9 = native, with no resampling.
- **B3 = E1, lossless WebP:** 8-bit, curve applied at tiling time. R = grey 2015, G = grey 2025, B = flags (1 = 2015 no data, 2 = 2025 no data, 4 = outside the raster).
- **B4 = hist_eq:** CDF of positive pixels, both years pooled; 0 stays black. The human's reason: newly lit, dim areas carry information about the spread of lighting. **B6 = top at P99.99** of pooled positive pixels (= 814.097 nW/cm²/sr), "for now".
- **B5 = N2:** −1.5 = "no data" (shown in magenta, labelled as a display colour). Other negatives → 0.
- **B7:** mean of linear radiance, then the curve ("we can change later if we don't like the effect").
- **B8 = T1b:** Python (GDAL 3.13.3 + numpy 2.5.3) in `final/.venv` (Homebrew python3.14, `--system-site-packages`).
- **B9 = L1:** `app/`, `pipeline/radiance/`, `data/derived/radiance/` (gitignored), `previews/` (gitignored).

## What exists now
- `.gitignore` (raw eog folder, `data/derived/`, `previews/`, `.venv/`, `app/node_modules/`, `app/dist/`, `.DS_Store`). `pipeline/requirements.txt`.
- `pipeline/radiance/` (run from `final/` with `.venv/bin/python`):
  - `config.py`: paths, raw hashes, constants.
  - `01_decompress_to_cog.py`: raw `.tif.gz` → lossless Float32 COGs in `data/derived/radiance/cog/` (308 / 370 MB). Raw hashes checked before and after. Value counts match the MANIFEST exactly for both years.
  - `02_check_no_coverage.py`: read-only check of where −1.5 pixels are → `checks/no_coverage.json`.
  - `03_preview_curves.py`: labelled curve previews → `previews/curves/index.html`.
  - `04_build_curve.py`: hist_eq curve → `curve/hist_eq_p9999.json`. Reference greys: 0.5→46, 1→127, 5→221, 10→236, 50→253, ≥100→255.
  - `05_build_tiles.py`: tiles → `data/derived/radiance/tiles/v1/{level}/{x}/{y}.webp` + `tiles.json` (metadata, curve, per-level existence bitmask). 20,333 tiles, 259 MB, ~10 min. Every tile is read back and matched exactly. Tiles that are 0 in both years with no no-data flag are skipped.
- `app/`: run with `npm --prefix app run dev` (http://localhost:5173), or the `alan-final-app` entry in `~/.claude/launch.json` (outside the repo).
  - Tiles are served in dev by a middleware in `vite.config.js`. The base URL comes from `VITE_TILE_BASE` (default `/tiles/v1/`).
  - `src/main.js` (globe.gl, black globe, atmosphere off, divider, legend).
  - `src/tileLayer.js`: own meshes added via `globe.scene()`, one swipe uniform, nearest filtering, LOD by screen pixel size, empty tiles drawn black.
  - Verified in the browser on 2026-10-03: renders, zooms to native, swipe works, no console errors.

## Facts found this session
- 2015 −1.5: 35,728 of 35,995 pixels are on the raster's last row (65.0°S, over the ocean). At those pixels 2025 is mostly small positive values (median ~1.03 on that row; not interpreted).
- 2025 −1.5: 1,977 scattered pixels, mostly 60–75°N, 45–60°S and near the equator. 2015 is 0 at 1,928 of them.
- The meaning of −1.5 is still unconfirmed without EOG's `cf_cvg` companion file (the human declined companions on 2026-10-02).
- Pooled positive pixels: 147,105,638. 49.6% are ≤ 1 nW/cm²/sr and 92.4% are ≤ 10.
- Under S1 with a 2:1 quad grid, z7 ≈ 611 m/px and z8 ≈ 305 m/px. That is why the native pyramid was chosen.
- The app-launched dev server needed a macOS folder-access permission for ~/Desktop (granted by the human).

## Open (human decides)
- **RULES §3 audits not done** for the COGs or the tiles: a cross-agent check in a fresh session plus a human spot check with a recorded seed.
- **A4 tile hosting** for publication; **git handling** of tiles and raw files. `final/` is still untracked; nothing committed.
- Whether to keep hist_eq / P99.99 / B7 mean after viewing the prototype.
- Licence (EOG CC BY 4.0 vs public domain) still unconfirmed.
- Prelude/story mechanics, colour/CCT layer, separate value product: not started.
- Suggestions from the log (not acted on): remove the unused `final/.claude/launch.json`; bundle size 1.94 MB; nearer fallback level while native tiles load.

## Next task
Not set by the human. Candidates already named in earlier handoffs or this session: the RULES §3 audit of the COGs and tiles, the human's review of the prototype, A4 hosting, git handling.

## Addendum (human, after review, 2026-10-03)
- The human reviewed the prototype and was positive about smoothness and efficiency.
- **Next, in order:** (1) the RULES §3 audit of the derived data (COGs, curve, tiles) against the raw EOG files, in a separate fresh session; (2) colour estimation (CCT), as its own task.
- The human noticed brightness in the sea between Korea and Japan and asked whether it could be fishing fleets. Not investigated. A possible source to check is EOG's VIIRS Boat Detection (VBD) product. Whether `average_masked` removes boat lights has not been checked.
- Later fix (AI_LOG step 9): large grey/white squares while rotating came from the level-0 fallback (2° block means). The loader now loads a fallback 3 levels coarser before the target level. Tile data is unchanged.
