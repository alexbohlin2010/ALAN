"""Regional white share from archive thumbnails -> smooth per-year grid of grey thresholds.

Human request 2026-10-03 (AI_LOG colour steps 22-23): broad-strokes regional distribution of
sodium vs white light, Iberia first, values `estimated`.

1. Per photo (`estimated`): every pool photo's archive thumbnail (data/raw/colour/eol/small/).
   Bright pixels and white rule as in 06_classify_cities.py (brightest channel MIN_BRIGHT..
   MAX_UNSATURATED, linear G/R >= WHITE_GR). Photos with < MIN_PIXELS bright pixels are skipped
   (night, cloud). Only lamp-like pixels count: linear G/R <= MAX_GR and B/G <= MAX_BG, which drops
   green airglow and blue twilight/sun glow seen in wide frames. White = linear G/R >= WHITE_GR
   AND B/R >= MIN_WHITE_BR: some photos render sodium yellow (G/R >= 0.8) but with little blue
   (agent check, step 24: yellow sodium B/R ~0.41, white B/R ~0.56-0.77) (agent check of thumbnails,
   AI_LOG colour step 23). Only lenses >= MIN_FOCAL_MM: wider frames show the horizon and their
   record point is far from the lights they show. Location = the record's lat/lon in <pilot>_records.csv (human centre point,
   or the ML record's point, which may be the station nadir). -> <pilot>_thumb_shares.csv
   Photos with exclude = 1 in <pilot>_frame_flags.csv (14_frame_flags.py: twilight/day or bright
   frame, not a city frame) are left out of steps 2 and 4 (human 2026-10-03, AI_LOG colour steps
   42, 45). No flag file (e.g. iberia): all photos are used.
   Share used in steps 2 and 4 (SHARE_SOURCE, per pilot): "gr" = the white share above; "cct" =
   white_share of <pilot>_thumb_cct.csv (12_thumb_cct.py: the archive's conversion white balance
   undone, lamp pixels >= 2,700 K; checked against NEF raw files, AI_LOG colour step 44). Global:
   "cct" (human 2026-10-03, "fix 2025 color", step 45); photos without a CCT value are left out.
2. Grid (`estimated`): STEP_DEG cells over the region (--pilot; edges snapped to STEP_DEG).
   Share = Gaussian-weighted median of photo shares (so one photo with an odd colour balance cannot
   set a cell) (sigma SIGMA_DEG, distance in degrees with longitude scaled by cos lat at the cell;
   photos beyond CUT_SIGMA sigma ignored). Coverage = 1 - exp(-sum of weights / W_FULL), 0..1.
3. Threshold (`inferred`): the (1 - share) quantile (method "lower", integer grey) of display grey
   of lit pixels (radiance > 0) in the (2 WINDOW_CELLS + 1)^2 cells around the cell in that year's
   COG (+-0.625 deg; human 2026-10-03, was +-0.5 deg), so the brightest `share` of the local lit
   pixels are drawn white. Built from one pass over the COG: a 256-bin grey histogram per cell,
   summed over the window (lights up to the window width outside the region count too).
   Fewer than MIN_LIT lit pixels, or no photo within CUT_SIGMA: threshold 0, coverage 0.
3b. Regional fallback (human 2026-10-03, "regional fallback", AI_LOG colour step 47; REGIONAL per
   pilot, global only): the same Gaussian-weighted median on a REGION_STEP_DEG grid with sigma
   REGION_SIGMA_DEG (cut REGION_CUT_SIGMA sigma), coverage 1 - exp(-W / W_FULL), each 0.25 deg cell
   taking its coarse cell's values. Per cell: share = (cov_l * share_l + (1 - cov_l) * cov_r * share_r)
   / cov, cov = cov_l + (1 - cov_l) * cov_r. The written coverage is cov, so the shader uses the
   global fallback (4) only for what neither the local nor the regional share covers.
4. Fallback (human 2026-10-03, global run): white share = median of all photo shares of the year
   (`estimated`); threshold = its (1 - share) grey quantile over all lit pixels of the region (`inferred`).
   FALLBACK_SHARE (per pilot and epoch) replaces the photo median where set. Global 2025 (human
   2026-10-03, "option 1", AI_LOG colour step 54): 0.410 = 1 - sodium-vapour share of Brazil's public
   lighting points (59.0 %, ABCIP census, ANEEL base 2023, Table 9; data/raw/colour/
   Censo-Iluminacao-Publica-Brasil.pdf). Brazil is the largest country the 2025 fallback paints.
   `estimated` (one country's documented value used for all fallback regions).
The shader blends each cell's threshold with the fallback by coverage.
5. Share PNG (human 2026-10-04, "prototype B and C", AI_LOG colour step 64; display prototype): the
   cell white share of step 2/3b (`estimated`) as <pilot>_white_share_values.png, R/G = share 2015/2025
   x 255 (0 where coverage is 0 or < MIN_LIT lit pixels), B/A = coverage as in the grid PNG. Used by the
   app's prototype colour modes (share by place, blend by share), which need the share, not the threshold.
Writes data/derived/colour/<pilot>_white_share_grid.png (R/G = threshold 2015/2025, B/A = coverage
2015/2025 x 255, row 0 = north) and <pilot>_white_share_grid.json (extent, parameters, fallbacks).
Note: iberia_white_share_grid.json (Iberia, AI_LOG colour step 24) came from the earlier version of
this script (one COG window read per cell, +-0.5 deg, JSON arrays) and was not rerun.
Run from final/:  .venv/bin/python pipeline/colour/10_white_share_grid.py --pilot global
"""
import csv, importlib, json
import numpy as np
from osgeo import gdal
from config import *

