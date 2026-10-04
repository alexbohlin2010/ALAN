"""Sensitivity of the story figures to the EOG product-version difference (2015 v2.1 vs 2025 v2.2).

Run from final/:  .venv/bin/python pipeline/story/03_version_sensitivity.py
Output: data/derived/story/version_sensitivity_2015_2025.json  (label: inferred; diagnostic only,
it does not replace radiance_change_2015_2025.json or country_change_2015_2025.json)

Requested by the human (AI_LOG "Story, step 38"): compare the current results with variants that
remove pixels only one product version keeps. Inputs and base rules are the same as 01/02
(average_masked COGs, read-only; pairwise -1.5 exclusion; other negatives -> 0; sphere pixel area;
country = pixel centre inside the Natural Earth polygon, via 02's layer_geom).

Variants (lit15 / lit25 = which pixels count in each year; radiance = sum of value x area over them):
- a_current:       lit = > 0 in each year (the published story rule, L1).
- b_lit_both:      only pixels > 0 in BOTH years, in both years (no newly lit, no lit -> unlit).
- c_floor_F:       lit = > F in both years, F = 0.653 (smallest positive 2015 value over Iceland,
                   AI_LOG step 37), 1, 2, 3 nW/cm2/sr.
- d_local_floor:   per 1 x 1 degree cell (240 x 240 pixels, cells counted from the raster's
                   top-left corner) the smallest positive value is found in each year
                   ("cell floor": the faintest value that version kept there). Both years then
                   count only pixels >= max(floor 2015, floor 2025) of that cell. If a year has no
                   positive pixel in a cell, only the other year's floor is used.
Also per variant: share of 2025 radiance x area in pixels not lit in 2015 under that variant.
Units: radiance nW/cm2/sr, area km2, radiance x area = nW/cm2/sr * km2.
"""
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
from config import FINAL, RAW, NO_COVERAGE, cog_path  # noqa: E402
layer_geom = importlib.import_module("02_country_change").layer_geom

gdal.UseExceptions(); ogr.UseExceptions()
OUT = FINAL / "data/derived/story/version_sensitivity_2015_2025.json"
R_AUTHALIC_M = 6371007.1809
CELL = 240
FLOORS = (0.653, 1.0, 2.0, 3.0)
KEYS = ("rad15", "rad25", "area15", "area25", "area_new", "area_lost", "rad25_in_new")


def variants(a, c, valid, fl):
    """Yield (name, lit15, lit25). a, c: values with invalid/negative already 0; fl: per-pixel local floor."""
    p15, p25 = (a > 0) & valid, (c > 0) & valid
    yield "a_current", p15, p25
    both = p15 & p25
    yield "b_lit_both", both, both
    for F in FLOORS:
        yield f"c_floor_{F:g}", (a > F) & valid, (c > F) & valid
    yield "d_local_floor", p15 & (a >= fl), p25 & (c >= fl)


def add(acc, name, a, c, A, l15, l25):
    s = acc.setdefault(name, dict.fromkeys(KEYS, 0.0))
    new = ~l15 & l25
    s["rad15"] += float((np.where(l15, a, 0) * A).sum())
    s["rad25"] += float((np.where(l25, c, 0) * A).sum())
    s["area15"] += float((l15 * A).sum()); s["area25"] += float((l25 * A).sum())
    s["area_new"] += float((new * A).sum()); s["area_lost"] += float(((l15 & ~l25) * A).sum())
    s["rad25_in_new"] += float((np.where(new, c, 0) * A).sum())


def summarise(acc):
    pct = lambda new, old: 100.0 * (new / old - 1.0) if old else None
    return {name: {
        "radiance_change_pct": pct(s["rad25"], s["rad15"]),
        "lit_area_change_pct": pct(s["area25"], s["area15"]),
        "share_of_2025_radiance_in_pixels_not_lit_2015_pct": 100.0 * s["rad25_in_new"] / s["rad25"] if s["rad25"] else None,
        **{k: s[k] for k in KEYS},
    } for name, s in acc.items()}


