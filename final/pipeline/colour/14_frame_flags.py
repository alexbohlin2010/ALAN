"""Per-photo flags for frames that should not count as night city photos (human 2026-10-03, AI_LOG
colour steps 39-40: option D = sun elevation OR brightness).

Why: the archive's `nighttime` query filter let daytime frames into the pool (AI_LOG colour step 37),
and the pool also holds night frames that are not city lights (aurora, moonlit cloud, lightning;
agent viewed 5 random examples, step 39).

Per photo of <pilot>_thumb_shares.csv (thumbnail in data/raw/colour/eol/small/):
1. sun_elev_deg (`inferred`): solar elevation at the camera's EXIF DateTimeOriginal (read as UTC) and
   the record's lat/lon (centre point, or the ML record's point). NOAA solar-position equations
   (Meeus, Astronomical Algorithms; NOAA Global Monitoring Laboratory solar calculator), no
   refraction correction. Check (step 39): from the page's nadir point this reproduces the
   archive's "Sun Elevation Angle" on all 89 saved photo pages (|diff| median 0.3, max 0.7 deg).
   It inherits wrong camera clocks: ISS041 daytime frames come out below -40 deg.
2. thumb_median (`inferred`): median over pixels of the brightest channel (0-255, sRGB as stored).
3. Flags (agent rules, not validated):
   twilight_or_day = sun_elev_deg >= MAX_SUN_DEG (astronomical twilight starts at -12 deg);
   bright_frame = thumb_median >= MAX_MEDIAN (daytime with a wrong clock, aurora, moonlit cloud);
   Missing EXIF time: sun_elev_deg empty, only the brightness flag applies.
4. city_frame (human 2026-10-03, "fix 2025 color", AI_LOG colour steps 44-45; agent rule tuned on 30
   labelled 2025 frames, checked on 90 more by eye): the pool holds photos of the Moon, lightning,
   moonlit cloud, aurora and horizons. City lights are small points; these are smooth areas.
   Lamp-like pixel = the grid's rule (10_white_share_grid.py: brightest channel MIN_BRIGHT..
   MAX_UNSATURATED, linear G/R <= MAX_GR, B/G <= MAX_BG). Point-like = brightest channel >=
   POINT_RATIO x its POINT_BOX x POINT_BOX box mean. city_frame = point_pixels >= MIN_POINT_PIXELS
   AND point_frac >= MIN_POINT_FRAC.
exclude = twilight_or_day OR bright_frame OR NOT city_frame.
Writes data/derived/colour/<pilot>_frame_flags.csv.
Run from final/:  .venv/bin/python pipeline/colour/14_frame_flags.py --pilot global
"""
import csv, datetime as dt, importlib, math, struct
import numpy as np
from osgeo import gdal
from config import *

gdal.UseExceptions()
cr = importlib.import_module("04_colour_ratios")
grid = importlib.import_module("10_white_share_grid")
MAX_SUN_DEG = -12.0
MAX_MEDIAN = 40
POINT_BOX, POINT_RATIO = 15, 2.0
MIN_POINT_PIXELS, MIN_POINT_FRAC = 800, 0.10

def box_mean(x, k):
    p = k // 2; c = np.pad(x, p + 1, mode="edge").cumsum(0).cumsum(1)
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return s[1:x.shape[0] + 1, 1:x.shape[1] + 1] / (k * k)

def point_pixels(a):
    """(lamp-like pixels, point-like lamp pixels) of a thumbnail array (3, h, w)."""
    a = a.astype(np.float32); mx = a.max(0)
    r, g, b = (cr.srgb_to_linear(a[k]) for k in range(3))
    lamp = ((mx >= cr.MIN_BRIGHT) & (mx <= cr.MAX_UNSATURATED) & (r > 0) & (g > 0)
            & (g / np.maximum(r, 1e-9) <= grid.MAX_GR) & (b / np.maximum(g, 1e-9) <= grid.MAX_BG))
    return int(lamp.sum()), int((lamp & (mx >= POINT_RATIO * box_mean(mx, POINT_BOX))).sum())

