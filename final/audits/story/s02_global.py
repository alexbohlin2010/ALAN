"""Audit s02: recompute every number in data/derived/story/radiance_change_2015_2025.json
from the raw EOG .tif.gz files (read via /vsigzip/, not the COGs), and compare.

Definitions (human decisions, restated in common.py): M1, lit = > t for t in 0 / 0.5 / 1,
newly lit = not lit 2015 & lit 2025, lit -> unlit, sphere pixel area (authalic radius),
pairwise -1.5 exclusion, other negatives -> 0. Every column as stored (86401).
Also recorded: raw value counts (vs MANIFEST), the same numbers without the last column
(duplicated 180°), total radiance over all valid pixels (no threshold), and per-block
category counts for the spot-check sampler (s05).

  .venv/bin/python audits/story/s02_global.py
Output: audits/story/results/s02_global.json (+ s02.log via shell)
"""
import json, math, time
import numpy as np
from common import (YEARS, THRESHOLDS, NO_DATA, R_AUTHALIC, OUT_GLOBAL, open_raw, row_area_km2,
                    centre_lat, clean, pct, relerr, write_result, raw_rad_path, rad_rows)

BLOCK = 512


def main():
    t0 = time.time()
    ds = {y: open_raw(y) for y in YEARS}
    W, H = ds[2015].RasterXSize, ds[2015].RasterYSize
    gt = ds[2015].GetGeoTransform()
    assert ds[2025].GetGeoTransform() == gt and (ds[2025].RasterXSize, ds[2025].RasterYSize) == (W, H)
    band = {y: ds[y].GetRasterBand(1) for y in YEARS}

    counts = {y: dict(zero=0, positive=0, positive_lt1=0, gt200=0, gt1000=0, eq_minus_1_5=0,
                      other_negative=0, nan=0, min=np.inf, max=-np.inf) for y in YEARS}
    pair = dict(nodata_2015_only=0, nodata_2025_only=0, nodata_both=0)
    area_all = 0.0          # every pixel
    area_valid = 0.0        # pixels kept by the pairwise rule
    variants = {}           # key -> accumulator dict
    for t in THRESHOLDS:
        for v in ("all_cols", "no_last_col"):
            variants[(t, v)] = dict(rad15=0.0, rad25=0.0, a15=0.0, a25=0.0, new=0.0, lost=0.0,
                                    both=0.0, n15=0, n25=0, nnew=0, nlost=0, nboth=0)
    total_rad_all_valid = {y: 0.0 for y in YEARS}   # threshold-free sum over valid pixels
    edge_rad = {t: {y: 0.0 for y in YEARS} for t in THRESHOLDS}  # first + last column
    blocks = []             # per-block counts for the sampler (main threshold)

    for r0 in range(0, H, BLOCK):
        n = min(BLOCK, H - r0)
        a = band[2015].ReadAsArray(0, r0, W, n)
        b = band[2025].ReadAsArray(0, r0, W, n)
        for y, x in ((2015, a), (2025, b)):
            c = counts[y]
            c["zero"] += int(np.count_nonzero(x == 0)); c["positive"] += int(np.count_nonzero(x > 0))
            c["positive_lt1"] += int(np.count_nonzero((x > 0) & (x < 1)))
            c["gt200"] += int(np.count_nonzero(x > 200)); c["gt1000"] += int(np.count_nonzero(x > 1000))
            nd = x == NO_DATA
            c["eq_minus_1_5"] += int(np.count_nonzero(nd))
            c["other_negative"] += int(np.count_nonzero((x < 0) & ~nd))
            c["nan"] += int(np.count_nonzero(np.isnan(x)))
            c["min"] = min(c["min"], float(np.nanmin(x))); c["max"] = max(c["max"], float(np.nanmax(x)))
        nda, ndb = a == NO_DATA, b == NO_DATA
        pair["nodata_2015_only"] += int(np.count_nonzero(nda & ~ndb))
        pair["nodata_2025_only"] += int(np.count_nonzero(~nda & ndb))
        pair["nodata_both"] += int(np.count_nonzero(nda & ndb))

        valid, a0, b0 = clean(a, b)
        area_row = row_area_km2(gt, np.arange(r0, r0 + n))[:, None]       # (n,1)
        area_all += float(area_row.sum() * W)
        area_valid += float((valid * area_row).sum())
        total_rad_all_valid[2015] += float((a0 * area_row * valid).sum())
        total_rad_all_valid[2025] += float((b0 * area_row * valid).sum())

        blk = dict(row0=r0, nrows=n)
        for t in THRESHOLDS:
            l15 = valid & (a0 > t); l25 = valid & (b0 > t)
            new = ~l15 & l25 & valid; lost = l15 & ~l25; both = l15 & l25
            for v, sl in (("all_cols", slice(None)), ("no_last_col", slice(0, W - 1))):
                acc = variants[(t, v)]
                A = area_row
                acc["rad15"] += float((a0[:, sl] * A * l15[:, sl]).sum())
                acc["rad25"] += float((b0[:, sl] * A * l25[:, sl]).sum())
                for k, m in (("a15", l15), ("a25", l25), ("new", new), ("lost", lost), ("both", both)):
                    acc[k] += float((m[:, sl] * A).sum())
                for k, m in (("n15", l15), ("n25", l25), ("nnew", new), ("nlost", lost), ("nboth", both)):
                    acc[k] += int(np.count_nonzero(m[:, sl]))
            for y, x0, l in ((2015, a0, l15), (2025, b0, l25)):
                edge_rad[t][y] += float((x0[:, [0, W - 1]] * area_row * l[:, [0, W - 1]]).sum())
            if t == 0.0:
                blk.update(lit_both=int(np.count_nonzero(both)), newly_lit=int(np.count_nonzero(new)),
                           lit_to_unlit=int(np.count_nonzero(lost)),
                           minus_1_5_any=int(np.count_nonzero(nda | ndb)),
                           minus_1_5_any_not_last_row=int(np.count_nonzero((nda | ndb)[:-1] if r0 + n == H else (nda | ndb))))
        blocks.append(blk)
        print(f"rows {r0}-{r0+n-1} done, {time.time()-t0:.0f}s", flush=True)

    # --- geometry checks
    R = R_AUTHALIC
    top, bottom = gt[3], gt[3] + H * gt[5]
    band_75_65 = 2 * math.pi * R**2 * (math.sin(math.radians(75)) + math.sin(math.radians(65))) / 1e6
    grid_analytic = R**2 * math.radians(W * gt[1]) * (math.sin(math.radians(top)) - math.sin(math.radians(bottom))) / 1e6
    geom = dict(width=W, height=H, geotransform=gt, top_edge=top, bottom_edge=bottom,
                first_row_centre_lat=float(centre_lat(gt, 0)), last_row_centre_lat=float(centre_lat(gt, H - 1)),
                first_col_centre_lon=gt[0] + 0.5 * gt[1], last_col_centre_lon=gt[0] + (W - 0.5) * gt[1],
                lon_span_deg=W * gt[1],
                area_sum_all_pixels_km2=area_all, area_valid_km2=area_valid,
                area_analytic_grid_km2=grid_analytic,
                area_analytic_band_75N_65S_km2=band_75_65,
                area_sum_vs_grid_analytic_relerr=relerr(area_all, grid_analytic),
                area_sum_vs_band_75N_65S_pct=pct(area_all, band_75_65),
                area_one_column_km2=area_all / W)

    results = {}
    for (t, v), acc in variants.items():
        results.setdefault(str(t), {})[v] = dict(
            radiance_change_pct=pct(acc["rad25"], acc["rad15"]),
            lit_area_change_pct=pct(acc["a25"], acc["a15"]),
            newly_lit_area_pct_of_2015_lit=100 * acc["new"] / acc["a15"],
            lit_to_unlit_area_pct_of_2015_lit=100 * acc["lost"] / acc["a15"],
            total_radiance_x_area={"2015": acc["rad15"], "2025": acc["rad25"]},
            lit_area_km2={"2015": acc["a15"], "2025": acc["a25"], "newly_lit": acc["new"],
                          "lit_to_unlit": acc["lost"], "lit_both": acc["both"]},
            pixel_counts_unweighted={"lit15": acc["n15"], "lit25": acc["n25"], "new": acc["nnew"],
                                     "lost": acc["nlost"], "both": acc["nboth"]},
            edge_columns_share_of_radiance_pct={"2015": 100 * edge_rad[t][2015] / variants[(t, "all_cols")]["rad15"],
                                                "2025": 100 * edge_rad[t][2025] / variants[(t, "all_cols")]["rad25"]}
            if v == "all_cols" else None)
    out = dict(source="raw .tif.gz via /vsigzip/", raw={y: str(raw_rad_path(y).name) for y in YEARS},
               counts=counts, pairwise=pair, geometry=geom, results=results,
               total_radiance_all_valid_no_threshold={"2015": total_rad_all_valid[2015], "2025": total_rad_all_valid[2025],
                                                      "change_pct": pct(total_rad_all_valid[2025], total_rad_all_valid[2015])},
               blocks=blocks, runtime_s=time.time() - t0)
    out["comparison"] = compare(out)
    write_result("s02_global.json", out)
    print(json.dumps(out["comparison"]["summary"], indent=1))


