"""Independent extraction from the raw Spitschan 2016 CSVs (run from final/, stdlib only). Written and run BEFORE
reading pipeline/spectra/01_night_spectra.py. Imports nothing from pipeline/.
Rules applied (from the human decisions given to the auditor):
  night = float(row 3) < -18 (strict); selection = night[round_half_up(i*(n-1)/239)], i=0..239;
  wavelengths 280,282,...,840 (CSV rows 6 + (wl-280)); values kept as the exact source text; 'NaN' -> null.
  display limits: log10 of every selected value > 0 (both sites pooled), sorted, linear-interpolation percentile at
  index (N-1)*q; floor(p01), ceil(p99).
Writes results/a02_extract.json (selected cells as source text) and results/a02_log.txt."""
import json, math
from fractions import Fraction
RAW = "data/raw/spectra/spitschan2016"
OUT = "audits/night_spectra/results"
SITES = [("philadelphia", "DRL"), ("cherry_springs", "CSSP")]
log = []
P = lambda *a: log.append(" ".join(str(x) for x in a))

def read_rows(path):
    b = open(path, "rb").read()
    assert b"\r" not in b and b'"' not in b, "unexpected CR or quote"
    t = b.decode("ascii")
    assert t.endswith("\n")
    rows = [ln.split(",") for ln in t[:-1].split("\n")]
    trail = [i + 1 for i, r in enumerate(rows) if r[-1] == ""]
    P(f"  {path}: rows ending in an empty field (trailing comma), 1-based: {trail}; empty fields elsewhere: "
      f"{sum(v == '' for r in rows for v in r[:-1])}")
    for i in trail: rows[i - 1] = rows[i - 1][:-1]   # drop the trailing empty field only
    return rows

def read_quality(path):
    h, v = open(path, encoding="ascii").read().strip().split("\n")
    return dict(zip(h.split(","), (int(x) for x in v.split(","))))

def rhu_float(x): return math.floor(x + 0.5)          # JS Math.round on the float value
def rhu_exact(i, n): return (2 * i * (n - 1) + 239) // 478   # exact round-half-up of i*(n-1)/239

