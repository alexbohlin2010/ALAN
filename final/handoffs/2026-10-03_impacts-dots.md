# Handoff: Impacts, part 3 (study dots + card built in the app)

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` "Impacts task", steps 15–16. Read `RULES.md` first. `2026-10-03_impacts-geocode.md` and `2026-10-03_impacts-studies.md` still hold where not superseded here. Other sessions (colour/CCT) may run in parallel. They own `pipeline/colour/` and `data/*/colour/`. Append to AI_LOG only with a single shell `cat >>`.

## Human decisions (this session)
- Card information hierarchy (human): the purpose is to show quickly that light impacts on biota are measured under different conditions. DOI is required; citation metadata is secondary. Layout **C2**: taxon + species; MEASURED (effects + topic group); LIGHT (source, approved plain words with the code in brackets, night/control lux, study type · habitat); then small: title, authors · year · journal, location + dot precision, DOI.
- Dot/ring colour: one accent, **cyan #5fd4e6** (no meaning; category colours come later).
- Data in dev: **extend the vite middleware** (`/impacts/` → `data/derived/impacts/`; `/impacts/maps/` → only the approved `light_types.csv`, `topic_groups.csv`).
- OSM/ODbL attribution: **inside the (i) pop-up** (Impacts mode only).

## What exists now
- `app/src/impacts.js`: R3 canvas overlay, P1 (Linda's sizes), S2 (Linda's hash offsets), click → card, Escape/×/empty click closes. Wired into `setMode` in `main.js`. `#study` in `index.html`; styles at the end of `style.css`; dev routes in `vite.config.js`.
- Checked in the browser at 1024×768 and 375×812 (step 16). No new dependencies. Nothing committed.
- Preview config `alan-final-app-impacts` (port 5175) in `~/.claude/launch.json`.

## Open (human decides)
- Garbled source characters in the Westhavelland Location strings show as-is on the card.
- Rings are faint over bright cities; up to 14 studies overlap at one coordinate (Netherlands).
- Agent choices open to change: sizes/alphas, card position, key wording, "+3 more" cut-off, "No single DOI in the source data" wording.
- Still open from earlier: the 6 Crossref-matched DOIs and the 13 non-matching ones; map wording vs README; 35 unresolved Location strings; RULES §3 audits; git handling; publication hosting of `/impacts/` data (dev-only now, like tiles).

## Next steps (as set earlier by the human)
- Linda's categorised view (category colours); showing the measured effects.

## Addendum (same day, AI_LOG steps 18–19)
- Human decisions: card = **title largest**; location name only (no point/region/country words); Lab/Field, habitat, topic group, light type + lux kept; species, measured effects, taxon class removed. **Clusters: expand on click** (count dot → fan). **Prev/next on the card** (‹ › and ← →, all 207, west → east). **Rings dropped** (the (i) key says some dots mark only a country or region). This supersedes P1 rings and S2 offsets above.
- Categories explained to the human (step 18): source `Category` (5: Behaviour 96, Physiology 91, Community 41, LHT 40, Population 25 of 207 drawn) and approved topic groups (7). 68 drawn studies have 2–4 categories; 86 have 2–5 topic groups. `studies.json` has no per-category effect counts.
- Open (human decides): **which category system colours the dots, and the rule for multi-category studies** (e.g. dominant by effect count, which needs a pipeline addition; a "mixed" colour; split dots). Portrait card can cover the selected dot. Fan order vs prev/next order.

## Addendum 2 (AI_LOG step 20)
- Human decisions: colour = **the source's own Category** (5, documented; topic groups dropped, files `topic_groups*.csv` **deleted** at the human's request). **Linda's colours**: Behaviour #ffb55a, Physiology #8bb8ff, LHT #d99cff, Population #7ce6cf, Community #f2e48b. **Split dots** for multi-category studies; **cluster dots = pie** of their studies' categories. Light plain words kept.
- Facts: the validator flags Linda's palette (LHT vs Physiology hard to tell apart for deutan; Community vs Behaviour close for everyone; the amber Behaviour colour sits on amber city lights). Category names are shown on the card and in the (i) key.
- Open: `app/vite.config.js` `/colour` route from the colour session references undefined `APPROVED_COLOUR`/`COLOUR_ROOT` (error overlay in dev) — owner: colour session/human.
