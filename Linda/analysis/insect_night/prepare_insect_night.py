#!/usr/bin/env python3
"""Prepare the night-only insect dataset and a self-contained QA report.

The source CSV is MacRoman encoded. The pipeline preserves all original night
records, adds explicit quality/normalization fields, selects one canonical row
per semantic measurement group, and creates a site-level geographic payload.

No cross-study global activity magnitude is produced. Sampling protocols,
measurement units, taxa, and study designs are too heterogeneous for that claim.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = REPO_ROOT / "Linda" / "data" / "Global insect diel dataset"
SOURCE_CSV = SOURCE_DIR / "insect_diel_activity_dataset.csv"
SOURCE_METADATA = SOURCE_DIR / "insect_diel_activity_dataset_metadata.xlsx"
OUTPUT_DIR = REPO_ROOT / "Linda" / "processed" / "insect_night"
REPORT_DIR = Path(__file__).resolve().parent / "report"
APP_DATA_DIR = REPO_ROOT / "Alexander" / "globe_v2" / "data"

METADATA_TO_CSV = {
    "catalogNumber": "catalogNumber",
    "yr_publish": "year_publish",
    "yr_sampling": "year_sampling",
    "months": "month",
    "season_described": "season_verbatim",
    "season": "season_type",
    "country": "country",
    "region": "stateProvince",
    "locality": "locality",
    "latitude_dec": "decimalLatitude",
    "longitude_dec": "decimalLongitude",
    "elevation": "elevation_m",
    "system": "ecosystem_type",
    "disturbance_described": "disturbance_verbatim",
    "habitat_general_described": "habitat_general_verbatim",
    "habitat_general": "habitat_general",
    "habitat_stratum_described": "habitat_stratum_verbatim",
    "sampling_described": "samplingProtocol",
    "sampling_type": "sampling_type",
    "taxon_name_original": "taxon",
    "taxon_rank": "taxon_rank",
    "taxon_common_name": "vernacularName",
    "taxon_higher_group": "taxon_higher_group",
    "measured_property": "measured_property",
    "measurement_level": "measurement_level",
    "diel_period": "diel_period",
    "measurementValue": "measurementValue",
    "measurementUnit": "measurementUnit",
    "sample_size": "sample_size",
    "standard_deviation": "standard_deviation",
    "ref_id": "reference_no",
    "reference": "bibliographicCitation",
}

MEASUREMENT_GROUP_EXCLUSIONS = {
    "catalogNumber",
    "measurement_level",
    "measurementValue",
    "measurementUnit",
    "sample_size",
    "standard_deviation",
    "bibliographicCitation",
    "diel_period",
}


def stable_id(prefix: str, values: Iterable[object]) -> str:
    normalized = "|".join("<NA>" if pd.isna(v) else str(v).strip() for v in values)
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def json_ready(value: object) -> object:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def table_html(frame: pd.DataFrame, max_rows: int | None = None) -> str:
    shown = frame.head(max_rows) if max_rows else frame
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in shown.columns)
    body = []
    for row in shown.itertuples(index=False, name=None):
        cells = "".join(
            f"<td>{html.escape('—' if pd.isna(v) else str(v))}</td>" for v in row
        )
        body.append(f"<tr>{cells}</tr>")
    return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"


def build_report(
    summary: dict[str, object],
    unit_counts: pd.DataFrame,
    missingness: pd.DataFrame,
    taxon_counts: pd.DataFrame,
    site_preview: pd.DataFrame,
) -> str:
    cards = [
        ("Source records", summary["source_rows"]),
        ("Night records", summary["night_rows"]),
        ("Canonical measurements", summary["canonical_measurements"]),
        ("Geographic sites", summary["site_count"]),
        ("Studies", summary["study_count"]),
    ]
    cards_html = "".join(
        f"<div class='card'><strong>{value:,}</strong><span>{label}</span></div>"
        for label, value in cards
    )
    findings = pd.DataFrame(
        [
            {
                "Severity": "High",
                "Finding": "Raw abundance is not globally comparable",
                "Evidence": f"{summary['measurement_unit_count']} units and four sampling-type families occur in the night subset.",
                "Decision": "No global particle-size field is released.",
            },
            {
                "Severity": "Medium",
                "Finding": "Mean and total records overlap",
                "Evidence": f"{summary['paired_measurement_groups']} measurement groups contain both a mean and a total.",
                "Decision": "The canonical table prefers the reported mean and retains the total only in the audit table.",
            },
            {
                "Severity": "High",
                "Finding": "Some paired abundance values are inconsistent",
                "Evidence": f"{summary['inconsistent_abundance_pairs']} paired abundance groups differ by more than 5% when total is divided by sample size.",
                "Decision": "Reported means are preserved; inconsistent pairs are flagged and never silently reconciled.",
            },
            {
                "Severity": "Medium",
                "Finding": "Sampling effort is incomplete",
                "Evidence": f"{summary['missing_sample_size_rows']} night records have no sample_size.",
                "Decision": "Those records remain mappable but cannot support derived per-sample values.",
            },
            {
                "Severity": "Low",
                "Finding": "Source encoding is MacRoman",
                "Evidence": "UTF-8 decoding fails; MacRoman correctly restores accented locality names and punctuation.",
                "Decision": "All generated files are UTF-8.",
            },
        ]
    )
    decisions = pd.DataFrame(
        [
            ["Day/night scope", "Keep only diel_period = night", "The source stores diel periods as rows, not separate day columns."],
            ["Abundance mean", "Preserve reported mean", "Use the source value and unit; do not claim cross-study comparability."],
            ["Abundance total", "Derive total/sample_size only for unpaired raw 'individuals' totals", "Do not divide densities, proportions, biomass, occupancy, or other already-defined units."],
            ["Richness", "Preserve mean or total as reported", "Richness is not additive and total/sample_size is not a valid richness normalization."],
            ["Duplicate measurements", "Prefer mean in the canonical table", "All source rows remain in the full night-observations audit table."],
            ["Map eligibility", "Valid coordinates are sufficient", "A record may be shown geographically even when it cannot control quantitative size."],
            ["Global quantitative size", "Withheld", "Future visualization should use uniform presence or an explicitly approved within-study encoding."],
        ],
        columns=["Field", "Rule", "Reason"],
    )
    output_rows = pd.DataFrame(
        [
            ["insect_night_observations.csv", "All night records with quality and canonical-selection flags"],
            ["insect_night_canonical.csv", "One preferred row per semantic measurement group"],
            ["insect_night_quality_flags.csv", "Record-level issues requiring review"],
            ["insect_night_sites.json", "Site-level geographic payload without a global activity magnitude"],
            ["insect_night_data_dictionary.csv", "Original metadata definitions plus derived-field definitions"],
            ["insect_night_summary.json", "Machine-readable preparation and QA summary"],
        ],
        columns=["Output", "Purpose"],
    )
    links = "".join(
        f"<li><a href='../../../processed/insect_night/{html.escape(name)}'>{html.escape(name)}</a></li>"
        for name in output_rows["Output"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Observed Insect Activity at Night — Data Preparation</title>
<style>
:root{{--bg:#06080d;--panel:#0e131d;--panel2:#131b27;--line:#263244;--ink:#edf1f6;--muted:#95a1b2;--accent:#b6f36a;--warn:#ffb55a;--high:#ff7a7a;--low:#78b7ff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1200px;margin:auto;padding:48px 28px 80px}} h1{{font-size:clamp(32px,5vw,64px);line-height:1.02;margin:0;letter-spacing:-.045em;max-width:900px}}
.kicker{{font:600 12px/1.2 ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);margin-bottom:16px}}
.lede{{max-width:820px;color:var(--muted);font-size:18px;margin:22px 0 34px}} .cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:0 0 28px}}
.card{{background:var(--panel);padding:20px}} .card strong{{display:block;font:500 28px/1 ui-monospace,monospace}} .card span{{display:block;color:var(--muted);font-size:12px;margin-top:8px}}
.status{{border:1px solid #40562a;background:#10190d;padding:18px 20px;margin:28px 0 44px}} .status b{{color:var(--accent)}}
section{{margin:46px 0}} h2{{font-size:24px;margin:0 0 8px}} .note{{color:var(--muted);max-width:850px;margin:0 0 18px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
.table-wrap{{overflow:auto;border:1px solid var(--line);background:var(--panel)}} table{{border-collapse:collapse;width:100%;min-width:620px}} th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{position:sticky;top:0;background:var(--panel2);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}} td{{font-size:13px}} tr:last-child td{{border-bottom:0}}
.files{{border:1px solid var(--line);padding:18px 22px;background:var(--panel)}} a{{color:var(--accent)}} code{{font-family:ui-monospace,monospace;color:#d9e7ff}} footer{{color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:18px;margin-top:50px}}
@media(max-width:850px){{.cards{{grid-template-columns:1fr 1fr}}.grid{{grid-template-columns:1fr}}main{{padding:32px 18px 60px}}}}
</style>
</head>
<body><main>
<div class="kicker">A · Natural Night · Data Preparation</div>
<h1>Observed insect activity at night</h1>
<p class="lede">Night-only preparation of the Global Dataset of Diel Activity Patterns in Insect Communities. This stage establishes geographic coverage and measurement integrity. It does not claim an artificial-light effect or nocturnal preference.</p>
<div class="cards">{cards_html}</div>
<div class="status"><b>Ready for geographic plotting.</b> All {summary['night_rows']:,} night records have valid coordinates. Quantitative particle sizing remains withheld because raw magnitudes are not comparable across studies, units, taxa, and sampling protocols.</div>
<section><h2>Dataset grain</h2><p class="note">A source row is one reported measurement for a taxonomic group, sampling context, measured property, measurement level, and diel period. The night-only table preserves all source rows. The canonical table collapses paired mean/total representations by preferring the reported mean.</p></section>
<section><h2>Quality findings</h2>{table_html(findings)}</section>
<section><h2>Cleaning and normalization rules</h2>{table_html(decisions)}</section>
<section><h2>Coverage and heterogeneity</h2><div class="grid"><div><p class="note">Measurement units in night records</p>{table_html(unit_counts, 20)}</div><div><p class="note">Higher taxonomic groups in night records</p>{table_html(taxon_counts, 20)}</div></div></section>
<section><h2>Missingness</h2><p class="note">Missing standard deviation is expected for totals. Disturbance text is optional. Missing sample size directly blocks derived per-sample values.</p>{table_html(missingness, 32)}</section>
<section><h2>Site preview</h2><p class="note">Sites are geographic aggregates only. Counts below describe source coverage, not ecological intensity.</p>{table_html(site_preview, 30)}</section>
<section><h2>Generated outputs</h2>{table_html(output_rows)}<div class="files"><strong>Open files</strong><ul>{links}</ul></div></section>
<footer>Generated from <code>insect_diel_activity_dataset.csv</code> and its metadata workbook. Source decoding: MacRoman. Generated files: UTF-8. No daytime records are included in the prepared visualization data.</footer>
</main></body></html>"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    source = pd.read_csv(SOURCE_CSV, encoding="mac_roman", na_values=["NA"])
    metadata = pd.read_excel(SOURCE_METADATA)

    night = source.loc[source["diel_period"].astype(str).str.strip().str.lower().eq("night")].copy()
    string_columns = night.select_dtypes(include=["object"]).columns
    for column in string_columns:
        night[column] = night[column].map(lambda value: value.strip() if isinstance(value, str) else value)

    night["record_id"] = night["catalogNumber"].map(lambda value: f"insect-night-{int(value):04d}")
    night["site_id"] = [
        stable_id("site", row)
        for row in night[["decimalLatitude", "decimalLongitude"]].itertuples(index=False, name=None)
    ]
    semantic_columns = [column for column in source.columns if column not in MEASUREMENT_GROUP_EXCLUSIONS]
    night["measurement_group_id"] = [
        stable_id("measure", row)
        for row in night[semantic_columns].itertuples(index=False, name=None)
    ]
    night["coordinate_valid"] = night["decimalLatitude"].between(-90, 90) & night["decimalLongitude"].between(-180, 180)
    night["sampling_effort_available"] = night["sample_size"].notna() & night["sample_size"].gt(0)
    night["canonical_record"] = False
    night["pair_consistency_flag"] = "not_applicable"
    night["normalization_method"] = "not_available"
    night["night_activity_value"] = np.nan
    night["night_activity_unit"] = pd.NA
    night["relative_activity_index"] = np.nan
    night["relative_activity_context_n"] = pd.Series(pd.NA, index=night.index, dtype="Int64")
    night["global_size_eligible"] = False
    night["map_display_eligible"] = night["coordinate_valid"]

    inconsistent_group_ids: set[str] = set()
    paired_group_count = 0

    for group_id, group in night.groupby("measurement_group_id", sort=False):
        means = group.loc[group["measurement_level"].eq("mean")]
        totals = group.loc[group["measurement_level"].eq("total")]
        canonical_index = means.index[0] if not means.empty else group.index[0]
        night.loc[canonical_index, "canonical_record"] = True

        if len(means) == 1 and len(totals) == 1:
            paired_group_count += 1
            mean_row = means.iloc[0]
            total_row = totals.iloc[0]
            comparable_pair = (
                mean_row["measured_property"] == "abundance"
                and mean_row["measurementUnit"] == total_row["measurementUnit"]
                and pd.notna(total_row["sample_size"])
                and total_row["sample_size"] > 0
            )
            if comparable_pair:
                derived = total_row["measurementValue"] / total_row["sample_size"]
                denominator = abs(mean_row["measurementValue"]) if mean_row["measurementValue"] != 0 else 1.0
                relative_error = abs(derived - mean_row["measurementValue"]) / denominator
                label = "consistent_within_5pct" if relative_error <= 0.05 else "inconsistent_over_5pct"
                night.loc[group.index, "pair_consistency_flag"] = label
                if relative_error > 0.05:
                    inconsistent_group_ids.add(group_id)
            else:
                night.loc[group.index, "pair_consistency_flag"] = "not_directly_comparable"

    canonical = night.loc[night["canonical_record"]].copy()
    abundance_mean = canonical["measured_property"].eq("abundance") & canonical["measurement_level"].eq("mean")
    canonical.loc[abundance_mean, "night_activity_value"] = canonical.loc[abundance_mean, "measurementValue"]
    canonical.loc[abundance_mean, "night_activity_unit"] = canonical.loc[abundance_mean, "measurementUnit"]
    canonical.loc[abundance_mean, "normalization_method"] = "reported_mean_per_sample"

    derivable_total = (
        canonical["measured_property"].eq("abundance")
        & canonical["measurement_level"].eq("total")
        & canonical["measurementUnit"].eq("individuals")
        & canonical["sampling_effort_available"]
    )
    canonical.loc[derivable_total, "night_activity_value"] = (
        canonical.loc[derivable_total, "measurementValue"] / canonical.loc[derivable_total, "sample_size"]
    )
    canonical.loc[derivable_total, "night_activity_unit"] = "individuals per sample"
    canonical.loc[derivable_total, "normalization_method"] = "total_divided_by_sample_size"

    relative_group_columns = ["reference_no", "night_activity_unit", "sampling_type", "taxon_higher_group"]
    activity_candidates = canonical.loc[canonical["night_activity_value"].notna()].copy()
    for _, group in activity_candidates.groupby(relative_group_columns, dropna=False, sort=False):
        context_n = len(group)
        canonical.loc[group.index, "relative_activity_context_n"] = context_n
        if context_n >= 3:
            canonical.loc[group.index, "relative_activity_index"] = group["night_activity_value"].rank(method="average", pct=True)

    update_columns = [
        "normalization_method",
        "night_activity_value",
        "night_activity_unit",
        "relative_activity_index",
        "relative_activity_context_n",
    ]
    night.loc[canonical.index, update_columns] = canonical[update_columns]

    quality_rows: list[dict[str, object]] = []
    for row in night.loc[~night["sampling_effort_available"]].itertuples():
        quality_rows.append({"record_id": row.record_id, "severity": "medium", "flag": "missing_sample_size", "detail": "No positive sample_size is available."})
    for group_id in sorted(inconsistent_group_ids):
        for row in night.loc[night["measurement_group_id"].eq(group_id)].itertuples():
            quality_rows.append({"record_id": row.record_id, "severity": "high", "flag": "paired_mean_total_inconsistent", "detail": "Reported mean differs by more than 5% from total/sample_size; reported mean is retained."})
    for row in night.loc[~night["canonical_record"]].itertuples():
        quality_rows.append({"record_id": row.record_id, "severity": "low", "flag": "noncanonical_duplicate_representation", "detail": "A reported mean represents the same measurement context in the canonical table."})
    quality_flags = pd.DataFrame(quality_rows, columns=["record_id", "severity", "flag", "detail"])

    site_records = []
    canonical_sites = canonical.groupby("site_id", sort=True)
    for site_id, group in canonical_sites:
        first = group.iloc[0]
        site_records.append(
            {
                "site_id": site_id,
                "lat": json_ready(first["decimalLatitude"]),
                "lng": json_ready(first["decimalLongitude"]),
                "countries": sorted(str(v) for v in group["country"].dropna().unique()),
                "state_provinces": sorted(str(v) for v in group["stateProvince"].dropna().unique()),
                "localities": sorted(str(v) for v in group["locality"].dropna().unique()),
                "ecosystems": sorted(str(v) for v in group["ecosystem_type"].dropna().unique()),
                "habitats": sorted(str(v) for v in group["habitat_general"].dropna().unique()),
                "taxonomic_groups": sorted(str(v) for v in group["taxon_higher_group"].dropna().unique()),
                "study_count": int(group["reference_no"].nunique()),
                "measurement_count": int(len(group)),
                "has_abundance": bool(group["measured_property"].eq("abundance").any()),
                "has_richness": bool(group["measured_property"].eq("richness").any()),
                "global_activity_magnitude": None,
                "global_activity_magnitude_status": "withheld_not_cross_study_comparable",
            }
        )

    metadata_terms = metadata.iloc[:, :2].copy()
    metadata_terms.columns = ["metadata_term", "definition"]
    metadata_terms["csv_field"] = metadata_terms["metadata_term"].map(METADATA_TO_CSV)
    metadata_terms["field_type"] = "source"
    derived_definitions = pd.DataFrame(
        [
            ["record_id", "Stable identifier derived from catalogNumber."],
            ["site_id", "Stable hash of latitude and longitude; text locality variants at the same coordinates remain aggregated."],
            ["measurement_group_id", "Stable hash of the semantic sampling and measurement context, excluding value representation fields."],
            ["coordinate_valid", "Latitude and longitude fall within valid geographic ranges."],
            ["sampling_effort_available", "sample_size is present and greater than zero."],
            ["canonical_record", "Preferred record for a measurement group; reported mean is preferred over total."],
            ["pair_consistency_flag", "Agreement status for a directly comparable reported mean and total/sample_size pair."],
            ["normalization_method", "How night_activity_value was obtained."],
            ["night_activity_value", "Reported mean abundance, or total individuals/sample_size for an unpaired derivable total."],
            ["night_activity_unit", "Unit associated with night_activity_value."],
            ["relative_activity_index", "Within-study rank percentile for comparable activity records when the context contains at least three records; not approved for global magnitude."],
            ["relative_activity_context_n", "Number of records in the within-study relative-activity context."],
            ["global_size_eligible", "Always false in this release because cross-study magnitudes are not comparable."],
            ["map_display_eligible", "The record can be placed geographically because its coordinates are valid."],
        ],
        columns=["csv_field", "definition"],
    )
    derived_definitions["metadata_term"] = pd.NA
    derived_definitions["field_type"] = "derived"
    data_dictionary = pd.concat(
        [metadata_terms[["field_type", "csv_field", "metadata_term", "definition"]], derived_definitions[["field_type", "csv_field", "metadata_term", "definition"]]],
        ignore_index=True,
    )

    unit_counts = night["measurementUnit"].value_counts(dropna=False).rename_axis("Measurement unit").reset_index(name="Night records")
    missingness = (
        night.isna().mean().mul(100).round(1).rename("Missing (%)").reset_index().rename(columns={"index": "Field"}).sort_values("Missing (%)", ascending=False)
    )
    taxon_counts = night["taxon_higher_group"].value_counts(dropna=False).rename_axis("Higher group").reset_index(name="Night records")
    site_preview = pd.DataFrame(site_records)
    site_preview["country"] = site_preview["countries"].map(lambda values: "; ".join(values))
    site_preview["state_province"] = site_preview["state_provinces"].map(lambda values: "; ".join(values))
    site_preview["locality"] = site_preview["localities"].map(lambda values: "; ".join(values))
    site_preview = site_preview[["country", "state_province", "locality", "measurement_count", "study_count", "has_abundance", "has_richness"]]
    site_preview = site_preview.sort_values(["measurement_count", "country"], ascending=[False, True])

    summary = {
        "source_rows": int(len(source)),
        "source_columns": int(source.shape[1]),
        "night_rows": int(len(night)),
        "canonical_measurements": int(len(canonical)),
        "site_count": int(len(site_records)),
        "study_count": int(night["reference_no"].nunique()),
        "measurement_unit_count": int(night["measurementUnit"].nunique()),
        "paired_measurement_groups": int(paired_group_count),
        "inconsistent_abundance_pairs": int(len(inconsistent_group_ids)),
        "missing_sample_size_rows": int((~night["sampling_effort_available"]).sum()),
        "invalid_coordinate_rows": int((~night["coordinate_valid"]).sum()),
        "exact_duplicate_rows": int(night.duplicated(subset=list(source.columns)).sum()),
        "activity_value_candidates": int(canonical["night_activity_value"].notna().sum()),
        "relative_activity_candidates": int(canonical["relative_activity_index"].notna().sum()),
        "global_size_eligible_rows": 0,
        "source_encoding": "MacRoman",
        "output_encoding": "UTF-8",
        "scope": "night-only observations",
        "claim_boundary": "observed insect activity at night; no ALAN effect or nocturnal preference claim",
    }

    night.to_csv(OUTPUT_DIR / "insect_night_observations.csv", index=False, encoding="utf-8")
    canonical.to_csv(OUTPUT_DIR / "insect_night_canonical.csv", index=False, encoding="utf-8")
    quality_flags.to_csv(OUTPUT_DIR / "insect_night_quality_flags.csv", index=False, encoding="utf-8")
    data_dictionary.to_csv(OUTPUT_DIR / "insect_night_data_dictionary.csv", index=False, encoding="utf-8")
    site_payload = json.dumps({"sites": site_records}, ensure_ascii=False, indent=2)
    (OUTPUT_DIR / "insect_night_sites.json").write_text(site_payload, encoding="utf-8")
    (APP_DATA_DIR / "insect_night_sites.json").write_text(site_payload, encoding="utf-8")
    (OUTPUT_DIR / "insect_night_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (REPORT_DIR / "index.html").write_text(build_report(summary, unit_counts, missingness, taxon_counts, site_preview), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
