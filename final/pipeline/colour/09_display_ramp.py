"""Option B display ramp: one white share per epoch -> one grey threshold per epoch.

Human choice 2026-10-03 (AI_LOG colour step 18): every lit pixel is drawn as
grey x tint. Tint = sodium (2000 K) below the epoch's grey threshold, white LED (4000 K)
above it, blended over +-BLEND_GREY. The brightest pixels turn white first (display choice).

1. Epoch white share (`estimated`): median of the four test cities' white shares in
   data/derived/colour/iberia_city_classes.csv (uncalibrated archive JPEGs; see METHOD.md).
   Median, so one city (Valencia 2025, 0.74) does not set the value.
2. Grey threshold (`inferred`): the (1 - share) quantile of the display grey of lit pixels
   (radiance > 0) in that year's COG inside the Iberia box (config.BBOX), using the tile curve
   (data/derived/radiance/curve/hist_eq_p9999.json), so the share of Iberia's lit pixels drawn
   white equals the epoch share.
3. Tints: blackbody sRGB at 2000 K and 4000 K from display_tints.json (08_display_tints.py).

The shader applies the same thresholds everywhere on the globe. Outside Iberia that is a
display choice only: no photo was used there.
Writes data/derived/colour/display_ramp.json.
Run from final/:  .venv/bin/python pipeline/colour/09_display_ramp.py
"""
import csv, json
import numpy as np
from osgeo import gdal
from config import *

CURVE = FINAL / "data/derived/radiance/curve/hist_eq_p9999.json"
COG = FINAL / "data/derived/radiance/cog/vnl_{year}_average_masked.tif"
BLEND_GREY = 8  # half-width of the sodium -> white blend, in grey levels (display choice)

def grey(v, c):
    g = np.round(255 * np.interp(np.minimum(v, c["top"]), c["edges"], c["cdf"]))
    return np.where(v > 0, g, 0)

def iberia(path):
    ds = gdal.Open(str(path))
    x0, dx, _, y0, _, dy = ds.GetGeoTransform()
    c0 = int((BBOX["left_lon"] - x0) / dx); c1 = int(np.ceil((BBOX["right_lon"] - x0) / dx))
    r0 = int((BBOX["upper_lat"] - y0) / dy); r1 = int(np.ceil((BBOX["lower_lat"] - y0) / dy))
    return ds.GetRasterBand(1).ReadAsArray(c0, r0, c1 - c0, r1 - r0)

def main():
    rows = list(csv.DictReader(open(DERIVED / "iberia_city_classes.csv")))
    curve = json.loads(CURVE.read_text())
    tints = json.loads((DERIVED / "display_tints.json").read_text())
    out = {"epochs": {}, "blend_grey": BLEND_GREY,
           "tint_sodium": dict(cct_k=2000, srgb=tints["1"]["srgb"]),
           "tint_white": dict(cct_k=4000, srgb=tints["3"]["srgb"]),
           "note": "display ramp (human choice B, 2026-10-03); share estimated, threshold inferred, "
                   "tints display choice; see pipeline/colour/METHOD.md"}
    for ep in EPOCHS:
        shares = [float(r["white_share"]) for r in rows if int(r["epoch"]) == ep]
        share = float(np.median(shares))
        v = iberia(str(COG).format(year=ep))
        g = grey(v[v > 0], curve)
        thr = float(np.quantile(g, 1 - share))
        out["epochs"][str(ep)] = dict(
            white_share=round(share, 4), white_share_label="estimated",
            city_shares=shares, lit_pixels_iberia=int(g.size),
            grey_threshold=thr, grey_threshold_label="inferred")
    (DERIVED / "display_ramp.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main()
