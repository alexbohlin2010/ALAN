# Handoff: display white back to 4000 K; impacts palette C (heraldic)

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Colour / design task" steps 1–3. Read `RULES.md` first. Earlier: `2026-10-04_intro-crickets-soundscape.md`, `2026-10-04_colour-mask-not-pursued.md` (update 3: white was 3200 K).

## Human decisions
- Increase the 2015/2025 contrast: the display white tint goes back to **4000 K** ("bring 2025 temperature up to 4000k").
- Impacts dot colours: **palette C "deep heraldic"** (chosen from agent options A royal jewel / B cool / C heraldic).
- Species-group colours change too, to match ("yes also change species colors").

## State (nothing committed)
- `pipeline/colour/08_display_tints.py`: `RAMP_WHITE_CCT_K = 4000`. Rerun; `data/derived/colour/display_tints.json` "ramp_white" = 4000 K [1.0, 0.8317, 0.649]. Nothing else in the file changed. The file does not show in `git status` (untracked or ignored; not checked).
- `app/src/tileLayer.js`: `RAMP_TINTS[1]` = [1.0, 0.8317, 0.649], with a "display choice, not data" comment. The same white is used in both years.
- `pipeline/colour/METHOD.md` "Display ramp": updated to 4000 K.
- `app/src/impacts.js`:
  - `CATEGORY_COLORS`: Behaviour #18b86b, Physiology #2f5bff, LHT #8a3dff, Population #e0306b, Community #14a8c4. Replaces Linda's globe_v2 colours and the Impacts step 22 picks (old values are in a code comment).
  - `SPECIES_COLORS`: Mammals #d0344f, Birds #2f5bff, Fish #14b0d0, Amphibians #8a3dff, Reptiles #c45ae6, Insects #c4c41e, Arthropods #ff6aa0, Plants #18a85e, Algae/fungi/microbes #62e6a8.
- Browser checks at :5173: Studies globe dots, All effects in both colour modes, India swipe before/after (3200 vs 4000 K, live-switched). No console errors.

## Open (human decides)
- The species hues are an agent draft in the C style; not yet explicitly approved. Smallest pair difference is 12.8 (Birds/Amphibians), lower than the old set's 15. Birds = Physiology blue and Amphibians = LHT violet (the same hex values are used in the two modes).
- Lane labels for Physiology (#2f5bff) and LHT (#8a3dff) are darker on black than before; readability not measured.
- Not changed: legend default key-dot #5fd4e6 (`style.css:127`), `OTHER` #888888, the "In the dark" grey #9a9a9a in the worked example.
- Narrow / tall pane (800 px wide): the All effects chart overlaps the left menu and the card (existing layout issue, not from this change).
- Earlier open items still stand (sun code, dev handles, CC BY credit, Safari .ogg, audits).

## Update 1 (AI_LOG colour / design task steps 4–7): fact text below the menu; Conclusion on the black globe
- **Human decisions:** the big fact text must never overlap the left menu; option A "below" (B "right of the menu" was prototyped and removed). Conclusion: text centred on the black globe, coming in as the lights fade out, with the blue glow back.
- **State (not committed):**
  - `app/src/story.js` `placeFact`: pushes `#fact` down (CSS var `--fact-shift`) to start 24 px below the menu whenever they would overlap; ResizeObserver on the menu and the text, plus window resize. `style.css`: landscape `#fact` transform uses the var.
  - `app/src/introScene.js` `createDarkScene` (+ `DARK_MS = 2500`): tile `uFade` 1 → 0 and the intro's even blue ring (uBase 0.18) in over 2.5 s; reversed when leaving. `main.js` calls it from `applyStage` (and clears it in `setMode('impacts')`). `style.css`: `body.story-dark #globe { opacity: 0 }` removed; Conclusion text centred, 2.5 s fade-in.
- **Agent choices open for the human:** 2.5 s duration; ring brightness (= intro's formless ring); text max-width min(40vw, 480px); text fade curve (CSS ease, it arrives a little ahead of the lights going out).
- **Not checked:** fact overlap in portrait / very small windows (the cards, chart filter and spectral number can still overlap the menu there; measured in step 4); whether pushing the text down can run it into the bottom nav on short windows (not seen at 1024×640 or 1280×800 in step 4/7 data).
