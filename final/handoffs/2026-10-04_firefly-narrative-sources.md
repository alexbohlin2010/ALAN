# Handoff: firefly narrative, round 0 (sources)

Written 2026-10-04. Facts and human decisions only. Full record: `AI_LOG.md` entries "Firefly narrative brief, implementation plan" and rounds 0a–0c. Before: `2026-10-04_firefly-door-transition.md`. Read `RULES.md` first.

## Human decisions
- Brief: `~/.codex/.chatgpt-projects/g-p-6aa3592867d481919852a34ccc43a1bb/ALAN_Firefly_Narrative_Implementation_Brief.md` (outside the repo). Order: global evidence → firefly studies → synthesis → *Photinus pyralis* (local bridge) → Philadelphia vs Cherry Springs measured spectra.
- Scene 1 = the existing "Light type" step (Impacts). The firefly studies start directly after it.
- Three papers, in this order:
  1. Owens, Meyer-Rochow & Yang 2018 (*Aquatica ficta*) = signal production plasticity: ambient wavelength changes how males flash.
  2. Owens & Lewis 2021 (*Photinus obscurellus*, study 299; the existing "fireflies" chapter, kept) = courtship dialogue disruption: ambient spectrum alters male signalling and female response.
  3. Kivelä et al. 2023 (*Lampyris noctiluca*, study 243) = mate-finding success.
  Summary: signal production → female response → mate-finding success.
- Owens 2018 scene shows the paper's reported results (no re-analysis of the raw recordings).
- Spectra scene: rebuilt in `final/app` (no React), the app's simple main-body style without surrounding text panels, keeping the draft's 3D light-dot spectrum effect. Draft: `Linda/visual tests/spatial/philadelphia-spectral-space/`; source CSVs: `Linda/data/philadelphia and cherry springs data/` (W m⁻² nm⁻¹, 280–840 nm, July 2014).

## Files now in `data/raw/impacts/narrative of fireflies/`
- Human-supplied: `Aquatica_ficta/` (8 nights, May 2016, strip charts + keys; README), `Data_Kivela2022.xlsx` (300 traps; Color, Lux, Photons, Males). No MANIFEST rows yet: source and download date not known to the agent.
- Agent-downloaded (human approved), read-only, MANIFEST rows added: Owens 2018 PDF (CC BY 4.0), Kivelä 2023 PDF (CC BY 4.0, Jukuri reprint).
- Data deposits named in the papers: Owens 2018 Dryad doi:10.5061/dryad.73qg8; Kivelä 2023 Dataverse doi:10.7910/DVN/QWQPLJ.

## Facts checked
- Data S1: 4,905 rows / 314 studies; app uses 3,254 effects / 207 located studies. No *A. ficta* rows. *L. noctiluca* study 243: 4 rows (BS cool/warm only). *P. pyralis*: 12 rows, studies 028 (5) + 229 (7), both Virginia field studies.
- Kivelä workbook has lux and photons per treatment but no wavelengths; one trap has `NA` males.
- PDF text can be extracted on this Mac with PDFKit via `osascript -l JavaScript` (no poppler/pypdf installed).

## Open (human decides)
- Source/date for the human-supplied `Aquatica_ficta/` and `Data_Kivela2022.xlsx` (for MANIFEST rows).
- Where the mice chapter sits relative to the firefly section.
- Claims/provenance record: keep `sources` in `story.js`, or add a claims file (new file layout).
- *P. pyralis* occurrence and sensitivity sources (draft curve is "modeled", not usable as is).
- Spectrum CSVs to be copied into `final/data/raw/` (needs a request).

## Next step (as agreed)
- Extract Owens 2018 reported results (treatments, flash measures, statistics) into a labelled derived file by script, then build the Owens 2018 scene directly after "Light type".
