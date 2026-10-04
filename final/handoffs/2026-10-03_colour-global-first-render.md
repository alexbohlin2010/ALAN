# Handoff: colour, global white-share grid, first render

Written 2026-10-03. Follows `handoffs/2026-10-03_colour-global-run.md`. Read `RULES.md` first.
- Log: `AI_LOG.md`, colour steps 27–31.
- Method: `pipeline/colour/METHOD.md`, section "Global run of the white-share grid".

## Human decisions (this session)
- **Query:** one box per mission, −56..+60 lat, all longitudes.
- **Layout:** `--pilot global` (works on every script; the default is still iberia).
- **Downloads:** thumbnails only at ≥ 50 mm, cap 5 per 1° cell per epoch. The human asked about cap 2, was shown the Iberia test (step 29), and chose cap 5. `PARALLEL_REQUESTS` = 5.
- **Grid:** 0.25°, threshold window 5×5 cells (±0.625°), output as PNG + JSON sidecar. The app uses the global grid.
- **Fallback:** global median photo share, with the global grey quantile.
- **Stronger-contrast variant:** deferred.
- **Wish (human):** after the exercise, delete the downloaded data and keep a textual record of what was used. **Not decided yet.** Open sub-questions, raised in step 29:
  - whether to also delete the 997 MB of query HTML and the 1,955 Iberia thumbnails;
  - the RULES §2.4 (rerun from raw) / §3 (audit) conflict: re-download, or audit before deleting.
  - Nothing has been deleted.

## State
- Thumbnails: `data/raw/colour/eol/small/`, 1.3 GB, about 27.6k files, `MANIFEST.csv` with URL + SHA-256.
- Query HTML: `data/raw/colour/eol/queries/2026-10-04/global/`, 997 MB.
- Derived:
  - `global_records.csv` (3.67M rows);
  - `global_thumb_pick.csv`;
  - `global_thumb_shares.csv` (20,707 usable);
  - `global_white_share_grid.png` + `.json`.
- Fallback: 2015 share 0.22 → grey 192; 2025 share 0.73 → grey 94. This replaced Iberia's 248 / 219 in the app.
- App files changed:
  - `app/src/tileLayer.js`: loads the PNG with the tiles' ImageBitmapLoader (flipY, no premultiplied alpha); thresholds from the sidecar.
  - `app/vite.config.js`: allow-list + `.png` type.
- First render checked in the browser: it loads and draws, with no console errors.
- Not audited (RULES §3). Nothing committed.

## Open question for the human: per-mission colour bias
Inside one region and epoch, some missions' photos come out almost entirely "white":
- Europe 2015: ISS041 0.98 vs ISS030–040 0.02–0.10.
- ISS064 1.00, ISS070 0.98 elsewhere too.

This is likely camera or processing settings, not lamps. It also raises the global fallback. Full numbers are in METHOD.md and AI_LOG step 31.

Options the agent listed (the human has not chosen):
- A: exclude missions whose median share in a reference region is far from the other missions'.
- B: normalise shares per mission.
- C: correct the colour per photo, using its own lamp colours as reference.
- D: keep as is.
- The fallback could also go back to the Iberia values.

## Still open from earlier
- Stronger-contrast variant.
- Tiles v2 / class raster / city-class files: keep or delete.
- RULES §3 audits for all colour data.
- Git handling of `data/raw/colour/`.
- Option 3 (per-pixel GeoTIFF colour): `GetGeotiff.pl` was down on 2026-10-03.

## Update (same session, AI_LOG colour steps 32–33)
- **Human:** "the 2025 global view is probably way too white". The human approved a white-balance correction and a web search.
- **Cause found:** the archive JPEGs were converted with varying white balance (XMP `crs:Temperature` 3,200–5,700 K; Auto / As Shot / Custom). Within one mission, auto-WB photos are much "whiter".
- **Correction tried** (`12_thumb_cct.py`, `global_thumb_cct.csv`): Bradford adaptation to the recorded temperature + McCamy CCT. **Failed the test.** Missions still disagree (Europe 2015: ISS030 2146 K vs ISS041 7215 K), and the shares got whiter. The grid and app were not changed.
- **Literature** (Sánchez de Miguel et al. 2021): JPEGs are not suitable for colour work. Use NEF raw files, calibrated.
- **Documented LED shares found:** US 12.7% (2014), 48.6% (2018); Spain 56% (2017); UK 51% (2019); South Africa 5% (2015). Full list in AI_LOG step 33.
- **Open:** choose a direction (options A–D given in chat, step 33). The app still shows the step-31 global render.

## Update 2 (AI_LOG colour steps 34–37)
- **NEFs:** available from the archive by request (queue, minutes per file), for ISS030–071; one ISS072 photo offers only a JPG. `rawpy` (LibRaw 0.22.1) installed with human approval. Pilot `13_nef_pilot.py`: 16 photos picked, 8 downloaded (`data/raw/colour/eol/nef/`), 8 queued.
- **Main 2015 bias cause:** daytime frames in the "night" pool (the archive's `nighttime` filter let them through). 92% of ISS041 and 58% of ISS042 Europe/US frames look like daytime. Without them those missions agree with the others.
- **2025:** missions still disagree after dropping day-like frames (ISS065/067 low, ISS064/070/072 high). Unresolved.
- **Open for the human:** how to exclude day frames (archive sun elevation from photo pages vs a brightness rule); how to resolve 2025 (NEF pairs from disagreeing 2025 missions on the same cities). The grid and app are unchanged since step 31.
