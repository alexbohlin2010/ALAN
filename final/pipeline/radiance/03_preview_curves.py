"""Step 03: labelled previews of candidate radiance -> brightness curves (B4).

Display products only (written to final/previews/, gitignored); no data values
are changed. Human choices applied (2026-10-03):
  N2  -1.5 = no data (shown in a labelled display colour); other negatives -> 0
  B6  top of curve = a percentile of positive pixels, both years pooled
  B7  low zoom = mean of linear radiance (no-data pixels excluded), then curve
One curve and one top value are used for both years.

Usage (from final/):
  .venv/bin/python pipeline/radiance/03_preview_curves.py
Outputs: previews/curves/index.html (self-contained; PNGs also kept), previews/curves/stats.json
"""
import base64, html, json
import numpy as np
from osgeo import gdal
from config import YEARS, NO_COVERAGE, PREVIEW_DIR, cog_path

gdal.UseExceptions()
gdal.SetConfigOption("GDAL_NUM_THREADS", "ALL_CPUS")

OUT = PREVIEW_DIR / "curves"
GLOBAL_FACTOR = 20          # 86401 px -> ~4320 px wide (mean of 20x20 blocks)
TOP_PERCENTILE = 99.99      # B6: preview top; other percentiles reported in stats.json
NODATA_RGB = (255, 0, 255)  # display choice only: magenta = -1.5 "no data"
# Preview-only test crops (agent-picked for contrast of dim and bright areas; not
# a narrative choice). (name, west, south, east, north) in degrees.
CROPS = [("nile_delta", 29.0, 29.0, 33.0, 32.0),
         ("west_africa_coast", -1.0, 5.0, 4.0, 8.0)]


def curves(top, cdf_x, cdf_y):
    lin = lambda v: np.clip(v / top, 0, 1)
    def log(k):
        return lambda v: np.clip(np.log1p(np.maximum(v, 0) / k) / np.log1p(top / k), 0, 1)
    heq = lambda v: np.where(v > 0, np.interp(np.minimum(v, top), cdf_x, cdf_y), 0.0)
    return [("linear", "v / top, clipped", lin),
            ("log_k0.1", "log(1+v/0.1) / log(1+top/0.1)", log(0.1)),
            ("log_k1", "log(1+v/1) / log(1+top/1)", log(1.0)),
            ("log_k10", "log(1+v/10) / log(1+top/10)", log(10.0)),
            ("hist_eq", "CDF of positive pixels (both years pooled), zeros stay 0", heq)]


def read_rows(ds, y, h, x=0, w=None):
    return ds.GetRasterBand(1).ReadAsArray(x, y, w or ds.RasterXSize, h)


