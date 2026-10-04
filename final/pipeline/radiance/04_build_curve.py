"""Step 04: build the radiance -> grey display curve (B4 = hist_eq, B6 = P99.99).

Pools all positive pixels (v > 0) of both years over the full raster, takes the
top value at CURVE_TOP_PERCENTILE, and builds a cumulative histogram on
CURVE_BINS log-spaced bins from the smallest positive value to the top.
grey(v) = 0 for v <= 0; 255 * interp(min(v, top), edges, cdf) for v > 0.
Display choice only: it does not change any data value.

Usage (from final/):  .venv/bin/python pipeline/radiance/04_build_curve.py
Output: data/derived/radiance/curve/hist_eq_p9999.json
"""
import json
import numpy as np
from osgeo import gdal
from config import (YEARS, cog_path, CURVE_TOP_PERCENTILE, CURVE_BINS, CURVE_PATH)

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")


def positives(path):
    ds = gdal.Open(str(path))
    b, out = ds.GetRasterBand(1), []
    for y in range(0, ds.RasterYSize, 2048):
        a = b.ReadAsArray(0, y, ds.RasterXSize, min(2048, ds.RasterYSize - y))
        out.append(a[a > 0])
    return np.concatenate(out)


def main():
    per_year = {y: positives(cog_path(y)) for y in YEARS}
    pos = np.concatenate(list(per_year.values()))
    top = float(np.percentile(pos, CURVE_TOP_PERCENTILE))
    vmin = float(pos.min())
    edges = np.logspace(np.log10(vmin), np.log10(top), CURVE_BINS + 1)
    hist, _ = np.histogram(np.minimum(pos, top), bins=edges)
    cdf = np.concatenate([[0.0], np.cumsum(hist) / hist.sum()])
    ref = [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, top]
    grey = np.round(255 * np.interp(ref, edges, cdf)).astype(int)
    out = {
        "curve": "hist_eq", "unit": "nW/cm2/sr",
        "rule": "grey = 0 if v <= 0 else round(255 * interp(min(v, top), edges, cdf))",
        "pool": "all pixels with v > 0 in both years (full 86401x33601 raster each)",
        "positive_pixels": {str(y): int(p.size) for y, p in per_year.items()},
        "top_percentile": CURVE_TOP_PERCENTILE, "top": top, "min_positive": vmin,
        "pixels_above_top": int((pos > top).sum()),
        "reference_grey": [{"radiance": float(r), "grey": int(g)} for r, g in zip(ref, grey)],
        "edges": edges.tolist(), "cdf": cdf.tolist(),
    }
    CURVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CURVE_PATH.write_text(json.dumps(out))
    print(json.dumps({k: v for k, v in out.items() if k not in ("edges", "cdf")}, indent=2))


if __name__ == "__main__":
    main()
