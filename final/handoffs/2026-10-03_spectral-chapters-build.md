# Handoff: Spectral chapters, first build (fireflies 299, mice 278)

Written 2026-10-03. Facts and human decisions only. Full record: `AI_LOG.md` Impacts steps 73–79 (before: `2026-10-03_spectral-chapters.md`). Read `RULES.md` first. Other sessions edit `story.js`, `main.js`, `style.css`, `vite.config.js`, `tileLayer.js`: re-read before editing; append to AI_LOG only with one shell `cat >>`.

## Human decisions (steps 74–78)
- Staging: fireflies = F-A (lamp spectra in depth rows, firefly sensitivity across them, flash at 567 nm, female reply % per lamp) + F-C (dim → bright = 10 × photons). Mice = M-B (two 278 spectra + melanopsin; 10 lx = 10 lx → 15 vs 1 mel lx → 51 vs 14 % → clock ring −117 vs −26 min).
- Placement P1: right after the "Light type" step in Part 2.
- Look: **Linda's visual approach (option A), rebuilt in plain JS + three** (no React/R3F). **Not** her label load: "keep this as simple as the rest of our data renderings … focus on clarity of story".
- **Two chapters only** (one story step each); beats **loop automatically**.
- **Perception layer** (lamp × animal sensitivity) yes, label `inferred`.
- 278 S. Fig. 1 and 299 Fig. 1 read from the PDF **vectors**: label `inferred` (both confirmed).
- No email to Owens & Lewis: "accept what we have and work with it".
- All step text, titles and number labels stay DRAFT until the human writes them.

## Built
- Data (all `inferred`, scripts rerunnable from raw, poppler CLI + stdlib only):
  - `pipeline/impacts/05_spectra_278.py` → `data/derived/impacts/spectra_278.json` (two LED curves, mW m⁻² nm⁻¹). Audit: `audits/impacts_spectra/AUDIT_2026-10-03.md` (Sonnet, PASS; 5 values −8e-5 kept). Source inconsistency: long-λ global max 641 nm, caption 608 (local max 607.96).
  - `pipeline/impacts/06_spectra_299.py` → `data/derived/impacts/spectra_299.json` (5 LEDs + P. scintillans). Audit: `audits/impacts_spectra_299/AUDIT_2026-10-03.md` (Sonnet, PASS).
  - `pipeline/impacts/07_perception_299.py` → `data/derived/impacts/perception_299.json` (LED × P. scintillans; null 676–775 nm where the sensitivity is not plotted). **Not audited yet.**
- App: `app/src/spectral.js` (new; shader adapted from Linda's `FireflyCommunication.tsx`, credited), small hooks in `app/src/main.js`, a CSS block at the end of `app/src/style.css`, two DRAFT steps `fireflies` and `mice` in `app/content/story.js` (beats with documented numbers + sources).
- Raw added: Lucas et al. 2014 supplement (`data/raw/impacts/mice/Lucas_2014_TrendsNeurosci_toolbox_workbook.xls`, `…_suppl_text.pdf`), MANIFEST rows.

## Open (human decides)
- **Melanopsin curve:** the Lucas workbook is binary `.xls`; no reader is installed. Options: install `xlrd` into `final/.venv` (needs approval), the human exports the sheet to CSV (Numbers), or a stdlib-only reader script. Then: script for the mouse melanopsin curve (`documented`) and a mice perception layer (278 lamp × melanopsin, `inferred`), with audit.
- §3.2 human spot checks pending: `audits/impacts_spectra/results/a04_spotcheck.md` (seed 20261003, N = 20) and `audits/impacts_spectra_299/results/b08_spotcheck.md` (seed 20261003, N = 24).
- §3.1 audit of `perception_299.json`.
- Look: the scene reads faint overall in screenshots; beat timing (4.2 s / 4.5 s); camera framing (bottom-right of the scene sits under the story card).
- Where the conclusion line ("white or amber lights won't solve this problem, only less light will") goes; earlier tension noted in step 68 (effects mostly not dose-dependent; 299 brightness mattered for females, not males; 278 only tested 10 lx).
- Only 5 of 299's 10 female-reply values are in the text (the rest only in Fig. 2b); dim amber is not available.
- Git-ignore for the CC BY-NC-ND 278 files and the Lucas files; whether Linda should be asked about reuse of her shader approach.

## Notes
- Preview: port 5175 is served by another chat's server; the pane throttles animation while hidden, so screenshots are needed to advance the loop.

## Next-session prompt
```
You're working in ~/Desktop/ALAN/final. Read RULES.md first and follow it for the whole session. Then read handoffs/2026-10-03_spectral-chapters-build.md and AI_LOG.md "Impacts task" steps 73–79. Skim app/src/spectral.js and the "fireflies" / "mice" steps in app/content/story.js.

CONCURRENCY: other Claude sessions may be running in final/ (e.g. the colour/CCT task), and they also edit app/vite.config.js, app/src/tileLayer.js, main.js, style.css and content/story.js.
- Do NOT read-modify-write AI_LOG.md (no Edit/Write tool on it). Append only with a single shell append (cat >> AI_LOG.md <<'EOF' ... EOF).
- Re-read any shared file right before editing it; never touch lines another session owns.
- Do NOT touch pipeline/colour/, data/raw/colour/, data/derived/colour/, or the radiance tiles/COGs (read-only).
- data/raw/ is read-only. ~/Downloads/spatial and ~/Desktop/ALAN/Linda are Linda's: read-only.
- Do not commit, push, delete or install anything without my explicit go-ahead.

Task: continue the two spectral chapters (fireflies 299, mice 278). First tell me the open items from the handoff in one short list and wait for my choices. Step text stays DRAFT unless I write it. Verify anything you build in the browser (preview "alan-final-app-impacts", port 5175; if another chat's server already runs there, use it). Log every step with my exact prompt; write a handoff when done or at ~30% context.
```

## Addendum (step 80): melanopsin curve
- xlrd 2.0.1 installed in `final/.venv` (human approved; not yet in `pipeline/requirements.txt`).
- The Lucas 2014 workbook holds **human** α-opic curves only ("Reference functions - human", 380–780 nm at 5 nm, human lens filtering, age 32). No mouse curve. Study 278's 15 vs 1 mel lx also used the human CIE S 026.
- Open (human decides): (1) human melanopic curve from the workbook (`documented`, labelled human) + mice perception layer (`inferred`); (2) mouse melanopsin from a pigment nomogram at 480 nm, no lens (`estimated`, on request); (3) keep the 480 nm line only. Optional: keep searching for the Lucas rodent toolbox (lab site did not resolve).
