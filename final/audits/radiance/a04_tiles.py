"""Audit a04: every tile of data/derived/radiance/tiles/v1 vs values recomputed from the RAW files.

Expected values follow the stated rules only (handoff 2026-10-03), not the pipeline code:
  grid   native pyramid on the raster's own pixel grid; level LMAX = native; level n
         uses blocks of f = 2**(LMAX-n) native pixels; 256x256 tiles, y = 0 at the north.
  grey   R = 2015, G = 2025: 0 if value <= 0, else round(255 * interp(min(v, top), edges, cdf))
         with the curve JSON (checked separately by a03).
  B7     coarser levels: mean of linear radiance over the block's in-raster pixels that are
         not -1.5, with other negatives counted as 0; then the curve.
  flags  B = 1 (2015 all -1.5 in block) + 2 (2025 same) + 4 (block entirely outside raster).
  skip   a tile is absent only if it has no grey > 0 and no flag 1/2 anywhere.
Coarser-level sums are built by repeated 2x2 summation in float64 (the pipeline sums each
f x f block directly), so any grey mismatch is also reported with whether the unrounded
value lies within 1e-6 of a .5 rounding boundary.

Also checks tiles.json (geometry, georeferencing, existence bitmask vs files on disk) and
cross-checks a random subset of tiles with a second decoder (libwebp's dwebp CLI).

Usage: .venv/bin/python audits/radiance/a04_tiles.py
Output: audits/radiance/results/a04_tiles.json
"""
import base64, json, math, os, random, shutil, subprocess, tempfile, time
import numpy as np
from osgeo import gdal
from common import (TILES, YEARS, NO_DATA, FLAG_ND, FLAG_OUT, TILE, open_raw, load_curve,
                    curve_grey_float, write_result)

CH = 512           # native rows per streamed chunk (= block size of level 0)
MAX_EXAMPLES = 25
DWEBP_SAMPLE, DWEBP_SEED = 200, 20261003


def decode(path):
    a = gdal.Open(str(path), gdal.GA_ReadOnly).ReadAsArray()
    return a


def grey_from(s, valid, curve):
    """Return (grey uint8, near_half bool) for block sums s and valid counts."""
    mean = np.where(valid > 0, s / np.maximum(valid, 1), 0.0)
    gf = curve_grey_float(mean, *curve)
    pos = (valid > 0) & (mean > 0)
    g = np.where(pos, np.round(gf), 0).astype(np.uint8)
    near = pos & (np.abs(gf - np.floor(gf) - 0.5) < 1e-6)
    return g, near