def compare(mine):
    """Compare every number in the pipeline output with the recomputation."""
    theirs = json.loads(OUT_GLOBAL.read_text())
    rows, worst = [], 0.0
    def cmp(name, a, b, exact=False):
        nonlocal worst
        e = relerr(a, b)
        ok = (a == b) if exact else e < 1e-9
        worst = max(worst, e) if not exact else worst
        rows.append(dict(item=name, pipeline=a, audit=b, relerr=e, pass_=ok))
    ch = theirs["checks"]
    for y in ("2015", "2025"):
        cmp(f"positive_pixels_without_exclusion[{y}]", ch["positive_pixels_without_exclusion"][y], mine["counts"][int(y)]["positive"], True)
        cmp(f"other_negatives_set_to_zero[{y}]", ch["other_negatives_set_to_zero"][y], mine["counts"][int(y)]["other_negative"], True)
    for k in ("nodata_2015_only", "nodata_2025_only", "nodata_both"):
        cmp(f"pixels_excluded_pairwise.{k}", ch["pixels_excluded_pairwise"][k], mine["pairwise"][k], True)
    cmp("valid_area_km2", ch["valid_area_km2"], mine["geometry"]["area_valid_km2"])
    cmp("grid.width", theirs["grid"]["width"], mine["geometry"]["width"], True)
    cmp("grid.height", theirs["grid"]["height"], mine["geometry"]["height"], True)
    for i in range(6):
        cmp(f"grid.geotransform[{i}]", theirs["grid"]["geotransform"][i], mine["geometry"]["geotransform"][i], True)
    cmp("sphere_radius_m", theirs["sphere_radius_m"], R_AUTHALIC, True)
    for r in theirs["results"]:
        t = str(float(r["lit_definition"].split(">")[1].split()[0]))
        m = mine["results"][t]["all_cols"]
        for k in ("radiance_change_pct", "lit_area_change_pct", "newly_lit_area_pct_of_2015_lit", "lit_to_unlit_area_pct_of_2015_lit"):
            cmp(f"[>{t}] {k}", r[k], m[k])
        for y in ("2015", "2025"):
            cmp(f"[>{t}] total_radiance_x_area[{y}]", r["total_radiance_x_area"][y], m["total_radiance_x_area"][y])
            cmp(f"[>{t}] edge_columns_share_of_radiance_pct[{y}]", r["edge_columns_share_of_radiance_pct"][y], m["edge_columns_share_of_radiance_pct"][y])
        for k in ("2015", "2025", "newly_lit", "lit_to_unlit", "lit_both"):
            cmp(f"[>{t}] lit_area_km2.{k}", r["lit_area_km2"][k], m["lit_area_km2"][k])
        for k in ("lit15", "lit25", "new", "lost"):
            cmp(f"[>{t}] pixel_counts_unweighted.{k}", r["pixel_counts_unweighted"][k], m["pixel_counts_unweighted"][k], True)
        cmp(f"[>{t}] is_main_result", r["is_main_result"], t == "0.0", True)
    n_fail = sum(not x["pass_"] for x in rows)
    return dict(rows=rows, summary=dict(items=len(rows), failed=n_fail, worst_relerr_float=worst,
                                        verdict="PASS" if n_fail == 0 else "FAIL"))


if __name__ == "__main__":
    main()
