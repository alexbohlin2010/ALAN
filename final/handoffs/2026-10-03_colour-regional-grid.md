# Handoff: colour, regional white-share grid (Iberia)

Written 2026-10-03. Follows `handoffs/2026-10-03_colour-ramp.md`. Read `RULES.md` first. Log: `AI_LOG.md`, colour steps 17–24. Method: `pipeline/colour/METHOD.md` (sections "Display ramp (option B)" and "Regional white-share grid").

## Decisions made by the human
- Option B (display ramp: sodium 2000 K → white 4000 K by brightness, per year), then "a single ramp for the whole globe is too crude": regional variation wanted.
- Option 3 (GeoTIFF per-pixel) first. It was blocked: `GetGeotiff.pl` still returned HTTP 502 on 2026-10-03.
- Then the fast route: archive thumbnails for all Iberia pool photos (download approved), values `estimated` accepted, and the new script/folder/grid/texture approved.
- The human asked how long a global version would take (answered in chat; not decided).

## Defaults the agent chose (the human has not confirmed them)
- Lenses ≥ 50 mm. Lamp-like pixel filter (G/R ≤ 1.3, B/G ≤ 1.2). White = G/R ≥ 0.8 AND B/R ≥ 0.5.
- 0.25° grid, σ 0.5°, weighted median, coverage scale 2, local ±0.5° quantile for the threshold.
- Brightest pixels turn white first. The same Iberia-wide ramp is used everywhere outside the grid.

## What exists now
- `pipeline/colour/03_fetch_images.py` (`--kind small`, `--pool`, parallel), `09_display_ramp.py`, `10_white_share_grid.py`.
- `data/raw/colour/eol/small/`: 1,955 thumbnails, read-only, with a manifest.
- `data/derived/colour/display_ramp.json`, `iberia_thumb_shares.csv`, `iberia_white_share_grid.json`.
- `app/src/tileLayer.js`: ramp shader + grid texture. `app/vite.config.js`: `/colour/` route (allow-list).
- Rendered on port 5173 (tiles v1). The regional differences are subtle because city-core greys saturate.

## Facts learned
- Thumbnails match full-size JPEG white shares closely.
- Wide-angle frames are contaminated by airglow, the station structure and twilight glow, and are located at the station nadir.
- Some photos render sodium yellow (G/R ≥ 0.8, B/R about 0.41).
- 2025 coverage is thin in the north of Iberia.
- **Concurrency:** another session edited `app/vite.config.js` (`APPROVED_MAPS`) at the same time; this session's lines were lost once and re-added. `main.js` and `impacts.js` are being changed by another session (impacts pyramids visible).

## Open (human decides)
- Whether the look is acceptable; whether to make the regional differences stronger (e.g. thresholds from the Iberia-wide grey distribution instead of the local one).
- Going global, and how (see the chat estimate).
- Option 3 when `GetGeotiff.pl` works again.
- Keep or delete tiles v2, the class raster and the city-class files.
- RULES §3 audits for all the colour data. Git handling of `data/raw/colour/`.
