# Handoff: intro sunrise scene prototype (`?intro=sunrise`)

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Intro scene task" steps 1–15. Read `RULES.md` first. Before this: `2026-10-04_sdgsat-colour-questions.md` (colour, unrelated).

## State
- The prototype runs only with the URL switch `?intro=sunrise`. **The default intro (CSS black overlay, A5a) is unchanged.** Whether the prototype becomes the default is open (human).
- Nothing committed. Files touched:
  - `app/src/introScene.js` (new): the whole scene, timeline, audio, Begin screen, mute button, rotation.
  - `app/src/tileLayer.js`: one uniform `uFade` (default 1) multiplying the tile colour.
  - `app/src/story.js`: optional `intro` argument; Begin gate before `go(0)`; `intro.spin()`; `clearAll` calls `intro.stop()`.
  - `app/src/main.js`: creates the scene only when `INTRO_MODE === 'sunrise'`.
  - `app/src/style.css`: prototype block (`#begin`, `#intro .hint`, `#mute`).
  - `app/public/audio/zarathustra_einleitung_macleod.ogg` + `MANIFEST.md` (new; download approved by the human).

## Human decisions
- Option B: three.js limb-glow shell + crescent + sun sprite added via `.scene()`, removed after the intro.
- Music: Kevin MacLeod, *Also sprach Zarathustra* Einleitung (Wikimedia Commons, CC BY 3.0, 2010), stored in `app/public/audio/`. Composition public domain (US: published 1896; EU: from 2020).
- Begin screen: one "Begin / *with audio*" button; a round speaker-icon mute button top right (shown on the Begin screen and while the music plays).
- "Use keys to navigate" (human's wording) with ← → key icons, bottom centre, shown from the music start until ~13.8 s music time.
- Sequence order: formless globe → text → the sun appears (text fades exactly then) → lights fade in on the first big chord → drums play on after full light → music stops before the second horn call.
- Formless start ~2 s; total ~19 s from click to silence ("21 is even better", then shortened further).
- Globe rotates (Earth's direction) from the intro until the first step with a camera flight (India).
- Sun moves at constant speed.
- Music end: moved earlier in several steps by ear to 28.85 s music time; long smooth fade (1.5 s).

## Timeline (music time = seconds into the recording; constants `T` at the top of `introScene.js`)
| Music time | What happens |
|---|---|
| 10.0 s | Begin click; music starts here (fade-in 0.6 s); formless ring; keys hint |
| 12.0 s | Text on the first trumpet C |
| 16.0 s | Sun's core clears the limb on the high C; text fades on that frame |
| 20.0 s | Lights fade in on the chord (6 s, story.js `lightsIn`) |
| 26.0 s | Fully lit; UI joins (story.js `uiIn`) |
| 27.35–28.85 s | Raised-cosine fade to silence (Web Audio gain), then pause |

Music events measured in the browser (pitch bands; agent readings, the human confirmed the horn by ear): trumpet C 12.0 / G 14.0 / high C 16.0 s; chord 20.0 s; timpani ~24.0–28.9 s; second trumpet call ~29.0 s. Steps 5–8 had mislabelled a ~3.6 s low swell as the trumpet (corrected in step 9).

## Open (human decides)
- Make `?intro=sunrise` the default (and remove the CSS intro path) or keep it as an option.
- The CC BY credit line: wording and placement (draft in `app/public/audio/MANIFEST.md`).
- Glow colours, sun position (`SUN_END`), fade lengths: agent prototype values.
- Narrow / portrait windows: the sun leaves the right edge ~2 s after appearing.
- Safari playback of `.ogg` not checked (a converted copy would need a tool such as ffmpeg, not installed); iOS not tested.
- Git: whether to commit `app/public/audio/` (4.3 MB).
- Dev-only handles in `introScene.js` (`window.introAudio`, `introSun`, `introGain`) can go before publication.

## Noted in the log
- Step 5: the agent's download command sent the human's email address in the User-Agent header to Wikimedia (not requested; reported in chat).
