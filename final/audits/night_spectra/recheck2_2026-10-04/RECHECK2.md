# Recheck 2: night spectra after C1/C2 edit (RULES §3.1 cross-agent check)

Date 2026-10-04. Tool: Claude Code subagent, model `claude-opus-5-5` (same model as the builder and the earlier audits, so the RULES §3.1 "ideally a different model" condition is not met). Fresh context. Scripts were run from `final/` with system `python3 -B`, stdlib only. Nothing outside this folder was written. `pipeline/spectra/01_night_spectra.py` was not run or imported (q06 parses it with `ast`). No state-changing git command was run. `AI_LOG.md` was not edited.

Scope: the round 3k edit (AI_LOG "Firefly narrative, round 3k"), i.e. C1 and C2 from `audits/night_spectra/recheck_2026-10-04/RECHECK.md`. Baseline = scratchpad copy `spectra_3h/` of the outputs before the edit.

## Summary

| # | Check | Result |
|---|---|---|
| 1 | Raw files vs `MANIFEST.csv` (size, SHA-256), start and end (q01) | **PASS.** 4/4 match at start and end. Snapshot (SHA-256, size, mtime, mode) of the 4 raw files, MANIFEST, 3 outputs and the script is identical start vs end. |
| 2 | Diff new vs `spectra_3h`, all leaves as text (`parse_float=str, parse_int=str`) (q02) | **PASS.** Baseline SHA-256 equals the values recorded in the previous recheck. Site files: 5 differences each (1 added, 4 removed, 0 changed, no key-order change, no length change). Meta: 1 added key. All data fields identical as text (list below). |
| 3 | Strict JSON (q03) | **PASS.** 3/3 files: UTF-8, no NaN/Infinity constants, no NaN/Infinity tokens outside strings, no duplicate keys at any depth, every number token matches the JSON number grammar (68,651 / 68,651 / 302 tokens). No `null`. |
| 4 | Site-file keys labelled or in `not_values` (q04) | **PASS.** Both files: 24 top-level keys = 18 labelled + 3 in `not_values` (`site`, `source_file`, `meta_file`) + 3 containers (`labels`, `label_notes`, `not_values`). No overlap, no unlabelled key, no label/not_values entry for a missing key. Labels used: `measured` (2), `documented` (8), `inferred` (8) only; `label_notes` keys = labels used. The string `identifier` no longer appears. |
| 5 | `source_column_note` correct (q05) | **PASS.** Against the raw CSVs (own `split(',')`): CSV column `source_column` (1-based) holds the output's timestamp, night id, solar/lunar elevation and lunar fraction 240/240 per site, and the irradiance at CSV row 6 + (w − 280) for 67,440/67,440 cells per site. A 0-based reading matches 0/240 timestamps. CSV column 1 is a spectrum (row 1, field 1 is a timestamp; no header column). |
| 6 | Script docstring vs code for C1/C2 (q06) | **PASS.** `labels`, `label_notes`, `not_values` in both outputs equal the script's `SITE_LABELS` (incl. order), `LABEL_NOTES`, `NOT_VALUES` literals; meta `source_column_note` equals the code literal; the docstring's measured/documented/inferred groups equal `SITE_LABELS`; docstring says `site`, `source_file`, `meta_file` are under `not_values` with no label, matching code; the unlabelled-field guard includes `NOT_VALUES` and the 3 containers; `identifier` absent from the script; docstring references round 3k C1/C2. |
| 7 | Spot-check sample `audits/night_spectra/results/a06_spotcheck.md` still valid (q07) | **Yes.** Re-drawing seed 20261004 on the current outputs gives the same 20 cells; all 8 columns (site, file, spectrum index, wavelength, value text, CSV row, CSV column, timestamp) identical in 20/20 rows. The human check itself was not performed or reported here. |

## Diff new vs `spectra_3h` (q02, complete list)

- `philadelphia.json` and `cherry_springs.json` (same in both):
  - ADDED `not_values` = `{"site": "site id", "source_file": "path of the raw file", "meta_file": "path of the meta file"}`
  - REMOVED `labels/site`, `labels/meta_file`, `labels/source_file` (each was `"identifier"`)
  - REMOVED `label_notes/identifier` (was `"a name or file path, not a value"`)
  - Everything else identical as text, including the other 18 `labels` entries and the `documented` / `inferred` / `measured` notes.
- `spectra_meta.json`:
  - ADDED `source_column_note`.
  - Everything else identical as text.
- Data fields confirmed identical as text: site files: `irradiance` (67,440 cells), `source_column`, `timestamp`, `night_id`, `solar_elevation_deg`, `lunar_elevation_deg`, `lunar_illuminated_fraction` (240 each), `n_source_spectra`, `n_night_spectra`, `n_selected`, `source_date_range`, `selected_date_range`, `source_dataquality`, `selected_cells`, `source_sha256`, `unit`, `place`, `paper_label`, `site`, `source_file`, `meta_file`. Meta: `wavelength_nm` (281), `wavelength_step_nm`, `display_limits_log10` (floor, ceil, rule, n_positive, p01, p50, p99), `sites`, `unit`, `units_other`, `timestamp_format`, `selection`, `files`, `null_means`, `verbatim`, `source`, `source_url`.

