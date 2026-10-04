# Handoff: Impacts, part 1 (switcher built; studies dataset registered and tabulated)

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` entries "Impacts task, step 1" to "step 6". Read `RULES.md` first. `2026-10-03_story-ux-skeleton.md` (with addenda) still holds where not superseded here. Other sessions (colour/CCT) may run in parallel. They own `pipeline/colour/` and `data/*/colour/`. Append to AI_LOG only with a single shell `cat >>`.

## The dataset (facts)
- The studies layer in Linda's last prototype (commit `db976a972`) is "C1", built from **Czarnecka et al. 2025, Data S1**. This is the supplementary data of the meta-analysis "Colours of the Night: Spectrum-Specific Impacts of Light Pollution on Biota", *Global Change Biology* 31(10): e70569, doi:10.1111/gcb.70569 (PMID 41123002). The data is on Dryad, doi:10.5061/dryad.xwdbrv1q0, v6, **CC0-1.0**. The study records are not AI-generated. Linda's geocoding, anchors and display caps are script-made and are not reused.
- Inclusion criteria (Dryad record): non-human organisms; a dark control vs treatment up to 180 lux; ≥2 replicates with light type and level reported; means, N and variation reported; Web of Science + Scopus to 30 Aug 2023; English, peer-reviewed. 1,758 papers screened, 314 included. It is not every ALAN–biosphere study.
- Now raw at `data/raw/impacts/czarnecka2025/` (+ `MANIFEST.csv`). The SHA-256 equals Dryad's digest.

## Human decisions
- Two super-categories, **Light** and **Impacts**. Switcher **S2**: labels with a step list under Light.
- Impacts = **A2**, free exploration: 2025 tiles only, study dots clickable, a card with plain fields and a DOI link. One small new file `app/src/impacts.js`; the step engine stays Light-only.
- Include **all 314 studies**. **DOI links, not abstracts.** **I1:** cards built from source fields only. **I2:** plain-language topic groups; the agent drafts, the human edits before use.
- Show **approximate (region/country) locations** as well as exact ones. **Re-geocode in our own pipeline** (OSM Nominatim, cached); hand fixes only from the source paper or by the human. The **69 studies without a location** stay in the data but are **not shown** on the globe for now.
- Design language: Linda's dots spread around the globe. Her categorised visualization comes later, after the barebones. Showing the measured effects is a later step.

## What exists now
- App: `#modes` panel (top left): Light + step list, Impacts. `story.js` returns `{go, pause, resume}` and takes `onStep`. Impacts hides the divider, the 2015 label, card, fact and nav, and sets the divider to all-2025. Checked in the browser at 1440×820; portrait not checked.
- `pipeline/impacts/01_studies.py` → `data/derived/impacts/studies.json` / `.csv` (**unaudited**). 314 studies; **304 with a DOI**. 10 empty: 4 with no DOI in the workbook; 6 with several DOIs (011, 029, 040, 100, 157, 296), which look like consecutive numbers under one title and were not resolved.
- Drafts for the human: `pipeline/impacts/maps/light_types_DRAFT.csv`, `activity_DRAFT.csv`, `topic_groups_DRAFT.csv` (7 groups), `README.txt`.

## Open (human decides)
- Edit/approve the three DRAFT maps (topic groups and names; plain words for the light codes; BS_UV and NS meanings to confirm in the article).
- Whether to check DOIs against Crossref (~310 API requests) to settle the 6 multi-DOI studies.
- Whether to download Dryad's README.md (5 KB) for code definitions.
- git handling of `data/raw/impacts/` and `data/derived/impacts/`. Nothing committed.
- RULES §3 audit of `01_studies.py` and its output (fresh session, plus a human spot check).

## Next steps (as set by the human's order)
1. `pipeline/impacts/02_geocode.py`: Nominatim for the distinct Location strings (one request per second, cached), labelled `inferred`, with a precision type (point / region / country) from the geocoder's result type. Unresolved strings stay empty and are reported.
2. `app/src/impacts.js`: dots on the 2025 globe (Linda's dot style), click → I1 card with a DOI link.
3. Later: Linda's categorised view; showing the measured effects.
