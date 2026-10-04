# Handoff: colour (CCT) pilot, Iberia, from ISS astronaut photos

Written 2026-10-03 at the end of the colour pilot session. Facts and human decisions only. The full record is in `AI_LOG.md` ("Colour (CCT) task, step 1" to "step 15", plus this handoff entry). Read `RULES.md` first. Method details for what was built are in `pipeline/colour/METHOD.md`.

## Human verdict on the pilot
- The human looked at the rendered pilot (city classes drawn as tinted 25 km discs) and said they **"look terrible for our purposes. Totally unrealistic."**
- **Next goal (human):** get to an answer **fast** on how the radiance tiles can show a much more **realistic** view of light colour (light temperature).
- **No legend.** The colour is to be "just a visual representation of light temperature" (human, 2026-10-03).
  - Possible tension, for the human to settle: the 2026-10-03 render-architecture handoff (decision 7) said any filler colour "must be labelled as a display choice per RULES". RULES §2.3 labels data values. The class data is labelled `estimated` in its files and in `METHOD.md`.

## Decisions the human made this session
- **Source:** ISS astronaut photos (NASA Gateway to Astronaut Photography, eol.jsc.nasa.gov). SDGSAT-1 is not used (no time).
- **Country/city lamp inventories:** not pursued (seen as a hassle and error-prone).
- **Method:** lamp-colour classes (M3), **broad strokes, not pixel-by-pixel accuracy, unless pixel-level turns out to be easy**. Every estimate must be documented clearly.
- **Each year gets its own colour.** Epoch "2015" = photos 2012–2015. Epoch "2025" = photos after 2020, as late as possible.
- **Photo pool:** human-catalogued and machine-learning-catalogued records. **No cataloguing or georeferencing of our own** ("too much work").
- **Pilot region:** Iberian Peninsula.
- **Option 3:** classify from processed images, not calibrated RAW files. Then **option 1**: full-size JPEGs located at city level, because GeoTIFF downloads failed.
- **Class boundaries were set by the human after seeing the data:** a pixel is "white" if linear G/R ≥ **0.8**. White share < 10% = mostly sodium, 10–50% = mixed, > 50% = mostly LED. The share cut-offs were proposed by the agent and accepted with "go for it".
- **Render choices:**
  - Area: lit pixels within 25 km of a city reference point.
  - Tints: blackbody colour at 2000 / 3000 / 4000 K.
  - **Baked into a new tile version v2.** Class bits go in B (bits 3–4 = 2015, bits 5–6 = 2025). The class raster is stored in its own file. v1 is untouched.
  - Coarser zoom levels: the class carrying the most radiance in a block wins.
- **The VIIRS caveat must be kept in the documentation:** VIIRS DNB under-detects the blue part of white-LED light. A tint changes the hue only and does not correct DNB brightness, and a sodium → LED switch can read as dimming.

## What exists now
- `pipeline/colour/` (run from `final/` with `.venv/bin/python`):
  - `config.py`: paths, Iberia box, epochs, missions, pool, retries, `PARALLEL_REQUESTS`, test cities, class rule, tints. It forces **IPv4** because the archive's IPv6 address does not answer from this network. Without that, Python stalls about 90 s per request.
  - `01_query_eol.py`: night photos in a lat/lon box via the archive's public CoordinateRangeSearch (no API key needed). Saves the responses to `data/raw/colour/eol/queries/2026-10-03/iberia/` and writes `data/derived/colour/iberia_records.csv`.
  - `02_photo_details.py [--sample N --seed S]`: parses each photo's page (nadir, centre, ML centre, camera, focal length, tilt, cloud cover, raw file offered, GeoTIFF offered). Pages are cached in `data/raw/colour/eol/photos/`. Known parser quirk: an empty field picks up the next label.
  - `03_fetch_images.py --kind jpeg|geotiff IDS…`: human-approved downloads only. Size cap, file-signature check, SHA-256 in `MANIFEST.csv`.
  - `04_colour_ratios.py [--name=N] IDS…`: G/R and B/G of bright pixels (brightest channel 40–249, linear sRGB). Writes JSON plus `previews/colour/ratios_<name>.html`.
  - `05_select_city_photos.py`, `06_classify_cities.py`, `07_class_raster.py`, `08_display_tints.py`, `METHOD.md`.
