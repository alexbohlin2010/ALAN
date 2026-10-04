"""Usage: a03_raw_integrity.py start|end. Checks the study-278 supplement PDF hash against MANIFEST.csv and snapshots
every file under data/raw/impacts/ (sha256, size, mtime); 'end' compares with 'start'. Also records the count/sizes of
all files under data/raw/ (other sessions write other sub-folders; only impacts/ is expected to be static here)."""
import csv, hashlib, os, sys, json
R = "data/raw"; PDF = "mice/Wang_2023_NeurobiolDis_study278_supplement_mmc1.pdf"
mode = sys.argv[1]; snapf = f"audits/impacts_spectra/results/a03_snapshot_{mode}.json"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
row = [r for r in csv.DictReader(open(f"{R}/impacts/MANIFEST.csv")) if r["path"] == PDF]
assert len(row) == 1
actual = sha(f"{R}/impacts/{PDF}"); size = os.path.getsize(f"{R}/impacts/{PDF}")
print(mode, "PDF sha256 manifest:", row[0]["sha256"], "\n    actual:  ", actual, "| match:", actual == row[0]["sha256"],
      "| size", size, "manifest", row[0]["size_bytes"], "match:", str(size) == row[0]["size_bytes"])
snap = {}
for d, _, fs in os.walk(f"{R}/impacts"):
    for f in fs:
        p = os.path.join(d, f); st = os.stat(p); snap[p] = [sha(p), st.st_size, st.st_mtime]
json.dump(snap, open(snapf, "w"), indent=1)
print("impacts files:", len(snap))
allraw = [(os.path.join(d, f)) for d, _, fs in os.walk(R) for f in fs]
print("all files under data/raw:", len(allraw), "| outside impacts:", sum(1 for p in allraw if not p.startswith(R + "/impacts/")))
if mode == "end":
    s0 = json.load(open("audits/impacts_spectra/results/a03_snapshot_start.json"))
    print("impacts snapshot identical start vs end (hash, size, mtime):", s0 == snap)
    for k in set(s0) | set(snap):
        if s0.get(k) != snap.get(k): print("  DIFF", k)
# every impacts raw file vs MANIFEST
rows = {r["path"]: r for r in csv.DictReader(open(f"{R}/impacts/MANIFEST.csv"))}
bad = [p for p, r in rows.items() if not os.path.exists(f"{R}/impacts/{p}") or sha(f"{R}/impacts/{p}") != r["sha256"]]
print("all MANIFEST rows verified:", len(rows), "bad:", bad)
extra = [p for p in snap if os.path.relpath(p, f"{R}/impacts") not in rows and not p.endswith("MANIFEST.csv")]
print("files in impacts/ not in MANIFEST:", extra)
