"""r01: raw integrity check (read-only).

Usage: python3 r01_raw_integrity.py start|end   (run from final/)

For each file in data/raw/spectra/MANIFEST.csv: size and SHA-256 vs the MANIFEST
values, plus mtime and mode. Also hashes the audited outputs and the pipeline
script so start and end can be compared (they must not change during the recheck).
Writes results/r01_<phase>.txt and results/r01_snapshot_<phase>.json.
"""
import csv, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
phase = sys.argv[1]
assert phase in ("start", "end")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

lines, snap, ok = [], {}, True
with open("data/raw/spectra/MANIFEST.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
for r in rows:
    p = os.path.join("data/raw/spectra/spitschan2016", r["filename"])
    st = os.stat(p)
    h = sha(p)
    m_size = st.st_size == int(r["size_bytes"])
    m_sha = h == r["sha256"]
    ok &= m_size and m_sha
    snap[p] = {"sha256": h, "size": st.st_size, "mtime_ns": st.st_mtime_ns, "mode": oct(st.st_mode)}
    lines.append(f"{'OK ' if (m_size and m_sha) else 'BAD'} {p} size={st.st_size} (manifest {r['size_bytes']}) "
                 f"sha256={h} (manifest match: {m_sha}) mode={oct(st.st_mode)}")
for p in ["data/derived/spectra/philadelphia.json", "data/derived/spectra/cherry_springs.json",
          "data/derived/spectra/spectra_meta.json", "pipeline/spectra/01_night_spectra.py"]:
    st = os.stat(p)
    snap[p] = {"sha256": sha(p), "size": st.st_size, "mtime_ns": st.st_mtime_ns, "mode": oct(st.st_mode)}
    lines.append(f"INFO {p} sha256={snap[p]['sha256']} size={st.st_size}")
lines.append(f"RAW vs MANIFEST: {'ALL MATCH' if ok else 'MISMATCH'} ({len(rows)} files)")
if phase == "end":
    with open(os.path.join(RES, "r01_snapshot_start.json")) as f:
        start = json.load(f)
    same = start == snap
    lines.append(f"START vs END snapshot (sha256, size, mtime, mode of raw + audited files): {'IDENTICAL' if same else 'DIFFERENT'}")
    if not same:
        for k in snap:
            if start.get(k) != snap[k]:
                lines.append(f"  changed: {k} {start.get(k)} -> {snap[k]}")
with open(os.path.join(RES, f"r01_snapshot_{phase}.json"), "w") as f:
    json.dump(snap, f, indent=1)
with open(os.path.join(RES, f"r01_{phase}.txt"), "w") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))