def reduce2(x):
    h, w = x.shape
    return x.reshape(h // 2, 2, w // 2, 2).sum((1, 3))


class Level:
    def __init__(self, n, f, W, H, cols, rows):
        self.n, self.f, self.cols, self.rows = n, f, cols, rows
        self.out_w, self.out_h = math.ceil(W / f), math.ceil(H / f)
        self.buf, self.ty = [], 0
        self.stats = dict(tiles_expected=0, tiles_on_disk_checked=0, missing_tiles=[],
                          extra_tiles=[], bad_shape=[], grey_mismatch_px={"r": 0, "g": 0},
                          grey_mismatch_near_half={"r": 0, "g": 0}, grey_max_abs_diff=0,
                          flag_mismatch_px=0, tiles_with_mismatch=0,
                          flag_px_expected={"1": 0, "2": 0, "4": 0},
                          flag_px_found={"1": 0, "2": 0, "4": 0}, examples=[])


def main():
    t0 = time.time()
    edges, cdf, top, _ = load_curve()
    curve = (edges, cdf, top)
    idx = json.loads((TILES / "tiles.json").read_text())
    raws = {y: open_raw(y) for y in YEARS}
    W, H = raws[2015].RasterXSize, raws[2015].RasterYSize
    gt = raws[2015].GetGeoTransform()
    res = {"checks": {}}
    ck = res["checks"]
    ck["raw_years_same_grid"] = (raws[2025].RasterXSize, raws[2025].RasterYSize,
                                 raws[2025].GetGeoTransform()) == (W, H, gt)

    # ---- tiles.json invariants ----
    lmax = 0
    while TILE * 2 ** lmax < max(W, H):
        lmax += 1
    ck["json_max_level"] = idx["max_level"] == lmax
    ck["json_tile_size"] = idx["tile_size"] == TILE
    ck["json_raster_size"] = (idx["raster_width"], idx["raster_height"]) == (W, H)
    ck["json_origin_equals_raw"] = (idx["origin_lon"], idx["origin_lat"]) == (gt[0], gt[3])
    ck["json_pixel_deg_equals_raw"] = idx["native_pixel_deg"] == gt[1] == -gt[5]
    ck["json_crs"] = idx["crs"] == "EPSG:4326"
    ck["json_flags"] = idx["channels"]["b"] == {"1": "2015 no data (-1.5)",
                                                "2": "2025 no data (-1.5)", "4": "outside raster"}
    levels, json_geom_ok, bitmask_ok, files_ok = {}, True, True, True
    exists = {}
    geom_detail = []
    for L in idx["levels"]:
        n = L["level"]
        f = 2 ** (lmax - n)
        ow, oh = math.ceil(W / f), math.ceil(H / f)
        cols, rows = math.ceil(ow / TILE), math.ceil(oh / TILE)
        g_ok = (L["block"], L["width_px"], L["height_px"], L["cols"], L["rows"]) == (f, ow, oh, cols, rows)
        json_geom_ok &= g_ok
        bits = np.unpackbits(np.frombuffer(base64.b64decode(L["exists_bitmask_b64"]), np.uint8))
        bm = bits[:rows * cols].reshape(rows, cols).astype(bool)
        on_disk = np.zeros((rows, cols), bool)
        stray = []
        ldir = TILES / str(n)
        for xd in os.listdir(ldir) if ldir.exists() else []:
            if xd.startswith("."):
                continue
            for fn in os.listdir(ldir / xd):
                if fn.startswith("."):
                    continue
                x, y = int(xd), int(fn.split(".")[0])
                if fn.endswith(".webp") and x < cols and y < rows:
                    on_disk[y, x] = True
                else:
                    stray.append(f"{n}/{xd}/{fn}")
        b_ok = np.array_equal(bm, on_disk) and int(bm.sum()) == L["tiles_written"] and not bits[rows * cols:].any()
        bitmask_ok &= b_ok
        files_ok &= not stray
        geom_detail.append(dict(level=n, block=f, width_px=ow, height_px=oh, cols=cols, rows=rows,
                                geometry_matches_json=g_ok, tiles_written_json=L["tiles_written"],
                                tiles_on_disk=int(on_disk.sum()), bitmask_matches_disk=b_ok,
                                stray_files=stray[:20]))
        levels[n] = Level(n, f, W, H, cols, rows)
        exists[n] = on_disk
    ck["json_level_list_complete"] = sorted(levels) == list(range(lmax + 1))
    ck["json_level_geometry"] = json_geom_ok
    ck["json_bitmask_matches_files"] = bitmask_ok
    ck["no_stray_files"] = files_ok
    res["levels_geometry"] = geom_detail

    # ---- stream raw, both years in lockstep ----
    WP = levels[lmax].cols * TILE
    assert WP % CH == 0
    n_chunks = math.ceil(H / CH)

    def check_tile_row(lv, rgb_rows, near_rows):
        """rgb_rows: (3, 256, width) expected; compare with each tile in tile row lv.ty."""
        st, ty = lv.stats, lv.ty
        for tx in range(lv.cols):
            exp = rgb_rows[:, :, tx * TILE:(tx + 1) * TILE]
            nr = near_rows[:, :, tx * TILE:(tx + 1) * TILE]
            for k, bit in (("1", 1), ("2", 2), ("4", 4)):
                st["flag_px_expected"][k] += int(((exp[2] & bit) > 0).sum())
            should_exist = bool(exp[0].any() or exp[1].any() or (exp[2] & 3).any())
            st["tiles_expected"] += should_exist
            on = exists[lv.n][ty, tx]
            if should_exist and not on:
                st["missing_tiles"].append(f"{lv.n}/{tx}/{ty}")
                continue
            if on and not should_exist:
                st["extra_tiles"].append(f"{lv.n}/{tx}/{ty}")
            if not on:
                continue
            got = decode(TILES / str(lv.n) / str(tx) / f"{ty}.webp")
            st["tiles_on_disk_checked"] += 1
            if got.shape != (3, TILE, TILE) or got.dtype != np.uint8:
                st["bad_shape"].append(f"{lv.n}/{tx}/{ty} {got.shape} {got.dtype}")
                continue
            for k, bit in (("1", 1), ("2", 2), ("4", 4)):
                st["flag_px_found"][k] += int(((got[2] & bit) > 0).sum())
            bad = False
            for ch, name in ((0, "r"), (1, "g")):
                d = got[ch] != exp[ch]
                if d.any():
                    bad = True
                    st["grey_mismatch_px"][name] += int(d.sum())
                    st["grey_mismatch_near_half"][name] += int((d & nr[ch]).sum())
                    st["grey_max_abs_diff"] = max(st["grey_max_abs_diff"], int(np.abs(
                        got[ch].astype(int) - exp[ch].astype(int)).max()))
                    for yy, xx in np.argwhere(d)[:3]:
                        if len(st["examples"]) < MAX_EXAMPLES:
                            st["examples"].append(dict(tile=f"{lv.n}/{tx}/{ty}", px=int(xx), py=int(yy),
                                                       channel=name, expected=int(exp[ch, yy, xx]),
                                                       found=int(got[ch, yy, xx]),
                                                       near_half=bool(nr[ch, yy, xx])))
            d = got[2] != exp[2]
            if d.any():
                bad = True
                st["flag_mismatch_px"] += int(d.sum())
                for yy, xx in np.argwhere(d)[:3]:
                    if len(st["examples"]) < MAX_EXAMPLES:
                        st["examples"].append(dict(tile=f"{lv.n}/{tx}/{ty}", px=int(xx), py=int(yy),
                                                   channel="b", expected=int(exp[2, yy, xx]),
                                                   found=int(got[2, yy, xx])))
            st["tiles_with_mismatch"] += bad

    def push(lv, rgb, near):
        """Append output rows (3, h, w_level) to the level buffer; flush full tile rows."""
        w_tiles = lv.cols * TILE
        h, w = rgb.shape[1:]
        pad = np.zeros((3, h, w_tiles), np.uint8)
        pad[2] = FLAG_OUT
        pad[:, :, :min(w, w_tiles)] = rgb[:, :, :w_tiles]
        npad = np.zeros((2, h, w_tiles), bool)
        npad[:, :, :min(w, w_tiles)] = near[:, :, :w_tiles]
        lv.buf.append((pad, npad))
        while sum(b[0].shape[1] for b in lv.buf) >= TILE:
            allr = np.concatenate([b[0] for b in lv.buf], axis=1)
            alln = np.concatenate([b[1] for b in lv.buf], axis=1)
            check_tile_row(lv, allr[:, :TILE], alln[:, :TILE])
            lv.ty += 1
            rest = (allr[:, TILE:], alln[:, TILE:])
            lv.buf = [rest] if rest[0].shape[1] else []

    native_nd = {y: 0 for y in YEARS}
    for k in range(n_chunks):
        r0 = k * CH
        n = min(CH, H - r0)
        S, V, I = {}, {}, {}
        for y in YEARS:
            a = np.full((CH, WP), np.nan, np.float32)
            a[:n, :W] = raws[y].GetRasterBand(1).ReadAsArray(0, r0, W, n)
            inr = ~np.isnan(a)
            valid = inr & (a != NO_DATA)
            native_nd[y] += int((inr & ~valid).sum())
            S[y] = np.where(valid, np.maximum(np.nan_to_num(a), 0), 0).astype(np.float64)
            V[y], I[y] = valid.astype(np.int32), inr.astype(np.int32)
            del a
        for n_lvl in range(lmax, -1, -1):
            if n_lvl != lmax:
                for y in YEARS:
                    S[y], V[y], I[y] = reduce2(S[y]), reduce2(V[y]), reduce2(I[y])
            gs, ns = [], []
            for y in YEARS:
                g, nr = grey_from(S[y], V[y], curve)
                gs.append(g)
                ns.append(nr)
            flags = (((V[2015] == 0) & (I[2015] > 0)) * FLAG_ND[2015]
                     + ((V[2025] == 0) & (I[2025] > 0)) * FLAG_ND[2025]
                     + (I[2015] == 0) * FLAG_OUT).astype(np.uint8)
            push(levels[n_lvl], np.stack([gs[0], gs[1], flags]), np.stack(ns))
        if k % 8 == 0:
            print(f"chunk {k + 1}/{n_chunks}  {time.time() - t0:.0f}s", flush=True)
    # flush partial last tile rows (padding rows are outside the raster)
    for lv in levels.values():
        while lv.ty < lv.rows:
            have = sum(b[0].shape[1] for b in lv.buf)
            need = TILE - have % TILE if have % TILE else (TILE if not have else 0)
            pad = np.zeros((3, need, lv.cols * TILE), np.uint8)
            pad[2] = FLAG_OUT
            lv.buf.append((pad, np.zeros((2, need, lv.cols * TILE), bool)))
            allr = np.concatenate([b[0] for b in lv.buf], axis=1)
            alln = np.concatenate([b[1] for b in lv.buf], axis=1)
            check_tile_row(lv, allr[:, :TILE], alln[:, :TILE])
            lv.ty += 1
            lv.buf = [(allr[:, TILE:], alln[:, TILE:])] if allr.shape[1] > TILE else []

    res["per_level"] = {}
    all_ok = True
    for n_lvl in sorted(levels):
        st = levels[n_lvl].stats
        ok = (not st["missing_tiles"] and not st["extra_tiles"] and not st["bad_shape"]
              and st["tiles_with_mismatch"] == 0
              and st["tiles_on_disk_checked"] == int(exists[n_lvl].sum()))
        st["pass"] = ok
        for key in ("missing_tiles", "extra_tiles", "bad_shape"):
            st[f"n_{key}"] = len(st[key])
            st[key] = st[key][:20]
        all_ok &= ok
        res["per_level"][n_lvl] = st
    ck["every_level_tiles_match_raw"] = all_ok
    nat = levels[lmax].stats
    res["native_no_data_pixels_raw"] = native_nd
    ck["native_flag1_count_equals_raw_minus_1_5"] = nat["flag_px_found"]["1"] == native_nd[2015]
    ck["native_flag2_count_equals_raw_minus_1_5"] = nat["flag_px_found"]["2"] == native_nd[2025]

    # ---- second decoder cross-check ----
    dw = shutil.which("dwebp")
    all_files = sorted(str(p.relative_to(TILES)) for p in TILES.rglob("*.webp"))
    sample = random.Random(DWEBP_SEED).sample(all_files, min(DWEBP_SAMPLE, len(all_files)))
    agree = 0
    if dw:
        with tempfile.TemporaryDirectory() as td:
            for rel in sample:
                out = os.path.join(td, "t.pam")
                subprocess.run([dw, "-quiet", "-pam", str(TILES / rel), "-o", out], check=True)
                raw = open(out, "rb").read()
                hdr_end = raw.index(b"ENDHDR\n") + len(b"ENDHDR\n")
                hdr = raw[:hdr_end].decode()
                depth = int(hdr.split("DEPTH ")[1].split()[0])
                px = np.frombuffer(raw[hdr_end:], np.uint8).reshape(TILE, TILE, depth)
                agree += np.array_equal(px[:, :, :3].transpose(2, 0, 1), decode(TILES / rel))
    res["second_decoder"] = dict(tool=dw, seed=DWEBP_SEED, sampled=len(sample), agree=agree)
    ck["second_decoder_agrees"] = bool(dw) and agree == len(sample)

    res["pass"] = all(ck.values())
    res["seconds"] = round(time.time() - t0)
    write_result("a04_tiles.json", res)
    print(json.dumps(ck, indent=1))
    print("PASS" if res["pass"] else "FAIL")


if __name__ == "__main__":
    main()
