"""Extra checks on the stroke-outline reading (question a) and white polygon completeness (question b). Run from final/. Writes results/b05_extra.txt"""
import os, sys, math, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b00_psparse as P
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
SCR = "/private/tmp/claude-501/-Users-alexander/7f5924cc-59f0-4937-8c2b-718f2e0be0ba/scratchpad"
txt = open(SCR + "/b01_p3.ps", errors="replace").read(); items = P.figure_items(txt)
cal = json.load(open(RES + "/b01_extract.json"))["calibration"]; xa, xb = cal["x_fit"]; ya, yb = cal["y_fit"]
out = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
COL = {"red": (0.933319, 0.172546, 0.172546), "amber": (1.0, 0.498032, 0.0), "blue": (0.117645, 0.564697, 1.0), "warm_white": (1.0, 0.972549, 0.862732), "cool_white": (0.749008, 0.937256, 1.0)}
def cross(poly, xp):
    ys = []
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if x0 != x1 and min(x0, x1) <= xp <= max(x0, x1):
            ys.append(y0 + (xp - x0) / (x1 - x0) * (y1 - y0))
    return ys
for name, c in COL.items():
    it = [i for i in items if i["colour"] and all(abs(a-b) < 2e-6 for a, b in zip(i["colour"], c)) and sum(len(s) for s in i["path"]) > 200][0]
    poly = P.flatten(it["path"][0], 16)
    cnt = collections.Counter(); ext = []
    for nm in range(401, 774):
        ys = cross(poly, (nm - xa) / xb); cnt[len(ys)] += 1; ext.append((max(ys) - min(ys)) * abs(yb))
    ext.sort(); flat = ext[:max(3, len(ext)//10)]
    ys_all = [p[1] for p in poly]
    topv = ya + yb * min(ys_all)
    say("%-11s crossings per whole-nm column (count: columns) %s | vertical extent value: min %.5f (=stroke width in pt %.3f, flat parts) median %.5f max %.4f" % (
        name, dict(sorted(cnt.items())), ext[0], ext[0] / abs(yb), ext[len(ext)//2], ext[-1]))
    say("            outline top edge = value %.4f ; minus half stroke width (%.4f) = estimated true apex %.4f ; extraction peak (midpoint) see b02" % (topv, ext[0]/2, topv - ext[0]/2))
# P. scintillans polygon
wh = [i for i in items if i["colour"] == (1.0, 1.0, 1.0) and i["op"] == "f"][0]
pl = P.flatten(wh["path"][0], 4)
say("white polygon: closed by baseline y=%.3f (value %.5f); vertices %d; first %s last %s; x range %.3f-%.3f pt = %.3f-%.3f nm" % (
    pl[0][1], ya + yb*pl[0][1], len(pl), pl[0], pl[-2], min(p[0] for p in pl), max(p[0] for p in pl), xa + xb*min(p[0] for p in pl), xa + xb*max(p[0] for p in pl)))
say("white polygon is monotone in x along its top edge (single-valued function, no overhang):", all(b[0] >= a[0] for a, b in zip(pl[:-3], pl[1:-2])))
say("plot panel (grey fill) x range pt/nm:", [ (round(min(p[0] for s in i['path'] for p in P.flatten(s)),2)) for i in items if i['colour'] and abs(i['colour'][0]-0.498032)<1e-4 and len(i['path'])==1][:1], "panel is 74.31-245.82 pt = %.1f-%.1f nm; white polygon lies entirely inside it" % (xa+xb*74.31, xa+xb*245.82))
open(RES + "/b05_extra.txt", "w").write("\n".join(out) + "\n")
