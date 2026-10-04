# Lamp-colour classes: how the estimate is made (pilot: Iberia, 2026-10-03)

Status: **pilot / test**. Every class value is labelled `estimated`, and was requested by a human (Alexander, 2026-10-03), who asked for broad strokes rather than pixel-by-pixel accuracy. Decisions are recorded in `AI_LOG.md` (Colour task, steps 1–15).

## What the classes mean
| Code | Class | Rule (per photo) |
|---|---|---|
| 0 | no estimate | no photo used for this place and epoch |
| 1 | mostly sodium | white share < 10% |
| 2 | mixed | white share 10–50% |
| 3 | mostly LED | white share > 50% |

"White share" = the fraction of a photo's bright pixels whose linear G/R ≥ 0.8.

## Steps (scripts in `pipeline/colour/`, run from `final/`)
1. `01_query_eol.py`: list night photos in the Iberia box (35.5–44.0°N, 10.0°W–4.5°E) from the NASA Gateway to Astronaut Photography (eol.jsc.nasa.gov), expeditions ISS030–046 and ISS064–075. Epochs: "2015" = photos from 2012–2015; "2025" = photos from 2021 on. Pool = human-catalogued (with centre point) and machine-learning-catalogued records. We did no cataloguing of our own.
2. `05_select_city_photos.py`: one photo per test city (Madrid, Lisbon, Barcelona, Valencia) and epoch: focal length 50–400 mm, centre within 0.25° of the city's reference point (approximate centre, typed by the agent), human-catalogued first, then nearest. The centre is confirmed on the photo's archive page.
3. `03_fetch_images.py --kind jpeg`: download the archive's full-size JPEG (public domain; credit "Image courtesy of the Earth Science and Remote Sensing Unit, NASA Johnson Space Center"). SHA-256 values are in `data/raw/colour/eol/jpeg/MANIFEST.csv`.
4. `06_classify_cities.py`: bright pixels = brightest channel 40–249 (8-bit). Convert sRGB to linear (IEC 61966-2-1). White = G/R ≥ 0.8. The class follows from the white share (table above).
5. `07_class_raster.py`: on the radiance grid (EOG VNL, 15″, EPSG:4326), each pixel that is lit that year (radiance > 0) and whose centre is within 25 km of the city reference point gets the city's class for that epoch. All other pixels: 0. Output: `data/derived/colour/classes/iberia_classes_v1.tif` (band 1 = 2015, band 2 = 2025) + `.json`.
6. `pipeline/radiance/05_build_tiles.py --version v2 --classes …`: class bits go into the tiles' blue channel (bits 3–4 = 2015, bits 5–6 = 2025). At coarser zoom levels, the class carrying the most radiance in a block wins, with "no estimate" included as a competitor.
7. Display (`app/src/tileLayer.js`): class pixels are drawn as grey × the blackbody colour of the class's nominal CCT (2000 / 3000 / 4000 K), from `08_display_tints.py`. This is a display choice. A class is not a measured CCT.

## Limits (read before using or showing this)
- **Uncalibrated.** The JPEGs are processed camera images: white balance, tone curve, lens vignetting and the atmosphere are not corrected. This departs from the published calibration method (Sánchez de Miguel et al. 2021, *Remote Sensing of Environment*, doi:10.1016/j.rse.2021.112611), which needs RAW files and star/atmosphere corrections.
- **The scale shifts between photos.** Two 2012 Lisbon photos taken with the same camera model put orange at G/R 0.17 and 0.40. The white cut-off (0.8) was chosen because white light sat near G/R ≈ 1.0 in the 2021–22 photos where it appears. This is an observation from 8–10 photos, not a calibration.
- **One photo per city and epoch.** Clouds or haze (e.g. Lisbon 2021), lens choice and framing all affect the result. The photo dates (2012, 2021–22) are not the radiance years (2015, 2025).
- **City level only.** Each class covers a 25 km circle, so it doesn't show real neighbourhood differences, and it ends at the circle's edge.
- **Satellite caveat.** The brightness comes from VIIRS DNB, which under-detects the blue part of white-LED light. A tint changes the hue only and does not correct the DNB brightness. A switch from sodium to LED can therefore look like dimming in the radiance data.
- Not audited yet (RULES §3).

