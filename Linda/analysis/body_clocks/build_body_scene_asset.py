#!/usr/bin/env python3
"""Build the compact browser asset for the Step 9 body-clock scene.

The canonical processed table remains Linda/processed/body_clocks/body_scene_data.json.
This script copies only the reviewed fields used by the browser visualization and
validates the comparison, molecular marker times, and one-minute activity coverage.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "Linda/processed/body_clocks/body_scene_data.json"
TARGET = ROOT / "Alexander/globe_v2/data/body_clocks.json"


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))

    assert [item["code"] for item in source["primary_comparison"]] == ["SLD", "SA"]
    assert source["time"]["measured_molecular_markers"] == [1, 7, 13, 19]

    profile = source["behaviour"]["profile"]
    for treatment in ("SLD", "SA"):
        rows = [row for row in profile if row["treatment"] == treatment]
        assert len(rows) == 1440
        assert [row["zt_minute"] for row in rows] == list(range(1440))

    marker_keys = {
        (row["treatment"], row["tissue"], row["gene"], row["zt"])
        for row in source["clock_expression"]["summary"]
    }
    for treatment in ("SLD", "SA"):
        for tissue in ("hypothalamus", "liver"):
            for gene in ("bmal1", "cry1", "per2", "per3"):
                for zt in (1, 7, 13, 19):
                    assert (treatment, tissue, gene, zt) in marker_keys

    scene = {
        "schema_version": source["schema_version"],
        "scene": source["scene"],
        "experiment": {
            "organism_common": "Zebra finch",
            "organism_scientific": "Taeniopygia guttata",
        },
        "primary_comparison": source["primary_comparison"],
        "time": source["time"],
        "visualization_rules": source["visualization_rules"],
        "behaviour": {
            "measurement_grain": source["behaviour"]["measurement_grain"],
            "continuous_resolution": source["behaviour"]["continuous_resolution"],
            "profile": profile,
        },
        "clock_expression": source["clock_expression"],
        "melatonin": source["melatonin"],
        "provenance": {
            "canonical_processed_asset": "Linda/processed/body_clocks/body_scene_data.json",
            "method": "Linda/analysis/body_clocks/METHOD.md",
            "source_paper": "https://pmc.ncbi.nlm.nih.gov/articles/PMC12289197/",
        },
    }

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(scene, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Wrote {TARGET} ({TARGET.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
