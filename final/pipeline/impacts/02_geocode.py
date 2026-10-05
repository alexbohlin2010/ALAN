"""Geocode the distinct study Location strings with OSM Nominatim (cached).

Run from final/:  .venv/bin/python pipeline/impacts/02_geocode.py [--offline]
Input:  data/derived/impacts/studies.json (from 01_studies.py)
Cache:  data/derived/impacts/nominatim_cache.json  (raw Nominatim responses, keyed by query;
        a query already in the cache is never sent again; --offline never contacts Nominatim)
Output: data/derived/impacts/geocodes.json (+ geocodes.csv): one row per distinct Location string
        data/derived/impacts/study_locations.json: per study, its located points (for the app)

Human decisions (AI_LOG "Impacts task", steps 3, 5, 8): re-geocode in our own pipeline with
Nominatim; show approximate (region/country) locations as well as exact ones; hand fixes only from
the source paper or the human; studies without a Location stay in the data but are not drawn.

Nominatim usage policy (operations.osmfoundation.org/policies/nominatim/): at most 1 request per
second (we wait 1.1 s), an identifying User-Agent, results cached, no repeated queries.
Results are (c) OpenStreetMap contributors, ODbL 1.0; this attribution must go with the data.

Rules (all deterministic):
- Query: the source string with any "( ... )" part removed (an unclosed "(" removes the rest),
  whitespace collapsed, leading/trailing spaces and commas stripped. Nothing else is changed:
  spelling errors in the source are NOT corrected, so such strings may stay unresolved.
- Request: /search?q=<query>&format=jsonv2&limit=5&addressdetails=1&accept-language=en.
  The coordinate used is Nominatim's FIRST (top-ranked) result. The other candidates are kept
  only to flag ambiguity.
- Precision, from the top result:
    country  if addresstype == "country"
    region   if addresstype is in REGION_TYPES (administrative areas larger than a city),
             or if the result's bounding box is larger than POINT_MAX_KM on its longer side
    point    otherwise (city, town, village, campus, building, small natural feature, ...)
- Flags for human review (nothing is changed because of a flag):
    country_mismatch       the source string names a country (a COUNTRY_WORDS entry as a whole
                           word anywhere in the string) and the top result lies in another country
    name_not_in_result     the query's first comma part (lower case, accents removed, non-letters
                           as spaces) does not appear in the result's display_name (same folding)
    feature_category       the result's OSM category is not in OK_CATEGORIES (e.g. a shop, road,
                           building or tourism feature)
    ambiguous_country      the source names no country and the 5 candidates span >1 country
    source_has_coordinates the source string contains coordinates (not parsed here; they were
                           removed from the query by the "( ... )" rule or left as they are)
    unresolved             Nominatim returned no result (lat/lon stay empty)
- Human review (pipeline/impacts/maps/geocode_review.csv; decisions by the human only, F1 in
  AI_LOG Impacts step 10-11). Applied after the rules above; `review` records which one applied:
    accept              keep the Nominatim result; the flags stay listed but the point is drawn
    use_location        take lat/lon/precision/country_code from the result of another source string
                        (`value`), e.g. "eastern France" -> "France"
    source_coords_mean  `value` = "lat lon;lat lon;..." copied from the source string; lat/lon =
                        their arithmetic mean, precision = point
    paper_coords        `value` = "lat lon" in decimal degrees, converted from coordinates stated in
                        the source paper (citation in `note`); precision = point
  (for both coordinate decisions the Nominatim fields of that row are cleared)
    pending             not drawn until the human decides
  `draw` = resolved AND (no flags OR review in accept/use_location/source_coords_mean/paper_coords).
- Per-study review (pipeline/impacts/maps/study_location_review.csv; decisions by the human only, AI_LOG
  Fireflies step 2): for a listed study_id, study_locations.json gets ONE point with the location, lat, lon
  printed in the source paper (precision point, label `documented`, `source` = citation, `replaces` = the
  Data S1 location strings it replaces). Applied last; geocodes.json (per string) is not changed.
- Label: lat/lon/precision are `inferred` (rule above; inputs = the source string and the cached
  Nominatim response). The location string itself is `documented` (Dryad dataset).
"""
import argparse
import csv
import json
import math
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FINAL = Path(__file__).resolve().parents[2]
SRC = FINAL / "data/derived/impacts/studies.json"
OUT = FINAL / "data/derived/impacts"
CACHE = OUT / "nominatim_cache.json"
REVIEW = Path(__file__).resolve().parent / "maps/geocode_review.csv"
STUDY_REVIEW = Path(__file__).resolve().parent / "maps/study_location_review.csv"

ENDPOINT = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ALAN-final-impacts-geocode/0.1 (Harvard GSD MDE student project, one-off cached run)"
WAIT_S = 1.1

REGION_TYPES = {"state", "province", "region", "state_district", "county", "district",
                "territory", "archipelago", "continent"}
POINT_MAX_KM = 50.0

