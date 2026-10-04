"""Independent extraction of study-299 Fig. 1 (page 3) via `pdftocairo -ps` and own PostScript parsing.
Stdlib + poppler only. Does not import from pipeline/. Run from final/ :  python3 audits/impacts_spectra_299/b01_extract_ps.py
Output: results/b01_extract.json, results/b01_log.txt"""
import json, os, sys, math
sys.path.insert(0, os.path.dirname(__file__))
import b00_psparse as P

PDF = "data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf"
SCR = "/private/tmp/claude-501/-Users-alexander/7f5924cc-59f0-4937-8c2b-718f2e0be0ba/scratchpad"
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
log = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

txt = P.load(PDF, os.path.join(SCR, "b01_p3.ps"))
items = P.figure_items(txt)

def bbox(it):
    pts = [p for s in it["path"] for p in P.flatten(s)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)

# --- axis ticks: grey (0.2) filled thin rectangles. x ticks: tall thin below the panel (width<0.6, height~1.27); y ticks: left of panel.
xt, yt = [], []
for it in items:
    if it["colour"] and abs(it["colour"][0] - 0.2) < 0.01 and len(it["path"]) == 1 and len(it["path"][0]) == 5:
        x0, x1, y0, y1 = bbox(it)
        if (x1 - x0) < 0.6 and (y1 - y0) > 1.0: xt.append((x0 + x1) / 2)
        elif (y1 - y0) < 0.6 and (x1 - x0) > 1.0: yt.append((y0 + y1) / 2)
xt.sort(); yt.sort(reverse=True)   # x: left->right = 400..700 ; y: bottom (largest y) -> top = 0..1
assert len(xt) == 4 and len(yt) == 5, (xt, yt)
xv = [400, 500, 600, 700]; yv = [0, .25, .5, .75, 1.0]
def ols(p, v):
    n = len(p); mp = sum(p)/n; mv = sum(v)/n
    b = sum((a-mp)*(c-mv) for a, c in zip(p, v)) / sum((a-mp)**2 for a in p); a0 = mv - b*mp
    res = max(abs(a0 + b*a - c) for a, c in zip(p, v)); return a0, b, res
xa, xb, xr = ols(xt, xv); ya, yb, yr = ols(yt, yv)
say("x ticks (pt):", [round(v, 4) for v in xt], "-> nm = %.4f + %.6f*x ; max residual %.4f nm" % (xa, xb, xr))
say("y ticks (pt):", [round(v, 4) for v in yt], "-> val = %.6f + %.7f*y ; max residual %.2e" % (ya, yb, yr))
X = lambda p: xa + xb*p; Y = lambda p: ya + yb*p
# inverse: pt for a given nm
pt_of_nm = lambda nm: (nm - xa) / xb

def crossings(it, xp):
    ys = []
    for sub in it["path"]:
        poly = P.flatten(sub, 16)
        if poly and poly[0] != poly[-1]: poly = poly + [poly[0]]
        for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
            if x0 == x1: continue
            if (x0 <= xp <= x1) or (x1 <= xp <= x0):
                t = (xp - x0) / (x1 - x0); ys.append(y0 + t*(y1 - y0))
    return ys

COL = {  # exact fill colours of the big outline polygons found in the figure (rg values)
 "red": (0.933319, 0.172546, 0.172546), "amber": (1.0, 0.498032, 0.0), "blue": (0.117645, 0.564697, 1.0),
 "warm_white": (1.0, 0.972549, 0.862732), "cool_white": (0.749008, 0.937256, 1.0)}
def same(a, b): return all(abs(x-y) < 2e-6 for x, y in zip(a, b))
out = {"calibration": {"x_ticks_pt": xt, "y_ticks_pt": yt, "x_fit": [xa, xb], "y_fit": [ya, yb], "x_resid_nm": xr, "y_resid": yr}, "curves": {}}
for name, c in COL.items():
    cand = [it for it in items if it["op"] == "f" and it["colour"] and same(it["colour"], c) and sum(len(s) for s in it["path"]) > 200]
    say(name, "big polygons with exactly this colour:", len(cand), "subpaths", [len(it["path"]) for it in cand],
        "segments", [sum(len(s) for s in it["path"]) for it in cand], "any 'c' curves:", any(seg[0] == "c" for it in cand for s in it["path"] for seg in s))
    assert len(cand) == 1
    it = cand[0]; x0, x1, y0, y1 = bbox(it)
    lo, hi = math.ceil(X(x0) - 0.01), math.floor(X(x1) + 0.01)
    samp = []; widths = []
    for nm in range(lo, hi + 1):
        ys = crossings(it, pt_of_nm(nm))
        if not ys: continue
        samp.append([nm, Y((min(ys) + max(ys)) / 2)]); widths.append(abs(Y(min(ys)) - Y(max(ys))))
    out["curves"][name] = {"samples": samp, "median_stroke_vertical_extent": sorted(widths)[len(widths)//2]}
    say("  ", name, "n =", len(samp), "nm", samp[0][0], "-", samp[-1][0], "bbox nm %.2f-%.2f" % (X(x0), X(x1)))

# --- P. scintillans: the white (1,1,1) polygon; top edge = smallest y crossing
wh = [it for it in items if it["op"] == "f" and it["colour"] == (1.0, 1.0, 1.0)]
say("white fills in figure:", len(wh), [bbox(w) for w in wh])
it = wh[0]; x0, x1, y0, y1 = bbox(it)
say("white polygon: subpaths", len(it["path"]), "segments", sum(len(s) for s in it["path"]), "x %.3f-%.3f pt = %.2f-%.2f nm; y %.3f-%.3f pt = value %.4f-%.4f" % (x0, x1, X(x0), X(x1), y0, y1, Y(y1), Y(y0)))
poly = P.flatten(it["path"][0], 4)
say("white polygon first 3 and last 4 points:", poly[:3], poly[-4:])
lo, hi = math.ceil(X(x0)), math.floor(X(x1)); samp = []
for nm in range(lo, hi + 1):
    ys = crossings(it, pt_of_nm(nm))
    if ys: samp.append([nm, Y(min(ys))])
out["curves"]["p_scintillans"] = {"samples": samp}
say("   p_scintillans n =", len(samp), "nm", samp[0][0], "-", samp[-1][0])
json.dump(out, open(os.path.join(RES, "b01_extract.json"), "w"))
open(os.path.join(RES, "b01_log.txt"), "w").write("\n".join(log) + "\n")
