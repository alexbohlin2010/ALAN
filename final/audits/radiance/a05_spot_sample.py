"""Audit a05: draw the random sample for the HUMAN spot check (RULES §3.2).

The agent only draws the sample and lists, for each sample, where to look in the RAW
file and what the derived data (COG value, tile pixel) claims. It does NOT read the
raw values: the human looks those up and fills in the blank columns.

Strata (agent's choice, stated so the human can change it):
  A  20 native pixels, uniform over raster pixels, kept only if > 0 in either year (COG)
  B   5 native pixels, uniform over all raster pixels (mostly 0)
  C   5 native pixels, uniform over the pixels that are -1.5 in either year (COG)
  D   5 level-8 tile pixels (2x2 native block), uniform over blocks, kept only if any
      native pixel in the block is > 0 in either year (COG)
"Uniform" is over the lat/lon pixel grid, not over area.

Usage: .venv/bin/python audits/radiance/a05_spot_sample.py <seed>
Output: audits/radiance/results/a05_spot_check_sample.md and .csv
"""
import csv, json, sys
from pathlib import Path
import numpy as np
from osgeo import gdal
from common import COG, TILES, YEARS, NO_DATA, TILE, RESULTS, FINAL, raw_path

N_A, N_B, N_C, N_D = 20, 5, 5, 5


def fmt(v):
    return "%.9g" % v


