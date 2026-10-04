"""One row per study from the Czarnecka et al. 2025 meta-analysis workbook (Data S1).

Run from final/:  .venv/bin/python pipeline/impacts/01_studies.py
Input:  data/raw/impacts/czarnecka2025/Data_S1_Czarnecka_et_al..xlsx (read-only; see MANIFEST.csv)
Output: data/derived/impacts/studies.json  (+ studies.csv, the same rows for reading by hand)

Human decisions (AI_LOG "Impacts task", steps 2-5): rebuild the studies dataset; include all
314 studies; a DOI link per study where available; interpretable cards built from source
fields only (I1); topic groups (I2) are a separate, human-edited mapping, not applied here.

Rules (all deterministic):
- A study = all rows sharing the workbook's `Study` value.
- Text cells: leading/trailing whitespace stripped. Per study, each field keeps its distinct
  values in first-seen order (a list), so nothing is chosen between conflicting values.
- DOI: each distinct source value is cleaned by (1) removing all whitespace and (2) removing a
  leading "doi.org/" or "dx.doi.org/" (with or without "http(s)://"), or "doi:". A value is kept only if it then
  matches 10.<4-9 digits>/<non-space>. `doi` is filled only when a study has exactly one
  distinct cleaned DOI; with 0 or >1 it stays empty and `doi_note` says why. The source values
  are always kept in `doi_source`.
- night_lux_min / _max: numeric `Night_Lux` values of the study's rows (non-numeric values are
  listed in `night_lux_unparsed`). Same for control lux.
- effect_count: number of workbook rows (effect sizes) of the study.
- category_effect_counts: per study, number of workbook rows per `Category ` value (first-seen order).
- dominant_category: the category with the most rows in the study (Linda's rule; human decision,
  AI_LOG Impacts step 22). Tie: the tied category whose first row comes first in the workbook
  (human decision, step 22). Empty only if the study has no category.
Labels: fields copied from the workbook are `documented` (source: the Dryad dataset);
derived fields are `inferred` with the rule above. See `fields` in the output.
"""
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx import read_first_sheet  # noqa: E402

FINAL = Path(__file__).resolve().parents[2]
SRC = FINAL / "data/raw/impacts/czarnecka2025/Data_S1_Czarnecka_et_al..xlsx"
SRC_SHA256 = "8fae8a0244047ab057808ea321962bf848cff42b6fd521f34b37a360efa154d6"
OUT = FINAL / "data/derived/impacts"
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
DOI_PREFIX = re.compile(r"^((https?://)?(dx\.)?doi\.org/|doi:)", re.I)

# output field -> (workbook column, label)
LISTS = {
    "authors": "Author", "title": "Title", "publication_year": "Publication.year",
    "journal": "Source", "study_type": "Study.Type", "habitat": "Habitat", "phylum": "Phylum",
    "class": "Class", "order": "Order", "species": "Species", "functional_group": "functional",
    "activity": "Activity", "measured_effect": "Measured.effect", "category": "Category ",
    "subcategory": "Sub.Category", "subcategory_detail": "Sub.Category1",
    "light_type_code": "Light_Type_coded", "light_source": "Light_Source",
    "night_lux_band": "Night_Lx_coded", "location": "Location",
}


