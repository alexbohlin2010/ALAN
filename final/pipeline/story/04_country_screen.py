"""Screen all countries: 2015 -> 2025 radiance change and how much it depends on the EOG version mask.

Run from final/:  .venv/bin/python pipeline/story/04_country_screen.py
Output: data/derived/story/country_screen_2015_2025.csv (+ .json with the rule)  (label: inferred;
screening aid for choosing a case-study country, AI_LOG "Story, step 40"; not a story figure)

Same inputs and base rules as 01-03 (average_masked COGs, read-only; pairwise -1.5 exclusion; other
negatives -> 0; sphere pixel area). Countries: Natural Earth 1:10m admin_0_countries (read in place),
pixel belongs to a country if its centre is inside (GDAL rasterize, ALL_TOUCHED = FALSE).
Variants (as in 03_version_sensitivity.py):
- a  lit = > 0 in each year (the story rule)
- b  only pixels > 0 in both years
- c2 / c3  lit = > 2 / > 3 nW/cm2/sr in both years (above every cell floor seen in 03)
- d  per-1-degree local floor (max of the two years' smallest positive value in the cell)
Columns per variant: radiance_change_pct. Plus, for a and c3: lit_area_change_pct and
new_share_pct = share of 2025 radiance x area in pixels not lit in 2015 under that variant.
same_sign_all_variants = the radiance change has the same sign under a, b, c2, c3 and d.
Units: radiance nW/cm2/sr, area km2.
"""
import csv
import importlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr, osr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "radiance"))
sys.path.insert(0, str(HERE))
from config import FINAL, RAW, cog_path  # noqa: E402
v03 = importlib.import_module("03_version_sensitivity")

gdal.UseExceptions(); ogr.UseExceptions()
NE = FINAL / "data/raw/boundaries/naturalearth/ne_10m_admin_0_countries.zip"
OUT_CSV = FINAL / "data/derived/story/country_screen_2015_2025.csv"
OUT_JSON = OUT_CSV.with_suffix(".json")
CELL = v03.CELL
VARIANTS = ("a", "b", "c2", "c3", "d")
SUMS = ("rad15", "rad25", "area15", "area25", "rad25_in_new")


def country_layer():
    """In-memory layer with an integer id per country (1..n); returns (layer, datasource, names)."""
    src = ogr.Open(f"/vsizip/{NE}/ne_10m_admin_0_countries.shp")
    sl = src.GetLayer()
    srs = osr.SpatialReference(); srs.ImportFromEPSG(4326)
    vds = ogr.GetDriverByName("MEM").CreateDataSource("")
    vl = vds.CreateLayer("c", srs, ogr.wkbMultiPolygon)
    vl.CreateField(ogr.FieldDefn("cid", ogr.OFTInteger))
    names = [None]
    for f in sl:
        names.append((f.GetField("ADMIN"), f.GetField("ADM0_A3")))
        g = ogr.Feature(vl.GetLayerDefn()); g.SetField("cid", len(names) - 1)
        g.SetGeometry(f.GetGeometryRef().Clone()); vl.CreateFeature(g)
    return vl, vds, src, names


