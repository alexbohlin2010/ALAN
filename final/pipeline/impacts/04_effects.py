"""One row per effect record (workbook row) of the studies that have a location on the globe.

Run from final/:  .venv/bin/python pipeline/impacts/04_effects.py
Input:  data/raw/impacts/czarnecka2025/Data_S1_Czarnecka_et_al..xlsx (read-only; see MANIFEST.csv)
        data/derived/impacts/study_locations.json (02_geocode.py; which studies are drawn)
        pipeline/impacts/maps/species_groups.csv (Phylum + Class -> species group; human, AI_LOG step 50)
Output: data/derived/impacts/effects.json

Human decision (AI_LOG "Impacts task", steps 26-27): an effect-level file for the effects chart,
for the located (drawn) studies only.

What a record is (Dryad README + article doi:10.1111/gcb.70569, sec. 2.5): one measured variable
compared between a dark control group and a group lit at night, in one study. `g` is the
workbook's `Effect size (ES)`, Hedges g = standardised mean difference between control and
treatment. Recomputed check (AI_LOG step 25): (Experimental_Mean - Control_Mean) / pooled SD x J
matches for 4,899 of 4,905 rows, so g > 0 means the lit group's mean is higher.
`g_directional` is the workbook's `Effect size_sign`, filled only where `Included (directional ES)`
is "yes": the authors adjusted the sign so that positive = intensified or accelerated under light
(e.g. reduced rest becomes positive = more activity); article sec. 2.5.

Rules (all deterministic):
- Kept: rows whose `Study` id is in study_locations.json. No row is changed or merged.
- effect_id = "<study_id>-<n>", n = 1-based order of the row within its study in the workbook;
  `row` = the workbook row number (header = row 1).
- Text cells: leading/trailing whitespace stripped; empty -> null.
- Numbers (g, SE, |g|, means, SD, N): parsed as float; a cell that does not parse -> null and the
  source text is kept under `unparsed`. Lux cells are kept as source text (they hold values like "<0,01").
- species_group: looked up from maps/species_groups.csv by (Phylum, Class) after stripping; empty
  class = ""; every pair in the workbook must be in the map (else the script stops); an empty group
  in the map -> null.
Labels: every field is `documented` (copied from the workbook), except effect_id and species_group
(`inferred`, rules above).
"""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx import read_first_sheet  # noqa: E402

FINAL = Path(__file__).resolve().parents[2]
SRC = FINAL / "data/raw/impacts/czarnecka2025/Data_S1_Czarnecka_et_al..xlsx"
SRC_SHA256 = "8fae8a0244047ab057808ea321962bf848cff42b6fd521f34b37a360efa154d6"
LOCS = FINAL / "data/derived/impacts/study_locations.json"
OUT = FINAL / "data/derived/impacts/effects.json"
GROUPS = Path(__file__).resolve().parent / "maps/species_groups.csv"

TEXT = {
    "category": "Category ", "subcategory": "Sub.Category", "subcategory_detail": "Sub.Category1",
    "measured_effect": "Measured.effect", "measure_comment": "Measure.comment",
    "study_type": "Study.Type", "phylum": "Phylum", "class": "Class", "species": "Species",
    "light_type_code": "Light_Type_coded", "light_source": "Light_Source",
    "night_lux": "Night_Lux", "control_lux": "Control_Lux", "night_lux_band": "Night_Lx_coded",
    "included_directional": "Included (directional ES)",
}
NUMBERS = {
    "g": "Effect size (ES)", "g_se": "SE", "g_abs": "Effects size_absolute",
    "g_directional": "Effect size_sign",
    "control_mean": "Control_Mean", "control_sd": "Control_SD", "control_n": "Control_N",
    "lit_mean": "Experimental_Mean", "lit_sd": "Experimental_SD", "lit_n": "Experimental_N",
}


def clean(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def main():
    sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
    assert sha == SRC_SHA256, f"raw file changed: {sha}"
    header, rows = read_first_sheet(SRC)
    col = {h: i for i, h in enumerate(header)}
    for c in ["Study", *TEXT.values(), *NUMBERS.values()]:
        assert c in col, c
    located = {s["study_id"] for s in json.loads(LOCS.read_text())["studies"]}
    with open(GROUPS, newline="") as f:
        group_of = {(r["phylum"], r["class"]): r["species_group"] or None for r in csv.DictReader(f)}
    pairs = {(clean(r[col["Phylum"]]), clean(r[col["Class"]]) or "") for r in rows}
    assert pairs <= group_of.keys(), sorted(pairs - group_of.keys(), key=str)

    effects, seen, n_in_study = [], set(), {}
    for i, r in enumerate(rows):
        sid = clean(r[col["Study"]])
        n_in_study[sid] = n_in_study.get(sid, 0) + 1
        if sid not in located:
            continue
        e = {"effect_id": f"{sid}-{n_in_study[sid]}", "study_id": sid, "row": i + 2}
        for f, c in TEXT.items():
            e[f] = clean(r[col[c]])
        unparsed = {}
        for f, c in NUMBERS.items():
            raw = clean(r[col[c]])
            try:
                e[f] = float(raw) if raw is not None else None
            except ValueError:
                e[f] = None
                unparsed[f] = raw
        e["species_group"] = group_of[(e["phylum"], e["class"] or "")]
        e["unparsed"] = unparsed or None
        effects.append(e)
        seen.add(sid)

    assert seen == located, located - seen
    assert len({e["effect_id"] for e in effects}) == len(effects)
    by_cat, by_group = {}, {}
    for e in effects:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
        by_group[e["species_group"]] = by_group.get(e["species_group"], 0) + 1
    meta = {
        "source": str(SRC.relative_to(FINAL)), "source_sha256": sha,
        "locations": str(LOCS.relative_to(FINAL)),
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "studies": len(seen), "effects": len(effects), "effects_by_category": by_cat,
        "effects_by_species_group": by_group,
        "missing_g": sum(e["g"] is None for e in effects),
        "g_abs_over_10": sum((e["g_abs"] or 0) > 10 for e in effects),
        "with_unparsed": sum(e["unparsed"] is not None for e in effects),
    }
    fields = {f: {"label": "documented", "source_column": c} for f, c in {**TEXT, **NUMBERS}.items()}
    fields.update({
        "study_id": {"label": "documented", "source_column": "Study"},
        "row": {"label": "documented", "rule": "workbook row number (header = 1)"},
        "effect_id": {"label": "inferred", "rule": "<study_id>-<1-based order of the row within its study>"},
        "species_group": {"label": "inferred", "rule": "maps/species_groups.csv by (Phylum, Class)"},
        "unparsed": {"label": "documented", "rule": "source text of number cells that did not parse"},
        "script": "pipeline/impacts/04_effects.py",
        "audit": "Not yet audited (RULES section 3).",
    })
    OUT.write_text(json.dumps({"meta": meta, "fields": fields, "effects": effects},
                              ensure_ascii=False, indent=1))
    print(json.dumps(meta, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
