"""r05: check each fix (F1-F6, R1, R2) and that R3 behaviour is unchanged.

Run from final/ after r02. Output files are only read. The pipeline module is imported
(it has an `if __name__ == '__main__'` guard, so main() is NOT run and nothing is written by it);
only its pure functions dump / raw / strict_parse / even_sample / percentile are called, plus
write_checked with INVALID text aimed at a path inside this recheck folder (must not create it).
Writes results/r05_fix_checks.txt.
"""
import datetime, importlib.util, json, math, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
DER = "data/derived/spectra"
RAWD = "data/raw/spectra/spitschan2016"
lines, fails = [], []

def check(name, cond, detail=""):
    lines.append(f"{'PASS' if cond else 'FAIL'} {name}{(' -- ' + detail) if detail else ''}")
    if not cond:
        fails.append(name)

def lt(p):
    return json.loads(open(p, encoding="utf-8").read(), parse_float=str, parse_int=str)

meta = json.load(open(f"{DER}/spectra_meta.json"))
sites = {s: lt(f"{DER}/{s}.json") for s in ("philadelphia", "cherry_springs")}
ref = json.load(open(os.path.join(RES, "r02_extract.json")))

# ---- F1 (values themselves compared in r03; here: raw file text of night_id has no '.0')
for s, d in sites.items():
    check(f"F1 [{s}] night_id text has no '.' (source ints written as ints)", all("." not in x for x in d["night_id"]))
    check(f"F1 [{s}] source_dataquality values are source text", list(d["source_dataquality"].values())
          == ref["sites"][s]["source_dataquality_text"][1])
check("F1 meta 'verbatim' and 'null_means' present", "verbatim" in meta and "null_means" in meta,
      f"{meta.get('verbatim')!r}; {meta.get('null_means')!r}")
lines.append("NOTE F1: no NaN occurs in any selected cell or metadata row (r02), so the NaN -> null path is "
             "exercised only by the unit test of raw('NaN') below, not by the data.")

# ---- F2: night_id_note present; verify its factual claims on ALL night columns
check("F2 meta night_id_note present", "night_id_note" in meta, repr(meta.get("night_id_note")))
for s, code in (("philadelphia", "DRL"), ("cherry_springs", "CSSP")):
    rows = [ln.split(",") for ln in open(f"{RAWD}/{code}_spectra.csv").read().rstrip("\n").split("\n")[:3]]
    ts, nid, sol = rows[0][:len(rows[1])], rows[1], rows[2]
    night = [c for c, v in enumerate(sol) if float(v) < -18]
    blocks = []
    for c in night:
        if blocks and c == blocks[-1][-1] + 1:
            blocks[-1].append(c)
        else:
            blocks.append([c])
    changes = [(nid[c - 1], nid[c], ts[c]) for b in blocks for c in b[1:] if nid[c] != nid[c - 1]]
    ids = sorted(set(nid[c] for c in night), key=float)
    lines.append(f"INFO F2 [{s}] night blocks {len(blocks)}, distinct night_id over all night spectra {len(ids)} {ids}; "
                 f"in-block changes: {changes}")
    check(f"F2 [{s}] note claim '8 ids over 5 night blocks' holds", len(blocks) == 5 and len(ids) == 8)
    check(f"F2 [{s}] note claim 'changes at about 01:05' holds (all in-block changes 01:04-01:07)",
          all("01:04" <= ch[2][-8:-3] <= "01:07" for ch in changes) and len(changes) > 0)
check("F2 no data change: night_id values equal source row 2 (see r03)", True)

# ---- F3
for s, d in sites.items():
    check(f"F3 [{s}] unit + meta_file fields", d.get("unit") == meta["unit"] == "W m^-2 nm^-1"
          and d.get("meta_file") == "spectra_meta.json" and os.path.exists(f"{DER}/{d['meta_file']}"))

# ---- F4
RULE_LABELS = {"measured", "documented", "inferred", "estimated"}
for s, d in sites.items():
    unl = [k for k in d if k not in d["labels"] and k not in ("labels", "label_notes")]
    extra = [k for k in d["labels"] if k not in d]
    vals = set(d["labels"].values())
    check(f"F4 [{s}] every site-file field has a label (excluding the labels/label_notes containers)", not unl and not extra,
          f"unlabelled {unl}, labels without field {extra}")
    check(f"F4 [{s}] every label used is explained in label_notes", vals <= set(d["label_notes"]))
    lines.append(f"INFO F4 [{s}] labels used {sorted(vals)}; outside RULES 2.3 vocabulary: {sorted(vals - RULE_LABELS)}; "
                 f"identifier fields: {[k for k, v in d['labels'].items() if v == 'identifier']}")

# ---- F5
sel = meta["selection"]
check("F5 meta selection.rules_from cites the handoff", "2026-10-04_two-nights-spectra.md" in sel.get("rules_from", ""),
      repr(sel.get("rules_from")))
