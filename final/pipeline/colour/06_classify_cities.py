"""Assign one lamp-colour class per test city and epoch from its archive JPEG.

For each photo in <pilot>_city_photos.csv: bright pixels as in 04_colour_ratios.py
(brightest channel MIN_BRIGHT..MAX_UNSATURATED, 8-bit), linear G/R per pixel,
white share = fraction with G/R >= WHITE_GR, class from SHARE_CUTS (see config.py).
Label: estimated (human-requested broad-strokes estimate, 2026-10-03; uncalibrated JPEG,
departs from Sanchez de Miguel et al. 2021, doi:10.1016/j.rse.2021.112611, which needs RAW).
Writes data/derived/colour/<pilot>_city_classes.csv.
Run from final/:  .venv/bin/python pipeline/colour/06_classify_cities.py
"""
import csv, importlib
import numpy as np
from osgeo import gdal
from config import *

cr = importlib.import_module("04_colour_ratios")

def white_share(pid):
    a = gdal.Open(str(RAW_DIR / "jpeg" / f"{pid}.JPG")).ReadAsArray().astype(np.float32)
    mx = a.max(0)
    m = (mx >= cr.MIN_BRIGHT) & (mx <= cr.MAX_UNSATURATED)
    r, g = cr.srgb_to_linear(a[0][m]), cr.srgb_to_linear(a[1][m])
    ok = r > 0
    gr = g[ok] / r[ok]
    return int(gr.size), float((gr >= WHITE_GR).mean())

def cls(share):
    return 1 if share < SHARE_CUTS[0] else 3 if share > SHARE_CUTS[1] else 2

def main():
    rows = list(csv.DictReader(open(DERIVED / f"{PILOT}_city_photos.csv")))
    out = []
    for r in rows:
        if not r.get("photo_id"):
            out.append(dict(city=r["city"], epoch=r["epoch"], class_code=0, class_name=CLASSES[0],
                            label="", note="no photo found by the selection rule"))
            continue
        n, s = white_share(r["photo_id"])
        c = cls(s)
        out.append(dict(city=r["city"], epoch=r["epoch"], photo_id=r["photo_id"], photo_date=r["date"],
                        pixels_used=n, white_share=round(s, 4), class_code=c, class_name=CLASSES[c],
                        label="estimated",
                        method=f"uncalibrated archive JPEG; white = linear G/R >= {WHITE_GR}; "
                               f"class cuts {SHARE_CUTS}; see pipeline/colour/METHOD.md",
                        requested_by="human (Alexander), 2026-10-03",
                        source=f"NASA Gateway to Astronaut Photography, {r['photo_id']}"))
        print(r["city"], r["epoch"], r["photo_id"], n, round(s, 4), CLASSES[c])
    keys = ["city", "epoch", "photo_id", "photo_date", "pixels_used", "white_share", "class_code",
            "class_name", "label", "method", "requested_by", "source", "note"]
    with open(DERIVED / f"{PILOT}_city_classes.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(out)

if __name__ == "__main__":
    main()
