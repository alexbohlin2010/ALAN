"""Step 02 (read-only check): where are the -1.5 pixels, and what does the other
year hold at the same places? Helps answer whether -1.5 means "dark" or "missing".

Writes data/derived/radiance/checks/no_coverage.json:
  - per year: counts of -1.5 per 5-degree latitude band
  - cross-tab: value class in the other year at each year's -1.5 pixels
  - per year: the 10 one-degree cells holding the most -1.5 pixels
  - per year: -1.5 count on the raster's last row (southern edge)
Usage (from final/):  .venv/bin/python pipeline/radiance/02_check_no_coverage.py
"""
import json
import numpy as np
from osgeo import gdal
from config import DERIVED, NO_COVERAGE, cog_path

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")


def classify(v):
    return {"-1.5": int((v == NO_COVERAGE).sum()),
            "other_negative": int(((v < 0) & (v != NO_COVERAGE)).sum()),
            "zero": int((v == 0).sum()),
            "0<v<=1": int(((v > 0) & (v <= 1)).sum()),
            "1<v<=10": int(((v > 1) & (v <= 10)).sum()),
            "v>10": int((v > 10).sum())}


def main():
    a_ds, b_ds = gdal.Open(str(cog_path(2015))), gdal.Open(str(cog_path(2025)))
    gt = a_ds.GetGeoTransform()
    W, H = a_ds.RasterXSize, a_ds.RasterYSize
    lat_bands = {2015: {}, 2025: {}}
    cells = {2015: {}, 2025: {}}
    other_at = {2015: [], 2025: []}  # other-year values at this year's -1.5 pixels
    step = 1200
    for y in range(0, H, step):
        h = min(step, H - y)
        a = a_ds.GetRasterBand(1).ReadAsArray(0, y, W, h)
        b = b_ds.GetRasterBand(1).ReadAsArray(0, y, W, h)
        for year, this, other in ((2015, a, b), (2025, b, a)):
            r, c = np.nonzero(this == NO_COVERAGE)
            if r.size == 0:
                continue
            lat = gt[3] + (y + r + 0.5) * gt[5]
            lon = gt[0] + (c + 0.5) * gt[1]
            for band, n in zip(*np.unique((np.floor(lat / 5) * 5).astype(int), return_counts=True)):
                lat_bands[year][int(band)] = lat_bands[year].get(int(band), 0) + int(n)
            keys = (np.floor(lat).astype(int) + 90) * 1000 + (np.floor(lon).astype(int) + 180)
            for k, n in zip(*np.unique(keys, return_counts=True)):
                cells[year][int(k)] = cells[year].get(int(k), 0) + int(n)
            other_at[year].append(other[r, c])
    out = {"note": "Counts of value == -1.5 per year. Latitude bands are 5 deg, labelled by "
                   "their southern edge. Cells are 1 deg, labelled by SW corner (lat, lon).",
           "years": {}}
    for year in (2015, 2025):
        other = np.concatenate(other_at[year]) if other_at[year] else np.array([], np.float32)
        top = sorted(cells[year].items(), key=lambda kv: -kv[1])[:10]
        out["years"][year] = {
            "count": int(sum(lat_bands[year].values())),
            "by_lat_band_5deg": dict(sorted(lat_bands[year].items())),
            f"value_in_{2025 if year == 2015 else 2015}_at_same_pixels": classify(other),
            "top_1deg_cells": [{"lat": k // 1000 - 90, "lon": k % 1000 - 180, "count": n}
                               for k, n in top],
        }
    # -1.5 pixels on the raster's last row (centre 65.0 deg S), per year
    last = H - 1
    out["last_row"] = {"row": last, "lat_centre": gt[3] + (last + 0.5) * gt[5]}
    for year, ds in ((2015, a_ds), (2025, b_ds)):
        out["last_row"][f"count_{year}"] = int(
            (ds.GetRasterBand(1).ReadAsArray(0, last, W, 1) == NO_COVERAGE).sum())
    p = DERIVED / "checks/no_coverage.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