OK_CATEGORIES = {"place", "boundary", "natural", "waterway", "leisure", "amenity"}

# Words in the source strings that name a country -> ISO 3166-1 alpha-2 (lower case, as Nominatim).
# Matched as whole words anywhere in the string, case-insensitive (dots ignored; the first match in
# the string wins). A list of names, not a correction: spellings not listed are not matched.
COUNTRY_WORDS = {
    "argentina": "ar", "australia": "au", "austria": "at", "bahamas": "bs", "belgium": "be",
    "brasil": "br", "brazil": "br", "canada": "ca", "chile": "cl", "china": "cn",
    "costa rica": "cr", "finland": "fi", "france": "fr", "french polynesia": "pf",
    "germany": "de", "india": "in", "ireland": "ie", "israel": "il", "italy": "it", "japan": "jp",
    "korea": "kr", "netherlands": "nl", "the netherlands": "nl", "new zealand": "nz",
    "norway": "no", "philippines": "ph", "poland": "pl", "portugal": "pt",
    "scotland": "gb", "england": "gb", "wales": "gb", "uk": "gb", "u.k": "gb",
    "united kingdom": "gb", "slovakia": "sk", "south africa": "za", "spain": "es",
    "sweden": "se", "switzerland": "ch", "usa": "us", "us": "us", "united states": "us",
}

COORD_RE = re.compile(r"\d+[,.]\d+\s*\S{0,3}\s*[NS]\b|\d+\s*\S{1,3}\s*\d+\S?\s*[NS]\b")


def make_query(s):
    q = re.sub(r"\([^)]*\)?", " ", s)
    q = re.sub(r"\s+", " ", q)
    return q.strip(" ,")


def named_country(s):
    t = s.lower().replace(".", "")
    hits = []
    for w, cc in COUNTRY_WORDS.items():
        m = re.search(r"(?<![a-z])" + re.escape(w.replace(".", "")) + r"(?![a-z])", t)
        if m:
            hits.append((m.start(), -len(w), cc))
    return min(hits)[2] if hits else None


