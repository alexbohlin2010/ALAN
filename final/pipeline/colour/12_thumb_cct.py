"""Per-photo lamp colour temperature from archive thumbnails, corrected for the white balance used
when the archive converted the raw file (human request 2026-10-03, AI_LOG colour step 32).

Why: the archive JPEGs were converted from NEF with Adobe Camera Raw at varying white balance
(XMP crs:Temperature 3,200-5,700 K; auto or fixed). A photo converted at a low temperature shows
sodium light much less orange, so a G/R rule (10_white_share_grid.py) measures colour relative to
the photo's white balance, not the lamps.

Per photo (thumbnail in data/raw/colour/eol/small/; pool records of <pilot>_thumb_shares.csv):
1. White balance: crs:Temperature (K) from the file's XMP. Missing -> photo skipped. crs:Tint is
   recorded but not used (approximation).
2. Pixels: brightest channel MIN_BRIGHT..MAX_UNSATURATED (as 04_colour_ratios.py), sRGB decoded to
   linear, to CIE XYZ (sRGB/D65 matrix, IEC 61966-2-1).
3. Undo the conversion's white balance: Bradford chromatic adaptation (von Kries type) from D65
   (where the conversion put the shot white) back to the Planckian white point at crs:Temperature
   (Kim et al. 2002 cubic approximation of the Planckian locus, 1667-25000 K).
4. CCT per pixel: McCamy (1992) from CIE 1931 xy. Duv: signed distance in CIE 1960 uv from the
   Planckian point at that CCT. Lamp-like pixels: CCT_RANGE and |Duv| <= MAX_DUV (drops airglow
   and twilight, which sit far off the locus).
5. Photo values: lamp pixel count, median CCT, shares of lamp pixels with CCT < SODIUM_MAX_K
   (sodium-like) and >= WHITE_MIN_K (white: LED / metal halide / fluorescent). Photos with fewer
   than MIN_PIXELS lamp pixels get no values.
Labels: CCT and shares `estimated` (uncalibrated JPEG, Adobe's camera-specific mapping of
Temperature approximated by a blackbody white, tone curve not undone, sodium is not a blackbody so
its CCT is nominal).
Writes data/derived/colour/<pilot>_thumb_cct.csv.
Run from final/:  .venv/bin/python pipeline/colour/12_thumb_cct.py --pilot global
"""
import csv, importlib, re
import numpy as np
from osgeo import gdal
from config import *

gdal.UseExceptions()
cr = importlib.import_module("04_colour_ratios")

MIN_PIXELS = 200
CCT_RANGE = (1500, 10000)
MAX_DUV = 0.02
SODIUM_MAX_K = 2500   # HPS nominal ~1900-2200 K
WHITE_MIN_K = 2700    # warmest common white LED (2700 K) and up

SRGB_TO_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                        [0.2126729, 0.7151522, 0.0721750],
                        [0.0193339, 0.1191920, 0.9503041]])
BRADFORD = np.array([[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]])
D65_XYZ = np.array([0.95047, 1.0, 1.08883])

def planck_xy(T):
    T = np.asarray(T, float)
    x = np.where(T <= 4000, -0.2661239e9 / T**3 - 0.2343589e6 / T**2 + 0.8776956e3 / T + 0.179910,
                 -3.0258469e9 / T**3 + 2.1070379e6 / T**2 + 0.2226347e3 / T + 0.240390)
    y = np.where(T <= 2222, -1.1063814 * x**3 - 1.34811020 * x**2 + 2.18555832 * x - 0.20219683,
        np.where(T <= 4000, -0.9549476 * x**3 - 1.37418593 * x**2 + 2.09137015 * x - 0.16748867,
                 3.0817580 * x**3 - 5.87338670 * x**2 + 3.75112997 * x - 0.37001483))
    return x, y

def xy_to_XYZ(x, y):
    return np.array([x / y, 1.0, (1 - x - y) / y])

def uv(x, y):
    d = -2 * x + 12 * y + 3
    return 4 * x / d, 6 * y / d

def adapt_matrix(T):
    """Bradford: XYZ rendered with D65 white -> XYZ under the Planckian white at T."""
    src = BRADFORD @ D65_XYZ; dst = BRADFORD @ xy_to_XYZ(*planck_xy(T))
    return np.linalg.inv(BRADFORD) @ np.diag(dst / src) @ BRADFORD

def xmp(pid):
    b = (RAW_DIR / "small" / f"{pid}.JPG").read_bytes()[:200000]
    g = lambda k: (m.group(1).decode() if (m := re.search(rb'crs:' + k + rb'="([^"]*)"', b)) else "")
    return g(b"Temperature"), g(b"Tint"), g(b"WhiteBalance")

def photo_cct(pid, T):
    a = gdal.Open(str(RAW_DIR / "small" / f"{pid}.JPG")).ReadAsArray().astype(np.float32)
    if a.ndim != 3: return 0, None
    mx = a.max(0); m = (mx >= cr.MIN_BRIGHT) & (mx <= cr.MAX_UNSATURATED)
    lin = np.stack([cr.srgb_to_linear(a[k][m]) for k in range(3)])
    XYZ = adapt_matrix(T) @ (SRGB_TO_XYZ @ lin)
    s = XYZ.sum(0); ok = s > 0
    x, y = XYZ[0, ok] / s[ok], XYZ[1, ok] / s[ok]
    n = (x - 0.3320) / (0.1858 - y)
    cct = 449 * n**3 + 3525 * n**2 + 6823.3 * n + 5520.33
    cctc = np.clip(cct, 1667, 25000)
    u, v = uv(x, y); up, vp = uv(*planck_xy(cctc))
    duv = np.sign(v - vp) * np.hypot(u - up, v - vp)
    lamp = (cct >= CCT_RANGE[0]) & (cct <= CCT_RANGE[1]) & (np.abs(duv) <= MAX_DUV)
    return int(lamp.sum()), cct[lamp]

def main():
    rows = list(csv.DictReader(open(DERIVED / f"{PILOT}_thumb_shares.csv")))
    out = []
    for i, r in enumerate(rows):
        T, tint, wb = xmp(r["photo_id"])
        rec = dict(photo_id=r["photo_id"], date=r["date"], epoch=r["epoch"], lat=r["lat"], lon=r["lon"],
                   focal_mm=r["focal_mm"], record_type=r["record_type"], crs_temperature=T, crs_tint=tint,
                   crs_white_balance=wb, lamp_pixels=0, median_cct_k="", sodium_share="", white_share="",
                   label="", note="")
        if not T:
            rec["note"] = "skipped: no crs:Temperature in XMP"
        else:
            n, c = photo_cct(r["photo_id"], float(T))
            rec["lamp_pixels"] = n
            if n >= MIN_PIXELS:
                rec.update(median_cct_k=int(np.median(c)), sodium_share=round(float((c < SODIUM_MAX_K).mean()), 4),
                           white_share=round(float((c >= WHITE_MIN_K).mean()), 4), label="estimated")
            else:
                rec["note"] = f"skipped: < {MIN_PIXELS} lamp-like pixels"
        out.append(rec)
        if i % 2000 == 0: print(i, "of", len(rows), flush=True)
    f = DERIVED / f"{PILOT}_thumb_cct.csv"
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("wrote", f.relative_to(FINAL), len(out), "rows;", sum(o["label"] == "estimated" for o in out), "with values")

if __name__ == "__main__":
    main()
