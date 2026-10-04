# Handoff: intro night soundscape (crickets before the music)

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Intro soundscape task" steps 1–9. Read `RULES.md` first. Earlier: `2026-10-04_light-story-taglines.md`, `2026-10-04_intro-sunrise-scene.md`.

## Human decisions
- After Begin, the black screen first plays night-wildlife sounds; then the flow runs as before (formless globe → text → sun → lights → UI). The sun stays unless the human asks.
- Intent (human): the artificial lights, "man's grandiosity", drown out the night nature sounds; "somewhat comical, somewhat serious".
- Recording: "Night ambience with crickets", KikeVilaplana, freesound 436528, CC0 (no credit required). Human downloaded the original WAV.
- Option A "drowned out gradually": crickets keep playing under the music and fade to nothing as the lights fade in.
- Crickets alone for ~4 s (step 3), then cut to **2 s** (step 7).
- Step 6: crickets fade faster; text in later and out exactly when the lights come in; **sun sprite removed** ("looks too fake"), blue halo kept.
- Step 7: the **orange limb glow stays** ("evocative"); lights rise faster from the same start on the chord (human chose "Faster rise, same start").
- Step 8: the crickets must be **gone by the time the lights hit**, fading from about halfway through the text.
- Mute button only (no "Begin without audio"); mute covers both sounds.

## State (committed on branch alexander-final-rebuild, step 9)
- `app/src/introScene.js` (constants near the top):
  - `PRE = 2000`: crickets alone on black after Begin; the music plays silently from 8.0 s music time, fade-in at 10.0 s.
  - `CRICKETS_IN = 500` (agent choice) fade-in; `CRICKETS_OUT = 2000`: crickets fade 18.0 → 20.0 s music time, silent exactly at `T.lights`.
  - `T.text = 16000` (high C; agent choice for "later"); text fades out from `T.lights` (20.0 s, the chord) over textOut 0.5 s.
  - Lights: same start (20.0 s) and length (6 s), curve ease-out cubic `1 − (1 − x)³` (agent choice; was smoothstep).
  - `SHOW_SUN = false`: sprite left out (code kept; the invisible sun path still paces the halo/orange glow).
  - Dev handle `window.introCrickets`.
- Click → silence ≈ 21 s. Music cut points unchanged (27.35 → 28.85 s).
- `app/public/audio/436528__kikevilaplana__night-ambience-with-crickets.wav` (14.8 MB, unmodified copy) + entry in `MANIFEST.md`.
- Browser checks at each step (timing samples, screenshots, skip during pre-roll); no console errors.

## Open (human decides)
- By ear: cricket level relative to the music; text-in point (16.0 s vs 14.0 s G was offered); lights curve steepness.
- Whether to remove the sun code entirely (now only switched off).
- File size (14.8 MB WAV): a smaller MP3/AAC copy would need a tool (e.g. ffmpeg, not installed); afconvert (macOS built-in) exists but its use was not discussed.
- Dev handles to remove before publication. Stale comments at the top of `T` in introScene.js still describe the text on the first trumpet C and the sun on the high C (superseded by the step 6 comment).
- Earlier open items still stand (CC BY credit line for the music, Safari .ogg for the music, narrow windows).
