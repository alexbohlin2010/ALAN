# Handoff: Experience refinement (pass 4): Spectra / Firefly Populations wording, Conclusion, data inventory

Written 2026-10-07. Facts and human decisions only. Full record: `AI_LOG.md` "Experience refinement" steps 28–38.
Read `RULES.md` first. Before: `2026-10-06_experience-refinement-3.md`.

## State
- Branch `main`. Commits b7fa29a35, 6475a5c8b (steps 28–31) and 4499b7013 (steps 32–37). The push from the agent's
  shell failed (no GitHub credentials, step 31); the human pushed the earlier commits; at step 37 `main` was 1 ahead of
  origin (4499b7013). This handoff and AI_LOG step 38 are not committed.
- Dev server: preview_start "alan-final-app" (the config lives in a launch.json the preview tool reads; the repo's
  final/.claude/launch.json has only "app", which the tool did not find). Port 5173.
- app/src/introScene.js (audio, another agent's) not edited. Its "Begin with audio" overlay sits over the centre in the
  in-app pane until clicked.

## Human decisions (step in AI_LOG "Experience refinement")
- Spectra (29): "Night light measured at Cherry Springs, PA, a dark sky park." → "In amber light, Philadelphia's night
  sky is about 150 times brighter." → "Fireflies see best in this band." (the unscripted Philadelphia-peak half dropped).
  Details rewritten; date range "30 June–19 July 2014". Axis words: WAVELENGTH (NM), BRIGHTNESS (LOG, W m⁻² nm⁻¹),
  SPECTRA IN TIME ORDER.
- Firefly Populations (30–31): "In the eastern US, firefly counts are lower in areas with more ALAN." with a smaller grey
  `subtext` "One factor alongside climate, soil and others." ("decreasing" rejected: McNeil et al. 2024 compare places,
  not years.)
- Light type (29): "Impacts occur across all light types."
- Conclusion (32–36): two beats on one screen, left-aligned block centred on screen, space kept so nothing moves
  (`block: true`, `together: [1]`): "ALAN is exposing Earth's critical ecosystems to systemic risk." / "Lights are not
  needed all the time, everywhere. Rather, lighting can be optimized to respond to its environment." Details & sources
  (Czarnecka et al. 2025, Bolliger et al. 2020) on beat 2. "Critical" and "systemic risk" are the human's framing; not
  stated by Czarnecka et al. 2025 (step 24); the first line has no source of its own.

## Mechanisms added (code)
- story.js content key `subtext` (src/story.js `<p class="sub">`; style.css `#fact .sub`, 15–20 px, #8a8a8a).
- Content key `block` (src/story.js toggles `#fact.block`; main.js anchorFact skips it; style.css keeps hidden lines'
  and the Details button's space, text left-aligned).

## Data inventory and audit (step 28, read only; nothing fixed)
- App reads: radiance tiles v1; colour global_white_share_grid (+2 PNGs); impacts studies, study_locations, effects,
  study_highlights, spectra_299, perception_299, spectra_278, owens2018_results, kivela2023; spectra philadelphia,
  cherry_springs, spectra_meta, species_curves. Values copied by hand into code: 41 % (radiance_change), 150×
  (amber_band_ratio), 207, abstracts quotes, display_ramp / display_tints, sensitivity_bands.
- No audit: all colour files, impacts studies / locations / effects / highlights / abstracts / perception_299,
  spectra species_curves / amber_band_ratio / sensitivity_bands, story version_sensitivity / country_screen, tiles v2.
- Human spot checks pending (samples drawn): radiance (seed 187824061), story (seed 2136234698, N 44), impacts_spectra
  (N 20), impacts_spectra_299 (N 24). Done 20/20: night_spectra, owens2018, kivela2023.
- country_change_2015_2025.json changed after its audit (sha 850db62c… → bbabdd52…); every card using it is retired.
- Other findings: Response values typed by hand (documented, no data file); "measured (camera raw, uncalibrated)" label
  in global_nef_pilot_ratios.csv; blank cells in global_thumb_cct.csv (5,405) and thumb shares (15) not checked for
  notes; spectra_278 / 299 scripts changed after their audits (outputs unchanged); *_pdftext.txt cited by audits are
  missing; colour/03 --kind geotiff needs a missing folder; vite `/impacts/*` has no allow-list.
- Agent proposals, not decided: cross-agent checks X1 impacts (Data S1 → studies / locations / effects / highlights),
  X2 spectra 03–04, X3 perception_299, X4 abstracts quotes, X5 colour grid; new human samples N 20 for
  amber_band_ratio, effects / studies, perception_299.

## Open
- Which cross-agent checks to run (the agent writes the prompt for a separate session; it does not run them).
- DATA_INVENTORY.md: still the 2026-10-02 trace of the old projects; proposed layout (keep as history, add a dated
  final/ section) awaiting the human's OK.
- From earlier handoffs, still open: lizard replacement (Jiang et al. 2023); release line without Details; dark share
  98.7 % not on screen; faint Cherry Springs reply; nav arrows do not step Response's beats; clicking → mid-flight.
- Step 38: the human asked how the globe's light data is made (explanation given in chat from the pipeline and
  METHOD.md; no changes). Points of note found there: the colour layer is `estimated`, unaudited, with a per-mission
  camera bias (METHOD.md); the 2025 fallback white share (0.41) comes from Brazil's public-lighting census (ABCIP 2024),
  per global_white_share_grid.json.
