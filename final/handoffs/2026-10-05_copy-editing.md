# Handoff: copy editing, divider labels, background hum, intro type

Written 2026-10-05. Facts and human decisions only. Full record: `AI_LOG.md` "Copy editing" steps 1–14.
Read `RULES.md` first. Before: `2026-10-05_broader-impacts-circle.md` (Update 4).

## State
- Branch `main`, HEAD `afac47d20`. **Nothing committed this session.** Uncommitted: `app/content/story.js`,
  `app/index.html`, `app/src/introScene.js`, `app/src/story.js`, `app/src/style.css`, `AI_LOG.md`, this handoff.
- Outside the repo: `~/.claude/launch.json` gained a "hum-test" entry (python http.server, 127.0.0.1:5190, serving
  this session's scratchpad, where the test page `hum-c.html` lives; scratchpad is temporary).

## Human decisions and what was built
1. **Statistic text** (human wording): "From 2015 to 2025, Artificial Light at Night (ALAN) increased by 41%."
   Word order only; number and sources unchanged.
2. **Divider explained, option A** (human): "2015" and "2025" sit beside the handle and move with the divider;
   the corner year labels are hidden while the divider shows. The corner "2025" stays in Impacts (no divider).
   Agent choice: labels at handle height, 16 px / 600 like the old corner labels. (`index.html`, `style.css`)
   **Option B** (a hint at the handle) also chosen by the human: **not built; waiting for the human's wording**.
3. **Background hum** (human: "low hum of light", calming; recordings found on freesound were "not pleasant").
   Made in Web Audio in `introScene.js`, no file/library/licence. Human's settings (test page): C1 32.7 Hz,
   warmth (low-pass) 2000 Hz, fifth 0 %, breathing 0 %, then volume 50 % and soft (brown) noise 35 % (step 10).
   - Fades in (3 s) as Zarathustra's close-out fade starts (agent choice: crossfade); starts at a skip if the intro
     is skipped.
   - Going back to the intro: hum fades out (0.6 s), returns after the intro (human: "don't overlap hum and intro").
   - Conclusion: fades out over 2.5 s (human); comes back if the viewer goes back to Broader Impacts (agent choice).
     Step field `humOff: true`.
   - Explore: muted on arrival, the mute button turns it back on (human). Step field `muteAudio: true`.
   - Mute covers music, crickets and hum; the mute button stays visible while the hum plays; where the corner
     "2025" shows, the mute sits to its left (human; first misread as "next to the Impacts heading", corrected).
4. **Statistic starts on its own** at the end of the music (human): when the music's tail reaches silence
   (28.85 s music time) the story advances, only if the intro is still the current step.
5. **Type**: intro line "...and then there was light" in **Cormorant Garamond italic 400**, 28 px, via a Google
   Fonts link in `index.html` (human chose the link over self-hosting; visitors' browsers fetch from Google;
   Georgia fallback). Step 12 tried system-ui first. "Use keys to navigate" hint now system-ui sans serif (human:
   consistency). Begin button and its "with audio" line are still Georgia (not discussed).

## Checked (in-app browser, port 5173, 1280×800; no console errors at each step)
Statistic text and divider labels; India/Tanzania sweeps clear of menu, card, nav; auto-advance 1/21 → 2/21;
hum gain values (0.175 on, 0 on intro replay / Conclusion), Explore mute and unmute, mute vs "2025" no overlap;
fonts loaded. **The agent cannot hear audio**: levels and sound judged by the human only.
Not checked: portrait / narrow windows; Safari.

## Open (human decides)
- Option B hint wording (and: Statistic only or also India/Tanzania; fades on first drag or on leaving).
- The copy edits themselves: the step-1 table of all user-facing strings is in the chat of this session only;
  regenerate it from `app/content/story.js` and the files listed in AI_LOG step 1. Live tags: 7 [DRAFT]
  (intensity, light-type, fireflies, signal-production, female-response, mate-finding, local-firefly),
  2 [PLACEHOLDER] (two-nights, species-perceptions); Tanzania text marked DRAFT only in a code comment.
- Strings outside story.js needing a human OK to touch: light-type words (`pipeline/impacts/maps/light_types.csv`),
  species tags (`data/derived/spectra/species_curves.json`).
- Begin button font; intro text size in Cormorant; Google Fonts vs self-hosting before publication (privacy).
- Dev-only handle added: `window.introHum` (with the other intro dev handles, to remove before publication).
- Commit when asked.

## Next-session prompt (suggested)
```
You're working in ~/Desktop/ALAN/final (git root ~/Desktop/ALAN; check which branch is checked out before anything else and tell me — last seen on main). Read RULES.md first and follow it for the whole session. Then read handoffs/2026-10-05_copy-editing.md and app/content/story.js.

Task: copy editing continues. I write the wording; you put it in exactly as I give it.
1. First, no changes: re-list every user-facing text of the live story steps (skip `retired`) as a table: step id, label, field, current text, [DRAFT]/[PLACEHOLDER] tag. Stop for my edits.
2. Apply my edits exactly as written. Remove a tag only when I give the final text for that field or say so. If an edit changes a number or a factual claim, tell me which source in the step's `sources` supports it, or that none does, before applying it.
3. After each batch, check in the browser preview (port 5173: Begin → intro → story steps) at 1280×800: new text shown, no overlap with the left menu or bottom nav, no console errors. Show me screenshots.

CONCURRENCY: other Claude sessions may edit app/vite.config.js, app/src/tileLayer.js, app/src/main.js, app/src/style.css, app/src/impacts.js, app/src/introScene.js and app/content/story.js. Re-read a file right before editing it and keep edits small and local.
- Do NOT read-modify-write AI_LOG.md. Append only with a single shell append (cat >> AI_LOG.md <<'EOF' ... EOF), logging every step with my exact prompt.
- data/raw/, ~/Desktop/ALAN/Linda and ~/Desktop/ALAN/Alexander are read-only. No data or pipeline changes.
- Do not commit, push, delete, download, install or create accounts without my explicit go-ahead. Ask before adding any library, font or asset. Do not send my email address or other personal data in any request.

Write a handoff in handoffs/ when the task is done or at ~30% context.
```