---

# Display ramp (option B, human choice 2026-10-03): replaces the city-disc render in the app

Status: **prototype / first look**. Chosen by the human (Alexander) on 2026-10-03 after the disc render was judged "totally unrealistic". No legend (human). AI_LOG colour steps 17–18.

## What is drawn
Every lit pixel is drawn as grey × tint. The tint is **sodium (blackbody 2000 K)** below the year's grey threshold and **white LED (blackbody 4000 K)** above it, with a soft blend of ±8 grey levels. The brightest pixels turn white first. Shader: `app/src/tileLayer.js`. It works on tiles v1 and v2 and ignores the v2 class bits.

## How the thresholds are set (`09_display_ramp.py` → `data/derived/colour/display_ramp.json`)
| Year | White share | Label | Grey threshold | Label |
|---|---|---|---|---|
| 2015 | 0.0349 (median of Madrid 0.016, Lisbon 0.038, Barcelona 0.058, Valencia 0.032) | `estimated` | 248 | `inferred` |
| 2025 | 0.1518 (median of 0.153, 0.151, 0.123, 0.738) | `estimated` | 219 | `inferred` |

- The white shares come from the classes above: one uncalibrated JPEG per city and epoch, white = linear G/R ≥ 0.8.
- Threshold = the (1 − share) quantile of the display grey (the tile curve `hist_eq_p9999.json`) over lit pixels (radiance > 0) inside the Iberia box. So the share of Iberia's lit pixels drawn white equals the year's share.

## Limits
- **Which** pixels are white (the brightest) is a **display choice**, not an observation. The photos show white and orange districts side by side, not white cores.
- The same thresholds are used **worldwide**. Outside Iberia this is a display choice only: no photo was used there.
- All the limits of the class estimate above apply (uncalibrated, scale shifts between photos, 4 cities, photo dates ≠ radiance years).
- **Satellite caveat (kept):** VIIRS DNB under-detects the blue part of white-LED light. The tint changes the hue only and does not correct the DNB brightness, so a sodium → LED switch can look like dimming.

---

# Regional white-share grid (Iberia, 2026-10-03): adds regional variation to the display ramp

Requested by the human (Alexander) on 2026-10-03 after option B was judged too uniform ("some areas are sodium, some are LEDs"). Values are `estimated` (human: "That's fine if values are estimated"). Script: `10_white_share_grid.py`, whose docstring has all the rules. AI_LOG colour steps 22–24.

## Steps
1. **Thumbnails.** All 1,955 pool photos (human centre point + ML-catalogued, epochs as above), from the archive's `small` thumbnails (640 px). Downloaded by `03_fetch_images.py --kind small --pool` to `data/raw/colour/eol/small/`: read-only, SHA-256 in the manifest, 132 MB.
2. **White share per photo** → `iberia_thumb_shares.csv`.
   - Only lenses ≥ 50 mm.
   - Bright pixels: brightest channel 40–249.
   - Only lamp-like colours count: linear G/R ≤ 1.3 and B/G ≤ 1.2. This drops airglow and twilight glow.
   - White = G/R ≥ 0.8 **and** B/R ≥ 0.5. Some photos render sodium yellow (G/R ≥ 0.8) but with little blue.
   - Photos with < 200 such pixels are skipped.
   - Photos used: 2015 = 346, 2025 = 294.
3. **Grid.** 0.25° cells over the Iberia box.
   - Cell share = Gaussian-weighted (σ 0.5°) **median** of the photo shares.
   - Coverage = 1 − exp(−Σweights / 2).
   - Grey threshold = the (1 − share) quantile of display grey over lit pixels within ±0.5°.
   - Output: `iberia_white_share_grid.json`.
