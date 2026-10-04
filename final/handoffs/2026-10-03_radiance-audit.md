# Handoff: RULES §3 audit of the derived radiance data

Written 2026-10-03 at the end of the audit session. Facts only. The full record is in `AI_LOG.md` (entries "Radiance audit, step 1" to "step 3"). Read `RULES.md` first. `2026-10-03_render-prototype.md` (with its addendum) still holds where not superseded here.

## What was done
- §3.1 cross-agent check, run in a fresh session (`claude-opus-5-5`, the same model ID as the builder, so "ideally a different model" is not met). The report is `audits/radiance/AUDIT_2026-10-03.md`.
- The scripts are in `audits/radiance/` (`common.py`, `a01`–`a05`, `curve_grey.py`) and import nothing from `pipeline/`. Run them from `final/` with `.venv/bin/python`. Results are in `audits/radiance/results/`.
- Outcome: all automated checks **PASS**.
  - Raw hashes are unchanged at start and end.
  - The COGs equal the raw files bit for bit, and all counts match the MANIFEST and `.counts.json`.
  - The curve rebuilds from raw with zero difference.
  - Every pixel of all 20,333 tiles at levels 0–9 matches the stated rules: greys, B7 block means and flags. No tiles are missing or extra, and `tiles.json` is consistent.
- §3.2 human spot check: sample drawn with **seed 187824061**, N = 35 (strata A20 positive / B5 uniform / C5 −1.5 / D5 level-8 blocks). The sheet is `audits/radiance/results/a05_spot_check_sample.md` (instructions) plus `.csv` (blank `human_*` columns). The agent did not read raw values for the sample.

## Decisions made by humans this session
- None beyond the task prompt. The agent chose the spot-check strata and N = 35; both are open to change.

## Facts noted (no rule broken)
- Under B7 + N2, a coarse-level block is flagged no-data only if all of its in-raster pixels are −1.5. Flag-2 (2025) pixels: 1,977 at level 9, 3 at level 8, 0 at levels ≤ 7.
- All 5 stratum-C samples are on the 65°S last row, where 35,728 of the 37,970 −1.5 pixels lie.
- The raw pixel size is stored as 0.0041666667° (rounded 1/240), so the last-row centre computes to −65.000001°. It is carried unchanged.
- `dwebp` and GDAL's WebP driver both use libwebp.

## Open (human decides)
- **Human spot check:** check the 35 samples by hand and record the match rate in the sheet. Agents do not do or report this.
- Whether to add a spot-check stratum for scattered −1.5 pixels.
- Whether to rerun the automated checks with a different model for §3.1.
- Items still open from earlier handoffs: A4 hosting, git handling (`final/` untracked, nothing committed), keeping hist_eq / P99.99 / B7, the licence, the Sea of Japan / VBD question.

## Next task
Per the human's addendum to the prototype handoff: colour estimation (CCT), as its own task in a fresh session. The human spot check above is still pending.
