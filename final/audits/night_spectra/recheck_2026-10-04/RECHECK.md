# Recheck after fixes: night spectra (RULES §3.1 cross-agent check)

Date 2026-10-04. Tool: Claude Code subagent, model `claude-opus-5-5` (the same model as the builder and as the first audit, so the RULES §3.1 "ideally a different model" condition is not met). Fresh context. Scripts were run from `final/` with system `python3`, stdlib only. Nothing under `data/`, `pipeline/`, `app/`, `AI_LOG.md` or the existing `audits/night_spectra/` files was written. The pipeline was not run (`main()` was never called; r05 imports the module, which is guarded by `if __name__ == '__main__'`, using `python3 -B`, so no `__pycache__` was written). No git command that changes state was run.

## Summary

| Check | Result |
|---|---|
| Raw integrity: 4 raw files, size and SHA-256 vs MANIFEST, at start and end (r01) | **PASS.** All 4 match. Start and end snapshots (SHA-256, size, mtime, mode of the raw files, the 3 outputs and the script) are identical. |
| Independent extraction vs new outputs, every field, as text (r02, r03) | **PASS.** 47/47 checks. Irradiance text identical 67,440/67,440 per site; timestamp, night_id, solar and lunar elevation, lunar fraction text identical 240/240 per site; source_column = my 0-based column + 1 (240/240); n_source / n_night / n_selected, source and selected date ranges, data-quality counts (keys, order, text), selected-cell counts, meta `sites` block, display limits (n_positive 126,886, p01/p50/p99 text = repr of my floats, floor −9, ceil −5), wavelength grid 280..840 step 2 (281 values). |
| Same, as floats (r03) | **PASS.** All float-equal. No nulls (no NaN in any selected cell or metadata row). |
| Strict JSON (r03) | **PASS.** All 3 files: UTF-8, no NaN/Infinity tokens outside string literals, no duplicate keys. |
| Diff new vs previous outputs (r04) | **PASS** (only the intended changes; list below). Irradiance, source_column, timestamps, elevations, lunar fraction, counts, date ranges, data-quality counts, wavelength grid, selection rule text and display limits are unchanged. `night_id` changed as text only (240/240 per site, 0 numerically different). |
| F1 verbatim source text, NaN → null (r03, r05) | **PASS.** `night_id` now `1`…`9` (no `.0`), data-quality counts as source text. NaN → null tested only by a unit test of `raw('NaN')`; the data contain no NaN in the selection. |
| F2 night_id note (r05) | **PASS.** `night_id_note` present; its claims hold on all night spectra: 5 night blocks and 8 distinct ids per site; in-block changes at 01:05:39–01:06:37 (source time). |
| F3 unit + meta_file (r05) | **PASS.** Both site files: `unit` = `W m^-2 nm^-1` (= meta), `meta_file` = `spectra_meta.json` (exists). |
| F4 labels on every site-file field (r05) | **PASS.** Every field except the `labels`/`label_notes` containers has a label; every label used is explained in `label_notes`; `site`, `source_file`, `meta_file` labelled `identifier`. |
| F5 rules source, draft not in git (r05) | **PASS.** `selection.rules_from` cites `handoff 2026-10-04_two-nights-spectra.md` (file exists); `draft_reference` ends "(not in git)" (confirmed: `git ls-files` and `git log --all` return nothing for that path); old `reproduces` key gone. |
| F6 wavelength grid source (r05) | **PASS.** `wavelength_source` present (README Table S1 + MANIFEST; CSVs have no wavelength row). |
| R1 verbatim writing independent of key order (r05) | **PASS.** Recursive serializer `dump()`; unit tests: `Raw` values written unquoted as source text in first, middle and nested positions; `raw()` accepts 7 valid tokens unchanged and rejects 12 invalid ones (`nan`, `Infinity`, `-Infinity`, `1.`, `.5`, `+1`, `01`, leading/trailing space, empty, `1,0`, `0x1`); `dump(float('nan'))` raises. |
| R2 strict parse before write (r05) | **PASS.** `strict_parse` rejects NaN, ±Infinity and duplicate keys; `write_checked` with invalid text raises and creates no file. |
| R3 unchanged (r05) | **PASS (unchanged, as decided).** `even_sample` still returns all n when n ≤ 240. Not triggered (n = 1,200 and 1,268). |
| Selection index arithmetic (r02, r05) | **PASS.** Float `floor(x+0.5)` equals exact-integer round-half-up for n = 1,200 and 1,268 (no exact .5 ties) and for every n from 241 to 20,000. |
| RULES §2.5 units / time zone / filters (r05) | **PASS with notes.** Irradiance unit in site files and meta; elevation and fraction units, "no time zone in the source" and the selection rule are in `spectra_meta.json` only (site files point to it via `meta_file`). See C1, C3. |
| Script docstring vs code | **PASS with notes.** Matches the code; see C4. |
| RULES §3.2 spot-check sample still valid (r06) | **Yes.** Re-drawing seed 20261004 on the new outputs gives the same 20 cells; value text, CSV row, CSV column and timestamp identical in 20/20 rows of `audits/night_spectra/results/a06_spotcheck.md`. The human check itself was not performed or reported here. |

