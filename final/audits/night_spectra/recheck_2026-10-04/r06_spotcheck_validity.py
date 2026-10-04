"""r06: is the existing human spot-check sample (audits/night_spectra/results/a06_spotcheck.md, seed 20261004)
still valid for the NEW outputs? Re-draws the same cells with the same seed and RNG calls, reads the NEW outputs
as text, and compares each of the 20 rows (site, spectrum index, wavelength, value, CSV row, CSV column, timestamp)
with the table in a06_spotcheck.md. Does NOT perform or report the human check; a06_spotcheck.md is only read.
Writes results/r06_spotcheck_validity.txt.
"""
import json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
SEED = 20261004
rng = random.Random(SEED)
redrawn = []
for site in ("philadelphia", "cherry_springs"):
    J = json.loads(open(f"data/derived/spectra/{site}.json").read(), parse_float=str, parse_int=str)
    for cell in sorted(rng.sample(range(240 * 281), 10)):
        i, j = divmod(cell, 281)
        wl = 280 + 2 * j
        v = J["irradiance"][i][j]
        redrawn.append([site, J["source_file"].split("/")[-1], str(i), str(wl), "null" if v is None else v,
                        str(6 + (wl - 280)), J["source_column"][i], J["timestamp"][i]])
table = [ln for ln in open("audits/night_spectra/results/a06_spotcheck.md").read().split("\n")
         if ln.startswith("| ") and ln[2].isdigit()]
existing = [[c.strip() for c in ln.strip("|").split("|")][1:9] for ln in table]
lines = [f"rows in a06_spotcheck.md: {len(existing)}; redrawn: {len(redrawn)}"]
same = 0
for n, (a, b) in enumerate(zip(existing, redrawn), 1):
    ok = a == b
    same += ok
    lines.append(f"{'SAME' if ok else 'DIFF'} row {n}: {b}" + ("" if ok else f" (a06: {a})"))
lines.append(f"RESULT: {same}/{len(existing)} rows identical (cell, value text, CSV row/column, timestamp)")
open(os.path.join(RES, "r06_spotcheck_validity.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
