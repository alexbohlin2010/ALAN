"""Audit a03: the display curve data/derived/radiance/curve/hist_eq_p9999.json.

Recomputes the stated curve from the RAW files: pool every v > 0 of both years,
top = P99.99 of the pool, 4096 log-spaced bins from min positive to top,
cdf = cumulative histogram of min(v, top) normalised to 1 with a leading 0.
Compares with the JSON, checks its internal invariants, and checks the
hist_eq meaning: grey(r)/255 should be close to the empirical fraction of
pooled positives <= r.

Usage: .venv/bin/python audits/radiance/a03_curve.py
Output: audits/radiance/results/a03_curve.json
"""
import json, time
import numpy as np
from common import YEARS, open_raw, load_curve, curve_grey, write_result

ROWS = 2048
TOP_P, BINS = 99.99, 4096  # stated: B6 = P99.99; bins from the curve's own description


def positives(year):
    ds = open_raw(year)
    b, out = ds.GetRasterBand(1), []
    for y in range(0, ds.RasterYSize, ROWS):
        a = b.ReadAsArray(0, y, ds.RasterXSize, min(ROWS, ds.RasterYSize - y))
        out.append(a[a > 0])
    return np.concatenate(out)


def main():
    t0 = time.time()
    edges_j, cdf_j, top_j, cj = load_curve()
    per = {y: positives(y) for y in YEARS}
    pool = np.concatenate([per[y] for y in YEARS])
    ck, res = {}, {}

    res["positive_pixels_raw"] = {str(y): int(per[y].size) for y in YEARS}
    ck["positive_counts_match"] = res["positive_pixels_raw"] == cj["positive_pixels"]

    top32 = float(np.percentile(pool, TOP_P))                    # on float32 values
    top64 = float(np.percentile(pool.astype(np.float64), TOP_P))  # in float64
    res.update(top_json=top_j, top_recomputed_float32=top32, top_recomputed_float64=top64)
    ck["top_matches"] = top32 == top_j
    ck["top_percentile_field"] = cj["top_percentile"] == TOP_P
    vmin = float(pool.min())
    res.update(min_positive_raw=vmin, min_positive_json=cj["min_positive"])
    ck["min_positive_matches"] = vmin == cj["min_positive"]
    above = int((pool > top_j).sum())
    res.update(pixels_above_top_raw=above, pixels_above_top_json=cj["pixels_above_top"])
    ck["pixels_above_top_matches"] = above == cj["pixels_above_top"]
    res["fraction_above_top"] = above / pool.size

    # Internal invariants of the JSON curve
    ck["edges_len"] = edges_j.size == BINS + 1
    ck["cdf_len"] = cdf_j.size == BINS + 1
    ck["edges_strictly_increasing"] = bool(np.all(np.diff(edges_j) > 0))
    ck["cdf_non_decreasing"] = bool(np.all(np.diff(cdf_j) >= 0))
    ck["cdf_starts_0_ends_1"] = cdf_j[0] == 0.0 and abs(cdf_j[-1] - 1.0) < 1e-12
    ck["edges_span_min_to_top"] = (np.isclose(edges_j[0], cj["min_positive"], rtol=1e-12)
                                   and np.isclose(edges_j[-1], top_j, rtol=1e-12))
    ck["edges_log_spaced"] = bool(np.allclose(np.diff(np.log10(edges_j)),
                                              np.diff(np.log10(edges_j)).mean(), rtol=1e-9))

    # Rebuild edges/cdf by the stated recipe and compare
    edges_r = np.logspace(np.log10(vmin), np.log10(top32), BINS + 1)
    hist, _ = np.histogram(np.minimum(pool, top32), bins=edges_r)
    cdf_r = np.concatenate([[0.0], np.cumsum(hist) / hist.sum()])
    res["edges_max_rel_diff"] = float(np.max(np.abs(edges_r - edges_j) / edges_j))
    res["cdf_max_abs_diff"] = float(np.max(np.abs(cdf_r - cdf_j)))
    ck["edges_rebuilt_match"] = res["edges_max_rel_diff"] < 1e-12
    ck["cdf_rebuilt_match"] = res["cdf_max_abs_diff"] < 1e-12
    res["hist_total"] = int(hist.sum())
    ck["hist_counts_every_positive"] = int(hist.sum()) == pool.size

    # Reference greys in the JSON follow the rule
    ref = cj["reference_grey"]
    got = curve_grey([r["radiance"] for r in ref], edges_j, cdf_j, top_j)
    res["reference_grey_check"] = [dict(radiance=r["radiance"], json=r["grey"], rule=int(g))
                                   for r, g in zip(ref, got)]
    ck["reference_greys_follow_rule"] = all(r["grey"] == int(g) for r, g in zip(ref, got))

    # hist_eq meaning: grey/255 ~ empirical CDF of pooled positives
    srt = np.sort(pool)
    probe = [0.01, 0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]
    emp = np.searchsorted(srt, probe, side="right") / srt.size
    gr = curve_grey(probe, edges_j, cdf_j, top_j)
    res["hist_eq_meaning"] = [dict(radiance=p, empirical_fraction_le=float(e),
                                   grey=int(g), grey_over_255=round(int(g) / 255, 4),
                                   abs_diff=round(abs(int(g) / 255 - float(e)), 4))
                              for p, e, g in zip(probe, emp, gr)]
    res["hist_eq_max_abs_diff"] = max(x["abs_diff"] for x in res["hist_eq_meaning"])
    ck["hist_eq_within_1_grey_step"] = res["hist_eq_max_abs_diff"] <= 1 / 255 + 1e-9
    ck["grey_0_for_nonpositive"] = bool(np.all(curve_grey([-1.5, -0.1, 0.0], edges_j, cdf_j, top_j) == 0))
    ck["grey_255_at_and_above_top"] = bool(np.all(curve_grey([top_j, 1e4, 1e5], edges_j, cdf_j, top_j) == 255))

    ck = {k: bool(v) for k, v in ck.items()}
    res["checks"], res["pass"] = ck, all(ck.values())
    res["seconds"] = round(time.time() - t0)
    write_result("a03_curve.json", res)
    print(json.dumps(ck, indent=1))
    print("PASS" if res["pass"] else "FAIL")


if __name__ == "__main__":
    main()
