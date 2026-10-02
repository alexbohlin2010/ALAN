#!/usr/bin/env python3
"""Build an auditable location-resolution table for the C1 meta-analysis.

The workbook contains free-text study locations rather than latitude/longitude.
This script resolves each distinct source string once, preserves the original
text, records the geocoder candidate and its bounding box, and separates
point-eligible places from country/region context. It does not silently turn a
country or broad region into an exact study point.
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

import certifi
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_XLSX = (
    REPO_ROOT
    / "Linda"
    / "data"
    / "spectrum-specific impacts of light pollution on biota"
    / "Data_S1_Czarnecka_et_al..xlsx"
)
OUTPUT_DIR = REPO_ROOT / "Linda" / "processed" / "c1_effects"
CACHE_PATH = OUTPUT_DIR / "c1_location_geocode_cache.json"
OUTPUT_CSV = OUTPUT_DIR / "c1_location_resolution.csv"
SUMMARY_PATH = OUTPUT_DIR / "c1_location_resolution_summary.json"
REVIEW_PATH = OUTPUT_DIR / "c1_location_review_needed.csv"

USER_AGENT = "ALAN-C1-location-audit/1.0 (academic data visualization)"
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"


QUERY_OVERRIDES = {
    "Arcachon Bay, France": "Arcachon, Gironde, France",
    "Abruzzo, Lazio and Molise National Park, Italy": "Pescasseroli, Italy",
    "Brasil": "Brazil",
    "British columbia": "British Columbia, Canada",
    "Cable Bay, UK": "Cable Bay, Anglesey, United Kingdom",
    "California`s Gump Research Station": "Gump Station, Moorea, French Polynesia",
    "Columbia River, USA": "Columbia River, United States",
    "Columbus Metropolitan Area, US": "Columbus, Ohio, United States",
    "Eliat Red Sea": "Eilat, Israel",
    "Fangshan National Geology Park, Nanjing, China": "Jiangning District, Nanjing, China",
    "Gulf of Aquaba/Eilat Red Sea, Israel": "Eilat, Israel",
    "Gulf of Eliat": "Eilat, Israel",
    "Gulf of Eilat, Red Sea": "Eilat, Israel",
    "Gulf of Eljat, Israel": "Eilat, Israel",
    "Great Mazurian Lakes, Poland": "Masurian Lake District, Poland",
    "Henan Academy, China": "Henan Academy of Agricultural Sciences, Zhengzhou, China",
    "Hong kong,": "Hong Kong",
    "Hertfordshire, southeast England": "Hertfordshire, England, United Kingdom",
    "IGB Berlin": "Mueggelseedamm 310, Berlin, Germany",
    "Kentucky University, USA": "University of Kentucky, Lexington, Kentucky, USA",
    "Kinki University": "Kindai University, Higashiosaka, Japan",
    "Lizard penisula": "The Lizard National Nature Reserve, Cornwall, United Kingdom",
    "Mebourne, Australia": "Melbourne, Australia",
    "North Somerset, southwest Britain": "North Somerset, England, United Kingdom",
    "Phillipines": "Philippines",
    "Piedmont": "Piedmont, Maryland, USA",
    "Potsdam, Eastern Germany": "Potsdam, Germany",
    "Prealps, Switzerland": "Swiss Alps, Switzerland",
    "Prince Edward Island, Atlantic Canada": "Prince Edward Island, Canada",
    "Ridea River, Ontario": "Rideau River, Ontario, Canada",
    "Regional Natural Park of Gatinais, France": "Parc naturel regional du Gatinais francais, France",
    "Ross Natural History Reservation": "Americus, Kansas, USA",
    "Rowardennan, Stirlingshire, U.K.": "Rowardennan, Scotland, United Kingdom",
    "San Antonio Oeste Bay": "San Antonio Oeste, Rio Negro, Argentina",
    "Seewiesen, South Germany": "Seewiesen, Pocking, Bavaria, Germany",
    "Sundial Bridge, Sacramento River": "Sundial Bridge, Redding, California, USA",
    "Tagus Esturay, Portugal": "Tagus Estuary, Portugal",
    "The Netherlands Institute of Ecology": "NIOO-KNAW, Wageningen, Netherlands",
    "University of Exeter, UK": "University of Exeter, Exeter, United Kingdom",
    "University of Exeter Penryn Campus": "Penryn Campus, Cornwall, United Kingdom",
    "University of Lyon, France": "Universite de Lyon, France",
    "University of Wisconsin": "University of Wisconsin-Madison, Wisconsin, USA",
    "University of Wisconsin Arlington Agricultural Research Station in Arlington": "Arlington Agricultural Research Station, Wisconsin, USA",
    "Wagenigen, Netherlands": "Wageningen, Netherlands",
    "Wainfleet bag, Ontario, Candada": "Wainfleet Bog Conservation Reserve, Ontario, Canada",
    "Westhavelland Nature Park": "Naturpark Westhavelland, Brandenburg, Germany",
    "Westhavelland Nature Park, Germany": "Naturpark Westhavelland, Brandenburg, Germany",
    "Westhavelland Nature Park, Brandenburg, Germany (52ĺÁ69? N, 12ĺÁ46? E).": "Naturpark Westhavelland, Brandenburg, Germany",
    "north-central Chile": "Chile",
    "eastern France": "France",
    "southern England": "England, United Kingdom",
    "southern England, UK": "England, United Kingdom",
    "southern Sweden": "Sweden",
    "south?west England and Wales between July and September 2014": "United Kingdom",
}


COUNTRY_ALIASES = {
    "Argentina", "Australia", "Bahamas", "Belgium", "Brasil", "Canada",
    "Chile", "China", "Costa Rica", "France", "French Polynesia", "Germany",
    "India", "Ireland", "Israel", "Italy", "Japan", "Korea", "Netherlands",
    "New Zealand", "Norway", "Phillipines", "Portugal", "Slovakia",
    "South Africa", "Spain", "Sweden", "Switzerland", "UK", "USA",
}

INSTITUTION_TERMS = (
    "university", "academy", "institute", "research station", "campus", "igb ",
)
NAMED_AREA_TERMS = (
    "bay", "river", "lake", "strait", "gulf", "estuary", "park", "reserve",
    "sanctuary", "lakes", "desert", "peninsula", "prealps", "bridge",
    "bog", "island", "moorea", "cornwall", "piedmont",
)
REGION_TERMS = (
    "northern ", "southern ", "eastern ", "western ", "north-central ",
    "southwest ", "southeast ", "county", "province", "prefecture", "state", "metropolitan area",
    "virginia", "california", "ohio", "nevada", "florida", "new jersey",
    "hampshire", "victoria", "brandenburg", "sussex", "yorkshire",
    "scotland", "england", "manitoba", "british columbia", "uttar pradesh",
)

APPROVED_POINT_LOCATIONS = {
    "Berlin, Germany", "Henan Academy, China", "Kentucky University, USA",
    "Technical University of Munich, Germany", "Mizoram University, Aizawl",
    "Ohio State University", "Torun, Poland", "Wageningen", "La Spezia, Italy",
    "Munich, Germany", "Sydney, Australia", "San Antonio, Texas, US",
    "University of Wisconsin", "Wagenigen, Netherlands", "Ithaca, US",
    "Strasbourg, France", "Konstanz, Germany", "Lowestoft, UK",
    "Monteverde, Costa Rica", "Vienna, Austria", "Wageningen, Netherlands",
    "Cleveland, USA", "University of Virginia", "Hong kong,", "Glasgow, UK",
    "Kinki University", "Seewiesen, South Germany", "University of Antwerp, Belgium",
    "University of Wisconsin Arlington Agricultural Research Station in Arlington",
    "Wallingford, Oxfordshire, UK", "Mebourne, Australia", "Miami, USA", "Reno, NV",
    "Saint Louis, USA",
}

MANUAL_RESOLUTIONS = {
    "Lebretshoeve, Radio Kootwijk and Klaterweg, Netherlands": {
        "display_name": "Lebretshoeve, Radio Kootwijk and Klaterweg, Gelderland, Netherlands",
        "lat": 52.2196885,
        "lon": 5.8673235,
        "boundingbox": [52.0968054, 52.3859590, 5.8286861, 5.9387521],
        "address": {"country": "Netherlands", "country_code": "nl"},
        "category": "study_sites",
        "type": "multiple_named_sites",
        "addresstype": "study_sites",
        "precision": "multiple_named_sites",
        "geometry_type": "multi_point",
        "coordinates": [
            {"label": "Lebretshoeve", "lat": 52.0968751, "lng": 5.9385261},
            {"label": "Radio Kootwijk", "lat": 52.1770547, "lng": 5.8335719},
            {"label": "Klaterweg", "lat": 52.3851357, "lng": 5.8298724},
        ],
        "confidence": "medium",
        "review_status": "reviewed_named_multi_site",
        "point_eligible": False,
        "resolution_source": "OpenStreetMap Nominatim candidates for the three named sites",
        "notes": "Three named locations resolved separately; retain as a multi-site area until the source paper confirms the exact sampling coordinates.",
    },
    "Libreville, Oregon, USA": {
        "display_name": "Boeckman Road Extension study site, Wilsonville, Oregon, USA",
        "lat": 45.316245,
        "lon": -122.783933,
        "boundingbox": [45.316245, 45.316245, -122.783933, -122.783933],
        "address": {"country": "United States", "country_code": "us"},
        "category": "study_site",
        "type": "source_paper_coordinates",
        "addresstype": "study_site",
        "confidence": "high",
        "review_status": "verified_from_source_paper",
        "point_eligible": True,
        "resolution_source": "Source paper site description, DOI 10.1016/j.biocon.2016.04.025",
        "notes": "Workbook label is incorrect; source paper gives Wilsonville coordinates 45.316245, -122.783933.",
    },
    "Wainfleet bag, Ontario, Candada": {
        "display_name": "Wainfleet Bog Conservation Reserve, Ontario, Canada",
        "lat": 42.924179,
        "lon": -79.280837,
        "boundingbox": [42.90, 42.95, -79.31, -79.25],
        "address": {"country": "Canada", "country_code": "ca"},
        "category": "protected_area",
        "type": "conservation_reserve",
        "addresstype": "protected_area",
        "confidence": "high",
        "review_status": "verified_official_place_name",
        "point_eligible": False,
        "resolution_source": "Canadian Geographical Names Database, place FEVQD",
        "notes": "Corrected source spelling; render as a protected-area region rather than an exact experimental point.",
    },
}

EXPLICIT_MULTI_SITE = (
    "Seewiesen (southern Germany) four sites (site 1: coordinates 47,96928ĺÁN, 11,2357ĺÁE; "
    "site 2: 47,9708ĺÁN, 11,2385ĺÁE; site 3: 47,97235ĺÁN, 11,2363ĺÁE; "
    "site 4: 47,9730ĺÁN, 11,2325ĺÁE"
)
EXPLICIT_MULTI_SITE_POINTS = [
    {"lat": 47.96928, "lng": 11.2357},
    {"lat": 47.9708, "lng": 11.2385},
    {"lat": 47.97235, "lng": 11.2363},
    {"lat": 47.9730, "lng": 11.2325},
]


def normalize(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def infer_precision(source_location: str, canonical_query: str) -> str:
    lower = normalize(f"{source_location} {canonical_query}")
    if source_location == EXPLICIT_MULTI_SITE:
        return "multiple_sites_source_coordinates"
    if source_location in COUNTRY_ALIASES:
        return "country"
    if any(term in lower for term in INSTITUTION_TERMS):
        return "institution"
    if any(term in lower for term in NAMED_AREA_TERMS):
        return "named_area"
    if any(term in lower for term in REGION_TERMS):
        return "region"
    if "," in source_location or lower in {
        "wageningen", "piedmont", "ithaca us", "torun poland", "vienna austria"
    }:
        return "city_or_locality"
    return "region_or_locality"


def expected_country_hint(query: str) -> str:
    lower = normalize(query)
    hints = {
        "united kingdom": "gb", " uk": "gb", "britain": "gb", "england": "gb",
        "scotland": "gb", "wales": "gb", " usa": "us", " united states": "us",
        "canada": "ca", "germany": "de", "netherlands": "nl", "france": "fr",
        "italy": "it", "portugal": "pt", "spain": "es", "switzerland": "ch",
        "australia": "au", "austria": "at", "belgium": "be", "poland": "pl",
        "china": "cn", "india": "in", "japan": "jp", "israel": "il",
        "argentina": "ar", "costa rica": "cr", "chile": "cl", "sweden": "se",
        "finland": "fi", "norway": "no", "new zealand": "nz", "ireland": "ie",
        "south africa": "za", "philippines": "ph", "french polynesia": "fr",
        "slovakia": "sk", "bahamas": "bs", "korea": "kr",
    }
    padded = f" {lower}"
    for term, code in hints.items():
        if term in padded:
            return code
    return ""


def load_cache() -> dict[str, list[dict]]:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, list[dict]]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def geocode(query: str, cache: dict[str, list[dict]], refresh: bool) -> list[dict]:
    if query in cache and not refresh:
        return cache[query]
    params = urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "limit": 5,
        "addressdetails": 1,
    })
    request = urllib.request.Request(
        f"{GEOCODER_URL}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept-Language": "en"},
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, context=context, timeout=30) as response:
        result = json.load(response)
    cache[query] = result
    save_cache(cache)
    time.sleep(1.05)
    return result


def choose_candidate(results: list[dict], country_hint: str) -> tuple[dict, bool]:
    if not results:
        return {}, False
    if country_hint:
        for result in results:
            code = result.get("address", {}).get("country_code", "").lower()
            if code == country_hint:
                return result, True
        return results[0], False
    return results[0], True


def geometry_for_precision(precision: str) -> str:
    if precision in {"multiple_sites_source_coordinates", "multiple_named_sites"}:
        return "multi_point"
    if precision in {"institution", "city_or_locality"}:
        return "point"
    if precision == "country":
        return "country_region"
    return "region"


def candidate_quality(
    source_location: str,
    precision: str,
    candidate: dict,
    country_matches: bool,
    query_was_overridden: bool,
) -> tuple[str, str, bool]:
    if precision == "multiple_sites_source_coordinates":
        return "high", "verified_from_source_coordinates", True
    if not candidate:
        return "unresolved", "needs_manual_resolution", False
    if not country_matches:
        return "low", "needs_manual_review_country_mismatch", False
    if precision == "country":
        candidate_type = candidate.get("addresstype") or candidate.get("type")
        if candidate_type == "country":
            return "high", "verified_auto_country", False
        return "medium", "needs_manual_review_country_geometry", False
    if source_location in APPROVED_POINT_LOCATIONS:
        return "high", "reviewed_point_candidate", True
    if precision in {"region", "region_or_locality"}:
        return "medium", "reviewed_as_broad_context", False
    if precision == "named_area":
        return "medium", "needs_manual_review_named_area", False
    if query_was_overridden:
        return "medium", "needs_manual_review_corrected_query", False
    return "medium", "needs_manual_review_geocoder_candidate", False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Refresh cached geocoder responses.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = pd.read_excel(SOURCE_XLSX)
    source["location_clean"] = source["Location"].astype("string").str.strip()
    located = source[source["location_clean"].notna()].copy()

    grouped = (
        located.groupby("location_clean", dropna=False)
        .agg(
            effect_count=("location_clean", "size"),
            study_count=("Study", "nunique"),
            field_effect_count=("Study.Type", lambda s: int(s.eq("Field").sum())),
            laboratory_effect_count=("Study.Type", lambda s: int(s.eq("Laboratory").sum())),
            study_ids=("Study", lambda s: "|".join(map(str, sorted(set(s.dropna().astype(int)))))),
        )
        .reset_index()
        .rename(columns={"location_clean": "source_location"})
        .sort_values(["effect_count", "source_location"], ascending=[False, True])
    )

    cache = load_cache()
    rows: list[dict] = []
    for record in grouped.to_dict(orient="records"):
        source_location = record["source_location"]
        query = QUERY_OVERRIDES.get(source_location, source_location)
        precision = infer_precision(source_location, query)
        geometry_type = geometry_for_precision(precision)

        manual = MANUAL_RESOLUTIONS.get(source_location)
        if manual:
            precision = manual.get("precision", precision)
            geometry_type = manual.get("geometry_type", geometry_type)
            candidate = manual
            country_matches = True
        elif precision == "multiple_sites_source_coordinates":
            lat = sum(point["lat"] for point in EXPLICIT_MULTI_SITE_POINTS) / len(EXPLICIT_MULTI_SITE_POINTS)
            lng = sum(point["lng"] for point in EXPLICIT_MULTI_SITE_POINTS) / len(EXPLICIT_MULTI_SITE_POINTS)
            candidate = {
                "display_name": "Seewiesen, Bavaria, Germany — four source-listed sites",
                "lat": lat,
                "lon": lng,
                "boundingbox": [
                    min(point["lat"] for point in EXPLICIT_MULTI_SITE_POINTS),
                    max(point["lat"] for point in EXPLICIT_MULTI_SITE_POINTS),
                    min(point["lng"] for point in EXPLICIT_MULTI_SITE_POINTS),
                    max(point["lng"] for point in EXPLICIT_MULTI_SITE_POINTS),
                ],
                "address": {"country": "Germany", "country_code": "de"},
                "category": "source_coordinates",
                "type": "study_sites",
                "addresstype": "study_sites",
            }
            country_matches = True
        else:
            results = geocode(query, cache, args.refresh)
            candidate, country_matches = choose_candidate(results, expected_country_hint(query))

        confidence, review_status, point_eligible = candidate_quality(
            source_location,
            precision,
            candidate,
            country_matches,
            source_location in QUERY_OVERRIDES,
        )
        bbox = candidate.get("boundingbox", [None, None, None, None]) if candidate else [None] * 4
        address = candidate.get("address", {}) if candidate else {}
        lat = candidate.get("lat") if candidate else None
        lng = candidate.get("lon") if candidate else None

        notes = []
        if source_location in QUERY_OVERRIDES:
            notes.append("query normalized/corrected; preserve source text")
        if precision == "country":
            notes.append("country-level context only; do not render as an exact study point")
        elif geometry_type == "region":
            notes.append("broad or areal location; render as uncertainty/region context")
        if not candidate:
            notes.append("no geocoder candidate")
        if candidate and not country_matches:
            notes.append("candidate country does not match query hint")
        if manual:
            confidence = manual["confidence"]
            review_status = manual["review_status"]
            point_eligible = manual["point_eligible"]
            notes.append(manual["notes"])

        row = {
            **record,
            "canonical_query": query,
            "candidate_label": candidate.get("display_name") if candidate else None,
            "geometry_type": geometry_type,
            "precision": precision,
            "latitude": float(lat) if lat is not None else None,
            "longitude": float(lng) if lng is not None else None,
            "bbox_south": float(bbox[0]) if bbox[0] is not None else None,
            "bbox_north": float(bbox[1]) if bbox[1] is not None else None,
            "bbox_west": float(bbox[2]) if bbox[2] is not None else None,
            "bbox_east": float(bbox[3]) if bbox[3] is not None else None,
            "country": address.get("country"),
            "country_code": address.get("country_code"),
            "geocoder_category": candidate.get("category") if candidate else None,
            "geocoder_type": candidate.get("type") if candidate else None,
            "geocoder_place_id": candidate.get("place_id") if candidate else None,
            "confidence": confidence,
            "review_status": review_status,
            "point_eligible": bool(point_eligible),
            "multi_site_coordinates_json": json.dumps(
                manual.get("coordinates", EXPLICIT_MULTI_SITE_POINTS)
                if manual else EXPLICIT_MULTI_SITE_POINTS,
                separators=(",", ":"),
            ) if precision in {"multiple_sites_source_coordinates", "multiple_named_sites"} else None,
            "notes": "; ".join(notes),
            "resolution_source": (
                manual["resolution_source"]
                if manual
                else "source_workbook_coordinates"
                if precision == "multiple_sites_source_coordinates"
                else "OpenStreetMap Nominatim candidate"
            ),
        }
        rows.append(row)

    resolution = pd.DataFrame(rows)
    resolution.to_csv(OUTPUT_CSV, index=False)
    resolution.loc[resolution["review_status"].str.startswith("needs_")].to_csv(REVIEW_PATH, index=False)

    total_effects = int(len(source))
    located_effects = int(located.shape[0])
    missing_effects = total_effects - located_effects
    summary = {
        "source_file": SOURCE_XLSX.name,
        "effect_count": total_effects,
        "effect_records_with_location": located_effects,
        "effect_records_without_location": missing_effects,
        "location_coverage_percent": round(located_effects / total_effects * 100, 2),
        "unique_source_locations": int(len(resolution)),
        "resolved_candidate_locations": int(resolution["latitude"].notna().sum()),
        "unresolved_locations": int(resolution["latitude"].isna().sum()),
        "country_context_locations": int(resolution["precision"].eq("country").sum()),
        "region_context_locations": int(resolution["geometry_type"].eq("region").sum()),
        "point_geometry_candidates": int(resolution["geometry_type"].eq("point").sum()),
        "point_eligible_after_current_review": int(resolution["point_eligible"].sum()),
        "locations_requiring_manual_review": int(resolution["review_status"].str.startswith("needs_").sum()),
        "effect_records_by_geometry": {
            key: int(value)
            for key, value in resolution.groupby("geometry_type")["effect_count"].sum().items()
        },
        "rule": "Countries and broad regions retain geocoder centers/bounds for context but are not exact study points.",
        "geocoder": "OpenStreetMap Nominatim; candidate results cached locally for reproducibility.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nWrote {OUTPUT_CSV}")
    print(f"Wrote {REVIEW_PATH}")


if __name__ == "__main__":
    main()
