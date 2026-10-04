"""r03: compare every field of the NEW outputs with r02 (independent extraction).

Run from final/ after r02. Reads the outputs twice:
  (a) strict text mode: parse_float=str, parse_int=str, NaN/Infinity rejected, duplicate keys rejected
      -> tests source-text identity of every number;
  (b) float mode -> tests numeric equality.
Writes results/r03_compare_new.txt.
"""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DER = "data/derived/spectra"
ref = json.load(open(os.path.join(RES, "r02_extract.json")))
lines, fails = [], []

def no_dupes(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate keys: {keys}")
    return dict(pairs)

def bad_const(c):
    raise ValueError(f"non-standard JSON constant {c}")

def load_text(p):
    with open(p, "rb") as f:
        raw = f.read()
    s = raw.decode("utf-8")  # strict UTF-8
    return json.loads(s, parse_float=str, parse_int=str, parse_constant=bad_const, object_pairs_hook=no_dupes), raw

def load_float(p):
    return json.loads(open(p, encoding="utf-8").read(), parse_constant=bad_const, object_pairs_hook=no_dupes)

def check(name, cond, detail=""):
    lines.append(f"{'PASS' if cond else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")
    if not cond:
        fails.append(name)

def num_eq(a_text, b_text):
    if a_text is None or b_text == "NaN":
        return a_text is None and b_text == "NaN"
    return float(a_text) == float(b_text)

meta_t, meta_raw = load_text(f"{DER}/spectra_meta.json")
meta_f = load_float(f"{DER}/spectra_meta.json")
check("spectra_meta.json strict parse (UTF-8, no NaN/Infinity, no duplicate keys)", True)

for site, r in ref["sites"].items():
    p = f"{DER}/{site}.json"
    t, raw = load_text(p)
    fl = load_float(p)
    check(f"[{site}] strict parse (UTF-8, no NaN/Infinity, no duplicate keys)", True)
    outside = re.sub(rb'"(?:[^"\\]|\\.)*"', b'""', raw)  # remove JSON string literals
    check(f"[{site}] no NaN/Infinity tokens outside string literals",
          b"NaN" not in outside and b"Infinity" not in outside)
    # scalar counts (text)
    for k in ["n_source_spectra", "n_night_spectra", "n_selected"]:
        check(f"[{site}] {k} text", t[k] == str(r[k]), f"{t[k]} vs {r[k]}")
    check(f"[{site}] source_date_range (column order first/last)", t["source_date_range"] == r["source_date_range_columnorder"],
          f"{t['source_date_range']}")
    check(f"[{site}] selected_date_range", t["selected_date_range"] == r["selected_date_range"], f"{t['selected_date_range']}")
    dqk, dqv = r["source_dataquality_text"]
    check(f"[{site}] source_dataquality keys+order+text", list(t["source_dataquality"].items()) == list(zip(dqk, dqv)),
          f"{t['source_dataquality']}")
    sc = {k: str(v) for k, v in r["selected_cells"].items() if k != "negative"}
    check(f"[{site}] selected_cells", t["selected_cells"] == sc, f"{t['selected_cells']} vs {sc}")
    check(f"[{site}] source_column == my 0-based column + 1", t["source_column"] == [str(c + 1) for c in r["col0"]])
    check(f"[{site}] source_column != my 0-based column (i.e. it is 1-based)", t["source_column"] != [str(c) for c in r["col0"]])
    for k in ["timestamp", "night_id", "solar_elevation_deg", "lunar_elevation_deg", "lunar_illuminated_fraction"]:
        a, b = t[k], r[k]
        nt = sum(x == y for x, y in zip(a, b))
        nf = sum(num_eq(x, y) if k != "timestamp" else x == y for x, y in zip(a, b))
        check(f"[{site}] {k}: length 240, text identical {nt}/240, float-equal {nf}/240",
              len(a) == 240 and nt == 240 and nf == 240)
    a, b = t["irradiance"], r["irradiance"]
    shape = len(a) == 240 and all(len(x) == 281 for x in a)
    ntext = sum(x == y for ra, rb in zip(a, b) for x, y in zip(ra, rb))
    nfl = sum(num_eq(x, y) for ra, rb in zip(a, b) for x, y in zip(ra, rb))
    nnull = sum(x is None for ra in a for x in ra)
    check(f"[{site}] irradiance shape 240x281, text identical {ntext}/67440, float-equal {nfl}/67440, nulls {nnull}",
          shape and ntext == 67440 and nfl == 67440)
    # float mode: type sanity
    check(f"[{site}] float mode: irradiance all numbers/None, night_id ints",
          all(isinstance(x, (int, float)) or x is None for ra in fl["irradiance"] for x in ra)
          and all(isinstance(x, int) for x in fl["night_id"]))
    # meta sites block
    ms = meta_t["sites"][site]
    check(f"[{site}] meta.sites block equals site file counts",
          ms["n_source_spectra"] == t["n_source_spectra"] and ms["n_night_spectra"] == t["n_night_spectra"]
          and ms["n_selected"] == t["n_selected"] and ms["selected_cells"] == t["selected_cells"])

d = ref["display_limits_log10"]
m = meta_t["display_limits_log10"]
for k in ["n_positive", "floor", "ceil"]:
    check(f"meta display {k} text", m[k] == str(d[k]), f"{m[k]} vs {d[k]}")
for k in ["p01", "p50", "p99"]:
    check(f"meta display {k} text == repr(my float)", m[k] == repr(d[k]), f"{m[k]} vs {d[k]!r}")
check("meta wavelength_nm == 280..840 step 2 (281 values)", meta_f["wavelength_nm"] == ref["wavelength_nm"])
check("meta wavelength_step_nm == 2", meta_f["wavelength_step_nm"] == 2)
lines.append(f"TOTAL: {len(fails)} FAIL")
open(os.path.join(RES, "r03_compare_new.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
