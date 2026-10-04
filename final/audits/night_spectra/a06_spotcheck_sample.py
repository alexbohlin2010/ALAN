"""RULES 3.2: draw N = 20 random irradiance cells (10 per site) from the output JSONs for a HUMAN to compare with the raw
CSVs by hand. Usage: a06_spotcheck_sample.py [seed]. Writes results/a06_spotcheck.md (human column left empty).
The agent does not perform or report the human check."""
import json, random, sys
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261004
D = "data/derived/spectra"; OUT = "audits/night_spectra/results"
rng = random.Random(SEED)
rows = []
for site in ("philadelphia", "cherry_springs"):
    J = json.load(open(f"{D}/{site}.json"), parse_float=str, parse_int=str)   # values as their literal text
    for cell in sorted(rng.sample(range(240 * 281), 10)):
        i, j = divmod(cell, 281)
        wl = 280 + 2 * j
        v = J["irradiance"][i][j]
        rows.append((site, J["source_file"].split("/")[-1], i, wl, "null" if v is None else v,
                     6 + (wl - 280), J["source_column"][i], J["timestamp"][i]))
L = ["# Human spot check, night spectra (RULES 3.2)", "",
     f"Random seed: **{SEED}** (python `random.Random(seed).sample(range(240*281), 10)` per site, philadelphia drawn first; "
     "cell = spectrum index * 281 + wavelength index). N = 20.", "",
     "For each row open the raw CSV in `data/raw/spectra/spitschan2016/` (read only; it is transposed: one column per spectrum).",
     "Go to the 1-based CSV column given, confirm that row 1 of that column shows the timestamp given, then read the cell at",
     "the 1-based CSV row given (row = 6 + (wavelength - 280)). The output value should be the identical text",
     "(W m^-2 nm^-1). Spectrum index is 0-based within the output's 240 spectra. Mark y if the text matches exactly.", "",
     "| # | site | raw file | spectrum index | wavelength (nm) | output value | CSV row (1-based) | CSV column (1-based) | timestamp (row 1 of that column) | human match? (y/n) |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for n, r in enumerate(rows, 1):
    L.append(f"| {n} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} | |")
L += ["", "Match rate: pending (human)", ""]
open(f"{OUT}/a06_spotcheck.md", "w").write("\n".join(L))
print("\n".join(L))
