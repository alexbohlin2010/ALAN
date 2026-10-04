# Handoff: colour, global white-share grid rebuilt from night-only frames

Written 2026-10-03. Follows `handoffs/2026-10-03_colour-global-first-render.md`. Read `RULES.md` first.
- Log: `AI_LOG.md`, colour steps 39–42.
- Method: `pipeline/colour/METHOD.md`, sections "Frame flags" and "Grid rebuilt without flagged frames".

## Human decisions (this session)
- Day / non-city frame exclusion: **option D**, sun elevation ≥ −12° OR thumbnail median ≥ 40. The per-photo flag file was approved.
- Note the aurora / moonlit-cloud limit in METHOD.md (done).
- Rebuild the grid with the flags (step 3, done).
- Still standing from earlier: values may be `estimated`; no legend; keep the VIIRS caveat.

## Facts found
- Thumbnails carry EXIF `DateTimeOriginal`. Sun elevation from that time + nadir matches the archive's "Sun Elevation Angle" on all 89 saved photo pages (≤ 0.7°). Fetching photo pages for sun elevation (old option A) would add nothing.
- The ISS041 camera clock looks wrong: daytime frames (e.g. ISS041-E-90094) come out at sun < −40°. Only the brightness flag catches them.
- Of the 3,575 bright frames, 3,540 are "night" by sun elevation. 5 viewed at random: aurora (3), moonlit cloud with lightning (2).

## State
- New: `pipeline/colour/14_frame_flags.py`, `data/derived/colour/global_frame_flags.csv` (26,356 rows, 5,160 exclude; 4,061 of the 20,707 usable).
- `10_white_share_grid.py` uses the flags. The new grid PNG + JSON have fallback grey 212 (2015, share 0.154) and 104 (2025, share 0.679).
- The app (no code change) shows the new grid. Checked at localhost:5173: loads, no console errors.
- NEF pilot: all 16 NEFs downloaded (254 MB, `data/raw/colour/eol/nef/`, 16 manifest rows). The 8 newest have not been analysed (`13_nef_pilot.py analyse` not rerun).
- Not audited (RULES §3). Nothing committed, nothing deleted.

## Open questions for the human
- 2025 per-mission disagreement (ISS065/067 low vs ISS064/070/072 high) is unresolved and is in the grid. Proposed earlier: ~10 NEFs of the same cities from those missions (~0.2–0.5 GB; pick list first, then ask before downloading with names / source / size).
- Analyse the 8 new pilot NEFs (no download needed).
- Dimmer aurora / moonlit frames under the brightness threshold remain in the pool. Whether to do anything about it is not decided.
- Still open from earlier: delete downloaded thumbnails / NEFs / query HTML after use (keep a textual record); RULES §3 audits; stronger-contrast variant; tiles v2 / class raster keep or delete; git handling of `data/raw/colour/`.

## Update (AI_LOG colour steps 44–45): 2025 fix
- **Human:** "okay we need to fix 2025 color now using NEF or whichever method helps us to get it right. Feel free to analyze those other 8 pilot NEFs too."
- **Cause of the 2025 disagreement:**
  1. Non-city frames (Moon, lightning, moonlit cloud, aurora, horizons) in the pool, mostly ML records.
  2. Per-photo conversion white balance in the archive JPEGs.
- **Done:**
  - `14_frame_flags.py` gained `city_frame` (point-like lamp pixels ≥ 800 and ≥ 10 %). `exclude` includes NOT city_frame.
  - `10_white_share_grid.py` uses the WB-corrected CCT white share (`12_thumb_cct.py`) for global (`SHARE_SOURCE`).
  - Grid rebuilt; render checked.
- **Result:** with city frames, 2025 missions agree: US 0.79–0.97; EU 0.18–0.33 (2021–22), with ISS071 (2024) at 0.77.
- **NEF check of the WB correction:** median CCT within ~130 K on 8 of 10 night NEFs (D3S, D5). The 2 frames converted at 2,850 K come out too white.
- **New grid:** 2015 fallback 0.184 / grey 203; 2025 fallback 0.848 / grey 68.
- **Coverage roughly halved:** 2025 mean coverage Europe 0.15, US 0.11, India 0.03. Most cells use the global fallback, which is whiter than Europe's own values.
- **Open for the human:**
  1. Fallback: global median (current) vs a regional fallback (e.g. a wide-kernel regional share).
  2. More thumbnails per cell (cap 5 now) to restore coverage (download, needs approval).
  3. More NEF checks (Z 9, D4, ~5,300 K conversions; download, needs approval).
  4. Audits (RULES §3) of the flags and grid.
- **Nothing committed or deleted.** Scratch copies of the step-42 grid are in the session scratchpad only.

## Update 2 (AI_LOG colour step 47): regional fallback
- **Human:** "regional fallback, then render again. 2025 too white globally".
- **Done:** regional share (1° grid, sigma 5°, cut 15°; agent's parameters) blended under the local share. The global fallback now covers only what neither reaches. Rendered: 2025 Europe is a mix of orange and white.
- **Coverage 2025:** Europe 0.88, US 0.78, India 0.67, E China 0.97, Africa 0.28.
- **Open:** whether the 2025 look is still too white overall (the human judges). The global fallback (0.85) still applies in sparse regions. Sigma / cut not chosen by the human. Earlier open items (more thumbnails, more NEF checks, audits) unchanged.

## Update 3 (AI_LOG colour step 48): facts about the 2025 global fallback (0.848)
- **Human:** "do we have any good reason to presume the globe is this white? it seems ABSURD". The human wants to propose a different 2025 global fallback in the next session.
- **What the value is:** the plain median of per-photo white shares over the 1,999 kept 2025 photos. It is not weighted by lit area, population or region. It applies only where neither local nor regional photos reach (e.g. much of Africa, Central Asia).
- **Kept photos by region** (agent's lat/lon boxes, `global_thumb_cct.csv` white share, frame flags applied): n (share of photos), median.

  | Region | 2015 | 2025 |
  |---|---|---|
  | Europe | 903 (34 %), 0.09 | 480 (24 %), 0.29 |
  | N America | 823 (31 %), 0.19 | 321 (16 %), 0.82 |
  | E Asia | 320 (12 %), 0.77 | 499 (25 %), 0.98 |
  | Africa / Middle East | 231 (9 %), 0.19 | 320 (16 %), 0.93 |
  | SE Asia | 26, 0.40 | 126, 0.94 |
  | S Asia | 52, 0.39 | 43, 0.97 |
  | Latin America | 51, 0.16 | 4, 0.87 |

- **The 2025 sample mix differs from 2015:** more E Asia, less Europe and N America.
- **E Asia is already 0.77 in 2015.** "White" here means lamp pixels ≥ 2,700 K: LED, but also metal halide, fluorescent and mercury. Not checked against any source.
- **Documented LED shares found so far** (AI_LOG step 33): US 12.7 % (2014), 48.6 % (2018); Spain 56 % (2017); UK 51 % (2019); South Africa 5 % (2015).
- **Known method biases toward white:**
  - JPEGs converted at low temperature (≤ ~2,900 K) overstate white (2 of 10 NEF checks).
  - Pixel share ≠ luminaire share: brighter white sources fill more pixels.
  - Astronauts photograph bright, large cities.
- **Not checked:** what the Africa / Middle East 2025 photos actually show (Gulf cities vs sub-Saharan Africa).
