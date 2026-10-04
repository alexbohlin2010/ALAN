"""RULES 3.2: draw N=20 random samples (10 per curve) from the pipeline JSON for a HUMAN to compare with the figure by hand.
Usage: a04_spotcheck_sample.py [seed]. Writes results/a04_spotcheck.md (human column left empty)."""
import json, random, sys
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261003
D = json.load(open("data/derived/impacts/spectra_278.json"))
rng = random.Random(SEED)
rows = []
for k in ("short", "long"):
    s = D["curves"][k]["samples"]
    for i in sorted(rng.sample(range(len(s)), 10)):
        rows.append((k, i, s[i][0], s[i][1]))
L = [f"# Human spot check, study 278 spectra (RULES 3.2)", "",
     f"Random seed: **{SEED}** (python `random.Random(seed).sample`, 10 sample indices per curve, short drawn first). N = {len(rows)}.", "",
     "Compare each (wavelength, value) with S. Fig. 1 (page 1 of `data/raw/impacts/mice/Wang_2023_NeurobiolDis_study278_supplement_mmc1.pdf`):",
     "find the wavelength on the x axis, read the height of the named curve (blue = short-lambda, magenta = long-lambda) on the y axis",
     "(mW/m2 as printed). Value is read from a printed figure, so allow about +/-0.01 for eyeballing. Tick the row y if the curve passes through the point.", "",
     "| # | curve | sample index | wavelength (nm) | value (mW/m2) | human match? (y/n) |", "|---|---|---|---|---|---|"]
for n, (k, i, w, v) in enumerate(rows, 1):
    L.append(f"| {n} | {k} | {i} | {w:.2f} | {v:.5f} | |")
L += ["", "Match rate: pending (human)", ""]
open("audits/impacts_spectra/results/a04_spotcheck.md", "w").write("\n".join(L))
print("\n".join(L))
