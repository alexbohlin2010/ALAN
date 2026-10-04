# Handoff: colour display ramp (option B)

Written 2026-10-03. Follows `handoffs/2026-10-03_colour-pilot.md`. Read `RULES.md` first. Log: `AI_LOG.md`, colour steps 17–18. Method: `pipeline/colour/METHOD.md`, section "Display ramp (option B)".

## Decisions made by the human
- Of five options (A ramp only, B ramp + per-year white share, C GeoTIFF per-pixel photo colour, D calibrated Europe product, E radiance-change tint), the human chose **B**. **C may be tried later.**
- No legend (from the earlier session).

## Defaults the agent chose (the human has not confirmed them)
- Year share = median of the 4 city white shares. Share counted over lit Iberia pixels. Brightest pixels turn white first. ±8 grey-level blend. Tints 2000 K / 4000 K. Same thresholds worldwide.

## What exists now
- `pipeline/colour/09_display_ramp.py` → `data/derived/colour/display_ramp.json`: shares 0.0349 / 0.1518 (`estimated`), grey thresholds 248 / 219 (`inferred`).
- `app/src/tileLayer.js`: the shader draws grey × mix(2000 K, 4000 K) by the year's threshold. The values are copied into constants at the top of the file, so rerunning the script means updating them by hand. It ignores the v2 class bits; v1 tiles are coloured too.
- Rendered on port 5173 (tiles v1): no console errors.

## Open (human decides)
- Whether the look is acceptable, and whether to confirm or change the defaults above.
- Keep or delete tiles v2, the class raster and `08_display_tints.py`'s class use (the shader no longer uses the classes).
- Whether to try option C.
- RULES §3 audits for `display_ramp.json` and the class data. Git handling of `data/raw/colour/`.
