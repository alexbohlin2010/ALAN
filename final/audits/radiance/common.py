"""Shared helpers for the RULES §3 audit of the derived radiance data (2026-10-03).

Deliberately independent of pipeline/radiance/: nothing is imported from there.
Raw files are opened read-only through /vsigzip/ with GDAL PAM off, so no
.aux.xml is ever written next to them. Expected values are restated here from
the MANIFEST and from the human decisions recorded in the handoff
(handoffs/2026-10-03_render-prototype.md), not taken from the pipeline code.

Run every script from final/ with .venv/bin/python.
"""
import csv, hashlib, json
from pathlib import Path
import numpy as np
from osgeo import gdal

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")

FINAL = Path(__file__).resolve().parents[2]
RAW_DIR = FINAL / "data/raw/radiance/eog"
MANIFEST = FINAL / "data/raw/radiance/MANIFEST.csv"
DERIVED = FINAL / "data/derived/radiance"
COG = {2015: DERIVED / "cog/vnl_2015_average_masked.tif",
       2025: DERIVED / "cog/vnl_2025_average_masked.tif"}
CURVE = DERIVED / "curve/hist_eq_p9999.json"
TILES = DERIVED / "tiles/v1"
RESULTS = Path(__file__).resolve().parent / "results"
YEARS = (2015, 2025)

# Stated rules (handoff 2026-10-03, human decisions B3/B5/B7, tile grid "native pyramid")
NO_DATA = -1.5                 # B5/N2: -1.5 = no data; other negatives -> 0
FLAG_ND = {2015: 1, 2025: 2}   # B3: blue channel bits
FLAG_OUT = 4
TILE = 256

# Value counts written in the MANIFEST notes (read-only check of the raw files, 2026-10-02)
MANIFEST_COUNTS = {
    2015: dict(width=86401, height=33601, pixels=2903160001, min=-1.5, max=99290.078,
               zero=2837640350, positive=65456583, positive_lt1=38250850, gt200=30745,
               gt1000=5149, eq_minus_1_5=35995, other_negative=27073, nan=0),
    2025: dict(width=86401, height=33601, pixels=2903160001, min=-1.5, max=83972.148,
               zero=2821508654, positive=81649055, positive_lt1=34789564, gt200=37533,
               gt1000=6860, eq_minus_1_5=1977, other_negative=315, nan=0),
}


def manifest_rows():
    """Return {year: row} from MANIFEST.csv, keyed by the year in the period column."""
    with open(MANIFEST, newline="") as f:
        rows = list(csv.DictReader(f))
    return {int(r["period"][:4]): r for r in rows}


def raw_path(year):
    return RAW_DIR / manifest_rows()[year]["filename"]


def open_raw(year):
    return gdal.Open(f"/vsigzip/{raw_path(year)}", gdal.GA_ReadOnly)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def load_curve():
    c = json.loads(CURVE.read_text())
    return np.asarray(c["edges"], np.float64), np.asarray(c["cdf"], np.float64), float(c["top"]), c


def curve_grey_float(v, edges, cdf, top):
    """Unrounded 255 * interp(min(v, top), edges, cdf), the stated rule before rounding."""
    return 255.0 * np.interp(np.minimum(np.asarray(v, np.float64), top), edges, cdf)


def curve_grey(v, edges, cdf, top):
    """Stated rule: grey = 0 if v <= 0 else round(255 * interp(min(v, top), edges, cdf))."""
    v = np.asarray(v, np.float64)
    g = np.round(curve_grey_float(v, edges, cdf, top))
    return np.where(v > 0, g, 0).astype(np.uint8)


def write_result(name, obj):
    RESULTS.mkdir(parents=True, exist_ok=True)
    p = RESULTS / name
    p.write_text(json.dumps(obj, indent=1, default=str))
    print(f"wrote {p.relative_to(FINAL)}")
    return p
