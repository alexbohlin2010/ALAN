"""Shared helpers for the RULES §3 audit of the story statistics (2026-10-03).

Deliberately independent of pipeline/: nothing is imported from there, and this file
was written from the human-chosen definitions (AI_LOG "Story UX task", steps 2, 3, 7,
13, 14) before the pipeline scripts were read. Raw files are opened read-only
(/vsigzip/ and /vsizip/, GDAL PAM off, so no .aux.xml is written next to them).

Run every script from final/ with .venv/bin/python.
"""
import csv, hashlib, json, math
from pathlib import Path
import numpy as np
from osgeo import gdal, ogr

gdal.UseExceptions()
ogr.UseExceptions()
gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")

FINAL = Path(__file__).resolve().parents[2]
RAD_RAW = FINAL / "data/raw/radiance"
BND_RAW = FINAL / "data/raw/boundaries"
COG = {2015: FINAL / "data/derived/radiance/cog/vnl_2015_average_masked.tif",
       2025: FINAL / "data/derived/radiance/cog/vnl_2025_average_masked.tif"}
OUT_GLOBAL = FINAL / "data/derived/story/radiance_change_2015_2025.json"
OUT_COUNTRY = FINAL / "data/derived/story/country_change_2015_2025.json"
RESULTS = Path(__file__).resolve().parent / "results"
YEARS = (2015, 2025)

# Human-chosen definitions (restated here, not taken from the pipeline)
R_AUTHALIC = 6371007.1809      # m, authalic radius of WGS84 ("sphere", B5)
NO_DATA = -1.5                 # pairwise exclusion (B7); other negatives -> 0
THRESHOLDS = (0.0, 0.5, 1.0)   # L1 lit = > 0 (main); sensitivity > 0.5, > 1 (step 7)


def read_manifest(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def rad_rows():
    return {int(r["period"][:4]): r for r in read_manifest(RAD_RAW / "MANIFEST.csv")}


def raw_rad_path(year):
    return RAD_RAW / rad_rows()[year]["path"]


def bnd_rows():
    return {r["layer"]: r for r in read_manifest(BND_RAW / "MANIFEST.csv")}


def bnd_zip(layer):
    return BND_RAW / bnd_rows()[layer]["path"]


def open_raw(year):
    return gdal.Open(f"/vsigzip/{raw_rad_path(year)}", gdal.GA_ReadOnly)


def open_layer(layer):
    ds = ogr.Open(f"/vsizip/{bnd_zip(layer)}")
    return ds, ds.GetLayer(0)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def row_area_km2(gt, rows):
    """Area (km2) of one pixel in each row, on a sphere of the authalic radius.
    A = R^2 * dlon_rad * (sin(lat_north) - sin(lat_south)), edges from the geotransform as stored."""
    rows = np.asarray(rows, np.float64)
    lat_n = gt[3] + rows * gt[5]
    lat_s = gt[3] + (rows + 1) * gt[5]
    dlon = math.radians(gt[1])
    return (R_AUTHALIC ** 2) * dlon * (np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_s))) / 1e6


def centre_lon(gt, cols):
    return gt[0] + (np.asarray(cols, np.float64) + 0.5) * gt[1]


def centre_lat(gt, rows):
    return gt[3] + (np.asarray(rows, np.float64) + 0.5) * gt[5]


def clean(a, b):
    """Pairwise rule: returns (valid, a0, b0) with -1.5 in either year excluded and other negatives -> 0."""
    valid = (a != NO_DATA) & (b != NO_DATA)
    a0 = np.where(a < 0, 0.0, a.astype(np.float64))
    b0 = np.where(b < 0, 0.0, b.astype(np.float64))
    return valid, a0, b0


def pct(new, old):
    return 100.0 * (new - old) / old


def write_result(name, obj):
    RESULTS.mkdir(exist_ok=True)
    def conv(o):
        if isinstance(o, (np.integer,)): return int(o)
        if isinstance(o, (np.floating,)): return float(o)
        if isinstance(o, (np.bool_,)): return bool(o)
        if isinstance(o, np.ndarray): return o.tolist()
        raise TypeError(type(o))
    (RESULTS / name).write_text(json.dumps(obj, indent=1, default=conv))


def relerr(a, b):
    a, b = float(a), float(b)
    if a == b: return 0.0
    return abs(a - b) / max(abs(a), abs(b))
