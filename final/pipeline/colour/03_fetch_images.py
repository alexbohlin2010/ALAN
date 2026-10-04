"""Download archive image files for the given photo IDs (human-approved downloads only).

--kind geotiff: GetGeotiff.pl -> data/raw/colour/eol/geotiff/<photo_id>.tif
--kind jpeg:    full-size JPEG (DatabaseImages/ESC/large) -> data/raw/colour/eol/jpeg/<photo_id>.JPG
--kind small:   archive thumbnail (DatabaseImages/ESC/small, ~74 KB) -> data/raw/colour/eol/small/<photo_id>.JPG
--kind nef:     camera raw file (NEF, 10-50 MB) -> data/raw/colour/eol/nef/<photo_id>.NEF. The archive copies
                it on request: RequestOriginalImage.pl is called first, then OriginalImagery/<file> is
                polled every NEF_POLL_S until it answers (up to NEF_WAIT_S). Human approved 2026-10-03.
Instead of IDs, --pool fetches every pool record (in_pool = 1, epoch set) in <pilot>_records.csv,
and --pick fetches the rows of <pilot>_thumb_pick.csv (11_pick_thumbs.py) not yet downloaded.
Fetches run PARALLEL_REQUESTS at a time; failures are listed at the end, nothing partial is saved.
Files are set read-only; photo_id, UTC time, bytes, sha256, url are appended to MANIFEST.csv
in the same folder. Stops a download that exceeds MAX_BYTES or has the wrong file signature.
Run from final/:  .venv/bin/python pipeline/colour/03_fetch_images.py --kind jpeg ISS030-E-188190 ...
                  .venv/bin/python pipeline/colour/03_fetch_images.py --kind small --pool
                  .venv/bin/python pipeline/colour/03_fetch_images.py --kind small --pick --pilot global
"""
import csv, datetime, hashlib, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import *

MAX_BYTES = 100 * 1024 * 1024
KINDS = {  # folder, extension, url, accepted file signatures
    "geotiff": ("geotiff", "tif", lambda p: EOL + f"GetGeotiff.pl?photo={p}", (b"II*\x00", b"MM\x00*")),
    "jpeg": ("jpeg", "JPG", lambda p: f"https://eol.jsc.nasa.gov/DatabaseImages/ESC/large/{p.split('-')[0]}/{p}.JPG", (b"\xff\xd8\xff",)),
    "small": ("small", "JPG", lambda p: f"https://eol.jsc.nasa.gov/DatabaseImages/ESC/small/{p.split('-')[0]}/{p}.JPG", (b"\xff\xd8\xff",)),
    "nef": ("nef", "NEF", lambda p: f"https://eol.jsc.nasa.gov/OriginalImagery/{nef_name(p)}", (b"II*\x00", b"MM\x00*")),
}
NEF_POLL_S, NEF_WAIT_S = 60, 3600

_NEF_NAMES = {}
def nef_name(p):
    """Raw file name as listed on the photo page (frame numbers are zero-padded, case varies)."""
    if p not in _NEF_NAMES:
        m, roll, frame = p.split("-")
        page = urllib.request.urlopen(urllib.request.Request(EOL + f"photo.pl?mission={m}&roll={roll}&frame={frame}",
                                      headers={"User-Agent": USER_AGENT}), timeout=120).read().decode("utf-8", "ignore")
        f = re.findall(r'RequestOriginalImage\.pl\?[^"\'\\]*file=([^"\'\\&]+)', page)
        if not f or not f[0].lower().endswith(".nef"): raise ValueError(f"no NEF listed on the photo page ({f[:1]})")
        _NEF_NAMES[p] = f[0]
    return _NEF_NAMES[p]

def request_nef(p):
    """Ask the archive to stage the raw file (its page says this takes 5 min or more)."""
    m, roll, frame = p.split("-")
    url = EOL + f"RequestOriginalImage.pl?mission={m}&roll={roll}&frame={frame}&file={nef_name(p)}"
    urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=120).read()

