"""Change in VIIRS radiance and lit area, 2015 -> 2025, for the case-study countries.

Run from final/:  .venv/bin/python pipeline/story/02_country_change.py
Output: data/derived/story/country_change_2015_2025.json  (label: inferred)

Same definitions as 01_radiance_change.py (M1, L1 lit = > 0 plus sensitivity > 0.5 and > 1,
newly lit, sphere pixel area, pairwise -1.5 exclusion, other negatives -> 0), applied
inside country boundaries.

Boundaries (human decisions, AI_LOG "Story UX task", steps 13-14): Natural Earth 1:10m v5.1.1,
read in place from data/raw/boundaries/naturalearth/*.zip (read-only).
- India: admin_0_countries ADMIN = 'India' (Natural Earth default line in Kashmir).
- Ukraine: admin_0_countries ADMIN = 'Ukraine'. Crimea excluded (in this layer Crimea is
  already outside Ukraine; checked below). Areas outside government control since 2014
  (Donetsk/Luhansk) included.
- France: mainland = admin_0_map_units GEOUNIT 'France' (metropolitan). Reported with and
  without Corsica (the human has not chosen); Corsica = polygon parts whose extent lies
  within 8.4..9.7 E, 41.3..43.1 N.
- Iceland: admin_0_countries ADMIN = 'Iceland' (human request, AI_LOG Impacts/Story step 36:
  Iceland to replace France in the story; France is still computed).
- Cote d'Ivoire: admin_0_countries ADMIN = 'Ivory Coast' (human request, AI_LOG Story step 41:
  Cote d'Ivoire replaces France in the story; the other areas are still computed).
- Pixel rule: a pixel belongs to a country if its centre lies inside the polygon
  (GDAL rasterize, ALL_TOUCHED = FALSE).
"""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from osgeo import gdal, ogr, osr

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "radiance"))
from config import FINAL, RAW, NO_COVERAGE, cog_path  # noqa: E402

gdal.UseExceptions(); ogr.UseExceptions()
NE = FINAL / "data/raw/boundaries/naturalearth"
OUT = FINAL / "data/derived/story/country_change_2015_2025.json"
R_AUTHALIC_M = 6371007.1809
THRESHOLDS = (0.0, 0.5, 1.0)
CORSICA_BOX = (8.4, 9.7, 41.3, 43.1)  # lon min, lon max, lat min, lat max


def layer_geom(name, field, value):
    ds = ogr.Open(f"/vsizip/{NE}/{name}.zip/{name}.shp")
    lyr = ds.GetLayer()
    lyr.SetAttributeFilter(f"{field} = '{value}'")
    feats = list(lyr)
    assert len(feats) == 1, (name, value, len(feats))
    return feats[0].GetGeometryRef().Clone()


def without_corsica(geom):
    out = ogr.Geometry(ogr.wkbMultiPolygon)
    dropped = 0
    for i in range(geom.GetGeometryCount()):
        part = geom.GetGeometryRef(i)
        x0, x1, y0, y1 = part.GetEnvelope()
        if x0 >= CORSICA_BOX[0] and x1 <= CORSICA_BOX[1] and y0 >= CORSICA_BOX[2] and y1 <= CORSICA_BOX[3]:
            dropped += 1
            continue
        out.AddGeometry(part.Clone())
    assert dropped >= 1
    return out, dropped


def stats(geom, ds, gt, W, H):
    x0, dx, _, y0, _, dy = gt
    gx0, gx1, gy0, gy1 = geom.GetEnvelope()
    c0 = max(0, int(np.floor((gx0 - x0) / dx))); c1 = min(W, int(np.ceil((gx1 - x0) / dx)) + 1)
    r0 = max(0, int(np.floor((gy1 - y0) / dy))); r1 = min(H, int(np.ceil((gy0 - y0) / dy)) + 1)
    w, h = c1 - c0, r1 - r0
    # Country mask on the raster's own grid (pixel centre rule).
    mem = gdal.GetDriverByName("MEM").Create("", w, h, 1, gdal.GDT_Byte)
    mem.SetGeoTransform((x0 + c0 * dx, dx, 0, y0 + r0 * dy, 0, dy))
    srs = osr.SpatialReference(); srs.ImportFromEPSG(4326); mem.SetProjection(srs.ExportToWkt())
    vds = ogr.GetDriverByName("MEM").CreateDataSource("")
    vl = vds.CreateLayer("c", srs, ogr.wkbMultiPolygon)
    f = ogr.Feature(vl.GetLayerDefn()); f.SetGeometry(geom); vl.CreateFeature(f)
    gdal.RasterizeLayer(mem, [1], vl, burn_values=[1], options=["ALL_TOUCHED=FALSE"])
    inside = mem.ReadAsArray().astype(bool)

    a = ds[2015].GetRasterBand(1).ReadAsArray(c0, r0, w, h).astype(np.float64)
    c = ds[2025].GetRasterBand(1).ReadAsArray(c0, r0, w, h).astype(np.float64)
    nd15, nd25 = (a == NO_COVERAGE) & inside, (c == NO_COVERAGE) & inside
    valid = inside & ~((a == NO_COVERAGE) | (c == NO_COVERAGE))
    a = np.where(valid, np.maximum(a, 0.0), 0.0)
    c = np.where(valid, np.maximum(c, 0.0), 0.0)
    lat_n = y0 + dy * np.arange(r0, r1)
    A = ((R_AUTHALIC_M ** 2 * np.radians(dx) *
          np.abs(np.sin(np.radians(lat_n)) - np.sin(np.radians(lat_n + dy)))) / 1e6)[:, None]

    pct = lambda new, old: 100.0 * (new / old - 1.0)
    res = []
    for t in THRESHOLDS:
        l15, l25 = (a > t) & valid, (c > t) & valid
        rad15, rad25 = float((np.where(l15, a, 0) * A).sum()), float((np.where(l25, c, 0) * A).sum())
        ar15, ar25 = float((l15 * A).sum()), float((l25 * A).sum())
        new, lost = float(((~l15 & l25) * A).sum()), float(((l15 & ~l25) * A).sum())
        res.append({
            "lit_definition": f"radiance > {t} nW/cm2/sr", "is_main_result": t == 0.0,
            "radiance_change_pct": pct(rad25, rad15), "lit_area_change_pct": pct(ar25, ar15),
            "newly_lit_area_pct_of_2015_lit": 100.0 * new / ar15,
            "lit_to_unlit_area_pct_of_2015_lit": 100.0 * lost / ar15,
            "total_radiance_x_area": {"2015": rad15, "2025": rad25},
            "lit_area_km2": {"2015": ar15, "2025": ar25, "newly_lit": new, "lit_to_unlit": lost},
        })
    return {
        "window": {"col0": c0, "row0": r0, "width": w, "height": h},
        "pixels_inside": int(inside.sum()),
        "area_inside_km2": float((inside * A).sum()),
        "pixels_excluded_pairwise": int((inside & ~valid).sum()),
        "nodata_pixels": {"2015": int(nd15.sum()), "2025": int(nd25.sum())},
        "results": res,
    }


