"""Recheck2 q07: does audits/night_spectra/results/a06_spotcheck.md still match the current outputs? Re-draws the
sample with the same seed and RNG calls as a06_spotcheck_sample.py (in memory, nothing written outside results/) and
compares every column of the 20 rows with the existing table. Does not perform the human check.
Writes results/q07_spotcheck_validity.txt."""
import json, random
R = "audits/night_spectra/recheck2_2026-10-04/results"
SEED = 20261004
rng = random.Random(SEED)
new = []
for site in ("philadelphia", "cherry_springs"):
    J = json.load(open(f"data/derived/spectra/{site}.json"), parse_float=str, parse_int=str)
    for cell in sorted(rng.sample(range(240 * 281), 10)):
        i, j = divmod(cell, 281)
        wl = 280 + 2 * j
        v = J["irradiance"][i][j]
        new.append([site, J["source_file"].split("/")[-1], str(i), str(wl), "null" if v is None else v,
                    str(6 + (wl - 280)), J["source_column"][i], J["timestamp"][i]])
old = []
for ln in open("audits/night_spectra/results/a06_spotcheck.md", encoding="utf-8"):
    c = [x.strip() for x in ln.strip().strip("|").split("|")]
    if len(c) == 10 and c[0].isdigit():
        old.append(c[1:9])
L = [f"seed {SEED}; rows in table {len(old)}; rows re-drawn {len(new)}"]
match = 0
for n, (a, b) in enumerate(zip(old, new), 1):
    same = a == b
    match += same
    L.append(f"{'SAME' if same else 'DIFF'} row {n}: table {a} | now {b}" if not same else f"SAME row {n}: {' | '.join(b)}")
L.append(f"{match}/{len(old)} rows identical in all 8 columns (site, file, spectrum index, wavelength, value text, "
         f"CSV row, CSV column, timestamp)")
open(f"{R}/q07_spotcheck_validity.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
