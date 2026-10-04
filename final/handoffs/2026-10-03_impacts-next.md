# Handoff: Impacts, part 4 (the dots as built; next = Linda's categorised view)

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` "Impacts task", steps 15–22 (earlier: `2026-10-03_impacts-dots.md`, `…_impacts-geocode.md`, `…_impacts-studies.md`). Read `RULES.md` first. Other sessions (colour/CCT) run in parallel and also edit `app/vite.config.js`, `app/src/tileLayer.js`, `style.css` and `main.js`. Re-read a file right before editing it, and append to AI_LOG only with a single shell `cat >>`.

## What exists now (Impacts mode)
- `app/src/impacts.js`: a 2D canvas over the globe (R3). Each of the **207 located studies** is a solid dot in the colour of its `dominant_category`. Studies within 14 px on screen form a **Linda-style halo** (faint dotted ring, dots offset inside). A click spreads them out (lines back to the spot, rest dimmed). A click on a dot opens the **card**: title (largest), location · Lab/Field · habitat, categories with swatches (dominant first), light type (approved plain words) + source + night/control lux, authors · year · journal, DOI. **‹ ›** and **← →** step through all 207 studies west → east; the globe turns to each one. (i) key: colours, rules, source, "© OpenStreetMap contributors, ODbL".
- Colours (human): Behaviour #2fb84a, Physiology #8bb8ff, LHT #d99cff, Population #7ce6cf, Community #3d7bff. Behaviour and Community are option 2 (step 21); the other three are Linda's. Validator caveat: Physiology vs LHT are hard to tell apart for red-green colour-blind viewers (ΔE 1.6).
- Data: `data/derived/impacts/studies.json` (01_studies.py) now has `category_effect_counts` and `dominant_category` (Linda's rule; tie → first in the workbook; 20 ties). `study_locations.json` (02_geocode.py). The dev server serves `/impacts/` and `/impacts/maps/light_types.csv` only (`app/vite.config.js`).
- Categories = the source's own `Category` column (Behaviour, Physiology, LHT = "life history traits" per the Dryad README, Population, Community). Topic groups were dropped and their files deleted (human, step 20).
- Preview: `alan-final-app-impacts` (port 5175) in `~/.claude/launch.json`.

## Human decisions in force
R3 canvas overlay; expand-on-click clusters (halo look); prev/next on the card; no precision rings (the (i) key says some dots are country/region-level); title-first card without species/measured effects; source categories only; dominant-category colouring with the tie rule above; option 2 colours.

## Facts about Linda's categorised view (`~/Desktop/ALAN/Alexander/globe_v2/layers/c1-effects.js`, data `globe_v2/data/c1_effects.json`)
- Two modes with an animated transition: an **effect chart**, with one lane per category (her 5 categories, "Life history" = LHT), each **effect record** a dot at x = |Hedges g| on a log scale (cap 10+), jittered within its lane; and the **map**, where the effects fly to their study's anchor on the globe. A category filter dims the other categories. Selecting an anchor fans out that study's individual effects around it.
- Her payload is effect-level (4,905 workbook rows) with Hedges g; ours is study-level. Earlier human decision (impacts-studies handoff): "showing the measured effects is a later step".

## Open (human decides)
- How far to follow Linda's categorised view (effect-level dots and Hedges g, lanes, the transition, the filter), and what new data that needs. Effect sizes are in the raw workbook; no effect-level derived file exists yet.
- From before: the 6 Crossref-matched DOIs and 13 non-matching DOIs; 35 unresolved locations; RULES §3 audits of 01/02/03 (01 changed again in step 22); git handling; garbled Westhavelland strings; portrait card covering the selected dot.
