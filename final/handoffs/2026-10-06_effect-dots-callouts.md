# Handoff: effect dots open study cards; Dots toggle removed; quote callouts on the four Impacts chart steps

Written 2026-10-06. Facts and human decisions only. Full record: `AI_LOG.md` "Effect dots and examples" steps 1–12.
Read `RULES.md` first. Before: `2026-10-06_impacts-firefly-first.md`.

## State
- Branch `main`. This session's work committed at the human's request (step 12), not pushed.
- Dev server on 5173 started by this session (launch config "alan-final-app"). The in-app pane was hidden at the end
  (document hidden, no animation frames): screenshots force frames.
- Another agent worked on audio (app/src/introScene.js) in parallel; not touched here.

## What the chart steps do now
- Every effect dot (All effects, Light level, Light type) and every dot of the Broader Impacts circle opens its study's
  card once settled; the open study's dots get a white ring. Dots: Effects | Studies toggle and the study-dot view removed.
- Card (`#study`) on chart / circle steps: bottom of the chart area, on the side away from its dot; draggable by its title.
- Callouts (`impacts.callouts` in content/story.js): each arrow press is a beat. Beat 0 = the step's sentence; each
  next beat replaces the big text with a verbatim quote, "Author Year" and a "Source" button; the study is ringed and
  its dot marked once the dots have settled; no card unless "Source" (or a dot) is clicked. Past the last quote the
  arrow moves the story; arriving backwards starts on the last quote.

| Step | Beats after the sentence (effect id, source of quote) |
|---|---|
| All effects | firefly 299-3 shown on arrival (fades at the first callout) → Thawley & Kolbe 2020 (169-1, title) |
| Light level | Stone et al. 2012 (166-1, abstract) |
| Light type | Atchoi et al. 2023 (308-1, abstract) |
| Broader Impacts | Heinen et al. 2022 (200-6, abstract) → Dimovski & Robert 2018 (154-2, abstract) → Moaraf et al. 2020 (106-108, title) → Oppedal et al. 2001 (112-4, title) |

- Broader Impacts sentence: "Across the biosphere, ALAN is upsetting the equilibrium of natural systems." (human).
- Firefly example removed from Light level and Light type.
- New data: `data/derived/impacts/abstracts.json` (145 studies, `documented`, Crossref cache, title_match only) made
  by `pipeline/impacts/11_abstracts.py` (offline). The JSON is git-ignored (final/.gitignore `data/derived/impacts/*`);
  only the script is committed. Not audited (RULES §3).

## Human decisions (step in AI_LOG "Effect dots and examples")
- Clicks on the three charts and the circle; remove the toggle; S2 / R3 / C2 / D1; quotes from abstracts (A) (step 2).
- Quotes are natural-language lines in the study's own words, not |g|; firefly beat fades at the first callout (3).
- The six-then-seven callouts and their steps (4–8, 11); "Author Year" citation (4); card on the side away from the dot,
  draggable; bats card bottom right; card only after the dots have rendered (6); callouts do not open the card,
  "Source" button instead (9). Story direction stated by the human: "disequilibrium → uncertainty → risk" (4, 6).

## Agent choices to confirm (display only)
- Which record of each study is marked (effect ids above); order within Broader Impacts; quote / citation sizes;
  drag handle = title only; click radius 5 px.

## Seen, not changed / open
- Data S1's aphid records for study 200 are mixed in direction (the quote is the authors' summary).
- The card shows "Median effect: |g| …" (e.g. bats 0.16 "below small").
- Escape does not close the card on story steps (as before).
- "Source" pressed before the dots have settled does nothing.
- Quotes from titles: 169, 106, 112 (Data S1 titles); 299 / 180 abstracts left out by the title_match rule.

## Next task (human, 2026-10-06)
- Start the Conclusion piece of the story (prompt given in chat at the end of this session).
