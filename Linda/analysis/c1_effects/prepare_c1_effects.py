#!/usr/bin/env python3
"""Prepare the C1 cross-species ALAN meta-analysis for visualization.

The source workbook contains one standardized effect-size record per row.
Positive and negative Hedges g values are not interpreted as beneficial or
harmful outcomes because direction depends on the measured variable. The app
therefore uses absolute magnitude for spatial position and keeps the signed
value only in record-level detail.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = REPO_ROOT / "Linda" / "data" / "spectrum-specific impacts of light pollution on biota"
SOURCE_XLSX = SOURCE_DIR / "Data_S1_Czarnecka_et_al..xlsx"
OUTPUT_DIR = REPO_ROOT / "Linda" / "processed" / "c1_effects"
APP_DATA_DIR = REPO_ROOT / "Alexander" / "globe_v2" / "data"
VIIRS_CITIES_JSON = REPO_ROOT / "Alexander" / "globe_v2" / "cities.json"
LOCATION_RESOLUTION_CSV = OUTPUT_DIR / "c1_location_resolution.csv"

DISPLAY_CAP = 10.0

CATEGORY_LABELS = {
    "Behaviour": "Behaviour",
    "Physiology": "Physiology",
    "LHT": "Life history",
    "Population": "Population",
    "Community": "Community",
}

CATEGORY_COLORS = {
    "Behaviour": "#ffb55a",
    "Physiology": "#8bb8ff",
    "Life history": "#d99cff",
    "Population": "#7ce6cf",
    "Community": "#f2e48b",
}

SOURCE_TO_CLEAN = {
    "Study": "study_id",
    "ID": "source_id",
    "Author": "authors",
    "Title": "title",
    "Publication.year": "publication_year",
    "DOI": "doi",
    "Source": "journal",
    "Study.Type": "study_type",
    "Habitat": "habitat",
    "Phylum": "phylum",
    "Class": "class",
    "Order": "order",
    "Species": "species",
    "functional": "functional_group",
    "Measure.comment": "measure_comment",
    "Measured.effect": "measured_effect",
    "Category ": "category_source",
    "Sub.Category": "subcategory",
    "Sub.Category1": "subcategory_detail",
    "Activity": "activity",
    "Light_Source": "light_source",
    "Light_Type_coded": "light_type",
    "Control_Lux": "control_lux",
    "Night_Lux": "night_lux",
    "Night_Lx_coded": "night_lux_band",
    "Location": "location",
    "Effect size (ES)": "effect_size",
    "SE": "effect_size_se",
    "Effects size_absolute": "effect_abs_source",
    "Effect size_sign": "directional_effect_source",
    "Included (directional ES)": "directional_included_source",
}


def clean_text(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, str):
        value = value.strip()
        return value if value else pd.NA
    return value


def json_value(value: object) -> object:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def normalize_place(value: object) -> str:
    """Normalize a place label for strict, accent-insensitive exact matching."""
    if value is None or pd.isna(value):
        return ""
    ascii_value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def resolve_existing_viirs_city(location: object, cities_by_name: dict[str, dict]) -> dict[str, object]:
    """Resolve only exact city-name matches against the project's existing VIIRS city file.

    The source workbook has free-text locations but no latitude/longitude fields. This deliberately
    does not geocode countries, universities, regions, or other vague descriptions. Text before the
    first comma must exactly match one of the already trusted VIIRS city labels.
    """
    if location is None or pd.isna(location):
        return {}
    city_name = normalize_place(str(location).split(",", 1)[0])
    return cities_by_name.get(city_name, {})


def compact_record(row: pd.Series) -> dict[str, object]:
    keys = [
        "effect_id", "study_id", "source_id", "publication_year", "study_type",
        "habitat", "phylum", "class", "order", "species", "measured_effect",
        "category", "subcategory", "subcategory_detail", "activity", "light_type",
        "light_source", "night_lux", "night_lux_band", "effect_size",
        "effect_size_se", "effect_abs", "effect_abs_display", "effect_abs_over_cap",
        "directional_included", "location", "title", "doi",
        "geo_mapped", "geo_context_available", "geo_point_eligible",
        "geo_lat", "geo_lng", "geo_label", "geo_geometry", "geo_precision",
        "geo_confidence", "geo_review_status", "geo_resolution",
        "geo_bbox_south", "geo_bbox_north", "geo_bbox_west", "geo_bbox_east",
        "anchor_group_id",
        "viirs_2024_meanlit", "viirs_context_scope",
    ]
    return {key: json_value(row[key]) for key in keys}


def make_anchor_groups(clean: pd.DataFrame) -> list[dict[str, object]]:
    """Create one geographic group per study + source location.

    A group may produce several anchors when the source lists multiple sites.
    Individual effect records remain linked through anchor_group_id and only
    expand after the group is selected in the globe view.
    """
    located = clean.loc[clean["geo_context_available"] & clean["location"].notna()].copy()
    groups: list[dict[str, object]] = []
    for group_index, ((study_id, location), group) in enumerate(
        located.groupby(["study_id", "location"], sort=True), start=1
    ):
        first = group.iloc[0]
        group_id = f"c1-anchor-group-{group_index:03d}"
        clean.loc[group.index, "anchor_group_id"] = group_id
        coordinates = None
        raw_coordinates = first.get("geo_multi_site_coordinates_json")
        if isinstance(raw_coordinates, str) and raw_coordinates.strip():
            coordinates = json.loads(raw_coordinates)
        if not coordinates:
            coordinates = [{"lat": first["geo_lat"], "lng": first["geo_lng"]}]

        category_counts = {
            str(category): int(count)
            for category, count in group["category"].value_counts().items()
        }
        study_types = sorted(set(group["study_type"].dropna().astype(str)))
        dominant_category = max(category_counts, key=category_counts.get)
        anchor_ids = []
        anchors = []
        for site_index, coordinate in enumerate(coordinates, start=1):
            anchor_id = f"{group_id}-site-{site_index}"
            anchor_ids.append(anchor_id)
            anchors.append({
                "anchor_id": anchor_id,
                "site_index": site_index,
                "site_count": len(coordinates),
                "site_label": coordinate.get("label") or (
                    f"Site {site_index}" if len(coordinates) > 1 else None
                ),
                "lat": float(coordinate["lat"]),
                "lng": float(coordinate["lng"]),
            })

        groups.append({
            "anchor_group_id": group_id,
            "study_id": int(study_id),
            "source_location": str(location),
            "label": json_value(first["geo_label"]) or str(location),
            "study_type": study_types[0] if len(study_types) == 1 else "Mixed",
            "publication_year": json_value(first["publication_year"]),
            "title": json_value(first["title"]),
            "doi": json_value(first["doi"]),
            "geometry_type": json_value(first["geo_geometry"]),
            "precision": json_value(first["geo_precision"]),
            "confidence": json_value(first["geo_confidence"]),
            "review_status": json_value(first["geo_review_status"]),
            "point_eligible": bool(first["geo_point_eligible"]),
            "bbox": [
                json_value(first["geo_bbox_south"]), json_value(first["geo_bbox_north"]),
                json_value(first["geo_bbox_west"]), json_value(first["geo_bbox_east"]),
            ],
            "effect_count": int(len(group)),
            "effect_ids": group["effect_id"].tolist(),
            "category_counts": category_counts,
            "dominant_category": dominant_category,
            "anchors": anchors,
            "anchor_ids": anchor_ids,
        })
    return groups


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    source = pd.read_excel(SOURCE_XLSX)
    if not LOCATION_RESOLUTION_CSV.exists():
        raise FileNotFoundError(
            f"Location audit is required before preparing C1: {LOCATION_RESOLUTION_CSV}"
        )
    location_resolution = pd.read_csv(LOCATION_RESOLUTION_CSV)
    viirs_cities = json.loads(VIIRS_CITIES_JSON.read_text(encoding="utf-8"))["cities"]
    cities_by_name = {normalize_place(city["name"]): city for city in viirs_cities}
    clean = source.rename(columns=SOURCE_TO_CLEAN).copy()
    clean = clean[list(SOURCE_TO_CLEAN.values())]

    for column in clean.select_dtypes(include=["object", "str"]).columns:
        clean[column] = clean[column].map(clean_text)

    for column in [
        "study_id", "publication_year", "control_lux", "night_lux", "effect_size",
        "effect_size_se", "effect_abs_source", "directional_effect_source",
    ]:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")

    clean.insert(0, "effect_id", [f"c1-effect-{index:04d}" for index in range(1, len(clean) + 1)])
    clean["source_row"] = np.arange(2, len(clean) + 2)
    clean["category"] = clean["category_source"].map(CATEGORY_LABELS)
    clean["effect_abs"] = clean["effect_size"].abs()
    clean["effect_abs_source_match"] = np.isclose(
        clean["effect_abs"], clean["effect_abs_source"], rtol=0, atol=1e-9, equal_nan=False
    )
    clean["effect_abs_display"] = clean["effect_abs"].clip(upper=DISPLAY_CAP)
    clean["effect_abs_over_cap"] = clean["effect_abs"].gt(DISPLAY_CAP)
    clean["directional_included"] = (
        clean["directional_included_source"].astype("string").str.lower().eq("yes")
    ).fillna(False)
    clean["directional_effect"] = clean["directional_effect_source"].where(clean["directional_included"])
    clean["record_key_unique"] = ~clean.duplicated(["study_id", "source_id"], keep=False)

    location_columns = {
        "source_location": "location",
        "candidate_label": "geo_label",
        "geometry_type": "geo_geometry",
        "precision": "geo_precision",
        "latitude": "geo_lat",
        "longitude": "geo_lng",
        "bbox_south": "geo_bbox_south",
        "bbox_north": "geo_bbox_north",
        "bbox_west": "geo_bbox_west",
        "bbox_east": "geo_bbox_east",
        "confidence": "geo_confidence",
        "review_status": "geo_review_status",
        "point_eligible": "geo_point_eligible",
        "multi_site_coordinates_json": "geo_multi_site_coordinates_json",
        "resolution_source": "geo_resolution",
    }
    clean = clean.merge(
        location_resolution[list(location_columns)].rename(columns=location_columns),
        how="left",
        on="location",
        validate="many_to_one",
    )
    clean["geo_context_available"] = clean["geo_lat"].notna() & clean["geo_lng"].notna()
    clean["geo_point_eligible"] = clean["geo_point_eligible"].fillna(False).astype(bool)
    clean["geo_mapped"] = clean["geo_context_available"] & clean["geo_point_eligible"]
    clean["anchor_group_id"] = pd.NA

    # VIIRS city statistics remain an optional contextual lookup. Geographic
    # resolution no longer depends on this 50-city reference table.
    resolved_cities = [resolve_existing_viirs_city(value, cities_by_name) for value in clean["location"]]
    clean["viirs_2024_meanlit"] = [city.get("meanlit", [None])[-1] if city else None for city in resolved_cities]
    clean["viirs_context_scope"] = ["2024 city-area mean radiance where lit" if city else pd.NA for city in resolved_cities]

    anchor_groups = make_anchor_groups(clean)

    flags: list[dict[str, object]] = []
    for row in clean.loc[~clean["effect_abs_source_match"]].itertuples():
        flags.append({
            "effect_id": row.effect_id,
            "source_row": row.source_row,
            "severity": "high",
            "flag": "absolute_effect_mismatch",
            "detail": "Source absolute-effect value does not equal abs(Effect size (ES)); processed effect_abs is recomputed from Effect size (ES).",
        })
    outside_direction = clean["directional_effect_source"].notna() & ~clean["directional_included"]
    for row in clean.loc[outside_direction].itertuples():
        flags.append({
            "effect_id": row.effect_id,
            "source_row": row.source_row,
            "severity": "medium",
            "flag": "directional_value_not_included",
            "detail": "A directional value exists although Included (directional ES) is blank; it is excluded from processed directional_effect.",
        })
    for row in clean.loc[clean["night_lux"].isna()].itertuples():
        flags.append({
            "effect_id": row.effect_id,
            "source_row": row.source_row,
            "severity": "medium",
            "flag": "night_lux_missing",
            "detail": "Night-lux category is present but the numeric Night_Lux value is missing.",
        })
    quality_flags = pd.DataFrame(
        flags, columns=["effect_id", "source_row", "severity", "flag", "detail"]
    )

    category_summary = []
    for category in CATEGORY_LABELS.values():
        group = clean.loc[clean["category"].eq(category)]
        top_subcategories = [
            {"name": str(name), "count": int(count)}
            for name, count in group["subcategory"].value_counts().head(6).items()
        ]
        category_summary.append({
            "category": category,
            "color": CATEGORY_COLORS[category],
            "effect_count": int(len(group)),
            "study_count": int(group["study_id"].nunique()),
            "named_species_count": int(group["species"].nunique()),
            "median_abs_effect": float(group["effect_abs"].median()),
            "p95_abs_effect": float(group["effect_abs"].quantile(0.95)),
            "over_display_cap_count": int(group["effect_abs_over_cap"].sum()),
            "point_ready_effect_count": int(group["geo_mapped"].sum()),
            "context_effect_count": int((group["geo_context_available"] & ~group["geo_mapped"]).sum()),
            "unlocated_effect_count": int((~group["geo_context_available"]).sum()),
            "top_subcategories": top_subcategories,
        })

    point_ready = clean["geo_mapped"]
    geographic_context = clean["geo_context_available"] & ~point_ready
    unlocated = ~clean["geo_context_available"]
    point_ready_locations = location_resolution.loc[
        location_resolution["point_eligible"].fillna(False), "source_location"
    ].nunique()
    review_needed_locations = int(
        location_resolution["review_status"].astype(str).str.startswith("needs_").sum()
    )
    exact_anchor_groups = sum(bool(group["point_eligible"]) for group in anchor_groups)

    summary = {
        "source_file": SOURCE_XLSX.name,
        "source_sheet": "Arkusz1",
        "source_rows": int(len(source)),
        "source_columns": int(source.shape[1]),
        "study_count": int(clean["study_id"].nunique()),
        "effect_count": int(len(clean)),
        "named_species_count": int(clean["species"].nunique()),
        "phylum_count": int(clean["phylum"].nunique()),
        "category_count": int(clean["category"].nunique()),
        "publication_year_min": int(clean["publication_year"].min()),
        "publication_year_max": int(clean["publication_year"].max()),
        "directional_included_count": int(clean["directional_included"].sum()),
        "duplicate_study_source_id_rows": int((~clean["record_key_unique"]).sum()),
        "exact_duplicate_rows": int(source.duplicated().sum()),
        "absolute_effect_mismatch_count": int((~clean["effect_abs_source_match"]).sum()),
        "directional_value_outside_included_count": int(outside_direction.sum()),
        "missing_night_lux_count": int(clean["night_lux"].isna().sum()),
        "effect_size_missing_count": int(clean["effect_size"].isna().sum()),
        "effect_size_se_nonpositive_count": int(clean["effect_size_se"].le(0).sum()),
        "effect_abs_median": float(clean["effect_abs"].median()),
        "effect_abs_p95": float(clean["effect_abs"].quantile(0.95)),
        "effect_abs_p99": float(clean["effect_abs"].quantile(0.99)),
        "effect_abs_max": float(clean["effect_abs"].max()),
        "display_cap": DISPLAY_CAP,
        "over_display_cap_count": int(clean["effect_abs_over_cap"].sum()),
        "mapped_effect_count": int(point_ready.sum()),
        "context_effect_count": int(geographic_context.sum()),
        "unlocated_effect_count": int(unlocated.sum()),
        "unmapped_effect_count": int((~point_ready).sum()),
        "mapped_field_effect_count": int((point_ready & clean["study_type"].eq("Field")).sum()),
        "mapped_laboratory_effect_count": int((point_ready & clean["study_type"].eq("Laboratory")).sum()),
        "mapped_location_count": int(point_ready_locations),
        "location_candidate_count": int(len(location_resolution)),
        "review_needed_location_count": review_needed_locations,
        "anchor_group_count": int(len(anchor_groups)),
        "anchor_count": int(sum(len(group["anchors"]) for group in anchor_groups)),
        "exact_anchor_group_count": int(exact_anchor_groups),
        "context_anchor_group_count": int(len(anchor_groups) - exact_anchor_groups),
        "geographic_resolution_rule": "Study + source-location anchors; crisp points only for reviewed point-eligible locations, with countries and broad regions shown as contextual uncertainty rather than exact sites.",
        "primary_visual_encoding": "absolute Hedges g magnitude on a log1p axis; signed direction retained only in record detail",
        "causal_interpretation": "standardized experimental/observational effect records; sign is not benefit/harm",
    }

    payload = {
        "meta": summary,
        "categories": category_summary,
        "anchor_groups": anchor_groups,
        "effects": [compact_record(row) for _, row in clean.iterrows()],
    }

    clean.to_csv(OUTPUT_DIR / "c1_effects.csv", index=False)
    quality_flags.to_csv(OUTPUT_DIR / "c1_effects_quality_flags.csv", index=False)
    (OUTPUT_DIR / "c1_effects_summary.json").write_text(
        json.dumps({"summary": summary, "categories": category_summary}, indent=2), encoding="utf-8"
    )
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (OUTPUT_DIR / "c1_effects.json").write_text(serialized, encoding="utf-8")
    (APP_DATA_DIR / "c1_effects.json").write_text(serialized, encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
