# Handoff: Experience refinement (pass 3): effects charts, Biosphere Response release beat, ALAN carry, Conclusion line

Written 2026-10-06. Facts and human decisions only. Full record: `AI_LOG.md` "Experience refinement" steps 22–26.
Read `RULES.md` first. Before: `2026-10-06_experience-refinement-2.md`.

## State
- Branch `main`. Committed at the human's request (step 26); not pushed.
- Dev server on 5173 belongs to another session (PID 24259; opened by URL). The repo's launch config has no "app" entry
  (names in ~/Desktop/ALAN/.claude/launch.json: "alan-final-app", …).
- app/src/introScene.js (audio, another agent's) not edited.

## Human decisions (step in AI_LOG "Experience refinement")
- Effects charts (Studies, Light level, Light type): under the chart only the axis label "Impacts of artificial light
  relative to darkness." (human wording); the two grey |g| lines moved verbatim to the end of each step's Details note
  (D1, 23). Tick numbers and small / medium / large kept (not answered).
- Biosphere Response: grey ranges under Large / Medium / Small removed (23). Callouts: aphids (200-6), birds (106-108),
  Czarnecka et al. 2025 quote; wallaby and salmon removed (23).
- Release beat (M1, T1, H1; 23): one arrow beat after the Czarnecka quote: labels, key and size buttons fade, dots
  bounce freely inside the circle (display device, not data; stated in impacts.js comments); dots keep moving while
  the canvas fades into the Conclusion; back = dots glide home.
- Release line (c, P1; 24–25): "Together, these impacts interact in uncertain ways." fades in below the quote 1.5 s
  into the release beat (human: 1 s earlier than 2.5 s). Human's first wording ("… reveals a major systemic risk")
  assessed in step 24: interaction and uncertainty supported by Czarnecka et al. 2025; "systemic risk" and "major" not.
- Conclusion: "ALAN is necessary for the modern apparatus of human society. But not all the time, everywhere." (24).
- Response: "ALAN interrupts female firefly responses to mating calls, in a lab environment." (23).
- ALAN → Fireflies (25): the question fades in below the Details button (nothing above moves); on leaving, the 41 %
  line and Details fade out; only the question flies, not pushed down by the growing menu; it fades at 2.0 s of the
  flight (US coast coming in, measured), then the Fireflies text fades in.
- Light type callout: wallaby (154-2, Dimovski & Robert 2018) replaces the seabird (308-1, Atchoi et al. 2023): more
  ringed dots (26).

## Mechanisms added (code)
- story.js: `revealLine()` export (adds a line below without the lines above moving; added height measured);
  `below` lines rendered after the Details button; `carryFade`; `holdPlace` (no menu push during a carry).
- impacts.js: `released` / `free` / stepFree (elastic discs, grid hash), relA. story key `impacts.release`,
  `impacts.releaseLine`. main.js: beatCount + 1 for release; RELEASE_LINE 1500 ms.

## Agent choices to confirm (display only)
- REL_SPEED 0.12 circle radii/s (offline at 60 fps: 23 % of dots outside their own sector after 10 s); directions random
  per release (not seeded); reduced motion: dots still, labels fade; REL_FADE 700, REL_HOME 5/s; `.below` gap 18 px;
  statistic fade 500 ms at flight start.

## Seen, not changed / open
- Lizard replacement on Studies (callout 169-1): candidate Jiang et al. 2023 = Data S1 study 310 (66 records; Data S1
  author spelling "Jiyang"); no Crossref abstract, quote would come from the human's PDF (~/Downloads, not copied).
  Candidate quotes (a) "the feeding and mating activities were significantly reduced", (b) "light stress above 10 lx
  significantly interferes with the behavioral activities", (c) background sentence. No decision yet; whether to copy
  the PDF to data/raw/impacts/ not decided.
- The release line has no Details & sources on Biosphere Response (adding them adds a Details button); not asked.
- The in-app pane often stalled frames (~1.4 fps); the 2.0 s question fade and the motion's real speed were not seen
  there.
- From pass 2, still open: dark share 98.7 % not on screen after the split; faint Cherry Springs reply; nav arrows do not
  step Response's beats; clicking → mid-flight opens the circle from the dot's current position; Spectra firefly line
  rests on a one-off check (not scripted).

## Addendum (step 27)
- Release line now at the quote's font size (`#fact .big.release`, clamp(20px, 2.1vw, 32px)); human: "make sure they're
  the same". Committed.
- Next session's tasks (human, step 27): simplify wording in Spectra ('two-nights') and Firefly Populations
  ('firefly-counts'); audit data and a general data-integrity check; update DATA_INVENTORY.md (last committed 2026-10-04).
