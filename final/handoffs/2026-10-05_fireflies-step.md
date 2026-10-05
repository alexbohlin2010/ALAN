# Handoff: Fireflies step (done)

Written 2026-10-05. Facts and human decisions only. Full record: `AI_LOG.md` "Fireflies step" steps 1–2.
Read `RULES.md` first. Before: `2026-10-05_species-perceptions.md`, `2026-10-05_impacts-reorder.md`.

## State
- Branch `main`. **Nothing committed.** Other sessions have uncommitted edits in the same files.
- Preview: another session's Vite server on port 5173.

## Human decisions and what was built
1. Fireflies (`female-site`) text: the human's sentence "Fireflies generate natural light to communicate in an
   increasingly lit environment", shown as big text like the other `kind: 'fact'` steps (Statistic, Ecosystems,
   Studies, Broader Impacts, Conclusion). [DRAFT] card text and title removed; note + source kept behind
   "Details & sources" (human: "Keep Details").
2. Yellow collection-site point removed from the step. Study 299 moved by the pipeline (human: "Data change (A)"):
   new pipeline/impacts/maps/study_location_review.csv (keyed by study_id) read by 02_geocode.py; study 299's point =
   "Arnold Arboretum, Boston, MA", 42.30469, −71.12099, precision point, label `documented` (Owens & Lewis 2021
   Methods). Shown at Boston on every globe view. Only study 299 changed in study_locations.json.
3. Fireflies ↔ Female response: plain cut both ways (human: "Plain cut").

## Checked (1280×800, no console errors)
Studies → Fireflies → Female response → Fireflies; dot at Boston; text style as the narrative steps; no overlap with
menu or nav.

## Open (not decided)
- Note text still says "The point marks the Boston collection site" (agent's earlier wording).
- Legibility of menu and big text over bright East Coast lights at altitude 0.35.
- Unused now: SITE_POINTS.owenslewis2021_boston and female-response's spectral.site (and its comment).
- Audit (RULES §3) of the study_locations.json change not run.
- Study 224 (Owens & Lewis 2021, J. Insect Physiol.) also sits at the "USA" centroid.

## Update (same day, AI_LOG steps 3–4)
- Human decisions: Fireflies big text on the right (`side: 'right'` story key, landscape only); a label under study
  299's dot (`impacts.studyLabel`): title + "Owens & Lewis 2021" (title/year from studies.json, author short form per
  the human); Female response card text replaced by the human's sentence "Light at night interrupts female responses
  to mating calls" (title and sources unchanged).
- Checked at 1280×800, no overlaps, no console errors.
- Open: label legibility over bright land lights; label/text gap on narrower landscape windows not tested.

## Update 2 (same day, AI_LOG steps 5–6)
- Human decisions: study label has a card background (as #card) and the title in quotes; Female response is big text
  (kind 'fact') on the right, no card; on the amber beat a big caption fades in bottom centre: "With bright amber
  lights reducing female responses to 0%" (beat key `caption`, spectral.js).
- Checked at 1280×800, no overlaps, no console errors.

## Update 3 (same day, AI_LOG step 7)
- Amber caption reworded by the human: "Bright amber lights reduced female response to 0%". Female response text now "ALAN interrupts female responses to mating calls" (AI_LOG step 8).
- Next task (human, verbatim in AI_LOG step 7, not started): move "Local firefly" to Explore with the other [DRAFT]
  steps; Female response goes straight to Two measured nights; the two glowing-orb animation is not needed there; a
  flyover to Philadelphia is fine.
