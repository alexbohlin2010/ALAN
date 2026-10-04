# Handoff: mice chapter dials; GitHub push not started

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` "Push task" steps 1–6. Before: `2026-10-03_spectral-chapters-build.md` (incl. addendum), `2026-10-03_colour-night-only-grid.md`. Read `RULES.md` first.

## Human decisions (this session)
- Remove the Glow-worms story step (done).
- Impacts colour/filter bar must not stay visible on Light steps (fixed).
- Fireflies chapter: the human finds it clear by the end; no change.
- Mice chapter "not clear to me as a viewer". Human chose: use Linda's body-clock visual idea (activity as moving particles over a day/night cycle, `Alexander/globe_v2/body.html`, data `Linda/processed/body_clocks/`, Hui, Zhang & Ouyang 2025, zebra finches) **with study 278's mice numbers**. Mice stays the lamp-colour chapter; the finch study is not used.
- Next session: first assess the mice chapter's interpretability, then push to GitHub.

## Done
- `app/content/story.js`: step `glow-worms` removed (15 steps now). Mice step: new DRAFT text and beats.
- `app/src/impacts.js` `loop()`: no draw after `hide()` (a queued frame re-showed the bar).
- `app/src/spectral.js`: `clockRing` replaced by `mouseDial`: two dials (outer blue-rich, inner long-wavelength), ZT 0 top, clockwise, 12:12 LD. 900 particles move through the night half (even density = display choice). Beats: `10 lx · 10 lx` → `−51 %` (blue-rich lamp, lit window ZT 14–15, 51 % of particles in it removed; label adds 15 melanopic lux) → `−14 %` (long-wavelength, 1 melanopic lux) → `117 vs 26 min` (15 min pulse window at 16–16.25 on both dials, night band starts later). Headline numbers coloured by lamp. Credit to Linda's scene in the file header.
- Correction: the old ring showed the −117 / −26 min shifts as earlier; the paper reports phase **delays** (later). Dials now move later.
- Protocol facts (278 Methods, raw XML): 12:12 LD, 300 lx / 0 lx, ZT 0 lights on; masking = 1 h light at ZT 14 vs ZT 14–15 the day before; phase shift = constant darkness, 15 min of 10 lx at CT 16, onset = CT 12.
- Browser check at localhost:5173 (another chat's server): 4 beats seen, no new console errors.

## Known weak points (seen, not fixed)
- The −51 % gap covers 1 of 12 night hours: small and hard to see.
- Day half of each dial is faint.
- The clock-test pulse is drawn on the same ZT dial although that test ran in constant darkness (CT); the DRAFT text does not say so.
- Dial radii, particle count/speed, colours, positions and camera are agent choices.
- Whether to ask Linda about reuse of her visual approaches (shader, body-clock idea) is still open.

## Push task: state
- Not started beyond step 1. At 23:28 the colour session looked active: `fallback_facts.py cov cov.json` had just started; `pipeline/colour/METHOD.md`, `10_white_share_grid.py`, `14_frame_flags.py`, `data/derived/colour/global_white_share_grid.*` modified within minutes. Vite servers on ports 5173 and 5175.
- Not yet done: size / file count per top-level folder and files > 50 MB; licence check against `data/raw/impacts/MANIFEST.csv` and the colour MANIFEST; what Linda needs from `data/derived/` and its size; the plan.
- Known from AI_LOG Impacts step 81: repo root `~/Desktop/ALAN`, branch main, origin github.com/alexbohlin2010/ALAN; all of `final/` untracked; `data/raw/colour/` ~27,800 files incl. EOL query HTML 52–230 MB (> GitHub 100 MB limit); 278 PDFs/XML are CC BY-NC-ND, Lucas 2014 files PMC fair use, neither ignored; `data/derived/` ignored; xlrd 2.0.1 in `final/.venv` but not in `pipeline/requirements.txt`.
- Nothing committed, pushed or deleted.