def clean(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def distinct(values):
    out = []
    for v in values:
        if v is not None and v not in out:
            out.append(v)
    return out


def clean_doi(v):
    d = DOI_PREFIX.sub("", re.sub(r"\s+", "", v))
    return d if DOI_RE.match(d) else None


def lux_range(values):
    nums, bad = [], []
    for v in values:
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            bad.append(v)
    return (min(nums) if nums else None, max(nums) if nums else None, distinct(bad))


def main():
    sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
    assert sha == SRC_SHA256, f"raw file changed: {sha}"
    header, rows = read_first_sheet(SRC)
    col = {h: i for i, h in enumerate(header)}
    for c in list(LISTS.values()) + ["Study", "DOI", "Night_Lux", "Control_Lux"]:
        assert c in col, c

    groups = {}
    for r in rows:
        groups.setdefault(clean(r[col["Study"]]), []).append(r)
    assert None not in groups, "row without Study id"

    studies = []
    for sid, rs in groups.items():
        s = {"study_id": sid, "effect_count": len(rs)}
        counts = {}
        for r in rs:
            cat = clean(r[col[LISTS["category"]]])
            if cat is not None:
                counts[cat] = counts.get(cat, 0) + 1
        s["category_effect_counts"] = counts
        # max() keeps the first maximum, and dict order is first-seen row order -> tie rule.
        s["dominant_category"] = max(counts, key=counts.get) if counts else None
        for field, c in LISTS.items():
            s[field] = distinct(clean(r[col[c]]) for r in rs)
        src_dois = distinct(clean(r[col["DOI"]]) for r in rs)
        cleaned = distinct(clean_doi(d) for d in src_dois)
        s["doi_source"] = src_dois
        if len(cleaned) == 1:
            s["doi"] = cleaned[0]
            s["doi_url"] = f"https://doi.org/{cleaned[0]}"
            s["doi_note"] = None if src_dois == cleaned else "cleaned by rule (whitespace/prefix removed)"
        else:
            s["doi"] = s["doi_url"] = None
            s["doi_note"] = ("no DOI in the workbook" if not cleaned and not src_dois else
                             "workbook value is not a DOI" if not cleaned else
                             f"{len(cleaned)} different DOIs in the workbook; not chosen")
        lo, hi, bad = lux_range(r[col["Night_Lux"]] for r in rs)
        s.update(night_lux_min=lo, night_lux_max=hi, night_lux_unparsed=bad)
        lo, hi, bad = lux_range(r[col["Control_Lux"]] for r in rs)
        s.update(control_lux_min=lo, control_lux_max=hi, control_lux_unparsed=bad)
        studies.append(s)

    fields = {f: {"label": "documented", "source_column": c} for f, c in LISTS.items()}
    fields.update({
        "study_id": {"label": "documented", "source_column": "Study"},
        "doi_source": {"label": "documented", "source_column": "DOI"},
        "doi": {"label": "inferred", "rule": "single distinct DOI after whitespace/prefix removal"},
        "doi_url": {"label": "inferred", "rule": "https://doi.org/ + doi"},
        "doi_note": {"label": "inferred", "rule": "why doi is empty or was cleaned"},
        "effect_count": {"label": "inferred", "rule": "number of workbook rows of the study"},
        "category_effect_counts": {"label": "inferred", "rule": "workbook rows per `Category ` value"},
        "dominant_category": {"label": "inferred", "rule": "category with most rows; tie -> first in workbook row order"},
        "night_lux_min": {"label": "inferred", "rule": "min of numeric Night_Lux"},
        "night_lux_max": {"label": "inferred", "rule": "max of numeric Night_Lux"},
        "control_lux_min": {"label": "inferred", "rule": "min of numeric Control_Lux"},
        "control_lux_max": {"label": "inferred", "rule": "max of numeric Control_Lux"},
    })
    meta = {
        "source": "Czarnecka et al. 2025, Data S1, Dryad doi:10.5061/dryad.xwdbrv1q0 (CC0-1.0); "
                  "article Global Change Biology 31(10): e70569, doi:10.1111/gcb.70569",
        "source_sha256": sha, "source_rows": len(rows), "source_columns": len(header),
        "study_count": len(studies),
        "with_doi": sum(1 for s in studies if s["doi"]),
        "doi_cleaned_by_rule": sum(1 for s in studies if s["doi_note"] and s["doi_note"].startswith("cleaned")),
        "doi_empty": {s["study_id"]: s["doi_note"] for s in studies if not s["doi"]},
        "with_location": sum(1 for s in studies if s["location"]),
        "dominant_category_ties": sorted(s["study_id"] for s in studies if len(s["category_effect_counts"]) > 1
                                         and sorted(s["category_effect_counts"].values())[-1]
                                         == sorted(s["category_effect_counts"].values())[-2]),
        "units": "lux values as given in the workbook (lx)",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "pipeline/impacts/01_studies.py",
        "audit": "Not yet audited (RULES section 3).",
    }
    assert sum(s["effect_count"] for s in studies) == len(rows)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "studies.json").write_text(json.dumps({"meta": meta, "fields": fields, "studies": studies},
                                                 ensure_ascii=False, indent=1))
    keys = list(studies[0].keys())
    with open(OUT / "studies.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(keys)
        for s in studies:
            w.writerow([" ; ".join(map(str, v)) if isinstance(v, list) else ("" if v is None else v)
                        for v in (s[k] for k in keys)])
    print(json.dumps(meta, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
