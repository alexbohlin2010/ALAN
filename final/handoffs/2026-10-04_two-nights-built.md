# Handoff: "Two measured nights", pipeline + audit + renderer built

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Firefly narrative" rounds 3a–3e.
Before: `2026-10-04_two-nights-spectra.md`. Read `RULES.md` first.

## State of the code
- Worktree branch `claude/cool-ishizaka-9fd75f`: merge commit acdd8f9a5 (main 6ea64b8f4 + `linda-firefly-narrative`
  80750733c, human-approved). Everything after that merge is **uncommitted** (nothing pushed).
- Uncommitted: `pipeline/spectra/01_night_spectra.py`, `data/derived/spectra/{philadelphia,cherry_springs,spectra_meta}.json`,
  `audits/night_spectra/`, `app/src/twoNights.js`, edits to `app/src/main.js`, `app/content/story.js`,
  `app/src/style.css`, `app/vite.config.js`, `.gitignore`, `AI_LOG.md`, this handoff. Also `.claude/launch.json` in
  the worktree root (preview config, outside `final/`).

## Human decisions (this session)
- Merge `linda-firefly-narrative` into the worktree branch, keeping both log blocks.
- Output layout: one JSON per site + `spectra_meta.json` in `data/derived/spectra/`; dev route `/spectra` (allow-list);
  `.gitignore` exception for the three files.
- Cross-agent audit run by Opus 5.5 ("still use opus 5.5 to run it, not sonnet").
- Renderer: own module `app/src/twoNights.js`, story key `nights: true`; OrbitControls + CSS3DRenderer from
  `three/examples/jsm`; Philadelphia left of the divider, Cherry Springs right; place names only.

## Data facts
- Philadelphia 3,199 spectra → 1,200 night (sun < −18°) → 240; Cherry Springs 3,192 → 1,268 → 240. 281 wavelengths
  (280–840 nm, 2 nm). Selected cells: no NaN; zeros 214 / 7,780. Display limits log₁₀ −9 … −5 (p01 −8.967, p99 −5.326).
- Values verbatim from source text. Labels: irradiance + timestamp `measured`; night id, solar/lunar elevation,
  lunar fraction `documented` (agent's choice, not yet confirmed by a human); selection + display limits `inferred`.
- Output equals the draft's own output (indices, timestamps, limits, float32 cells).

## Audit (`audits/night_spectra/AUDIT_2026-10-04.md`)
- All six rules PASS. Same model as builder, so RULES 3.1 "ideally a different model" not met.
- Findings F1–F6 and script risks R1–R3 listed there and in AI_LOG round 3d (none changes a value).
- RULES 3.2 human spot check: seed 20261004, N = 20, `audits/night_spectra/results/a06_spotcheck.md`. Match rate 20/20 (human, round 3n).

## Renderer facts
- Reproduces the draft's Physical (log) layer, scene, camera, controls, axis frame and labels, 90 s auto-scan; both sites
  share the focus index. Differences: 1 px lines instead of drei fat lines (0.7–1.25 px); no species markers.
- The draft's axis labels carry no irradiance unit (height label reads "HEIGHT · LOG₁₀ IRRADIANCE"); kept as in the draft.
- Checked in the in-app browser (port 5174): renders, divider and orbit work, hides on leaving the step, no console errors.

## Later in the session (AI_LOG rounds 3f–3j)
- Human: unit added to the height label ("HEIGHT · LOG₁₀ IRRADIANCE · W m⁻² nm⁻¹"); `documented` labels kept in the
  data but not shown on the web page; no commit yet; fix audit findings F1–F6, R1, R2, keep R3 as is.
- Fixes done and pipeline re-run: values, selection and display limits unchanged; `night_id` now source text.
- Re-check (`audits/night_spectra/recheck_2026-10-04/RECHECK.md`, Opus 5.5): fixes confirmed; new notes C1–C6
  (1-based `source_column` not stated in the files; `identifier` is not a RULES 2.3 label (agent's choice); some
  units only in the meta file; writes not atomic; raw files 0644 although MANIFEST says read-only; same model).
  Spot-check sample still valid.

- Rounds 3k–3l: C1 fixed (`source_column_note`, 1-based), C2 fixed (`identifier` label replaced by a `not_values` list),
  C3/C4 left as is, C5 explained (raw files are read-only in the main checkout; git does not keep the read-only bit in
  a worktree checkout). Second re-check `audits/night_spectra/recheck2_2026-10-04/RECHECK2.md`: 7/7 pass, all values
  unchanged, spot-check sample still valid. RULES does not define `not_values` (noted by the auditor).

## Next step options (given to the human; human decides)
- Close this step: human spot check; commit when asked; card text for `two-nights` by the human.
- Then the firefly tabs in workflow order, starting with Signal production: extract Owens et al. 2018 reported
  results into a labelled file by script, audit, then build the scene after "Light type" (as agreed in
  `2026-10-04_firefly-narrative-sources.md`).

## Open (human decides)
1. (done: C1–C5 handled in rounds 3k–3l)
2. (done: human spot check 20/20 matched, recorded in round 3n)
3. Commit, when asked (and whether the two 2.5 MB auditor extracts, `a02_extract.json` / `r02_extract.json`, go in).
4. Step card text for `two-nights` is still `[PLACEHOLDER]`.
