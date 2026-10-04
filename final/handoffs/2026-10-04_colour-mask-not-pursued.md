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

## Update 1 (AI_LOG colour steps 60–62): India, Italy, white tint 3000 K
- **Human decision:** the white display tint is **3000 K** (was 4000 K). `app/src/tileLayer.js` `RAMP_TINTS[1]` = [1.0, 0.7247, 0.4295], from `display_tints.json` class 2. METHOD.md "Display ramp" updated. No data or grid change.
- **India 2025 photos:**
  - 23 kept photos from 5 runs, all with share ≥ 0.9 (median 0.988). 2015: 19 photos, median 0.243.
  - Most are oblique with limb, Moon or lightning. With the limb/glow rules applied, the shares stay 0.95–1.0: the city lights themselves are counted ≥ 2,700 K.
  - Photo median CCTs are 3,811–4,851 K.
- **India sources:** SLNP 13.1 M LED streetlights by Nov 2024. Programme aim: 35 M conventional streetlights replaced. 13.1 / 35 ≈ 0.37 (`inferred`, the denominator is a target).
- **Italy:** about 65 % of about 10 M public light points are LED (`documented`, ASSIL / PoliMi via Il Fatto Quotidiano, Feb 2026). Kept photos: 2025 median 0.725; drawn 0.62.
- **CCT of kept photos** (median of photo medians): 2015 2,249 K; 2025 3,207 K.
- **Open:** any India-specific value or review (options in step 60), not decided. City CCT accuracy still untested. The display choices listed in step 61 (brightest-first, two tints, no atmosphere) are unchanged apart from the tint.

## Update 2 (AI_LOG colour steps 63–64): prototype colour modes
- **Human:** "prototype B and C, show me screenshots". No mode chosen yet.
- **Prototype switch:** URL `?ramp=brightest|place|blend`, `?block=N`. The default (brightest-first) is unchanged.
  - Needs the new `data/derived/colour/global_white_share_values.png`: cell white shares, written by `10_white_share_grid.py` step 5.
  - The existing grid outputs are byte-identical.
  - Dev-only `window.tileLayer` lets the mode be switched live (`tileLayer.uniforms.uMode/uBlocks`).
- **Seen:** at country zoom the three modes look nearly the same. Differences show only close up (Po valley).
- **Open:** keep, change or remove the prototype modes (human). METHOD.md not updated for them.

## Update 3 (AI_LOG colour step 65): white tint 3200 K; session closed
- **Human decision:** display white = **3200 K** (`08_display_tints.py` `RAMP_WHITE_CCT_K`, `display_tints.json` "ramp_white" [1.0, 0.7499, 0.4789]; `tileLayer.js` `RAMP_TINTS[1]`). Sodium stays 2000 K. Supersedes the 3000 K of update 1.
- **Prototype colour modes** (update 2): still in the code, default off. Keep or remove: open.
- **Still open:** India value or review; city CCT accuracy; 2015 fallback; record-point offsets; audits (RULES §3); git handling of `data/raw/colour/`.

## Update 4 (AI_LOG colour steps 66–67): option B is the default
- **Human decision:** default colour mode = **B, white by place**, 1/20° blocks (~5 km). A block is white if a fixed position hash < the cell's white share; brightness does not matter.
  - Tints 2000 K / 3200 K.
  - `?ramp=brightest` (the old rule) and `?ramp=blend` remain as URL switches.
- **Needs** `data/derived/colour/global_white_share_values.png` (`10_white_share_grid.py` step 5). METHOD.md "Display ramp" documents it.
- **Human remark (step 66, not acted on):** India's 2025 radiance growth is not visually impressive on the globe. Brightness display not changed.
- **Still open:** as in update 3, plus whether to remove the unused URL modes and the dev-only `window.tileLayer` handle.