gdal.UseExceptions()
cr = importlib.import_module("04_colour_ratios")
ramp = importlib.import_module("09_display_ramp")

MIN_PIXELS = 200      # bright lamp-like thumbnail pixels needed to use a photo
MIN_FOCAL_MM = 50
MAX_GR = 1.3          # above: greenish (airglow), not a lamp
MAX_BG = 1.2          # above: bluish (twilight, sun glow), not a lamp
MIN_WHITE_BR = 0.5    # white pixels also need this much blue (linear B/R)
STEP_DEG = 0.25
SIGMA_DEG = 0.5
W_FULL = 2.0          # summed kernel weight at which coverage reaches 1 - 1/e
WINDOW_CELLS = 2      # threshold window: (2k+1)^2 cells = +-0.625 deg (human 2026-10-03, was +-0.5 deg)
CUT_SIGMA = 5         # photos beyond 5 sigma (weight < 4e-6) are ignored
MIN_LIT = 50
REGIONAL = {"global": True}.get(PILOT, False)
REGION_STEP_DEG = 1.0
REGION_SIGMA_DEG = 5.0
REGION_CUT_SIGMA = 3
SHARE_SOURCE = {"global": "cct"}.get(PILOT, "gr")
FALLBACK_SHARE = {"global": {2025: 0.410}}.get(PILOT, {})   # see docstring step 4
FALLBACK_SOURCE = {"global": {2025: "1 - sodium-vapour share (59.0 %) of Brazil's public lighting points, "
                               "ABCIP Censo da Iluminacao Publica Brasil, base 2023 (ANEEL), Table 9, publ. Sept 2024"}
                   }.get(PILOT, {})

def thumb_share(pid):
    a = gdal.Open(str(RAW_DIR / "small" / f"{pid}.JPG")).ReadAsArray().astype(np.float32)
    if a.ndim != 3: return 0, None
    mx = a.max(0)
    m = (mx >= cr.MIN_BRIGHT) & (mx <= cr.MAX_UNSATURATED)
    r, g, b = (cr.srgb_to_linear(a[k][m]) for k in range(3))
    ok = (r > 0) & (g > 0)
    gr, bg, br = g[ok] / r[ok], b[ok] / g[ok], b[ok] / r[ok]
    lamp = (gr <= MAX_GR) & (bg <= MAX_BG)
    gr, br = gr[lamp], br[lamp]
    return int(gr.size), (float(((gr >= WHITE_GR) & (br >= MIN_WHITE_BR)).mean()) if gr.size else None)

def wmedian(v, w):
    o = np.argsort(v); c = np.cumsum(w[o])
    return float(v[o][np.searchsorted(c, c[-1] / 2)])