def fold(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def bbox_km(bb):
    """Longer side of a Nominatim boundingbox [south, north, west, east], in km (sphere)."""
    s, n, w, e = map(float, bb)
    lat_km = (n - s) * 111.195
    lon_km = (e - w) * 111.195 * math.cos(math.radians((n + s) / 2))
    return max(abs(lat_km), abs(lon_km))


def precision(r):
    if r.get("addresstype") == "country":
        return "country"
    if r.get("addresstype") in REGION_TYPES or bbox_km(r["boundingbox"]) > POINT_MAX_KM:
        return "region"
    return "point"


def fetch(query):
    url = ENDPOINT + "?" + urllib.parse.urlencode({
        "q": query, "format": "jsonv2", "limit": 5, "addressdetails": 1, "accept-language": "en"})
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return url, json.load(resp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="use the cache only")
    args = ap.parse_args()

    studies = json.loads(SRC.read_text())["studies"]
    strings = []
    for st in studies:
        for loc in st["location"]:
            if loc not in strings:
                strings.append(loc)
    strings.sort()

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    fetched = 0
    for s in strings:
        q = make_query(s)
        if not q or q in cache:
            continue
        if args.offline:
            sys.exit(f"--offline: query not cached: {q!r}")
        if fetched:
            time.sleep(WAIT_S)
        url, results = fetch(q)
        cache[q] = {"url": url, "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "results": results}
        fetched += 1
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1, sort_keys=True))
        print(f"fetched {fetched}: {q!r} -> {len(results)} result(s)", flush=True)

    rows = []
    for s in strings:
        q = make_query(s)
        res = cache.get(q, {}).get("results", []) if q else []
        src_cc = named_country(s)
        flags = []
        row = {"location": s, "query": q, "lat": None, "lon": None, "precision": None,
               "country_code": None, "osm_display_name": None, "osm_addresstype": None, "osm_category": None,
               "osm_type_id": None, "bbox_km": None, "candidates": len(res),
               "source_country_code": src_cc}
        if COORD_RE.search(s):
            flags.append("source_has_coordinates")
        if not res:
            flags.append("unresolved")
        else:
            top = res[0]
            cc = top.get("address", {}).get("country_code")
            row.update(lat=float(top["lat"]), lon=float(top["lon"]), precision=precision(top),
                       country_code=cc, osm_display_name=top.get("display_name"),
                       osm_addresstype=top.get("addresstype"), osm_category=top.get("category"),
                       osm_type_id=f"{top.get('osm_type')}/{top.get('osm_id')}",
                       bbox_km=round(bbox_km(top["boundingbox"]), 1))
            if src_cc and cc != src_cc:
                flags.append("country_mismatch")
            if fold(q.split(",")[0]) not in fold(top.get("display_name", "")):
                flags.append("name_not_in_result")
            if top.get("category") not in OK_CATEGORIES:
                flags.append("feature_category")
            ccs = {r.get("address", {}).get("country_code") for r in res}
            if not src_cc and len(ccs) > 1:
                flags.append("ambiguous_country")
        row["flags"] = flags
        row["review"] = None
        rows.append(row)

    by_string = {r["location"]: r for r in rows}
    with open(REVIEW, newline="") as f:
        reviews = list(csv.DictReader(f))
    for rv in reviews:
        r = by_string[rv["location"]]  # KeyError = review row for an unknown string
        d = rv["decision"]
        if d == "use_location":
            t = by_string[rv["value"]]
            assert t["lat"] is not None and not t["flags"], rv
            r.update({k: t[k] for k in ("lat", "lon", "precision", "country_code")})
        elif d in ("source_coords_mean", "paper_coords"):
            pts = [tuple(map(float, p.split())) for p in rv["value"].split(";")]
            r.update(lat=round(sum(p[0] for p in pts) / len(pts), 6),
                     lon=round(sum(p[1] for p in pts) / len(pts), 6), precision="point",
                     country_code=None, osm_display_name=None, osm_addresstype=None,
                     osm_category=None, osm_type_id=None, bbox_km=None)
        elif d not in ("accept", "pending"):
            raise ValueError(rv)
        r["review"] = f"{d}{': ' + rv['value'] if d == 'use_location' else ''} ({rv['decided_by']}, {rv['date']})"
    for r in rows:
        d = (r["review"] or "").split(":")[0].split(" ")[0]
        r["draw"] = r["lat"] is not None and (not r["flags"] or d in ("accept", "use_location", "source_coords_mean",
                                                                 "paper_coords"))

    meta = {
        "source": "data/derived/impacts/studies.json (Location field; Czarnecka et al. 2025, Data S1)",
        "geocoder": "OSM Nominatim " + ENDPOINT,
        "attribution": "Geocoding data (c) OpenStreetMap contributors, ODbL 1.0",
        "rules": "see docstring of pipeline/impacts/02_geocode.py",
        "coordinates": "WGS84 lat/lon in decimal degrees, as returned by Nominatim (top result)",
        "labels": {"location": "documented", "lat/lon/precision/country_code": "inferred"},
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "strings": len(rows),
        "resolved": sum(r["lat"] is not None for r in rows),
        "precision_counts": {p: sum(r["precision"] == p for r in rows) for p in ("point", "region", "country")},
        "flag_counts": {f: sum(f in r["flags"] for r in rows) for f in
                        ("unresolved", "country_mismatch", "ambiguous_country", "name_not_in_result",
                         "feature_category", "source_has_coordinates")},
        "reviewed": sum(r["review"] is not None for r in rows),
        "draw": sum(r["draw"] for r in rows),
        "resolved_without_flags": sum(r["lat"] is not None and not r["flags"] for r in rows),
    }
    (OUT / "geocodes.json").write_text(json.dumps({"meta": meta, "geocodes": rows}, ensure_ascii=False, indent=1))
    cols = list(rows[0].keys())
    with open(OUT / "geocodes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({**r, "flags": ";".join(r["flags"])})

    located = []
    for st in studies:
        pts = [{"location": loc, "lat": by_string[loc]["lat"], "lon": by_string[loc]["lon"],
                "precision": by_string[loc]["precision"], "flags": by_string[loc]["flags"],
                "review": by_string[loc]["review"]}
               for loc in st["location"] if by_string[loc]["draw"]]
        if pts:
            located.append({"study_id": st["study_id"], "points": pts})
    with open(STUDY_REVIEW, newline="") as f:
        study_reviews = list(csv.DictReader(f))
    ids = {st["study_id"]: st for st in studies}
    for rv in study_reviews:
        st = ids[rv["study_id"]]  # KeyError = review row for an unknown study
        pt = {"location": rv["location"], "lat": float(rv["lat"]), "lon": float(rv["lon"]), "precision": "point",
              "flags": [], "review": f"study_paper_coords ({rv['decided_by']}, {rv['date']})",
              "label": "documented", "source": rv["source"], "replaces": st["location"]}
        row = next((s for s in located if s["study_id"] == st["study_id"]), None)
        if row:
            row["points"] = [pt]
        else:
            located.append({"study_id": st["study_id"], "points": [pt]})
    no_loc = sum(1 for st in studies if not st["location"])
    unresolved_only = sum(1 for st in studies if st["location"] and not any(
        by_string[l]["draw"] for l in st["location"]))
    smeta = {**meta, "studies": len(studies), "studies_located": len(located),
             "studies_without_location": no_loc, "studies_with_location_not_drawn": unresolved_only,
             "study_reviews": len(study_reviews),
             "labels": {**meta["labels"], "points with label = documented": "location/lat/lon as printed in `source` (per-study review)"},
             "note": "Only points with draw = true (see geocodes.json). Studies without such a point are not listed here; they stay in studies.json."}
    (OUT / "study_locations.json").write_text(json.dumps({"meta": smeta, "studies": located}, ensure_ascii=False, indent=1))

    print(json.dumps(smeta, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
