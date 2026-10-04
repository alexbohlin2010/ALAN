# Handoff: mice chapter option 2; final/ committed on branch alexander-final-rebuild

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` "Push task" steps 7–13. Before: `2026-10-03_mice-dials-and-push.md`. Read `RULES.md` first.

## Human decisions (this session)
- Mice chapter: option 2 (lamp beats zoom to the night quarter; the clock test on its own all-dark constant-darkness dial with before / after onset ticks; 5 beats). No untreated baseline. Part A declared done by the human.
- No ISS photos in git; keep the three EOL `MANIFEST.csv` files.
- A1: git-ignore EOL photos and query / photo-page HTML, the Brazil census PDF, all of `data/raw/impacts/mice/` (study 278 CC BY-NC-ND; Lucas 2014 PMC fair use).
- B1: the derived data the app needs goes to Linda as a separate zip.
- C2: the human opens the PR. The human pushes via GitHub Desktop (the agent's push had no stored GitHub credentials).
- Wait for the colour session before committing (it finished 00:12:57 with `2026-10-04_colour-mask-not-pursued.md`).

## Done
- `app/src/spectral.js` / `app/content/story.js` (mice): lamp shown as a tick outside the ring (band shows the thinning); `view: 'night'` on the lamp beats; new beat `show: 'dark'` ("15 min", label marked [DRAFT]); `clock` beat on the DD dial; tags `constant darkness` vs `day` / `night`; time-based camera easing. Browser-checked at localhost:5173.
- 278 numbers checked (step 7): all match; the paper reports the long-λ −14 % and −26 min as not significantly different from untreated controls (not shown); §2.4 contradicts itself on pulse length (60 vs 15 min).
- `final/.gitignore`: new block (step 11).
- Branch `alexander-final-rebuild` from `main` 6e1d06d40; commit b63e2836f (177 files, 18.2 MB) + a second commit with this handoff and the log. **Not pushed by the agent; no PR yet.**
- Zip: `~/Desktop/ALAN_derived_for_Linda.zip` (outside the repo), 220,117,658 bytes, sha256 83616116a85c44b783068a98ea8763b08681274bcd9f05f5f22206f881a0b1e6, 21,033 entries. Contains `data/derived/radiance/tiles/v1/`, `data/derived/impacts/{effects,studies,study_locations,spectra_278,spectra_299,perception_299}.json`, `data/derived/colour/global_white_share_grid.{json,png}`. Unzip inside `final/`.

## Open (human decides)
- Push via GitHub Desktop; open the PR (draft description in AI_LOG step 9 chat / below); hand the zip to Linda.
- Mice step text still says "one day for each lamp" (DRAFT, human's to write); the new "15 min" beat label is agent wording, DRAFT.
- In the night zoom the top of the outer dial sits behind the headline.
- `pipeline/requirements.txt` lacks xlrd 2.0.1.
- Whether to ask Linda about reuse of her visual approaches (shader, body-clock idea).
- To rebuild data from raw, Linda would also need the git-ignored raw downloads (EOG radiance 593 MB; EOL colour ≈2.7 GB; licensed papers), listed in the MANIFESTs.

## PR description (draft given in chat)
Adds `final/`, the rebuild of the ALAN globe from raw data. Please read `final/RULES.md` first: every agent session follows it (humans decide story, design and architecture; raw data is read-only; every value is labelled; every AI step is logged). Then read the newest files in `final/handoffs/` (what was done and decided) and `final/AI_LOG.md` (the full step-by-step record with exact prompts). Large raw downloads, licence-restricted papers and `data/derived/` are git-ignored; raw sources are listed in each `data/raw/*/MANIFEST.csv`, and the derived data the app needs comes separately as a zip (unzip inside `final/`). Notes: xlrd 2.0.1 is installed in `final/.venv` (used to read the Lucas 2014 workbook) but is not yet in `pipeline/requirements.txt`. The mice chapter (`app/src/spectral.js`, DRAFT) uses a visual idea from Linda's body-clock scene, credited in the file header; the spectral point shader is adapted from Linda's `FireflyCommunication.tsx`. Whether to ask Linda about reusing these is still open.
