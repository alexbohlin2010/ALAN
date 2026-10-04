"""Shared helper for the study-299 audit: parse the cairo PostScript of page 3 into fill/stroke items.
Stdlib only. Coordinates are page points, y down (cairo PS applies '1 0 0 -1 0 783 cm' itself,
so numbers in the file are already top-down, same frame as pdftotext)."""
import re, subprocess, sys

def load(pdf, ps_out):
    subprocess.run(["pdftocairo", "-ps", "-f", "3", "-l", "3", pdf, ps_out], check=True)
    return open(ps_out, errors="replace").read()

def figure_items(txt):
    start = txt.index("74.312 449.809 171.508 116.707 re W n")  # figure clip rectangle
    body = txt[start:]
    toks = body.replace("\n", " ").split()
    items = []; cur = []; fill = None; stroke = None; pts = []
    i = 0; stack = []
    colour = None; gray = None
    sub = []; path = []
    ops = {"m", "l", "c", "h", "f", "S", "re", "rg", "g", "RG", "w", "q", "Q", "n", "W", "cm", "d", "J", "j", "M", "BT", "ET"}
    nums = []
    for t in toks:
        if t in ops:
            if t == "rg": colour = tuple(float(x) for x in nums[-3:])
            elif t == "g": colour = (float(nums[-1]),) * 3
            elif t == "m": path.append([("m", float(nums[-2]), float(nums[-1]))])
            elif t == "l": path[-1].append(("l", float(nums[-2]), float(nums[-1])))
            elif t == "c": path[-1].append(("c",) + tuple(float(x) for x in nums[-6:]))
            elif t == "h": path[-1].append(("h",))
            elif t == "re":
                x, y, w, h = (float(v) for v in nums[-4:])
                path.append([("m", x, y), ("l", x + w, y), ("l", x + w, y + h), ("l", x, y + h), ("h",)])
            elif t in ("f", "S"):
                items.append({"op": t, "colour": colour, "path": path}); path = []
            elif t == "n": path = []
            nums = []
        else:
            nums.append(t)
    return items

def flatten(sub, n=8):
    """sub: list of segments -> list of (x,y) polyline (curves subdivided)."""
    out = []; cx = cy = None
    for s in sub:
        if s[0] in ("m", "l"):
            out.append((s[1], s[2])); cx, cy = s[1], s[2]
        elif s[0] == "c":
            x0, y0 = cx, cy; x1, y1, x2, y2, x3, y3 = s[1:]
            for k in range(1, n + 1):
                u = k / n; v = 1 - u
                out.append((v**3*x0 + 3*v*v*u*x1 + 3*v*u*u*x2 + u**3*x3,
                            v**3*y0 + 3*v*v*u*y1 + 3*v*u*u*y2 + u**3*y3))
            cx, cy = x3, y3
    return out
