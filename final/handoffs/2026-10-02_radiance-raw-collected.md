# Handoff: raw radiance collected (EOG VNL 2015 + 2025)

Written 2026-10-02 at the end of the radiance-acquisition session. Facts and human decisions only. The full history is in `AI_LOG.md` (entries from "Radiance raw data, step 1" onward).

## Decisions the human made
- Globe radiance = **EOG / Colorado School of Mines annual VNL originals**, layer **`average_masked`**. This replaces the Zenodo 17294744 repackage, whose `average_viirs` files appear to be the unmasked layer (an inference from filenames, not verified).
- Years: **2015 and 2025**. These replace 2012 and 2024. Reasons: matching full calendar years (2012 starts in April), and the same stray-light config.
- Both files are config `vcmslcfg` and satellite S-NPP. The human **accepted** the version mix (2015 from `annual/v21/`, 2025 from `annual/v22/`, filename tag `v2`) to get about a decade between the years. Per the human, `v22` only goes back to 2021.
- Location: `final/data/raw/radiance/eog/`. **Git handling deferred** (both files are >100 MB). Don't commit them.
- The human downloads anything behind the EOG login. GDAL (Homebrew) is approved and installed.

## What exists now
- `data/raw/radiance/eog/VNL_v21_npp_2015_global_vcmslcfg_c202205302300.average_masked.dat.tif.gz`, 280,997,747 B, SHA-256 `1cdafa2039e49fe64b629592e20d33dc746ecc77824a6a4898a76c03311104fa`
- `data/raw/radiance/eog/VNL_npp_2025_global_vcmslcfg_v2_c202604011200.average_masked.dat.tif.gz`, 340,942,192 B, SHA-256 `55cdc85dab51a26b2806071c2efee49314d1d8bb235581df2b0a03574c95e3ab`
- `data/raw/radiance/MANIFEST.csv`: source URL (assembled from the folder the human gave plus the filename), citation, version, config, period, licence status, sizes, hashes, and read-only check results.

## Facts from the read-only checks
- 86401×33601 px, Float32, EPSG:4326, 15 arc-sec, extent 75N–65S. No nodata tag in either file.
- No cap at 200 nW: max 99290 (2015), 83972 (2025).
- Negative values present: −1.5 (35,995 / 1,977 px) and other small negatives (27,073 / 315 px). Their meaning is undocumented in the file. The EOG v2.2 readme mentions −1.5 as a median placeholder for zero cloud-free coverage (unconfirmed for `average_masked`).
- About 97% of pixels are 0.

## Open questions (for the human)
1. Licence: the EOG page says "many" products are CC BY 4.0; GEE says public domain. Not yet confirmed (EOG's licence PDF couldn't be parsed).
2. Companion files: human decided 2026-10-02 not to get them for now.
3. How to treat −1.5 and other negatives. Decide in a later transformation task; don't "fix" them in raw.
4. Git: gitignore + manifest, or Git LFS. Deferred.
5. Keep `value_counts.py` (currently only in the session scratchpad; its code logic is described in AI_LOG) as a script in the repo? Not decided.
6. HDNTL: **dropped by the human** 2026-10-02 (no added spatial resolution; the effect of the angular correction on the visualization is unclear).
7. Colour (CCT) vs tiling order: the human raised whether colour estimates should come after tiling. Facts given: colour estimation is independent of tiling; it would be its own `estimated` layer, and tiles would be generated from radiance (and colour, if chosen) as display products. Not decided.
8. RULES §3 audits haven't been done yet (no transformed data exists).

## Not in scope (unchanged)
Global CCT map (separate future task), HDNTL (dropped), Linda's datasets, any processing, tiling or rendering.

## The next task (set by the human, 2026-10-02)
Tile the globe with lights for **2015 and 2025, with a comparison**, for rendering in globe.gl. Starting point: the two raw files above (read-only). Things the human has not decided yet, which the agent proposes as short options and then waits on:
- How the comparison is shown to the viewer.
- Tile scheme, maximum zoom/resolution, bit depth, image format, and whether empty tiles are skipped.
- How raw values become display brightness (tone curve). The old `tiler.py` choices (HI=8.3, γ 0.62, aurora fill, amber ramp) are **not** carried over unless the human re-decides them (DATA_INVENTORY Tier D).
- How −1.5, other negatives and the very bright pixels (flares) are treated.
- Where scripts and outputs live in the repo, and any new dependency (GDAL 3.13.3 is installed and approved).
Colour/CCT is out of scope for this task.