## Method

1. Read `RULES.md`, the previous `RECHECK.md`, MANIFEST, `a06_spotcheck.md`, the output structure, the script, and AI_LOG round 3k (read only).
2. `q01_raw_integrity.py start`.
3. `q02_diff_vs_3h.py`: baseline SHA-256 vs previous recheck; recursive leaf diff (keys, key order, list lengths, text values) of each output vs `spectra_3h/`; named data fields compared whole.
4. `q03_strict_json.py`: strict parse with hooks for constants, duplicate keys and number grammar; regex for NaN/Infinity outside string literals.
5. `q04_labels.py`: key coverage by `labels` / `not_values` / containers.
6. `q05_source_column_note.py`: every selected spectrum and cell checked against the raw CSVs at the stated 1-based column and row; 0-based reading as control.
7. `q06_docstring_vs_code.py`: `ast` parse of the script; constants vs outputs; docstring sentences vs constants (the measured/documented/inferred key groups in q06 are this auditor's reading of the docstring sentence, printed in the result file).
8. `q07_spotcheck_validity.py`: same seed and RNG calls as `a06_spotcheck_sample.py`, compared with the existing table.
9. `q01_raw_integrity.py end` (compared with start).

## Findings

No data value changed and no check failed. Notes (facts, no value is wrong):

- **N1. Script diff not possible.** No copy of the pre-edit script exists (it is untracked in git; the previous recheck recorded only its SHA-256, `be7688a4…`). The edit was verified through its outputs (q02) and the current script's docstring/code (q06), not by diffing the script.
- **N2. Docstring change beyond C1/C2.** The docstring's verbatim list now also names the data-quality counts (previous recheck note C4(c)). AI_LOG round 3k records this. It matches the code (`'source_dataquality': {k: raw(v) ...}`). The added words break the line oddly ("data-quality counts) is written" / "exactly as the source text"); text only.
- **N3. `not_values` is a project key.** RULES §2.3 defines the four labels and empty cells; it has no category for names/paths. `not_values` is how this file marks them; RULES does not define it.
- **N4. Baseline copy not read-only.** The `spectra_3h/` files are mode `0644` (owner-writable), not read-only as the brief describes. Their SHA-256 equals the hashes recorded in the previous recheck, so the content is the audited state.
- **N5. Same model** as the builder (see header).
- Earlier notes C3, C4(a,b,d), C5, C6 from the previous recheck are outside this scope and were not re-examined (AI_LOG round 3k says they were left as is).

## Passes

All 7 rows of the summary table.

## Files created (all in `audits/night_spectra/recheck2_2026-10-04/`)

`q01_raw_integrity.py`, `q02_diff_vs_3h.py`, `q03_strict_json.py`, `q04_labels.py`, `q05_source_column_note.py`, `q06_docstring_vs_code.py`, `q07_spotcheck_validity.py`, `RECHECK2.md`; in `results/`: `q01_start.txt`, `q01_end.txt`, `q01_snapshot_start.json`, `q01_snapshot_end.json`, `q02_diff.txt`, `q03_strict_json.txt`, `q04_labels.txt`, `q05_source_column_note.txt`, `q06_docstring_vs_code.txt`, `q07_spotcheck_validity.txt`.

## SHA-256 of audited files (unchanged from start to end)

```
4e78967a18f41b2d7c07da8fa58f4f4dfb274a5e955648b3ec9c42787cbd2354  data/derived/spectra/philadelphia.json
6080a9911fa1c688271f2b11fdaaae478c2c68644e7493364dac4721eb8fffd8  data/derived/spectra/cherry_springs.json
928df96ccae186fc6a6fef9d16921cb20f89eef2debc665998f05105d014decc  data/derived/spectra/spectra_meta.json
06c4f91152f18a64115c137af701d74f163de29790a3e462672cd28e9803492b  pipeline/spectra/01_night_spectra.py
07c9ade8708d136165531dc1f75f188f67aa663f962e966ca489d1ae56a50331  data/raw/spectra/MANIFEST.csv
```

Baseline (`spectra_3h/`, = previous recheck): philadelphia `84fd2b83…bd899`, cherry_springs `670472fe…a5181`, meta `4446efd5…c2e3`.

Recheck scripts:

```
dc0ae8d0208647bbe4ff410a02f8df24ab758a0a3c229e6b68abf73607d8ae3b  q01_raw_integrity.py
9c8d3a59ba2803d270cd276ca9f6ad8785f6469eae25f6952e4473c4c27182b4  q02_diff_vs_3h.py
9458ff48ca2754ed1d1113f3e61c6753af6ead1a3219061bcb8cc7fb0b47fd4c  q03_strict_json.py
05623a7515c6133b1920d9a41aef4a38fcc3babe124eac82326df83f9eb91f13  q04_labels.py
198dc31ae967eac0234489e12d35afa02a7d5ed6aa13857f37606cebfd020de8  q05_source_column_note.py
4cd5dab9f448c72b20278edef6f70bcbd71c58c0c9e03d17542f309c6b9d6285  q06_docstring_vs_code.py
b4f13fe58cdfc0da9bbda9ed00764534217652f9854168597785cd6505dc4ae1  q07_spotcheck_validity.py
```
