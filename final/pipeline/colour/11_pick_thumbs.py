"""Pick which pool thumbnails to download for a region, with a cap per cell (human, 2026-10-03).

Rule (human approved the agent's proposal, AI_LOG colour step 28):
- Candidates: pool records (in_pool = 1, epoch set) with focal length >= MIN_FOCAL_MM
  (10_white_share_grid.py uses no other photos).
- Cell = 1 deg x 1 deg by the record's lat/lon (floor), separately per epoch.
- Thumbnails already in data/raw/colour/eol/small/ are always used and count toward the cap.
- New picks fill each cell up to CAP: records "Cataloged With Center Point" first (better
  location), then the rest, each group in random order (numpy default_rng(SEED)).
Writes data/derived/colour/<pilot>_thumb_pick.csv (photo_id, epoch, cell, record_type, status)
with status = have | new, and prints the count of new files.
Run from final/:  .venv/bin/python pipeline/colour/11_pick_thumbs.py --pilot global
"""
import csv, math
from collections import defaultdict
import numpy as np
from config import *

CAP = 5
CELL_DEG = 1.0
MIN_FOCAL_MM = 50
SEED = 20261003

def main():
    rows = [r for r in csv.DictReader(open(DERIVED / f"{PILOT}_records.csv"))
            if r["in_pool"] == "1" and r["epoch"] and float(r["focal_mm"] or 0) >= MIN_FOCAL_MM]
    cells = defaultdict(list)
    for r in rows:
        c = (r["epoch"], math.floor(float(r["lat"]) / CELL_DEG), math.floor(float(r["lon"]) / CELL_DEG))
        cells[c].append(r)
    rng = np.random.default_rng(SEED)
    out = []
    for c in sorted(cells):
        have = [r for r in cells[c] if (RAW_DIR / "small" / f"{r['photo_id']}.JPG").exists()]
        rest = [r for r in cells[c] if r not in have]
        cp = [r for r in rest if r["record_type"] == "Cataloged With Center Point"]
        ml = [r for r in rest if r["record_type"] != "Cataloged With Center Point"]
        order = [cp[i] for i in rng.permutation(len(cp))] + [ml[i] for i in rng.permutation(len(ml))]
        new = order[:max(0, CAP - len(have))]
        cell = f"{c[1] * CELL_DEG:g},{c[2] * CELL_DEG:g}"
        out += [dict(photo_id=r["photo_id"], epoch=c[0], cell=cell, record_type=r["record_type"], status="have") for r in have]
        out += [dict(photo_id=r["photo_id"], epoch=c[0], cell=cell, record_type=r["record_type"], status="new") for r in new]
    f = DERIVED / f"{PILOT}_thumb_pick.csv"
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    n_new = sum(o["status"] == "new" for o in out)
    print(f"candidates {len(rows)} in {len(cells)} cell-epochs; picked {len(out)} "
          f"({len(out) - n_new} already here, {n_new} new, ~{n_new * 74 / 1e6:.2f} GB at 74 KB)")
    for ep in EPOCHS:
        print(ep, "cells", sum(1 for c in cells if c[0] == str(ep)),
              "new", sum(o["status"] == "new" and o["epoch"] == str(ep) for o in out))
    print("wrote", f.relative_to(FINAL))

if __name__ == "__main__":
    main()
