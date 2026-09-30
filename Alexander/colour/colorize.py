"""Attach an estimated colour and a colour-source code to every tile pixel.

    python colorize.py 2012 2024

Reads   ../globe_v2/tiles/<year>/<z>/<x>/<y>.webp     (greyscale, VIIRS brightness, from tiler.py)
Writes  ../globe_v2/tiles_rgba/<year>/<z>/<x>/<y>.webp (lossless RGBA)
        city_colour_audit.csv                          (one row per city-year actually applied)

Pixel encoding (see METHOD_colour.md):
    R = brightness, unchanged from the greyscale tile
    G = (x - 0.25) / 0.35 * 255      CIE 1931 chromaticity x of the estimated light mix
    B = (y - 0.25) / 0.20 * 255      CIE 1931 chromaticity y
    A = 255 - source_code            0 unknown, 2 inferred city mix, 3 documented city mix (1 = era prior, retired in v2)
"""
import csv, json, math, os, shutil, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GLOBE = os.path.join(HERE, '..', 'globe_v2')
T = 256
D65 = (0.3127, 0.3290)
UNKNOWN_SAT = 0.40                             # unknown colour keeps 40% of the typical chroma
CODE = {'unknown': 0, 'prior': 1, 'inferred': 2, 'documented': 3}
R_SCALE, FEATHER = 1.2, 1.5                    # full weight to 1.2*r_lit, linear fade to 1.5x that
YEAR_CENTRE = {2012: 2012.75, 2024: 2024.5}    # VNL windows: Apr 2012-Mar 2013, Jan-Dec 2024
COMPARED = (2012, 2024)

XY = {r['lamp_class']: (float(r['x']), float(r['y'])) for r in csv.DictReader(open(os.path.join(HERE, 'lamp_class_xy.csv')))}
PRIOR_2012 = XY['HPS']


def typical_unknown_xy():
    """Display colour for 'unknown': midpoint of the median 2012 and median 2024 city mixes, moved
    60% toward D65. Identical in both years, so it cannot create apparent change."""
    per_year = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'city_colour_compositions.csv'))):
        parts = [(XY[p.split(':')[0].strip()], float(p.split(':')[1])) for p in r['composition'].split(';')]
        per_year.setdefault(int(r['year']), []).append(mix_xy(parts))
    med = [np.median(np.array(per_year[y]), axis=0) for y in COMPARED]
    mx, my = (med[0] + med[1]) / 2
    return (D65[0] + UNKNOWN_SAT * (mx - D65[0]), D65[1] + UNKNOWN_SAT * (my - D65[1])), med


NEUTRAL, _MEDIANS = None, None


def mix_xy(parts):
    """Luminance-weighted mixture of chromaticities: sum XYZ at Y = weight, then back to xy."""
    X = Y = Z = 0.0
    for (x, y), w in parts:
        X += w * x / y; Y += w; Z += w * (1 - x - y) / y
    s = X + Y + Z
    return X / s, Y / s


def load_cities(year):
    d = json.load(open(os.path.join(GLOBE, 'cities.json')))
    yi = d['years'].index(year)
    comp = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'city_colour_compositions.csv'))):
        if int(r['year']) == year:
            parts = [(p.split(':')[0].strip(), float(p.split(':')[1])) for p in r['composition'].split(';')]
            comp[r['city']] = (parts, r['colour_confidence'], r['rule'])
    alias = {'Dallas–Fort Worth': 'Dallas', 'São Paulo': 'Sao Paulo'}
    out = []
    for c in d['cities']:
        key = alias.get(c['name'], c['name'])
        if key not in comp: continue
        parts, conf, rule = comp[key]
        xy = mix_xy([(XY[k], w) for k, w in parts])
        # same circle in both compared years (larger lit area), so the edge cannot create change
        lit = max(c['litkm2'][d['years'].index(y)] for y in COMPARED)
        r_km = R_SCALE * math.sqrt(lit / math.pi)
        out.append(dict(city=key, lat=c['lat'], lng=c['lng'], r_km=r_km, x=xy[0], y=xy[1],
                        code=CODE[conf], conf=conf, rule=rule,
                        composition=';'.join(f'{k}:{w}' for k, w in parts)))
    return out


def tile_lonlat(z, tx, ty):
    n = T * 2 ** z
    X = tx * T + np.arange(T) + 0.5
    Y = ty * T + np.arange(T) + 0.5
    lon = X / n * 360 - 180
    lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * Y / n))))
    return np.meshgrid(lon, lat)