4. **Shader.** The threshold = mix(the year's Iberia-wide threshold from `09_display_ramp.py`, the cell's threshold, coverage). Outside the box, or where there are no photos, the result is option B unchanged.

## Checks done
- Thumbnail vs full-size JPEG white share for the four 2015 city photos, under the earlier G/R-only rule: 0.013/0.016, 0.031/0.038, 0.057/0.058, 0.024/0.032.
- Seville 2015 first came out at 0.32. Two photos (ISS034-E-5863/5864) render sodium yellow. The B/R rule and the median bring it to 0.06.

## Limits
- All the limits above apply: uncalibrated JPEGs, the colour scale shifts between photos, photo dates ≠ radiance years (2025 photos are mostly 2021–22).
- **Locations.** The record point of ML-catalogued photos may be the station nadir, not the image centre, so it can be off by tens to hundreds of km for tilted frames.
- **Thin 2025 coverage.** Only 583 of 2,065 cells have coverage > 0.5 for 2025 (2015: 1,387). The north (Bilbao, Zaragoza) has almost none.
- **The median smooths out real outliers.** For example, Valencia 2025 is 0.07 in the grid, while the one full-size photo used for the city classes gave 0.74.
- **Saturated city cores.** The display grey saturates in big-city cores, so the local thresholds there sit at 246–255, and white shows mainly in mid-size towns and coastal strips.
- **Satellite caveat (kept):** VIIRS DNB under-detects the blue part of white-LED light. The tint changes the hue only, not the DNB brightness, so a sodium → LED switch can read as dimming.
- Not audited (RULES §3).

---

# Global run of the white-share grid (2026-10-03): first render

Human request 2026-10-03 ("run the regional white-share grid … for the whole globe"). Values `estimated`. No legend (human). Choices made by the human: AI_LOG colour steps 27–30. Same per-photo rules as the Iberia grid above.

## Steps (run from `final/`, `--pilot global`)
1. **Query.** `01_query_eol.py`: one box per mission, −56..+60 lat, all longitudes, night only, ISS030–046 and ISS064–075.
   - Raw responses: `data/raw/colour/eol/queries/2026-10-04/global/`, 997 MB.
   - Records: `global_records.csv`, 3,672,847 records; 265,408 in pool; 72,880 at ≥ 50 mm.
2. **Pick.** `11_pick_thumbs.py`: at most 5 thumbnails per 1° cell per epoch (centre-point records first, then random, seed 20261003). Thumbnails already here (655 Iberia) always count.
   - Result: `global_thumb_pick.csv`, 26,356 photos.
   - Downloaded 25,701 new (0 failed) by `03_fetch_images.py --kind small --pick`. The thumbnail folder is now 1.3 GB.
3. **Grid.** `10_white_share_grid.py`.
   - Photo shares → `global_thumb_shares.csv`: 20,707 of 26,356 usable (the rest have < 200 lamp-like pixels).
   - Grid: 0.25°, 1440 × 464 cells.
   - Threshold window: 5×5 cells (±0.625°; human, was ±0.5°), computed from one pass over the COG with a grey histogram per cell.
   - Output: `global_white_share_grid.png` (R/G thresholds, B/A coverage) + `global_white_share_grid.json` (extent, parameters, fallbacks).
4. **Fallback** (no photos nearby), human choice:
   - White share = median of all usable photo shares of the year (`estimated`).
   - Grey threshold = its (1 − share) quantile over all lit pixels in the grid (`inferred`).

   | Year | Photos | Fallback share | Fallback grey | Cells with coverage > 0.5 |
   |---|---|---|---|---|
   | 2015 | 14,185 | 0.2207 | 192 | 47,439 |
   | 2025 | 6,522 | 0.7277 | 94 | 24,526 |

5. **App.** `app/src/tileLayer.js` loads the PNG grid and the sidecar's fallback thresholds. These replace the Iberia-wide 248/219 everywhere.

