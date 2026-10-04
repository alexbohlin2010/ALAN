"""Independent extraction of S. Fig. 1 from the raw PDF via `pdftocairo -svg` (stdlib only).
Imports nothing from pipeline/. Output: results/a01_extract.json and results/a01_log.txt"""
import re, subprocess, json, tempfile, os, sys, hashlib
RAW = "data/raw/impacts/mice/Wang_2023_NeurobiolDis_study278_supplement_mmc1.pdf"
OUT = "audits/impacts_spectra/results"
tmp = tempfile.mkdtemp(prefix="a01_", dir=os.environ.get("AUDIT_TMP", "/tmp"))
svg = os.path.join(tmp, "p1.svg"); bbox = os.path.join(tmp, "p1.html")
subprocess.run(["pdftocairo", "-svg", "-f", "1", "-l", "1", RAW, svg], check=True)
subprocess.run(["pdftotext", "-f", "1", "-l", "1", "-bbox", RAW, bbox], check=True)
S = open(svg).read(); B = open(bbox).read()
log = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

paths = re.findall(r'<path fill="none" stroke-width="([\d.]+)"[^>]*stroke="rgb\(([^)]*)\)"[^>]*d="([^"]*)" transform="matrix\(([^)]*)\)"', S)
def page(d, m):
    a, b, c, dd, e, f = [float(x) for x in m.split(",")]
    pts = [tuple(map(float, p.split())) for p in re.findall(r'[ML] ([\d.\-]+ [\d.\-]+)', d)]
    return [(a*x + c*y + e, b*x + dd*y + f) for x, y in pts]  # SVG page coords (y down)
objs = [(float(w), col, page(d, m)) for w, col, d, m in paths]

# ticks: black short 2-point segments, stroke 1.6668 *0.6
black = [o for o in objs if o[1].startswith("0%, 0%, 0%")]
xt = sorted(set(round(p[0][0], 4) for w, c, p in black if len(p) == 2 and abs(p[0][0]-p[1][0]) < 1e-6 and abs(p[0][1]-p[1][1]) < 3 ))
yt = sorted(set(round(p[0][1], 4) for w, c, p in black if len(p) == 2 and abs(p[0][1]-p[1][1]) < 1e-6 and abs(p[0][0]-p[1][0]) < 3))
P("x tick page-x:", xt); P("y tick page-y:", yt)
# printed labels
words = re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', B)
xl = {w[4]: (float(w[0])+float(w[2]))/2 for w in words if w[4] in ("400","500","600","700","800")}
yl = {w[4]: (float(w[1])+float(w[3]))/2 for w in words if w[4] in ("0.0","0.1","0.2","0.3","0.4","0.5","0.6")}
P("x labels centre:", xl); P("y labels centre:", yl)
# x axis: ticks are labelled 400..800 in order (5 ticks, 5 labels); verify label-centre vs tick offset constant
xs = [xt[-5:][i] for i in range(5)] if len(xt) >= 5 else xt
xv = [400,500,600,700,800]
n = len(xv)
# least squares x = a*nm + b
def ols(u, v):
    n = len(u); mu = sum(u)/n; mv = sum(v)/n
    a = sum((x-mu)*(y-mv) for x, y in zip(u, v))/sum((x-mu)**2 for x in u); return a, mv - a*mu
ax, bx = ols(xv, xs)
P("x fit page_x = %.6f*nm + %.4f; tick residuals (pt):" % (ax, bx), [round(x - (ax*v+bx), 5) for v, x in zip(xv, xs)])
P("x label-centre minus tick (pt):", [round(xl[str(v)] - x, 3) for v, x in zip(xv, xs)])
# y: ticks 0.0..0.5 -> page y descending
ys = sorted(yt, reverse=True)[:6]
yv = [0.0,0.1,0.2,0.3,0.4,0.5]
ay, by = ols(yv, ys)
P("y fit page_y = %.6f*val + %.4f; tick residuals (pt):" % (ay, by), [round(y - (ay*v+by), 5) for v, y in zip(yv, ys)])
P("y label-centre minus tick (pt):", [round(yl["%.1f" % v] - y, 3) for v, y in zip(yv, ys)])
nm = lambda x: (x - bx)/ax
val = lambda y: (y - by)/ay
P("x axis line from page-x %.3f (%.2f nm) to %.3f (%.2f nm)" % (min(p[0] for p in black[0][2]), nm(black[0][2][0][0]), black[0][2][1][0], nm(black[0][2][1][0])))

# curves: long blue/magenta paths with many points
curves = [o for o in objs if len(o[2]) > 50]
P("curves (>50 pts):", [(w, c, len(p)) for w, c, p in curves])
# legend swatches
for w, c, p in objs:
    if len(p) == 2 and ("61.96" in c or "89.8" in c):
        P("legend swatch", c, "page y = %.2f x %.2f-%.2f" % (p[0][1], p[0][0], p[1][0]))
for w in words:
    if w[4] in ("Short", "Long"):
        P("legend text", w[4], "y centre %.2f" % ((float(w[1])+float(w[3]))/2))
res = {}
for w, c, p in curves:
    name = "blue" if "61.96" in c else "magenta"
    res[name] = {"colour": c, "n": len(p), "nm": [nm(x) for x, y in p], "value": [val(y) for x, y in p]}
json.dump({"ax": ax, "bx": bx, "ay": ay, "by": by, "curves": res, "raw_sha256": hashlib.sha256(open(RAW,"rb").read()).hexdigest()}, open(OUT + "/a01_extract.json", "w"))
open(OUT + "/a01_log.txt", "w").write("\n".join(log) + "\n")
