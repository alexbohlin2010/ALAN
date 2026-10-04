"""Compare the pipeline outputs (data/derived/spectra/*.json) with the independent extraction (results/a02_extract.json)
cell by cell: as exact number text (JSON literals read with parse_float/parse_int=str) and as floats. Also checks JSON
validity (strict: no NaN/Infinity, no duplicate keys), lengths, metadata and display limits. Run from final/.
Writes results/a03_compare.txt."""
import json, math, hashlib
D = "data/derived/spectra"
OUT = "audits/night_spectra/results"
A = json.load(open(f"{OUT}/a02_extract.json"))
log = []
P = lambda *a: log.append(" ".join(str(x) for x in a))

def bad_const(c): raise ValueError(f"non-standard JSON constant {c}")
def no_dupes(pairs):
    ks = [k for k, _ in pairs]
    if len(ks) != len(set(ks)): raise ValueError(f"duplicate keys {ks}")
    return dict(pairs)
def load_text(p):   # numbers kept as their literal text
    return json.load(open(p, encoding="utf-8"), parse_float=str, parse_int=str, parse_constant=bad_const, object_pairs_hook=no_dupes)
def load_num(p):
    return json.load(open(p, encoding="utf-8"), parse_constant=bad_const, object_pairs_hook=no_dupes)
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

for f in ("philadelphia.json", "cherry_springs.json", "spectra_meta.json"):
    try:
        load_text(f"{D}/{f}"); P(f"{f}: strict JSON parse OK (no NaN/Infinity, no duplicate keys), utf-8")
    except Exception as e:
        P(f"{f}: JSON PROBLEM {e}")

M = load_num(f"{D}/spectra_meta.json")
for site, a in A["sites"].items():
    T = load_text(f"{D}/{site}.json"); J = load_num(f"{D}/{site}.json")
    P(f"\n[{site}]")
    P("  source_file equal:", J["source_file"] == a["source_file"])
    P("  source_sha256 equals actual raw file sha256:", J["source_sha256"] == sha(a["source_file"]))
    for k_out, k_a in (("n_source_spectra", "n_source_spectra"), ("n_night_spectra", "n_night_spectra")):
        P(f"  {k_out}: output {J[k_out]} mine {a[k_a]} equal {J[k_out] == a[k_a]}")
    P("  n_selected:", J["n_selected"], "equal 240:", J["n_selected"] == 240)
    P("  source_date_range equal:", J["source_date_range"] == a["source_date_range"], J["source_date_range"])
    P("  selected_date_range equal:", J["selected_date_range"] == a["selected_date_range"], J["selected_date_range"])
    P("  source_dataquality equal to raw *_dataquality.csv:", J["source_dataquality"] == a["dataquality"])
    c = a["counts"]
    mine_cells = {"total": c["total"], "null_nan": c["nan"], "zero": c["zero"], "positive": c["positive"]}
    P("  selected_cells equal:", J["selected_cells"] == mine_cells, J["selected_cells"], "| meta copy equal:",
      M["sites"][site]["selected_cells"] == J["selected_cells"],
      "| meta n_* equal:", all(M["sites"][site][k] == J[k] for k in ("n_source_spectra", "n_night_spectra", "n_selected")))
    sc = J["source_column"]
    P("  source_column: len", len(sc), "equal to mine (1-based):", sc == a["source_column_1based"],
      "| distinct", len(set(sc)), "| strictly increasing", all(x < y for x, y in zip(sc, sc[1:])))
    if sc != a["source_column_1based"]:
        d0 = [i for i, (x, y) in enumerate(zip(sc, a["source_column_1based"])) if x != y]
        P("    first differing selection index:", d0[:10], "output", [sc[i] for i in d0[:5]], "mine", [a["source_column_1based"][i] for i in d0[:5]])
    P("  timestamp equal (exact text):", J["timestamp"] == a["timestamp"])
    for k in ("night_id", "solar_elevation_deg", "lunar_elevation_deg", "lunar_illuminated_fraction"):
        lit = T[k]; src = a[k]
        same_text = sum(x == y for x, y in zip(lit, src))
        same_float = sum(float(x) == float(y) for x, y in zip(lit, src))
        diffs = [(x, y) for x, y in zip(lit, src) if x != y]
        P(f"  {k}: len {len(lit)}; exact-text equal {same_text}/{len(src)}; float equal {same_float}/{len(src)}"
          + (f"; text differences e.g. output {diffs[0][0]!r} vs source {diffs[0][1]!r} ({len(diffs)} cells)" if diffs else ""))
    # irradiance
    LI = T["irradiance"]; src = a["irradiance_text"]
    shape_ok = len(LI) == 240 and all(len(r) == 281 for r in LI)
    n = txt = flt = nulls = null_match = 0; diffs = []
    for i in range(240):
        for j in range(281):
            o = LI[i][j]; s = src[i][j]; n += 1
            if o is None:
                nulls += 1; null_match += (s == "NaN"); continue
            if s == "NaN": diffs.append((i, j, o, s)); continue
            txt += (o == s)
            if float(o) == float(s): flt += 1
            else: diffs.append((i, j, o, s))
    textdiff = [(i, j, LI[i][j], src[i][j]) for i in range(240) for j in range(281)
                if LI[i][j] is not None and LI[i][j] != src[i][j]]
    P(f"  irradiance shape 240 x 281: {shape_ok}; cells {n}; null {nulls} (source NaN at those: {null_match});"
      f" exact-text equal {txt}; float equal {flt}; float differences {len(diffs)}")
    P(f"  irradiance cells whose output literal text differs from the source text: {len(textdiff)}"
      + (f"; e.g. {textdiff[:5]}" if textdiff else ""))
    if textdiff:
        kinds = {}
        for _, _, o, s in textdiff:
            key = ("source '0' -> output " + repr(o)) if s == "0" else "other"
            kinds[key] = kinds.get(key, 0) + 1
        P("    kinds:", kinds)
    neg = sum(1 for r in J["irradiance"] for v in r if v is not None and v < 0)
    P(f"  irradiance negatives in output: {neg}; min>0 {min(v for r in J['irradiance'] for v in r if v)!r}; "
      f"max {max(v for r in J['irradiance'] for v in r if v is not None)!r}")
    P("  labels:", J["labels"])
    P("  top-level keys:", list(J.keys()))

P("\n[spectra_meta]")
P("  wavelength_nm == 280..840 step 2:", M["wavelength_nm"] == A["wavelength_nm"], "len", len(M["wavelength_nm"]),
  "| wavelength_step_nm", M["wavelength_step_nm"])
dl = M["display_limits_log10"]; mine = A["display_limits_log10"]
for k in ("n_positive", "p01", "p50", "p99", "floor", "ceil"):
    P(f"  display {k}: output {dl[k]!r} mine {mine[k]!r} equal {dl[k] == mine[k]}"
      + ("" if dl[k] == mine[k] else f" absdiff {abs(dl[k] - mine[k])!r}"))
P("  display label:", dl.get("label"), "| rule present:", bool(dl.get("rule")))
P("  selection:", M["selection"])
P("  unit:", M.get("unit"), "| quantity:", M.get("quantity"), "| timestamp_format:", M.get("timestamp_format"))
P("  units_other:", M.get("units_other"), "| null_means:", M.get("null_means"))
P("  files exist:", {k: __import__("os").path.exists(f"{D}/{v}") for k, v in M["files"].items()}, "| script:", M.get("script"))
P("  top-level keys:", list(M.keys()))
open(f"{OUT}/a03_compare.txt", "w").write("\n".join(log) + "\n")
print("\n".join(log))
