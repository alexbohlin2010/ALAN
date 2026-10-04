# Handoff: SDGSAT-1 and the colour question (Q&A only)

Written 2026-10-04. Read `RULES.md` first. Colour state is unchanged: see `handoffs/2026-10-04_colour-mask-not-pursued.md` (updates 1–4) and `pipeline/colour/METHOD.md`. Log: AI_LOG entry "2026-10-04: SDGSAT-1 and the colour question".

## Done
- Read-only research. No code, data, tiles or METHOD.md changed. Nothing downloaded into the repo, nothing committed.

## Human decisions (this session)
- None yet. Three options were offered (A: 2025 check for a few cities; B: replacement; C: not at all). The human's choice is pending.
- Human note: they created an SDGSAT-1 account at sdgsat.ac.cn on 2026-10-04. Verification status / quota: not known to the agent (the agent did not and must not sign in).

## Facts found (sources in the log entry)
- **Glimmer (GIU/GLI):** P 10 m (444–910 nm), B 424–526, G 506–612, R 600 or 615–894 nm (sources differ), RGB 40 m; 300 km swath; ~11-day revisit; launched 2021-11-05; science service from July 2022. `documented` (eoPortal; MDPI Remote Sens. 14:4543). Night overpass: ~22:00 or ~22:30 local (sources differ).
- **Years:** 2022 onward only. No 2015 data exists. Nearest to our 2025 = 2024–25 scenes.
- **Coverage:** described as global routine acquisition; actual cloud-free night coverage per city not checked.
- **Access:** free; register at sdgsat.ac.cn; verification "can take several days"; default quota 20 images; more needs a proposal; contact sdgsat1@cbas.ac.cn; product grade L4A for GIU; files = preview, metadata, TIFF. `documented` (CBAS SDGSAT-1 User Manual, read directly this session). Licence: "Regulations of the Use of SDGSAT-1 Data" exists (UN-SPIDER) but its text was not read.
- **LED vs sodium in papers:** Lv et al. 2024 Applied Energy (DC streetlight data, 80.3 %, Beijing/Shanghai/Guangzhou/Shenzhen); Liu et al. 2024 RSE 305:114079 (89.9 %, Shanghai); IJDE 2023 doi:10.1080/17538947.2023.2297013 (Beijing, 0.92/0.95); Labrousse, Haspel & Levin 2025 JQSRT 340:109450 (one interchange, Israel; R/G most consistent; satellite brightness change not detected). All need local ground truth and a trained classifier.
- **Open ready-made products:** none found for lamp type or colour, global or per city. JRC GHS-SDGSAT = Po Plain only. CBAS 2023 "atlas" of 147 cities = 10 m (panchromatic per news), no download link or colour layer found.
- Not found: per-scene file size, radiometric accuracy of the colour bands, the licence text, a public lamp-type dataset.

## Open for the human
1. Choose A, B or C (or other).
2. If A or B: check own account quota/verification on sdgsat.ac.cn; any download needs explicit go-ahead and goes to `data/raw/` with a manifest (RULES §2).
3. All earlier colour open items unchanged (India value, city CCT accuracy, 2015 fallback, record-point offsets, audits, git handling of `data/raw/colour/`).

## Scratch (session scratchpad only, not in the repo)
- `manual.txt` (pdftotext of the CBAS manual), `polyu.pdf` (an HTML error page from a failed curl, not the paper).
