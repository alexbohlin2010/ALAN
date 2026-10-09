# Handoff: globe flicker measured (left open), species colours by default, Studies text

Written 2026-10-09. Facts and human decisions only. Full record: `AI_LOG.md` "Experience refinement" steps 60–64.
Read `RULES.md` first. Before: `2026-10-09_closing-beat-built.md`.

## State
- Branch `main`. Steps 60–63 committed together after 78f19ae0d (human request, step 64). Not pushed.
- Step 60 (release line "unpredictable consequences") was made by another session; committed here with the rest.
- Dev server: "alan-final-app" (~/.claude/launch.json), port 5173. The app stops it when idle; restart with that config.
- app/src/introScene.js (audio, another agent's) not edited.

## Human decisions
- Globe flicker on ALAN → Fireflies: measured (step 61), no fix applied. Human: "I'll ignore those globe effects it's
  okay for now."
- Dot colours on the impacts chart and the Biosphere Response circle: **Species group** by default (was Effect
  category since Impacts step 63). Human: "Viewers understand more when they see the species colors." The toggle
  still switches to Effect category; the choice is kept across steps.
- Studies text: "These 207 Studies reveal widespread impacts of ALAN on biota." (human, verbatim, capital "S").
- Biosphere Response release line: "Together, these impacts interact in uncertain ways, with unpredictable
  consequences." (human, step 60).

## Code changes
- app/src/impacts.js: `colourBy` default 'species' (comments updated).
- app/content/story.js: `effects` text (step 63); `releaseLine` (step 60). Old wording kept in comments.

## Globe flicker measurements (step 61; facts, for whoever picks it up)
- ALAN → Fireflies: uAA (4-sample shading) is on for the whole flight. capFlight holds nothing here: start and end are
  both level 8 (alt 0.45 / 0.35). ~500 level-8 tiles stream in mid-flight on a cold cache (level-5 fallback until each
  arrives); none when cached.
- The divider jumps from 0.42 of the width to 0 on the flight's first frame (left part 2015 → 2025 at once; 10.1 % of lit
  pixels change in that frame).
- Benefits → ALAN: cap 7 held, ~270 level-7 tiles stream mid-flight (cold); one refinement 7 → 8 on arrival.
- Shimmer at the ALAN view (0.3 px shift, changed lit pixels): 1 sample 35 %, 4 samples (now) 12.7 %, 9 samples over
  1.5 px 4.5 %, 16 over 2 px 0.7 %. Render cost in the preview pane: +0.7 ms (9) / +2.3 ms (16) per frame.
- Options given in chat (none chosen): A wider averaging while moving (shader only, sharp at rest); B ease the divider
  instead of the jump; C preload the path's tiles during the ALAN step (more memory, moderate code).

## Noted
- Studies: the species colour list wraps to three rows above the chart at 1280×800; clear of the chart.
- uAA dips to −0.04 on its first ease tick (rAF timestamp earlier than performance.now()); no visible effect.

## Open (decisions for the human)
- Globe flicker (above), if revisited.
- Still open from earlier handoffs: photo sizes / positions; Details note for Biosphere Response; Benefits Details
  (India research); ALAN Details wording; cross-agent checks X1–X5; DATA_INVENTORY.md layout; human spot checks.
