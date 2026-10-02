#!/usr/bin/env python3
"""Prepare the Body / circadian-clock data for the ALAN narrative.

The pipeline preserves three different grains:

* mechanized-perch behaviour is measured per cage and minute;
* gene expression is measured per sampled bird, tissue, gene and ZT;
* melatonin is measured per sampled bird and ZT.

Social-cage behaviour is never relabelled as individual behaviour. Gene and
melatonin values are exported only at their measured ZT1/7/13/19 markers; this
script does not create interpolated measurements.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = ROOT / "Linda/data/body data"
OUTPUT_DIR = ROOT / "Linda/processed/body_clocks"

SOCIAL_ALAN = SOURCE_DIR / "Social_ALAN.csv"
PRIMARY_TREATMENTS = {"SA", "SLD"}
TREATMENT_LABELS = {
    "SA": "Social ALAN",
    "SLD": "Social Control",
    "A": "Isolated ALAN",
    "LD": "Isolated Control",
}
MEASURED_ZT = {1, 7, 13, 19}
LIGHTS_ON_MINUTE = 9 * 60
LIGHTS_OFF_MINUTE = 21 * 60


@dataclass(frozen=True)
class BehaviourCohort:
    cohort_id: str
    experiment_start: str
    directory: str
    metadata: str


BEHAVIOUR_COHORTS = (
    BehaviourCohort("cohort_1", "2/7/2023", "Raw Data", "meta.csv"),
    BehaviourCohort("cohort_2", "3/15/2023", "Raw Data2", "meta2.csv"),
    BehaviourCohort("cohort_3", "9/1/2023", "Raw Data3", "meta3.csv"),
    BehaviourCohort("cohort_4", "10/13/2023", "Raw Data4", "meta4.csv"),
)

GENES = (
    ("hypothalamus", "bmal1", "BMAL"),
    ("hypothalamus", "cry1", "CRY"),
    ("hypothalamus", "per2", "PER2"),
    ("hypothalamus", "per3", "PER3"),
    ("liver", "bmal1", "L_BMAL"),
    ("liver", "cry1", "L_CRY"),
    ("liver", "per2", "L_PER2"),
    ("liver", "per3", "L_PER3"),
)


class RunningStats:
    def __init__(self) -> None:
        self.n = 0
        self.total = 0.0
        self.total_sq = 0.0

    def add(self, value: float) -> None:
        self.n += 1
        self.total += value
        self.total_sq += value * value

    @property
    def mean(self) -> float | None:
        return self.total / self.n if self.n else None

    @property
    def sd(self) -> float | None:
        if self.n < 2:
            return None
        variance = (self.total_sq - self.total * self.total / self.n) / (self.n - 1)
        return math.sqrt(max(0.0, variance))

    @property
    def sem(self) -> float | None:
        return self.sd / math.sqrt(self.n) if self.sd is not None else None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def clean_text(value: str | None) -> str:
    return str(value or "").strip()


def parse_float(value: str | None) -> float | None:
    text = clean_text(value)
    if text == "" or text.lower() in {"na", "nan", "n/a"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int(value: str | None) -> int | None:
    number = parse_float(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def rounded(value: float | None, digits: int = 6) -> float | str:
    return "" if value is None else round(float(value), digits)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        if not rows:
            raise ValueError(f"Cannot infer columns for empty output: {path}")
        fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sample_stats(values: Iterable[float]) -> dict[str, float | int | None]:
    vals = [float(value) for value in values]
    if not vals:
        return {"n": 0, "mean": None, "sd": None, "sem": None}
    sd = statistics.stdev(vals) if len(vals) > 1 else None
    return {
        "n": len(vals),
        "mean": statistics.mean(vals),
        "sd": sd,
        "sem": sd / math.sqrt(len(vals)) if sd is not None else None,
    }


def cohort_type(date_in: str) -> str:
    if date_in == "9/1/2023":
        return "molecular_fall"
    if date_in == "10/13/2023":
        return "melatonin_only"
    return "molecular_spring"


def subject_record_id(row: dict[str, str]) -> str:
    return f"{row['Date_In']}|{row['Bird_Id']}"


def load_subject_rows() -> tuple[list[dict[str, str]], dict]:
    rows = read_csv(SOCIAL_ALAN)
    required = {
        "Bird_Id", "Cage", "Sex", "Light_Condition", "Social_Condition",
        "treatment", "Date_In", "Sac_Day", "phase", "time", "melatonin",
        *(column for _, _, column in GENES),
        *(f"on{day}" for day in range(1, 10)),
        *(f"off{day}" for day in range(1, 10)),
    }
    missing = required - set(rows[0]) if rows else required
    if missing:
        raise ValueError(f"Social_ALAN.csv missing columns: {sorted(missing)}")

    ids = [subject_record_id(row) for row in rows]
    global_ids = Counter(row["Bird_Id"] for row in rows)
    quality = {
        "source_rows": len(rows),
        "source_columns": len(rows[0]) if rows else 0,
        "duplicate_composite_subject_ids": sum(count - 1 for count in Counter(ids).values() if count > 1),
        "bird_ids_reused_across_experiments": sum(1 for count in global_ids.values() if count > 1),
        "missing_sampling_time": sum(parse_int(row["time"]) is None for row in rows),
        "unexpected_sampling_time": sum(
            parse_int(row["time"]) is not None and parse_int(row["time"]) not in MEASURED_ZT
            for row in rows
        ),
        "treatment_counts": dict(sorted(Counter(row["treatment"] for row in rows).items())),
        "cohort_counts": dict(sorted(Counter(row["Date_In"] for row in rows).items())),
    }
    return rows, quality


def treatment_overrides(subjects: list[dict[str, str]]) -> dict[tuple[str, int], str]:
    candidates: defaultdict[tuple[str, int], set[str]] = defaultdict(set)
    for row in subjects:
        cage = parse_int(row["Cage"])
        treatment = clean_text(row["treatment"])
        if cage is not None and treatment:
            candidates[(row["Date_In"], cage)].add(treatment)
    return {
        key: next(iter(values))
        for key, values in candidates.items()
        if len(values) == 1
    }


def make_subjects(subjects: list[dict[str, str]]) -> list[dict]:
    output = []
    for row in subjects:
        zt = parse_int(row["time"])
        treatment = clean_text(row["treatment"])
        has_gene = any(parse_float(row[column]) is not None for _, _, column in GENES)
        output.append({
            "subject_record_id": subject_record_id(row),
            "bird_id": row["Bird_Id"],
            "experiment_start": row["Date_In"],
            "source_cohort": cohort_type(row["Date_In"]),
            "cage": row["Cage"],
            "sex": row["Sex"].upper(),
            "treatment": treatment,
            "treatment_label": TREATMENT_LABELS.get(treatment, treatment),
            "light_condition": row["Light_Condition"],
            "social_condition": row["Social_Condition"],
            "sacrifice_day": row["Sac_Day"],
            "zt_sample": "" if zt is None else zt,
            "source_phase": row["phase"],
            "primary_comparison": bool_text(treatment in PRIMARY_TREATMENTS),
            "has_clock_gene_measurement": bool_text(has_gene),
            "has_melatonin_measurement": bool_text(parse_float(row["melatonin"]) is not None),
            "comments": row["Comments"],
        })
    return output


def normalization_key(row: dict[str, str], tissue: str, gene: str) -> str | None:
    cohort = cohort_type(row["Date_In"])
    if cohort == "melatonin_only":
        return None
    if gene == "per2" and cohort == "molecular_fall":
        return None
    if tissue == "liver" and gene == "per3":
        return "all_molecular"
    return cohort


def make_expression(subjects: list[dict[str, str]]) -> tuple[list[dict], list[dict], dict]:
    prepared: list[dict] = []
    scale_values: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in subjects:
        for tissue, gene, column in GENES:
            value = parse_float(row[column])
            key = normalization_key(row, tissue, gene)
            if value is not None and key is not None:
                scale_values[(tissue, gene, key)].append(value)
            prepared.append({
                "subject_record_id": subject_record_id(row),
                "bird_id": row["Bird_Id"],
                "experiment_start": row["Date_In"],
                "source_cohort": cohort_type(row["Date_In"]),
                "treatment": row["treatment"],
                "treatment_label": TREATMENT_LABELS.get(row["treatment"], row["treatment"]),
                "primary_comparison": bool_text(row["treatment"] in PRIMARY_TREATMENTS),
                "zt": parse_int(row["time"]),
                "tissue": tissue,
                "gene": gene,
                "source_column": column,
                "raw_expression_2ddct": value,
                "normalization_key": key,
            })

    scales: dict[tuple[str, str, str], tuple[float, float]] = {}
    for key, values in scale_values.items():
        scales[key] = (min(values), max(values))

    missing_by_field: Counter = Counter()
    excluded_fall_per2 = 0
    for item in prepared:
        value = item["raw_expression_2ddct"]
        key = item["normalization_key"]
        quality_flag = "valid"
        normalized = None
        if value is None:
            quality_flag = "missing_source_value"
            missing_by_field[item["source_column"]] += 1
        elif key is None:
            if item["source_cohort"] == "molecular_fall" and item["gene"] == "per2":
                quality_flag = "excluded_by_source_analysis_fall_per2"
                excluded_fall_per2 += 1
            else:
                quality_flag = "not_a_molecular_subject"
        else:
            lower, upper = scales[(item["tissue"], item["gene"], key)]
            normalized = (value - lower) / (upper - lower) if upper > lower else 0.0
        item["raw_expression_2ddct"] = rounded(value, 7)
        item["analysis_value_0_1"] = rounded(normalized, 7)
        item["quality_flag"] = quality_flag
        item["measured_not_interpolated"] = "true"
        if item["zt"] is None:
            item["zt"] = ""

    grouped: defaultdict[tuple[str, str, str, int], dict[str, list[float]]] = defaultdict(
        lambda: {"raw": [], "normalized": []}
    )
    for item in prepared:
        if item["treatment"] not in PRIMARY_TREATMENTS or item["quality_flag"] != "valid":
            continue
        zt = int(item["zt"])
        key = (item["treatment"], item["tissue"], item["gene"], zt)
        grouped[key]["raw"].append(float(item["raw_expression_2ddct"]))
        grouped[key]["normalized"].append(float(item["analysis_value_0_1"]))

    summary = []
    for (treatment, tissue, gene, zt), values in sorted(grouped.items()):
        raw_stats = sample_stats(values["raw"])
        norm_stats = sample_stats(values["normalized"])
        summary.append({
            "treatment": treatment,
            "treatment_label": TREATMENT_LABELS[treatment],
            "tissue": tissue,
            "gene": gene,
            "zt": zt,
            "n": norm_stats["n"],
            "raw_mean_2ddct": rounded(raw_stats["mean"], 7),
            "raw_sem_2ddct": rounded(raw_stats["sem"], 7),
            "analysis_mean_0_1": rounded(norm_stats["mean"], 7),
            "analysis_sem_0_1": rounded(norm_stats["sem"], 7),
            "measurement_status": "measured marker",
        })

    quality = {
        "long_rows": len(prepared),
        "valid_measurements": sum(item["quality_flag"] == "valid" for item in prepared),
        "missing_by_source_column": dict(sorted(missing_by_field.items())),
        "fall_per2_rows_excluded_to_match_source_analysis": excluded_fall_per2,
        "summary_rows": len(summary),
    }
    return prepared, summary, quality


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 3:
        return None
    x_mean = statistics.mean(x)
    y_mean = statistics.mean(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    denominator = math.sqrt(
        sum((a - x_mean) ** 2 for a in x) * sum((b - y_mean) ** 2 for b in y)
    )
    return numerator / denominator if denominator else None


def make_correlations(expression_rows: list[dict]) -> list[dict]:
    by_subject: defaultdict[tuple[str, int, str], dict[tuple[str, str], float]] = defaultdict(dict)
    for row in expression_rows:
        if row["treatment"] not in {"A", "SA"} or row["quality_flag"] != "valid":
            continue
        zt = int(row["zt"])
        if zt not in {1, 13}:
            continue
        key = (row["treatment"], zt, row["subject_record_id"])
        by_subject[key][(row["tissue"], row["gene"])] = float(row["analysis_value_0_1"])

    output = []
    for treatment in ("A", "SA"):
        for zt in (1, 13):
            subjects = [values for (group, time, _), values in by_subject.items() if group == treatment and time == zt]
            for brain_gene in ("bmal1", "cry1", "per2", "per3"):
                for liver_gene in ("bmal1", "cry1", "per2", "per3"):
                    pairs = [
                        (values[("hypothalamus", brain_gene)], values[("liver", liver_gene)])
                        for values in subjects
                        if ("hypothalamus", brain_gene) in values and ("liver", liver_gene) in values
                    ]
                    r = pearson([pair[0] for pair in pairs], [pair[1] for pair in pairs])
                    output.append({
                        "treatment": treatment,
                        "treatment_label": TREATMENT_LABELS[treatment],
                        "zt": zt,
                        "brain_gene": brain_gene,
                        "liver_gene": liver_gene,
                        "n_paired_birds": len(pairs),
                        "pearson_r": rounded(r, 6),
                        "evidence_scope": "ALAN-exposed isolated-versus-social comparison; exploratory display support",
                    })
    return output


def make_melatonin(
    subjects: list[dict[str, str]],
) -> tuple[list[dict], list[dict], list[dict], dict]:
    values_by_cohort: defaultdict[str, list[float]] = defaultdict(list)
    for row in subjects:
        value = parse_float(row["melatonin"])
        if value is not None:
            values_by_cohort[cohort_type(row["Date_In"])].append(value)
    scales = {key: (min(values), max(values)) for key, values in values_by_cohort.items()}

    output = []
    for row in subjects:
        value = parse_float(row["melatonin"])
        cohort = cohort_type(row["Date_In"])
        normalized = None
        if value is not None:
            lower, upper = scales[cohort]
            normalized = (value - lower) / (upper - lower) if upper > lower else 0.0
        output.append({
            "subject_record_id": subject_record_id(row),
            "bird_id": row["Bird_Id"],
            "experiment_start": row["Date_In"],
            "source_cohort": cohort,
            "treatment": row["treatment"],
            "treatment_label": TREATMENT_LABELS.get(row["treatment"], row["treatment"]),
            "primary_comparison": bool_text(row["treatment"] in PRIMARY_TREATMENTS),
            "zt": "" if parse_int(row["time"]) is None else parse_int(row["time"]),
            "raw_melatonin": rounded(value, 6),
            "raw_units": "not stated in source CSV",
            "analysis_value_0_1": rounded(normalized, 7),
            "quality_flag": "valid" if value is not None else "missing_source_value",
            "measured_not_interpolated": "true",
        })

    grouped: defaultdict[tuple[str, str, int], dict[str, list[float]]] = defaultdict(
        lambda: {"raw": [], "normalized": []}
    )
    for row in output:
        if row["treatment"] not in PRIMARY_TREATMENTS or row["quality_flag"] != "valid" or row["zt"] == "":
            continue
        key = (row["source_cohort"], row["treatment"], int(row["zt"]))
        grouped[key]["raw"].append(float(row["raw_melatonin"]))
        grouped[key]["normalized"].append(float(row["analysis_value_0_1"]))
    by_cohort_summary = []
    for (source_cohort, treatment, zt), values in sorted(grouped.items()):
        raw_stats = sample_stats(values["raw"])
        norm_stats = sample_stats(values["normalized"])
        by_cohort_summary.append({
            "source_cohort": source_cohort,
            "treatment": treatment,
            "treatment_label": TREATMENT_LABELS[treatment],
            "zt": zt,
            "n": norm_stats["n"],
            "raw_mean": rounded(raw_stats["mean"], 6),
            "raw_sem": rounded(raw_stats["sem"], 6),
            "analysis_mean_0_1": rounded(norm_stats["mean"], 7),
            "analysis_sem_0_1": rounded(norm_stats["sem"], 7),
            "measurement_status": "measured marker",
        })
    # The 10/13/2023 rows contain no clock-gene measurements and exactly match
    # the dedicated 40-bird melatonin cohort described in the source paper.
    # Keep molecular-cohort melatonin values in the long table and by-cohort
    # summary, but use only this dedicated cohort for the Body scene series.
    scene_summary = [
        row for row in by_cohort_summary if row["source_cohort"] == "melatonin_only"
    ]
    quality = {
        "rows": len(output),
        "valid_measurements": sum(row["quality_flag"] == "valid" for row in output),
        "missing_measurements": sum(row["quality_flag"] != "valid" for row in output),
        "by_cohort_summary_rows": len(by_cohort_summary),
        "scene_summary_rows": len(scene_summary),
        "scene_source_cohort": "melatonin_only",
        "scene_primary_measurements": sum(
            row["quality_flag"] == "valid"
            and row["source_cohort"] == "melatonin_only"
            and row["treatment"] in PRIMARY_TREATMENTS
            for row in output
        ),
        "raw_units_known": False,
    }
    return output, scene_summary, by_cohort_summary, quality


def make_activity_timing(subjects: list[dict[str, str]]) -> tuple[list[dict], list[dict], dict]:
    candidates: defaultdict[tuple[str, int, str, int], set[tuple[float | None, float | None]]] = defaultdict(set)
    for row in subjects:
        cage = parse_int(row["Cage"])
        if cage is None:
            continue
        for day in range(1, 10):
            onset = parse_float(row[f"on{day}"])
            offset = parse_float(row[f"off{day}"])
            candidates[(row["Date_In"], cage, row["treatment"], day)].add((onset, offset))

    inconsistent = sum(len(values) > 1 for values in candidates.values())
    output = []
    for (experiment_start, cage, treatment, day), values in sorted(candidates.items()):
        valid_pairs = sorted(pair for pair in values if pair != (None, None))
        if not valid_pairs:
            onset, offset = None, None
            flag = "missing_both"
        elif len(valid_pairs) == 1:
            onset, offset = valid_pairs[0]
            flag = "valid" if onset is not None and offset is not None else "partial_missing"
        else:
            onset, offset = None, None
            flag = "conflicting_values_within_cage_day"
        output.append({
            "cage_record_id": f"{experiment_start}|cage-{cage}",
            "experiment_start": experiment_start,
            "cage": cage,
            "measurement_grain": "cage",
            "treatment": treatment,
            "treatment_label": TREATMENT_LABELS.get(treatment, treatment),
            "primary_comparison": bool_text(treatment in PRIMARY_TREATMENTS),
            "experimental_day": day,
            "onset_minutes_from_lights_on": rounded(onset, 3),
            "offset_minutes_from_lights_off": rounded(offset, 3),
            "quality_flag": flag,
        })

    grouped: defaultdict[tuple[str, int], dict[str, list[float]]] = defaultdict(
        lambda: {"onset": [], "offset": []}
    )
    for row in output:
        if row["treatment"] not in PRIMARY_TREATMENTS or row["quality_flag"] not in {"valid", "partial_missing"}:
            continue
        key = (row["treatment"], row["experimental_day"])
        if row["onset_minutes_from_lights_on"] != "":
            grouped[key]["onset"].append(float(row["onset_minutes_from_lights_on"]))
        if row["offset_minutes_from_lights_off"] != "":
            grouped[key]["offset"].append(float(row["offset_minutes_from_lights_off"]))
    summary = []
    for (treatment, day), values in sorted(grouped.items()):
        onset_stats = sample_stats(values["onset"])
        offset_stats = sample_stats(values["offset"])
        summary.append({
            "treatment": treatment,
            "treatment_label": TREATMENT_LABELS[treatment],
            "experimental_day": day,
            "n_cages_onset": onset_stats["n"],
            "onset_mean_minutes_from_lights_on": rounded(onset_stats["mean"], 3),
            "onset_sem": rounded(onset_stats["sem"], 3),
            "n_cages_offset": offset_stats["n"],
            "offset_mean_minutes_from_lights_off": rounded(offset_stats["mean"], 3),
            "offset_sem": rounded(offset_stats["sem"], 3),
        })
    quality = {
        "cage_day_rows": len(output),
        "conflicting_cage_day_values": inconsistent,
        "valid_rows": sum(row["quality_flag"] == "valid" for row in output),
        "partial_missing_rows": sum(row["quality_flag"] == "partial_missing" for row in output),
        "missing_rows": sum(row["quality_flag"] == "missing_both" for row in output),
    }
    return output, summary, quality


def parse_lights(value: str) -> int:
    parsed = datetime.strptime(value.strip(), "%I:%M %p")
    return parsed.hour * 60 + parsed.minute


def make_behaviour(
    subjects: list[dict[str, str]],
) -> tuple[list[dict], list[dict], dict]:
    overrides = treatment_overrides(subjects)
    hourly_rows: list[dict] = []
    profile_stats: defaultdict[tuple[str, int], RunningStats] = defaultdict(RunningStats)
    file_count = 0
    separator_rows = 0
    nonzero_separator_values = 0
    invalid_shapes = []
    metadata_fills = []
    recorded_metadata_fills: set[tuple[str, int, str]] = set()
    skipped_blank_treatment_cage_days = 0

    for cohort in BEHAVIOUR_COHORTS:
        metadata_rows = read_csv(SOURCE_DIR / cohort.metadata)
        metadata = {int(row["Cage"]): row for row in metadata_rows}
        paths = sorted(
            (SOURCE_DIR / cohort.directory).glob("*.txt"),
            key=lambda path: datetime.strptime(path.stem, "%B %d, %Y"),
        )
        for path in paths:
            file_count += 1
            date = datetime.strptime(path.stem, "%B %d, %Y").date().isoformat()
            matrix = []
            with path.open(encoding="ascii") as handle:
                for line in handle:
                    values = [int(value) for value in line.split()]
                    matrix.append(values)
            data_shape_ok = len(matrix) == 600 and all(
                (index % 25 == 24 and (len(row) == 0 or (len(row) == 60 and not any(row))))
                or (index % 25 != 24 and len(row) == 60)
                for index, row in enumerate(matrix)
            )
            if not data_shape_ok:
                invalid_shapes.append({"file": str(path), "rows": len(matrix)})
                continue
            if any(value < 0 for row in matrix for value in row):
                raise ValueError(f"Negative behaviour count in {path}")

            for cage in range(1, 25):
                meta = metadata[cage]
                treatment = clean_text(meta["Treatment"])
                if not treatment:
                    treatment = overrides.get((cohort.experiment_start, cage), "")
                    if treatment:
                        fill_key = (cohort.experiment_start, cage, treatment)
                        if fill_key not in recorded_metadata_fills:
                            recorded_metadata_fills.add(fill_key)
                            metadata_fills.append({
                                "experiment_start": cohort.experiment_start,
                                "cage": cage,
                                "filled_treatment": treatment,
                                "source": "Social_ALAN.csv consensus",
                            })
                block = matrix[(cage - 1) * 25:cage * 25]
                separator_rows += 1
                nonzero_separator_values += sum(value != 0 for value in block[24])
                if not treatment:
                    skipped_blank_treatment_cage_days += 1
                    continue
                lights_on = parse_lights(meta["LightsOn"])
                lights_off = parse_lights(meta["LightsOff"])
                for clock_hour, minute_values in enumerate(block[:24]):
                    hour_start = clock_hour * 60
                    phase = "day" if lights_on <= hour_start < lights_off else "night"
                    zt_hour = (clock_hour - lights_on // 60) % 24
                    hourly_rows.append({
                        "cohort_id": cohort.cohort_id,
                        "experiment_start": cohort.experiment_start,
                        "date": date,
                        "cage_record_id": f"{cohort.experiment_start}|cage-{cage}",
                        "cage": cage,
                        "measurement_grain": "cage",
                        "treatment": treatment,
                        "treatment_label": TREATMENT_LABELS.get(treatment, treatment),
                        "primary_comparison": bool_text(treatment in PRIMARY_TREATMENTS),
                        "clock_hour": clock_hour,
                        "zt_hour": zt_hour,
                        "phase": phase,
                        "hops_total_in_hour": sum(minute_values),
                        "mean_hops_per_minute": rounded(statistics.mean(minute_values), 6),
                        "source_file": path.name,
                    })
                    if treatment in PRIMARY_TREATMENTS:
                        for minute, value in enumerate(minute_values):
                            clock_minute = clock_hour * 60 + minute
                            zt_minute = (clock_minute - lights_on) % 1440
                            profile_stats[(treatment, zt_minute)].add(float(value))

    global_max = max(stats.mean or 0.0 for stats in profile_stats.values())
    profile = []
    for (treatment, zt_minute), stats in sorted(profile_stats.items()):
        clock_minute = (zt_minute + LIGHTS_ON_MINUTE) % 1440
        phase = "day" if 0 <= zt_minute < 720 else "night"
        mean_value = stats.mean or 0.0
        profile.append({
            "treatment": treatment,
            "treatment_label": TREATMENT_LABELS[treatment],
            "zt_minute": zt_minute,
            "zt_hour": round(zt_minute / 60, 4),
            "clock_time": f"{clock_minute // 60:02d}:{clock_minute % 60:02d}",
            "phase": phase,
            "n_cage_days": stats.n,
            "mean_hops_per_minute": rounded(mean_value, 6),
            "sd": rounded(stats.sd, 6),
            "sem": rounded(stats.sem, 6),
            "display_intensity_0_1": rounded(mean_value / global_max if global_max else 0.0, 7),
        })

    quality = {
        "raw_files": file_count,
        "hourly_rows": len(hourly_rows),
        "profile_rows": len(profile),
        "separator_rows_checked": separator_rows,
        "nonzero_separator_values": nonzero_separator_values,
        "invalid_file_shapes": invalid_shapes,
        "metadata_treatment_fills": metadata_fills,
        "blank_treatment_cage_days_skipped": skipped_blank_treatment_cage_days,
        "measurement_grain": "cage; social cages contain multiple birds",
    }
    return hourly_rows, profile, quality


def build_scene_json(
    behaviour_profile: list[dict],
    timing_summary: list[dict],
    expression_summary: list[dict],
    melatonin_summary: list[dict],
    correlations: list[dict],
) -> dict:
    return {
        "schema_version": 1,
        "scene": "Body — Clocks Lose Alignment",
        "primary_comparison": [
            {"code": "SLD", "label": "Social Control"},
            {"code": "SA", "label": "Social ALAN"},
        ],
        "time": {
            "zt0_clock_time": "09:00",
            "lights_on_zt": 0,
            "lights_off_zt": 12,
            "measured_molecular_markers": [1, 7, 13, 19],
            "full_cycle_hours": 24,
        },
        "behaviour": {
            "measurement_grain": "cage",
            "continuous_resolution": "one minute",
            "profile": behaviour_profile,
            "activity_timing": timing_summary,
        },
        "clock_expression": {
            "measurement_grain": "sampled bird × tissue × gene × ZT",
            "markers_only": True,
            "summary": expression_summary,
        },
        "melatonin": {
            "measurement_grain": "sampled bird × ZT",
            "markers_only": True,
            "raw_units": "not stated in source CSV",
            "summary": melatonin_summary,
        },
        "brain_liver_correlations": {
            "scope": "A versus SA at ZT1 and ZT13; not the primary SA-versus-SLD comparison",
            "exploratory": True,
            "values": correlations,
        },
        "visualization_rules": [
            "Behaviour may be animated continuously from measured one-minute data.",
            "Gene expression and melatonin are measured only at ZT1, ZT7, ZT13 and ZT19.",
            "Any curve or motion between molecular markers must be labelled interpolation.",
            "Do not relabel social-cage behaviour as individual-bird behaviour.",
            "Do not depict material flowing from brain to liver.",
            "Melatonin remains rhythmic; do not depict a total system collapse.",
        ],
    }


def build_scientific_summary(
    behaviour_profile: list[dict],
    timing_summary: list[dict],
    expression_summary: list[dict],
    melatonin_summary: list[dict],
) -> dict:
    def phase_mean(treatment: str, phase: str) -> float:
        values = [
            float(row["mean_hops_per_minute"])
            for row in behaviour_profile
            if row["treatment"] == treatment and row["phase"] == phase
        ]
        return statistics.mean(values)

    def timing_row(treatment: str, day: int) -> dict:
        return next(
            row for row in timing_summary
            if row["treatment"] == treatment and row["experimental_day"] == day
        )

    def expression_row(treatment: str, tissue: str, gene: str, zt: int) -> dict:
        return next(
            row for row in expression_summary
            if row["treatment"] == treatment
            and row["tissue"] == tissue
            and row["gene"] == gene
            and row["zt"] == zt
        )

    day9 = {treatment: timing_row(treatment, 9) for treatment in ("SLD", "SA")}
    selected_markers = []
    for tissue, gene, zt in (
        ("hypothalamus", "bmal1", 13),
        ("liver", "bmal1", 13),
        ("liver", "per3", 7),
    ):
        selected_markers.append({
            "tissue": tissue,
            "gene": gene,
            "zt": zt,
            "social_control_mean_0_1": expression_row("SLD", tissue, gene, zt)["analysis_mean_0_1"],
            "social_alan_mean_0_1": expression_row("SA", tissue, gene, zt)["analysis_mean_0_1"],
            "interpretation": "descriptive group means; statistical claims remain tied to the paper",
        })

    melatonin_series = {
        treatment: [
            {"zt": row["zt"], "analysis_mean_0_1": row["analysis_mean_0_1"], "n": row["n"]}
            for row in melatonin_summary if row["treatment"] == treatment
        ]
        for treatment in ("SLD", "SA")
    }
    return {
        "primary_comparison": "Social Control (SLD) versus Social ALAN (SA)",
        "behaviour": {
            "social_control_mean_day_hops_per_minute": round(phase_mean("SLD", "day"), 6),
            "social_control_mean_night_hops_per_minute": round(phase_mean("SLD", "night"), 6),
            "social_alan_mean_day_hops_per_minute": round(phase_mean("SA", "day"), 6),
            "social_alan_mean_night_hops_per_minute": round(phase_mean("SA", "night"), 6),
            "day_9_onset_minutes_from_lights_on": {
                "SLD": day9["SLD"]["onset_mean_minutes_from_lights_on"],
                "SA": day9["SA"]["onset_mean_minutes_from_lights_on"],
            },
            "interpretation": "SA activity extends further into night and begins earlier; activity is cage-level.",
        },
        "selected_clock_markers": selected_markers,
        "melatonin": {
            "measured_markers": melatonin_series,
            "interpretation": "retain rhythmic markers; do not depict melatonin as absent",
        },
        "scope_limits": [
            "Descriptive means do not replace the source paper's inferential statistics.",
            "Gene and melatonin measurements are discrete ZT markers, not continuous observations.",
            "Brain–liver correlation claims use the separate A-versus-SA evidence table.",
        ],
    }


def make_quality_markdown(quality: dict) -> str:
    subject = quality["subjects"]
    behaviour = quality["behaviour"]
    expression = quality["expression"]
    melatonin = quality["melatonin"]
    timing = quality["activity_timing"]
    checks = quality["checks"]
    lines = [
        "# Body data preparation quality report",
        "",
        "## Result",
        "",
        "The supplied files cover behaviour, hypothalamus and liver clock-gene expression, and melatonin. The processed outputs are suitable for Step 9 with the caveats below.",
        "",
        "## Dataset grain",
        "",
        "- Behaviour: mechanized-perch hop counts per cage and minute. Social cages contain multiple birds, so these records are not individual trajectories.",
        "- Clock genes: one sampled bird, tissue, gene and ZT marker per record.",
        "- Melatonin: one sampled bird and ZT marker per record in the supplied combined CSV.",
        "- Activity onset and offset: cage-level values supplied in `on1`–`on9` and `off1`–`off9`, measured relative to lights on/off.",
        "",
        "## Coverage",
        "",
        f"- Social_ALAN.csv rows: {subject['source_rows']}",
        f"- Behaviour files: {behaviour['raw_files']}",
        f"- Behaviour hourly records: {behaviour['hourly_rows']}",
        f"- Valid clock-gene measurements: {expression['valid_measurements']}",
        f"- Valid melatonin measurements across all supplied cohorts: {melatonin['valid_measurements']}",
        f"- Dedicated melatonin-cohort measurements in the primary social comparison: {melatonin['scene_primary_measurements']}",
        f"- Valid cage-day onset/offset rows: {timing['valid_rows']}",
        "",
        "## Quality findings",
        "",
        f"- Behaviour matrix blank/zero separators checked: {behaviour['separator_rows_checked']}; non-zero separator values: {behaviour['nonzero_separator_values']}.",
        f"- Invalid behaviour file shapes: {len(behaviour['invalid_file_shapes'])}.",
        f"- Composite subject-ID duplicates: {subject['duplicate_composite_subject_ids']}.",
        f"- Bird labels reused across experiments: {subject['bird_ids_reused_across_experiments']}. The output therefore uses `experiment_start|bird_id` as the stable subject key.",
        f"- Missing sampling times: {subject['missing_sampling_time']}; these rows are retained in subject metadata but excluded from time-point summaries.",
        f"- Conflicting onset/offset values within a cage-day: {timing['conflicting_cage_day_values']}.",
        f"- Fall PER2 records excluded from normalized analysis to match the supplied R workflow: {expression['fall_per2_rows_excluded_to_match_source_analysis']}.",
        f"- Metadata treatment fills: {len(behaviour['metadata_treatment_fills'])}. Cage 4 in the fourth cohort is filled as SLD from the unanimous Social_ALAN.csv records; cage 5 remains unused.",
        "",
        "## Interpretation limits",
        "",
        "- Raw melatonin units are not stated in Social_ALAN.csv, so the scene data uses clearly labelled 0–1 analysis values and retains the raw value without inventing a unit.",
        "- The Body scene melatonin series uses only the dedicated 10/13/2023 melatonin cohort. Values from molecular cohorts remain available in the long table and the by-cohort summary but are not silently pooled.",
        "- The supplied R code normalizes some molecular cohorts separately and excludes fall PER2. The processed data reproduces those choices and records the normalization key for every value.",
        "- Brain–liver correlations are exported only for the paper-aligned ALAN comparison (A versus SA) at ZT1 and ZT13. They must not be presented as an SA-versus-SLD result.",
        "- Molecular and melatonin values are discrete measurements. Step 9 may animate between them only with a visible interpolation label.",
        "",
        "## Validation checks",
        "",
    ]
    lines.extend(f"- {'PASS' if item['passed'] else 'FAIL'}: {item['name']}" for item in checks)
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    if not SOCIAL_ALAN.exists():
        raise FileNotFoundError(f"Missing source data: {SOCIAL_ALAN}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source_subjects, subject_quality = load_subject_rows()
    subjects = make_subjects(source_subjects)
    expression, expression_summary, expression_quality = make_expression(source_subjects)
    correlations = make_correlations(expression)
    melatonin, melatonin_summary, melatonin_by_cohort, melatonin_quality = make_melatonin(source_subjects)
    timing, timing_summary, timing_quality = make_activity_timing(source_subjects)
    behaviour_hourly, behaviour_profile, behaviour_quality = make_behaviour(source_subjects)

    checks = [
        {"name": "all behaviour files have 24 × 60 data rows plus one separator per cage", "passed": not behaviour_quality["invalid_file_shapes"]},
        {"name": "all cage separator rows are blank or zero", "passed": behaviour_quality["nonzero_separator_values"] == 0},
        {"name": "subject composite keys are unique", "passed": subject_quality["duplicate_composite_subject_ids"] == 0},
        {"name": "all non-missing molecular sampling times are ZT1/7/13/19", "passed": subject_quality["unexpected_sampling_time"] == 0},
        {"name": "onset/offset duplicates agree within cage and experimental day", "passed": timing_quality["conflicting_cage_day_values"] == 0},
        {"name": "both primary social treatments have 1,440 minute profile values", "passed": len(behaviour_profile) == 2880},
        {"name": "both primary social treatments have all four molecular ZT markers", "passed": len(expression_summary) == 2 * 2 * 4 * 4},
        {"name": "both primary social treatments have all four melatonin ZT markers", "passed": len(melatonin_summary) == 2 * 4},
    ]
    quality = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_directory": str(SOURCE_DIR.relative_to(ROOT)),
        "subjects": subject_quality,
        "behaviour": behaviour_quality,
        "expression": expression_quality,
        "melatonin": melatonin_quality,
        "activity_timing": timing_quality,
        "correlations": {"rows": len(correlations), "scope": "A versus SA, ZT1 and ZT13"},
        "checks": checks,
        "all_required_checks_passed": all(item["passed"] for item in checks),
    }

    write_csv(OUTPUT_DIR / "body_subjects.csv", subjects)
    write_csv(OUTPUT_DIR / "body_behavior_hourly.csv", behaviour_hourly)
    write_csv(OUTPUT_DIR / "body_behavior_profile.csv", behaviour_profile)
    write_csv(OUTPUT_DIR / "body_activity_timing.csv", timing)
    write_csv(OUTPUT_DIR / "body_activity_timing_summary.csv", timing_summary)
    write_csv(OUTPUT_DIR / "body_clock_expression.csv", expression)
    write_csv(OUTPUT_DIR / "body_clock_expression_summary.csv", expression_summary)
    write_csv(OUTPUT_DIR / "body_melatonin.csv", melatonin)
    write_csv(OUTPUT_DIR / "body_melatonin_summary.csv", melatonin_summary)
    write_csv(OUTPUT_DIR / "body_melatonin_by_cohort_summary.csv", melatonin_by_cohort)
    write_csv(OUTPUT_DIR / "body_brain_liver_correlations.csv", correlations)

    scene = build_scene_json(
        behaviour_profile,
        timing_summary,
        expression_summary,
        melatonin_summary,
        correlations,
    )
    scientific_summary = build_scientific_summary(
        behaviour_profile,
        timing_summary,
        expression_summary,
        melatonin_summary,
    )
    with (OUTPUT_DIR / "body_scene_data.json").open("w", encoding="utf-8") as handle:
        json.dump(scene, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    with (OUTPUT_DIR / "body_quality_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(quality, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    with (OUTPUT_DIR / "body_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(scientific_summary, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    (OUTPUT_DIR / "DATA_QUALITY.md").write_text(make_quality_markdown(quality), encoding="utf-8")

    print(json.dumps({
        "output_directory": str(OUTPUT_DIR),
        "all_required_checks_passed": quality["all_required_checks_passed"],
        "subjects": len(subjects),
        "behaviour_hourly": len(behaviour_hourly),
        "behaviour_profile": len(behaviour_profile),
        "expression": len(expression),
        "expression_summary": len(expression_summary),
        "melatonin": len(melatonin),
        "melatonin_summary": len(melatonin_summary),
    }, indent=2))


if __name__ == "__main__":
    main()
