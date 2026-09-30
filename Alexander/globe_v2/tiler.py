"""Cut VNL v2.1 annual rasters (86400 x 35849, 15 arc-sec) into Web Mercator XYZ tiles.

    python tiler.py 2024 [--zmax 9] [--out tiles]

- Radiance: apply each file's own `scales` tag, then /10 -> nW/cm2/sr (see HANDOFF: 2022-24 are
  packed differently; internal overviews are unusable, so everything is read at full resolution).
- Aurora (7 events, 2012/2023/2024) is replaced inside each event bbox by the per-pixel median
  across the 13 years, at native resolution, using the coarse mask from the v1 globe session.
- z7-z9 are resampled straight from native pixels (area-mean when shrinking, nearest when
  enlarging); z0-z6 from a float 4x box-mean master. Means are taken in linear radiance.
- Colour: neutral greyscale. The data has one scalar per pixel; any hue would be invented.
- Tiles whose pixels are all ~black are not written; exists_<year>_z<z>.bin is a bitmask of
  written tiles so the client never requests a missing tile.
"""
import argparse, os, time
import numpy as np, rasterio
from rasterio.windows import Window
from PIL import Image

YEARS = list(range(2012, 2025))
KNEE, GAMMA, HI = 0.12, 0.62, None   # HI fixed across years, set in main()
VNL = os.path.expanduser('~/alan-streetlight-cct/vnl/vnl_{y}.tif')
AURORA_MASK = os.path.expanduser('~/alan-streetlight-cct/globe_v1/aurora_mask.npy')  # (13, 1793, 4320)
EVENTS = [  # year, lat_min, lat_max, lon_min, lon_max  (aurora_events.csv, padded 0.5 deg)
    (2012, 52.26, 55.25, -70.96, -64.29), (2023, 61.0, 62.67, -149.62, -147.29),
    (2023, 59.09, 60.25, -136.21, -133.12), (2024, 50.59, 51.59, -59.46, -57.79),
    (2023, 51.09, 51.67, -56.71, -55.54), (2024, 67.83, 68.33, 70.62, 71.88),
    (2023, 67.33, 67.75, 31.29, 32.38)]
T = 256


class Source:
    def __init__(self, year):
        self.year = year
        self.s = rasterio.open(VNL.format(y=year))
        self.W, self.H = self.s.width, self.s.height
        self.top, self.res = self.s.bounds.top, self.s.res[0]
        self.scale, self.nd = self.s.scales[0], self.s.nodata
        self.patches = self._aurora_patches()

    def _aurora_patches(self):
        """Native-res replacement arrays for this year's aurora events: {(r0,c0): (mask, median)}."""
        out = {}
        evs = [e for e in EVENTS if e[0] == self.year]
        if not evs: return out
        coarse = np.load(AURORA_MASK)[YEARS.index(self.year)]   # factor 20 grid
        F = 20
        for _, la0, la1, lo0, lo1 in evs:
            r0 = max(0, int((self.top - (la1 + .5)) / self.res)); r1 = min(self.H, int((self.top - (la0 - .5)) / self.res))
            c0 = max(0, int((lo0 - .5 + 180) / self.res)); c1 = min(self.W, int((lo1 + .5 + 180) / self.res))
            win = Window(c0, r0, c1 - c0, r1 - r0)
            stack = []
            for y in YEARS:
                with rasterio.open(VNL.format(y=y)) as o:
                    a = o.read(1, window=win).astype('float32')
                    a[a == o.nodata] = 0; a *= o.scales[0] / 10; a[a < 0] = 0
                    stack.append(a)
            med = np.median(np.stack(stack), axis=0)
            rr = (np.arange(r0, r1) // F).clip(0, coarse.shape[0] - 1)
            cc = (np.arange(c0, c1) // F).clip(0, coarse.shape[1] - 1)
            m = coarse[np.ix_(rr, cc)]
            out[(r0, c0)] = (m, med)
        return out

    def read_rows(self, r0, r1):
        """Float radiance for source rows [r0, r1), full width, aurora-cleaned."""
        r0, r1 = max(0, r0), min(self.H, r1)
        if r1 <= r0: return np.zeros((0, self.W), 'float32'), r0
        a = self.s.read(1, window=Window(0, r0, self.W, r1 - r0)).astype('float32')
        a[a == self.nd] = 0; a *= self.scale / 10; a[a < 0] = 0
        for (pr0, pc0), (m, med) in self.patches.items():
            ir0, ir1 = max(r0, pr0), min(r1, pr0 + m.shape[0])
            if ir1 <= ir0: continue
            sub = slice(ir0 - pr0, ir1 - pr0); cs = slice(pc0, pc0 + m.shape[1])
            blk = a[ir0 - r0:ir1 - r0, cs]
            a[ir0 - r0:ir1 - r0, cs] = np.where(m[sub], med[sub], blk)
        return a, r0


def merc_lat_edges(z, ty):
    """Latitudes of the 257 pixel-row edges of tile row ty at zoom z."""
    n = T * 2 ** z
    Y = ty * T + np.arange(T + 1)
    return np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * Y / n))))


