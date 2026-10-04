"""Audit s06: invariants and internal consistency.

- raw value counts (s02, from raw) vs the counts written in the radiance MANIFEST notes;
- counts add up to the pixel total; pairwise exclusions add up to the -1.5 counts;
- total grid area vs the analytic 75N-65S band, with the difference broken down;
- both pipeline outputs: percentages recomputed from their own totals, area identities
  (2025 lit = 2015 lit + newly lit - lit->unlit; lit both = 2015 lit - lit->unlit),
  pixel-count identities, France excl. <= incl. Corsica, Corsica area vs its polygon.

  .venv/bin/python audits/story/s06_invariants.py
Output: results/s06_invariants.json
"""
import json, math, re
from common import (RESULTS, OUT_GLOBAL, OUT_COUNTRY, R_AUTHALIC, rad_rows, pct, relerr, write_result)


def manifest_counts():
    out = {}
    for y, r in rad_rows().items():
        n = r["notes"]
        g = lambda pat: int(re.search(pat, n).group(1))
        out[y] = dict(width=g(r"(\d+)x\d+ px"), height=g(r"\d+x(\d+) px"), pixels=g(r"Counts of (\d+) px"),
                      zero=g(r"zero (\d+)"), positive=g(r">0 (\d+)"), positive_lt1=g(r"<1: (\d+)"),
                      gt200=g(r">200: (\d+)"), gt1000=g(r">1000: (\d+)"), eq_minus_1_5=g(r"==-1.5: (\d+)"),
                      other_negative=g(r"other negative: (\d+)"), nan=g(r"NaN (\d+)"),
                      max=float(re.search(r"max ([\d.]+)", n).group(1)))
    return out


def main():
    s02 = json.loads((RESULTS / "s02_global.json").read_text())
    s03 = json.loads((RESULTS / "s03_masks.json").read_text())
    res, ok = {}, True
    # counts vs MANIFEST
    mc = manifest_counts(); cmpc = {}
    for y in (2015, 2025):
        c = s02["counts"][str(y)]; m = mc[y]
        rows = {k: dict(manifest=m[k], raw=c[k], pass_=m[k] == c[k]) for k in
                ("zero", "positive", "positive_lt1", "gt200", "gt1000", "eq_minus_1_5", "other_negative", "nan")}
        rows["max(3 dp)"] = dict(manifest=m["max"], raw=c["max"], pass_=abs(m["max"] - c["max"]) < 1e-3)
        total = c["zero"] + c["positive"] + c["eq_minus_1_5"] + c["other_negative"] + c["nan"]
        rows["sum_of_classes_eq_pixels"] = dict(manifest=m["pixels"], raw=total, pass_=total == m["pixels"] == s02["geometry"]["width"] * s02["geometry"]["height"])
        cmpc[y] = rows; ok &= all(v["pass_"] for v in rows.values())
    res["counts_vs_manifest"] = cmpc
    p = s02["pairwise"]
    res["pairwise_sums"] = dict(
        nd2015=p["nodata_2015_only"] + p["nodata_both"], nd2025=p["nodata_2025_only"] + p["nodata_both"],
        pass_=(p["nodata_2015_only"] + p["nodata_both"] == mc[2015]["eq_minus_1_5"]
               and p["nodata_2025_only"] + p["nodata_both"] == mc[2025]["eq_minus_1_5"]))
    ok &= res["pairwise_sums"]["pass_"]

    # area breakdown
    g = s02["geometry"]; R2 = R_AUTHALIC ** 2 / 1e6
    s = lambda d: math.sin(math.radians(d))
    W, dx = g["width"], g["geotransform"][1]
    band = 2 * math.pi * R2 * (s(75) + s(65))
    lat_part = 2 * math.pi * R2 * (s(g["top_edge"]) - s(g["bottom_edge"]))      # 360°, grid lat edges
    lon_dup = lat_part * (W * dx / 360.0)                                        # + width as stored
    res["area"] = dict(
        band_75N_65S_km2=band, grid_sum_km2=g["area_sum_all_pixels_km2"],
        diff_total_km2=g["area_sum_all_pixels_km2"] - band,
        diff_from_half_pixel_overhang_top_and_bottom_km2=lat_part - band,
        diff_from_86401_columns_and_stored_pixel_size_km2=lon_dup - lat_part,
        of_which_one_duplicate_column_km2=lat_part / 86400.0,
        residual_km2=g["area_sum_all_pixels_km2"] - lon_dup,
        valid_area_pipeline_km2=json.loads(OUT_GLOBAL.read_text())["checks"]["valid_area_km2"],
        valid_area_audit_km2=g["area_valid_km2"])
    res["area"]["pass_"] = abs(res["area"]["residual_km2"]) < 1.0
    ok &= res["area"]["pass_"]

    # internal consistency of the pipeline outputs
    def consistency(name, r):
        L, T = r["lit_area_km2"], r["total_radiance_x_area"]
        d = dict(where=name, lit=r["lit_definition"],
                 radiance_pct=relerr(r["radiance_change_pct"], pct(T["2025"], T["2015"])),
                 lit_area_pct=relerr(r["lit_area_change_pct"], pct(L["2025"], L["2015"])),
                 newly_pct=relerr(r["newly_lit_area_pct_of_2015_lit"], 100 * L["newly_lit"] / L["2015"]),
                 lost_pct=relerr(r["lit_to_unlit_area_pct_of_2015_lit"], 100 * L["lit_to_unlit"] / L["2015"]),
                 identity_2025=relerr(L["2025"], L["2015"] + L["newly_lit"] - L["lit_to_unlit"]))
        if "lit_both" in L:
            d["identity_both"] = relerr(L["lit_both"], L["2015"] - L["lit_to_unlit"])
        if "pixel_counts_unweighted" in r:
            c = r["pixel_counts_unweighted"]
            d["pixel_identity_exact"] = c["lit25"] == c["lit15"] + c["new"] - c["lost"]
        d["pass_"] = all((v < 1e-12) if isinstance(v, float) else v for k, v in d.items() if k not in ("where", "lit"))
        return d
    G = json.loads(OUT_GLOBAL.read_text()); C = json.loads(OUT_COUNTRY.read_text())
    cons = [consistency("global", r) for r in G["results"]]
    for nm, a in C["areas"].items():
        cons += [consistency(nm, r) for r in a["results"]]
    res["output_consistency"] = cons; ok &= all(c["pass_"] for c in cons)
    fi, fe = C["areas"]["France (mainland incl. Corsica)"], C["areas"]["France (mainland excl. Corsica)"]
    cor_poly = sum(p["area_km2"] for p in s03["checks"]["france_parts"] if p["corsica"])
    res["corsica"] = dict(area_incl_minus_excl_km2=fi["area_inside_km2"] - fe["area_inside_km2"],
                          corsica_polygons_area_km2=cor_poly,
                          pixels_incl_minus_excl=fi["pixels_inside"] - fe["pixels_inside"],
                          excl_le_incl=all(fe["results"][i]["lit_area_km2"][y] <= fi["results"][i]["lit_area_km2"][y]
                                           for i in range(3) for y in ("2015", "2025")))
    res["corsica"]["pass_"] = res["corsica"]["excl_le_incl"] and relerr(res["corsica"]["area_incl_minus_excl_km2"], cor_poly) < 1e-3
    ok &= res["corsica"]["pass_"]
    res["pass"] = ok
    write_result("s06_invariants.json", res)
    print("PASS" if ok else "FAIL"); print(json.dumps(res["area"], indent=1)); print(res["corsica"])


if __name__ == "__main__":
    main()
