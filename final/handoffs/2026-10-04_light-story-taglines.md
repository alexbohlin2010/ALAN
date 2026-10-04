# Handoff: Light story — tagline cards, Tanzania, sunrise intro default

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Light story refinement task" steps 1–5. Read `RULES.md` first. Earlier: `2026-10-04_intro-sunrise-scene.md`.

## Human decisions
- Statistic line: "Artificial Light at Night (ALAN) increased by 41% between 2015 and 2025."
- Country cards drop the "ALAN increased by x%" figure lines. Each card shows a narrative tagline; the small text and the sources sit behind a "Details & sources" button (click to expand). No % figure on the cards.
- Tanzania replaces Côte d'Ivoire (Côte d'Ivoire moved to `retired` in `app/content/story.js`). **Tanzania is not computed** in `02_country_change.py` (human: "Don't compute tanzania").
- No "encroachment" wording.
- Taglines (agent drafts chosen by the human):
  - India (I-3): "India’s rural electrification policy brought light to places that were dark at night."
  - Tanzania (T-3): "As Tanzania’s villages joined the grid, light reached new places, alongside the ecosystems around them."
  - The policy / village facts are sourced; "brought light to places that were dark" and "alongside the ecosystems around them" are the humans' framing (comments in `story.js`).
- The sunrise intro is now the default. `?intro=css` gives the old CSS intro (code kept).

## What exists now (nothing committed)
- `app/content/story.js`: `tagline` field; India + Tanzania steps; Côte d'Ivoire in `retired`; statistic wording.
- `app/src/story.js`: tagline card layout + inline "Details & sources"; `toggleMore(container)`.
- `app/src/style.css`: `#card .tagline / .more / .more-body`.
- `app/src/introScene.js`: `INTRO_MODE` defaults to `'sunrise'`.
- Checked in the browser at :5173 (no console errors).

## Tanzania sources (details text, `documented`)
- 4,395 of 12,268 mainland villages (36%), June 2016: TanzaniaInvest, 9 Aug 2016 (news report).
- 11,313 of 12,318 villages, Nov 2023: Daily News, 24 Nov 2023 (REA's Eng. Jones Olotu).
- Protected land 39.9% (2025): World Bank WDI ER.LND.PTLD.ZS (UNEP-WCMC WDPA).
- Not verified (pages did not load): 12,301 of 12,318 villages (99.9%) Dec 2024 (The Guardian/IPP); Zhu, Li & Ru 2022 (doi:10.3390/rs14174240) abstract.
- Not found: a source attributing the light change to mining; a source that light spread into or near protected areas.
- REA counts are mainland only; a Natural Earth Tanzania polygon would include Zanzibar.

## Open (human decides)
- Tanzania details sentence is an agent DRAFT; the human may edit it.
- The statistic footnote still begins "ALAN: artificial light at night." (now repeats the headline).
- Tanzania camera/sweep (lat −6.3, lng 34.9, alt 0.35; sweep 40.4 → 29.3) are approximate; in an 800×600 pane the card covers the south-east coast and parts of Kenya/Uganda are in view.
- Whether to delete the CSS intro path; open items from the intro handoff (CC BY credit line, Safari .ogg, dev handles) still stand.
- Audit: Côte d'Ivoire's 02 value was never audited (now retired); India's 93% no longer on screen; the §3.2 human spot check (seed 2136234698) is still pending for the 41% statistic.
- Git: nothing committed.
