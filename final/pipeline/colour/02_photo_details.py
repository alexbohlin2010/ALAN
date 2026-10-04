"""Fetch the archive's photo page for every pooled record and extract its technical metadata.

Input:  data/derived/colour/<pilot>_records.csv (rows with in_pool == 1)
Saves:  each photo page as fetched to data/raw/colour/eol/photos/<photo_id>.html
Writes: data/derived/colour/<pilot>_photo_details.csv
Values are copied as stated on the page (no interpretation). Missing fields stay empty.
Run from final/:  .venv/bin/python pipeline/colour/02_photo_details.py [--sample N --seed S]
--sample N: only N random pooled records per epoch (numpy default_rng(S)); output gets a _sample suffix.
"""
import argparse, csv, html as H, re, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from config import *

def latlon(s):
    m = re.match(r"([\d.]+)&deg; ([NS]), ([\d.]+)&deg; ([EW])", s or "")
    if not m: return "", ""
    la = float(m.group(1)) * (1 if m.group(2) == "N" else -1)
    lo = float(m.group(3)) * (1 if m.group(4) == "E" else -1)
    return la, lo

def field(text, label):
    m = re.search(re.escape(label) + r"\s*:?\s*\n\s*([^\n]*)", text)
    return m.group(1).strip() if m else ""

def details(page):
    t = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    d = {}
    d["nadir_lat"], d["nadir_lon"] = latlon(field(t, "Spacecraft nadir point"))
    d["centre_lat"], d["centre_lon"] = latlon(field(t, "Photo center point"))
    d["ml_centre_lat"], d["ml_centre_lon"] = latlon(field(t, "Photo center point by machine learning"))
    d["altitude"] = field(t, "Spacecraft Altitude").lstrip(": ")
    d["cloud_pct"] = field(t, "Cloud Cover Percentage")
    d["sun_elev"] = H.unescape(field(t, "Sun Elevation Angle"))
    d["camera"] = field(t, "Camera")
    d["focal"] = field(t, "Focal Length")
    d["tilt"] = field(t, "Camera Tilt")
    d["format"] = field(t, "Format")
    m = re.search(r"file=([\w.]+\.(?:NEF|nef|CR2|ARW|DNG|[a-z0-9]{3}))", page)
    d["raw_file_offered"] = m.group(1) if m else ""
    d["geotiff"] = "no" if "No GeoTIFF is available" in page else ("yes" if re.search(r"(?i)geotiff", page) else "")
    d["caption_start"] = re.sub(r"\s+", " ", field(t, "Image Caption").lstrip(": "))[:120]
    return d

def main():
    src = DERIVED / f"{PILOT}_records.csv"
    pdir = RAW_DIR / "photos"
    pdir.mkdir(parents=True, exist_ok=True)
    ap = argparse.ArgumentParser(); ap.add_argument("--sample", type=int); ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    rows = [r for r in csv.DictReader(open(src)) if r["in_pool"] == "1"]
    suffix = ""
    if a.sample:
        import numpy as np
        rng = np.random.default_rng(a.seed)
        rows = [r for e in sorted(EPOCHS) for r in
                (lambda g: [g[i] for i in sorted(rng.choice(len(g), min(a.sample, len(g)), replace=False))])(
                    [r for r in rows if r["epoch"] == str(e)])]
        suffix = f"_sample{a.sample}_seed{a.seed}"
    def fetch(r):
        f = pdir / f"{r['photo_id']}.html"
        if f.exists(): return
        mission, roll, frame = r["photo_id"].split("-")
        req = urllib.request.Request(EOL + f"photo.pl?mission={mission}&roll={roll}&frame={frame}",
                                     headers={"User-Agent": USER_AGENT})
        for attempt in range(RETRIES):
            try:
                page = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "ignore"); break
            except (urllib.error.URLError, TimeoutError) as e:
                print(r["photo_id"], "error", e, "attempt", attempt + 1, flush=True)
                if attempt == RETRIES - 1: raise
                time.sleep(RETRY_WAIT_S)
        if "Spacecraft nadir point" not in page:
            raise RuntimeError(f"{r['photo_id']}: not a photo page; not saved")
        f.write_text(page)
        time.sleep(REQUEST_PAUSE_S)
    with ThreadPoolExecutor(PARALLEL_REQUESTS) as ex:
        for i, _ in enumerate(ex.map(fetch, rows)):
            if i % 100 == 0: print(i, "/", len(rows), flush=True)
    out = []
    for r in rows:
        f = pdir / f"{r['photo_id']}.html"
        out.append({**{k: r[k] for k in ("photo_id", "date", "epoch", "record_type", "lat", "lon", "focal_mm")},
                    **details(f.read_text()), "page_file": str(f.relative_to(FINAL))})
    dst = DERIVED / f"{PILOT}_photo_details{suffix}.csv"
    with open(dst, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print("wrote", dst.relative_to(FINAL), len(out))

if __name__ == "__main__":
    main()