def photo_shares():
    rows = [r for r in csv.DictReader(open(DERIVED / f"{PILOT}_records.csv"))
            if r["in_pool"] == "1" and r["epoch"] and float(r["focal_mm"] or 0) >= MIN_FOCAL_MM]
    out = []
    for r in rows:
        if not (RAW_DIR / "small" / f"{r['photo_id']}.JPG").exists(): continue
        n, s = thumb_share(r["photo_id"])
        out.append(dict(photo_id=r["photo_id"], date=r["date"], epoch=r["epoch"], lat=r["lat"], lon=r["lon"],
                        focal_mm=r["focal_mm"], record_type=r["record_type"], bright_pixels=n,
                        white_share=round(s, 4) if s is not None and n >= MIN_PIXELS else "",
                        label="estimated" if s is not None and n >= MIN_PIXELS else "",
                        note="" if n >= MIN_PIXELS else f"skipped: < {MIN_PIXELS} bright pixels"))
    with open(DERIVED / f"{PILOT}_thumb_shares.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    return out

def grid_cells():
    """Cell edges: STEP_DEG cells covering BBOX (outer edges snapped outward to STEP_DEG)."""
    w = np.floor(BBOX["left_lon"] / STEP_DEG) * STEP_DEG; e = np.ceil(BBOX["right_lon"] / STEP_DEG) * STEP_DEG
    s = np.floor(BBOX["lower_lat"] / STEP_DEG) * STEP_DEG; n = np.ceil(BBOX["upper_lat"] / STEP_DEG) * STEP_DEG
    return w, n, e, s, int(round((e - w) / STEP_DEG)), int(round((n - s) / STEP_DEG))

def photo_grid(plat, plon, pval, w0, n0, nx, ny, STEP_DEG=STEP_DEG, SIGMA_DEG=SIGMA_DEG, CUT_SIGMA=CUT_SIGMA):
    """Gaussian-weighted median share and summed weight per cell; photos beyond CUT_SIGMA ignored."""
    cj, ci, cv, cw = [], [], [], []
    r = int(np.ceil(CUT_SIGMA * SIGMA_DEG / STEP_DEG))
    wrap = abs(nx * STEP_DEG - 360) < 1e-9
    for la, lo, v in zip(plat, plon, pval):
        j0 = int((n0 - la) / STEP_DEG); i0 = int((lo - w0) / STEP_DEG)
        rl = int(np.ceil(r / max(np.cos(np.radians(abs(la) + CUT_SIGMA * SIGMA_DEG)), 0.2)))
        jj, ii = np.mgrid[max(j0 - r, 0):min(j0 + r + 1, ny), i0 - rl:i0 + rl + 1]
        jj, ii = jj.ravel(), ii.ravel()
        if wrap: ii = ii % nx
        else: m = (ii >= 0) & (ii < nx); jj, ii = jj[m], ii[m]
        clat = n0 - (jj + 0.5) * STEP_DEG; clon = w0 + (ii + 0.5) * STEP_DEG
        dlon = (clon - lo + 180) % 360 - 180
        d2 = (la - clat) ** 2 + (dlon * np.cos(np.radians(clat))) ** 2
        k = d2 <= (CUT_SIGMA * SIGMA_DEG) ** 2
        cj.append(jj[k]); ci.append(ii[k]); cv.append(np.full(k.sum(), v)); cw.append(np.exp(-0.5 * d2[k] / SIGMA_DEG ** 2))
    share = np.zeros((ny, nx)); W = np.zeros((ny, nx))
    if not cj: return share, W
    cell = np.concatenate(cj) * nx + np.concatenate(ci); v = np.concatenate(cv); w = np.concatenate(cw)
    o = np.lexsort((v, cell)); cell, v, w = cell[o], v[o], w[o]
    starts = np.r_[0, np.flatnonzero(np.diff(cell)) + 1]
    tot = np.add.reduceat(w, starts); cs = np.cumsum(w)
    base = np.r_[0, cs[starts[1:] - 1]]
    # weighted median: first value in each cell where cumulative weight reaches half the cell total
    idx = np.searchsorted(cs, base + tot / 2)
    idx = np.minimum(np.maximum(idx, starts), np.r_[starts[1:], len(v)] - 1)
    share.flat[cell[starts]] = v[idx]; W.flat[cell[starts]] = tot
    return share, W

def grey_hist(year, curve, w0, n0, nx, ny):
    """256-bin display-grey histogram of lit pixels (radiance > 0) per cell, one pass over the COG."""
    ds = gdal.Open(str(ramp.COG).format(year=year)); band = ds.GetRasterBand(1)
    x0, dx, _, y0, _, dy = ds.GetGeoTransform()
    H = np.zeros(ny * nx * 256, np.int32)
    lon = x0 + (np.arange(ds.RasterXSize) + 0.5) * dx
    ci_all = np.floor((lon - w0) / STEP_DEG).astype(int)
    in_lon = (ci_all >= 0) & (ci_all < nx); ci_all = np.clip(ci_all, 0, nx - 1)
    r0 = max(int((y0 - n0) / -dy), 0); r1 = min(int(np.ceil((y0 - (n0 - ny * STEP_DEG)) / -dy)), ds.RasterYSize)
    for a in range(r0, r1, 480):
        v = band.ReadAsArray(0, a, ds.RasterXSize, min(480, r1 - a))
        rr, cc = np.nonzero(v > 0)
        lat = y0 + (a + rr + 0.5) * dy
        cj = np.floor((n0 - lat) / STEP_DEG).astype(int); ok = (cj >= 0) & (cj < ny) & in_lon[cc]
        if not ok.any(): continue
        g = ramp.grey(v[rr[ok], cc[ok]], curve).astype(np.int64)
        j0, j1 = cj[ok].min(), cj[ok].max() + 1
        idx = ((cj[ok] - j0) * nx + ci_all[cc[ok]]) * 256 + g
        H[j0 * nx * 256:j1 * nx * 256] += np.bincount(idx, minlength=(j1 - j0) * nx * 256).astype(np.int32)
    return H.reshape(ny, nx, 256)

def box_sum(H, k):
    """Sum over (2k+1) x (2k+1) neighbouring cells; longitude wraps on a 360 deg grid, latitude never."""
    out = H.copy()
    wrap = abs(H.shape[1] * STEP_DEG - 360) < 1e-9
    for d in range(1, k + 1):
        if wrap: out += np.roll(H, d, 1) + np.roll(H, -d, 1)
        else: out[:, d:] += H[:, :-d]; out[:, :-d] += H[:, d:]
    t = out.copy()
    for d in range(1, k + 1):
        out[d:] += t[:-d]; out[:-d] += t[d:]
    return out

def window_hist(year, curve, w0, n0, nx, ny):
    """Windowed histograms per cell (lit pixels up to WINDOW_CELLS beyond the grid edge count too),
    and the grid's own per-cell histograms."""
    k = WINDOW_CELLS; wrap = abs(nx * STEP_DEG - 360) < 1e-9; kx = 0 if wrap else k
    Hp = grey_hist(year, curve, w0 - kx * STEP_DEG, n0 + k * STEP_DEG, nx + 2 * kx, ny + 2 * k)
    Hs = box_sum(Hp, k)[k:k + ny, kx:kx + nx]
    return Hs, Hp[k:k + ny, kx:kx + nx]

def quantile_from_hist(h, q):
    """np.quantile(..., method='lower')-style level for each row of an (n, 256) histogram."""
    c = np.cumsum(h, 1); n = c[:, -1]
    target = np.floor(q * (n - 1))
    return np.argmax(c > target[:, None], 1)

def main():
    shares = photo_shares()
    ff = DERIVED / f"{PILOT}_frame_flags.csv"
    excl = {r["photo_id"] for r in csv.DictReader(open(ff)) if r["exclude"] == "1"} if ff.exists() else set()
    if SHARE_SOURCE == "cct":
        cct = {r["photo_id"]: r["white_share"] for r in csv.DictReader(open(DERIVED / f"{PILOT}_thumb_cct.csv"))}
        shares = [dict(s, white_share=float(cct[s["photo_id"]]) if cct.get(s["photo_id"]) else "") for s in shares]
    curve = json.loads(ramp.CURVE.read_text())
    w0, n0, e0, s0, nx, ny = grid_cells()
    meta = dict(extent=dict(west=w0, north=n0, east=e0, south=s0), step_deg=STEP_DEG, nx=nx, ny=ny,
                png=f"{PILOT}_white_share_grid.png", share_png=f"{PILOT}_white_share_values.png",
                share_png_channels="R = white share 2015 x 255, G = white share 2025 x 255, B/A = coverage as png "
                                   "(display prototype, human 2026-10-04)",
                png_channels="R = grey threshold 2015, G = grey threshold 2025, B = coverage 2015 x 255, "
                             "A = coverage 2025 x 255; row 0 = north; cells without photos: 0",
                params=dict(MIN_PIXELS=MIN_PIXELS, MIN_FOCAL_MM=MIN_FOCAL_MM, MAX_GR=MAX_GR, MAX_BG=MAX_BG,
                            MIN_WHITE_BR=MIN_WHITE_BR, SIGMA_DEG=SIGMA_DEG, CUT_SIGMA=CUT_SIGMA, W_FULL=W_FULL,
                            WINDOW_CELLS=WINDOW_CELLS, MIN_LIT=MIN_LIT, WHITE_GR=WHITE_GR, REGIONAL=REGIONAL,
                            REGION_STEP_DEG=REGION_STEP_DEG, REGION_SIGMA_DEG=REGION_SIGMA_DEG,
                            REGION_CUT_SIGMA=REGION_CUT_SIGMA),
                labels=dict(white_share="estimated", coverage="inferred", grey_threshold="inferred",
                            fallback_white_share="estimated", fallback_grey_threshold="inferred"),
                frame_flags=ff.name if ff.exists() else None,
                share_source=SHARE_SOURCE + (f" ({PILOT}_thumb_cct.csv white_share)" if SHARE_SOURCE == "cct" else ""),
                note="human request 2026-10-03; see pipeline/colour/METHOD.md", epochs={})
    png = np.zeros((4, ny, nx), np.uint8); spng = np.zeros((4, ny, nx), np.uint8)
    for k, ep in enumerate(EPOCHS):
        u = [s for s in shares if s["epoch"] == str(ep) and s["white_share"] != ""]
        p = [s for s in u if s["photo_id"] not in excl]
        plat = np.array([float(s["lat"]) for s in p]); plon = np.array([float(s["lon"]) for s in p])
        pval = np.array([s["white_share"] for s in p])
        share, W = photo_grid(plat, plon, pval, w0, n0, nx, ny)
        cov_l = 1 - np.exp(-W / W_FULL)
        if REGIONAL:
            f = int(round(REGION_STEP_DEG / STEP_DEG))
            rs, rW = photo_grid(plat, plon, pval, w0, n0, -(-nx // f), -(-ny // f),
                                REGION_STEP_DEG, REGION_SIGMA_DEG, REGION_CUT_SIGMA)
            rs = np.repeat(np.repeat(rs, f, 0), f, 1)[:ny, :nx]; rW = np.repeat(np.repeat(rW, f, 0), f, 1)[:ny, :nx]
            cov_r = 1 - np.exp(-rW / W_FULL)
            cov_t = cov_l + (1 - cov_l) * cov_r
            share = np.where(cov_t > 0, (cov_l * share + (1 - cov_l) * cov_r * rs) / np.maximum(cov_t, 1e-12), 0)
        else:
            cov_t = cov_l
        Hs, H = window_hist(ep, curve, w0, n0, nx, ny)
        allh = H.sum((0, 1))
        photo_median = float(np.median(pval))
        fb_share = FALLBACK_SHARE.get(ep, photo_median); fb_thr = int(quantile_from_hist(allh[None], 1 - fb_share)[0])
        sel = np.flatnonzero((cov_t.ravel() >= 5e-7) & (Hs.reshape(-1, 256).sum(1) >= MIN_LIT))
        thr = np.zeros(ny * nx); cov = np.zeros(ny * nx)
        thr[sel] = quantile_from_hist(Hs.reshape(-1, 256)[sel], 1 - share.ravel()[sel])
        cov[sel] = cov_t.ravel()[sel]
        png[k] = thr.reshape(ny, nx); png[2 + k] = np.round(255 * cov).reshape(ny, nx)
        sh = np.zeros(ny * nx); sh[sel] = share.ravel()[sel]
        spng[k] = np.round(255 * sh).reshape(ny, nx); spng[2 + k] = png[2 + k]
        meta["epochs"][str(ep)] = dict(photos_used=len(p), photos_flagged_out=len(u) - len(p), fallback_white_share=round(fb_share, 4),
                                       fallback_source=FALLBACK_SOURCE.get(ep, "median of photo shares"),
                                       photo_share_median=round(photo_median, 4),
                                       fallback_grey_threshold=fb_thr, lit_pixels=int(allh.sum()),
                                       cells_coverage_gt_0_5=int((cov > 0.5).sum()))
        print(ep, "photos", len(p), "photo median", round(photo_median, 4), "fallback share", round(fb_share, 4), "fallback grey", fb_thr,
              "cells covered>0.5", int((cov > 0.5).sum()), "of", cov.size, flush=True)
        del H, Hs
    drv = gdal.GetDriverByName("MEM").Create("", nx, ny, 4, gdal.GDT_Byte)
    for b in range(4): drv.GetRasterBand(b + 1).WriteArray(png[b])
    gdal.GetDriverByName("PNG").CreateCopy(str(DERIVED / meta["png"]), drv)
    drv = gdal.GetDriverByName("MEM").Create("", nx, ny, 4, gdal.GDT_Byte)
    for b in range(4): drv.GetRasterBand(b + 1).WriteArray(spng[b])
    gdal.GetDriverByName("PNG").CreateCopy(str(DERIVED / meta["share_png"]), drv)
    (DERIVED / f"{PILOT}_white_share_grid.json").write_text(json.dumps(meta, indent=1))
    print("wrote", meta["png"], f"{PILOT}_white_share_grid.json")

if __name__ == "__main__":
    main()