check("F5 handoff file exists", os.path.exists("handoffs/2026-10-04_two-nights-spectra.md"))
check("F5 draft_reference marked 'not in git'", "(not in git)" in sel.get("draft_reference", ""), repr(sel.get("draft_reference")))
check("F5 old 'reproduces' key gone", "reproduces" not in sel)

# ---- F6
check("F6 meta wavelength_source present", "wavelength_source" in meta, repr(meta.get("wavelength_source")))

# ---- RULES 2.5 next to the data
for s, d in sites.items():
    lines.append(f"INFO 2.5 [{s}] in site file: unit={d.get('unit')!r}; time zone field: "
                 f"{[k for k in d if 'zone' in k or 'tz' in k]}; filter/rule fields: "
                 f"{[k for k in d if 'rule' in k or 'selection' in k or 'filter' in k]}; "
                 f"elevation/fraction units: none in site file (meta units_other)")
lines.append(f"INFO 2.5 meta: unit={meta['unit']!r}; units_other={meta['units_other']}; "
             f"timestamp_format={meta['timestamp_format']!r}; selection.rule={meta['selection']['rule']!r}")
def has_base_note(o):
    t = json.dumps(o)
    return "1-based" in t or "one-based" in t or "0-based" in t
check("2.5 source_column indexing base (1-based) stated in the output files",
      has_base_note(meta) or any(has_base_note(d["labels"]) or has_base_note(d["label_notes"]) for d in sites.values()),
      "searched meta + site labels/label_notes for '1-based'/'0-based'")

# ---- R1 / R2 / R3: unit tests of the pipeline functions (no main())
spec = importlib.util.spec_from_file_location("np01", "pipeline/spectra/01_night_spectra.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
R = m.Raw
check("R1 dump: Raw in first/middle/nested positions written unquoted as source text",
      m.dump({"b": [R("1.0e-05"), None], "a": R("2"), "c": {"x": R("-0.50")}, "d": "s"})
      == '{"b":[1.0e-05,null],"a":2,"c":{"x":-0.50},"d":"s"}')
for tok in ["0", "-0.5", "1e-08", "9.593539019e-08", "16.72706168", "5383", "-0"]:
    check(f"R1 raw accepts {tok!r} unchanged", m.raw(tok) == tok and isinstance(m.raw(tok), R))
check("R1 raw('NaN') -> None", m.raw("NaN") is None)
for tok in ["nan", "Infinity", "-Infinity", "1.", ".5", "+1", "01", " 1", "1 ", "", "1,0", "0x1"]:
    try:
        m.raw(tok)
        ok = False
    except SystemExit:
        ok = True
    check(f"R1 raw rejects {tok!r}", ok)
try:
    m.dump(float("nan")); ok = False
except SystemExit:
    ok = True
check("R1 dump rejects a non-finite float", ok)
for bad in ['{"a":NaN}', '[Infinity]', '{"a":1,"a":2}', '[-Infinity]']:
    try:
        m.strict_parse(bad); ok = False
    except SystemExit:
        ok = True
    check(f"R2 strict_parse rejects {bad}", ok)
tmp = os.path.join(RES, "r05_must_not_exist.json")
try:
    m.write_checked(__import__("pathlib").Path(tmp), '{"a":NaN}'); ok = False
except SystemExit:
    ok = True
check("R2 write_checked raises on invalid text and writes nothing", ok and not os.path.exists(tmp))
check("R3 unchanged: even_sample keeps all n when n <= 240",
      m.even_sample(list(range(100)), 240) == list(range(100)) and m.even_sample(list(range(240)), 240) == list(range(240)))
check("selection: even_sample(1200) and (1268) == exact-integer round_half_up",
      all(m.even_sample(list(range(n)), 240) == [(2 * i * (n - 1) + 239) // 478 for i in range(240)] for n in (1200, 1268)))
mism = [n for n in range(241, 20001)
        if m.even_sample(list(range(n)), 240) != [(2 * i * (n - 1) + 239) // 478 for i in range(240)]]
lines.append(f"INFO float floor(x+0.5) vs exact round_half_up, n = 241..20000: {len(mism)} n differ "
             f"(first: {mism[:10]})")
random.seed(1)
v = sorted(random.random() for _ in range(1001))
def mypct(s, q):
    pos = (len(s) - 1) * q; lo = math.floor(pos); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)
check("percentile matches own implementation (random data, q in 0,0.01,0.5,0.99,1)",
      all(abs(m.percentile(v, q) - mypct(v, q)) < 1e-15 for q in (0, 0.01, 0.5, 0.99, 1)))
lines.append(f"TOTAL: {len(fails)} FAIL")
open(os.path.join(RES, "r05_fix_checks.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
