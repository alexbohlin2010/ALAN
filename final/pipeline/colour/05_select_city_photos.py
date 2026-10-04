"""Pick one photo per test city and epoch for the colour-ratio comparison.

Rule (agent-proposed, logged): pooled records with focal length in SELECT_FOCAL_MM and listed
lat/lon within SELECT_RADIUS_DEG (east-west scaled by cos(lat)) of the city's reference point;
human-catalogued (centre point) before ML-catalogued, then nearest. The top candidates' photo
pages are fetched and the first whose page states a centre point (human or ML) within the
radius is chosen.
Writes data/derived/colour/<pilot>_city_photos.csv.
Run from final/:  .venv/bin/python pipeline/colour/05_select_city_photos.py
"""
import csv, importlib, math
from config import *

pd = importlib.import_module("02_photo_details")
TOP = 5

def dist(la, lo, ref):
    return math.hypot(la - ref[0], (lo - ref[1]) * math.cos(math.radians(ref[0])))

def main():
    import urllib.request, time
    rows = [r for r in csv.DictReader(open(DERIVED / f"{PILOT}_records.csv")) if r["in_pool"] == "1" and r["lat"]]
    pdir = RAW_DIR / "photos"
    out = []
    for city, ref in TEST_CITIES.items():
        for e in sorted(EPOCHS):
            c = [r for r in rows if r["epoch"] == str(e) and r["focal_mm"]
                 and SELECT_FOCAL_MM[0] <= float(r["focal_mm"]) <= SELECT_FOCAL_MM[1]
                 and dist(float(r["lat"]), float(r["lon"]), ref) <= SELECT_RADIUS_DEG]
            c.sort(key=lambda r: (not r["record_type"].startswith("Cataloged With"), dist(float(r["lat"]), float(r["lon"]), ref)))
            chosen = None
            for r in c[:TOP]:
                f = pdir / f"{r['photo_id']}.html"
                if not f.exists():
                    m, roll, fr = r["photo_id"].split("-")
                    req = urllib.request.Request(EOL + f"photo.pl?mission={m}&roll={roll}&frame={fr}", headers={"User-Agent": USER_AGENT})
                    for attempt in range(RETRIES):
                        try:
                            page = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "ignore"); break
                        except Exception as ex:
                            print(r["photo_id"], "error", ex, "attempt", attempt + 1, flush=True)
                            if attempt == RETRIES - 1: raise
                            time.sleep(RETRY_WAIT_S)
                    f.write_text(page); time.sleep(REQUEST_PAUSE_S)
                d = pd.details(f.read_text())
                la, lo = (d["centre_lat"], d["centre_lon"]) if d["centre_lat"] != "" else (d["ml_centre_lat"], d["ml_centre_lon"])
                if la != "" and dist(la, lo, ref) <= SELECT_RADIUS_DEG:
                    chosen = {**r, "city": city, "page_centre_lat": la, "page_centre_lon": lo,
                              "centre_source": "human" if d["centre_lat"] != "" else "ml",
                              "camera": d["camera"], "focal": d["focal"], "candidates": len(c)}
                    break
            print(city, e, len(c), "candidates ->", chosen and chosen["photo_id"], flush=True)
            out.append(chosen or {"city": city, "epoch": e, "candidates": len(c)})
    keys = ["city", "epoch", "photo_id", "date", "record_type", "centre_source", "page_centre_lat", "page_centre_lon", "focal", "camera", "candidates"]
    with open(DERIVED / f"{PILOT}_city_photos.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(out)

if __name__ == "__main__":
    main()
