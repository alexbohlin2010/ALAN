# Handoff: story UX, part 1 skeleton built (steps, intro fade, cards)

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` entries "Story UX task, step 1" to "step 4". Read `RULES.md` first. `2026-10-03_render-prototype.md` and `2026-10-03_radiance-audit.md` still hold. A colour (CCT) session ran in parallel; it owns `pipeline/colour/` and `data/*/colour/`.

## Decisions the human made
- **Story structure:** three parts: 1) intro/context (global illumination), 2) Light impacts (map of global light studies, case studies, abstract visualizations; whether these sit on the globe, in a pop-up or in a separate view is undecided), 3) Beyond us (insects/animals). Only part 1 has been started.
- **Part 1 content (human's skeleton):** black screen with italic "...and then there was light", then the lights fade in; the statistic; case studies India (increase, policy), France (decrease, policy), Ukraine (decrease, war), each a 3–5 s overview with a simple explanation.
- **A1a:** step buttons + arrow keys; no separate prelude; the app opens at the start of the story. **A2:** one separate content file for everything, as a JS module. **A3:** globe controls stay free. **A4c (tentative):** swipe always available; to revisit after viewing. **A5a:** CSS black-overlay fade (sound may come later). **A6:** existing globe.gl + tile-layer architecture.
- **Statistic definitions:** B1a (total radiance change % + lit-area change %), denominator = 2015 lit area, **L1** lit = > 0 in average_masked, "newly lit" = 0 in 2015 and > 0 in 2025, **sphere** pixel areas, **M1** (both numbers), **pairwise** exclusion of −1.5, a **sensitivity check** (thresholds not chosen), scripts in **`pipeline/story/`**, extreme values not discussed in the story. Keep the LED under-detection caveat, with sources.
- **C0:** no country boundaries. Case-study claims: the human asked the agent to draft simple causal claims with simple citations as placeholders, to be edited by the human.

## What exists now
- `app/content/story.js`: 5 steps with text, sources, camera, timing. The case-study sentences and the caveat note are **AI-drafted placeholders** (marked in the file). Sources are listed in AI_LOG step 4.
- `app/src/story.js`: step engine. `index.html`, `main.js`, `style.css`: small additions. Verified in the browser at :5173.

## Open (human decides)
- Edit the placeholder wording. Whether the statistic sentence stays as written now that M1 defines the second number as change in lit area.
- Swipe per step (`swipe` field, A4). Which year the intro reveals. Layout and styling of the card, nav and intro (all prototype-only).
- Sensitivity-check thresholds. Computing the statistic (script in `pipeline/story/`, label `inferred`, RULES §3 audit).
- Whether to read the Kyba et al. 2023 paper text to confirm the caveat wording.
- Facts the human may want checked: the S-NPP overpass is around 01:30 local time, after France's 1 a.m. switch-off; 2015 is already after the 2014 conflict began in eastern Ukraine; the overlay hides the nav buttons during the intro.

## Next task
Not set by the human. Named candidates: the statistic script in `pipeline/story/`; editing the content.

## Addendum (same session, AI_LOG step 5)
- **Human decisions:** automatic divider sweep per case study, from the country's far right (2015) to its far left (2025); intro shortened by ~1.5 s, with an arrival sequence (black → lights fade in → UI joins); the statistic shown as a prominent fact on the left of the globe.
- Built and verified in the browser. Sweep longitudes are approximate and set by hand in `app/content/story.js`.
- India: the human asked about the "rural lighting initiative". DDUGJY (launched Dec 2014; all census villages electrified by 28 Apr 2018; PIB factsheet 27 May 2022) is documented in AI_LOG step 5. The card still cites Saubhagya; the human decides which to use.
- AI_LOG step 6: India card now uses DDUGJY (human decision). Statistic wording (human): "Radiance from Artificial Light at Night (ALAN) has increased by X% ..."; the rest of the sentence still carries the earlier skeleton wording. **The statistic is still not computed.** Open for that task: sensitivity thresholds; checking what EOG's average_masked mask removes (fires, background, aurora), since the wording says "artificial".
- AI_LOG step 7: the human chose sensitivity thresholds 0.5 and 1 and asked this session to compute the statistic. `pipeline/story/01_radiance_change.py` → `data/derived/story/radiance_change_2015_2025.json` (`inferred`, **unaudited**). Main (lit > 0): radiance +40.99%, lit area +25.28% vs 2015. At > 0.5 / > 1: radiance +44.17% / +41.92%, lit area +76.40% / +74.33%. Internal counts match the MANIFEST. Open: RULES §3 audit in a separate session; whether and how the numbers go into the fact text; which threshold the story uses, given the lit-area spread.
- AI_LOG steps 8–10: literature found (Kyba 2017 Sci. Adv.; Li et al. 2026 Nature; Güneş et al. 2026 Ann. NYAS; Kyba 2023 Science; abstracts only). **Human chose option 2:** our number is the headline, literature cited as consistent. The fact now reads "...has increased by 41% between 2015 and 2025, and the lit area by 25%." The note says provisional, audit pending. The agent reworded "across x% of surface area" (M1 mismatch); the human should check this. **Next, before publication:** a §3 audit of `pipeline/story/01_radiance_change.py` and its output in a fresh session, plus a human spot check; reading the full texts of the cited papers.
- AI_LOG step 11 (human decisions): the statistic step flies to an India/China view with an automatic sweep (China east coast → India west coast); the headline reads "ALAN has increased by 41% between 2015 and 2025, and the lit area by 25%."; "radiance" is explained in the footnote; the legend is a pop-up behind an (i) button (Escape closes it).

## Addendum 2 (AI_LOG step 12)
- **Human decision:** two super-categories, **"Light"** (first) and **"Impacts"** (second, below it), selected from a simple interface on the left side of the screen. This replaces the three parts listed above. "Impacts" shows only the 2025 tiles (no divider), with studies placed around the globe.
- **Next task (human):** the Impacts layer, borrowed from Linda's last prototype (the one incorporating earth-after-dark). Identify its academic-studies dataset (the human believes Claude generated it entirely); find next steps to refine or improve it for narrative power; build the Light/Impacts switcher.
- **Pending, not started:** per-country metrics (India, France, Ukraine). They need boundary polygons, a new raw dataset. Human choices: dataset (Natural Earth / geoBoundaries / GADM), disputed areas (Crimea, eastern Ukraine since 2014, Kashmir), France with or without overseas departments, pixel rule.
- Known locations (not inspected for this task): `~/Desktop/ALAN/Linda/`, `~/Desktop/ALAN/Alexander/`, `~/Desktop/ALAN-linda/` (contains `Alexander/globe_v2/`), `~/alan-streetlight-cct/globe_v2/` ("earth-after-dark" entry in `~/.claude/launch.json`). `DATA_INVENTORY.md` lists the earlier datasets.
- AI_LOG steps 13–14 (human decisions): per-country metrics with Natural Earth 1:10m v5.1.1 (downloaded to `data/raw/boundaries/`, MANIFEST added), mainland France, Crimea excluded, Donetsk/Luhansk included, India default line, pixel-centre rule. Corsica not decided (both variants computed). `pipeline/story/02_country_change.py` → `data/derived/story/country_change_2015_2025.json` (`inferred`, **unaudited**, not in the app). Main (lit > 0): India radiance +92.6% / lit area +26.5%; France (incl. Corsica) −41.1% / −30.3%; Ukraine excl. Crimea −32.1% / −38.6%. Lit-area changes swing with the threshold. Open: §3 audit of 01 and 02; Corsica; whether the country numbers go on the cards; git handling of `data/raw/boundaries/`.
- AI_LOG step 15 (human decisions): France = mainland incl. Corsica. The LED / blue-light caveat is important: it is now on the France card as well as in the statistic footnote (Kyba et al. 2023; paper text still to be read before publication).
- AI_LOG step 16 (human decision): the country numbers are shown large on the cards: India "ALAN increased by 93%", France "ALAN decreased by 41%", Ukraine "ALAN decreased by 32%" (radiance, lit > 0), marked provisional until the §3 audit (prompt in chat, covers `01` and `02`).