## Method and order

1. Read `RULES.md`, `CLAUDE.md`, the latest handoffs (`2026-10-04_two-nights-spectra.md`, `2026-10-04_two-nights-built.md`), the first audit's Findings F1–F6 and R1–R3, the MANIFEST, and the output structure (not the script).
2. `r01_raw_integrity.py start`.
3. `r02_independent_extract.py` written and run **before the pipeline script was read**: own parser (`str.split(',')`, after checking that the files contain no CR or quote characters; row 1's trailing empty field removed), night = `float(solar) < -18`, exact-integer index `(2*i*(n-1)+239)//478`, wavelength row = 6 + (wl − 280), own percentile. All values kept as source text (`results/r02_extract.json`).
4. `r03_compare_new.py`: every field of the new outputs vs r02, read with `parse_float=str, parse_int=str` (strict, no constants, no duplicate keys), then as floats.
5. `r04_diff_before_after.py`: new vs the previous outputs (scratchpad copy `spectra_before/`), as text and as floats, leaf by leaf.
6. Pipeline script read; AI_LOG rounds 3f–3h read (read only).
7. `r05_fix_checks.py`: F1–F6, RULES §2.5 items, unit tests of the script's pure functions for R1, R2, R3, selection and percentile.
8. `r06_spotcheck_validity.py`: same seed and RNG calls as `a06_spotcheck_sample.py`, run against the new outputs, compared with the existing table.
9. `r01_raw_integrity.py end` (compared with start).

## Diff new vs previous outputs (r04)

- **Site files (both):** added `unit`, `meta_file`, `label_notes` (`documented`, `inferred`, `measured`, `identifier`), and 15 `labels` entries (`site`, `place`, `paper_label`, `unit`, `meta_file`, `source_file`, `source_sha256`, `n_source_spectra`, `n_night_spectra`, `n_selected`, `source_date_range`, `selected_date_range`, `source_dataquality`, `selected_cells`, `source_column`). Removed `labels.selection`. Changed: `night_id` text (`1.0` → `1` etc.), 240/240 elements, numerically equal. The 6 existing value labels are unchanged. All other keys are identical as text.
- **spectra_meta.json:** added `wavelength_source`, `night_id_note`, `verbatim`, `selection.rules_from`, `selection.draft_reference`. Removed `selection.reproduces`. Everything else is identical as text, including `selection.rule`, `wavelength_nm` and all of `display_limits_log10`.
- These SHA-256 values match the ones recorded in AI_LOG round 3h.

## Findings

### Concerning or worth a human look (no value is wrong)

- **C1. `source_column` indexing base not stated in the outputs.** The values are 1-based CSV columns (= 0-based + 1, verified 240/240). This is stated only in a script code comment (line 224) and in `a06_spotcheck.md`, not in `philadelphia.json`, `cherry_springs.json` or `spectra_meta.json` (RULES §2.5: coordinate systems written down next to the data). This was the same before the fixes.
- **C2. Label vocabulary.** `identifier` (used for `site`, `source_file`, `meta_file`) is not one of the four RULES §2.3 labels. The brief says the human asked for identifiers to be marked as such. The `labels` and `label_notes` containers carry no label themselves.
- **C3. Site files are not self-contained for §2.5.** They hold the irradiance unit. Elevation and fraction units, the time-zone statement and the selection rule are only in `spectra_meta.json`, which is referenced by `meta_file`.
- **C4. Script notes (`pipeline/spectra/01_night_spectra.py`).**
  (a) R2 is per file: the three files are written one after another (site files first, meta last), each with a non-atomic `write_text`. A failure while checking or writing a later file would leave a mixed set of new and old files on disk. Not triggered.
  (b) `parse()` silently removes `\r` and strips whitespace from timestamps (`t.strip()`). That would change the timestamp text if it were present. Not triggered: there is no CR in either file, and all timestamps are exactly 20 characters.
  (c) The docstring's verbatim list (line 27) omits the data-quality counts, which the code (line 221) also writes verbatim. The rest of the docstring (rules, labels, output check, R3 note, round 3h reference) matches the code and AI_LOG.
  (d) The NaN → null path is never exercised by these data.
- **C5. Raw files not read-only.** MANIFEST says the raw files were "made read-only". In this worktree they are mode `0644` (owner-writable) with no immutable flag. Their content matches MANIFEST.
- **C6. Same model.** This recheck uses the same model as the builder (see header).
- **C7. Logging.** `CLAUDE.md` asks each session to append to `AI_LOG.md`. Per the brief, this recheck did not edit it; the main session logs it.

### Passes

All rows of the summary table. The selection rules, values, counts and display limits are unchanged by the fixes, and each of F1–F6, R1 and R2 is in place.

## Files created (all in `audits/night_spectra/recheck_2026-10-04/`)

`r01_raw_integrity.py`, `r02_independent_extract.py`, `r03_compare_new.py`, `r04_diff_before_after.py`, `r05_fix_checks.py`, `r06_spotcheck_validity.py`, `RECHECK.md`, and in `results/`: `r01_start.txt`, `r01_end.txt`, `r01_snapshot_start.json`, `r01_snapshot_end.json`, `r02_extract.json` (2.5 MB, selected cells as source text), `r02_log.txt`, `r03_compare_new.txt`, `r04_diff.txt`, `r05_fix_checks.txt`, `r06_spotcheck_validity.txt`.

## SHA-256 of audited files (unchanged from start to end of the recheck)

```
84fd2b83056bbf78058b19b4bc712bd7b07a685d2bd57398a727be70173bd899  data/derived/spectra/philadelphia.json
670472fef2a59c28478a4cd02a41ce9efefbbdb3a52033a10d2cee6dd91a5181  data/derived/spectra/cherry_springs.json
4446efd5fef22ac60d6d2b7a0f2e4dd35dd1b041ec0ac969f6d9286e57c3c2e3  data/derived/spectra/spectra_meta.json
be7688a4af0c66075e8f3b6c1e984403bfb63849a3815cc0170e04d95547f3af  pipeline/spectra/01_night_spectra.py
```

Recheck scripts:

```
abd526bfa1f3762f2fb86b48066c506b457678e8b1689ca3fd517b41ab1157d7  r01_raw_integrity.py
7931ccd5da3cff7e2189e3c44f8a810b65919194722b151a713a86e2d831f135  r02_independent_extract.py
a131e8c062eb543e33e658375acedd46b88ed5b9d5c58a025fbc69cb0e74030d  r03_compare_new.py
9637addc8efec32c84975449acb876c332b347493332ee632ceaf67c007c81ad  r04_diff_before_after.py
861375bfc3d4388c8632ac70ba0f061f7f935c4de0aaee2367b0cb776205ade9  r05_fix_checks.py
b794715e04cfaee4c996cf2332d524f71deeefb13f6383b0bef31c930d78185f  r06_spotcheck_validity.py
```

Note: r03 was first run with an over-broad NaN byte search, which matched the key text `"N NaN or Zero spectra"`. It was corrected to search outside string literals and re-run; `results/r03_compare_new.txt` is from the final run. r05 contains one check (C1, indexing base stated in the outputs) that reports FAIL; it is the only non-pass among the r03/r05 checks.
