"""Raw integrity. usage (from final/): python3 audits/impacts_spectra_299/b07_raw_integrity.py start|end
- SHA-256 + size of the study-299 PDF vs the MANIFEST row; all MANIFEST rows of data/raw/impacts verified; unlisted files noted
- digest of (relative path, size, mtime_ns) over the WHOLE data/raw tree (metadata only, fast), plus SHA-256 of every file under data/raw/impacts
Writes results/b07_<mode>.txt and results/b07_snapshot_<mode>.json; 'end' also diffs against 'start'."""
import csv, hashlib, json, os, sys
mode = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
RAW = "data/raw"; IMP = "data/raw/impacts"; PDF = "fireflies/Owens_Lewis_2021_ICD_study299.pdf"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
out = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
rows = list(csv.DictReader(open(IMP + "/MANIFEST.csv", newline="")))
say("MANIFEST columns:", list(rows[0].keys())[:12], "rows:", len(rows))
fcol = [k for k in rows[0] if k.lower().startswith("path") or k.lower() in ("file", "local_path", "filename")][0]
hcol = [k for k in rows[0] if "sha" in k.lower()][0]; scol = [k for k in rows[0] if "size" in k.lower() or "byte" in k.lower()][0]
ok = 0; bad = []
for r in rows:
    p = os.path.join(IMP, r[fcol])
    if os.path.exists(p) and sha(p) == r[hcol] and str(os.path.getsize(p)) == r[scol].strip(): ok += 1
    else: bad.append(r[fcol])
say("manifest rows verified (sha256 + size):", ok, "of", len(rows), "bad:", bad)
r299 = [r for r in rows if r[fcol] == PDF][0]; p = os.path.join(IMP, PDF); h = sha(p)
say("study 299 PDF: sha256", h, "size", os.path.getsize(p), "| MANIFEST", r299[hcol], r299[scol], "| MATCH:", h == r299[hcol] and str(os.path.getsize(p)) == r299[scol].strip())
listed = {r[fcol] for r in rows} | {"MANIFEST.csv"}
actual = {os.path.relpath(os.path.join(d, f), IMP) for d, _, fs in os.walk(IMP) for f in fs}
say("files in impacts/:", len(actual), "unlisted:", sorted(actual - listed), "listed but absent:", sorted(listed - actual))
meta = []
for d, _, fs in os.walk(RAW):
    for f in fs:
        q = os.path.join(d, f); st = os.stat(q); meta.append((q, st.st_size, st.st_mtime_ns))
meta.sort(); dig = hashlib.sha256(json.dumps(meta).encode()).hexdigest()
say("data/raw tree: files", len(meta), "metadata digest (path,size,mtime_ns)", dig)
snap = {"tree_digest": dig, "n": len(meta), "impacts_sha": {os.path.relpath(q, IMP): sha(q) for q, _, _ in meta if q.startswith(IMP + "/")}, "meta_impacts": [m for m in meta if m[0].startswith(IMP + "/")]}
json.dump(snap, open(RES + "/b07_snapshot_%s.json" % mode, "w"))
if mode == "end":
    s0 = json.load(open(RES + "/b07_snapshot_start.json"))
    say("END vs START: tree digest identical:", s0["tree_digest"] == snap["tree_digest"], "| file count", s0["n"], snap["n"], "| impacts hashes identical:", s0["impacts_sha"] == snap["impacts_sha"], "| impacts size/mtime identical:", s0["meta_impacts"] == json.loads(json.dumps(snap["meta_impacts"])))
open(RES + "/b07_%s.txt" % mode, "w").write("\n".join(out) + "\n")
