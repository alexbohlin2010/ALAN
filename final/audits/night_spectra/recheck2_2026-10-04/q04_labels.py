"""Recheck2 q04: site-file labels. Every top-level key is either labelled (measured / documented / inferred) in
`labels` or listed in `not_values`, apart from the containers labels / label_notes / not_values. Writes
results/q04_labels.txt."""
import json
R = "audits/night_spectra/recheck2_2026-10-04/results"
ALLOWED = {"measured", "documented", "inferred"}
CONTAINERS = {"labels", "label_notes", "not_values"}
L, allok = [], True
for f in ("philadelphia.json", "cherry_springs.json"):
    d = json.load(open(f"data/derived/spectra/{f}"), parse_float=str, parse_int=str)
    lab, notes, nv = d["labels"], d["label_notes"], d["not_values"]
    keys = set(d) - CONTAINERS
    checks = {
        "every key labelled or in not_values": sorted(keys - set(lab) - set(nv)) == [],
        "no key both labelled and in not_values": sorted(set(lab) & set(nv)) == [],
        "every label value in {measured, documented, inferred}": all(v in ALLOWED for v in lab.values()),
        "labels has no key absent from the file": sorted(set(lab) - keys) == [],
        "not_values has no key absent from the file": sorted(set(nv) - keys) == [],
        "not_values == {site, source_file, meta_file}": set(nv) == {"site", "source_file", "meta_file"},
        "label_notes keys == labels used": set(notes) == set(lab.values()),
        "string 'identifier' absent from labels/label_notes/not_values":
            "identifier" not in json.dumps([lab, notes, nv]),
    }
    L.append(f"== {f}: {len(d)} top-level keys; {len(lab)} labelled, {len(nv)} not_values, 3 containers")
    for k, v in checks.items():
        allok &= v
        L.append(f"  {'PASS' if v else 'FAIL'} {k}")
    for k in d:
        L.append(f"    {k}: " + (lab[k] if k in lab else "not_values" if k in nv else "container" if k in CONTAINERS
                                 else "UNLABELLED"))
L.append("ALL PASS" if allok else "SOME FAIL")
open(f"{R}/q04_labels.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
