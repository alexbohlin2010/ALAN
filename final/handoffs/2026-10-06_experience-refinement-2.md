# Handoff: Experience refinement (pass 2): Response values, firefly transitions, ALAN question, Impact on black

Written 2026-10-06. Facts and human decisions only. Full record: `AI_LOG.md` "Experience refinement" steps 16–21.
Read `RULES.md` first. Before: `2026-10-06_experience-refinement.md`.

## State
- Branch `main`. Committed at the human's request (step 21); not pushed.
- Dev server on 5173 belongs to another session (opened by URL). The repo's launch config is named "app".
- app/src/introScene.js (audio, another agent's) not edited.

## Human decisions (step in AI_LOG "Experience refinement")
- Female response: menu label "Response"; text "ALAN interrupts female firefly responses to mating calls." (17).
- Response values (option A, 17–18): the range "10.3–48.6 %" and its grey label fade; the four values fly to their lamp
  tags (red 48.6, blue 36.1, warm white 11.6, cool white 10.3 %; `documented`, Owens & Lewis 2021 Results; 48.6 is
  correct, 49.6 appears nowhere); "female response rates" (human wording) flies with them as their axis label, above
  the top value; values 18 px from the lamp names.
- Owens & Lewis 2021 is a lab study (field-collected adults, tested in acrylic chambers under LEDs); Impact text
  "Outside of the lab, does ALAN impact fireflies in the wild?" (17).
- Spectra firefly line: "Fireflies are most visually sensitive to the same wavelength band which is most prominent in
  the Philadelphia night sky." (human wording, 17).
- Perception: reply colour = the cloud's channel yellow (M1, 17); dimmed to nearly disappear in Philadelphia (18).
- Fireflies → Response: no zoom; a dark circle opens from the dot at once, scene unscaled (17).
- Perception → Firefly Populations: no flight; Perception fades out onto the eastern US view; the text fades in after
  0.5 s (18–19).
- ALAN (A4, 19): the question fades in below the 41 % line (line unmoved); both stay through the flight to Fireflies,
  then the Fireflies text fades in.
- Response → Impact → Spectra: sideways pan (P2) built, then cancelled by the human ("makes me a bit dizzy"); now
  sequential fades: Response out, then Impact in; Impact out, then Spectra in; back the same. Impact on plain black,
  no globe or limb ring; the firefly guide glow kept (human, 20).

## Mechanisms added (code)
- story.js (src): `onLeave` hook; `cutFrom` (no flight from that step; text fades in after 500 ms); `carryFrom` (the
  previous step's text stays through the flight); `revealBelow` (line 1 under line 0, line 0 anchored).
- spectral.js: beat `values` / `valuesLabel` (runSplit); door `flat` (no scaling). twoNights.js: REPLY_DIM, set()
  `fade` and `hold`. main.js: panLeave / panRun / clearPan / ghostFact (fades), #pan-backdrop, story key `black`.

## Agent choices to confirm (display only)
- Split: hold 1200 ms, flight 900 ms; door 1300 / 900 ms; REPLY_DIM 0.35, REPLY_SIZE 2; Perception fade 1200 ms;
  Response / Impact / Spectra fades 600 out, 900 in; text fade-ins 900 ms.

## Seen, not changed / open
- After the split the dark share (98.7 %) is no longer on screen; the amber beat keeps its grey label (asked, no answer).
- Cherry Springs reply pulse is faint at the shared REPLY_DIM (asked, no answer).
- The nav arrows do not step Response's beats (only ← → keys and the top-right toggle), as before.
- Clicking → during Fireflies' 3.5 s flight opens the circle from the dot's position at that moment.
- The guide glow fades in on Impact while Response is still fading out.
- The Spectra firefly line rests on the step-5 one-off check (Philadelphia median peak 594 nm), not scripted (RULES §2.4).

## Next
- Human's next items (prompt given in chat, AI_LOG step 20): effects charts' text → axis label; size filter numbers;
  Biosphere Response down to two examples; an interconnection ending for Biosphere Response.
