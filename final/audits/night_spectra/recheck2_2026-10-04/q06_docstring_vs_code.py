"""Recheck2 q06: script docstring vs code vs outputs, for the C1/C2 changes. The script is parsed with `ast`
(never imported or run). Literal constants SITE_LABELS, LABEL_NOTES, NOT_VALUES and the source_column_note literal
are compared with the outputs; the docstring's label sentences are compared with SITE_LABELS / NOT_VALUES.
Writes results/q06_docstring_vs_code.txt."""
import ast, json, re
R = "audits/night_spectra/recheck2_2026-10-04/results"
src = open("pipeline/spectra/01_night_spectra.py", encoding="utf-8").read()
tree = ast.parse(src)
doc = ast.get_docstring(tree)
consts = {}
for n in tree.body:
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in (
            "SITE_LABELS", "LABEL_NOTES", "NOT_VALUES"):
        consts[n.targets[0].id] = ast.literal_eval(n.value)
note_lit = None
for n in ast.walk(tree):
    if isinstance(n, ast.Dict):
        for k, v in zip(n.keys, n.values):
            if isinstance(k, ast.Constant) and k.value == "source_column_note":
                note_lit = ast.literal_eval(v)
L, ok = [], True
def chk(name, cond):
    global ok
    ok &= bool(cond); L.append(f"{'PASS' if cond else 'FAIL'} {name}")
meta = json.load(open("data/derived/spectra/spectra_meta.json"))
for f in ("philadelphia.json", "cherry_springs.json"):
    d = json.load(open(f"data/derived/spectra/{f}"))
    chk(f"{f}: labels == SITE_LABELS (incl. order)", list(d["labels"].items()) == list(consts["SITE_LABELS"].items()))
    chk(f"{f}: label_notes == LABEL_NOTES", d["label_notes"] == consts["LABEL_NOTES"])
    chk(f"{f}: not_values == NOT_VALUES", d["not_values"] == consts["NOT_VALUES"])
chk("spectra_meta source_column_note == code literal", meta.get("source_column_note") == note_lit)
chk("code writes source_column as j + 1 (1-based) with comment", "'source_column': [j + 1 for j in cols],  # 1-based" in src)
chk("code check: unlabelled-field guard subtracts SITE_LABELS, NOT_VALUES and the 3 containers",
    "missing = set(doc) - set(SITE_LABELS) - set(NOT_VALUES) - {'labels', 'label_notes', 'not_values'}" in src)
chk("'identifier' absent from script", "identifier" not in src)
# docstring label sentences
flat = " ".join(doc.split())
chk("docstring mentions round 3k C1 (1-based) and C2 (no non-RULES label)",
    "C1 (state that source_column is 1-based)" in flat and "C2 (no non-RULES label)" in flat)
m = re.search(r"Labels \(RULES 2\.3\), every field of the site files: (.*?)`site`", flat)
L.append("docstring label sentence: " + (m.group(1) if m else "NOT FOUND"))
SL = consts["SITE_LABELS"]
expect = {"measured": {"irradiance", "timestamp"},
          "documented": {"night_id", "solar_elevation_deg", "lunar_elevation_deg", "lunar_illuminated_fraction",
                         "place", "paper_label", "unit", "source_dataquality"},
          "inferred": {"source_column", "n_source_spectra", "n_night_spectra", "n_selected", "source_date_range",
                       "selected_date_range", "selected_cells", "source_sha256"}}
for lab, keys in expect.items():
    chk(f"docstring '{lab}' group == SITE_LABELS keys labelled {lab}", {k for k, v in SL.items() if v == lab} == keys)
chk("docstring: display limits inferred == meta display_limits_log10.label",
    meta["display_limits_log10"]["label"] == "inferred")
chk("docstring: `site`, `source_file`, `meta_file` listed under `not_values`, no label",
    "`site`, `source_file`, `meta_file` are names, not values: listed under `not_values`, with no label" in flat
    and set(consts["NOT_VALUES"]) == {"site", "source_file", "meta_file"} and not set(consts["NOT_VALUES"]) & set(SL))
chk("docstring verbatim list includes data-quality counts; code writes them via raw()",
    "lunar fraction, data-quality counts) is written" in flat and "'source_dataquality': {k: raw(v)" in src)
L.append("ALL PASS" if ok else "SOME FAIL")
open(f"{R}/q06_docstring_vs_code.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