def colour_tile(args):
    year, z, tx, ty, cities, neutral = args
    global NEUTRAL
    NEUTRAL = neutral
    src = os.path.join(GLOBE, 'tiles', str(year), str(z), str(tx), f'{ty}.webp')
    v = np.asarray(Image.open(src).convert('L'))
    lon, lat = tile_lonlat(z, tx, ty)
    # Evidence-only rule (v2): outside city circles colour is unknown in every year. The 2012 HPS era
    # prior (v1) is retired from the tiles because it made the 2012|2024 swipe show change that was
    # only a change of rule. PRIOR_2012 is kept for reference.
    bx, by, bcode = NEUTRAL[0], NEUTRAL[1], CODE['unknown']
    x = np.full(v.shape, bx, 'float32'); y = np.full(v.shape, by, 'float32')
    code = np.full(v.shape, bcode, 'uint8')
    for c in cities:
        # equirectangular distance is accurate to <1% at these radii (< 60 km)
        dx = (lon - c['lng']) * math.cos(math.radians(c['lat'])) * 111.32
        dy = (lat - c['lat']) * 110.57
        d = np.hypot(dx, dy)
        r0, r1 = c['r_km'], c['r_km'] * FEATHER
        if d.min() > r1: continue
        w = np.clip((r1 - d) / (r1 - r0), 0, 1).astype('float32')
        if bcode == CODE['prior']:
            # blend the two mixes in XYZ (luminance-weighted), same as mix_xy
            X = w * c['x'] / c['y'] + (1 - w) * x / y
            Z = w * (1 - c['x'] - c['y']) / c['y'] + (1 - w) * (1 - x - y) / y
            s = X + 1 + Z; x, y = X / s, 1 / s
        else:
            # background colour is unknown: fade saturation, never invent a hue
            x = NEUTRAL[0] + w * (c['x'] - NEUTRAL[0]) + (1 - w) * (x - NEUTRAL[0])
            y = NEUTRAL[1] + w * (c['y'] - NEUTRAL[1]) + (1 - w) * (y - NEUTRAL[1])
        code = np.where(w >= 0.5, np.uint8(c['code']), code)
    G = np.clip((x - 0.25) / 0.35 * 255 + .5, 0, 255).astype('uint8')
    B = np.clip((y - 0.25) / 0.20 * 255 + .5, 0, 255).astype('uint8')
    A = (255 - code).astype('uint8')
    out = os.path.join(GLOBE, 'tiles_rgba', str(year), str(z), str(tx))
    os.makedirs(out, exist_ok=True)
    Image.fromarray(np.dstack([v, G, B, A]), 'RGBA').save(os.path.join(out, f'{ty}.webp'), 'WEBP', lossless=True, method=4)


def main(years):
    global NEUTRAL, _MEDIANS
    NEUTRAL, _MEDIANS = typical_unknown_xy()
    print('unknown xy', [round(float(v), 4) for v in NEUTRAL], 'from year medians', [m.round(4).tolist() for m in _MEDIANS], flush=True)
    audit = []
    for year in years:
        cities = load_cities(year)
        for c in cities:
            audit.append(dict(year=year, **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()}))
        root = os.path.join(GLOBE, 'tiles', str(year))
        jobs = []
        for z in sorted(os.listdir(root)):
            if not z.isdigit(): continue
            for tx in os.listdir(os.path.join(root, z)):
                for f in os.listdir(os.path.join(root, z, tx)):
                    jobs.append((year, int(z), int(tx), int(f[:-5]), cities, NEUTRAL))
        with ProcessPoolExecutor(max_workers=8) as ex:
            for i, _ in enumerate(ex.map(colour_tile, jobs, chunksize=64)):
                if i % 10000 == 0: print(year, i, '/', len(jobs), flush=True)
        for f in os.listdir(root):
            if f.startswith('exists_'):
                shutil.copy(os.path.join(root, f), os.path.join(GLOBE, 'tiles_rgba', str(year), f))
        print(year, 'done', len(jobs), 'tiles', flush=True)
    with open(os.path.join(HERE, 'city_colour_audit.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, ['year', 'city', 'composition', 'conf', 'code', 'rule', 'x', 'y', 'r_km', 'lat', 'lng'])
        w.writeheader(); w.writerows(audit)


if __name__ == '__main__':
    main([int(a) for a in sys.argv[1:]])
