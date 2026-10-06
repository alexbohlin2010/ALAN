"""Study abstracts from the cached Crossref responses (offline: no requests are made).

Run from final/:  .venv/bin/python pipeline/impacts/11_abstracts.py
Inputs:  data/derived/impacts/studies.json        (from 01_studies.py; the study's chosen DOI)
         data/derived/impacts/crossref_cache.json (from 03_crossref_check.py; raw Crossref "message" per DOI)
         data/derived/impacts/crossref_check.json (from 03_crossref_check.py; title match status per study + DOI)
Output:  data/derived/impacts/abstracts.json

Human decision: AI_LOG "Effect dots and examples", step 2 (option A: abstracts from the Crossref cache only).

Rules (all deterministic):
- A study gets an abstract only if its chosen DOI (studies.json `doi`) has an `abstract` in the cache AND that
  study + DOI has status "title_match" in crossref_check.json (Crossref title ratio >= 0.90 to the workbook title).
- Text: the publisher-deposited JATS markup is reduced to plain text: the leading <jats:title> heading is dropped,
  each closing paragraph / list item becomes a paragraph break, all other tags are removed, HTML entities are
  unescaped and runs of whitespace collapsed. Words are not changed.
Label: `text` is `documented` (abstract as deposited by the publisher with Crossref; source = the DOI's Crossref record).
Studies without an abstract are left out; the meta block lists how many and why.
"""
import html
import json
import re
from pathlib import Path

FINAL = Path(__file__).resolve().parents[2]
D = FINAL / "data/derived/impacts"


def plain(jats):
    s = re.sub(r"<jats:title>.*?</jats:title>", "", jats, flags=re.S)
    s = re.sub(r"</jats:(p|list-item|sec)>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    paras = [" ".join(p.split()) for p in s.split("\n")]
    return "\n\n".join(p for p in paras if p)


def main():
    studies = json.loads((D / "studies.json").read_text())["studies"]
    cache = json.loads((D / "crossref_cache.json").read_text())
    status = {(r["study_id"], r["doi"]): r["status"] for r in json.loads((D / "crossref_check.json").read_text())["rows"]}
    out, why = {}, {"no_doi": 0, "no_abstract_in_crossref": 0, "doi_not_title_match": 0}
    for st in studies:
        doi = st.get("doi")
        if not doi:
            why["no_doi"] += 1
            continue
        msg = (cache.get(doi) or {}).get("message") or {}
        if not msg.get("abstract"):
            why["no_abstract_in_crossref"] += 1
            continue
        if status.get((st["study_id"], doi)) != "title_match":
            why["doi_not_title_match"] += 1
            continue
        out[st["study_id"]] = {
            "doi": doi,
            "text": plain(msg["abstract"]),
            "label": "documented",
            "source": f"Crossref record https://api.crossref.org/works/{doi} (cached by 03_crossref_check.py)",
        }
    meta = {
        "source": "crossref_cache.json (03_crossref_check.py), filtered by crossref_check.json title_match",
        "script": "pipeline/impacts/11_abstracts.py",
        "label": "documented: publisher-deposited abstract; markup stripped, words unchanged",
        "use": "on screen only short verbatim quotes (< 15 words) with the study cited (human, AI_LOG Effect dots and examples step 1)",
        "studies": len(studies), "with_abstract": len(out), "left_out": why,
    }
    (D / "abstracts.json").write_text(json.dumps({"meta": meta, "abstracts": out}, ensure_ascii=False, indent=1))
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
