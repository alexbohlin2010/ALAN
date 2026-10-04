# Handoff: colour, lamp-pixel mask fix tested and not pursued

Written 2026-10-04. Follows `handoffs/2026-10-03_colour-fallback-documented.md`. Read `RULES.md` first. Log: `AI_LOG.md`, colour steps 58–59.

## Human decisions (this session)
- The lamp-pixel mask fix is **not pursued**. Human: "the change is so small it's not worth it".
- No change to code, grid, sidecar or render.

## State (unchanged from the previous handoff)
- 2025 fallback: 0.41 / grey 159 (Brazil census, `estimated`). 2015 fallback: 0.1844 / 203 (photo median).
- `photo_share_median` 2025 = 0.848 is in the sidecar but not used.
- Not audited (RULES §3). Nothing committed, nothing deleted.

## Facts found (step 58; details in the log)
- **Sample:** same 24 frames as before (seed 20261003, 1,999 kept 2025 frames with a CCT value). The per-pixel re-run reproduces the stored values.
- **Options tested:**
  - **A, limb cut** (long thin arc + its sky side): correct on 4 of 24, no clean city frame cut, 2 missed.
  - **B, glow blobs:** the texture threshold overlaps city cores (0.136–0.139) and glow (0.098–0.174).
  - **C, frame-level drop:** loses 382 frames (2015) and 519 (2025).
  - **D, human contact-sheet review:** not built.
  - **Point-like-only:** biased toward white (removes orange city cores). Not offered.
  - **Station hardware:** not detected by any automatic rule.
- **All kept frames:**
  - Limb found in 149 (2015) and 350 (2025) frames. Precision on the full set is not checked.
  - Photo-median change: 2015 0.184 → 0.185 (A) / 0.171 (A+B); 2025 0.848 → 0.841 (A) / 0.850 (A+B).
- **Not measured:** per-cell and per-country effect of A/B (individual limb frames changed −0.44 to +0.74).

## Open for the human
1. **City CCT accuracy** (orange-looking lights counted ≥ 2,700 K): untested. Update 1 of the previous handoff showed the white regions come from the local/regional photo shares.
2. **2015 fallback (0.184, photo median):** unchanged.
3. **Record point ≠ location of lights in oblique frames:** not addressed.
4. **Still open from earlier:** more thumbnails per cell; NEF checks; audits (RULES §3); deleting downloaded thumbnails / NEFs; git handling of `data/raw/colour/`.

## Scratch (session scratchpad only, not in the repo)
- `mask_options.py`, `count_all.py`, `count_all.json`, `opt_sheet_0..3.png`.
- If any of these numbers are used in data, redo the method as a repo script.
