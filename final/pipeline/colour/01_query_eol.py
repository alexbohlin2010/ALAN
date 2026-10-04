"""Query the NASA Gateway to Astronaut Photography for night photos in the pilot box.

Saves each response as fetched to data/raw/colour/eol/queries/<UTC date>/<pilot>/<mission>.html
and writes the parsed rows to data/derived/colour/<pilot>_records.csv.
Missions are queried PARALLEL_QUERIES at a time.
Uses the public CoordinateRangeSearch form (no API key). Read-only toward the archive.
Run from final/:  .venv/bin/python pipeline/colour/01_query_eol.py [--pilot global]
"""
import csv, datetime, http.cookiejar, re, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from config import *

TIMEOUT_S = 1800  # a worldwide query can take many minutes server-side

def opener():
    cj = http.cookiejar.CookieJar()
    o = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    o.addheaders = [("User-Agent", USER_AGENT)]
    return o

def query(mission):
    o = opener()
    o.open(EOL, timeout=TIMEOUT_S).read()
    b = BBOX
    form = {"body": "Earth", "AltLowerLat": b["lower_lat"], "AltUpperLat": b["upper_lat"],
            "AltLeftLon": b["left_lon"], "AltRightLon": b["right_lon"],
            "LowerLat": b["lower_lat"], "UpperLat": b["upper_lat"],
            "LeftLon": b["left_lon"], "RightLon": b["right_lon"],
            f"mission-{mission}": "on", "nighttime": "on",
            "UseCatalogedWithCP": "on", "UseCatalogedWithoutCP": "on",
            "UseNotCataloged": "on", "IncludeHO": "on"}
    r = o.open(EOL + "CoordinateRangeSearch.pl", urllib.parse.urlencode(form).encode(), timeout=TIMEOUT_S).read().decode("utf-8", "ignore")
    rid = re.search(r"results=(\d+)", r).group(1)
    return o.open(EOL + f"ShowQueryResults-TextTable.pl?results={rid}", timeout=TIMEOUT_S).read().decode("utf-8", "ignore")

def parse(html):
    for tr in re.findall(r"<tr.*?</tr>", html, flags=re.S):
        c = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<td.*?</td>", tr, flags=re.S)]
        if len(c) >= 9 and re.match(r"ISS\d+-", c[0]):
            yield dict(photo_id=c[0], date=c[1], lat=c[2], lon=c[3], focal_mm=c[6], record_type=c[8])

def fetch(m, f):
    for attempt in range(RETRIES):
        try:
            html = query(m); break
        except (urllib.error.URLError, TimeoutError) as e:  # e.g. 502 from the archive, timeout
            print(m, "error", getattr(e, "code", e), "attempt", attempt + 1, flush=True)
            if attempt == RETRIES - 1: raise
            time.sleep(RETRY_WAIT_S)
    if "Displayed:" not in html:
        raise RuntimeError(f"{m}: response has no result table; not saved")
    f.write_text(html)
    print(m, "saved", len(html), "chars", flush=True)
    time.sleep(REQUEST_PAUSE_S)

def main():
    day = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    qdir = RAW_DIR / "queries" / day / PILOT
    qdir.mkdir(parents=True, exist_ok=True)
    todo = [m for m in MISSIONS if not (qdir / f"{m}.html").exists()]
    with ThreadPoolExecutor(PARALLEL_QUERIES) as ex:
        for fu in [ex.submit(fetch, m, qdir / f"{m}.html") for m in todo]: fu.result()
    rows = {}
    for m in MISSIONS:
        f = qdir / f"{m}.html"
        n = 0
        for r in parse(f.read_text()):
            rows.setdefault(r["photo_id"], r); n += 1
        print(m, n)
    DERIVED.mkdir(parents=True, exist_ok=True)
    out = DERIVED / f"{PILOT}_records.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["photo_id", "date", "lat", "lon", "focal_mm", "record_type", "epoch", "in_pool", "query_file"])
        w.writeheader()
        for r in rows.values():
            d = int(r["date"])
            r["epoch"] = next((y for y, (a, z) in EPOCHS.items() if a <= d <= z), "")
            r["in_pool"] = int(bool(r["epoch"]) and r["record_type"] in RECORD_TYPES)
            r["query_file"] = str((qdir / f"{r['photo_id'].split('-')[0]}.html").relative_to(FINAL))
            w.writerow(r)
    print("wrote", out.relative_to(FINAL), len(rows), "records;", sum(int(r["in_pool"]) for r in rows.values()), "in pool")

if __name__ == "__main__":
    main()
