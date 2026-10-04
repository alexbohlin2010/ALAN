"""RULES 3.2 human spot check sample: 4 random samples per curve (6 curves, N = 24) drawn from data/derived/impacts/spectra_299.json with a recorded seed.
Run from final/. Writes results/b08_spotcheck.md. The human check is NOT done or reported here."""
import json, os, random
SEED = 20261003
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
js = json.load(open("data/derived/impacts/spectra_299.json")); rng = random.Random(SEED)
order = ["cool_white", "warm_white", "blue", "amber", "red", "p_scintillans"]
nice = {"cool_white": "cool white (LED)", "warm_white": "warm white (LED)", "blue": "blue (LED)", "amber": "amber (LED)", "red": "red (LED)", "p_scintillans": "P. scintillans sensitivity (white area, top edge)"}
L = ["# Human spot check sample, study 299 spectra (RULES 3.2)", "",
     "Seed: **%d** (python `random.Random`, `sample` of 4 indices per curve, curves in the order below). N = 24." % SEED,
     "Source figure: `data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf`, page 3, Fig. 1. Axes: x Wavelength (nm) ticks 400/500/600/700; y Relative intensity ticks 0.00/0.25/0.50/0.75/1.00.",
     "Check by hand: find the curve at the given wavelength in the figure and read its relative intensity (for the LED lines: the centre of the drawn line, not its edge). Tick = match within about 0.01 (one pixel of a normal zoom).", "",
     "| # | curve | wavelength (nm) | value (JSON) | human match? (y/n) |", "|---|---|---|---|---|"]
k = 0
for name in order:
    s = js["curves"][name]["samples"]
    for i in sorted(rng.sample(range(len(s)), 4)):
        k += 1; L.append("| %d | %s | %s | %s | |" % (k, nice[name], s[i][0], s[i][1]))
L += ["", "Match rate: pending (human)", ""]
open(RES + "/b08_spotcheck.md", "w").write("\n".join(L)); print("\n".join(L))
