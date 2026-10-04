"""Compare my extraction (results/b01_extract.json) with data/derived/impacts/spectra_299.json, plus JSON invariants and peaks.
Run from final/. Writes results/b02_compare.txt"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
mine = json.load(open(RES + "/b01_extract.json")); js = json.load(open("data/derived/impacts/spectra_299.json"))
out = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
doc = {"cool_white": 453.2, "warm_white": 616.43, "blue": 455.31, "amber": 613.41, "red": 658.06}
say("calibration: mine x_resid %.4f nm y_resid %.2e | json x %.4f y %.2e" % (mine["calibration"]["x_resid_nm"], mine["calibration"]["y_resid"], js["calibration"]["x_max_residual_nm"], js["calibration"]["y_max_residual"]))
say("json top-level keys:", list(js))
for k in ("label", "rule", "source", "units"):
    say("  present:", k, bool(js.get(k)))
for name, c in js["curves"].items():
    a = {n: v for n, v in c["samples"]}; b = {n: v for n, v in mine["curves"][name]["samples"]}
    only_j = sorted(set(a) - set(b)); only_m = sorted(set(b) - set(a))
    common = sorted(set(a) & set(b))
    d = [(abs(a[n] - b[n]), n) for n in common]; md = max(d)
    nms = [n for n, v in c["samples"]]; vals = [v for n, v in c["samples"]]
    inc = all(y > x for x, y in zip(nms, nms[1:]))
    pk = max(c["samples"], key=lambda s: s[1]); pkm = max(mine["curves"][name]["samples"], key=lambda s: s[1])
    say("%-14s json n=%d (field n=%d) range %d-%d | mine n=%d | only-json %s only-mine %s | max|diff| %.6f at %d nm | strictly increasing %s | value min %.4f max %.4f | peak json %s mine %s%s" % (
        name, len(a), c["n"], nms[0], nms[-1], len(b), only_j, only_m, md[0], md[1], inc, min(vals), max(vals), pk, pkm,
        (" | documented %s, json-peak minus documented = %.2f nm" % (doc[name], pk[0] - doc[name])) if name in doc else ""))
    if name in doc:
        # sub-nm refinement: parabola through peak sample and neighbours (mine)
        s = dict(mine["curves"][name]["samples"]); n0 = pkm[0]
        y0, y1, y2 = s[n0-1], s[n0], s[n0+1]; den = y0 - 2*y1 + y2
        off = 0.5*(y0 - y2)/den if den else 0
        say("     parabolic sub-nm peak (my samples): %.2f nm ; |.-documented| = %.2f nm" % (n0 + off, abs(n0 + off - doc[name])))
    say("     n field == len(samples):", c["n"] == len(c["samples"]), "| curve dict keys:", [k for k in c if k != "samples"])
open(RES + "/b02_compare.txt", "w").write("\n".join(out) + "\n")
