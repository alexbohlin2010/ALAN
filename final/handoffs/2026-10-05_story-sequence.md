# Handoff: story sequence (Light opening shortened; Impacts reorder next)

Written 2026-10-05. Facts and human decisions only. Full record: `AI_LOG.md` "Copy editing and drafting" steps 1–6.
Read `RULES.md` first. Before: `2026-10-05_copy-editing.md`.

## State
- Branch `main`. **Nothing committed this session.** Uncommitted: `app/content/story.js`, `AI_LOG.md`, this handoff.
- Preview: another session's Vite server was already on port 5173 (same folder); this session viewed it in the in-app
  browser instead of starting its own.

## Human decisions and what was built (all in `app/content/story.js`)
1. **India and Tanzania out** (human: "Let's toss them"). Both steps moved unchanged into `retired` (agent read
   "toss" as retire, not delete; the human did not object).
2. **Ecosystems moved into Light** (`question`, part 2 -> 1), right after Statistic. Text (human, exact):
   "As light is expanding into new territory, what are the impacts on global ecosystems?"
   - Divider sweeps over West Africa while the question shows (human), using the existing `sweep` (east 15, west -17.5;
     agent choice). Its `impacts` stage was removed because any impacts stage hides the divider.
   - Camera { lat 10, lng -13, altitude 0.9 }, fly 3000 (agent choices; lng moved west so the sweep ends clear of the text).
   - Human: "good enough for now".
3. **Studies** (`studies`): `kind: 'fact'` (big text on the left like Statistic, human). Text (human, exact):
   "These 207 published studies measure the impacts of artificial light on biota." ("detail" -> "measure", human.)
   Former card text is now `note`, behind "Details & sources" with the two sources. `fly: 3000` added (human: the jump
   was "too stark"; duration agent choice).
4. Story is now 19 steps: Light = Intro, Statistic, Ecosystems; Impacts = Studies, Black swans, One effect, All effects,
   Light level, Light type, Fireflies, Signal production, Female response, Mate-finding, Local firefly, Two measured
   nights, Species perceptions, Broader Impacts, Conclusion; Explore = Explore all studies.

## Checked (in-app browser, port 5173, 1280x800; no console errors at each step)
Ecosystems text and sweep; Studies big text, fly-in, Details pop-up (ends close to the bottom edge but fits).
Not checked: narrow windows (at ~446 px a card's button sat under the left menu, seen in passing).

## Next task (human, 2026-10-05): reorder the Impacts sequence only (chapter content changes come later)
Human's words: "We are going to remove the swan example, and its worked example. and instead replace it with the
firefly female response study example ... then the order will be "female response", "local firefly", "two measured
nights", and "studies perceptions". let's move signal production and mate response into explore as drafts for now.
We are going to change these specific chapters too, but first let's just reorder the sequencing"

### Open questions for the human (not decided)
- "its worked example": the `one-effect` step ("What is an effect?") uses swan record 005-2; `effects`, `intensity`,
  `light-type` (and retired `species`) highlight it too (`example: '005-2'`, `exampleLabel: 'Black swans, night-time
  rest'`). Remove the `one-effect` step, or keep it and drop/replace its example? Same question for the chart highlights.
- Where `effects` (All effects), `intensity` (Light level) and `light-type` (Light type) go in the new order, or whether
  they stay at all.
- `fireflies` (Taipei collection site of Owens 2018) leads into `signal-production`. With signal production moving to
  Explore: does `fireflies` go with it, stay, or go?
- "studies perceptions" read as `species-perceptions`; "mate response" read as `mate-finding`. Confirm.
- "into explore as drafts": part 3 under Explore, and should their labels carry "[DRAFT]" (as the retired Mice did)?
- `swans`: move to `retired` (as India/Tanzania) or delete?
- `broader` and `conclusion`: assumed to stay after Species perceptions.

### Technical facts the reorder touches
- Transitions keyed by `site` (main.js, spectral.js, impacts.js): `fireflies` (impacts.site 'owens2018') ->
  `signal-production` (spectral.site 'owens2018') grows the scene out of the glow; `mate-finding` (spectral.site
  'spitschan2016_city', camera over Philadelphia) -> `local-firefly` (impacts.site 'spitschan2016_city') closes the
  scene into the glow; `local-firefly` -> `two-nights` (nightsSites) opens the halves from the glows. Removing
  `mate-finding` from between `female-response` and `local-firefly` removes that close-into-glow transition.
- `female-response` has no `impacts` stage (camera global, no study point); study 299 (Owens & Lewis 2021) is in
  Data S1, so a globe point like Black swans (`impacts: { view: 'globe', study: ... }`) is possible if the human wants it.
- Menu grouping is by `part` (main.js `partOf`); order = array order in `story`.
- Live inline tags: [DRAFT] on intensity, light-type, fireflies, signal-production, female-response, mate-finding,
  local-firefly; [PLACEHOLDER] on two-nights, species-perceptions.

## Other open items (from earlier handoffs, unchanged)
Option B divider hint wording; Begin button font; Google Fonts vs self-hosting; dev handle `window.introHum`; RULES §6
question (is agent drafting on request within the rules? asked this session, not yet answered); commit when asked.
