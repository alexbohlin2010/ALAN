"""r02: independent extraction from the raw CSVs (written and run BEFORE reading the pipeline script).

Run from final/: python3 audits/night_spectra/recheck_2026-10-04/r02_independent_extract.py

Own parser (plain str.split on ',' after checking the file has no quotes / CR), own selection,
own percentile. Every value is kept as its exact source text. Rules (from the task brief and
handoffs/2026-10-04_two-nights-spectra.md):
  night     = float(solar elevation text) < -18 (strict); NaN never passes
  sampling  = 240 of the n night spectra in source column order, k_i = round_half_up(i*(n-1)/239),
              computed with exact integers: k_i = (2*i*(n-1) + 239) // 478
  wavelengths 280..840 step 2 -> data row (1-based) 6 + (wl - 280)
  display   = log10 of every selected value > 0 of both sites, sorted; percentile q at
              index (N-1)*q with linear interpolation; floor(p01), ceil(p99)
Writes results/r02_extract.json and results/r02_log.txt.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
RAW = "data/raw/spectra/spitschan2016"
SITES = {"philadelphia": "DRL", "cherry_springs": "CSSP"}
log = []

def read_rows(path):
    with open(path, "rb") as f:
        b = f.read()
    assert b"\r" not in b and b'"' not in b, "unexpected CR or quote"
    text = b.decode("ascii")
    assert text.endswith("\n")
    return [ln.split(",") for ln in text[:-1].split("\n")]

def rhu(i, n):
    return (2 * i * (n - 1) + 239) // 478

out = {"sites": {}}
all_pos_logs = []
for site, code in SITES.items():
    rows = read_rows(f"{RAW}/{code}_spectra.csv")
    log.append(f"[{site}] {code}_spectra.csv: {len(rows)} lines; field counts per line: "
               f"{sorted(set(len(r) for r in rows))}")
    assert len(rows) == 566
    # row 1 ends with a trailing comma -> one empty extra field
    ts = rows[0]
    if ts[-1] == "":
        ts = ts[:-1]
        log.append(f"[{site}] row 1 has a trailing empty field (removed)")
    n = len(ts)
    assert all(len(r) == n for r in rows[1:]), "ragged rows"
    assert all(t != "" for t in ts)
    # every non-timestamp token is a number or NaN
    tok_kinds = {"NaN": 0, "num": 0, "other": 0}
    for ri in range(1, 566):
        for v in rows[ri]:
            if v == "NaN":
                tok_kinds["NaN"] += 1
            else:
                try:
                    x = float(v)
                    tok_kinds["num" if math.isfinite(x) else "other"] += 1
                except ValueError:
                    tok_kinds["other"] += 1
    log.append(f"[{site}] tokens rows 2-566: {tok_kinds}")
    nid, sol, lun, frac = rows[1], rows[2], rows[3], rows[4]
    meta_nan = {name: sum(1 for v in r if v == "NaN") for name, r in
                [("night_id", nid), ("solar", sol), ("lunar", lun), ("fraction", frac)]}
    log.append(f"[{site}] NaN in metadata rows: {meta_nan}")
    eq18 = [c for c, v in enumerate(sol) if v != "NaN" and float(v) == -18.0]
    log.append(f"[{site}] columns with solar elevation exactly -18: {eq18}")
    night = [c for c, v in enumerate(sol) if v != "NaN" and float(v) < -18]
    nn = len(night)
    k = [rhu(i, nn) for i in range(240)]
    kf = [math.floor(i * (nn - 1) / 239 + 0.5) for i in range(240)]
    ties = [i for i in range(240) if (2 * i * (nn - 1)) % 478 == 239]
    log.append(f"[{site}] n columns {n}, night {nn}, exact-int vs float floor(x+.5) indices equal: {k == kf}, "
               f"exact .5 ties: {ties}")
    sel = [night[j] for j in k]
    assert len(set(sel)) == 240 and sel == sorted(sel)
    wl = list(range(280, 841, 2))
    wl_rows = [5 + (w - 280) for w in wl]  # 0-based line index; line 6 (1-based) = 280 nm
    irr = [[rows[r][c] for r in wl_rows] for c in sel]
    cells = [v for spec in irr for v in spec]
    nan_c = sum(v == "NaN" for v in cells)
    zero_c = sum(v != "NaN" and float(v) == 0 for v in cells)
    pos_c = sum(v != "NaN" and float(v) > 0 for v in cells)
    neg_c = sum(v != "NaN" and float(v) < 0 for v in cells)
    all_pos_logs += [math.log10(float(v)) for v in cells if v != "NaN" and float(v) > 0]
    # date ranges
    chrono_sorted = None
    import datetime
    dts = [datetime.datetime.strptime(t, "%d-%b-%Y %H:%M:%S") for t in ts]
    mono = all(dts[i] < dts[i + 1] for i in range(n - 1))
    log.append(f"[{site}] timestamps strictly increasing in column order: {mono}; duplicates: {n - len(set(ts))}")
    # night blocks (consecutive night columns)
    blocks = []
    for c in night:
        if blocks and c == blocks[-1][-1] + 1:
            blocks[-1].append(c)
        else:
            blocks.append([c])
    per_block = [sum(1 for c in sel if b[0] <= c <= b[-1]) for b in blocks]
    log.append(f"[{site}] night blocks: {len(blocks)}, selected per block: {per_block}; "
               f"distinct night_id in selection: {sorted(set(nid[c] for c in sel), key=float)}")
    with open(f"{RAW}/{code}_dataquality.csv", "rb") as f:
        dq = f.read().decode("ascii")
    dql = dq.rstrip("\n").split("\n")
    assert len(dql) == 2
    dqk, dqv = dql[0].split(","), dql[1].split(",")
    log.append(f"[{site}] dataquality: {dict(zip(dqk, dqv))}; N final == n columns: {dqv[-1] == str(n)}")
    out["sites"][site] = {
        "n_source_spectra": n, "n_night_spectra": nn, "n_selected": len(sel),
        "source_date_range_columnorder": [ts[0], ts[-1]],
        "selected_date_range": [ts[sel[0]], ts[sel[-1]]],
        "source_dataquality_text": [dqk, dqv],
        "selected_cells": {"total": len(cells), "null_nan": nan_c, "zero": zero_c, "positive": pos_c, "negative": neg_c},
        "col0": sel,
        "timestamp": [ts[c] for c in sel],
        "night_id": [nid[c] for c in sel],
        "solar_elevation_deg": [sol[c] for c in sel],
        "lunar_elevation_deg": [lun[c] for c in sel],
        "lunar_illuminated_fraction": [frac[c] for c in sel],
        "irradiance": irr,
    }
    log.append(f"[{site}] cells {len(cells)}: NaN {nan_c}, zero {zero_c}, positive {pos_c}, negative {neg_c}")

def pct(sorted_vals, q):
    pos = (len(sorted_vals) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)

s = sorted(all_pos_logs)
p01, p50, p99 = pct(s, 0.01), pct(s, 0.50), pct(s, 0.99)
out["display_limits_log10"] = {"n_positive": len(s), "p01": p01, "p50": p50, "p99": p99,
                               "floor": math.floor(p01), "ceil": math.ceil(p99)}
out["wavelength_nm"] = list(range(280, 841, 2))
log.append(f"display: {out['display_limits_log10']}")
with open(os.path.join(RES, "r02_extract.json"), "w") as f:
    json.dump(out, f)
with open(os.path.join(RES, "r02_log.txt"), "w") as f:
    f.write("\n".join(log) + "\n")
print("\n".join(log))