## Checks done
- The new grid code reproduces the old Iberia grid's white share exactly (cells with coverage > 0.01).
- Thresholds differ by a median of 1 (2015) and 3 (2025) grey levels, because of the wider window. Worst cells were checked against an exact quantile over the ±0.625° window and are equal.
- Cap 2 / cap 5 vs all photos, on Iberia: AI_LOG colour step 29.

## Limits (read before using or showing this)
- **Strong per-mission colour bias (found in this run).** Inside one region and epoch, photos from some missions come out almost all "white" while the others are mostly sodium.
  - Europe 2015, median share: ISS030–040 0.02–0.10; ISS041 0.98 (n 96); ISS033 0.74 (n 23); ISS064 1.00 (n 24).
  - US/Canada: ISS041 0.97 and ISS070 0.98, against ISS030 0.05.
  - This points to camera / white-balance / processing settings per mission, not lamps. Where one such mission dominates a cell, the cell's white share reflects the camera, not the lights.
  - The global fallback shares (0.22 / 0.73) are pulled up by this too.
  - No correction is applied yet. Options are a human decision (AI_LOG colour step 31).
- **Thumbnails per 1° cell are capped at 5.** Well-photographed regions use fewer photos than are available. On Iberia this cut coverage from a median of 0.90 to 0.79 (2015) and from 0.91 to 0.62 (2025).
- All earlier limits apply:
  - uncalibrated JPEGs;
  - ML record points may be the station nadir;
  - photo dates ≠ radiance years;
  - saturated city cores;
  - which pixels are white (the brightest) is a display choice.
- **Coverage stops at about ±52° latitude.** Outside it, there is the fallback only.
- **Satellite caveat (kept):** VIIRS DNB under-detects the blue part of white-LED light. The tint changes the hue only, not the DNB brightness, so a sodium → LED switch can read as dimming.
- Not audited (RULES §3).

## Frame flags: daytime and non-city frames (2026-10-03, AI_LOG colour steps 39–40)
Human choice: option D (sun elevation OR brightness). `14_frame_flags.py --pilot global` → `global_frame_flags.csv`, one row per photo of `global_thumb_shares.csv`. Values `inferred`; the rules are the agent's own and not validated.
- `sun_elev_deg`: solar elevation at the camera's EXIF capture time (read as UTC) and the record's lat/lon (NOAA solar-position equations). From the nadir point it reproduces the archive's "Sun Elevation Angle" on all 89 saved photo pages (|diff| ≤ 0.7°).
- `twilight_or_day` = sun ≥ −12°. `bright_frame` = thumbnail median of the brightest channel ≥ 40. `exclude` = either.
- Result: 26,356 photos; 1,591 twilight_or_day, 3,605 bright_frame, 5,160 excluded. Of the 20,707 usable photos, 4,061 are excluded.
- **Wrong camera clocks:** sun elevation inherits the camera time. ISS041's daytime frames (e.g. ISS041-E-90094, Gibraltar in sunlight) come out below −40°. The archive's sun elevation and its `nighttime` filter seem to use the same time. Only the brightness flag catches these frames.
- **Aurora, moonlit cloud, lightning (limit):** the "night" pool also holds night frames without city lights. In 5 random bright night frames (seed 20261003): 3 aurora, 2 moonlit cloud with lightning; white shares 0.22–0.99. Aurora and moonlight pass the lamp-like pixel rules often enough to give a high white share, and the frame's record point can be over the ocean or far from any city. The brightness flag drops the bright ones. Dimmer aurora / moonlit frames under the threshold stay in and can colour cells with no cities (e.g. ISS030-E-36159, aurora, record point at −25° lat, share 0.99, before flagging).
- Not yet used by the grid (step 3 pending human confirmation).

### Grid rebuilt without flagged frames (2026-10-03, AI_LOG colour step 42)
Human: "step 3, rebuild the grid". `10_white_share_grid.py` now leaves out photos with `exclude` = 1 in `<pilot>_frame_flags.csv` (grid and fallback). Per-photo shares are unchanged (`global_thumb_shares.csv` is byte-identical). These numbers replace the table in step 4 above:

