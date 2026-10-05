# Handoff: Impacts reorder done (chapter content changes next)

Written 2026-10-05. Facts and human decisions only. Full record: `AI_LOG.md` "Impacts reorder" steps 1–4.
Read `RULES.md` first. Before: `2026-10-05_story-sequence.md`.

## State
- Branch `main`. **Nothing committed.** Uncommitted: `app/content/story.js`, `app/src/impacts.js`, `AI_LOG.md`,
  `handoffs/2026-10-05_story-sequence.md`, this handoff.
- Preview: another session's Vite server on port 5173 (same folder), viewed in the in-app browser.

## Human decisions and what was built
1. Order (human): Light = Intro, Statistic, Ecosystems; Impacts = Studies, Fireflies, Female response, Local firefly,
   Two measured nights, Species perceptions, All effects, Light level, Light type, Broader Impacts, Conclusion;
   Explore = Explore all studies, [DRAFT] Signal production, [DRAFT] Mate-finding. 17 steps.
2. Retired, not deleted (human): `swans`, `one-effect`, `fireflies` (Taipei, Owens et al. 2018).
3. New step `female-site` ("Fireflies"): globe view of the Female response study (Owens & Lewis 2021, Data S1 study 299).
   Point = Arnold Arboretum, Boston (42.30469, −71.12099, printed in the paper's Methods; "Boston only", human).
   Card: [DRAFT] by the agent from the paper's Methods, at the human's request ("Reuse Taipei card shape").
   Code: one entry `owenslewis2021_boston` in `SITE_POINTS` (app/src/impacts.js).
4. Female response grows out of that point's glow (spectral.site `owenslewis2021_boston`; camera Boston 0.04, fly 2200).
5. Female response -> Local firefly is a plain cut (the human accepted this "for now"; one spectral site serves both
   directions, so closing into the Philadelphia glow would need a code change).
6. Chart highlight on All effects / Light level / Light type: record 299-3 (female response rate, blue LED 31 lx,
   |g| 2.68), label "Fireflies, female response" (human picked 299-3; label as proposed).

## Checked (1280x800, no console errors)
Menu order; each moved step loads; Boston glow transition both ways; Local firefly -> Two nights halves; charts show
the 299-3 highlight; Explore heading lands on Explore all studies; cards clear of menu and nav.

## Open items (not decided)
- Beat toggle overlaps the mute button top right on spectral steps (Female response, both drafts). Not touched.
- Chapter wording changes (human: "We are going to change these specific chapters too"). Example: All effects text
  says "The 207 studies on the globe", now reached from Species perceptions.
- Explore drafts keep their old transition settings (Signal production site owens2018; Mate-finding site
  spitschan2016_city, camera Philadelphia); in Explore they arrive as plain cuts.
- From earlier handoffs, unchanged: Option B divider hint wording; Begin button font; Google Fonts vs self-hosting;
  dev handle `window.introHum`; RULES §6 question on agent drafting; commit when asked.
