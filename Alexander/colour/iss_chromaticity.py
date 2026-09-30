"""'Eyedropper' on calibrated ISS frames: camera channels -> CIE 1931 xy.

For each frame, the linear calibrated channels (R1, G2, B4) are converted with the camera's
Adobe/LibRaw ColorMatrix (XYZ(D65) -> camera, D65-referenced), inverted:  XYZ = M^-1 · [R, G, B].
Matrices from LibRaw src/tables/colordata.cpp (inputs/libraw_colordata.cpp):
  Nikon D3S { 8828,-2406,-694,-4874,12603,2541,-660,1509,7587 } / 10000
  Nikon D4  { 8598,-2848,-857,-5618,13606,2195,-1002,1773,7137 } / 10000
  Nikon D5  { 9200,-3522,-992,-5755,13803,2117,-753,1486,6338 } / 10000
Camera models and dates from NASA Gateway to Astronaut Photography (eol.jsc.nasa.gov).

Assumption to test: the 'cal2N' calibration preserves the camera's native channel ratios (i.e. it is
a common scale, not a per-channel rescaling). If it holds, 2012 Madrid (documented sodium stock)
should land near the measured HPS chromaticity (0.536, 0.415) in lamp_class_xy.csv.

Outputs: iss_chromaticity.csv (per frame: luminance-weighted xy over lit pixels, and xy percentiles).
"""
import csv, math
import numpy as np, rasterio
from rasterio.windows import from_bounds

M = {'D3S': [8828, -2406, -694, -4874, 12603, 2541, -660, 1509, 7587],
     'D4': [8598, -2848, -857, -5618, 13606, 2195, -1002, 1773, 7137],
     'D5': [9200, -3522, -992, -5755, 13803, 2117, -753, 1486, 6338]}
FRAMES = [('2012-02-12', 'iss030e082053', 'D3S'), ('2015-01-24', 'iss042e183298', 'D4'),
          ('2019-11-08', 'iss061e035301', 'D5')]
LAT, LON, R_KM = 40.42, -3.70, 30.0
dlat = R_KM / 110.57; dlon = R_KM / (111.32 * math.cos(math.radians(LAT)))
BOX = (LON - dlon, LAT - dlat, LON + dlon, LAT + dlat)


def read(frame, ch):
    with rasterio.open(f'inputs/iss/Corr_{frame}{ch}F.cal2N.Ao2_rect.tiff') as s:
        w = from_bounds(*BOX, transform=s.transform)
        return s.read(1, window=w, boundless=True, fill_value=np.nan).astype('float64'), s.window_transform(w)


rows = []
for date, frame, cam in FRAMES:
    (R, t), (G, _), (B, _) = read(frame, 'R1'), read(frame, 'G2'), read(frame, 'B4')
    h, w = R.shape
    ys, xs = np.mgrid[0:h, 0:w]
    lon = t.c + (xs + .5) * t.a; lat = t.f + (ys + .5) * t.e
    d = np.hypot((lon - LON) * 111.32 * math.cos(math.radians(LAT)), (lat - LAT) * 110.57)
    ok = np.isfinite(R) & np.isfinite(G) & np.isfinite(B) & (d <= R_KM) & (R > 0) & (G > 0) & (B > 0)
    cam_rgb = np.stack([R[ok], G[ok], B[ok]])
    XYZ = np.linalg.inv(np.array(M[cam]).reshape(3, 3) / 1e4) @ cam_rgb
    Y = XYZ[1]
    lit = Y > np.percentile(Y, 50)
    Xs, Ys, Zs = XYZ[:, lit].sum(axis=1)
    x, y = Xs / (Xs + Ys + Zs), Ys / (Xs + Ys + Zs)
    s = XYZ[:, lit].sum(axis=0); px_x = XYZ[0, lit] / s; px_y = XYZ[1, lit] / s
    rows.append(dict(date=date, frame=frame, camera=f'Nikon {cam}', x=round(x, 4), y=round(y, 4),
                     x_p10=round(np.percentile(px_x, 10), 4), x_p90=round(np.percentile(px_x, 90), 4),
                     y_p10=round(np.percentile(px_y, 10), 4), y_p90=round(np.percentile(px_y, 90), 4),
                     n_px=int(lit.sum())))
    print(rows[-1], flush=True)

with open('iss_chromaticity.csv', 'w', newline='') as fh:
    wr = csv.DictWriter(fh, list(rows[0])); wr.writeheader(); wr.writerows(rows)
