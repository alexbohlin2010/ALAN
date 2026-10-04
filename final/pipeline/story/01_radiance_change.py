"""Global change in VIIRS radiance and lit area, 2015 -> 2025 (story statistic, part 1).

Run from final/:  .venv/bin/python pipeline/story/01_radiance_change.py
Output: data/derived/story/radiance_change_2015_2025.json  (label: inferred)

Inputs: the two Float32 COGs from pipeline/radiance/01 (bit-identical to the raw EOG
average_masked files; audits/radiance/AUDIT_2026-10-03.md). Read-only.

Definitions (human decisions, AI_LOG "Story UX task", steps 2, 3 and 7):
- M1: two numbers: % change in total area-weighted radiance, and % change in lit area,
  both relative to 2015.
- L1: lit = radiance > 0 in average_masked. Sensitivity check: also lit = > 0.5 and > 1
  nW/cm2/sr. Total radiance at a threshold sums only pixels lit at that threshold.
- Newly lit = not lit in 2015 and lit in 2025 (reported as area; also lit -> unlit).
- Pixel area on a sphere (authalic WGS84 radius): A = R^2 * dlon * (sin(lat_n) - sin(lat_s)).
- Pairwise: a pixel that is -1.5 (no data) in either year is left out of both years.
  Other negative values are set to 0 (same rule as the tiles, B5/N2).
- All columns of the raster are used as stored (86401 columns: the first and last
  are both centred on the 180th meridian); their share is reported separately.
Units: radiance nW/cm2/sr (EOG docs), area km2, radiance x area = nW/cm2/sr * km2.
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from osgeo import gdal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "radiance"))
from config import FINAL, RAW, NO_COVERAGE, cog_path  # noqa: E402

gdal.UseExceptions()
OUT = FINAL / "data/derived/story/radiance_change_2015_2025.json"
R_AUTHALIC_M = 6371007.1809  # WGS84 authalic sphere radius (m)
THRESHOLDS = (0.0, 0.5, 1.0)  # lit = value > threshold (nW/cm2/sr)
ROWS = 512


def main():
    t_start = time.time()
    ds = {y: gdal.Open(str(cog_path(y))) for y in (2015, 2025)}
    b = {y: ds[y].GetRasterBand(1) for y in ds}
    W, H = ds[2015].RasterXSize, ds[2015].RasterYSize
    gt = ds[2015].GetGeoTransform()
    assert (W, H, gt) == (ds[2025].RasterXSize, ds[2025].RasterYSize, ds[2025].GetGeoTransform())
    x0, dx, _, y0, _, dy = gt
    dlon = np.radians(dx)

    acc = {t: {k: 0.0 for k in ("rad15", "rad25", "area15", "area25", "area_new", "area_lost",
                                 "area_both", "rad15_edgecols", "rad25_edgecols")} for t in THRESHOLDS}
    cnt = {t: {k: 0 for k in ("lit15", "lit25", "new", "lost")} for t in THRESHOLDS}
    raw_pos = {2015: 0, 2025: 0}            # > 0 without exclusion, to compare with MANIFEST
    excl = {"nodata_2015_only": 0, "nodata_2025_only": 0, "nodata_both": 0}
    neg_set_zero = {2015: 0, 2025: 0}
    valid_area = 0.0

    for r0 in range(0, H, ROWS):
        n = min(ROWS, H - r0)
        a = b[2015].ReadAsArray(0, r0, W, n).astype(np.float64)
        c = b[2025].ReadAsArray(0, r0, W, n).astype(np.float64)
        raw_pos[2015] += int((a > 0).sum()); raw_pos[2025] += int((c > 0).sum())
        nd15, nd25 = a == NO_COVERAGE, c == NO_COVERAGE
        excl["nodata_2015_only"] += int((nd15 & ~nd25).sum())
        excl["nodata_2025_only"] += int((nd25 & ~nd15).sum())
        excl["nodata_both"] += int((nd15 & nd25).sum())
        valid = ~(nd15 | nd25)
        neg_set_zero[2015] += int(((a < 0) & ~nd15).sum()); neg_set_zero[2025] += int(((c < 0) & ~nd25).sum())
        a = np.where(valid, np.maximum(a, 0.0), 0.0)
        c = np.where(valid, np.maximum(c, 0.0), 0.0)

        lat_n = y0 + dy * np.arange(r0, r0 + n)          # row north edges (dy < 0)
        area_km2 = (R_AUTHALIC_M ** 2 * dlon * np.abs(np.sin(np.radians(lat_n)) -
                    np.sin(np.radians(lat_n + dy)))) / 1e6  # per row
        A = area_km2[:, None]
        valid_area += float((valid * A).sum())

        for t in THRESHOLDS:
            l15, l25 = (a > t) & valid, (c > t) & valid
            s = acc[t]
            s["rad15"] += float((np.where(l15, a, 0) * A).sum())
            s["rad25"] += float((np.where(l25, c, 0) * A).sum())
            s["area15"] += float((l15 * A).sum()); s["area25"] += float((l25 * A).sum())
            s["area_new"] += float(((~l15 & l25) * A).sum())
            s["area_lost"] += float(((l15 & ~l25) * A).sum())
            s["area_both"] += float(((l15 & l25) * A).sum())
            edge = np.r_[0, W - 1]
            s["rad15_edgecols"] += float((np.where(l15[:, edge], a[:, edge], 0) * A).sum())
            s["rad25_edgecols"] += float((np.where(l25[:, edge], c[:, edge], 0) * A).sum())
            k = cnt[t]
            k["lit15"] += int(l15.sum()); k["lit25"] += int(l25.sum())
            k["new"] += int((~l15 & l25).sum()); k["lost"] += int((l15 & ~l25).sum())
        if r0 % (ROWS * 8) == 0:
            print(f"row {r0}/{H}  {time.time() - t_start:.0f}s", flush=True)

    pct = lambda new, old: 100.0 * (new / old - 1.0)
    results = []
    for t in THRESHOLDS:
        s = acc[t]
        results.append({
            "lit_definition": f"radiance > {t} nW/cm2/sr",
            "is_main_result": t == 0.0,
            "radiance_change_pct": pct(s["rad25"], s["rad15"]),
            "lit_area_change_pct": pct(s["area25"], s["area15"]),
            "newly_lit_area_pct_of_2015_lit": 100.0 * s["area_new"] / s["area15"],
            "lit_to_unlit_area_pct_of_2015_lit": 100.0 * s["area_lost"] / s["area15"],
            "total_radiance_x_area": {"2015": s["rad15"], "2025": s["rad25"]},
            "lit_area_km2": {"2015": s["area15"], "2025": s["area25"], "newly_lit": s["area_new"],
                             "lit_to_unlit": s["area_lost"], "lit_both": s["area_both"]},
            "edge_columns_share_of_radiance_pct": {
                "2015": 100.0 * s["rad15_edgecols"] / s["rad15"],
                "2025": 100.0 * s["rad25_edgecols"] / s["rad25"]},
            "pixel_counts_unweighted": cnt[t],
        })

    out = {
        "label": "inferred",
        "rule": __doc__.split("Definitions", 1)[1].strip(),
        "inputs": {str(y): {"cog": str(cog_path(y).relative_to(FINAL)), "raw_file": RAW[y][0],
                            "raw_sha256": RAW[y][1]} for y in (2015, 2025)},
        "source": "EOG Annual VNL V2 (VIIRS DNB, S-NPP), average_masked; 2015 = v2.1, 2025 = v2.2. "
                  "Elvidge et al. 2021, doi:10.3390/rs13050922",
        "script": "pipeline/story/01_radiance_change.py",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sphere_radius_m": R_AUTHALIC_M,
        "grid": {"width": W, "height": H, "geotransform": gt},
        "checks": {
            "positive_pixels_without_exclusion": raw_pos,
            "pixels_excluded_pairwise": excl,
            "other_negatives_set_to_zero": neg_set_zero,
            "valid_area_km2": valid_area,
        },
        "results": results,
        "caveats": [
            "VIIRS DNB under-detects light below ~500 nm (blue part of white LEDs); "
            "a switch to LEDs can read as a decrease (Kyba et al. 2023, doi:10.1126/science.abq7781).",
            "2015 (v2.1) and 2025 (v2.2) were processed with different EOG versions, incl. the "
            "background mask that decides which pixels are > 0.",
            "Not yet audited (RULES section 3).",
        ],
        "runtime_s": round(time.time() - t_start, 1),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps({r["lit_definition"]: {k: round(r[k], 2) for k in (
        "radiance_change_pct", "lit_area_change_pct", "newly_lit_area_pct_of_2015_lit",
        "lit_to_unlit_area_pct_of_2015_lit")} for r in results}, indent=2))
    print(json.dumps(out["checks"], indent=2))


if __name__ == "__main__":
    main()
