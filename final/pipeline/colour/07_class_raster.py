"""Write the estimated lamp-colour class raster on the radiance grid (separate from tiles).

Grid: identical to the radiance COGs (EPSG:4326, 15 arc-sec, same origin and size).
Band 1 = 2015 epoch, band 2 = 2025 epoch; Byte; 0 = no estimate, 1 = mostly sodium,
2 = mixed, 3 = mostly LED (config.CLASSES). A pixel gets its city's class when its
radiance in that year's COG is > 0 (not -1.5) and its centre lies within CITY_RADIUS_KM
(haversine, EARTH_RADIUS_KM) of the city's reference point. All other pixels are 0.
Values are `estimated` (see pipeline/colour/METHOD.md); the sidecar JSON records sources.
Run from final/:  .venv/bin/python pipeline/colour/07_class_raster.py
"""
import csv, json, math, sys
import numpy as np
from osgeo import gdal
from config import *

sys.path.insert(0, str(FINAL / "pipeline/radiance"))
import importlib.util
spec = importlib.util.spec_from_file_location("rad_config", FINAL / "pipeline/radiance/config.py")
rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
EPOCH_BANDS = {2015: 1, 2025: 2}

def main():
    classes = list(csv.DictReader(open(DERIVED / f"{PILOT}_city_classes.csv")))
    ref = rc.cog_path(2015)
    src = gdal.Open(str(ref)); W, H, gt = src.RasterXSize, src.RasterYSize, src.GetGeoTransform()
    CLASS_RASTER.parent.mkdir(parents=True, exist_ok=True)
    tmp = CLASS_RASTER.with_suffix(".tmp.tif")
    ds = gdal.GetDriverByName("GTiff").Create(str(tmp), W, H, 2, gdal.GDT_Byte,
                                              ["TILED=YES", "COMPRESS=DEFLATE", "SPARSE_OK=TRUE"])
    ds.SetGeoTransform(gt); ds.SetProjection(src.GetProjection())
    for b in (1, 2): ds.GetRasterBand(b).Fill(0)
    rad = {y: gdal.Open(str(rc.cog_path(y))) for y in EPOCH_BANDS}
    counts = []
    for r in classes:
        y, code = int(r["epoch"]), int(r["class_code"])
        lat0, lon0 = TEST_CITIES[r["city"]]
        dlat = math.degrees(CITY_RADIUS_KM / EARTH_RADIUS_KM)
        dlon = dlat / math.cos(math.radians(lat0))
        c0 = max(0, int((lon0 - dlon - gt[0]) / gt[1]) - 1); c1 = min(W, int((lon0 + dlon - gt[0]) / gt[1]) + 2)
        r0 = max(0, int((gt[3] - (lat0 + dlat)) / -gt[5]) - 1); r1 = min(H, int((gt[3] - (lat0 - dlat)) / -gt[5]) + 2)
        lon = gt[0] + (np.arange(c0, c1) + 0.5) * gt[1]
        lat = gt[3] + (np.arange(r0, r1) + 0.5) * gt[5]
        LON, LAT = np.meshgrid(np.radians(lon), np.radians(lat))
        p0, l0 = math.radians(lat0), math.radians(lon0)
        hav = np.sin((LAT - p0) / 2) ** 2 + math.cos(p0) * np.cos(LAT) * np.sin((LON - l0) / 2) ** 2
        inside = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(hav)) <= CITY_RADIUS_KM
        v = rad[y].GetRasterBand(1).ReadAsArray(c0, r0, c1 - c0, r1 - r0)
        lit = inside & (v > 0)
        band = ds.GetRasterBand(EPOCH_BANDS[y])
        cur = band.ReadAsArray(c0, r0, c1 - c0, r1 - r0)
        if (cur[lit] != 0).any(): raise SystemExit(f"overlap at {r['city']} {y}")
        cur[lit] = code
        band.WriteArray(cur, c0, r0)
        counts.append(dict(city=r["city"], epoch=y, class_code=code, pixels=int(lit.sum()),
                           pixels_in_circle=int(inside.sum())))
        print(counts[-1])
    ds.FlushCache(); ds = None
    gdal.Translate(str(CLASS_RASTER), str(tmp), format="COG", creationOptions=["COMPRESS=DEFLATE"])
    tmp.unlink()
    meta = dict(file=CLASS_RASTER.name, bands={"1": "2015 epoch (photos 2012-2015)", "2": "2025 epoch (photos 2021+)"},
                codes=CLASSES, label="estimated", requested_by="human (Alexander), 2026-10-03",
                method="pipeline/colour/METHOD.md", grid=f"same as {ref.name}", crs="EPSG:4326",
                rule=f"lit (radiance > 0 that year) and within {CITY_RADIUS_KM} km of the city reference point",
                city_reference_points=TEST_CITIES, city_classes=str((DERIVED / f'{PILOT}_city_classes.csv').relative_to(FINAL)),
                counts=counts)
    CLASS_RASTER.with_suffix(".json").write_text(json.dumps(meta, indent=1))
    print("wrote", CLASS_RASTER.relative_to(FINAL))

if __name__ == "__main__":
    main()
