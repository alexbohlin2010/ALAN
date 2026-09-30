# Data not in the repo

The globe runs from what is committed (`globe_v2/tiles_rgba/`). These inputs are only needed to
**rebuild** tiles or re-run analyses. They are large, public, or licence-restricted.

| Input | Size | Source | Licence / note |
|---|---|---|---|
| VIIRS VNL v2.1 annual rasters, 2012–2024 (`vnl_<year>.tif`, 86400 × 35849, int16) | ~70 MB each | Zenodo record 17294744 (OpenGeoHub repackaging of EOG / Colorado School of Mines VNL V2) | CC-BY 4.0. **Trap:** 2022–24 are packed differently — apply each file's `scales` tag, then ÷10 → nW/cm²/sr. Never read the internal overviews. |
| Greyscale tiles (`globe_v2/tiles/`) | 418 MB | `tiler.py` from the rasters above | Build input for `colour/colorize.py` only |
| Aurora mask (`aurora_mask.npy`, 13 × 1793 × 4320 bool) | ~100 MB | Earlier globe session (`detect_aurora.py`, 4-test rule in `docs/HANDOFF_globe_session.md` §C) | Needed by `tiler.py` |
| ISS calibrated frames, Madrid (`Corr_iss030e082053*`, `iss042e183298*`, `iss061e035301*`) | ~300 MB | Zenodo 10.5281/zenodo.6638505 (`pre2013.zip`, `post2013.zip`) | CC-BY 4.0. The two published mosaics in that record are broken (NaN, wrong extent) — use per-frame files. |
| LICA-UCM lamp spectra (300–900 nm) | ~3 MB | https://guaix.fis.ucm.es/lamps_spectra | Authors ask to be contacted before use — not redistributed here |
| LSPDD lamp spectra (380–780 nm) | <1 MB | api.lspdd.sbcloud.ca (Université de Sherbrooke) | Not redistributed; fetched by API |
| CIE S 026 α-opic Toolbox v1.049a | 1 MB | files.cie.co.at | CIE terms |
| VIIRS DNB relative spectral response | small | pyspectral `download_rsr()` | — |
| Camera colour matrices (Nikon D3S/D4/D5) | — | LibRaw `src/tables/colordata.cpp` | Values quoted in `colour/iss_chromaticity.py` |

## Rebuild order

```
# 1. spectra → lamp classes (needs numpy, pandas, openpyxl, colour-science)
python scripts/compute_spectra.py && python scripts/lamp_classes.py
python colour/lamp_class_xy.py
# 2. tiles (needs rasterio, numpy, pillow; ~25 min per year on 10 cores)
python globe_v2/tiler.py 2012 --out globe_v2/tiles
python globe_v2/tiler.py 2024 --out globe_v2/tiles
# 3. colour layer (~5 min)
python colour/colorize.py 2012 2024
# then bump TILE_V in globe_v2/index.html so browsers reload tiles
```

**Paths:** `tiler.py` reads rasters from `~/alan-streetlight-cct/vnl/` and the aurora mask from
`~/alan-streetlight-cct/globe_v1/`; `lamp_class_xy.py` reads spectra from `~/alan-streetlight-cct/spectra/`.
Edit those constants at the top of each script if your copies live elsewhere.
