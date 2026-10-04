"""Audit s05: random pixel sample for the RULES §3.2 human spot check. The agent does not do
the check and does not report a match rate.

  .venv/bin/python audits/story/s05_spot_sample.py <seed>
Needs results/s02_global.json (per-block counts) and results/s03_masks.npz (masks).
Values are read from the raw .tif.gz (via /vsigzip/) and, as a cross-check, from the COGs.
Output: results/s05_spot_check_sample.csv and .md

Strata (chosen by the agent; open to change by the humans), N = 44:
  A  8  lit in both years (> 0), uniform over the globe
  B  8  newly lit (not > 0 in 2015, > 0 in 2025), uniform
  C  6  lit -> unlit, uniform
  D  2  -1.5 in either year, uniform; D2 2 the same but not on the last (65°S) row
  E 12  country border: for India, France (incl. Corsica), Ukraine: 2 pixels just inside the
        mask (an edge neighbour is outside) and 2 just outside (an edge neighbour is inside)
  F  6  Corsica 2 (in France incl. Corsica, not in excl.), Crimea 2 (inside Natural Earth's
        Crimea polygon), Donetsk/Luhansk 2 (inside polygons C02/C03)
"""
import csv, json, sys
import numpy as np
from osgeo import gdal
from common import (COG, YEARS, RESULTS, open_raw, row_area_km2, centre_lat, centre_lon, NO_DATA,
                    raw_rad_path)

MASKS = {"India": "India", "France_incl_Corsica": "France", "France_excl_Corsica": "France_nocor",
         "Ukraine_excl_Crimea": "Ukraine"}


def unpack(z, key):
    shape = tuple(z[key + "_shape"]); win = tuple(int(x) for x in z[key + "_win"])
    return np.unpackbits(z[key + "_mask"])[:np.prod(shape)].reshape(shape).astype(bool), win


def in_mask(m, win, r, c):
    c0, r0, w, h = win
    return bool(0 <= r - r0 < h and 0 <= c - c0 < w and m[r - r0, c - c0])


def boundary(m):
    p = np.pad(m, 1)
    nb_out = ~p[:-2, 1:-1] | ~p[2:, 1:-1] | ~p[1:-1, :-2] | ~p[1:-1, 2:]
    nb_in = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m & nb_out, ~m & nb_in


