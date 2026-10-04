"""Draw the pipeline JSON samples (one dot per nm) on a 600 dpi render of the figure and save a PNG in the session scratchpad (not in final/).
Stdlib only (zlib PNG writer). Needs b03 to have produced the PPM first. Calibration is read from the JSON's own tick table inverse:
here it uses MY fit (results/b01_extract.json) so the overlay is independent of the pipeline's calibration."""
import json, os, zlib, struct
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results")
SCR = "/private/tmp/claude-501/-Users-alexander/7f5924cc-59f0-4937-8c2b-718f2e0be0ba/scratchpad"
DPI = 600; S = DPI/72.0; X0, Y0, W, H = 600, 3700, 1500, 1000; PSHIFT = -(783 - 782.362)
d = open(os.path.join(SCR, "b03_fig-03.ppm"), "rb").read(); parts = d.split(b"\n", 3)
pix = bytearray(parts[3])
c = json.load(open(RES + "/b01_extract.json"))["calibration"]; xa, xb = c["x_fit"]; ya, yb = c["y_fit"]
js = json.load(open("data/derived/impacts/spectra_299.json"))
dot = {"red": (0, 0, 0), "amber": (0, 0, 0), "blue": (0, 0, 0), "warm_white": (200, 0, 160), "cool_white": (0, 0, 0), "p_scintillans": (0, 160, 0)}
def put(px, py, col, r=1):
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            x, y = px+dx, py+dy
            if 0 <= x < W and 0 <= y < H:
                o = (y*W+x)*3; pix[o:o+3] = bytes(col)
for name, cv in js["curves"].items():
    for nm, v in cv["samples"]:
        xp = (nm - xa)/xb; yp = (v - ya)/yb - PSHIFT   # value -> PS pt -> true pt
        put(int(round(xp*S - X0)), int(round(yp*S - Y0)), dot[name])
raw = b"".join(b"\x00" + bytes(pix[y*W*3:(y+1)*W*3]) for y in range(H))
def chunk(t, b): return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xffffffff)
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
open(os.path.join(SCR, "b04_overlay.png"), "wb").write(png); print("wrote", os.path.join(SCR, "b04_overlay.png"))
