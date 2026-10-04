"""Helper for the human spot check: apply the stated curve to radiance values.

grey = 0 if v <= 0 else round(255 * interp(min(v, top), edges, cdf)),
with edges/cdf/top read from data/derived/radiance/curve/hist_eq_p9999.json.
For a level-8 sample, pass the block mean (leave out -1.5, other negatives as 0).

Usage: .venv/bin/python audits/radiance/curve_grey.py <radiance> [<radiance> ...]
"""
import sys
from common import load_curve, curve_grey

edges, cdf, top, _ = load_curve()
for a in sys.argv[1:]:
    print(a, "->", int(curve_grey([float(a)], edges, cdf, top)[0]))