def main():
    t0 = time.time()
    ds = {y: gdal.Open(str(cog_path(y))) for y in (2015, 2025)}
    W, H, gt = ds[2015].RasterXSize, ds[2015].RasterYSize, ds[2015].GetGeoTransform()
    assert (W, H, gt) == (ds[2025].RasterXSize, ds[2025].RasterYSize, ds[2025].GetGeoTransform())

    india = layer_geom("ne_10m_admin_0_countries", "ADMIN", "India")
    ukraine = layer_geom("ne_10m_admin_0_countries", "ADMIN", "Ukraine")
    iceland = layer_geom("ne_10m_admin_0_countries", "ADMIN", "Iceland")
    ivory = layer_geom("ne_10m_admin_0_countries", "ADMIN", "Ivory Coast")
    france = layer_geom("ne_10m_admin_0_map_units", "GEOUNIT", "France")
    france_nc, n_dropped = without_corsica(france)
    crimea = layer_geom("ne_10m_admin_0_disputed_areas", "BRK_NAME", "Crimea")
    crimea_overlap = ukraine.Intersection(crimea).GetArea()  # square degrees
    crimea_area = crimea.GetArea()

    areas = {
        "India": stats(india, ds, gt, W, H),
        "France (mainland incl. Corsica)": stats(france, ds, gt, W, H),
        "France (mainland excl. Corsica)": stats(france_nc, ds, gt, W, H),
        "Ukraine (excl. Crimea)": stats(ukraine, ds, gt, W, H),
        "Iceland": stats(iceland, ds, gt, W, H),
        "Cote d'Ivoire": stats(ivory, ds, gt, W, H),
    }
    out = {
        "label": "inferred",
        "rule": __doc__.split("Same definitions", 1)[1].strip(),
        "inputs": {
            **{str(y): {"cog": str(cog_path(y).relative_to(FINAL)), "raw_file": RAW[y][0],
                        "raw_sha256": RAW[y][1]} for y in (2015, 2025)},
            "boundaries": "data/raw/boundaries/MANIFEST.csv (Natural Earth 1:10m v5.1.1)",
        },
        "script": "pipeline/story/02_country_change.py",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "checks": {
            "crimea_overlap_with_ukraine_sq_deg": crimea_overlap,
            "crimea_area_sq_deg": crimea_area,
            "corsica_polygons_dropped": n_dropped,
        },
        "areas": areas,
        "caveats": [
            "VIIRS DNB under-detects light below ~500 nm (white LEDs); an LED switch can read as a "
            "decrease (Kyba et al. 2023, doi:10.1126/science.abq7781).",
            "2015 (v2.1) and 2025 (v2.2) were processed with different EOG versions.",
            "Not yet audited (RULES section 3).",
        ],
        "runtime_s": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2))
    for name, s in areas.items():
        print(name, f"{s['area_inside_km2']:,.0f} km2, excl {s['pixels_excluded_pairwise']}")
        for r in s["results"]:
            print(f"   {r['lit_definition']:<26} radiance {r['radiance_change_pct']:+7.2f}%  "
                  f"lit area {r['lit_area_change_pct']:+7.2f}%  new {r['newly_lit_area_pct_of_2015_lit']:6.2f}%  "
                  f"lost {r['lit_to_unlit_area_pct_of_2015_lit']:6.2f}%")
    print(json.dumps(out["checks"]), out["runtime_s"], "s")


if __name__ == "__main__":
    main()
