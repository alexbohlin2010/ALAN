"""Colour ratios of bright pixels in archive JPEGs, for the human to set class boundaries.

Per photo: 8-bit sRGB -> linear (IEC 61966-2-1 transfer function), keep pixels whose
brightest channel is in [MIN_BRIGHT, MAX_UNSATURATED] (8-bit), compute G/R and B/G on the
linear values. Uncalibrated: camera white balance, JPEG processing, lens vignetting and
atmosphere are NOT corrected (human chose broad strokes, 2026-10-03).
Writes data/derived/colour/<pilot>_ratios_<ids>.json and previews/colour/ratios.html.
Run from final/:  .venv/bin/python pipeline/colour/04_colour_ratios.py [--name=NAME] ISS030-E-188190 ...
--name: output name (default: the joined photo IDs). Labels (city, epoch) come from <pilot>_city_photos.csv if listed.
"""
import csv, json, sys
import numpy as np
from osgeo import gdal
from config import *

gdal.UseExceptions()
MIN_BRIGHT = 40        # 8-bit; agent's provisional choice to drop dark/noisy pixels (human may change)
MAX_UNSATURATED = 249  # 8-bit; saturated channels distort ratios
BINS = np.geomspace(0.05, 3.0, 121)
PCTS = [5, 25, 50, 75, 95]

def srgb_to_linear(v):
    v = v / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)

def ratios(pid):
    a = gdal.Open(str(RAW_DIR / "jpeg" / f"{pid}.JPG")).ReadAsArray().astype(np.float32)
    mx = a.max(0)
    m = (mx >= MIN_BRIGHT) & (mx <= MAX_UNSATURATED)
    r, g, b = (srgb_to_linear(a[i][m]) for i in range(3))
    ok = (r > 0) & (g > 0)
    gr, bg = g[ok] / r[ok], b[ok] / g[ok]
    return dict(photo_id=pid, pixels_total=int(mx.size), pixels_used=int(gr.size),
                g_over_r_pct=dict(zip(PCTS, np.percentile(gr, PCTS).round(4).tolist())),
                b_over_g_pct=dict(zip(PCTS, np.percentile(bg, PCTS).round(4).tolist())),
                g_over_r_hist=np.histogram(gr, BINS)[0].tolist(),
                b_over_g_hist=np.histogram(bg, BINS)[0].tolist())

def svg(results, key, title):
    W, H, P = 560, 220, 40
    lx = lambda x: P + (np.log(x) - np.log(BINS[0])) / (np.log(BINS[-1]) - np.log(BINS[0])) * (W - 2 * P)
    cols = ["#d9822b", "#3b82c4", "#4caf50", "#9c27b0", "#e53935", "#00897b", "#6d4c41", "#546e7a"]
    out = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}"><text x="{P}" y="16">{title} (share of used pixels per bin; log x)</text>']
    mids = np.sqrt(BINS[:-1] * BINS[1:])
    ymax = max(max(np.array(r[key]) / max(1, r["pixels_used"])) for r in results)
    for i, r in enumerate(results):
        y = np.array(r[key]) / max(1, r["pixels_used"])
        pts = " ".join(f"{lx(x):.1f},{H - P - v / ymax * (H - 2 * P - 10):.1f}" for x, v in zip(mids, y))
        out.append(f'<polyline fill="none" stroke="{cols[i % 8]}" stroke-width="2" points="{pts}"/>')
        out.append(f'<text x="{W - 200}" y="{30 + 14 * i}" fill="{cols[i % 8]}">{r["label"] or r["photo_id"]}</text>')
    for t in [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0]:
        out.append(f'<line x1="{lx(t):.1f}" x2="{lx(t):.1f}" y1="{H - P}" y2="{H - P + 4}" stroke="#888"/><text x="{lx(t) - 8:.1f}" y="{H - P + 16}" font-size="10">{t}</text>')
    out.append(f'<line x1="{P}" x2="{W - P}" y1="{H - P}" y2="{H - P}" stroke="#888"/></svg>')
    return "\n".join(out)

def main(ids, name=None):
    labels = {}
    cp = DERIVED / f"{PILOT}_city_photos.csv"
    if cp.exists():
        labels = {r["photo_id"]: f"{r['city']} {r['epoch']} ({r['date'][:4]}, {r['focal']})" for r in csv.DictReader(open(cp))}
    res = [ratios(p) for p in ids]
    for r in res: r["label"] = labels.get(r["photo_id"], "")
    DERIVED.mkdir(parents=True, exist_ok=True)
    name = name or "_".join(ids)
    dst = DERIVED / f"{PILOT}_ratios_{name}.json"
    dst.write_text(json.dumps(dict(min_bright=MIN_BRIGHT, max_unsaturated=MAX_UNSATURATED,
                                   bins=BINS.round(5).tolist(), photos=res), indent=1))
    pv = FINAL / "previews/colour"; (pv / "thumbs").mkdir(parents=True, exist_ok=True)
    for p in ids:
        gdal.Translate(str(pv / "thumbs" / f"{p}.jpg"), str(RAW_DIR / "jpeg" / f"{p}.JPG"), format="JPEG", width=520, height=0)
    thumbs = "".join(f'<figure style="margin:0"><img src="thumbs/{r["photo_id"]}.jpg" width="520"><figcaption>{r["label"]} {r["photo_id"]}: G/R median {r["g_over_r_pct"][50]}</figcaption></figure>' for r in res)
    rows = "".join(f"<tr><td>{r['label']} {r['photo_id']}</td><td>{r['pixels_used']:,}</td><td>{r['g_over_r_pct']}</td><td>{r['b_over_g_pct']}</td></tr>" for r in res)
    (pv / f"ratios_{name}.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>Colour ratios (test)</title>
<body style="font:13px system-ui;background:#fff;color:#111;max-width:1180px;margin:20px auto">
<h3>Colour ratios of bright pixels, uncalibrated archive JPEGs (test, not a result)</h3>
<p>Pixels with brightest channel {MIN_BRIGHT}–{MAX_UNSATURATED} (8-bit); ratios on linearised sRGB. No white-balance, vignetting or atmospheric correction.</p>
<div style="display:flex;gap:20px;flex-wrap:wrap">{svg(res, 'g_over_r_hist', 'G/R')}{svg(res, 'b_over_g_hist', 'B/G')}</div>
<table border=1 cellpadding=4 style="border-collapse:collapse"><tr><th>photo</th><th>pixels used</th><th>G/R percentiles</th><th>B/G percentiles</th></tr>{rows}</table>
<div style="display:grid;grid-template-columns:repeat(2,520px);gap:12px;margin-top:16px">{thumbs}</div>
</body>""")
    print("wrote", dst.relative_to(FINAL), f"and previews/colour/ratios_{name}.html")
    for r in res: print(r["label"], r["photo_id"], r["pixels_used"], "G/R", r["g_over_r_pct"], "B/G", r["b_over_g_pct"])

if __name__ == "__main__":
    args = sys.argv[1:]
    name = next((a.split("=", 1)[1] for a in args if a.startswith("--name=")), None)
    main([a for a in args if not a.startswith("--name=")], name)
