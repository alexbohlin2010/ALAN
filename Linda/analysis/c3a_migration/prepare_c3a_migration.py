#!/usr/bin/env python3
"""Prepare C3A Movebank migration tracks for the Earth After Dark globe.

This pipeline intentionally keeps the two source datasets as separate adapters.
It samples the red channel of the existing 2024 globe tiles as a monotonic,
0–1 *display brightness* proxy.  That value is not physical VIIRS radiance and
must never be labelled nW/cm²/sr.
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

from PIL import Image


REPO = Path(__file__).resolve().parents[3]
MOVEBANK = REPO / "Linda/data/movebank"
OUTPUT_DIR = REPO / "Linda/processed/c3a_migration"
CLIENT_JSON = REPO / "Alexander/globe_v2/data/c3a_migration.json"
TILE_ROOT = REPO / "Alexander/globe_v2/tiles_rgba/2024"

WHIP_EVENTS = MOVEBANK / "whip poor will/GPS tracking of eastern whip-poor-will.csv"
WHIP_REFERENCE = MOVEBANK / "whip poor will/GPS tracking of eastern whip-poor-will-reference-data.csv"
ROBIN_GPS = MOVEBANK / "robins/ABoVE_ Boelman Alberta American Robins.csv"
ROBIN_ARGOS = MOVEBANK / "robins/ABoVE_ Boelman Alberta American Robins (1).csv"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
TILE_ZOOM = 9
GPS_SPEED_LIMIT_KMH = 120.0
ARGOS_SPEED_LIMIT_KMH = 180.0
ROBIN_GPS_PREFERENCE_HOURS = 6.0

# Source-defined migration and stopover states. Breeding, wintering, daytime
# roost, uncertain-transition, LFW, and owner-marked removal records are not
# silently promoted to migration observations.
WHIP_MIGRATION_PHASES = {
    "FM": "fall migration",
    "Stop1": "fall stopover",
    "Stop2": "fall stopover",
    "SM": "spring migration",
    "SM.stop1": "spring stopover",
    "SM.stop2": "spring stopover",
    "Arr": "spring arrival",
}


@dataclass(frozen=True)
class Adapter:
    dataset_id: str
    common_name: str
    scientific_name: str
    sensor_type: str
    gap_hours: float
    speed_limit_kmh: float


WHIP_ADAPTER = Adapter(
    "eastern_whip_poor_will",
    "Eastern Whip-poor-will",
    "Antrostomus vociferus",
    "GPS",
    14 * 24,
    GPS_SPEED_LIMIT_KMH,
)
ROBIN_GPS_ADAPTER = Adapter(
    "american_robin_gps",
    "American Robin",
    "Turdus migratorius",
    "GPS",
    10 * 24,
    GPS_SPEED_LIMIT_KMH,
)
ROBIN_ARGOS_ADAPTER = Adapter(
    "american_robin_argos",
    "American Robin",
    "Turdus migratorius",
    "Argos",
    24,
    ARGOS_SPEED_LIMIT_KMH,
)


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, TIMESTAMP_FORMAT)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() == "true"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def haversine_km(a: dict, b: dict) -> float:
    radius = 6371.0088
    lat1, lat2 = math.radians(a["latitude"]), math.radians(b["latitude"])
    dlat = lat2 - lat1
    dlng = math.radians(b["longitude"] - a["longitude"])
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(value)))


def elapsed_hours(a: dict, b: dict) -> float:
    return (b["_time"] - a["_time"]).total_seconds() / 3600


def speed_kmh(a: dict, b: dict) -> float:
    hours = elapsed_hours(a, b)
    return haversine_km(a, b) / hours if hours > 0 else math.inf


def base_row(raw: dict[str, str], adapter: Adapter) -> dict:
    timestamp = parse_timestamp(raw["timestamp"])
    return {
        "dataset_id": adapter.dataset_id,
        "species": adapter.common_name,
        "scientific_name": adapter.scientific_name,
        "individual_id": raw["individual-local-identifier"].strip(),
        "timestamp": raw["timestamp"],
        "year": timestamp.year,
        "latitude": float(raw["location-lat"]),
        "longitude": float(raw["location-long"]),
        "sensor_type": adapter.sensor_type,
        "spatial_precision": "fine-scale GPS" if adapter.sensor_type == "GPS" else "lower-precision Argos",
        "event_id": raw.get("event-id", ""),
        "tag_id": raw.get("tag-local-identifier", ""),
        "study_name": raw.get("study-name", ""),
        "_time": timestamp,
        "_adapter": adapter,
    }


def exclusion_reason(raw: dict[str, str]) -> str | None:
    try:
        latitude = float(raw["location-lat"])
        longitude = float(raw["location-long"])
    except (TypeError, ValueError, KeyError):
        return "missing_or_invalid_coordinate"
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return "coordinate_out_of_range"
    if not raw.get("timestamp"):
        return "missing_timestamp"
    if str(raw.get("visible", "true")).strip().lower() == "false":
        return "movebank_not_visible"
    if truthy(raw.get("algorithm-marked-outlier")) or truthy(raw.get("manually-marked-outlier")):
        return "source_marked_outlier"
    return None


def load_whip_poor_will() -> tuple[list[dict], Counter]:
    reference = {row["deployment-id"]: row for row in read_csv(WHIP_REFERENCE)}
    # The event file has tag and animal identifiers, while reference deployment
    # IDs are animal_tag. Use that deterministic key to retain deployment fields.
    reference_by_pair = {
        (row["animal-id"], row["tag-id"]): row for row in reference.values()
    }
    kept: list[dict] = []
    exclusions: Counter = Counter()
    for raw in read_csv(WHIP_EVENTS):
        reason = exclusion_reason(raw)
        if reason:
            exclusions[reason] += 1
            continue
        source_phase = raw.get("behavioural-classification", "")
        if source_phase not in WHIP_MIGRATION_PHASES:
            exclusions["not_source_classified_migration"] += 1
            continue
        row = base_row(raw, WHIP_ADAPTER)
        meta = reference_by_pair.get((row["individual_id"], row["tag_id"]), {})
        row.update({
            "source_phase": source_phase,
            "movement_phase": WHIP_MIGRATION_PHASES[source_phase],
            "deployment_id": meta.get("deployment-id", ""),
            "deploy_on_date": meta.get("deploy-on-date", ""),
            "deploy_off_date": meta.get("deploy-off-date", ""),
            "study_site": meta.get("study-site", ""),
            "animal_sex": meta.get("animal-sex", ""),
            "deployment_comments": meta.get("deployment-comments", ""),
        })
        kept.append(row)
    return kept, exclusions


def load_robin(path: Path, adapter: Adapter) -> tuple[list[dict], Counter]:
    kept: list[dict] = []
    exclusions: Counter = Counter()
    for raw in read_csv(path):
        reason = exclusion_reason(raw)
        if reason:
            exclusions[reason] += 1
            continue
        row = base_row(raw, adapter)
        row.update({
            "source_phase": "",
            "movement_phase": "tracked movement",
            "deployment_id": "",
            "deploy_on_date": "",
            "deploy_off_date": "",
            "study_site": "",
            "animal_sex": "",
            "deployment_comments": "",
            "argos_location_class": raw.get("argos:lc", "") if adapter.sensor_type == "Argos" else "",
        })
        kept.append(row)
    return kept, exclusions


def deduplicate(rows: list[dict], exclusions: Counter) -> list[dict]:
    output: list[dict] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in sorted(rows, key=lambda item: (item["individual_id"], item["_time"], item["event_id"])):
        key = (row["dataset_id"], row["individual_id"], row["timestamp"], row["sensor_type"])
        if key in seen:
            exclusions["duplicate_individual_timestamp_sensor"] += 1
            continue
        seen.add(key)
        output.append(row)
    return output


def remove_speed_spikes(rows: list[dict], exclusions: Counter) -> list[dict]:
    by_track: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        by_track[(row["dataset_id"], row["individual_id"])].append(row)
    output: list[dict] = []
    for track in by_track.values():
        track.sort(key=lambda item: item["_time"])
        keep = [True] * len(track)
        for index in range(1, len(track) - 1):
            previous, current, following = track[index - 1:index + 2]
            limit = current["_adapter"].speed_limit_kmh
            incoming = speed_kmh(previous, current)
            outgoing = speed_kmh(current, following)
            bypass = speed_kmh(previous, following)
            # A point that creates an impossible incoming *or* outgoing step,
            # while its two neighbours form a plausible direct step, is a
            # spatial spike even when a long gap makes the other leg's average
            # speed look superficially plausible.
            if (incoming > limit or outgoing > limit) and bypass <= limit:
                keep[index] = False
                exclusions["biologically_impossible_speed_spike"] += 1
        output.extend(row for row, valid in zip(track, keep) if valid)
    return output


def prefer_robin_gps(gps: list[dict], argos: list[dict], exclusions: Counter) -> list[dict]:
    gps_times: defaultdict[str, list[datetime]] = defaultdict(list)
    for row in gps:
        gps_times[row["individual_id"]].append(row["_time"])
    limit_seconds = ROBIN_GPS_PREFERENCE_HOURS * 3600
    kept: list[dict] = []
    for row in argos:
        candidates = gps_times.get(row["individual_id"], [])
        if candidates and min(abs((row["_time"] - value).total_seconds()) for value in candidates) <= limit_seconds:
            exclusions["argos_near_gps_preferred_gps"] += 1
        else:
            kept.append(row)
    return kept


class TileSampler:
    def __init__(self, root: Path, zoom: int):
        self.root = root
        self.zoom = zoom
        self.cache: dict[tuple[int, int], Image.Image | None] = {}
        self.missing_tile_points = 0

    def sample(self, latitude: float, longitude: float) -> float:
        n = 2 ** self.zoom
        lat = max(-85.05112878, min(85.05112878, latitude))
        x_float = (longitude + 180) / 360 * n
        y_float = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
        tile_x = max(0, min(n - 1, int(x_float)))
        tile_y = max(0, min(n - 1, int(y_float)))
        key = (tile_x, tile_y)
        if key not in self.cache:
            path = self.root / str(self.zoom) / str(tile_x) / f"{tile_y}.webp"
            self.cache[key] = Image.open(path).convert("RGBA") if path.exists() else None
        image = self.cache[key]
        if image is None:
            self.missing_tile_points += 1
            return 0.0
        pixel_x = max(0, min(255, int((x_float - tile_x) * 256)))
        pixel_y = max(0, min(255, int((y_float - tile_y) * 256)))
        red = image.getpixel((pixel_x, pixel_y))[0]
        return round(red / 255, 6)


def percentile(values: Iterable[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def assign_segments(rows: list[dict]) -> None:
    by_track: defaultdict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        # Whip-poor-will fall and spring routes must not be joined to each other.
        phase_family = "fall" if row["movement_phase"].startswith("fall") else "spring" if row["movement_phase"].startswith("spring") else "tracked"
        by_track[(row["dataset_id"], row["individual_id"], phase_family)].append(row)
    segment_counter = 0
    for key, track in sorted(by_track.items()):
        track.sort(key=lambda item: item["_time"])
        segment_counter += 1
        segment_id = f"{key[0]}:{key[1]}:{key[2]}:{segment_counter}"
        previous = None
        for row in track:
            break_reason = "track_start"
            if previous is not None:
                gap = elapsed_hours(previous, row)
                movement_speed = speed_kmh(previous, row)
                if gap > row["_adapter"].gap_hours:
                    segment_counter += 1
                    segment_id = f"{key[0]}:{key[1]}:{key[2]}:{segment_counter}"
                    break_reason = "large_time_gap"
                elif movement_speed > row["_adapter"].speed_limit_kmh:
                    segment_counter += 1
                    segment_id = f"{key[0]}:{key[1]}:{key[2]}:{segment_counter}"
                    break_reason = "impossible_speed_break"
                else:
                    break_reason = "continuous"
                row["hours_from_previous"] = round(gap, 3)
                row["speed_from_previous_kmh"] = round(movement_speed, 3)
            else:
                row["hours_from_previous"] = None
                row["speed_from_previous_kmh"] = None
            row["segment_id"] = segment_id
            row["segment_break_reason"] = break_reason
            previous = row


def summarise(rows: list[dict], threshold: float) -> tuple[list[dict], list[dict]]:
    def summary(group: list[dict], species: str, individual_id: str | None = None) -> dict:
        values = [row["viirs_relative_brightness"] for row in group]
        elevated = [value >= threshold and value > 0 for value in values]
        distances = []
        by_segment: defaultdict[str, list[dict]] = defaultdict(list)
        for row in group:
            by_segment[row["segment_id"]].append(row)
        for segment in by_segment.values():
            segment.sort(key=lambda item: item["_time"])
            distances.extend(haversine_km(a, b) for a, b in zip(segment, segment[1:]))
        result = {
            "species": species,
            "point_count": len(group),
            "individual_count": len({row["individual_id"] for row in group}),
            "segment_count": len(by_segment),
            "first_timestamp": min(row["timestamp"] for row in group),
            "last_timestamp": max(row["timestamp"] for row in group),
            "sensor_types": sorted({row["sensor_type"] for row in group}),
            "median_relative_brightness": round(statistics.median(values), 6),
            "maximum_relative_brightness": round(max(values), 6),
            "high_brightness_point_count": sum(elevated),
            "high_brightness_point_proportion": round(sum(elevated) / len(group), 6),
            "connected_distance_km": round(sum(distances), 1),
        }
        if individual_id is not None:
            result["individual_id"] = individual_id
        return result

    species_groups: defaultdict[str, list[dict]] = defaultdict(list)
    individual_groups: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        species_groups[row["species"]].append(row)
        individual_groups[(row["species"], row["individual_id"])].append(row)
    species_summary = [summary(group, species) for species, group in sorted(species_groups.items())]
    individual_summary = [summary(group, species, individual) for (species, individual), group in sorted(individual_groups.items())]
    return species_summary, individual_summary


def public_row(row: dict) -> dict:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    for path in [WHIP_EVENTS, WHIP_REFERENCE, ROBIN_GPS, ROBIN_ARGOS]:
        if not path.exists():
            raise FileNotFoundError(path)
    if not TILE_ROOT.exists():
        raise FileNotFoundError(TILE_ROOT)

    whip, whip_exclusions = load_whip_poor_will()
    robin_gps, robin_gps_exclusions = load_robin(ROBIN_GPS, ROBIN_GPS_ADAPTER)
    robin_argos, robin_argos_exclusions = load_robin(ROBIN_ARGOS, ROBIN_ARGOS_ADAPTER)

    whip = remove_speed_spikes(deduplicate(whip, whip_exclusions), whip_exclusions)
    robin_gps = remove_speed_spikes(deduplicate(robin_gps, robin_gps_exclusions), robin_gps_exclusions)
    robin_argos = remove_speed_spikes(deduplicate(robin_argos, robin_argos_exclusions), robin_argos_exclusions)
    robin_argos = prefer_robin_gps(robin_gps, robin_argos, robin_argos_exclusions)

    rows = whip + robin_gps + robin_argos
    assign_segments(rows)

    sampler = TileSampler(TILE_ROOT, TILE_ZOOM)
    for index, row in enumerate(sorted(rows, key=lambda item: (item["species"], item["individual_id"], item["_time"]))):
        row["point_id"] = f"c3a-{index + 1:05d}"
        row["viirs_relative_brightness"] = sampler.sample(row["latitude"], row["longitude"])

    nonzero = [row["viirs_relative_brightness"] for row in rows if row["viirs_relative_brightness"] > 0]
    threshold = round(percentile(nonzero, 0.90), 6)
    for row in rows:
        value = row["viirs_relative_brightness"]
        row["high_relative_brightness"] = bool(value >= threshold and value > 0)

    species_summary, individual_summary = summarise(rows, threshold)
    segments = Counter(row["segment_id"] for row in rows)
    usable_segments = sum(count >= 2 for count in segments.values())
    singleton_segments = sum(count == 1 for count in segments.values())
    quality = {
        "source_rows": {
            "eastern_whip_poor_will": len(read_csv(WHIP_EVENTS)),
            "american_robin_gps": len(read_csv(ROBIN_GPS)),
            "american_robin_argos": len(read_csv(ROBIN_ARGOS)),
        },
        "retained_rows": {
            "eastern_whip_poor_will": len(whip),
            "american_robin_gps": len(robin_gps),
            "american_robin_argos": len(robin_argos),
        },
        "exclusions": {
            "eastern_whip_poor_will": dict(sorted(whip_exclusions.items())),
            "american_robin_gps": dict(sorted(robin_gps_exclusions.items())),
            "american_robin_argos": dict(sorted(robin_argos_exclusions.items())),
        },
        "route_segments_with_two_or_more_points": usable_segments,
        "singleton_segments_not_drawn_as_lines": singleton_segments,
        "points_in_omitted_dark_tiles": sampler.missing_tile_points,
    }

    metadata = {
        "title": "C3A — Migration Through Artificial Night",
        "point_count": len(rows),
        "individual_count": len({(row["species"], row["individual_id"]) for row in rows}),
        "species_count": len(species_summary),
        "segment_count": usable_segments,
        "sensor_counts": dict(sorted(Counter(row["sensor_type"] for row in rows).items())),
        "date_start": min(row["timestamp"] for row in rows),
        "date_end": max(row["timestamp"] for row in rows),
        "viirs_context_year": 2024,
        "brightness_field": "viirs_relative_brightness",
        "brightness_definition": "Red-channel display intensity sampled from the existing 2024 VIIRS globe tile at zoom 9, divided by 255. It is a monotonic visual proxy, not physical radiance.",
        "high_brightness_threshold": threshold,
        "high_brightness_threshold_method": "90th percentile of non-zero relative display brightness across all retained migration points; zero/dark points remain in each proportion denominator.",
        "gps_argos_rule": f"Robin Argos points within {ROBIN_GPS_PREFERENCE_HOURS:g} hours of a GPS point for the same individual are excluded in favour of GPS.",
        "gap_rules": {
            "Eastern Whip-poor-will GPS": "break after 14 days",
            "American Robin GPS": "break after 10 days",
            "American Robin Argos": "break after 24 hours",
        },
        "interpretation": "Shows where tracked birds passed through darker and brighter 2024 nighttime environments. It does not test whether artificial light caused route choice or movement change.",
    }

    public_rows = [public_row(row) for row in sorted(rows, key=lambda item: item["point_id"])]
    payload = {
        "meta": metadata,
        "species": species_summary,
        "individuals": individual_summary,
        "quality": quality,
        "points": public_rows,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CLIENT_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_DIR / "c3a_tracking_points.csv", public_rows)
    write_csv(OUTPUT_DIR / "c3a_individual_summary.csv", individual_summary)
    (OUTPUT_DIR / "c3a_quality_summary.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    CLIENT_JSON.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    print(json.dumps({"meta": metadata, "species": species_summary, "quality": quality}, indent=2))


if __name__ == "__main__":
    main()