| Year | Photos used | Flagged out | Fallback share | Fallback grey | Cells with coverage > 0.5 |
|---|---|---|---|---|---|
| 2015 | 10,852 | 3,333 | 0.1543 | 212 | 40,735 |
| 2025 | 5,794 | 728 | 0.6786 | 104 | 22,184 |

The 2025 per-mission disagreement (ISS065/067 low vs ISS064/070/072 high, AI_LOG step 37) is not resolved by the flags and remains in this grid.

## 2025 fix: city frames only + white-balance-corrected share (2026-10-03, AI_LOG colour steps 44–45)
Human: "fix 2025 color now using NEF or whichever method helps us to get it right".
- **Cause of the 2025 mission disagreement** (step 44):
  1. Non-city frames in the pool: the Moon, lightning, moonlit cloud, aurora, horizons, the station. In 30 random 2025 frames with share ≥ 0.7, about 9 were the Moon and 8 lightning / cloud.
  2. The archive's conversion white balance: ISS067 at ~5,300 K vs ISS065/066 at ~3,400 K, both with the same camera (D5).
- **City-frame flag** (`14_frame_flags.py`, `city_frame`): ≥ 800 point-like lamp pixels and ≥ 10 % of lamp pixels point-like (brightest channel ≥ 2 × its 15×15 box mean). Agent rule, tuned on 30 labelled frames and checked by eye on 90 more (seeds 1 and 7). `inferred`.
- **Share:** the grid now uses the white-balance-corrected share from `12_thumb_cct.py` (lamp pixels ≥ 2,700 K), not the G/R share (`SHARE_SOURCE` = "cct" for global).
- **Check against NEF raw files** (camera matrix, daylight multipliers, same CCT rule; scratch script, step 44): median CCT agrees within ~130 K on 8 of 10 night frames. The two frames converted at 2,850 K come out too white in the JPEG (CCT 3,650 / 2,678 K vs NEF ~2,220 K; white share 0.68 / 0.49 vs 0.21 / 0.19).
- **After the fix, city frames, white share by mission** (median, Europe / US):
  - 2015: EU 0.04–0.33, US 0.13–0.35.
  - 2025 US: ISS065 0.83, ISS066 0.82, ISS067 0.79, ISS069 0.83, ISS072 0.97.
  - 2025 EU: ISS065 0.18, ISS066 0.33, ISS067 0.22; ISS071 (2024) 0.77, n 29; ISS064 0.89, n 11.

| Year | Photos used | Fallback share | Fallback grey | Cells with coverage > 0.5 |
|---|---|---|---|---|
| 2015 | 2,683 | 0.1844 | 203 | 17,683 |
| 2025 | 1,999 | 0.8480 | 68 | 10,278 |

**Limits of this fix**
- **Coverage fell by about half.** Mean coverage 2025: Europe 0.15, US 0.11, India 0.03. Most lit cells now show the global fallback. In 2025 that fallback (0.85) is driven by Asia / India / Latin America frames and is much whiter than Europe's city-frame values.
- **The city-frame rule is the agent's own and was checked by eye only.** Some kept frames still contain lightning; some dropped ones are wide horizon frames with real cities.
- **Low conversion temperatures** (≤ ~2,900 K) can still overstate white share (2 of 10 NEF checks).
- **Only 10 NEFs checked**, all D3S (ISS030) and D5 (ISS066). Not checked: D4 and Z 9 cameras, and conversions at ~5,300 K.

