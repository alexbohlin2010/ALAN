# Handoff: Experience refinement (pass 1) — Spectra timing, globe flicker, Biosphere Response → Conclusion, copy changes

Written 2026-10-06. Facts and human decisions only. Full record: `AI_LOG.md` "Experience refinement" steps 1–8.
Read `RULES.md` first. Before: `2026-10-06_conclusion.md`.

## State
- Branch `main`. Nothing from this session committed (human has not asked). Files changed: app/content/story.js,
  app/src/main.js, app/src/story.js, app/src/style.css, app/src/tileLayer.js, app/src/twoNights.js, AI_LOG.md, this file.
- Dev server on 5173 belongs to another session (opened by URL). Preview pane ~2 fps; it draws emulated sizes small.
- app/src/introScene.js (audio, another agent's) not edited; main.js calls its humFor({ part, humOff }).

## Human decisions (step in AI_LOG "Experience refinement")
- Spectra: divider sweep 7000 → 3500 ms; Philadelphia line swaps when the divider crosses the middle (2).
- "Cherry Springs, PA": the shared site label (Spectra, Perception, transition glow) and Spectra's first line; the
  150× line unchanged (3). Study line "Bright amber light silenced female fireflies most (Owens & Lewis 2021)." moved
  from Spectra (now 3 beats) to Perception's text, replacing "Philadelphia’s Artificial Light drowns out the firefly
  light." ("a risky non academic claim"); Owens & Lewis 2021 added to Perception's sources (3).
- "All effects" → "Studies"; text "Beyond fireflies, 207 published studies reveal widespread impacts of artificial
  light on biota." (4, 7).
- "Broader Impacts" → "Biosphere Response", opening "So how is the biosphere responding?", same 5 callouts (2, 5).
- Conclusion: "Across the biosphere, ALAN is upsetting the equilibrium of natural systems." first (centred; dots fade
  1 s; earth fades to dark from this line), dusk line comes in below it on its own after 2.5 s with the hum fading
  then; first line anchored; next arrow: 5b line alone; then responsive lighting + Details (5, 6).
- ALAN: divider faster (1000 ms), starts short of the right edge (start 0.72), one smooth glide (6, 7).
- Female response: big text raised (factTop 0.42) clear of the spectrum row tags (6).
- Dawn: "The dawn of human nighttime activity is changing the globe,\nand its residents." (line break) (7).
- Globe flicker: one-level-coarser tiles tried and rejected ("The original was more beautiful"; LEVEL_BIAS = 0) (2, 7);
  then B (4-sample shading only while the camera moves) and D (no tile refinement mid-flight) applied (8).

## Mechanisms added (code)
- twoNights.js moveTo(…, mid) callback. story.js format(): "\n" = line break; sweep `start`; `factTop` story key.
- main.js: `darkFrom`, `humFrom`, `together`, `autoBeat` story keys; applyDark, anchorFact; body class `story-centre`;
  capFlight. tileLayer.js: LEVEL_BIAS, MOVE_AA (+ timings), shade()/uAA, levelAt, capFlight, moved/easeAA.

## Agent choices to confirm (display only)
- ALAN start 0.72, sweep 1000 ms; Female response factTop 0.42; Conclusion dot fade 1000 ms; AA timings 150/120/600 ms.

## Seen, not changed / open
- ALAN's question "How is the biosphere responding?" and Biosphere Response's "So how is the biosphere responding?"
  are near-identical, a few steps apart.
- Coming back from Perception to Spectra, ← skips to the previous step until the cloud → spectra morph ends
  (twoNights.js beat(): mix > 0.01); slow only in the preview.
- On a zoom-in flight the one refinement on arrival is a ~0.5 s pop-in (ALAN: level 5 → 8 during the 800 ms hold).
- Not tried: mipmapped tiles (option C; needs the flags split out — architecture, ask first); preloading destination tiles.
- The hum behaviour is checked by code path only (preview muted).

## Next
- Human to review the pass in a full-size browser (motion flicker, transition feel, hum timing) and say what to commit.

## Addendum (after the commit, AI_LOG step 11)
- The four [DRAFT] Explore steps (Signal production, Mate-finding, Local firefly, Species perceptions draft) moved to
  `retired` in story.js (human). Story = 15 steps. Their code paths are unused, not deleted. Not committed yet.
