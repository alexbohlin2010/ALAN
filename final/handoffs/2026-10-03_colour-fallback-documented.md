# Handoff: colour, documented 2025 fallback; lamp-pixel mask problem found

Written 2026-10-03. Follows `handoffs/2026-10-03_colour-night-only-grid.md`. Read `RULES.md` first.
- Log: `AI_LOG.md`, colour steps 49–54.
- Method: `pipeline/colour/METHOD.md`, section "Documented 2025 fallback".

## Human decisions (this session)
- The 2025 global fallback is **option 1**: 0.410 = 1 − sodium share of Brazil's public lighting points.
- Download the ABCIP census PDF (approved, done).
- **The pixel-mask fix is for the next session.**
- Still standing: values may be `estimated`; no legend; keep the VIIRS caveat.

## State
- `10_white_share_grid.py` has `FALLBACK_SHARE` {global: {2025: 0.410}} and `FALLBACK_SOURCE`.
- 2025 fallback: 0.410 / grey 159 (was 0.848 / 68). 2015 is unchanged: 0.184 / 203 (photo median).
- The grid PNG is byte-identical. The sidecar records `fallback_source` and `photo_share_median`.
- Raw files:
  - New `data/raw/colour/Censo-Iluminacao-Publica-Brasil.pdf` (12.2 MB).
  - New `data/raw/colour/MANIFEST.csv`.
  - Table 9, base ANEEL 2023: 19,362,437 points; sodium 59.0 %, LED 19.6 %, mercury 9.2 %, metal halide 7.2 %.
- Render checked at localhost:5173: no console errors; 2025 South America is mostly orange.
- Not audited (RULES §3). Nothing committed, nothing deleted.

## Facts found (step 49)
**Where the fallback paints in 2025** (lit pixels in cells with coverage < 0.5): 16.4 % of all lit pixels.
- South America 46.9 % (Brazil 25.1 %), Russia 14.8 %, sub-Saharan Africa 9.5 %, Northern Europe above 60° N 5.9 %, Australia 3.0 %.
- Central Asia is under 0.5 %.

**Kept 2025 photos:**
- 541 of 1,999 have their record point at sea (median 0.97).
- 682 have under 20 VIIRS pixels above 5 nW within ±0.25° of the record point (median 0.96, against 0.75 for the rest).
- Sub-Saharan Africa: 67 photos, mostly two machine-catalogued runs along the station track (ISS065-E-4370xx, ISS071-E-1687xx–1688xx); only 6 are over Johannesburg/Pretoria.
- The 32 "Syria" photos (ISS071-E-6112xx) show the Nile delta seen at a tilt.

## Facts found (step 51): lamp-pixel mask test
- **Method:** per-pixel re-run of the `12_thumb_cct.py` mask and the `14_frame_flags.py` point-like rule. It reproduces the stored shares exactly. 24 random kept 2025 photos (seed 20261003) were checked by eye.
- **What the mask counts as white:** airglow and the bright Earth limb (6 of 24 random frames).
- **Also counted:** stars in star-field frames, lit station hardware (3 of 24), lightning and cloud-diffused light (3 of 24).
- **Overall:** about 9–10 of 24 random frames had visible non-lamp light in the mask.
- **Stars and the city-frame rule:** in ISS065-E-437041, 1,193 of 1,949 point-like pixels are stars. Without them it has 756 and would fail the city-frame rule (≥ 800).
- **Share with all lamp pixels vs only those below a horizon row set by eye:**

  | Frame | All | Below horizon |
  |---|---|---|
  | ISS065-E-437041 | 0.88 | 0.51 |
  | ISS065-E-436628 | 0.63 | 0.52 |
  | ISS072-E-144994 | 0.93 | 0.91 |
  | ISS072-E-144841 | 0.89 | 0.98 |

  Size and direction vary.
- **Not tested:** whether the CCT of city lights is right. Several frames with visibly orange or mixed lights are mostly ≥ 2,700 K (e.g. ISS064-E-21869, ISS071-E-663867, ISS064-E-23814 Tokyo: G/R share 0.17 vs CCT share 0.97).
- **Location points:** ML record points are often the nadir, not the lights in a wide or oblique frame (Syria → Nile delta; Zimbabwe → a South African city).

