# Handoff: colour, global run of the regional white-share grid

Written 2026-10-03. Follows `handoffs/2026-10-03_colour-regional-grid.md`, which has the full Iberia detail. Read `RULES.md` first. Log: `AI_LOG.md`, colour steps 17–25. Method: `pipeline/colour/METHOD.md` (sections "Display ramp (option B)" and "Regional white-share grid").

## Human decisions so far
- Source: ISS astronaut photos (NASA Gateway to Astronaut Photography). No cataloguing or georeferencing of our own. Values may be `estimated` ("That's fine if values are estimated").
- No legend. Colour is "just a visual representation of light temperature".
- Display: option B. Every lit pixel = display grey × tint, sodium (blackbody 2000 K) → white LED (4000 K) by brightness, with a per-year threshold. A **regional grid** of white share changes the threshold where photos exist ("a single ramp for the whole globe is too crude").
- Iberia was built first and the human looked at it ("this is cool and it looks better"). **Next task (human, 2026-10-03): the global run.**
- Option 3 (per-pixel colour from the archive's GeoTIFFs) is for later. `GetGeotiff.pl` returned HTTP 502 all day on 2026-10-03.
- The VIIRS caveat stays in the docs: DNB under-detects white-LED blue, the tint changes hue only, and a sodium → LED switch can read as dimming.

## Defaults the agent chose for Iberia (the human has not confirmed them; ask before changing them)
- Lenses ≥ 50 mm.
- Lamp-like pixel filter: linear G/R ≤ 1.3 and B/G ≤ 1.2.
- White = G/R ≥ 0.8 AND B/R ≥ 0.5.
- At least 200 such pixels per photo.
- 0.25° grid, Gaussian σ 0.5°, weighted median, coverage = 1 − exp(−Σw/2).
- Threshold = local (±0.5°) (1 − share) quantile of display grey. Brightest pixels turn white first.
- Fallback = Iberia-wide thresholds 248 (2015) / 219 (2025) from `09_display_ramp.py`.

## What exists (all run from `final/` with `.venv/bin/python`)
- `pipeline/colour/config.py`:
  - `PILOT = "iberia"`, `BBOX`, `EPOCHS` (2015 = photos 2012–2015; 2025 = 2021 on), `MISSIONS` (ISS030–046, ISS064–075).
  - `RECORD_TYPES` (human centre point + ML-catalogued), `PARALLEL_REQUESTS = 3`.
  - Forces IPv4: the archive's IPv6 address does not answer from this network.
- `01_query_eol.py`: public CoordinateRangeSearch, one request per mission, night only, inside `BBOX`. Responses are saved to `data/raw/colour/eol/queries/<date>/<pilot>/`; rows go to `data/derived/colour/<pilot>_records.csv` (photo_id, date, lat, lon, focal_mm, record_type, epoch, in_pool).
- `03_fetch_images.py --kind small --pool`: thumbnails (~74 KB, 640 px) of every pool record, run in parallel, read-only, with a SHA-256 manifest. Failures are listed at the end.
- `09_display_ramp.py` → `display_ramp.json` (Iberia-wide thresholds).
- `10_white_share_grid.py` → `<pilot>_thumb_shares.csv` and `<pilot>_white_share_grid.json` (bbox, step, nx, ny, north-first rows; per epoch: white_share, coverage, grey_threshold).
- `app/src/tileLayer.js`:
  - The shader samples one grid texture (R/G = threshold 2015/2025, B/A = coverage). The extent comes from the JSON's bbox.
  - `GRID_URL = '/colour/iberia_white_share_grid.json'` is hard-coded.
  - The thresholds/tints are hard-coded constants copied from `display_ramp.json`.
- `app/vite.config.js`: `/colour/` route with the allow-list `APPROVED_COLOUR = ['iberia_white_share_grid.json']`.
- Iberia data: 1,955 thumbnails (132 MB) in `data/raw/colour/eol/small/`; 346 (2015) / 294 (2025) photos usable.

## Facts that matter for a global run
- **Query time:** about 3 min per mission per box query (server response time, AI_LOG colour step 4). An earlier worldwide night-photo count produced about 0.9 GB of response HTML (scratchpad, not kept).
- **Worldwide night photos** (colour-pilot handoff):

  | | 2012–2015 | 2021–2026 |
  |---|---|---|
  | Human centre point | 5,904 | 338 |
  | ML-catalogued | 173,973 | 85,223 |

  The share of these at ≥ 50 mm is unknown.
- **Thumbnail download speed** at 3 parallel requests: about 1.3–6 files/s (varied); 1,955 files took about 20 min.
- **ISS nadir coverage** ends at about ±52° latitude (inclination 51.6°). Beyond that only oblique frames exist.
- **The ML record point may be the station nadir,** not the image centre.
- **Speed bottleneck:** `10_white_share_grid.py` reads a COG window per cell (fine for 2,065 cells, too slow for a global 0.25° grid of about 1.4M cells).
- **Colour scale shifts between photos.** Some photos render sodium yellow; the B/R rule and the median handle most of it (Seville 2015 0.32 → 0.06).
- **Display limit:** city-core display greys saturate, so local thresholds there are 246–255 and the regional effect is subtle. The human was offered a stronger-contrast variant (threshold from a wider grey distribution), but has not chosen it.

## Questions for the human before starting (agent proposes, human decides)
1. Query scope: one worldwide box per mission, or several regional boxes. File layout for the responses and records (`PILOT = "global"`?).
2. A cap on thumbnails per grid cell and epoch, to bound the download. **Download approval** with count and size once the records are known.
3. `PARALLEL_REQUESTS` (3 now) for the thumbnail download.
4. Grid resolution and texture size for the globe; whether Iberia's grid is replaced by the global one.
5. The fallback threshold outside photo coverage (the Iberia-wide values, or a global value computed the same way).
6. Whether to apply the stronger-contrast variant at the same time.

## Concurrency
- Other sessions edit `app/src/main.js`, `story.js`, `style.css`, `impacts.js`, `app/vite.config.js` and `AI_LOG.md`. On 2026-10-03 a simultaneous edit to `vite.config.js` dropped this task's lines once.
- Re-read a file right before editing it, and make small targeted edits.
- Append to `AI_LOG.md` only with one `cat >> AI_LOG.md <<'EOF' … EOF`.
- Don't edit main.js/story.js/style.css without asking.

## Still open from earlier
- Keep or delete tiles v2, the class raster and the city-class files.
- RULES §3 audits for all colour data.
- Git handling of `data/raw/colour/`.
