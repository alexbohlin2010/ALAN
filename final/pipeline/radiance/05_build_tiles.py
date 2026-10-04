"""Step 05: build display tiles (native pyramid, both years in one tile).

Grid (human, 2026-10-03): the raster's own pixel grid (EPSG:4326, 15 arc-sec,
origin = top-left corner of the files). Deepest level LMAX is native (no
resampling). Level n has pixel size (2 ** (LMAX - n)) native pixels; level 0
fits the whole raster in one 256x256 tile.
Coarser levels: mean of linear radiance over each block of native pixels (B7),
excluding -1.5 (N2); other negatives count as 0.
Encoding (E1), lossless WebP, 256x256 RGB:
  R = grey 2015, G = grey 2025 (curve from step 04, same for both years)
  B = flags: 1 = 2015 no data (-1.5), 2 = 2025 no data, 4 = outside the raster
A tile is skipped if it has no grey > 0 and no no-data flag in either year
(i.e. measured 0 everywhere, or outside). Every written tile is read back and
compared with the array that was written.

Optional lamp-colour classes (human, 2026-10-03; tile version v2):
  --version vN --classes PATH  PATH = 2-band Byte class raster on the same grid
  (band 1 = 2015, band 2 = 2025; 0 no estimate, 1-3 classes; pipeline/colour/07_class_raster.py).
  B additionally carries the class: bits 3-4 = 2015 class, bits 5-6 = 2025 class.
  Coarser levels: per year, the class (0 included) with the largest sum of valid radiance
  in the block wins; ties go to the lower code. Without these options the output is v1, unchanged.

Usage (from final/):  .venv/bin/python pipeline/radiance/05_build_tiles.py [--version vN --classes PATH] [levels...]
Output: data/derived/radiance/tiles/<version>/{level}/{x}/{y}.webp and tiles.json
"""
import base64, json, math, sys, time
from pathlib import Path
import numpy as np
from osgeo import gdal
from config import (YEARS, NO_COVERAGE, cog_path, CURVE_PATH, TILE_SIZE, TILE_DIR,
                    TILE_VERSION, FLAG_NODATA_2015, FLAG_NODATA_2025, FLAG_OUTSIDE)

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")
gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
T = TILE_SIZE
NATIVE_ROWS_PER_READ = 2048
CLASS_SHIFT = {2015: 3, 2025: 5}  # class bits in B (v2)
N_CLASSES = 4


def grey(mean, valid, curve):
    """Apply the step-04 curve. Pixels with no valid data get 0 (flag carries them)."""
    edges, cdf, top = curve
    g = np.round(255 * np.interp(np.minimum(mean, top), edges, cdf))
    return np.where((mean > 0) & valid, g, 0).astype(np.uint8)


