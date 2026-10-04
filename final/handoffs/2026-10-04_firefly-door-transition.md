# Handoff: door transition from the effects chart into the fireflies chapter

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Firefly transition task" steps 1–2. Before: `2026-10-04_mice-option2-and-push.md`. Read `RULES.md` first.

## Human decisions
- Option B (the 3D chapter grows out of the chart dot) with the click trigger (C); the story arrow also triggers it.
- Door = record 299-3 only (female response, dim blue; workbook 36.03 % ≈ paper 36.1 %).

## Facts checked (step 1–2, raw PDF)
- 299-1..4 as in `effects.json`; "only for reduced intensity" = the dim treatments (2018 trials). Workbook values look read from Fig. 2b (inference).
- Lux values (31 / 70 lx) are not in the paper or its SI; Czarnecka 2025 sec. 2.1 says non-photometric units were converted; the conversion behind these values was not found.
- Amber: bright amber had the greatest impact (abstract 6); females never answered (Results p. 203); males flashed least under amber; Discussion p. 204 "amber light of any intensity is most disruptive". No amber record for 299 in Data S1.

## Built (not committed)
- `app/src/impacts.js`: `door` / `doorLabel` stage keys (pulsing ring + label, clickable), `onDoor`, `setStage(s, { snap })`, `doorAt(id)`.
- `app/src/spectral.js`: `set(st, { from, to, onDone })`: circle clip + scale about the dot (open 1.3 s, close 0.9 s).
- `app/src/main.js`: door logic in `applyStage` (only between `light-type` and `fireflies`); `onDoor` → story step.
- `app/content/story.js`: `door` on `light-type` (impacts) and `fireflies` (spectral); door label is agent wording, DRAFT.
- Browser-checked at localhost:5173: forwards (click and arrow), backwards, other steps unchanged, no console errors.

## Open (human decides)
- Which beat the fireflies loop starts with (now: dark 98.7 %; alternative: dim blue 36.1 %, matching the door).
- Door label text (DRAFT); at 800×600 it runs under the story card.
- With Dots: Studies the ring sits on the 299 study dot (median of 299-1 and 299-3) but the label names the 299-3 record.
- Timing / look of the expansion (1.3 s open, 0.9 s close, start scale 0.3).

## Update (step 3)
- Human: door stays 299-3 ("Don't want to overthink it").
- Human: fireflies chapter no longer auto-advances; top-right toggle of the six states (dark, cool white, warm white, blue, red, amber); keyboard ← → step the states, then leave the step at either end. Story key `spectral.manual: true`. Mice still loops.
- Agent choice (open to change): arriving from Mice starts on the last state (amber); the bottom-right ‹ › buttons still move whole story steps.
- Still open: which state the chapter opens on (now dark); door label wording (DRAFT).

## Update (step 4): story structure
- Human: Species groups step retired (moved to `retired` in story.js, text kept).
- Human: One effect bars no longer timed; they hold until →, then collapse into the dot.
- Human: new steps after Mice: "Broader Impacts" (fact screen, human's question; charts/data/sources to come) and "Conclusion" (dark screen; DRAFT call to action in the human's suggested wording).
- Human: "Explore all studies" moved to a third top-level heading "Explore" (part 3), after the Conclusion.
- Open: content of Broader Impacts; final Conclusion text; at narrow widths the big fact text overlaps the left step list.
