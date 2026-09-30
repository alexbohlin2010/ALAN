# Alexander — Earth After Dark + street-lighting colour

Two connected pieces of work on artificial light at night (ALAN):

1. **Street-lighting colour for 50 VIIRS cities** — what lamps (CCT, LED share, melanopic DER) each city's
   streetlights actually are, from retrofit contracts, tenders and official documents.
2. **Earth After Dark** — a globe comparing VIIRS night lights in 2012 and 2024 at native 500 m resolution,
   with an estimated, fully documented light colour per pixel.

## Run the globe

Needs only Python 3 (no packages):

```
python3 Alexander/globe_v2/serve.py
```

Open http://localhost:8766. Drag the divider to compare 2012 (left) with 2024 (right); scroll to zoom;
click a city in the list. **Colour / Brightness / Source** (top right) switch between the estimated
colour, raw VIIRS brightness, and where each pixel's colour came from. Stop the server with Ctrl+C.

## What is measured and what is estimated

- **Brightness is measured** (VIIRS Day/Night Band, VNL v2.1 annual composites).
- **Colour is estimated.** VIIRS cannot see colour. Colour is shown only inside cities with lamp-stock
  evidence, in both years; elsewhere a fixed "typical night light" tone is shown in both years so the
  swipe never shows false change. Read `colour/METHOD_colour.md` before citing any colour.
- The sensor under-reads white LED relative to sodium: a sodium → 3000 K LED conversion reads ~28 %
  dimmer at equal visual brightness, mostly because VIIRS credits sodium's 819 nm near-infrared line.

## Contents

| Path | What |
|---|---|
| `globe_v2/` | The app: `index.html`, `cities.json`, `serve.py`, and `tiles_rgba/` (2012, 2024; z0–z9). `tiler.py` builds tiles from the VIIRS rasters. |
| `colour/` | Colour estimation: `METHOD_colour.md` (method, rules, biases, audit steps), `city_colour_compositions.csv` (every judgement call with its evidence), `city_colour_audit.csv`, `lamp_class_xy.csv`, ISS validation for Madrid, and the scripts. |
| `data/alan_streetlight_cct_50cities.csv` | Main table: city, CCT, lamp tech, LED share, retrofit dates, melanopic DER, confidence, sources. |
| `data/lamp_class_reference.csv` | Per-lamp-type melanopic DER, blue fraction, VIIRS response per lumen (from measured spectra). |
| `data/research_rows/` | Raw per-region research notes and source links behind the main table. |
| `scripts/` | Spectral computation (`compute_spectra.py`, `lamp_classes.py`) and table build (`build_csv.py`). |
| `docs/` | Satellite colour-data review (`satellite_colour.md`), earlier project handoff notes. |
| `DATA.md` | Large inputs not in the repo: where to get them and how to rebuild. |

## Known gaps

- 14 of the 50 cities were not researched (Kano, Khartoum, Baghdad, Cairo, Alexandria, Riyadh, Tel Aviv,
  Jinan, Qingdao, Zhengzhou, Dalian, Shijiazhuang, Ningbo, Shantou). Blank rows mean *not researched*,
  not *no LEDs*.
- No city-wide lamp-colour documentation was found for any of the 7 Sub-Saharan African cities — a finding
  in itself.
