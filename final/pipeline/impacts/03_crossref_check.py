"""Check each study's DOI candidate(s) against Crossref (cached). Report only: studies.json is NOT changed.

Run from final/:  .venv/bin/python pipeline/impacts/03_crossref_check.py [--offline]
Input:  data/derived/impacts/studies.json (from 01_studies.py)
Cache:  data/derived/impacts/crossref_cache.json  (raw Crossref "message" per DOI, or the HTTP status)
Output: data/derived/impacts/crossref_check.json (+ .csv): one row per (study, DOI candidate)

Human decision: AI_LOG "Impacts task", step 8 ("Yes, run it").
Crossref etiquette (api.crossref.org): identifying User-Agent, one request at a time, we wait 1.1 s.

Rules (all deterministic):
- Candidates: every distinct source DOI value of a study, cleaned with 01_studies.py's clean_doi
  (whitespace removed, doi.org/ or doi: prefix removed, must match 10.<4-9 digits>/...).
- Request: GET https://api.crossref.org/works/<doi>. 404 -> status "not_in_crossref".
- Title match: both titles lower-cased, accents removed, non-letters/digits as spaces; the
  similarity is difflib.SequenceMatcher ratio against each of the study's workbook titles (best one).
  status "title_match" if ratio >= 0.90, "title_partial" if 0.60-0.90, "title_mismatch" if < 0.60.
- Year: the Crossref "issued" year is compared with the workbook year(s) (reported, not scored).
- For studies with several candidates: `only_match` is true for a candidate when it is the ONLY
  candidate of that study with status title_match. Nothing is chosen or written back here.
Label: crossref_title / crossref_year are `documented` (Crossref metadata); status, ratio and
only_match are `inferred` (rule above).
"""
import argparse
import csv
import difflib
import importlib.util
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FINAL = Path(__file__).resolve().parents[2]
SRC = FINAL / "data/derived/impacts/studies.json"
OUT = FINAL / "data/derived/impacts"
CACHE = OUT / "crossref_cache.json"
USER_AGENT = "ALAN-final-impacts-doi-check/0.1 (Harvard GSD MDE student project, one-off cached run)"
WAIT_S = 1.1

_spec = importlib.util.spec_from_file_location("s01", Path(__file__).parent / "01_studies.py")
_s01 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_s01)
clean_doi = _s01.clean_doi


def fold(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def fetch(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"http": 200, "message": json.load(resp)["message"]}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"http": 404, "message": None}
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    studies = json.loads(SRC.read_text())["studies"]
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}

    pairs = []
    for st in studies:
        cands = []
        for v in st["doi_source"]:
            d = clean_doi(v)
            if d and d not in cands:
                cands.append(d)
        pairs += [(st, d) for d in cands]

    n = 0
    for _, d in pairs:
        if d.lower() in cache:
            continue
        if args.offline:
            sys.exit(f"--offline: DOI not cached: {d}")
        if n:
            time.sleep(WAIT_S)
        r = fetch(d)
        cache[d.lower()] = {**r, "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        n += 1
        if n % 25 == 0:
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True))
            print(f"fetched {n}", flush=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True))

    rows = []
    for st, d in pairs:
        m = cache[d.lower()]["message"]
        row = {"study_id": st["study_id"], "doi": d, "candidates": sum(1 for s, _ in pairs if s is st),
               "workbook_title": " | ".join(st["title"]), "workbook_year": " | ".join(st["publication_year"]),
               "crossref_title": None, "crossref_year": None, "ratio": None, "year_equal": None}
        if m is None:
            row["status"] = "not_in_crossref"
        else:
            ct = " ".join(m.get("title") or [])
            sub = " ".join(m.get("subtitle") or [])
            yr = ((m.get("issued") or {}).get("date-parts") or [[None]])[0][0]
            ratio = max(max(difflib.SequenceMatcher(None, fold(t), fold(ct)).ratio(),
                            difflib.SequenceMatcher(None, fold(t), fold(ct + " " + sub)).ratio())
                        for t in st["title"]) if st["title"] else 0.0
            row.update(crossref_title=ct + (": " + sub if sub else ""), crossref_year=yr, ratio=round(ratio, 3),
                       year_equal=str(yr) in st["publication_year"],
                       status="title_match" if ratio >= 0.9 else "title_partial" if ratio >= 0.6 else "title_mismatch")
        rows.append(row)
    for r in rows:
        same = [x for x in rows if x["study_id"] == r["study_id"]]
        matches = [x for x in same if x["status"] == "title_match"]
        r["only_match"] = len(matches) == 1 and matches[0] is r

    meta = {"source": "data/derived/impacts/studies.json (doi_source)", "api": "https://api.crossref.org/works/",
            "rules": "see docstring of pipeline/impacts/03_crossref_check.py",
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "candidates": len(rows), "studies_with_candidates": len({r["study_id"] for r in rows}),
            "status_counts": {s: sum(r["status"] == s for r in rows) for s in
                              ("title_match", "title_partial", "title_mismatch", "not_in_crossref")},
            "year_not_equal": sum(r["year_equal"] is False for r in rows)}
    (OUT / "crossref_check.json").write_text(json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False, indent=1))
    with open(OUT / "crossref_check.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
