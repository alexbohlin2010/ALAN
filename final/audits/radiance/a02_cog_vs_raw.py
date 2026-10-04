"""Audit a02: each COG vs its raw file.

Checks: dimensions, band count, data type, geotransform, CRS, nodata tag,
COG layout + compression, and bit-for-bit pixel equality over the full raster.
Value counts and ranges are recomputed from the RAW file and compared with
(a) the MANIFEST notes and (b) the pipeline's <cog>.counts.json.

Usage: .venv/bin/python audits/radiance/a02_cog_vs_raw.py <year>
Output: audits/radiance/results/a02_cog_vs_raw_<year>.json
"""
import json, sys, time
import numpy as np
from osgeo import gdal, osr
from common import COG, MANIFEST_COUNTS, NO_DATA, open_raw, raw_path, write_result

ROWS = 1024


def meta(ds):
    b = ds.GetRasterBand(1)
    srs = osr.SpatialReference(wkt=ds.GetProjection())
    srs.AutoIdentifyEPSG()
    return dict(width=ds.RasterXSize, height=ds.RasterYSize, bands=ds.RasterCount,
                dtype=gdal.GetDataTypeName(b.DataType), geotransform=list(ds.GetGeoTransform()),
                epsg=srs.GetAuthorityCode(None), nodata=b.GetNoDataValue(),
                overviews=b.GetOverviewCount(), wkt=ds.GetProjection())


def main():
    year = int(sys.argv[1])
    t0 = time.time()
    raw, cog = open_raw(year), gdal.Open(str(COG[year]), gdal.GA_ReadOnly)
    mr, mc = meta(raw), meta(cog)
    res = {"year": year, "raw": raw_path(year).name, "cog": str(COG[year].name),
           "raw_meta": {k: v for k, v in mr.items() if k != "wkt"},
           "cog_meta": {k: v for k, v in mc.items() if k != "wkt"},
           "cog_image_structure": cog.GetMetadata("IMAGE_STRUCTURE"), "checks": {}}
    ck = res["checks"]
    for k in ("width", "height", "bands", "dtype", "geotransform", "epsg", "nodata"):
        ck[f"meta_{k}_equal"] = mr[k] == mc[k]
    ck["crs_is_same"] = bool(osr.SpatialReference(wkt=mr["wkt"]).IsSame(
        osr.SpatialReference(wkt=mc["wkt"])))
    ck["cog_layout_is_COG"] = res["cog_image_structure"].get("LAYOUT") == "COG"
    ck["cog_compression"] = res["cog_image_structure"].get("COMPRESSION")

    W, H = mr["width"], mr["height"]
    br, bc = raw.GetRasterBand(1), cog.GetRasterBand(1)
    c = dict(zero=0, positive=0, positive_lt1=0, gt200=0, gt1000=0, eq_minus_1_5=0,
             other_negative=0, nan=0)
    vmin, vmax, total, minpos = np.inf, -np.inf, 0.0, np.inf
    neg_vals = set()
    diff_pixels, first_diff = 0, None
    for y in range(0, H, ROWS):
        n = min(ROWS, H - y)
        a = br.ReadAsArray(0, y, W, n)
        b = bc.ReadAsArray(0, y, W, n)
        d = a.view(np.uint32) != b.view(np.uint32)  # bitwise, NaN-safe
        if d.any():
            diff_pixels += int(d.sum())
            if first_diff is None:
                r, cc = np.argwhere(d)[0]
                first_diff = dict(row=int(y + r), col=int(cc), raw=float(a[r, cc]), cog=float(b[r, cc]))
        c["nan"] += int(np.isnan(a).sum())
        c["zero"] += int((a == 0).sum())
        pos = a > 0
        c["positive"] += int(pos.sum())
        c["positive_lt1"] += int(((a > 0) & (a < 1)).sum())
        c["gt200"] += int((a > 200).sum())
        c["gt1000"] += int((a > 1000).sum())
        c["eq_minus_1_5"] += int((a == NO_DATA).sum())
        on = (a < 0) & (a != NO_DATA)
        c["other_negative"] += int(on.sum())
        if on.any() and len(neg_vals) < 2000:
            neg_vals.update(np.unique(a[on]).tolist())
        vmin, vmax = min(vmin, float(np.nanmin(a))), max(vmax, float(np.nanmax(a)))
        if pos.any():
            minpos = min(minpos, float(a[pos].min()))
        total += float(a.sum(dtype=np.float64))
    raw_counts = dict(width=W, height=H, pixels=W * H, min=vmin, max=vmax,
                      mean=total / (W * H), min_positive=minpos, **c)
    res["raw_counts"] = raw_counts
    res["other_negative_range"] = [min(neg_vals), max(neg_vals)] if neg_vals else None
    ck["pixels_bitwise_equal"] = diff_pixels == 0
    res["diff_pixels"], res["first_diff"] = diff_pixels, first_diff
    ck["counts_sum_to_pixels"] = (c["zero"] + c["positive"] + c["eq_minus_1_5"]
                                  + c["other_negative"] + c["nan"]) == W * H

    # vs MANIFEST notes (max rounded to 3 decimals there)
    man = MANIFEST_COUNTS[year]
    vs_man = {}
    for k, v in man.items():
        got = raw_counts[k]
        vs_man[k] = dict(manifest=v, raw=got,
                         equal=(round(got, 3) == v) if k == "max" else (got == v))
    res["vs_manifest"] = vs_man
    ck["counts_match_manifest"] = all(x["equal"] for x in vs_man.values())

    # vs pipeline counts.json
    pj = json.loads(COG[year].with_suffix(".counts.json").read_text())
    vs_pj = {}
    for k, v in pj.items():
        if k in ("source", "source_sha256"):
            continue
        got = raw_counts.get(k) if k != "geotransform" else mr["geotransform"]
        eq = abs(got - v) <= 1e-12 * max(1, abs(v)) if k == "mean" else got == v
        vs_pj[k] = dict(counts_json=v, raw=got, equal=bool(eq))
    vs_pj["source"] = dict(counts_json=pj["source"], raw=raw_path(year).name,
                           equal=pj["source"] == raw_path(year).name)
    res["vs_counts_json"] = vs_pj
    ck["counts_json_matches_raw"] = all(x["equal"] for x in vs_pj.values())

    res["pass"] = all(v for k, v in ck.items() if k != "cog_compression")
    res["seconds"] = round(time.time() - t0)
    write_result(f"a02_cog_vs_raw_{year}.json", res)
    print(json.dumps(ck, indent=1))
    print("PASS" if res["pass"] else "FAIL")


if __name__ == "__main__":
    main()