### Regional fallback (2026-10-03, AI_LOG colour step 47)
Human: "regional fallback, then render again. 2025 too white globally".
- `10_white_share_grid.py`, global only (`REGIONAL`): a second Gaussian-weighted median share on a 1° grid, sigma 5°, cut at 3 sigma (15°), from the same city-frame photos.
- Per 0.25° cell: share = (cov_l·share_l + (1 − cov_l)·cov_r·share_r) / cov, with cov = cov_l + (1 − cov_l)·cov_r. The PNG's coverage channel is this cov, so the global fallback (0.184 / 0.848) applies only to the remainder. No app change.
- Sigma and cut are the agent's choice. `estimated` (share), `inferred` (coverage, thresholds).
- Cells with coverage > 0.5: 2015 143,406 (was 17,683); 2025 128,834 (was 10,278).
- Mean coverage 2025 (was): Europe 0.88 (0.15), US 0.78 (0.11), India 0.67 (0.03), E China 0.97 (0.20), Africa 0.28 (0.01).
- **Limit:** a regional share spreads a few cities' values up to ~15° away. Sparse regions (much of Africa, Central Asia) still lean on the global fallback, which is 0.85 in 2025.

### Documented 2025 fallback (2026-10-03, AI_LOG colour steps 49–54)
Human: "option 1, download the PDF". `10_white_share_grid.py`, `FALLBACK_SHARE` (global, 2025 only).
- **Why:** the photo median (0.848) was not a defensible global value.
  - The 2025 kept photos lean to East Asia and the Middle East.
  - 682 of 1,999 have no VIIRS city lights near their record point (median 0.96).
  - Airglow, stars, the Earth's limb and station hardware pass the lamp-pixel mask and count as white (step 51).
- **What the fallback paints** (2025, lit pixels in cells with coverage < 0.5, 16.4 % of all lit pixels): South America 46.9 % (Brazil 25.1 %), Russia 14.8 %, sub-Saharan Africa 9.5 %, Northern Europe above 60° N 5.9 %, Australia 3.0 % (step 49).
- **Value:** 2025 fallback white share = **0.410**, grey threshold **159** (was 0.848 / 68).
  - 0.410 = 1 − sodium-vapour share of Brazil's public lighting points.
  - Source: ABCIP, *Censo da Iluminação Pública Brasil – Base 2023*, published September 2024, Table 9 (ANEEL data), `data/raw/colour/Censo-Iluminacao-Publica-Brasil.pdf`.
  - Table 9 counts 19,362,437 points: sodium 59.0 %, LED 19.6 %, mercury vapour 9.2 %, metal halide 7.2 %, other 5.0 %.
  - "Not sodium" was chosen (human) because the photo white share counts all lamps ≥ 2,700 K (LED, metal halide, mercury, fluorescent), not LED only. It also includes incandescent 0.5 % and other 2.3 %.
- **Labels:** the Brazil shares are `documented`. Using them for all fallback regions is `estimated` (requested by the human). Grey threshold `inferred` (same rule as before).
- **The photo median is kept in the sidecar** (`photo_share_median`) with `fallback_source`. 2015 is unchanged (photo median 0.184 / 203).
- **The grid PNG is byte-identical**; only the sidecar's 2025 fallback changed.
- **Other documented installed-base shares found** (not used; AI_LOG step 52):
  - World < 15 % and South America < 5 % (~2019–20, UNEP-DTU C2E2 2021).
  - City figures: São Paulo 90 % (2021), Buenos Aires 100 % (2019), Bogotá ~56 % (2022), Moscow ~50 % (2023).
  - Australia ~57 % (IPWEA via AEMC, not verified).
  - South Africa 5 % (2015). Peru Distriluz 37 % (2025).
  - No national figure was found for Russia, sub-Saharan Africa (after 2015) or Central Asia.

**Limits**
- **One country's value for all fallback regions.** Brazil may not represent Russia, sub-Saharan Africa or Australia.
- **Base 2023, not 2025.** The census notes the utility records may lag ongoing modernisation.
- **A share of lamp points, not lit area or light output.**
- **The local and regional shares still come from photos.** Those photos have the mask problems of step 51 (airglow, stars, limb, station). This is not fixed: the human deferred the pixel fix to the next session.
- **Seams are possible** where photo-based white regions border fallback regions.
- **VIIRS caveat (kept):** VIIRS DNB under-detects the blue part of white-LED light. The tint changes the hue only, not the DNB brightness, so a sodium → LED switch can read as dimming.
- **Not audited** (RULES §3).