def exif_time(path):
    """EXIF DateTimeOriginal (tag 0x9003) as a UTC datetime, or None."""
    b = open(path, "rb").read(200_000); i = b.find(b"Exif\x00\x00")
    if i < 0: return None
    t = b[i + 6:]; e = "<" if t[:2] == b"II" else ">"
    def ifd(off):
        n = struct.unpack(e + "H", t[off:off + 2])[0]
        return {struct.unpack(e + "H", t[off + 2 + 12 * k:off + 4 + 12 * k])[0]:
                struct.unpack(e + "I", t[off + 10 + 12 * k:off + 14 + 12 * k])[0] for k in range(n)}
    sub = ifd(struct.unpack(e + "I", t[4:8])[0]).get(0x8769)
    off = ifd(sub).get(0x9003) if sub else None
    if off is None: return None
    try: return dt.datetime.strptime(t[off:off + 19].decode(), "%Y:%m:%d %H:%M:%S").replace(tzinfo=dt.timezone.utc)
    except ValueError: return None

def sun_elevation(lat, lon, when):
    """Solar elevation (deg), NOAA solar calculator equations, no refraction."""
    r = math.radians
    T = (when.timestamp() / 86400 + 2440587.5 - 2451545) / 36525
    L0 = (280.46646 + T * (36000.76983 + T * 0.0003032)) % 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    ecc = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    C = (math.sin(r(M)) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(r(2 * M)) * (0.019993 - 0.000101 * T) + math.sin(r(3 * M)) * 0.000289)
    om = 125.04 - 1934.136 * T
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(r(om))
    eps = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60 + 0.00256 * math.cos(r(om))
    dec = math.asin(math.sin(r(eps)) * math.sin(r(lam)))
    y = math.tan(r(eps / 2)) ** 2
    eqt = 4 * math.degrees(y * math.sin(2 * r(L0)) - 2 * ecc * math.sin(r(M))
                           + 4 * ecc * y * math.sin(r(M)) * math.cos(2 * r(L0))
                           - 0.5 * y * y * math.sin(4 * r(L0)) - 1.25 * ecc * ecc * math.sin(2 * r(M)))
    ha = r(((when.hour * 60 + when.minute + when.second / 60 + eqt + 4 * lon) % 1440) / 4 - 180)
    cz = math.sin(r(lat)) * math.sin(dec) + math.cos(r(lat)) * math.cos(dec) * math.cos(ha)
    return 90 - math.degrees(math.acos(max(-1.0, min(1.0, cz))))

def main():
    out = []
    for r in csv.DictReader(open(DERIVED / f"{PILOT}_thumb_shares.csv")):
        path = RAW_DIR / "small" / f"{r['photo_id']}.JPG"
        when = exif_time(path)
        sun = round(sun_elevation(float(r["lat"]), float(r["lon"]), when), 1) if when else ""
        a = gdal.Open(str(path)).ReadAsArray()
        med = float(np.median(a.max(axis=0)))
        n, npt = point_pixels(a)
        tw = sun != "" and sun >= MAX_SUN_DEG; br = med >= MAX_MEDIAN
        city = npt >= MIN_POINT_PIXELS and npt / max(n, 1) >= MIN_POINT_FRAC
        out.append(dict(photo_id=r["photo_id"], exif_time_utc=when.isoformat() if when else "",
                        sun_elev_deg=sun, thumb_median=med, lamp_pixels=n, point_pixels=npt,
                        point_frac=round(npt / max(n, 1), 4), twilight_or_day=int(tw), bright_frame=int(br),
                        city_frame=int(city), exclude=int(tw or br or not city), label="inferred",
                        note="" if when else "no EXIF DateTimeOriginal; brightness flag only"))
    with open(DERIVED / f"{PILOT}_frame_flags.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(len(out), "photos;", sum(o["twilight_or_day"] for o in out), "twilight_or_day;",
          sum(o["bright_frame"] for o in out), "bright_frame;", sum(o["city_frame"] for o in out), "city_frame;", sum(o["exclude"] for o in out), "exclude;",
          sum(o["sun_elev_deg"] == "" for o in out), "without EXIF time")

if __name__ == "__main__":
    main()