def reduce_axis(a, edges, axis):
    """Mean over [edges[i], edges[i+1]) along axis; when a bin is empty, take the nearest cell."""
    edges = np.clip(edges, 0, a.shape[axis] - 1)
    lo = edges[:-1]; hi = np.maximum(edges[1:], lo + 1)
    cnt = (hi - lo).astype('float32')
    cs = np.cumsum(a, axis=axis, dtype='float64')
    cs = np.concatenate([np.zeros_like(np.take(cs, [0], axis=axis)), cs], axis=axis)
    s = (np.take(cs, hi, axis=axis) - np.take(cs, lo, axis=axis)).astype('float32')
    shape = [1] * a.ndim; shape[axis] = -1
    return s / cnt.reshape(shape)


def to_grey(v):
    g = np.clip(np.log1p(v / KNEE) / HI, 0, 1) ** GAMMA
    return (g * 255 + 0.5).astype('uint8')


def write_row(tiles_row, z, ty, out, year, exists):
    """tiles_row: (256, 256*2^z) float radiance -> tiles; skip ~black ones."""
    g = to_grey(tiles_row)
    n = 2 ** z
    for tx in range(n):
        t = g[:, tx * T:(tx + 1) * T]
        if t.max() <= 2: continue
        d = f'{out}/{year}/{z}/{tx}'
        os.makedirs(d, exist_ok=True)
        Image.fromarray(t, 'L').save(f'{d}/{ty}.webp', 'WEBP', lossless=True, method=4)
        exists[ty * n + tx] = 1


def native_level(src, z, out):
    n = 2 ** z
    exists = np.zeros(n * n, 'uint8')
    col_edges = np.round(np.arange(T * n + 1) * src.W / (T * n)).astype(int)
    for ty in range(n):
        lat = merc_lat_edges(z, ty)
        redges = np.floor((src.top - lat) / src.res).astype(int)
        a, r0 = src.read_rows(redges[0], redges[-1] + 1)
        if a.shape[0] == 0: continue
        valid = (redges >= 0) & (redges <= src.H)
        if not valid.any(): continue
        rows = reduce_axis(a, redges - r0, 0)
        rows[~(valid[:-1] & valid[1:])] = 0
        tile_row = reduce_axis(rows, col_edges, 1)
        write_row(tile_row, z, ty, out, src.year, exists)
    return exists


def master(src, F=4):
    """Float box-mean at 1/F resolution (21600 x 8963 for F=4)."""
    oh = -(-src.H // F); ow = src.W // F
    m = np.zeros((oh, ow), 'float32')
    for r in range(0, oh, 256):
        r1 = min(r + 256, oh)
        a, _ = src.read_rows(r * F, r1 * F)
        pad = (r1 - r) * F - a.shape[0]
        if pad > 0: a = np.vstack([a, np.zeros((pad, src.W), 'float32')])
        m[r:r1] = a.reshape(r1 - r, F, ow, F).mean(axis=(1, 3))
    return m


def master_level(m, top, res, z, out, year):
    n = 2 ** z
    exists = np.zeros(n * n, 'uint8')
    H, W = m.shape
    col_edges = np.round(np.arange(T * n + 1) * W / (T * n)).astype(int)
    for ty in range(n):
        lat = merc_lat_edges(z, ty)
        redges = np.floor((top - lat) / res).astype(int)
        valid = (redges >= 0) & (redges <= H)
        if not valid.any(): continue
        lo, hi = max(0, redges.min()), min(H, redges.max() + 1)
        rows = reduce_axis(m[lo:hi], redges - lo, 0)
        rows[~(valid[:-1] & valid[1:])] = 0
        write_row(reduce_axis(rows, col_edges, 1), z, ty, out, year, exists)
    return exists


def main():
    global HI
    p = argparse.ArgumentParser()
    p.add_argument('year', type=int); p.add_argument('--zmax', type=int, default=9)
    p.add_argument('--zmin_native', type=int, default=7); p.add_argument('--out', default='tiles')
    p.add_argument('--hi', type=float, default=8.3)
    a = p.parse_args()
    HI = a.hi
    t0 = time.time()
    src = Source(a.year)
    print(f'{a.year}: aurora patches {len(src.patches)}', flush=True)
    m = master(src)
    print(f'  master {m.shape} {time.time()-t0:.0f}s', flush=True)
    for z in range(0, a.zmin_native):
        ex = master_level(m, src.top, src.res * 4, z, a.out, a.year)
        np.packbits(ex).tofile(f'{a.out}/{a.year}/exists_z{z}.bin')
        print(f'  z{z}: {int(ex.sum())} tiles {time.time()-t0:.0f}s', flush=True)
    del m
    for z in range(a.zmin_native, a.zmax + 1):
        ex = native_level(src, z, a.out)
        np.packbits(ex).tofile(f'{a.out}/{a.year}/exists_z{z}.bin')
        print(f'  z{z}: {int(ex.sum())} tiles {time.time()-t0:.0f}s', flush=True)
    print(f'done {a.year} {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
