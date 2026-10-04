"""Raster cross-check of the LED line positions: pdftoppm 600 dpi PPM, find pixels whose colour is within TOL of the line colour
(from the PS fill colour of the outline), midpoint of the highest and lowest matching pixel in each whole-nm column.
Calibration comes from b01_extract.json (tick marks). Writes results/b03_raster.txt. Stdlib only."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
SCR = "/private/tmp/claude-501/-Users-alexander/7f5924cc-59f0-4937-8c2b-718f2e0be0ba/scratchpad"
PDF = "data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf"
DPI = 600; S = DPI / 72.0; X0, Y0, W, H = 600, 3700, 1500, 1000
base = os.path.join(SCR, "b03_fig")
subprocess.run(["pdftoppm", "-f", "3", "-l", "3", "-r", str(DPI), "-x", str(X0), "-y", str(Y0), "-W", str(W), "-H", str(H), PDF, base], check=True)
fn = [f for f in os.listdir(SCR) if f.startswith("b03_fig") and f.endswith(".ppm")][0]
d = open(os.path.join(SCR, fn), "rb").read()
parts = d.split(b"\n", 3); assert parts[0] == b"P6"; w, h = map(int, parts[1].split()); pix = parts[3]
assert (w, h) == (W, H), (w, h)
mine = json.load(open(RES + "/b01_extract.json")); c = mine["calibration"]; xa, xb = c["x_fit"]; ya, yb = c["y_fit"]
pt_of_nm = lambda nm: (nm - xa) / xb
# cairo PS output uses page height 783 (true 782.362): a 0.638 pt vertical offset between the PS frame and the raster frame. Ticks and curves share the PS frame, so calibration is unaffected.
# The sign was found empirically (the opposite sign doubled the offset), not derived.
PSHIFT = -(783 - 782.362)
val_of_py = lambda py: ya + yb * ((py + 0.5 + Y0) / S + PSHIFT)   # pixel row centre -> pt -> PS frame -> value
LINE = {"red": (238, 44, 44), "amber": (255, 127, 0), "blue": (30, 144, 255), "warm_white": (255, 248, 220), "cool_white": (191, 239, 255)}
TOL = 40
WIN = 0.05
out = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
say("PPM", fn, w, h, "dpi", DPI, "tol", TOL, "window +-", WIN)
for name, col in LINE.items():
    diffs = []; miss = 0; worst = (0, None)
    for nm, v in mine["curves"][name]["samples"]:
        px = int(pt_of_nm(nm) * S - X0)
        if not (0 <= px < W): continue
        ys = []
        for py in range(H):
            if abs(val_of_py(py) - v) > WIN: continue   # only look near the vector value (stray same-colour pixels elsewhere in the column are ignored)
            o = (py * W + px) * 3
            r, g, b = pix[o], pix[o+1], pix[o+2]
            if abs(r-col[0]) + abs(g-col[1]) + abs(b-col[2]) <= TOL: ys.append(py)
        if not ys: miss += 1; continue
        rv = val_of_py((min(ys) + max(ys)) / 2)
        dd = abs(rv - v); diffs.append(dd)
        if dd > worst[0]: worst = (dd, nm)
    diffs.sort()
    say("%-11s columns matched %d, no-match %d | |raster - vector| median %.5f  p95 %.5f  max %.5f (at %s nm)  [1 px = %.5f value]" % (
        name, len(diffs), miss, diffs[len(diffs)//2], diffs[int(len(diffs)*.95)], diffs[-1], worst[1], abs(yb) / S))
open(os.path.join(RES, "b03_raster.txt"), "w").write("\n".join(out) + "\n")
