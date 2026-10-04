"""Shared paths and constants for the radiance pipeline. Paths are relative to final/."""
from pathlib import Path

FINAL = Path(__file__).resolve().parents[2]
RAW_DIR = FINAL / "data/raw/radiance/eog"
DERIVED = FINAL / "data/derived/radiance"
COG_DIR = DERIVED / "cog"
PREVIEW_DIR = FINAL / "previews"

# Raw inputs (read-only). SHA-256 from data/raw/radiance/MANIFEST.csv.
RAW = {
    2015: ("VNL_v21_npp_2015_global_vcmslcfg_c202205302300.average_masked.dat.tif.gz",
           "1cdafa2039e49fe64b629592e20d33dc746ecc77824a6a4898a76c03311104fa"),
    2025: ("VNL_npp_2025_global_vcmslcfg_v2_c202604011200.average_masked.dat.tif.gz",
           "55cdc85dab51a26b2806071c2efee49314d1d8bb235581df2b0a03574c95e3ab"),
}
YEARS = (2015, 2025)
NO_COVERAGE = -1.5  # B5/N2 (human, 2026-10-03): -1.5 is "no data"; other negatives -> 0


def cog_path(year):
    return COG_DIR / f"vnl_{year}_average_masked.tif"

# Display curve (human, 2026-10-03): histogram equalisation over positive pixels of
# both years pooled; top = this percentile of the same pooled positives.
CURVE_TOP_PERCENTILE = 99.99
CURVE_BINS = 4096
CURVE_PATH = DERIVED / "curve/hist_eq_p9999.json"

# Tiles (human, 2026-10-03): native pyramid on the raster's own pixel grid.
TILE_SIZE = 256
TILE_VERSION = "v1"
TILE_DIR = DERIVED / "tiles" / TILE_VERSION
# Blue-channel flags (bit values)
FLAG_NODATA_2015, FLAG_NODATA_2025, FLAG_OUTSIDE = 1, 2, 4
