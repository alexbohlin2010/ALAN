from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


SOURCE = Path(
    "/Users/lindaxiangyideng/Documents/FA26 studio A2/data/street spectra data/"
    "ACTION_Street_Spectra.csv"
)
OUT = Path(
    "/Users/lindaxiangyideng/Documents/FA26 studio A2/analysis/"
    "street_spectra_summary.json"
)

SOURCE_FIELD = "4_Illumination_sourc"
PHOTO_FIELD = "3_Take_an_image_of_a"
LAT_FIELD = "lat_2_Location"
LON_FIELD = "long_2_Location"
ACCURACY_FIELD = "accuracy_2_Location"

SOURCE_NAMES = {
    "LED - Light Emitting Diode": "LED",
    "HPS - High Pressure Sodium": "HPS",
    "MV - Mercury Vapor": "MV",
    "MH - Metal Halide": "MH",
}


def parse_float(value: str):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def parse_timestamp(value: str):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.DictReader(handle))

total = len(rows)
source_counts = Counter(SOURCE_NAMES.get(row[SOURCE_FIELD], "Unknown") for row in rows)
classified = total - source_counts["Unknown"]

valid_coords = []
accuracies = []
spain_bbox = 0
for row in rows:
    lat = parse_float(row[LAT_FIELD])
    lon = parse_float(row[LON_FIELD])
    accuracy = parse_float(row[ACCURACY_FIELD])
    if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
        valid_coords.append((lat, lon))
        if 35.5 <= lat <= 44.5 and -10.0 <= lon <= 4.5:
            spain_bbox += 1
    if accuracy is not None and accuracy >= 0:
        accuracies.append(accuracy)

accuracies.sort()


def percentile(values, probability):
    if not values:
        return None
    index = (len(values) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[lower]
    return values[lower] * (upper - index) + values[upper] * (index - lower)


created = [parse_timestamp(row["created_at"]) for row in rows]
created = [value for value in created if value]
uploaded = [parse_timestamp(row["uploaded_at"]) for row in rows]
uploaded = [value for value in uploaded if value]

upload_lags_seconds = []
for row in rows:
    created_at = parse_timestamp(row["created_at"])
    uploaded_at = parse_timestamp(row["uploaded_at"])
    if created_at and uploaded_at:
        lag = (uploaded_at - created_at).total_seconds()
        if lag >= 0:
            upload_lags_seconds.append(lag)
upload_lags_seconds.sort()

year_counts = Counter(value.year for value in created)
source_by_year = defaultdict(Counter)
for row in rows:
    date = parse_timestamp(row["created_at"])
    if date:
        source_by_year[date.year][SOURCE_NAMES.get(row[SOURCE_FIELD], "Unknown")] += 1

uuid_counts = Counter(row["ec5_uuid"] for row in rows)
photo_present = sum(bool(row[PHOTO_FIELD].strip()) for row in rows)
nickname_present = sum(bool(row["1_Share_your_nick_wi"].strip()) for row in rows)
comments_present = sum(bool(row["5_Comments"].strip()) for row in rows)
title_uuid_matches = sum(row["title"] == row["ec5_uuid"] for row in rows)

summary_rows = []
for category in ["LED", "HPS", "MV", "MH", "Unknown"]:
    count = source_counts[category]
    summary_rows.append(
        {
            "technology": category,
            "records": count,
            "share_all_pct": round(100 * count / total, 1),
            "share_classified_pct": (
                round(100 * count / classified, 1) if category != "Unknown" else None
            ),
        }
    )

output = {
    "file": SOURCE.name,
    "rows": total,
    "date_range": {
        "created_min": min(created).date().isoformat(),
        "created_max": max(created).date().isoformat(),
    },
    "identity": {
        "unique_uuid": len(uuid_counts),
        "duplicate_uuid_rows": sum(count - 1 for count in uuid_counts.values() if count > 1),
        "title_equals_uuid": title_uuid_matches,
    },
    "completeness": {
        "photo_present": photo_present,
        "photo_present_pct": round(100 * photo_present / total, 1),
        "nickname_present": nickname_present,
        "nickname_present_pct": round(100 * nickname_present / total, 1),
        "comments_present": comments_present,
        "comments_present_pct": round(100 * comments_present / total, 1),
        "coordinates_present": len(valid_coords),
        "coordinates_present_pct": round(100 * len(valid_coords) / total, 1),
        "source_label_present": classified,
        "source_label_present_pct": round(100 * classified / total, 1),
    },
    "location": {
        "valid_coordinates": len(valid_coords),
        "unique_exact_coordinates": len(set(valid_coords)),
        "spain_bbox_records": spain_bbox,
        "spain_bbox_pct_of_valid": round(100 * spain_bbox / len(valid_coords), 1),
        "gps_accuracy_median_m": round(percentile(accuracies, 0.5), 1),
        "gps_accuracy_p90_m": round(percentile(accuracies, 0.9), 1),
        "gps_accuracy_max_m": max(accuracies),
        "gps_accuracy_le_10m_pct": round(
            100 * sum(value <= 10 for value in accuracies) / len(accuracies), 1
        ),
    },
    "upload_lag": {
        "median_seconds": round(percentile(upload_lags_seconds, 0.5), 1),
        "p90_seconds": round(percentile(upload_lags_seconds, 0.9), 1),
    },
    "technology_summary": summary_rows,
    "records_by_year": dict(sorted(year_counts.items())),
    "technology_by_year": {
        str(year): dict(source_by_year[year]) for year in sorted(source_by_year)
    },
}

OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
print(json.dumps(output, indent=2))
