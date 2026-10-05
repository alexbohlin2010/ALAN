# Handoff: Impacts transitions (Local firefly to Explore, Perception, Species perceptions text, into All effects)

Written 2026-10-05. Facts and human decisions only. Full record: `AI_LOG.md` "Fireflies step" steps 8–15 (note: steps 8
and 9 each appear twice; another session logged its own edits under the same numbers).
Read `RULES.md` first. Before: `2026-10-05_fireflies-step.md`, `2026-10-05_impacts-reorder.md`.

## State
- Branch `main`. **Nothing committed.** Other sessions have uncommitted edits in the same files (story.js, main.js, …).
- Preview: another session's Vite server on port 5173 (same folder), viewed in the in-app browser. The Begin screen
  (introScene.js) blanks the globe tiles until clicked.

## Human decisions and what was built
1. Local firefly moved to Explore, after [DRAFT] Mate-finding, label "[DRAFT] Local firefly", part 3 (human: "A with
   [DRAFT]"). Mate-finding ↔ Local firefly uses the existing glow transition (spitschan2016_city); Local firefly ↔
   [DRAFT] Species perceptions: plain cuts.
2. A flyover Female response → Two measured nights was built (step 9) and then removed (human: "the flyover on map
   isn't good"); main.js back to its earlier state for that path.
3. New step `perception` ("Perception") between Female response and Two measured nights: kind 'fact', `dark: true`
   like Conclusion (camera lat 20, lng 10, alt 2.2), text "Humans perceive ALAN differently to other parts of the
   biota." (human). Transitions: plain cuts.
4. Species perceptions: big narrative text on the right (kind 'fact', side 'right'), no card, text "Fireflies perceive
   ALAN with their own eyes, not ours." (human); sources kept behind "Details & sources".
5. Species perceptions → All effects (human: "Sequence in All effects", "Card at once", back "Plain cut"): All effects
   has `fly: 2500` and `globeHold: 500` (hold changed from 1 s to 0.5 s by the human). main.js applyStage: a chart step
   with `globeHold`, entered from a step without `impacts`, shows the Impacts globe stage (study dots) during the
   flight and hold, then sets its chart stage; the existing records morph (globe → lanes, 1800 ms) plays.
6. Story now 19 steps: Impacts = Studies, Fireflies, Female response, Perception, Two measured nights, Species
   perceptions, All effects, Light level, Light type, Broader Impacts, Conclusion; Explore = Explore all studies,
   [DRAFT] Signal production, [DRAFT] Mate-finding, [DRAFT] Local firefly, [DRAFT] Species perceptions.

## Checked (1280×800, no console errors)
Female response → Perception → Two measured nights and back; Two measured nights ↔ Species perceptions; Species
perceptions → All effects (globe, hold, morph) and back; Light level → All effects (unchanged); Local firefly in
Explore from Mate-finding and to/from [DRAFT] Species perceptions; text/cards clear of menu and nav.

## Open (not decided)
- Two measured nights' `nightsSites` glow path no longer runs from its neighbours (code kept).
- During the All effects hold the camera faces Europe/Africa; the Americas' studies sit at the globe's edge.
- Species perceptions text sits over the Human half of the cloud.
- While Two measured nights' divider sweeps to the left edge it passes over the menu; on [DRAFT] Species perceptions
  the looping divider crosses the Explore menu.
- From earlier handoffs: beat toggle over the mute button; Fireflies note wording; study 299 audit (RULES §3);
  study 224 at the USA centroid; commit when asked.

## Update (same day, AI_LOG step 17)
- All effects, Light level, Light type: big text on the right column beside the chart (body class `story-chart`,
  style.css), old card text behind "Details & sources". Sentences: All effects "The impacts of artificial light on biota
  are generally substantial." and Light level "Impacts occur at every light level, even in low light." (agent drafts
  picked by the human); Light type "Impacts occur regardless of light type." (human). Broader Impacts: "All classes of
  biota are simultaneously responding to a new global environment." (human).
- Human's narrative note (verbatim in AI_LOG step 17, "flattened time …"): not acted on.
- Open: portrait/narrow layout of the chart steps not checked; stale comment above `intensity`.
