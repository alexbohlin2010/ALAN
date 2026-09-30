"""Chromaticity (CIE 1931 xy) of each lamp class, from measured spectra.

Input : ../lamp_class_reference.csv  (class -> member spectrum names, from lamp_classes.py)
        spectra from LICA-UCM / LSPDD / CIE (same files used for melanopic DER)
Output: lamp_class_xy.csv  class, n, x, y, x_iqr, y_iqr, srgb_hex

Each spectrum is truncated to 380-780 nm (the visible range; the 819 nm Na line does not affect
colour), converted to XYZ with the CIE 1931 2-degree observer, and reduced to xy. The class value is
the per-coordinate median across member spectra.
"""
import csv, glob, json, re, warnings
import numpy as np
warnings.filterwarnings('ignore')
import colour

SCR = '/private/tmp/claude-501/-Users-alexander/7625fe9f-c602-45a9-8fc2-7c285e52c493/scratchpad/'
SPEC = '/Users/alexander/alan-streetlight-cct/spectra/'


def lica(name):
    f = glob.glob(SPEC + 'lica/' + name + '_cor*.txt')
    if not f: return None
    pts = []
    for line in open(f[0], encoding='latin-1'):
        p = line.split()
        try: pts.append((float(p[0]), float(p[1])))
        except (ValueError, IndexError): pass
    return np.array(pts)


def lspdd(lamp_id):
    for c in json.load(open(SPEC + f'lspdd/{lamp_id}.json')):
        for sc in c.get('spectral_captures') or []:
            if sc.get('spectral_datas'): return np.array(sc['spectral_datas'], float)


def cie(name):
    sd = colour.SDS_ILLUMINANTS[name]
    return np.c_[sd.wavelengths, sd.values]


def resolve(member):
    member = member.strip()
    if member.startswith('LICA '): return lica(member[5:])
    if member.startswith('LSPDD '): return lspdd(member.split()[1])
    if member.startswith('CIE '): return cie(member[4:])


def xy_of(a):
    wl = np.arange(380, 781, 1.0)
    v = np.clip(np.interp(wl, a[:, 0], a[:, 1], left=0, right=0), 0, None)
    sd = colour.SpectralDistribution(dict(zip(wl, v)))
    return colour.XYZ_to_xy(colour.sd_to_XYZ(sd))


def hex_of(x, y):
    XYZ = colour.xy_to_XYZ([x, y])
    rgb = np.clip(colour.XYZ_to_sRGB(XYZ, apply_cctf_encoding=False), 0, None)
    rgb = colour.cctf_encoding(rgb / rgb.max())
    return '#%02x%02x%02x' % tuple((np.clip(rgb, 0, 1) * 255).round().astype(int))


rows = []
for r in csv.DictReader(open('/Users/alexander/alan-streetlight-cct/lamp_class_reference.csv')):
    xs, ys, used = [], [], []
    for m in r['members'].split(';'):
        a = resolve(m)
        if a is None or len(a) < 50: continue
        x, y = xy_of(a); xs.append(x); ys.append(y); used.append(m.strip())
    if not xs: continue
    x, y = float(np.median(xs)), float(np.median(ys))
    rows.append(dict(lamp_class=r['lamp_class'], n=len(xs), x=round(x, 4), y=round(y, 4),
                     x_iqr=round(float(np.subtract(*np.percentile(xs, [75, 25]))), 4),
                     y_iqr=round(float(np.subtract(*np.percentile(ys, [75, 25]))), 4),
                     srgb_hex=hex_of(x, y), members='; '.join(used)))

with open('lamp_class_xy.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows:
    print(f"{r['lamp_class']:22s} n={r['n']:2d}  x={r['x']:.4f} y={r['y']:.4f}  iqr=({r['x_iqr']:.3f},{r['y_iqr']:.3f})  {r['srgb_hex']}")
