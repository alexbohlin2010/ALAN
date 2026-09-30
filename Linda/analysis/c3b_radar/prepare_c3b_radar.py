#!/usr/bin/env python3
"""Prepare the McLaren et al. (2018) radar/ALAN data for the C3B globe layer.

The raw response is a multi-year geometric mean of vertically integrated radar
reflectivity (VIR), used by the study as a proxy for migrant stopover density.
The supplied CSV rounds UTM coordinate text enough that multiple source grid
cells share a displayed X/Y pair.  Those collisions are collapsed with medians
before geographic display; the original analysis grain is not re-created.
"""

from __future__ import annotations

import bisect
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "Linda/data/ALAN for habitat/EL_data.csv"
OUT = ROOT / "Linda/processed/c3b_radar"
CLIENT = ROOT / "Alexander/globe_v2/data/c3b_radar.json"

FIELDS = (
    "meanVIR",
    "ALAN",
    "dBrL",
    "dRdr",
    "dAtl",
    "decForestCover",
    "devLandCover",
)


def median(values: list[float]) -> float:
    return float(statistics.median(values))


def rounded(value: float, digits: int = 5) -> float:
    return round(float(value), digits)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    position = (len(values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    weight = position - lower
    return float(values[lower] * (1 - weight) + values[upper] * weight)


def rank_fraction(sorted_values: list[float], value: float) -> float:
    return bisect.bisect_right(sorted_values, value) / len(sorted_values)


def utm18_to_wgs84(easting: float, northing: float) -> tuple[float, float]:
    """Convert WGS84 UTM zone 18N coordinates to latitude/longitude.

    This is the standard transverse-Mercator inverse used here to avoid a
    heavyweight projection dependency in the reproducible data-prep script.
    """

    semi_major = 6378137.0
    eccentricity = 0.08181919084262149
    second_eccentricity_sq = 0.006739496742276434
    scale = 0.9996

    x = easting - 500000.0
    meridional_arc = northing / scale
    mu = meridional_arc / (
        semi_major
        * (
            1
            - eccentricity**2 / 4
            - 3 * eccentricity**4 / 64
            - 5 * eccentricity**6 / 256
        )
    )
    e1 = (1 - math.sqrt(1 - eccentricity**2)) / (
        1 + math.sqrt(1 - eccentricity**2)
    )
    footprint = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )

    cos_footprint = math.cos(footprint)
    tan_sq = math.tan(footprint) ** 2
    c1 = second_eccentricity_sq * cos_footprint**2
    n1 = semi_major / math.sqrt(
        1 - eccentricity**2 * math.sin(footprint) ** 2
    )
    r1 = semi_major * (1 - eccentricity**2) / (
        1 - eccentricity**2 * math.sin(footprint) ** 2
    ) ** 1.5
    d = x / (n1 * scale)

    latitude = footprint - (n1 * math.tan(footprint) / r1) * (
        d**2 / 2
        - (5 + 3 * tan_sq + 10 * c1 - 4 * c1**2 - 9 * second_eccentricity_sq)
        * d**4
        / 24
        + (
            61
            + 90 * tan_sq
            + 298 * c1
            + 45 * tan_sq**2
            - 252 * second_eccentricity_sq
            - 3 * c1**2
        )
        * d**6
        / 720
    )
    longitude_delta = (
        d
        - (1 + 2 * tan_sq + c1) * d**3 / 6
        + (
            5
            - 2 * c1
            + 28 * tan_sq
            - 3 * c1**2
            + 8 * second_eccentricity_sq
            + 24 * tan_sq**2
        )
        * d**5
        / 120
    ) / cos_footprint
    return math.degrees(latitude), -75.0 + math.degrees(longitude_delta)


def band_summary(
    cells: list[dict[str, float]], field: str, boundaries: list[float]
) -> list[dict[str, float | int | str]]:
    result = []
    for lower, upper in zip(boundaries, boundaries[1:]):
        members = [cell for cell in cells if lower <= cell[field] < upper]
        if not members:
            continue
        result.append(
            {
                "variable": field,
                "lower": lower,
                "upper": upper,
                "label": f"{lower:g}–{upper:g}",
                "display_coordinate_count": len(members),
                "source_cell_count": int(sum(cell["source_cell_count"] for cell in members)),
                "median_mean_vir": rounded(
                    median([cell["mean_vir"] for cell in members]), 4
                ),
            }
        )
    return result


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError(f"Missing source data: {RAW}")

    grouped: dict[tuple[float, float], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    all_coordinates: set[tuple[float, float]] = set()
    seen_rows: set[tuple[str, ...]] = set()
    exact_duplicate_rows = 0
    row_count = 0
    valid_response_rows = 0

    with RAW.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("EL_data.csv has no header")
        missing = {"X", "Y", *FIELDS} - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        for row in reader:
            row_count += 1
            raw_key = tuple(row[column] for column in reader.fieldnames)
            if raw_key in seen_rows:
                exact_duplicate_rows += 1
            else:
                seen_rows.add(raw_key)

            coordinate = (float(row["X"]), float(row["Y"]))
            all_coordinates.add(coordinate)
            if row["meanVIR"].strip().lower() in {"", "na", "nan"}:
                continue
            valid_response_rows += 1
            for field in FIELDS:
                grouped[coordinate][field].append(float(row[field]))

    cells: list[dict[str, float | int | str]] = []
    for index, ((x, y), values) in enumerate(sorted(grouped.items()), start=1):
        latitude, longitude = utm18_to_wgs84(x, y)
        cells.append(
            {
                "id": f"c3b-{index:05d}",
                "latitude": rounded(latitude, 5),
                "longitude": rounded(longitude, 5),
                "utm18_x": rounded(x, 1),
                "utm18_y": rounded(y, 1),
                "source_cell_count": len(values["meanVIR"]),
                "mean_vir": rounded(median(values["meanVIR"]), 4),
                "alan_ratio": rounded(median(values["ALAN"]), 5),
                "distance_bright_km": rounded(median(values["dBrL"]), 2),
                "distance_radar_km": rounded(median(values["dRdr"]), 2),
                "distance_atlantic_km": rounded(median(values["dAtl"]), 1),
                "deciduous_cover": rounded(median(values["decForestCover"]), 4),
                "developed_cover": rounded(median(values["devLandCover"]), 4),
            }
        )

    sorted_density = sorted(float(cell["mean_vir"]) for cell in cells)
    for cell in cells:
        cell["density_percentile"] = rounded(
            rank_fraction(sorted_density, float(cell["mean_vir"])), 5
        )
        cell["regional_proximity"] = rounded(
            1 - min(float(cell["distance_bright_km"]), 250.0) / 250.0, 5
        )
        cell["local_brightness"] = rounded(
            math.log1p(float(cell["alan_ratio"])) / math.log1p(18.933), 5
        )

    bands = band_summary(
        cells, "distance_bright_km", [0, 5, 25, 50, 100, 150, 200, 261]
    ) + band_summary(cells, "alan_ratio", [0, 0.01, 0.1, 0.5, 1, 2, 5, 19.1])

    unique_valid_coordinates = len(cells)
    collision_groups = sum(
        1 for values in grouped.values() if len(values["meanVIR"]) > 1
    )
    quality = {
        "source": str(RAW.relative_to(ROOT)),
        "row_count": row_count,
        "column_count": 14,
        "valid_response_rows": valid_response_rows,
        "missing_mean_vir_rows": row_count - valid_response_rows,
        "missing_mean_vir_rate": rounded((row_count - valid_response_rows) / row_count, 6),
        "exact_duplicate_rows": exact_duplicate_rows,
        "unique_displayed_coordinates_all_rows": len(all_coordinates),
        "unique_displayed_coordinates_valid_response": unique_valid_coordinates,
        "valid_coordinate_collision_groups": collision_groups,
        "maximum_source_cells_per_display_coordinate": max(
            len(values["meanVIR"]) for values in grouped.values()
        ),
        "coordinate_precision_note": (
            "The study used 1 x 1 km cells, but the supplied CSV text rounds UTM Y "
            "to 10 km increments and collapses many source cells onto one displayed "
            "coordinate. The globe therefore maps medians at approximate display "
            "coordinates, not reconstructed 1 km cell centers."
        ),
        "valid_response_ranges": {
            "mean_vir": [rounded(min(sorted_density), 4), rounded(max(sorted_density), 4)],
            "latitude": [
                rounded(min(float(cell["latitude"]) for cell in cells), 5),
                rounded(max(float(cell["latitude"]) for cell in cells), 5),
            ],
            "longitude": [
                rounded(min(float(cell["longitude"]) for cell in cells), 5),
                rounded(max(float(cell["longitude"]) for cell in cells), 5),
            ],
        },
    }

    meta = {
        "title": "Measured migration response to artificial light at night",
        "evidence_type": "Community-level weather-radar stopover-density proxy",
        "study_period": "Autumn migration, 2008–2014",
        "autumn_seasons": 7,
        "radar_stations": 16,
        "screened_nights": 1491,
        "source_grid_cells": row_count,
        "model_cells_with_response": valid_response_rows,
        "display_coordinates": unique_valid_coordinates,
        "source_grid_km": 1,
        "display_hex_h3_resolution": 5,
        "response_measure": (
            "Geometric mean vertically integrated reflectivity at peak exodus "
            "(cm2/ha), used as a proxy for stopover density"
        ),
        "alan_measure": (
            "2014 artificial:natural zenith sky luminance ratio, averaged within 2 km"
        ),
        "bright_source_definition": "ALAN ratio at least 5 in a 1 km source cell",
        "published_model_results": {
            "local_alan_influence_percent": 1.9,
            "distance_bright_influence_percent": 1.2,
            "combined_light_influence_percent": 3.1,
            "local_brightness_response": (
                "Modelled stopover density decreased by up to 50% as local 2 km "
                "artificial-light intensity increased."
            ),
            "regional_proximity_response": (
                "Modelled stopover density decreased by up to 70% with distance from "
                "bright sources, especially beyond 50–100 km."
            ),
            "interpretation": (
                "The two predictors describe a scale-dependent association: regional "
                "concentration nearer bright areas alongside reduced use of the most "
                "locally illuminated habitat. They are not individual trajectories or "
                "a randomized causal test."
            ),
        },
        "source_urls": {
            "paper": "https://doi.org/10.1111/ele.12902",
            "dataset": "https://doi.org/10.5061/dryad.18v5d",
        },
        "coordinate_precision_note": quality["coordinate_precision_note"],
    }

    payload = {"meta": meta, "quality": quality, "bands": bands, "cells": cells}

    OUT.mkdir(parents=True, exist_ok=True)
    CLIENT.parent.mkdir(parents=True, exist_ok=True)
    with (OUT / "c3b_response_cells.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cells[0].keys()))
        writer.writeheader()
        writer.writerows(cells)
    with (OUT / "c3b_raw_band_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(bands[0].keys()))
        writer.writeheader()
        writer.writerows(bands)
    (OUT / "c3b_quality_summary.json").write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf-8"
    )
    client_text = json.dumps(payload, separators=(",", ":")) + "\n"
    CLIENT.write_text(client_text, encoding="utf-8")
    (OUT / "c3b_response.json").write_text(client_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "raw_rows": row_count,
                "valid_response_rows": valid_response_rows,
                "display_coordinates": unique_valid_coordinates,
                "coordinate_collision_groups": collision_groups,
                "client_bytes": CLIENT.stat().st_size,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