- **Data:**
  - `data/raw/colour/eol/jpeg/`: 10 JPEGs, read-only, with a manifest.
  - `data/derived/colour/`: records, sample details, city photos, ratios, `iberia_city_classes.csv`, `classes/iberia_classes_v1.tif` and `.json`, `display_tints.json`.
- **Tiles:**
  - `pipeline/radiance/05_build_tiles.py` now takes an optional `--version vN --classes PATH`. Without the option it still writes v1.
  - `data/derived/radiance/tiles/v2/` was built (20,333 tiles). Spot check of 600 tiles: R, G and the no-data flags are identical to v1.
- **App:** `app/src/tileLayer.js` shader decodes the class bits and draws grey × tint. Class 0 stays grey, and v1 tiles render unchanged. `main.js` was not touched (other sessions were editing it).
- **Preview:** `~/.claude/launch.json` entry `alan-final-app-colour-v2` (port 5174, `VITE_TILE_BASE=/tiles/v2/`). It may still be running.
- **Scratchpad only, not in the repo:** the global night-photo counts and their query responses (about 0.9 GB HTML) from this session.

## Facts learned
- **Archive size.** Night photos in the archive, worldwide:

  | | 2012–2015 | 2021–2026 |
  |---|---|---|
  | Night photos | 663,011 | 2,976,187 (2025 alone: 1,395,552) |
  | Human centre point | 5,904 | 338 |
  | ML-catalogued | 173,973 | 85,223 |
  | Uncatalogued (only the station's nadir known) | the rest | the rest |

  - Wide-angle (≤35 mm) frames are numerous, but almost all are uncatalogued.
  - The ISS reaches only about ±52° latitude when looking straight down.
- **Iberia box:**
  - 20,133 night records. The pool is 988 for 2012–2015 and 967 for 2021+. The 2021+ pool is mostly 2021–2022, with only 38 photos from 2024–2025.
  - A 60-photo sample (seed 20261003) showed:
    - Cameras: Nikon D3S/D4 (2012–15) and D5 (2021+). The 2021 calibration paper covers all of these; a Nikon Z 9 appears in 2024 elsewhere.
    - Raw files: offered for all 60.
    - **GeoTIFF:** offered for 9 of 60, all 85–400 mm city-scale frames.
    - Locations: most ML-catalogued pages give only the station's nadir, not an image centre.
- **GeoTIFF download (`GetGeotiff.pl`) failed on 2026-10-03:** HTTP 502, or HTTP 200 with 0 bytes. The JPEGs (`DatabaseImages/ESC/large/<MISSION>/<ID>.JPG`) download fine.
- **NASA's API** (`PhotosDatabaseAPI.pl`, JSON) needs a free key requested by email. Not requested.
- **Calibrated method:** Sánchez de Miguel et al. 2021 (RSE, doi:10.1016/j.rse.2021.112611) needs RAW files, star calibration and atmospheric correction.
- **Existing calibrated products:**
  - Europe, pre/post 2013 (Zenodo 6638505, CC BY 4.0). The old folder's copies were noted as broken.
  - ESA/Cities at Night Europe mosaic from 2017, about 100 m. No data download found.
  - UCM Iberia mosaic: 16 images, 2008–2012.
  - A newer NASA portal/API for georeferenced ISS imagery is described in NTRS 20240004906. Its URL was not found.
- **Colour observations from the 10 JPEGs:**
  - Within photos, colour varies at street and neighbourhood scale. Madrid 2021 shows orange and white districts side by side.
  - The G/R position of orange shifts between photos: two 2012 Lisbon photos give medians of 0.17 and 0.40. White sits near G/R ≈ 1.0 in the 2021–22 photos.
  - Valencia 2022 is mostly white (white share 0.74). The other 2021 photos have shares of 0.12–0.15, and all 2012 photos 0.016–0.058.
- **Rendering observations** (agent's description of screenshots):
  - The tinted discs have hard edges, and city cores look flat because the hist_eq greys are near 255 there.
  - Unclassified light is drawn neutral white, so it looks cooler than the "mostly LED" tint.

## Open (human decides)
- How to get a realistic look fast. The human has not chosen an approach yet.
- Keep, replace or delete tiles v2, the class raster and the shader change.
- The legend/label tension noted above.
- RULES §3 audits for any colour data that is kept.
- Git handling of `data/raw/colour/`.

## Next task
Present short options, with trade-offs, for making the radiance tiles show realistic light colour fast. Then wait for the human's choice.