def global_mean(ds, f):
    """Block mean of linear radiance; -1.5 excluded, other negatives -> 0.
    Returns (mean, all_nodata_mask)."""
    W, H = ds.RasterXSize // f * f, ds.RasterYSize // f * f
    means, masks, positives = [], [], []
    for y in range(0, H, f * 60):
        a = read_rows(ds, y, min(f * 60, H - y), 0, W)
        positives.append(a[a > 0])
        nod = a == NO_COVERAGE
        a = np.where(nod | (a < 0), 0, a).astype(np.float64)
        s = a.reshape(a.shape[0] // f, f, W // f, f).sum((1, 3))
        n = (~nod).reshape(a.shape[0] // f, f, W // f, f).sum((1, 3))
        means.append(np.where(n > 0, s / np.maximum(n, 1), 0))
        masks.append(n == 0)
    return np.vstack(means), np.vstack(masks), np.concatenate(positives)


def read_crop(ds, west, south, east, north):
    gt = ds.GetGeoTransform()
    x0, x1 = int((west - gt[0]) / gt[1]), int((east - gt[0]) / gt[1])
    y0, y1 = int((north - gt[3]) / gt[5]), int((south - gt[3]) / gt[5])
    a = read_rows(ds, y0, y1 - y0, x0, x1 - x0)
    nod = a == NO_COVERAGE
    return np.where(nod | (a < 0), 0, a), nod


def write_png(path, grey01, nodata):
    g = np.round(grey01 * 255).astype(np.uint8)
    rgb = [np.where(nodata, c, g).astype(np.uint8) for c in NODATA_RGB]
    mem = gdal.GetDriverByName("MEM").Create("", g.shape[1], g.shape[0], 3, gdal.GDT_Byte)
    for i, band in enumerate(rgb):
        mem.GetRasterBand(i + 1).WriteArray(band)
    gdal.GetDriverByName("PNG").CreateCopy(str(path), mem)


def img(path):
    """Embed a PNG as a data URI so index.html is self-contained."""
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def curve_svg(fn, top):
    xs = np.logspace(-3, np.log10(top), 200)
    ys = fn(xs)
    lx = (np.log10(xs) + 3) / (np.log10(top) + 3)
    pts = " ".join(f"{160 * x:.1f},{80 - 80 * y:.1f}" for x, y in zip(lx, ys))
    return (f'<svg viewBox="-2 -2 164 84" width="160" height="80"><rect x="0" y="0" width="160" '
            f'height="80" fill="none" stroke="#999"/><polyline points="{pts}" fill="none" '
            f'stroke="#000" stroke-width="1.5"/></svg>'
            f'<div class="ax">x: radiance 0.001 → {top:.0f} (log axis) · y: grey 0 → 255</div>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dss = {y: gdal.Open(str(cog_path(y))) for y in YEARS}
    glob, posall = {}, []
    for y in YEARS:
        m, mask, pos = global_mean(dss[y], GLOBAL_FACTOR)
        glob[y] = (m, mask)
        posall.append(pos)
        print(y, "global mean done", flush=True)
    pos = np.concatenate(posall)
    pcts = [99.0, 99.9, 99.99, 99.999]
    pv = dict(zip(pcts, np.percentile(pos, pcts)))
    top = float(pv[TOP_PERCENTILE])
    # Histogram-equalisation CDF on log-spaced bins of pooled positive pixels (<= top)
    edges = np.logspace(np.log10(pos.min()), np.log10(top), 4097)
    hist, _ = np.histogram(np.minimum(pos, top), bins=edges)
    cdf_y = np.concatenate([[0], np.cumsum(hist) / hist.sum()])
    stats = {"note": "Percentiles from the first 86400 cols x 33600 rows of each year (the "
                     "block-mean grid; last column and row skipped). Preview use only.",
             "positive_pixels_pooled": int(pos.size),
             "percentiles_of_positive_pooled": {str(k): float(v) for k, v in pv.items()},
             "top_used": top, "top_percentile": TOP_PERCENTILE,
             "global_block_factor": GLOBAL_FACTOR,
             "share_of_positive_pixels_le": {str(t): float((pos <= t).mean())
                                            for t in (0.1, 0.5, 1, 5, 10, 50)}}
    del pos, posall
    (OUT / "stats.json").write_text(json.dumps(stats, indent=2))
    crops = {name: {y: read_crop(dss[y], *bb) for y in YEARS} for name, *bb in CROPS}

    rows = []
    for cname, formula, fn in curves(top, edges, cdf_y):
        cells = []
        for y in YEARS:
            m, mask = glob[y]
            write_png(OUT / f"global_{cname}_{y}.png", fn(m), mask)
            for name, *_ in CROPS:
                v, nod = crops[name][y]
                write_png(OUT / f"{name}_{cname}_{y}.png", fn(v), nod)
        rows.append((cname, formula, curve_svg(fn, top)))
        print(cname, "done", flush=True)

    regions = [("global", f"whole extent, mean of {GLOBAL_FACTOR}×{GLOBAL_FACTOR} native pixels "
                          f"(~{GLOBAL_FACTOR * 463 / 1000:.1f} km/px)")] + \
              [(n, f"native 15″ pixels, {w}°…{e}°E, {s}°…{nn}°N") for n, w, s, e, nn in CROPS]
    e = html.escape
    body = []
    for rname, rdesc in regions:
        body.append(f"<h2>{e(rname)} <small>{e(rdesc)}</small></h2><table>")
        body.append("<tr><th>curve</th><th>2015</th><th>2025</th></tr>")
        for cname, formula, svg in rows:
            body.append(f"<tr><td class='lab'><b>{e(cname)}</b><br><code>{e(formula)}</code>"
                        f"<br>top = {top:.2f} nW/cm²/sr (P{TOP_PERCENTILE})<br>{svg}</td>")
            for y in YEARS:
                body.append(f"<td><div class='cap'>{y} · {e(cname)}</div>"
                            f"<img src='{img(OUT / f'{rname}_{cname}_{y}.png')}'></td>")
            body.append("</tr>")
        body.append("</table>")
    page = f"""<!doctype html><meta charset="utf-8"><title>Curve previews</title>
<style>body{{font:13px system-ui;margin:16px;background:#fff;color:#111}}
table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:6px;vertical-align:top}}
td img{{width:100%;max-width:640px;display:block;background:#000;image-rendering:pixelated}}
.lab{{width:230px}}.cap{{font-weight:600;margin-bottom:4px}}.ax{{color:#666;font-size:11px}}
.note{{background:#f4f4f4;padding:10px;max-width:900px}}code{{font-size:11px}}</style>
<h1>Radiance → brightness curve previews (B4)</h1>
<div class="note"><b>Display previews, not data.</b> Source: EOG VNL V2 annual, <code>average_masked</code>,
2015 (v2.1) and 2025 (v2.2), via lossless COGs from step 01. Unit nW/cm²/sr.<br>
Same curve and same top value for both years. Grey = curve output quantised to 8 bits (as tiles would be, E1).<br>
<b>Magenta = display choice for “no data” (−1.5 pixels, N2)</b>, not a measured value. Other negatives shown as 0.<br>
Top of curve = P{TOP_PERCENTILE} of all positive pixels from both years pooled = {top:.2f}; values above it are white.
Other percentiles: {", ".join(f"P{k}={v:.1f}" for k, v in pv.items())}.<br>
Crops were picked by the agent as test areas with dim and bright lights; they are not a narrative choice.</div>
{''.join(body)}"""
    (OUT / "index.html").write_text(page)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
