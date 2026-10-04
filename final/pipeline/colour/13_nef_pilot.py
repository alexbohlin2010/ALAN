"""Raw (NEF) pilot (human approved 2026-10-03, AI_LOG colour step 35): do the archive's raw files
remove the per-mission colour differences seen in the JPEGs (steps 31-33)?

pick:    writes data/derived/colour/<pilot>_nef_pilot.csv. Cells (0.5 deg, by record lat/lon) where
         2015 photos exist from both mission groups: A = ISS030-038 (JPEGs look sodium-orange) and
         B = ISS041-042 (JPEGs look white). Per cell and group up to K photos (>= 50 mm, records
         "Cataloged With Center Point" first, then by photo_id). Plus 2025 photos (ISS064, 066, 071)
         from the same cells or, if none, from Europe. Agent choice of cells, listed in CELLS.
analyse: decodes each NEF in data/raw/colour/eol/nef/ with LibRaw (rawpy): no white balance
         (multipliers 1,1,1,1), camera colour space (no colour matrix), linear (gamma 1,1), no auto
         brightness, 16 bit, half size. This follows Sanchez de Miguel et al. 2021 (RSE 112611:
         dcraw "-o 0", no colour balance). Lamp pixels: brightest channel >= MIN_SIGNAL of the
         16-bit range after subtracting the photo's per-channel median (sky background / airglow)
         and no channel >= SAT_FRAC (saturation). Per photo: camera-space G/R and B/G
         of lamp pixels (median, p10, p90) next to the JPEG thumbnail's old white share.
         Writes data/derived/colour/<pilot>_nef_pilot_ratios.csv and prints a comparison.
Run from final/:  .venv/bin/python pipeline/colour/13_nef_pilot.py pick|analyse --pilot global
"""
import csv, sys
import numpy as np
from config import *

A = {"ISS030", "ISS032", "ISS034", "ISS035", "ISS037", "ISS038"}
B = {"ISS041", "ISS042"}
LATE = {"ISS064", "ISS066", "ISS071"}
CELLS = {(36.0, -5.5): 3, (36.5, -6.0): 1, (52.0, 21.0): 1, (43.5, 3.5): 1}  # cell -> K per group
N_LATE = 4
MIN_SIGNAL = 0.03     # above background (agent check, step 36: background ~0.01 of range in D3S night NEFs)
SAT_FRAC = 0.95

def cell(x):
    return (round(float(x["lat"]) * 2) / 2, round(float(x["lon"]) * 2) / 2)

def pick():
    rows = [x for x in csv.DictReader(open(DERIVED / f"{PILOT}_thumb_cct.csv")) if float(x["focal_mm"] or 0) >= 50]
    old = {x["photo_id"]: x["white_share"] for x in csv.DictReader(open(DERIVED / f"{PILOT}_thumb_shares.csv"))}
    key = lambda x: (x["record_type"] != "Cataloged With Center Point", x["photo_id"])
    out = []
    for c, k in CELLS.items():
        for g, ms in (("A", A), ("B", B)):
            cand = sorted([x for x in rows if x["epoch"] == "2015" and cell(x) == c and x["photo_id"].split("-")[0] in ms], key=key)
            out += [dict(photo_id=x["photo_id"], group=g, cell=f"{c[0]},{c[1]}", epoch=x["epoch"]) for x in cand[:k]]
    late = sorted([x for x in rows if x["epoch"] == "2025" and x["photo_id"].split("-")[0] in LATE and cell(x) in CELLS], key=key)
    if len(late) < N_LATE:
        late += sorted([x for x in rows if x["epoch"] == "2025" and x["photo_id"].split("-")[0] in LATE and x not in late
                        and 36 <= float(x["lat"]) < 44 and -10 <= float(x["lon"]) < 4.5], key=key)
    out += [dict(photo_id=x["photo_id"], group="2025", cell=f"{cell(x)[0]},{cell(x)[1]}", epoch=x["epoch"]) for x in late[:N_LATE]]
    for o in out: o["jpeg_old_white_share"] = old.get(o["photo_id"], "")
    f = DERIVED / f"{PILOT}_nef_pilot.csv"
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    for o in out: print(o)
    print("wrote", f.relative_to(FINAL), len(out))

def analyse():
    import rawpy
    pil = list(csv.DictReader(open(DERIVED / f"{PILOT}_nef_pilot.csv")))
    out = []
    for r in pil:
        f = RAW_DIR / "nef" / f"{r['photo_id']}.NEF"
        if not f.exists(): print("missing", r["photo_id"]); continue
        with rawpy.imread(str(f)) as raw:
            model = raw.color_desc.decode()
            rgb = raw.postprocess(user_wb=[1, 1, 1, 1], output_color=rawpy.ColorSpace.raw, gamma=(1, 1),
                                  no_auto_bright=True, output_bps=16, half_size=True).reshape(-1, 3).astype(np.float64) / 65535
        sat = rgb.max(1) >= SAT_FRAC
        rgb = rgb - np.median(rgb, 0)  # sky background / airglow level per channel
        mx = rgb.max(1)
        m = (mx >= MIN_SIGNAL) & ~sat & (rgb.min(1) > 0)
        gr = rgb[m, 1] / rgb[m, 0]; bg = rgb[m, 2] / rgb[m, 1]
        out.append(dict(photo_id=r["photo_id"], group=r["group"], cell=r["cell"], cfa=model, lamp_pixels=int(m.sum()),
                        gr_p10=round(float(np.percentile(gr, 10)), 3), gr_median=round(float(np.median(gr)), 3),
                        gr_p90=round(float(np.percentile(gr, 90)), 3), bg_median=round(float(np.median(bg)), 3),
                        jpeg_old_white_share=r["jpeg_old_white_share"], label="measured (camera raw, uncalibrated)"))
        print(out[-1], flush=True)
    f = DERIVED / f"{PILOT}_nef_pilot_ratios.csv"
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print("wrote", f.relative_to(FINAL))

if __name__ == "__main__":
    {"pick": pick, "analyse": analyse}[sys.argv[1]]()
