"""Recheck2 q02: new outputs vs the pre-edit copy (scratchpad spectra_3h/), every leaf compared as text
(json parse_float=str, parse_int=str). Lists every changed / added / removed key path and confirms the data fields
are identical. Writes results/q02_diff.txt."""
import hashlib, json, sys
OLD = ("/private/tmp/claude-501/-Users-lindaxiangyideng-Documents-GitHub-ALAN--claude-worktrees-cool-ishizaka-9fd75f/"
       "f4206848-779e-44ba-ac70-d5bff7e07f5c/scratchpad/spectra_3h")
NEW = "data/derived/spectra"
R = "audits/night_spectra/recheck2_2026-10-04/results"
PREV_RECHECK_SHA = {  # recorded in recheck_2026-10-04/RECHECK.md
    "philadelphia.json": "84fd2b83056bbf78058b19b4bc712bd7b07a685d2bd57398a727be70173bd899",
    "cherry_springs.json": "670472fef2a59c28478a4cd02a41ce9efefbbdb3a52033a10d2cee6dd91a5181",
    "spectra_meta.json": "4446efd5fef22ac60d6d2b7a0f2e4dd35dd1b041ec0ac969f6d9286e57c3c2e3"}
def load(p):
    return json.load(open(p, encoding="utf-8"), parse_float=str, parse_int=str)
def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            if k not in b: out.append(("REMOVED", path + [k], a[k], None))
        for k in b:
            if k not in a: out.append(("ADDED", path + [k], None, b[k]))
        for k in a:
            if k in b: walk(a[k], b[k], path + [k], out)
        if [k for k in a if k in b] != [k for k in b if k in a]: out.append(("KEY_ORDER", path, None, None))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): out.append(("LENGTH", path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, path + [i], out)
    elif type(a) is not type(b) or a != b:
        out.append(("CHANGED", path, a, b))
L = []
for f, s in PREV_RECHECK_SHA.items():
    got = hashlib.sha256(open(f"{OLD}/{f}", "rb").read()).hexdigest()
    L.append(f"spectra_3h/{f} sha256 {got} {'== previous recheck' if got == s else '!= previous recheck ' + s}")
DATA = {  # fields that hold data values; must be identical as text
    "site": ["source_column", "timestamp", "night_id", "solar_elevation_deg", "lunar_elevation_deg",
             "lunar_illuminated_fraction", "irradiance", "n_source_spectra", "n_night_spectra", "n_selected",
             "source_date_range", "selected_date_range", "source_dataquality", "selected_cells", "source_sha256",
             "unit", "place", "paper_label", "site", "source_file", "meta_file"],
    "meta": ["wavelength_nm", "wavelength_step_nm", "display_limits_log10", "sites", "unit", "units_other",
             "timestamp_format", "selection", "files", "null_means", "verbatim", "source", "source_url"]}
for f in ("philadelphia.json", "cherry_springs.json", "spectra_meta.json"):
    a, b = load(f"{OLD}/{f}"), load(f"{NEW}/{f}")
    diffs = []
    walk(a, b, [], diffs)
    L.append(f"\n== {f}: {len(diffs)} differences (top-level keys old {len(a)}, new {len(b)})")
    for kind, p, x, y in diffs:
        L.append(f"  {kind} {'/'.join(map(str, p))}: {json.dumps(x)} -> {json.dumps(y)}")
    kind = "meta" if f == "spectra_meta.json" else "site"
    for k in DATA[kind]:
        same = k in a and k in b and a[k] == b[k]
        n = ""
        if isinstance(b.get(k), list):
            n = f" ({len(b[k])} items" + (f", {sum(len(r) for r in b[k])} cells" if k == "irradiance" else "") + ")"
        L.append(f"  {'IDENTICAL' if same else 'DIFFERENT'} {k}{n}")
open(f"{R}/q02_diff.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
