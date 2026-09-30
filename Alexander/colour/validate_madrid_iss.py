"""Consistency check of the estimated colour layer against calibrated ISS photographs of Madrid.

Frames (Sánchez de Miguel et al., Zenodo 10.5281/zenodo.6638505, CC-BY-4.0; calibrated, rectified):
  2012  iss030e082053  (Expedition 30, early 2012, ~43 m px)   pre2013.zip
  2014  iss042e183298  (Expedition 42, ~2014/15, ~250 m px)     post2013.zip
  2019  iss061e035301  (Expedition 61, ~late 2019/early 2020, ~390 m px) post2013.zip
Channels: R1 (red), G2 (green), B4 (blue) of the DSLR, calibrated per the Zenodo record.

Metric: G/R and B/G channel ratios of lit pixels within the Madrid colour circle (r = 28.8 km used for
2024 in city_colour_audit.csv), radiance-weighted. White LED raises both ratios relative to HPS. This
is a *relative* check (direction and size of change within one city and one camera model family),
not an absolute calibration of the xy estimate: the camera's spectral sensitivities are not available
here to convert ratios to CIE xy.
"""
import csv, math, os
import numpy as np, rasterio
from rasterio.windows import from_bounds

os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_USE_HEAD='NO')
Z = 'https://zenodo.org/records/6638505/files/{}?download=1'
FRAMES = [('2012', 'pre2013.zip', 'iss030e082053'), ('2014-15', 'post2013.zip', 'iss042e183298'),
          ('2019-20', 'post2013.zip', 'iss061e035301')]
LAT, LON, R_KM = 40.42, -3.70, 28.8
dlat = R_KM / 110.57; dlon = R_KM / (111.32 * math.cos(math.radians(LAT)))
BOX = (LON - dlon, LAT - dlat, LON + dlon, LAT + dlat)


def read(zipname, frame, ch):
    p = f'inputs/iss/Corr_{frame}{ch}F.cal2N.Ao2_rect.tiff'   # extracted from {zipname}
    with rasterio.open(p) as s:
        w = from_bounds(*BOX, transform=s.transform)
        a = s.read(1, window=w, boundless=True, fill_value=np.nan).astype('float64')
        t = s.window_transform(w)
    return a, t


rows = []
for label, zipname, frame in FRAMES:
    R, t = read(zipname, frame, 'R1'); G, _ = read(zipname, frame, 'G2'); B, _ = read(zipname, frame, 'B4')
    h, w = R.shape
    ys, xs = np.mgrid[0:h, 0:w]
    lon = t.c + (xs + .5) * t.a; lat = t.f + (ys + .5) * t.e
    d = np.hypot((lon - LON) * 111.32 * math.cos(math.radians(LAT)), (lat - LAT) * 110.57)
    ok = np.isfinite(R) & np.isfinite(G) & np.isfinite(B) & (d <= R_KM)
    lit = ok & (R > np.nanpercentile(R[ok], 50))            # brighter half of in-circle pixels
    wgt = R[lit]
    gr = np.sum(G[lit]) / np.sum(R[lit]); bg = np.sum(B[lit]) / np.sum(G[lit])
    q = np.percentile(G[lit] / R[lit], [10, 50, 90])
    rows.append(dict(period=label, frame=frame, px=int(lit.sum()), px_deg=round(abs(t.a), 5),
                     GR_weighted=round(gr, 4), BG_weighted=round(bg, 4),
                     GR_p10=round(q[0], 4), GR_p50=round(q[1], 4), GR_p90=round(q[2], 4)))
    print(rows[-1], flush=True)

with open('validation_madrid_iss.csv', 'w', newline='') as fh:
    wr = csv.DictWriter(fh, list(rows[0])); wr.writeheader(); wr.writerows(rows)