out = {"wavelength_nm": list(range(280, 841, 2)), "sites": {}}
pooled = []
for site, code in SITES:
    rows = read_rows(f"{RAW}/{code}_spectra.csv")
    q = read_quality(f"{RAW}/{code}_dataquality.csv")
    ncol = {len(r) for r in rows}
    P(f"[{site}] {code}_spectra.csv: rows {len(rows)}, columns per row {sorted(ncol)}; dataquality {q}")
    assert len(rows) == 566 and len(ncol) == 1
    C = len(rows[0])
    P(f"  columns == dataquality 'N final spectra': {C == q['N final spectra']}")
    # metadata row checks
    for r in (2, 3, 4, 5):
        vals = rows[r - 1]
        nn = sum(v == "NaN" for v in vals)
        fl = [float(v) for v in vals if v != "NaN"]
        P(f"  row {r}: NaN {nn}, min {min(fl)}, max {max(fl)}, distinct {len(set(vals))}")
    ts = rows[0]
    P(f"  timestamps: distinct {len(set(ts))} of {C}; first {ts[0]}; last {ts[-1]}")
    # irradiance block, all columns
    blk = rows[5:]
    nan = sum(v == "NaN" for r in blk for v in r)
    neg = sum(1 for r in blk for v in r if v != "NaN" and float(v) < 0)
    zero = sum(1 for r in blk for v in r if v != "NaN" and float(v) == 0)
    P(f"  all-column irradiance cells: {C * 561}, NaN {nan}, zero {zero}, negative {neg}")
    sol = [float(v) for v in rows[2]]
    night = [c for c in range(C) if sol[c] < -18]
    n = len(night)
    P(f"  night columns (solar < -18): {n}; solar == -18 exactly: {sum(s == -18 for s in sol)}")
    # night runs (contiguous column blocks)
    runs = []
    for c in night:
        if runs and c == runs[-1][1] + 1: runs[-1][1] = c
        else: runs.append([c, c])
    P(f"  night blocks (0-based column ranges): {len(runs)}: {runs}")
    P(f"  night ids per block: {[sorted(set(rows[1][a:b + 1])) for a, b in runs]}")
    idx_f = [rhu_float(i * (n - 1) / 239) for i in range(240)]
    idx_e = [rhu_exact(i, n) for i in range(240)]
    P(f"  float vs exact round-half-up indices identical: {idx_f == idx_e}; exact .5 ties: "
      f"{sum(Fraction(i * (n - 1), 239).denominator == 2 for i in range(240))}")
    sel = [night[k] for k in idx_e]
    P(f"  selected: {len(sel)}, distinct {len(set(sel))}, strictly increasing {all(a < b for a, b in zip(sel, sel[1:]))}, "
      f"first/last night used {sel[0] == night[0]}/{sel[-1] == night[-1]}")
    wl_rows = [6 + (w - 280) for w in range(280, 841, 2)]   # 1-based CSV rows
    irr = [[rows[r - 1][c] for r in wl_rows] for c in sel]
    cells = [v for s in irr for v in s]
    sel_nan = sum(v == "NaN" for v in cells)
    sel_zero = sum(1 for v in cells if v != "NaN" and float(v) == 0)
    sel_neg = sum(1 for v in cells if v != "NaN" and float(v) < 0)
    sel_pos = [float(v) for v in cells if v != "NaN" and float(v) > 0]
    P(f"  selected cells {len(cells)}: NaN {sel_nan}, zero {sel_zero}, negative {sel_neg}, positive {len(sel_pos)}; "
      f"min>0 {min(sel_pos)}, max {max(sel_pos)}")
    P(f"  zero text forms: {sorted({v for v in cells if v != 'NaN' and float(v) == 0})}; "
      f"texts with exponent: {sum(('e' in v or 'E' in v) for v in cells)}")
    pooled += [math.log10(v) for v in sel_pos]
    out["sites"][site] = {
        "source_file": f"{RAW}/{code}_spectra.csv", "n_source_spectra": C, "n_night_spectra": n,
        "source_column_1based": [c + 1 for c in sel],
        "timestamp": [rows[0][c] for c in sel], "night_id": [rows[1][c] for c in sel],
        "solar_elevation_deg": [rows[2][c] for c in sel], "lunar_elevation_deg": [rows[3][c] for c in sel],
        "lunar_illuminated_fraction": [rows[4][c] for c in sel],
        "source_date_range": [ts[0], ts[-1]], "selected_date_range": [rows[0][sel[0]], rows[0][sel[-1]]],
        "dataquality": q,
        "counts": {"total": len(cells), "nan": sel_nan, "zero": sel_zero, "negative": sel_neg, "positive": len(sel_pos)},
        "irradiance_text": irr,
    }
pooled.sort()
N = len(pooled)
def pct(qq):
    x = (N - 1) * qq; lo = math.floor(x); hi = math.ceil(x)
    return pooled[lo] + (pooled[hi] - pooled[lo]) * (x - lo)
p01, p50, p99 = pct(0.01), pct(0.5), pct(0.99)
out["display_limits_log10"] = {"n_positive": N, "p01": p01, "p50": p50, "p99": p99,
                               "floor": math.floor(p01), "ceil": math.ceil(p99)}
P(f"[pooled] n_positive {N}, p01 {p01!r}, p50 {p50!r}, p99 {p99!r}, floor {math.floor(p01)}, ceil {math.ceil(p99)}")
P(f"  log10 range of selected positives: {pooled[0]!r} .. {pooled[-1]!r}")
json.dump(out, open(f"{OUT}/a02_extract.json", "w"))
open(f"{OUT}/a02_log.txt", "w").write("\n".join(log) + "\n")
print("\n".join(log))
