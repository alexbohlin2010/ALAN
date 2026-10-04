"""Step 01: decompress each raw .tif.gz to a lossless Cloud-Optimized GeoTIFF.

Raw files are only read (via /vsigzip/), never written; PAM is disabled so no
.aux.xml lands next to them. Values are copied unchanged (Float32, lossless
DEFLATE). Afterwards the COG is re-read in full and its value counts are written
to <cog>.counts.json for comparison with the MANIFEST read-only check.

Usage (from final/):  .venv/bin/python pipeline/radiance/01_decompress_to_cog.py
"""
import hashlib, json, sys
import numpy as np
from osgeo import gdal
from config import RAW, RAW_DIR, COG_DIR, YEARS, NO_COVERAGE, cog_path

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def counts(path):
    ds = gdal.Open(str(path))
    b = ds.GetRasterBand(1)
    c = dict(zero=0, positive=0, gt200=0, gt1000=0, eq_minus_1_5=0, other_negative=0, nan=0)
    vmin, vmax, total = np.inf, -np.inf, 0.0
    step = 1024
    for y in range(0, ds.RasterYSize, step):
        a = b.ReadAsArray(0, y, ds.RasterXSize, min(step, ds.RasterYSize - y))
        c["nan"] += int(np.isnan(a).sum())
        c["zero"] += int((a == 0).sum())
        c["positive"] += int((a > 0).sum())
        c["gt200"] += int((a > 200).sum())
        c["gt1000"] += int((a > 1000).sum())
        c["eq_minus_1_5"] += int((a == NO_COVERAGE).sum())
        c["other_negative"] += int(((a < 0) & (a != NO_COVERAGE)).sum())
        vmin, vmax = min(vmin, float(np.nanmin(a))), max(vmax, float(np.nanmax(a)))
        total += float(a.sum(dtype=np.float64))
    n = ds.RasterXSize * ds.RasterYSize
    return dict(width=ds.RasterXSize, height=ds.RasterYSize, pixels=n,
                geotransform=ds.GetGeoTransform(), min=vmin, max=vmax, mean=total / n, **c)


def main():
    COG_DIR.mkdir(parents=True, exist_ok=True)
    years = [int(a) for a in sys.argv[1:]] or YEARS
    for year in years:
        name, expected = RAW[year]
        raw = RAW_DIR / name
        got = sha256(raw)
        if got != expected:
            raise SystemExit(f"{year}: SHA-256 mismatch {got} != {expected}")
        out = cog_path(year)
        print(f"{year}: hash ok, writing {out.name}", flush=True)
        gdal.Translate(str(out), f"/vsigzip/{raw}", format="COG",
                       creationOptions=["COMPRESS=DEFLATE", "PREDICTOR=YES", "BIGTIFF=YES",
                                        "NUM_THREADS=ALL_CPUS", "OVERVIEWS=NONE"])
        stats = dict(source=name, source_sha256=got, **counts(out))
        out.with_suffix(".counts.json").write_text(json.dumps(stats, indent=2))
        print(json.dumps(stats, indent=2), flush=True)
        if sha256(raw) != expected:
            raise SystemExit(f"{year}: raw file changed during run")


if __name__ == "__main__":
    main()