def main():
    seed = int(sys.argv[1])
    rng = np.random.default_rng(seed)
    g = json.loads((RESULTS / "s02_global.json").read_text())
    blocks = g["blocks"]
    cog = {y: gdal.Open(str(COG[y])) for y in YEARS}
    gt = cog[2015].GetGeoTransform(); W, H = cog[2015].RasterXSize, cog[2015].RasterYSize
    z = np.load(RESULTS / "s03_masks.npz")
    masks = {k: unpack(z, v) for k, v in MASKS.items()}
    picks = []   # (stratum, row, col)

    def draw_global(stratum, key, k):
        tot = np.array([b[key] for b in blocks], np.int64)
        idx = np.sort(rng.choice(tot.sum(), size=k, replace=False))
        cum = np.cumsum(tot)
        for i in idx:
            bi = int(np.searchsorted(cum, i, side="right"))
            j = int(i - (cum[bi] - tot[bi]))
            b = blocks[bi]
            a = cog[2015].GetRasterBand(1).ReadAsArray(0, b["row0"], W, b["nrows"])
            c = cog[2025].GetRasterBand(1).ReadAsArray(0, b["row0"], W, b["nrows"])
            valid = (a != NO_DATA) & (c != NO_DATA)
            l15, l25 = valid & (a > 0), valid & (c > 0)
            if key == "lit_both": m = l15 & l25
            elif key == "newly_lit": m = ~l15 & l25
            elif key == "lit_to_unlit": m = l15 & ~l25
            else:
                m = (a == NO_DATA) | (c == NO_DATA)
                if key.endswith("not_last_row") and b["row0"] + b["nrows"] == H:
                    m[-1] = False
            flat = np.flatnonzero(m)
            assert len(flat) == b[key], (key, len(flat), b[key])
            r, cc = divmod(int(flat[j]), W)
            picks.append((stratum, b["row0"] + r, cc))

    def draw_mask(stratum, m, win, k):
        rr, cc = np.nonzero(m)
        for i in rng.choice(len(rr), size=k, replace=False):
            picks.append((stratum, win[1] + int(rr[i]), win[0] + int(cc[i])))

    draw_global("A lit both", "lit_both", 8)
    draw_global("B newly lit", "newly_lit", 8)
    draw_global("C lit to unlit", "lit_to_unlit", 6)
    draw_global("D -1.5", "minus_1_5_any", 2)
    draw_global("D2 -1.5 not last row", "minus_1_5_any_not_last_row", 2)
    for name in ("India", "France_incl_Corsica", "Ukraine_excl_Crimea"):
        m, win = masks[name]
        bi, bo = boundary(m)
        draw_mask(f"E border inside {name}", bi, win, 2)
        # outside-border pixels may lie on the window edge; the window has a 2-pixel margin
        draw_mask(f"E border outside {name}", bo, win, 2)
    mf, wf = masks["France_incl_Corsica"]; mn, wn = masks["France_excl_Corsica"]
    cor = np.zeros_like(mf)
    cor[:mn.shape[0], :mn.shape[1]] = mn       # same origin (col0,row0) by construction; checked below
    assert wf[:2] == wn[:2]
    draw_mask("F Corsica", mf & ~cor, wf, 2)
    for code, label in (("B89", "F Crimea polygon"),):
        m, win = unpack(z, f"disp_{code}"); draw_mask(label, m, win, 2)
    m2, w2 = unpack(z, "disp_C02"); m3, w3 = unpack(z, "disp_C03")
    draw_mask("F Donetsk/Luhansk polygon (C02)", m2, w2, 1)
    draw_mask("F Donetsk/Luhansk polygon (C03)", m3, w3, 1)

    # values from raw (sequential, rows sorted) and from COG
    order = sorted(range(len(picks)), key=lambda i: picks[i][1])
    raw_ds = {y: open_raw(y) for y in YEARS}
    raw = {y: raw_ds[y].GetRasterBand(1) for y in YEARS}
    vals = {}
    for i in order:
        _, r, c = picks[i]
        vals[i] = {y: float(raw[y].ReadAsArray(c, r, 1, 1)[0, 0]) for y in YEARS}
        for y in YEARS:
            assert float(cog[y].GetRasterBand(1).ReadAsArray(c, r, 1, 1)[0, 0]) == vals[i][y]
    rows = []
    for i, (s, r, c) in enumerate(picks):
        v15, v25 = vals[i][2015], vals[i][2025]
        excl = v15 == NO_DATA or v25 == NO_DATA
        def lit(v, t): return (not excl) and max(v, 0.0) > t
        def cls(t):
            if excl: return "excluded (-1.5)"
            return {(True, True): "lit both", (False, True): "newly lit", (True, False): "lit->unlit",
                    (False, False): "unlit both"}[(lit(v15, t), lit(v25, t))]
        rows.append(dict(
            id=f"S{i+1:02d}", stratum=s, row=r, col=c,
            lon_centre=f"{centre_lon(gt, c):.7f}", lat_centre=f"{centre_lat(gt, r):.7f}",
            lon_west=f"{gt[0] + c * gt[1]:.7f}", lon_east=f"{gt[0] + (c + 1) * gt[1]:.7f}",
            lat_north=f"{gt[3] + r * gt[5]:.7f}", lat_south=f"{gt[3] + (r + 1) * gt[5]:.7f}",
            raw_2015=repr(v15), raw_2025=repr(v25),
            pixel_area_km2=f"{float(row_area_km2(gt, [r])[0]):.6f}",
            class_gt0=cls(0.0), class_gt0_5=cls(0.5), class_gt1=cls(1.0),
            **{f"in_{k}": in_mask(m, w, r, c) for k, (m, w) in masks.items()},
            human_raw_2015="", human_raw_2025="", human_area_km2="", human_country="", human_match="", human_note=""))
    fields = list(rows[0].keys())
    with open(RESULTS / "s05_spot_check_sample.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(rows)
    write_md(seed, rows, gt)
    print(f"{len(rows)} samples written, seed {seed}")


def write_md(seed, rows, gt):
    L = [f"# Story statistic audit: human spot-check sheet (RULES §3.2)", "",
         f"Seed **{seed}** (drawn with `secrets.randbelow(2**31)`; numpy `default_rng(seed)`). "
         f"N = {len(rows)}. Generated by `audits/story/s05_spot_sample.py {seed}`. "
         "The agent has **not** done the check and reports no match rate. "
         "Fill the `human_*` columns in `s05_spot_check_sample.csv`.", "",
         "## What to check for each sample", "",
         "1. **Raw values.** Open the raw files in QGIS (read-only): Layer > Add Raster Layer, path "
         f"`/vsigzip//<full path>/data/raw/radiance/eog/{raw_rad_path(2015).name}` and the 2025 file "
         f"`{raw_rad_path(2025).name}`. Use Identify Features at `lon_centre, lat_centre` "
         "(or go to row/col). The value should equal `raw_2015` / `raw_2025` (Float32; QGIS may show fewer digits).",
         "2. **Pixel area.** `A = R² · Δλ · (sin(lat_north) − sin(lat_south))`, R = 6371.0071809 km, "
         f"Δλ = {gt[1]} ° in radians (= {np.radians(gt[1]):.12e}). Should equal `pixel_area_km2`.",
         "3. **Class.** Pairwise rule: if either value is −1.5 the pixel is excluded; other negatives count as 0. "
         "Lit at threshold t = value > t. Check `class_gt0` (main), `class_gt0_5`, `class_gt1`.",
         "4. **Country.** Add `/vsizip//<full path>/data/raw/boundaries/naturalearth/ne_10m_admin_0_countries.zip` "
         "(India: ADMIN = India; Ukraine: ADMIN = Ukraine) and `ne_10m_admin_0_map_units.zip` (France: GEOUNIT = France). "
         "A pixel belongs to a country if its **centre** (`lon_centre, lat_centre`) lies inside the polygon. "
         "For E samples the centre is close to the line: zoom in. Crimea / Donetsk / Luhansk polygons are in "
         "`ne_10m_admin_0_disputed_areas.zip` (BRK_A3 B89, C02, C03). Corsica: `in_France_excl_Corsica` should be False "
         "for any pixel on the island.", "",
         "Note: last row centre is −65.000001° (raw pixel size 0.0041666667°); the first and last columns are both centred on 180°.", "",
         "| id | stratum | row | col | lon | lat | raw 2015 | raw 2025 | area km² | class >0 | >0.5 | >1 | India | France incl. Cors. | France excl. Cors. | Ukraine |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    yn = lambda b: "yes" if b else "–"
    for r in rows:
        L.append(f"| {r['id']} | {r['stratum']} | {r['row']} | {r['col']} | {r['lon_centre']} | {r['lat_centre']} | "
                 f"{r['raw_2015']} | {r['raw_2025']} | {r['pixel_area_km2']} | {r['class_gt0']} | {r['class_gt0_5']} | "
                 f"{r['class_gt1']} | {yn(r['in_India'])} | {yn(r['in_France_incl_Corsica'])} | "
                 f"{yn(r['in_France_excl_Corsica'])} | {yn(r['in_Ukraine_excl_Crimea'])} |")
    L += ["", "Match rate: **pending (human)**.", ""]
    (RESULTS / "s05_spot_check_sample.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