def main():
    seed = int(sys.argv[1])
    rng = np.random.default_rng(seed)
    cogs = {y: gdal.Open(str(COG[y]), gdal.GA_ReadOnly) for y in YEARS}
    W, H = cogs[2015].RasterXSize, cogs[2015].RasterYSize
    gt = cogs[2015].GetGeoTransform()
    band = {y: cogs[y].GetRasterBand(1) for y in YEARS}
    idx = json.loads((TILES / "tiles.json").read_text())
    lmax = idx["max_level"]

    def cog_vals(c, r, w=1, h=1):
        return {y: band[y].ReadAsArray(c, r, w, h) for y in YEARS}

    picks = []  # (stratum, level, col, row)
    seen = set()
    while sum(p[0] == "A" for p in picks) < N_A:
        c, r = int(rng.integers(W)), int(rng.integers(H))
        v = cog_vals(c, r)
        if (c, r) not in seen and any(v[y][0, 0] > 0 for y in YEARS):
            seen.add((c, r)); picks.append(("A", lmax, c, r))
    while sum(p[0] == "B" for p in picks) < N_B:
        c, r = int(rng.integers(W)), int(rng.integers(H))
        if (c, r) not in seen:
            seen.add((c, r)); picks.append(("B", lmax, c, r))
    nd = []
    for y in YEARS:
        for r0 in range(0, H, 2048):
            a = band[y].ReadAsArray(0, r0, W, min(2048, H - r0))
            rr, cc = np.nonzero(a == NO_DATA)
            nd.extend(zip((cc).tolist(), (rr + r0).tolist()))
    nd = sorted(set(nd))
    for i in rng.choice(len(nd), size=len(nd), replace=False):
        if sum(p[0] == "C" for p in picks) >= N_C:
            break
        c, r = nd[i]
        if (c, r) not in seen:
            seen.add((c, r)); picks.append(("C", lmax, c, r))
    W8, H8 = (W + 1) // 2, (H + 1) // 2
    while sum(p[0] == "D" for p in picks) < N_D:
        bc, br = int(rng.integers(W8)), int(rng.integers(H8))
        c, r = 2 * bc, 2 * br
        v = cog_vals(c, r, min(2, W - c), min(2, H - r))
        if ("D", bc, br) not in seen and any((v[y] > 0).any() for y in YEARS):
            seen.add(("D", bc, br)); picks.append(("D", lmax - 1, bc, br))

    rows = []
    for i, (s, lvl, c, r) in enumerate(picks, 1):
        f = 2 ** (lmax - lvl)
        tx, ty, px, py = c // TILE, r // TILE, c % TILE, r % TILE
        tile_rel = f"{lvl}/{tx}/{ty}.webp"
        tp = TILES / tile_rel
        if tp.exists():
            t = gdal.Open(str(tp), gdal.GA_ReadOnly).ReadAsArray(px, py, 1, 1)[:, 0, 0]
            tile_rgb = "/".join(str(int(x)) for x in t)
        else:
            tile_rgb = "tile not written (pipeline skipped it as empty)"
        nc0, nr0 = c * f, r * f
        natives = [(nc0 + dx, nr0 + dy) for dy in range(f) for dx in range(f)
                   if nc0 + dx < W and nr0 + dy < H]
        cv = {y: [band[y].ReadAsArray(nc, nr, 1, 1)[0, 0] for nc, nr in natives] for y in YEARS}
        rows.append(dict(
            id=i, stratum=s, tile_level=lvl, tile=tile_rel, tile_px_x=px, tile_px_y=py,
            tile_RGB=tile_rgb,
            raw_cols_rows=" ".join(f"{nc},{nr}" for nc, nr in natives),
            lon_lat_centre=" ".join(f"{gt[0] + (nc + .5) * gt[1]:.6f},{gt[3] + (nr + .5) * gt[5]:.6f}"
                                    for nc, nr in natives),
            cog_2015=" ".join(fmt(v) for v in cv[2015]),
            cog_2025=" ".join(fmt(v) for v in cv[2025]),
            human_raw_2015="", human_raw_2025="", human_cog_equals_raw="",
            human_tile_grey_follows_curve="", human_flags_correct="", human_notes=""))

    RESULTS.mkdir(parents=True, exist_ok=True)
    csv_p = RESULTS / "a05_spot_check_sample.csv"
    with open(csv_p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    rel = {y: raw_path(y).relative_to(FINAL) for y in YEARS}
    md = [f"# Human spot check: radiance COGs + tiles (RULES §3.2)", "",
          f"Drawn 2026-10-03 by `audits/radiance/a05_spot_sample.py` with **seed {seed}** "
          f"(numpy `default_rng`). Rerun: `.venv/bin/python audits/radiance/a05_spot_sample.py {seed}`.", "",
          "The agent did **not** read raw values for these samples. The derived values listed are what the "
          "COGs and tiles claim; the human looks up the raw values and fills in the blank columns "
          "of `a05_spot_check_sample.csv`.", "",
          "## Strata (agent's choice; can be changed)",
          f"- **A** ({N_A}) native pixels, uniform over the pixel grid, kept only if > 0 in either year",
          f"- **B** ({N_B}) native pixels, uniform over the whole pixel grid (mostly 0)",
          f"- **C** ({N_C}) native pixels, uniform over pixels that are −1.5 in either year",
          f"- **D** ({N_D}) level-8 tile pixels (2×2 native block), kept only if any pixel > 0 in either year",
          "", "## Raw files (read-only)",
          f"- 2015: `{rel[2015]}`", f"- 2025: `{rel[2025]}`", "",
          "## How to check one sample (suggested; from `final/`)",
          "1. Raw value at (col, row), 0-based, without writing anything next to the raw file:",
          "   `gdallocationinfo -valonly --config GDAL_PAM_ENABLED NO /vsigzip/<raw file> <col> <row>`",
          "   (or in QGIS: Identify at the listed lon/lat, which is the pixel centre, EPSG:4326). Each call "
          "decompresses the file, so expect up to ~1 min per call.",
          "2. Compare it with the COG value listed (should be identical).",
          "3. Tile pixel: `gdallocationinfo -valonly <tile path> <px> <py>` prints R, G, B. "
          "R/G should equal the curve grey of the raw value: 0 if ≤ 0, else "
          "`round(255·interp(min(v, top), edges, cdf))` from `data/derived/radiance/curve/hist_eq_p9999.json`. "
          "Helper: `.venv/bin/python audits/radiance/curve_grey.py <v> [<v> ...]`. "
          "Reference: 0.5→46, 1→127, 2→184, 5→221, 10→236, 20→245, 50→253, ≥100→255.",
          "4. For **D** (level 8): mean of the 4 raw pixels per year, leaving out −1.5 and counting "
          "other negatives as 0, then the curve. If all 4 are −1.5 the grey is 0 and the flag is set.",
          "5. B flags: 1 = 2015 is −1.5 (all of the block), 2 = 2025 is −1.5, 4 = outside the raster; "
          "values add up.", "",
          f"Tile paths are relative to `data/derived/radiance/tiles/v1/`.", "",
          "## Samples", "",
          "| # | S | tile (level/x/y) | px,py | tile R/G/B | raw col,row | lon,lat (centre) | COG 2015 | COG 2025 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['id']} | {r['stratum']} | `{r['tile']}` | {r['tile_px_x']},{r['tile_px_y']} | "
                  f"{r['tile_RGB']} | {r['raw_cols_rows'].replace(' ', '<br>')} | "
                  f"{r['lon_lat_centre'].replace(' ', '<br>')} | {r['cog_2015'].replace(' ', '<br>')} | "
                  f"{r['cog_2025'].replace(' ', '<br>')} |")
    md += ["", "## Human results",
           "Fill in `a05_spot_check_sample.csv` (columns `human_*`). Match rate = samples where every "
           "check matched / samples checked. Recorded by the human, not by an agent.", "",
           "- Checked by: ", "- Date: ", "- Samples checked: ", "- Matches: ", "- Match rate: ",
           "- Notes: "]
    md_p = RESULTS / "a05_spot_check_sample.md"
    md_p.write_text("\n".join(md) + "\n")
    print(f"wrote {md_p.relative_to(FINAL)} and {csv_p.relative_to(FINAL)}  ({len(rows)} samples)")


if __name__ == "__main__":
    main()
