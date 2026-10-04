"""Recheck2 q01: raw files vs MANIFEST.csv (size, SHA-256) plus a snapshot of raw files, outputs and script.
Usage (from final/): python3 audits/night_spectra/recheck2_2026-10-04/q01_raw_integrity.py start|end
Writes results/q01_<phase>.txt and results/q01_snapshot_<phase>.json. Read-only on everything else."""
import csv, hashlib, json, os, sys
phase = sys.argv[1]
R = "audits/night_spectra/recheck2_2026-10-04/results"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()
out, snap, ok = [], {}, True
for r in csv.DictReader(open("data/raw/spectra/MANIFEST.csv", newline="", encoding="utf-8")):
    p = "data/raw/spectra/spitschan2016/" + r["path"]
    s, z = sha(p), os.path.getsize(p)
    m = s == r["sha256"] and str(z) == r["size_bytes"]
    ok &= m
    out.append(f"{'MATCH' if m else 'MISMATCH'} {r['path']} size {z} (manifest {r['size_bytes']}) sha256 {s}")
files = [f"data/raw/spectra/spitschan2016/{n}" for n in sorted(os.listdir("data/raw/spectra/spitschan2016"))] + [
    "data/raw/spectra/MANIFEST.csv", "data/derived/spectra/philadelphia.json", "data/derived/spectra/cherry_springs.json",
    "data/derived/spectra/spectra_meta.json", "pipeline/spectra/01_night_spectra.py"]
for p in files:
    st = os.stat(p)
    snap[p] = {"sha256": sha(p), "size": st.st_size, "mtime": st.st_mtime, "mode": oct(st.st_mode)}
out.append("ALL RAW MATCH MANIFEST" if ok else "RAW MISMATCH")
for p in files: out.append(f"{snap[p]['sha256']}  {p}")
open(f"{R}/q01_{phase}.txt", "w").write("\n".join(out) + "\n")
json.dump(snap, open(f"{R}/q01_snapshot_{phase}.json", "w"), indent=1)
if phase == "end":
    a = json.load(open(f"{R}/q01_snapshot_start.json"))
    same = a == snap
    msg = "SNAPSHOT start == end" if same else "SNAPSHOT DIFFERS: " + str([k for k in snap if a.get(k) != snap[k]])
    open(f"{R}/q01_end.txt", "a").write(msg + "\n"); print(msg)
print("\n".join(out))
