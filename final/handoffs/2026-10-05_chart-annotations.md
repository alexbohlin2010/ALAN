# Handoff: chart annotations (All effects, Light level, Light type, Broader Impacts)

Written 2026-10-05. Facts and human decisions only. Full record: `AI_LOG.md` "Fireflies step" steps 27–32.
Read `RULES.md` first. Before: `2026-10-05_impacts-transitions.md` (with Updates 1–2).

## State
- Branch `main`. All changes committed at the human's request (AI_LOG Fireflies step 32), including the earlier
  uncommitted pad work in `app/src/introScene.js` and the impacts-transitions handoff update (steps 20–26).
- Preview: another session's Vite server on port 5173 (same folder), viewed in the in-app browser. The Begin screen
  blanks the globe until clicked.

## Human decisions and what was built
1. Reading key on All effects, Light level, Light type (human: A1, picks 1a, 2a; the same on all three chart steps).
   After revisions by the human ("in the black above the header text, and a bit larger"; "remove the 'white line …'
   callout"; "aligned with the top of the visualization"), it is: two rows in the right column, 14 px, first row level
   with the top of the chart: a sample dot + "One dot = one measured effect", an arrow + "bigger change under light".
   Samples, not real records. (impacts.js `drawKey` / `KEY_ROWS`.)
2. Timing (human: (i)): the key fades in over 0.6 s once the dots have settled and stays; on Light level / Light type
   it fades out (0.3 s) while the lanes re-sort and returns after. Agent choice: hidden with Dots: Studies or a filter.
3. Broader Impacts (human: C, picks 1a, 2a, 5b; slice size not explained; "Numbers = records per group" removed by
   the human): key rows "One dot = one measured effect" and a small + big dot "Bigger dot = bigger change", level with
   the top of the circle; grey Cohen ranges under the size buttons ("≥ 0.8", "0.5–0.8", "0.2–0.5"), fading in with
   the key. Ranges placed under each label inside the button (agent choice; no room beside).
4. Broader Impacts layout (human: same structure as the charts): circle left in the chart's box (top-anchored, agent
   choice), big text + key on the right (story.js `side: 'right'`; main.js `story-chart` class also for the circle
   stage), size buttons as a row on top where the chart bar sits.
5. Broader Impacts sentence (human, exact): "The biosphere is responding to a new nighttime experience."
6. "Light type" kept as the label; the human asked for the agent's opinion on type vs temperature (logged as
   [AGENT OPINION], step 29); no change made.

## Checked (5173, 1280×800; no console errors)
Species perceptions → All effects (globe, hold, morph, then key) → Light level → Light type → Broader Impacts and back
to Species perceptions. Keys clear of the big text, Details pop-up, menu (right edge 156 px) and nav (from x 1136).

## Open (not decided)
- Portrait / narrow windows not checked for the keys or the new Broader Impacts layout.
- Broader Impacts: empty space below the circle (top-anchored); no "Details & sources" on this step.
- Comment above `intensity` in story.js is out of date (from earlier handoff).
- From earlier handoffs: Two measured nights glow path unused; All effects hold faces Europe/Africa; Species
  perceptions text over the Human half; divider passing over the menu; beat toggle over the mute button; study 299
  audit (RULES §3); study 224 at the USA centroid; pad not heard by an agent; commit when asked.
- The human's narrative note (AI_LOG step 17, "flattened time …") has not been acted on.

## Story as it stands (19 steps, app/content/story.js)
Light: Intro · Statistic ("From 2015 to 2025, ALAN increased by 41%.") · Ecosystems (question).
Impacts: Studies · Fireflies · Female response · Perception · Two measured nights · Species perceptions · All effects ·
Light level · Light type · Broader Impacts · Conclusion ("We need ALAN, but do we need it all the time, everywhere?").
Explore: Explore all studies · [DRAFT] Signal production · [DRAFT] Mate-finding · [DRAFT] Local firefly ·
[DRAFT] Species perceptions.
