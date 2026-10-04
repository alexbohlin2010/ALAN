# Handoff: RULES §3 audit of the story statistics

Written 2026-10-03 at the end of the audit session. Facts only. The full record is in `AI_LOG.md` ("Story statistic audit", steps 1–3). Read `RULES.md` first. `2026-10-03_story-ux-skeleton.md` (with its addenda) still holds where not superseded here.

## What was done
- §3.1 cross-agent check of `pipeline/story/01_radiance_change.py` and `02_country_change.py`, and their outputs in `data/derived/story/`.
  - Ran in a fresh session on `claude-opus-5-5`, the **same model ID as the builder**, so "ideally a different model" is not met.
  - Report: `audits/story/AUDIT_2026-10-03.md`.
  - Scripts are in `audits/story/` (`common.py`, `s01`–`s06`) and import nothing from `pipeline/`. Run them from `final/` with `.venv/bin/python`. Results are in `audits/story/results/`.
- Outcome: all automated checks **PASS**.
  - Raw hashes (radiance and boundaries) match both MANIFESTs at start and end.
  - Global numbers were recomputed from the raw `.tif.gz`: 71/71 match.
  - Country numbers: 152/152 match.
  - Country masks were built by an independent scanline method: 0 differing pixels from the pipeline's, and areas within 0.001% of the exact polygon areas.
  - Crimea: 0 pixels in Ukraine. Donetsk/Luhansk: 100% in Ukraine. Corsica: 2 parts dropped in the "excl." variant. No overseas France.
  - Counts match the MANIFEST. The grid area matches the 75°N–65°S band, with the +0.0025% difference fully explained.
- §3.2 human spot check: sample drawn with **seed 2136234698**, N = 44.
  - Strata: A8 lit both / B8 newly lit / C6 lit→unlit / D2+D2 −1.5 / E12 country borders / F6 Corsica, Crimea, Donetsk/Luhansk.
  - Sheet: `audits/story/results/s05_spot_check_sample.md` (instructions) plus `.csv` (blank `human_*` columns).

## Decisions made by humans this session
- None beyond the task prompt. The agent chose the spot-check strata and N = 44; both are open to change.

## Facts noted (see report §1 and §5)
- **D1 (agent-chosen, documented):** at the 0.5 and 1 thresholds, total radiance sums only pixels lit at that threshold (+44.17% and +41.92%). Summed over all valid pixels whatever the threshold, the change is +40.99%.
- **D2 (agent-chosen, documented):** the duplicated 180° column is included. Its effect is in the 4th–5th decimal.
- The `02` docstring and output `rule` text still say Corsica is "not chosen". AI_LOG step 15 records incl. Corsica.
- `02` does not record the boundary zip hashes in its output.
- Both outputs still say "Not yet audited".
- India mask = Natural Earth default line: India-administered disputed areas in; Pakistan- and China-administered areas and Siachen out.

## Open (human decides)
- **Human spot check:** check the 44 samples by hand and record the match rate in the sheet. Agents do not do or report this.
- Keep or change D1 and D2.
- Whether to update the stale Corsica wording, add the boundary hashes and change the "Not yet audited" caveat in `pipeline/story/` (outside this audit's scope).
- Whether to rerun §3.1 with a different model.
- Still pending from earlier: the human spot check of the radiance audit (seed 187824061).

## Next task
Not set by the human.