def fetch_nef(url, sigs, kind, p):
    request_nef(p)
    t0 = time.time()
    while True:
        try: return fetch(url, sigs, kind)
        except urllib.error.HTTPError as e:
            if e.code not in (404, 500) or time.time() - t0 > NEF_WAIT_S: raise
            time.sleep(NEF_POLL_S)

def fetch(url, sigs, kind):
    """Return the file bytes, or raise ValueError (too big / wrong signature)."""
    r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=600)
    data = bytearray()
    while chunk := r.read(1 << 20):
        data += chunk
        if len(data) > MAX_BYTES: raise ValueError(f"over {MAX_BYTES} bytes")
    if not any(data.startswith(g) for g in sigs):
        raise ValueError(f"response is not a {kind} ({bytes(data[:60])!r})")
    return bytes(data)

def main(kind, ids):
    folder, ext, make_url, sigs = KINDS[kind]
    gdir = RAW_DIR / folder; gdir.mkdir(parents=True, exist_ok=True)
    man = gdir / "MANIFEST.csv"; new = not man.exists() or man.stat().st_size == 0
    todo = [p for p in ids if not (gdir / f"{p}.{ext}").exists()]
    # Files present but missing from the manifest (a run stopped before its rows were written):
    # add them with the file's modification time as fetched_utc.
    listed = {r[0] for r in csv.reader(open(man))} if man.exists() else set()
    lost = [p for p in ids if (gdir / f"{p}.{ext}").exists() and p not in listed]
    if lost:
        with open(man, "a", newline="") as mf:
            w = csv.writer(mf)
            if new: w.writerow(["photo_id", "fetched_utc", "bytes", "sha256", "url"]); new = False
            for p in lost:
                f = gdir / f"{p}.{ext}"; data = f.read_bytes()
                w.writerow([p, datetime.datetime.fromtimestamp(f.stat().st_mtime, datetime.UTC).isoformat(timespec="seconds") + " (file mtime)",
                            len(data), hashlib.sha256(data).hexdigest(), make_url(p)])
        print("manifest rows added for", len(lost), "files already here")
    print(f"{len(ids) - len(todo)} exist, {len(todo)} to fetch", flush=True)
    failed = []
    with open(man, "a", newline="") as mf, ThreadPoolExecutor(PARALLEL_REQUESTS) as ex:
        w = csv.writer(mf)
        if new: w.writerow(["photo_id", "fetched_utc", "bytes", "sha256", "url"])
        futs = {(ex.submit(fetch_nef, make_url(p), sigs, kind, p) if kind == "nef" else ex.submit(fetch, make_url(p), sigs, kind)): p
                for p in todo}
        for i, f in enumerate(as_completed(futs), 1):
            pid = futs[f]
            try: data = f.result()
            except Exception as e: failed.append((pid, str(e)[:120])); continue
            dst = gdir / f"{pid}.{ext}"
            dst.write_bytes(data); dst.chmod(0o444)
            w.writerow([pid, datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"), len(data),
                        hashlib.sha256(data).hexdigest(), make_url(pid)]); mf.flush()
            if i % 100 == 0 or len(todo) < 20: print(i, pid, "saved", len(data), "bytes", flush=True)
    print(f"done: {len(todo) - len(failed)} saved, {len(failed)} failed")
    for pid, e in failed: print("FAILED", pid, e)

def pool_ids():
    rows = csv.DictReader(open(DERIVED / f"{PILOT}_records.csv"))
    return [r["photo_id"] for r in rows if r["in_pool"] == "1" and r["epoch"]]

def pick_ids():
    return [r["photo_id"] for r in csv.DictReader(open(DERIVED / f"{PILOT}_thumb_pick.csv"))]

def nef_pilot_ids():
    return [r["photo_id"] for r in csv.DictReader(open(DERIVED / f"{PILOT}_nef_pilot.csv"))]

if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] != "--kind": sys.exit(__doc__)
    ids = {"--pool": pool_ids, "--pick": pick_ids, "--nef-pilot": nef_pilot_ids}.get(sys.argv[3], lambda: sys.argv[3:])()
    main(sys.argv[2], ids)
