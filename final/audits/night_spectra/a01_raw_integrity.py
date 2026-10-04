"""Usage: a01_raw_integrity.py start|end  (run from final/).
Checks every row of data/raw/spectra/MANIFEST.csv (sha256 + size) and snapshots every file under data/raw/
(sha256, size, mtime). Also snapshots the audited outputs and script (data/derived/spectra/*, pipeline/spectra/*).
'end' compares with 'start'. Read-only on everything outside audits/night_spectra/."""
import csv, hashlib, os, sys, json
OUT = "audits/night_spectra/results"
mode = sys.argv[1]
assert mode in ("start", "end")
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
def snap(root):
    s = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f); st = os.stat(p); s[p] = [sha(p), st.st_size, st.st_mtime]
    return s
lines = []
P = lambda *a: lines.append(" ".join(str(x) for x in a))
rows = list(csv.DictReader(open("data/raw/spectra/MANIFEST.csv", newline="", encoding="utf-8")))
P(mode, "MANIFEST rows:", len(rows))
for r in rows:
    p = os.path.join("data/raw/spectra/spitschan2016", r["path"])
    a = sha(p); z = os.path.getsize(p)
    P(f"  {r['path']}: sha256 {a} manifest {r['sha256']} match={a == r['sha256']} | size {z} manifest {r['size_bytes']} match={str(z) == r['size_bytes']}")
listed = {os.path.join("data/raw/spectra/spitschan2016", r["path"]) for r in rows}
on_disk = {os.path.join(d, f) for d, _, fs in os.walk("data/raw/spectra") for f in fs}
P("  files under data/raw/spectra not in MANIFEST (excluding MANIFEST.csv):", sorted(on_disk - listed - {"data/raw/spectra/MANIFEST.csv"}))
P("  MANIFEST rows with no file:", sorted(listed - on_disk))
S = {"raw": snap("data/raw"), "derived_spectra": snap("data/derived/spectra"), "pipeline_spectra": snap("pipeline/spectra")}
P("  files under data/raw:", len(S["raw"]), "| data/derived/spectra:", len(S["derived_spectra"]), "| pipeline/spectra:", len(S["pipeline_spectra"]))
tree = hashlib.sha256("".join(f"{k}\t{v[0]}\t{v[1]}\n" for k, v in sorted(S["raw"].items())).encode()).hexdigest()
P("  tree hash of data/raw (path, sha256, size):", tree)
for k in ("derived_spectra", "pipeline_spectra"):
    for p, v in sorted(S[k].items()): P(f"  {p}: {v[0]}")
json.dump(S, open(f"{OUT}/a01_snapshot_{mode}.json", "w"), indent=1)
if mode == "end":
    S0 = json.load(open(f"{OUT}/a01_snapshot_start.json"))
    for k in S:
        same = S0[k] == S[k]
        P(f"  {k}: identical start vs end (sha256, size, mtime): {same}")
        if not same:
            for p in sorted(set(S0[k]) | set(S[k])):
                if S0[k].get(p) != S[k].get(p): P("    DIFF", p, S0[k].get(p), S[k].get(p))
open(f"{OUT}/a01_{mode}.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
