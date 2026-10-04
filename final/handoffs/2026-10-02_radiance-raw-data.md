# Handoff: collect raw radiance data for the globe

Written 2026-10-02 at the end of the session that set up `final/`. It records facts and human decisions only. Background is in `DATA_INVENTORY.md`, and the full history is in `AI_LOG.md`.

## Decisions the human has made

- The final app is rebuilt **from original datasets**, slowly, under `RULES.md`.
- The globe surface radiance and the city-level data are two separate questions. Combining VNL (globe) with HDNTL (cities) is of interest, but **not decided**.
- Colour will be handled later, in a separate task (see "Not in scope").
- Linda will supply the raw files for her own datasets. That is not part of this task.

## Facts the next agent needs

**The radiance copy we already have**, at `~/alan-streetlight-cct/vnl/vnl_2012..2024.tif`:
- It's a Zenodo 17294744 repackaging (OpenGeoHub) of EOG VNL annual composites.
- Format: int16, EPSG:4326, 86400×35849, nodata −32768.
- Every year is rounded to 1 nW/cm²/sr. 2012–21 have `scales`=1 and 2022–24 have `scales`=10, so values ×scale÷10 give nW/cm²/sr.
- Versions are mixed: 2022 is v2.2 (S-NPP + NOAA-20), 2023–24 are v2, and 2012–21 are untagged.
- There is no download log. SHA-256 for 2012 and 2024 is in `Alexander/colour/METHOD_colour.md:182-183`.

**The EOG originals** (Colorado School of Mines, eogdata.mines.edu):
- Float, not rounded. They need a free account (Keycloak).
- **Agents must not create accounts or enter passwords** (RULES and the safety rules). The human registers and downloads, or takes over the browser for the login step.

**HDNTL** (Zenodo 17079409, v2, CC-BY 4.0; Pei, Zhu, Tan, Hu, Chen; doi:10.5194/essd-17-5675-2025):
- Daily, 653 cities, ~500 m, 2012–2024, derived from Black Marble VNP46A2.
- Values are angular-corrected and partly **interpolated**; flag rasters mark which.
- Size: ~33 GB for all cities, or 7.1 GB for the 5 zips that held our previous 50 cities.

**Other facts:**
- No satellite product gives colour. VIIRS DNB is a single panchromatic band.
- Repo: `~/Desktop/ALAN` (github.com/alexbohlin2010/ALAN). `final/data/raw/` exists and is empty. The repo's `.gitignore` has not yet been set up for `final/`.

## The task for the next session

Acquire the raw radiance inputs for the globe, and only that. No transformation, tiling or rendering.

1. **Research and present options.** Do not choose. Cover:
   - Which VNL product and version give one consistent series 2012–2024: v2.1 vs v2.2, single vs dual satellite, `average_masked` vs `average` vs `median`, and the companion `cf_cvg` / `lit_mask` files.
   - Repackaged Zenodo vs EOG originals.
   - Note that 2012 starts in April 2012.
   - For each option give: URL/DOI, licence, version, per-file and total size, what's lost or changed, and whether an account is needed.
2. **Wait for the human to choose.**
3. **Plan storage with the human:** raw rasters in git or gitignored. GitHub's limit is 100 MB per file, and repo size matters. Propose and wait.
4. **Download (or receive from the human)** into `final/data/raw/radiance/<source>/`, files unmodified. Write `final/data/raw/radiance/MANIFEST.csv`. For each file: filename, source URL/DOI, product, version, licence, download date, who downloaded it (agent/human), size in bytes, SHA-256.
5. **Read-only verification:** dims, dtype, CRS, nodata, scale tags, value range. Record the results in the manifest notes. Don't "fix" anything.
6. Log every step in `AI_LOG.md`. Write a new handoff when done or at about 30% context.

## Not in scope (record only, don't start)

- **Global colour temperature (CCT) map.** The human wants a full-globe CCT map, even a crude one. They prefer ISS astronaut photos as the colour source, with SDGSAT-1 as a possible 2022–24 check. The free account at sdgsat.ac.cn reportedly takes several days to verify, with a starting quota of about 20 images. This is a separate future task with its own handoff.
- HDNTL download (unless the human brings it into this task).
- Linda's datasets.