def clean(a, c):
    valid = ~((a == NO_COVERAGE) | (c == NO_COVERAGE))
    return np.where(valid, np.maximum(a, 0.0), 0.0), np.where(valid, np.maximum(c, 0.0), 0.0), valid


def row_area(y0, dy, dx, r0, n):
    lat_n = y0 + dy * np.arange(r0, r0 + n)
    return ((R_AUTHALIC_M ** 2 * np.radians(dx) *
             np.abs(np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_n + dy)))) / 1e6)[:, None]


def cell_floors(b, W, H):
    """Per 1-degree cell: smallest positive value (inf if none). Pass 1."""
    nc = -(-W // CELL)
    out = np.full((-(-H // CELL), nc), np.inf)
    for i, r0 in enumerate(range(0, H, CELL)):
        n = min(CELL, H - r0)
        a = b.ReadAsArray(0, r0, W, n)
        a = np.where(a > 0, a, np.inf)
        pad = np.full((n, nc * CELL), np.inf, dtype=a.dtype); pad[:, :W] = a
        out[i] = pad.reshape(n, nc, CELL).min(axis=(0, 2))
    return out


def pixel_floor(fl15, fl25, r0, n, c0, w):
    """Local floor per pixel for a window: max of the two years' cell floors (ignoring inf)."""
    f15, f25 = np.where(np.isinf(fl15), 0, fl15), np.where(np.isinf(fl25), 0, fl25)
    cf = np.maximum(f15, f25)
    rows = np.arange(r0, r0 + n) // CELL; cols = np.arange(c0, c0 + w) // CELL
    return cf[rows[:, None], cols[None, :]]


def country_mask(geom, gt, W, H):
    x0, dx, _, y0, _, dy = gt
    gx0, gx1, gy0, gy1 = geom.GetEnvelope()
    c0 = max(0, int(np.floor((gx0 - x0) / dx))); c1 = min(W, int(np.ceil((gx1 - x0) / dx)) + 1)
    r0 = max(0, int(np.floor((gy1 - y0) / dy))); r1 = min(H, int(np.ceil((gy0 - y0) / dy)) + 1)
    w, h = c1 - c0, r1 - r0
    mem = gdal.GetDriverByName("MEM").Create("", w, h, 1, gdal.GDT_Byte)
    mem.SetGeoTransform((x0 + c0 * dx, dx, 0, y0 + r0 * dy, 0, dy))
    srs = osr.SpatialReference(); srs.ImportFromEPSG(4326); mem.SetProjection(srs.ExportToWkt())
    vds = ogr.GetDriverByName("MEM").CreateDataSource("")
    vl = vds.CreateLayer("c", srs, ogr.wkbMultiPolygon)
    f = ogr.Feature(vl.GetLayerDefn()); f.SetGeometry(geom); vl.CreateFeature(f)
    gdal.RasterizeLayer(mem, [1], vl, burn_values=[1], options=["ALL_TOUCHED=FALSE"])
    return c0, r0, w, h, mem.ReadAsArray().astype(bool)


def main():
    t0 = time.time()
    ds = {y: gdal.Open(str(cog_path(y))) for y in (2015, 2025)}
    b = {y: ds[y].GetRasterBand(1) for y in ds}
    W, H, gt = ds[2015].RasterXSize, ds[2015].RasterYSize, ds[2015].GetGeoTransform()
    assert (W, H, gt) == (ds[2025].RasterXSize, ds[2025].RasterYSize, ds[2025].GetGeoTransform())
    x0, dx, _, y0, _, dy = gt

    fl = {y: cell_floors(b[y], W, H) for y in (2015, 2025)}
    print(f"cell floors done {time.time() - t0:.0f}s", flush=True)

    # Global (pass 2)
    acc = {}
    for r0 in range(0, H, CELL):
        n = min(CELL, H - r0)
        a, c, valid = clean(b[2015].ReadAsArray(0, r0, W, n).astype(np.float64),
                            b[2025].ReadAsArray(0, r0, W, n).astype(np.float64))
        A = row_area(y0, dy, dx, r0, n)
        pf = pixel_floor(fl[2015], fl[2025], r0, n, 0, W)
        for name, l15, l25 in variants(a, c, valid, pf):
            add(acc, name, a, c, A, l15, l25)
    areas = {"Global": summarise(acc)}
    print(f"global done {time.time() - t0:.0f}s", flush=True)

    for label, layer, field, value in (
            ("India", "ne_10m_admin_0_countries", "ADMIN", "India"),
            ("Ukraine (excl. Crimea)", "ne_10m_admin_0_countries", "ADMIN", "Ukraine"),
            ("Iceland", "ne_10m_admin_0_countries", "ADMIN", "Iceland"),
            # Added AI_LOG step 39 (France back in the story): same geometry as 02's story figure.
            ("France (mainland incl. Corsica)", "ne_10m_admin_0_map_units", "GEOUNIT", "France")):
        geom = layer_geom(layer, field, value)
        c0, r0, w, h, inside = country_mask(geom, gt, W, H)
        a, c, valid = clean(b[2015].ReadAsArray(c0, r0, w, h).astype(np.float64),
                            b[2025].ReadAsArray(c0, r0, w, h).astype(np.float64))
        valid &= inside
        A = row_area(y0, dy, dx, r0, h)
        pf = pixel_floor(fl[2015], fl[2025], r0, h, c0, w)
        acc = {}
        for name, l15, l25 in variants(a, c, valid, pf):
            add(acc, name, a, c, A, l15, l25)
        rows = np.arange(r0, r0 + h) // CELL; cols = np.arange(c0, c0 + w) // CELL
        f15 = fl[2015][rows[:, None], cols[None, :]][inside]
        f25 = fl[2025][rows[:, None], cols[None, :]][inside]
        areas[label] = summarise(acc)
        areas[label]["_cell_floor_median_over_country_pixels"] = {
            "2015": float(np.median(f15[np.isfinite(f15)])), "2025": float(np.median(f25[np.isfinite(f25)]))}

    finite = {y: fl[y][np.isfinite(fl[y])] for y in fl}
    lat_c = y0 + dy * (np.arange(fl[2015].shape[0]) * CELL + CELL / 2)
    by_lat = {}
    for hi in range(75, -65, -10):
        s = (lat_c <= hi) & (lat_c > hi - 10)
        by_lat[f"{hi - 10}..{hi}N"] = {str(y): (float(np.median(v[np.isfinite(v)])) if np.isfinite(v).any() else None)
                                       for y, v in ((y, fl[y][s]) for y in fl)}
    out = {
        "label": "inferred",
        "purpose": "diagnostic; does not replace the published story figures",
        "rule": __doc__.split("Variants", 1)[1].strip(),
        "inputs": {str(y): {"cog": str(cog_path(y).relative_to(FINAL)), "raw_file": RAW[y][0],
                            "raw_sha256": RAW[y][1]} for y in (2015, 2025)},
        "script": "pipeline/story/03_version_sensitivity.py",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cell_floor_summary": {
            "cells_with_positive": {str(y): int(finite[y].size) for y in fl},
            "median": {str(y): float(np.median(finite[y])) for y in fl},
            "median_by_latitude_band": by_lat,
        },
        "areas": areas,
        "caveats": ["Cell floor = minimum, so a single odd pixel can set it.",
                    "Not audited (RULES section 3)."],
        "runtime_s": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2))
    for name, res in areas.items():
        print(name)
        for v, r in res.items():
            if v.startswith("_"):
                print("   ", v, {k: round(x, 3) for k, x in r.items()}); continue
            print(f"   {v:<16} radiance {r['radiance_change_pct']:+8.1f}%  lit area {r['lit_area_change_pct']:+8.1f}%  "
                  f"2025 rad in not-lit-2015 {r['share_of_2025_radiance_in_pixels_not_lit_2015_pct']:5.1f}%")
    print(json.dumps(out["cell_floor_summary"], indent=1), out["runtime_s"], "s")


if __name__ == "__main__":
    main()
