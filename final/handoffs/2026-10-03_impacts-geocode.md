# Handoff: Impacts, part 2 (geocoded, flagged points reviewed, Crossref check run; drawing chosen, not built)

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` "Impacts task", steps 8–14. Read `RULES.md` first. `2026-10-03_impacts-studies.md` still holds where not superseded here. Other sessions (colour/CCT) may run in parallel. They own `pipeline/colour/` and `data/*/colour/`. Append to AI_LOG only with a single shell `cat >>`.

## Human decisions (this session)
- The three maps are **approved as written**: `pipeline/impacts/maps/light_types.csv`, `activity.csv`, `topic_groups.csv`. The `*_DRAFT.csv` files are kept as the record.
- The Crossref DOI check ran (report only). The Dryad README is now in raw.
- Drawing the studies in Impacts: **R3** = a 2D canvas overlay projected from the globe, as in Linda's `~/Desktop/ALAN/Alexander/globe_v2/layers/c1-effects.js`. **P1** = Linda's halos: solid dot = point; dashed ring = region; wider dotted ring = country. **S2** = one dot per study, with a small deterministic display offset when studies share a coordinate (as Linda did). **F1** = flagged geocodes are drawn only after the human reviews them.
- Flagged geocodes: all reviewed by the human (`pipeline/impacts/maps/geocode_review.csv`). "Phillipines" (study 262) = the paper's reef coordinates, 16.293883 N, 120.01455 E (Baquiran et al. 2020, PMC7601249, Methods 2.1; AI_LOG step 14).

## What exists now
- `pipeline/impacts/02_geocode.py`: Nominatim, cached in `data/derived/impacts/nominatim_cache.json`; reruns with `--offline`. Rules (query, top result, precision, flags, review) are in its docstring. Outputs: `geocodes.json`/`.csv` (one row per Location string), `study_locations.json` (only `draw` points; **for the app**). **207 studies drawn, 209 points: 111 country, 50 region, 48 point.** Not drawn: 69 with no Location, 38 unresolved. Attribution needed in the app: "© OpenStreetMap contributors, ODbL".
- `pipeline/impacts/03_crossref_check.py` → `crossref_check.json`/`.csv`. Each of the 6 multi-DOI studies has exactly one candidate whose title matches (011 → …12927, 029 → …11.020, 040 → rsbl.2019.0272, 100 → rstb.2014.0130, 157 → …01715-9, 296 → rbe.2016.11.004). **Not written back.** Single-DOI studies that don't match: 102, 143, 188, 302 (DOI points to another paper); partial 124, 128, 180, 269, 270, 299; not in Crossref 085 (figshare), 101 (comma in the DOI), 192 (bioRxiv "v1").
- `data/raw/impacts/czarnecka2025/README.md`: the real Dryad README, SHA-256 matches Dryad, MANIFEST row added. It defines BS/NS, CCT cut 3000 K, blue 15%, BS_UV = cool white + UV, NS yellow-red = "yellow-orange", and nocturnal includes crepuscular. The approved map wording differs slightly on BS_UV, NS yellow-red and noct.
- Nothing has been drawn in the app yet. globe.gl 2.46.2 is installed.
- All outputs are **unaudited** (RULES §3). `data/derived/` is git-ignored, and git handling is undecided.

## Open (human decides)
- Whether to apply the 6 Crossref-matched DOIs, and what to do with the 13 non-matching single DOIs.
- Whether to update the map wording to the README definitions.
- The 35 Location strings still unresolved (many are source misspellings). They can be fixed via `geocode_review.csv`, which needs a new decision type (e.g. a corrected query) if the human wants that.
- RULES §3 audit of 01/02/03 and their outputs. Git handling of `data/raw/impacts/` and `data/derived/impacts/`.
- Card fields and dot colour (category colours come later, per the earlier handoff).

## Next step (set by the human's choices)
Build `app/src/impacts.js`: R3 canvas overlay, P1, S2, reading `data/derived/impacts/study_locations.json` (+ `studies.json` for the I1 card with DOI link), shown only in Impacts mode. No new dependencies.