## Sources found (steps 49, 52; full list in METHOD.md and the log)
- **Documented installed-base LED shares:**
  - World < 15 %, South America < 5 % (~2019–20, UNEP-DTU C2E2).
  - Brazil 19.6 % (base 2023, verified).
  - São Paulo 90 %, Buenos Aires 100 %, Bogotá ~56 %, Moscow ~50 %.
  - Australia ~57 % (not verified).
  - Finnish regions 45–60 %; Vestland 15 %.
  - South Africa 5 % (2015); Peru Distriluz 37 %.
- **Not found:** national figures for Russia, sub-Saharan Africa after 2015, Central Asia and most of South America.

## Open for the human
1. **Pixel-mask fix (decided: next session).** Approach not chosen. Problems seen: sky above the horizon (stars, airglow, limb), station hardware, lightning / cloud glow, and record point ≠ location of the lights in oblique frames. This changes the local and regional shares (and the 2025 photo median, now unused).
2. **2015 fallback (0.184, photo median):** same structure but a smaller effect (alternatives 0.15–0.22). It paints 7.8 % of lit pixels (Brazil, sub-Saharan Africa, Finland, Russia). Not changed.
3. **City CCT accuracy** (orange-looking lights counted ≥ 2,700 K): not tested.
4. **Still open from earlier:** more thumbnails per cell; more NEF checks; audits (RULES §3); deleting downloaded thumbnails / NEFs; git handling of `data/raw/colour/`.

## Scratch (session scratchpad only, not in the repo)
Analysis scripts:
- `fallback_facts.py`: photo countries, fallback coverage by country.
- `near_lights.py`
- `options.py`
- `lamp_overlay.py`, `sample_montage.py`, `sky_cut.py`: the mask test.

They are not in the repo. If the next session uses any of these numbers in data, the method should be redone as a repo script. The previous sidecar/PNG (step 47) is also in the scratchpad.

## Update 1 (AI_LOG colour steps 56–57): 2025 still looks white
- **Human:** "looks pretty white still no?" (screenshots: Europe / Middle East). Then: "option 1, write the handoff".
- **Human decision:** option 1. No interim change; the pixel-mask fix is the next session's task.
  - Not chosen: a single 0.41 for all 2025; documented country values plus 0.41; doing the fix in this session.
- **Fact:** the regions in the screenshots are coloured by the local / regional photo shares, not the fallback. The 0.41 fallback only fills cells that photos don't reach.
- **Share of lit pixels drawn white**, 2015 → 2025 (shader rule: mix(fallback, cell threshold, coverage), ±8 blend ignored; scratch `drawn_white.py`):

  | Group | Values |
  |---|---|
  | Europe | UK 0.05 → 0.62, Italy 0.10 → 0.62, Germany 0.10 → 0.51, Poland 0.07 → 0.55, Sweden 0.07 → 0.56, Spain 0.06 → 0.22, France 0.10 → 0.22 |
  | Middle East / Africa | Turkey 0.19 → 0.66, Egypt 0.17 → 0.91, Saudi Arabia 0.20 → 0.76, South Africa 0.09 → 0.98 |
  | Other | US 0.20 → 0.80, India 0.32 → 0.98, China 0.24 → 0.81, Russia 0.33 → 0.64, Brazil 0.14 → 0.35, Japan 0.81 → 0.99 |

- **Documented installed LED shares for comparison** (other years, LED only):
  - Spain 56 % (2017) vs 0.22 drawn.
  - UK 51 % (2019) vs 0.62.
  - US 48.6 % (2018) vs 0.80.
  - South Africa 5 % (2015) vs 0.98.
  - Brazil 41 % not-sodium (2023) vs 0.35.
- **For the next session:**
  - Read this handoff's "Facts found (step 51)" for the observed mask problems: sky / airglow / limb / stars, station hardware, lightning / cloud glow, record point ≠ location of lights in oblique frames.
  - Untested: CCT accuracy of city lights.
  - The drawn-white table above is a way to compare before and after a fix. It is not a target.