def block_stats(ds, r0, n_native_rows, f, out_w, cls_band=None):
    """Sum of valid radiance, valid count and in-raster count for f x f blocks.
    With cls_band: also the winning class per block (largest valid-radiance sum)."""
    W, H = ds.RasterXSize, ds.RasterYSize
    n_read = max(0, min(n_native_rows, H - r0))
    a = np.full((n_native_rows, out_w * f), np.nan, np.float32)
    if n_read:
        a[:n_read, :W] = ds.GetRasterBand(1).ReadAsArray(0, r0, W, n_read)
    inr = ~np.isnan(a)
    valid = inr & (a != NO_COVERAGE)
    v = np.where(valid, np.maximum(np.nan_to_num(a), 0), 0).astype(np.float64)
    shp = (n_native_rows // f, f, out_w, f)
    stats = (v.reshape(shp).sum((1, 3)), valid.reshape(shp).sum((1, 3)),
             inr.reshape(shp).sum((1, 3)))
    if cls_band is None:
        return stats
    c = np.zeros((n_native_rows, out_w * f), np.uint8)
    if n_read:
        c[:n_read, :W] = cls_band.ReadAsArray(0, r0, W, n_read)
    per = np.stack([np.where(c == k, v, 0).reshape(shp).sum((1, 3)) for k in range(N_CLASSES)])
    win = per.argmax(0).astype(np.uint8)
    return stats + (np.where(stats[0] > 0, win, 0).astype(np.uint8),)


def write_tile(path, rgb):
    path.parent.mkdir(parents=True, exist_ok=True)
    mem = gdal.GetDriverByName("MEM").Create("", T, T, 3, gdal.GDT_Byte)
    for i in range(3):
        mem.GetRasterBand(i + 1).WriteArray(rgb[i])
    gdal.GetDriverByName("WEBP").CreateCopy(str(path), mem, options=["LOSSLESS=YES"])
    back = gdal.Open(str(path)).ReadAsArray()
    if not np.array_equal(back, rgb):
        raise SystemExit(f"read-back mismatch: {path}")


def build_level(level, lmax, dss, curve, tile_dir=TILE_DIR, cls_ds=None):
    W, H = dss[YEARS[0]].RasterXSize, dss[YEARS[0]].RasterYSize
    f = 2 ** (lmax - level)
    out_w, out_h = math.ceil(W / f), math.ceil(H / f)
    cols, rows = math.ceil(out_w / T), math.ceil(out_h / T)
    exists = np.zeros((rows, cols), bool)
    chunk = max(1, min(T, NATIVE_ROWS_PER_READ // f))  # output rows per read
    for ty in range(rows):
        n_out = min(T, out_h - ty * T)
        g, nod, cls = {}, {}, {}
        for bi, y in enumerate(YEARS):
            cb = cls_ds.GetRasterBand(bi + 1) if cls_ds else None
            parts = [block_stats(dss[y], (ty * T + o) * f, min(chunk, n_out - o) * f, f, out_w, cb)
                     for o in range(0, n_out, chunk)]
            s, valid, inr = (np.vstack([p[i] for p in parts]) for i in range(3))
            if cls_ds:
                cls[y] = np.vstack([p[3] for p in parts])
            mean = np.where(valid > 0, s / np.maximum(valid, 1), 0)
            g[y] = grey(mean, valid > 0, curve)
            nod[y] = (valid == 0) & (inr > 0)
            outside = inr == 0
        flags = (nod[2015] * FLAG_NODATA_2015 + nod[2025] * FLAG_NODATA_2025
                 + outside * FLAG_OUTSIDE).astype(np.uint8)
        for y in cls:
            flags |= (cls[y] << CLASS_SHIFT[y]).astype(np.uint8)
        for tx in range(cols):
            sl = np.s_[:, tx * T:(tx + 1) * T]
            r, gg, b = g[2015][sl], g[2025][sl], flags[sl]
            if not (r.any() or gg.any() or (b & (FLAG_NODATA_2015 | FLAG_NODATA_2025)).any()):
                continue
            rgb = np.zeros((3, T, T), np.uint8)
            rgb[2] = FLAG_OUTSIDE  # padding beyond the level's extent
            h, w = r.shape
            rgb[0, :h, :w], rgb[1, :h, :w], rgb[2, :h, :w] = r, gg, b
            write_tile(tile_dir / str(level) / str(tx) / f"{ty}.webp", rgb)
            exists[ty, tx] = True
    return dict(level=level, block=f, cols=cols, rows=rows, width_px=out_w, height_px=out_h,
                tiles_written=int(exists.sum()),
                exists_bitmask_b64=base64.b64encode(np.packbits(exists.ravel())).decode())


def main():
    dss = {y: gdal.Open(str(cog_path(y))) for y in YEARS}
    ds = dss[YEARS[0]]
    W, H, gt = ds.RasterXSize, ds.RasterYSize, ds.GetGeoTransform()
    lmax = math.ceil(math.log2(max(W, H) / T))
    c = json.loads(CURVE_PATH.read_text())
    curve = (np.array(c["edges"]), np.array(c["cdf"]), c["top"])
    args = sys.argv[1:]
    version, cls_path = TILE_VERSION, None
    if "--version" in args:
        i = args.index("--version"); version = args[i + 1]; del args[i:i + 2]
    if "--classes" in args:
        i = args.index("--classes"); cls_path = Path(args[i + 1]).resolve(); del args[i:i + 2]
    if (version == TILE_VERSION) != (cls_path is None):
        raise SystemExit("--classes needs a new --version (v1 is the class-free version)")
    cls_ds = None
    if cls_path:
        cls_ds = gdal.Open(str(cls_path))
        if (cls_ds.RasterXSize, cls_ds.RasterYSize, cls_ds.GetGeoTransform()) != (W, H, gt):
            raise SystemExit("class raster grid differs from the radiance grid")
    tile_dir = TILE_DIR.parent / version
    levels = [int(a) for a in args] or list(range(lmax, -1, -1))
    tile_dir.mkdir(parents=True, exist_ok=True)
    index_path = tile_dir / "tiles.json"
    old = json.loads(index_path.read_text())["levels"] if index_path.exists() else []
    done = {d["level"]: d for d in old}
    for level in levels:
        t0 = time.time()
        done[level] = build_level(level, lmax, dss, curve, tile_dir, cls_ds)
        print(f"level {level}: {done[level]['tiles_written']} tiles, "
              f"{time.time() - t0:.0f}s", flush=True)
    index = {
        "version": version, "tile_size": T, "max_level": lmax, "format": "webp-lossless",
        "crs": "EPSG:4326", "origin_lon": gt[0], "origin_lat": gt[3],
        "native_pixel_deg": gt[1], "raster_width": W, "raster_height": H,
        "channels": {"r": "grey 2015", "g": "grey 2025",
                     "b": {"1": "2015 no data (-1.5)", "2": "2025 no data (-1.5)",
                           "4": "outside raster"}},
        "row_order": "tile y = 0 at the top (north); bitmask row-major, packbits big-endian",
        "values": "Display encoding (not data): grey from measured radiance via the "
                  "step-04 curve; flags inferred by rule (-1.5 = no data, human N2).",
        "sources": [f"data/derived/radiance/cog/{cog_path(y).name}" for y in YEARS],
        "curve": {k: c[k] for k in ("curve", "rule", "pool", "top_percentile", "top",
                                     "unit", "reference_grey")},
        "levels": [done[k] for k in sorted(done)],
    }
    if cls_ds:
        meta = json.loads(cls_path.with_suffix(".json").read_text())
        index["channels"]["b"].update({"bits 3-4": "2015 lamp-colour class", "bits 5-6": "2025 lamp-colour class"})
        index["classes"] = {"codes": meta["codes"], "label": meta["label"], "method": meta["method"],
                            "source": str(cls_path.relative_to(Path(__file__).resolve().parents[2])),
                            "coarse_levels": "class with the largest valid-radiance sum in the block (0 included); ties -> lower code"}
    index_path.write_text(json.dumps(index, indent=1))


if __name__ == "__main__":
    main()
