"""Question (c): colour -> LED name. (1) legend swatches (filled squares at x~253.5) top-to-bottom paired with legend words from pdftotext -bbox,
(2) swatch colour = alpha*line colour + (1-alpha)*key background, solved per channel, (3) peak positions vs the documented peaks in the paper text.
Run from final/. Writes results/b06_identity.txt"""
import os, sys, re, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import b00_psparse as P
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
SCR = "/private/tmp/claude-501/-Users-alexander/7f5924cc-59f0-4937-8c2b-718f2e0be0ba/scratchpad"
PDF = "data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf"
out = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
items = P.figure_items(open(SCR + "/b01_p3.ps", errors="replace").read())
# swatches: 'x y w h re f' with w~h~8.035 at x=253.465; each is a grey (0.949) square then the coloured square on top
sw = []
for it in items:
    if it["op"] == "f" and len(it["path"]) == 1 and len(it["path"][0]) == 5:
        xs = [s[1] for s in it["path"][0][:4]]; ys = [s[2] for s in it["path"][0][:4]]
        if abs(min(xs) - 253.465) < 0.01 and abs(max(xs) - min(xs) - 8.035) < 0.01: sw.append((min(ys), it["colour"]))
coloured = sorted([s for s in sw if abs(s[1][0] - 0.949005) > 1e-4 or abs(s[1][1]-0.949005) > 1e-4])
bg = 0.949005
say("legend swatches top->bottom (y_top pt, colour):", [(round(y, 2), tuple(round(c, 3) for c in col)) for y, col in coloured])
# legend words are outlined glyphs (no text layer): take the y-centre of each black glyph cluster to the right of the swatches, and read the NAMES
# visually from the 400 dpi render (cool white, warm white, blue, amber, red, top to bottom; see AUDIT note) - this part is a visual read, not parsed.
glyph = []
for it in items:
    if it["op"] == "f" and it["colour"] == (0.0, 0.0, 0.0) and it["path"]:
        pts = [q for sp in it["path"] for q in P.flatten(sp)]
        xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
        if 262 < min(xs) < 270 and 485 < min(ys) < 535: glyph.append(((min(ys) + max(ys)) / 2, min(xs), max(xs)))
glyph.sort()
say("legend text blocks (outlined glyph clusters; y-centre, x range):", [(round(a, 1), round(b, 1), round(c, 1)) for a, b, c in glyph])
NAMES = ["cool white", "warm white", "blue", "amber", "red"]
assert len(glyph) == 5, "expected 5 legend text blocks"
labels = [(g[0] - 3.6, n) for g, n in zip(glyph, NAMES)]
LINE = {"red": (0.933319, 0.172546, 0.172546), "amber": (1.0, 0.498032, 0.0), "blue": (0.117645, 0.564697, 1.0), "warm white": (1.0, 0.972549, 0.862732), "cool white": (0.749008, 0.937256, 1.0)}
for (ys, col), (ly, lab) in zip(coloured, labels):
    mid = ys + 4.0175; wmid = ly + 3.6
    # alpha from the channel with the largest contrast to the key background
    best = max(range(3), key=lambda k: abs(LINE[lab][k] - bg))
    alpha = (col[best] - bg) / (LINE[lab][best] - bg)
    pred = [alpha*LINE[lab][k] + (1-alpha)*bg for k in range(3)]
    err = max(abs(pred[k] - col[k]) for k in range(3))
    say("swatch y-centre %.1f  word '%s' y-centre %.1f (dy %.1f pt)  | blend alpha(solved) %.3f; max channel error using line colour of '%s': %.4f" % (mid, lab, wmid, mid - wmid, alpha, lab, err))
    # does any OTHER line colour fit equally with the same alpha?
    alt = {n: max(abs(alpha*c[k] + (1-alpha)*bg - col[k]) for k in range(3)) for n, c in LINE.items()}
    say("      fit error with each candidate line colour:", {n: round(v, 3) for n, v in alt.items()})
# paper text peaks
txt = subprocess.run(["pdftotext", "-f", "3", "-l", "3", PDF, "-"], capture_output=True, text=True).stdout
say("peak lines in the page-3 text:", re.findall(r"(?:cool white|warm white|blue|amber|deep red)\s*\([^)]*nm[^)]*\)", txt.replace("\n", " ")))
open(RES + "/b06_identity.txt", "w").write("\n".join(out) + "\n")