def main():
    t0 = time.time()
    ds = {y: gdal.Open(str(cog_path(y))) for y in (2015, 2025)}
    b = {y: ds[y].GetRasterBand(1) for y in ds}
    W, H, gt = ds[2015].RasterXSize, ds[2015].RasterYSize, ds[2015].GetGeoTransform()
    assert (W, H, gt) == (ds[2025].RasterXSize, ds[2025].RasterYSize, ds[2025].GetGeoTransform())
    x0, dx, _, y0, _, dy = gt
    vl, _vds, _src, names = country_layer()
    n = len(names)
    srs = osr.SpatialReference(); srs.ImportFromEPSG(4326)

    fl = {y: v03.cell_floors(b[y], W, H) for y in (2015, 2025)}
    print(f"cell floors done {time.time() - t0:.0f}s", flush=True)

    acc = {v: {s: np.zeros(n) for s in SUMS} for v in VARIANTS}
    area_inside = np.zeros(n)
    for r0 in range(0, H, CELL):
        h = min(CELL, H - r0)
        mem = gdal.GetDriverByName("MEM").Create("", W, h, 1, gdal.GDT_UInt16)
        mem.SetGeoTransform((x0, dx, 0, y0 + r0 * dy, 0, dy)); mem.SetProjection(srs.ExportToWkt())
        gdal.RasterizeLayer(mem, [1], vl, options=["ATTRIBUTE=cid", "ALL_TOUCHED=FALSE"])
        cid = mem.ReadAsArray()
        A = np.broadcast_to(v03.row_area(y0, dy, dx, r0, h), (h, W))
        inside = cid > 0
        area_inside += np.bincount(cid[inside], weights=A[inside], minlength=n)
        a, c, valid = v03.clean(b[2015].ReadAsArray(0, r0, W, h).astype(np.float64),
                                b[2025].ReadAsArray(0, r0, W, h).astype(np.float64))
        keep = inside & valid & ((a > 0) | (c > 0))      # only pixels lit in at least one year matter
        if not keep.any():
            continue
        rr, cc = np.nonzero(keep)
        av, cv, Av, idv = a[keep], c[keep], A[keep], cid[keep]
        pf = np.maximum(*(np.where(np.isinf(fl[y]), 0, fl[y])[(rr + r0) // CELL, cc // CELL] for y in (2015, 2025)))
        p15, p25 = av > 0, cv > 0
        lits = {"a": (p15, p25), "b": (p15 & p25, p15 & p25),
                "c2": (av > 2, cv > 2), "c3": (av > 3, cv > 3), "d": (p15 & (av >= pf), p25 & (cv >= pf))}
        for v, (l15, l25) in lits.items():
            s = acc[v]
            s["rad15"] += np.bincount(idv, weights=np.where(l15, av, 0) * Av, minlength=n)
            s["rad25"] += np.bincount(idv, weights=np.where(l25, cv, 0) * Av, minlength=n)
            s["area15"] += np.bincount(idv, weights=l15 * Av, minlength=n)
            s["area25"] += np.bincount(idv, weights=l25 * Av, minlength=n)
            s["rad25_in_new"] += np.bincount(idv, weights=np.where(~l15 & l25, cv, 0) * Av, minlength=n)
        if r0 % (CELL * 20) == 0:
            print(f"row {r0}/{H}  {time.time() - t0:.0f}s", flush=True)

    def pct(new, old):
        return round(100.0 * (new / old - 1.0), 2) if old > 0 else None

    rows = []
    for i in range(1, n):
        r = {"country": names[i][0], "adm0_a3": names[i][1], "area_km2": round(area_inside[i], 1),
             "radiance_x_area_2015": round(acc["a"]["rad15"][i], 1), "radiance_x_area_2025": round(acc["a"]["rad25"][i], 1)}
        for v in VARIANTS:
            r[f"radiance_change_pct_{v}"] = pct(acc[v]["rad25"][i], acc[v]["rad15"][i])
        for v in ("a", "c3"):
            r[f"lit_area_change_pct_{v}"] = pct(acc[v]["area25"][i], acc[v]["area15"][i])
            r[f"new_share_pct_{v}"] = (round(100.0 * acc[v]["rad25_in_new"][i] / acc[v]["rad25"][i], 2)
                                       if acc[v]["rad25"][i] > 0 else None)
        ch = [r[f"radiance_change_pct_{v}"] for v in VARIANTS]
        r["same_sign_all_variants"] = (None if any(x is None for x in ch)
                                       else all(x > 0 for x in ch) or all(x < 0 for x in ch))
        rows.append(r)
    rows.sort(key=lambda r: -r["radiance_x_area_2025"])
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    OUT_JSON.write_text(json.dumps({
        "label": "inferred", "purpose": "screening aid; not a story figure",
        "rule": __doc__.split("Same inputs", 1)[1].strip(),
        "inputs": {str(y): {"cog": str(cog_path(y).relative_to(FINAL)), "raw_file": RAW[y][0],
                            "raw_sha256": RAW[y][1]} for y in (2015, 2025)},
        "boundaries": "data/raw/boundaries/MANIFEST.csv (Natural Earth 1:10m v5.1.1, admin_0_countries)",
        "script": "pipeline/story/04_country_screen.py", "csv": str(OUT_CSV.relative_to(FINAL)),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "countries": len(rows), "caveats": ["Not audited (RULES section 3)."],
        "runtime_s": round(time.time() - t0, 1)}, indent=2))
    print(f"{len(rows)} countries, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
