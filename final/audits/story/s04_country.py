"""Audit s04: recompute every number in data/derived/story/country_change_2015_2025.json
with the audit's own masks (s03_masks.npz, scanline point-in-polygon) and compare.

Radiance is read from the COGs (window reads). The COGs were audited bit-identical to the
raw files (audits/radiance/AUDIT_2026-10-03.md, a02); their mtimes predate that audit.

  .venv/bin/python audits/story/s04_country.py
Output: results/s04_country.json
"""
import json
import numpy as np
from osgeo import gdal
from common import (COG, YEARS, THRESHOLDS, NO_DATA, OUT_COUNTRY, row_area_km2, clean, pct, relerr,
                    write_result, RESULTS)

KEYS = {"India": "India", "France (mainland incl. Corsica)": "France",
        "France (mainland excl. Corsica)": "France_nocor", "Ukraine (excl. Crimea)": "Ukraine"}


def load_mask(z, key):
    shape = tuple(z[key + "_shape"]); win = tuple(int(x) for x in z[key + "_win"])
    m = np.unpackbits(z[key + "_mask"])[:np.prod(shape)].reshape(shape).astype(bool)
    return m, win


def stats(a, b, m, area_row):
    nd = {"2015": int(((a == NO_DATA) & m).sum()), "2025": int(((b == NO_DATA) & m).sum())}
    valid, a0, b0 = clean(a, b)
    valid &= m
    res = []
    for t in THRESHOLDS:
        l15 = valid & (a0 > t); l25 = valid & (b0 > t)
        A = area_row
        r15 = float((a0 * A * l15).sum()); r25 = float((b0 * A * l25).sum())
        s15 = float((l15 * A).sum()); s25 = float((l25 * A).sum())
        new = float((~l15 & l25 * A).sum()) if False else float(((~l15 & l25) * A).sum())
        lost = float(((l15 & ~l25) * A).sum())
        res.append(dict(threshold=t, radiance_change_pct=pct(r25, r15), lit_area_change_pct=pct(s25, s15),
                        newly_lit_area_pct_of_2015_lit=100 * new / s15, lit_to_unlit_area_pct_of_2015_lit=100 * lost / s15,
                        total_radiance_x_area={"2015": r15, "2025": r25},
                        lit_area_km2={"2015": s15, "2025": s25, "newly_lit": new, "lit_to_unlit": lost}))
    return dict(pixels_inside=int(m.sum()), area_inside_km2=float((m * area_row).sum()),
                pixels_excluded_pairwise=int((m & ~((a != NO_DATA) & (b != NO_DATA))).sum()),
                nodata_pixels=nd, results=res)


def main():
    z = np.load(RESULTS / "s03_masks.npz")
    ds = {y: gdal.Open(str(COG[y])) for y in YEARS}
    gt = ds[2015].GetGeoTransform()
    theirs = json.loads(OUT_COUNTRY.read_text())
    out, rows = {}, []
    def cmp(name, p, a, exact=False):
        e = relerr(p, a)
        rows.append(dict(item=name, pipeline=p, audit=a, relerr=e, pass_=(p == a) if exact else e < 1e-9))
    for name, key in KEYS.items():
        m, (c0, r0, w, h) = load_mask(z, key)
        a = ds[2015].GetRasterBand(1).ReadAsArray(c0, r0, w, h)
        b = ds[2025].GetRasterBand(1).ReadAsArray(c0, r0, w, h)
        s = stats(a, b, m, row_area_km2(gt, np.arange(r0, r0 + h))[:, None])
        out[name] = s
        t = theirs["areas"][name]
        for k in ("pixels_inside", "pixels_excluded_pairwise"):
            cmp(f"{name}: {k}", t[k], s[k], True)
        for y in ("2015", "2025"):
            cmp(f"{name}: nodata_pixels[{y}]", t["nodata_pixels"][y], s["nodata_pixels"][y], True)
        cmp(f"{name}: area_inside_km2", t["area_inside_km2"], s["area_inside_km2"])
        for tr in t["results"]:
            th = float(tr["lit_definition"].split(">")[1].split()[0])
            sr = next(x for x in s["results"] if x["threshold"] == th)
            cmp(f"{name} [>{th}]: is_main_result", tr["is_main_result"], th == 0.0, True)
            for k in ("radiance_change_pct", "lit_area_change_pct", "newly_lit_area_pct_of_2015_lit", "lit_to_unlit_area_pct_of_2015_lit"):
                cmp(f"{name} [>{th}]: {k}", tr[k], sr[k])
            for y in ("2015", "2025"):
                cmp(f"{name} [>{th}]: total_radiance_x_area[{y}]", tr["total_radiance_x_area"][y], sr["total_radiance_x_area"][y])
            for k in ("2015", "2025", "newly_lit", "lit_to_unlit"):
                cmp(f"{name} [>{th}]: lit_area_km2.{k}", tr["lit_area_km2"][k], sr["lit_area_km2"][k])
        print(name, "done", flush=True)
    # internal consistency: 2025 lit = 2015 lit + newly lit - lit->unlit
    cons = []
    for name, s in out.items():
        for r in s["results"]:
            L = r["lit_area_km2"]
            cons.append(dict(area=name, threshold=r["threshold"],
                             identity_relerr=relerr(L["2025"], L["2015"] + L["newly_lit"] - L["lit_to_unlit"])))
    nf = sum(not r["pass_"] for r in rows)
    res = dict(areas=out, comparison=dict(rows=rows, summary=dict(items=len(rows), failed=nf,
               worst_relerr=max(r["relerr"] for r in rows), verdict="PASS" if nf == 0 else "FAIL")),
               identity_lit25_eq_lit15_plus_new_minus_lost=cons)
    write_result("s04_country.json", res)
    print(json.dumps(res["comparison"]["summary"]))


if __name__ == "__main__":
    main()
