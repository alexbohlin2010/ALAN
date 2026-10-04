# Handoff: firefly tabs (Signal production, Female response, Mate-finding) built as one scene

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` rounds 4a–4i (Signal production) and
5a–5g (Firefly tabs). Before: `2026-10-04_two-nights-built.md`, `2026-10-04_firefly-narrative-sources.md`. Read
`RULES.md` first.

## State of the code
- Worktree branch `claude/interesting-gagarin-73979e` (fast-forwarded to `claude/cool-ishizaka-9fd75f` 71b2d3ada at
  the start, human request). One commit on top with this session's `final/` work (round 5g); not pushed.
- Not committed: `.claude/launch.json` in the worktree root (preview config: `npm --prefix final/app run dev -- --port
  5175 --strictPort`; port 5173 = main checkout, 5174 = previous worktree).

## Human decisions (this session)
- Signal production = Owens, Meyer-Rochow & Yang 2018 reported results only (no re-analysis of `Aquatica_ficta/`).
- Files in the impacts folders: `pipeline/impacts/08_owens2018.py` → `data/derived/impacts/owens2018_results.json`;
  `pipeline/impacts/09_kivela2023.py` → `data/derived/impacts/kivela2023.json` (one file: `paper` + `traps` + `checks`);
  PDF text files saved but gitignored; `.gitignore` exceptions for the two JSONs; audits in `audits/owens2018/`,
  `audits/kivela2023/`.
- Cross-agent audits by `claude-sonnet-5-5` (different model from the builder).
- Signal production scene "A + B": 3D beats (8 LED peak columns, two males: dark base values vs the chosen light,
  flashing at Table 1 rate and relative brightness) + 2D Table 1 strip; colours = generic nm → RGB (Bruton 1996).
- Female response = the former '[DRAFT] Fireflies' chapter (study 299) moved in; its Explore entry and the door from
  the Light type dot 299-3 removed.
- Mate-finding = Kivelä et al. 2023 reported results + the deposited trap table (`Data_Kivela2022.xlsx`), counts per
  trap, no new statistics; each trap drawn as a pillar of male points, grouped by treatment at its peak wavelength,
  control at the left ('dark').
- The three tabs are one continuous scene: depth bands along the shared nm axis (signal 0, fireflies −7, glow −14),
  camera glides between them, other bands faint.
- Continue in the same session for the two tabs (human override of RULES §5 for that step).
- Agent-written card text for the three tabs (marked `[DRAFT]`), on the human's request (round 5g).
- Do not play the app's music when testing (mute before Begin).
- Any further changes to the three tabs (incl. audit findings below) in a new session; the human reviews the three
  tabs together in the app.

## Data facts
- Owens 2018: Table 1 = 8 wavelengths (444, 463, 488, 515, 533, 597, 628, 663 nm) × dim/bright; dark base 5420 counts,
  43.167 peaks/min; 20 Results-text p-values; 31 statements. Three text vs Table 1 p-value disagreements in the paper
  itself (dim intensity 488 nm 0.017/0.018; dim frequency 463 nm 0.049/0.0049; bright frequency 463 nm <0.0001/0.00042),
  listed, not resolved. The text layer drops ≤/≥; affected statements carry `as_printed` from rendered pages.
- Kivelä 2023: Table 1 (blue 452 nm, white 449, yellow 575, red 625; photons, lux), Tables 2–4, Table 3 success %
  (control 68.3, blue 35.0, white 36.7, yellow 71.2, red 73.3); 299 traps + 1 all-"NA" row (night 10, site 3, Excel row
  139) excluded; 42 checks (traps vs paper) all agree (624 males, 170/299 traps with ≥ 1 male).

## Audits
- Owens: `audits/owens2018/AUDIT_2026-10-04.md` (no wrong value; F1–F7); F2–F4 fixed (round 4i); re-check
  `recheck_2026-10-04/RECHECK.md` 6/6 PASS (notes C1–C4, info). RULES 3.2: seed 20261004, N = 20, **20/20** (human).
- Kivelä: `audits/kivela2023/AUDIT_2026-10-04.md` (no wrong value). RULES 3.2: seed 20261004, N = 20, **20/20**
  (human, reported in chat). Findings not acted on (human: new session):
  - F1 Table 1 `Filter` column not in the JSON nor in `not_reported`.
  - F2 some Results "did not differ" sentences and Methods details (light sources, site spacing, measurement setup)
    neither captured nor listed.
  - F3 docstring says per-treatment "sum of males" checks; the code checks only the total.
  - F4 no automatic check for control lux/photons, `fig2_n`, dates, replicate balance (auditor confirmed by hand).
  - F5 red photon check passes exactly on the rounding boundary (1.265e13 vs printed 1.27e13).
  - F6 labels at section level; lux/photons per trap labelled `measured` though one value per treatment, measurement
    context (dark room, 20 cm) not stored with the data.
  - F7 `units.males` "per night (2 h)" is from the paper, not the deposit (unit "Number"); traps carry no source-row
    field.
  - MANIFEST note (raw folder, human edit): says "1 row has Males = NA"; that row has all five value fields NA.

## App facts
- `app/src/spectral.js`: chapters `signal`, `fireflies`, `glow` (+ `mice`), `BANDS`, `#spectral-strip`; `main.js`
  unchanged; door code in `impacts.js`/`main.js` kept but inactive (no step has a `door` key).
- Checked in the in-app browser at 800×600 and 1280×800: no console errors. At 800×600 the Signal strip covers the
  lower part of the 444–488 nm columns. Phone width not checked.

## Open (human decides)
1. Review of the three tabs together; changes in a new session.
2. Kivelä F1–F7 (above); Owens re-check notes C1–C4 (info).
3. Card text: the three `[DRAFT]` texts.
4. Push / merge of this branch.
