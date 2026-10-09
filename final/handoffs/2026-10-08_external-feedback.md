# Handoff: after the external review: feedback to integrate (benefits of light, urgency, message from the start)

Written 2026-10-08. Facts and human decisions only. Full record: `AI_LOG.md` "Experience refinement" steps 38–43.
Read `RULES.md` first. Before: `2026-10-07_experience-refinement-4.md` (its state, decisions and open items still hold).

## State
- Branch `main`. Last agent commit 59e03eb69 (handoff pass 4, AI_LOG 38–39). Also in history: 41105dc16 "Update
  AI_LOG.md" (not the agent's). At the time of writing `main` was 1 ahead of origin; AI_LOG steps 40–43 and this
  handoff are not committed.
- No app changes since 4499b7013 (Conclusion).
- Dev server: preview_start "alan-final-app", port 5173. The desktop app stopped it several times on 2026-10-07 (pane
  closed or idle); the human was given `cd ~/Desktop/ALAN/final/app && npm run dev` to run it from a terminal for the
  presentation. The app has no full-screen control of its own (none found in src/ or index.html); browser full screen /
  Chrome kiosk explained in chat (step 42).
- app/src/introScene.js (audio, another agent's) not edited.

## Explanations given for the presentation (steps 38, 40, 41; facts, no changes)
- Globe brightness: EOG Annual VNL V2 (VIIRS DNB, S-NPP), average_masked, 2015 (v2.1) and 2025 (v2.2); one GeoTIFF per
  year, 86,401 × 33,601 Float32 pixels, 15″ (EPSG:4326), nW/cm²/sr; pixel location from the header's geotransform
  (top-left 180° W, 75° N). Pipeline: lossless COG → −1.5 = no data, other negatives → 0 → hist-eq grey curve (P99.99,
  both years pooled, display only) → 256 px tile pyramid, levels 0–9, native at 9, block means above; R = 2015, G = 2025.
- Globe colour: `estimated` white share from ISS astronaut photo thumbnails on a 0.25° grid, drawn per 1/20° block as
  4000 K white or 2000 K sodium; fallback shares 0.1844 (2015, photo median) and 0.41 (2025, Brazil ABCIP census) per
  global_white_share_grid.json; METHOD.md's fallback table (0.2207 / 0.7277) does not match the file. Unaudited; per-
  mission camera bias (METHOD.md).

## External review feedback (as reported by the human, 2026-10-08; verbatim in AI_LOG step 43)
The human reported a panel of external judges and critics (named by the human: a former global creative director at
Nike, and a real-estate developer). Three points:
1. "Well we need more context on the good aspects of light ... why it matters for safety, economic development etc."
   The human's reading: the panel seemed somewhat defensive and may want a more balanced view of ALAN; the narrative may
   be too dogmatic, or it may have been those reviewers' personal view. Not decided.
2. More examples, to create more urgency for the message.
3. The message needs to be clearer from the beginning ("the hardest part"). The human's statement of the message: not
   simply "light is impacting the biosphere", but light is impacting the biosphere in so many ways, causing so much
   unpredictability, that its systemic risks need to be considered. The human notes the story reaches this only at the
   end (Biosphere Response release beat, "Together, these impacts interact in uncertain ways."; Conclusion "ALAN is
   exposing Earth's critical ecosystems to systemic risk.").

## Facts relevant to the feedback (from earlier steps)
- Current on-screen order (story.js ids): intro (Intro), statistic (Dawn), question (ALAN), female-site (Fireflies),
  female-response (Response), perception (Impact), two-nights (Spectra), species-perceptions (Perception),
  firefly-counts (Firefly Populations), effects (Studies), intensity (Light level), light-type (Light type), broader
  (Biosphere Response), conclusion (Conclusion); Explore after.
- Backing of the "systemic risk" framing (step 24): Czarnecka et al. 2025 supports interaction across species and
  trophic levels, cascading effects and uncertainty in model estimates; it does not state "systemic risk" or its size.
  The Conclusion's first line has no source of its own.
- No source on the benefits of ALAN (safety, economy) is in the repo's story sources as far as earlier sessions read;
  the next session should check, not assume.

## Open (decisions for the human)
- Whether and how to add context on the benefits of light (point 1), and with which sources.
- Which examples to add for urgency (point 2), and where.
- How to state the message early (point 3), in the human's wording.
- Still open from pass 4: cross-agent checks X1–X5; DATA_INVENTORY.md layout; spot checks pending (radiance, story,
  impacts_spectra, impacts_spectra_299).
