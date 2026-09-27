from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np


DATA_DIR = Path(
    "/Users/lindaxiangyideng/Documents/FA26 studio A2/data/philadelphia and cherry springs data"
)
VIZ_DIR = Path(
    "/Users/lindaxiangyideng/.codex/visualizations/2026/09/21/01a0c502-9042-7130-8969-23a01c4c4ba8"
)


def load_spectra(filename: str) -> dict[str, object]:
    with (DATA_DIR / filename).open(newline="") as handle:
        rows = list(csv.reader(handle))

    date_strings = [value for value in rows[0] if value]
    n_spectra = len(date_strings)
    numeric = np.array(
        [
            [float(value) if value not in ("", "NaN") else np.nan for value in row[:n_spectra]]
            for row in rows[1:]
        ],
        dtype=float,
    )

    return {
        "timestamps": np.array(
            [datetime.strptime(value, "%d-%b-%Y %H:%M:%S") for value in date_strings]
        ),
        "date_id": numeric[0],
        "solar_elevation_deg": numeric[1],
        "lunar_elevation_deg": numeric[2],
        "lunar_fraction": numeric[3],
        "spectral_irradiance": numeric[4:],
        "wavelength_nm": np.arange(280, 841),
    }


datasets = {
    "Cherry Springs": load_spectra("CSSP_spectra.csv"),
    "Philadelphia": load_spectra("DRL_spectra.csv"),
}

night_masks = {
    "Cherry Springs": (
        (datasets["Cherry Springs"]["solar_elevation_deg"] < -18)
        & (datasets["Cherry Springs"]["lunar_fraction"] < 0.3)
    ),
    "Philadelphia": (
        (datasets["Philadelphia"]["solar_elevation_deg"] < -18)
        & (datasets["Philadelphia"]["lunar_fraction"] < 1.0)
    ),
}


quality = []
for location, data in datasets.items():
    spectral = data["spectral_irradiance"]
    missing_by_wavelength = np.isnan(spectral).sum(axis=1)
    affected_wavelengths = data["wavelength_nm"][missing_by_wavelength > 0]
    timestamps = data["timestamps"]
    comparison = spectral[:, night_masks[location]]
    visible = (data["wavelength_nm"] >= 360) & (data["wavelength_nm"] <= 700)
    quality.append(
        {
            "location": location,
            "spectra": int(len(timestamps)),
            "timestamp_start": timestamps[0].isoformat(sep=" "),
            "timestamp_end": timestamps[-1].isoformat(sep=" "),
            "duplicate_timestamps": int(len(timestamps) - len(set(timestamps))),
            "missing_cell_rate": float(np.isnan(spectral).mean()),
            "missing_wavelength_min_nm": int(affected_wavelengths.min()),
            "missing_wavelength_max_nm": int(affected_wavelengths.max()),
            "negative_cells": int((spectral < 0).sum()),
            "comparison_spectra": int(night_masks[location].sum()),
            "comparison_missing_cells_360_700_nm": int(np.isnan(comparison[visible]).sum()),
            "comparison_zero_rate_360_700_nm": float((comparison[visible] == 0).mean()),
        }
    )


bands = [
    ("UV-A proxy", 315, 399),
    ("Violet-blue", 400, 499),
    ("Green", 500, 569),
    ("Amber-red", 570, 700),
    ("Visible", 400, 700),
]

band_summary = []
for band_name, lower_nm, upper_nm in bands:
    medians = {}
    for location, data in datasets.items():
        wavelength_mask = (data["wavelength_nm"] >= lower_nm) & (
            data["wavelength_nm"] <= upper_nm
        )
        per_spectrum = np.nansum(
            data["spectral_irradiance"][wavelength_mask][:, night_masks[location]], axis=0
        )
        medians[location] = float(np.median(per_spectrum))

    band_summary.append(
        {
            "band": band_name,
            "range_nm": f"{lower_nm}-{upper_nm}",
            "cherry_springs_median_w_m2": medians["Cherry Springs"],
            "philadelphia_median_w_m2": medians["Philadelphia"],
            "city_to_rural_ratio": medians["Philadelphia"] / medians["Cherry Springs"],
        }
    )


spectral_profiles = {}
for location, data in datasets.items():
    spectral_profiles[location] = np.nanmedian(
        data["spectral_irradiance"][:, night_masks[location]], axis=1
    )

visible_mask = (datasets["Cherry Springs"]["wavelength_nm"] >= 400) & (
    datasets["Cherry Springs"]["wavelength_nm"] <= 700
)
visible_peaks = {}
for location, profile in spectral_profiles.items():
    local_wavelengths = datasets[location]["wavelength_nm"][visible_mask]
    local_profile = profile[visible_mask]
    peak_index = int(np.nanargmax(local_profile))
    visible_peaks[location] = {
        "wavelength_nm": int(local_wavelengths[peak_index]),
        "spectral_irradiance_w_m2_nm": float(local_profile[peak_index]),
    }


chart_rows = []
chart_wavelengths = datasets["Cherry Springs"]["wavelength_nm"]
chart_mask = (chart_wavelengths >= 360) & (chart_wavelengths <= 700)
for wavelength in chart_wavelengths[chart_mask][::2]:
    index = int(wavelength - 280)
    for location in ("Philadelphia", "Cherry Springs"):
        value = float(spectral_profiles[location][index])
        chart_rows.append(
            {
                "wavelengthNm": int(wavelength),
                "location": location,
                "log10Irradiance": math.log10(value) if value > 0 else None,
            }
        )


chart_payload = {
    "schemaVersion": 1,
    "id": "night-spectrum-philadelphia-cherry-springs",
    "queryId": "local_csv_astronomical_night_spectrum",
    "title": "Night-time spectrum: Philadelphia and Cherry Springs",
    "description": "Median downwelling spectral irradiance during astronomical night; values shown on a logarithmic scale.",
    "chart": {
        "type": "line",
        "x": "wavelengthNm",
        "y": "log10Irradiance",
        "series": "location",
        "xLabel": "Wavelength (nm)",
        "yLabel": "log10 spectral irradiance (W m^-2 nm^-1)",
        "showXAxisLabel": True,
    },
    "rows": chart_rows,
    "source": {
        "label": "Spitschan et al. outdoor illumination spectra",
        "files": [
            {"label": "CSSP_spectra.csv"},
            {"label": "DRL_spectra.csv"},
        ],
        "metricDefinitions": [
            {
                "name": "Night-time spectral profile",
                "definition": "Median calibrated downwelling vector irradiance at each wavelength from 360 to 700 nm during astronomical night.",
            }
        ],
        "filters": [
            "Solar elevation: below -18 degrees",
            "Cherry Springs lunar fraction: below 0.3",
            "Philadelphia lunar fraction: below 1.0",
            "Wavelength: 360-700 nm",
        ],
        "caveats": [
            "The locations were measured on different dates and under different lunar fractions, so the comparison is descriptive rather than a controlled causal estimate.",
            "About 5% of Cherry Springs night cells from 360-700 nm are recorded as zero, consistent with a low-signal detection floor; medians reduce the influence of those zeros.",
        ],
        "evidenceFlow": [
            {
                "kind": "calculation",
                "title": "Aggregation",
                "description": "For each location and wavelength, select astronomical-night spectra and take the median across observations; plot the base-10 logarithm of positive medians.",
            },
            {
                "kind": "validation",
                "title": "Comparison coverage",
                "description": "The comparison contains 854 Cherry Springs spectra and 1,200 Philadelphia spectra, with no missing cells from 360-700 nm.",
            },
        ],
    },
    "theme": "codex-classic",
}


receipt_payload = {
    "schemaVersion": 1,
    "items": [
        {
            "id": "night-spectrum-comparison",
            "title": "Philadelphia night spectra are brighter across the visible range",
            "queries": [
                {
                    "id": "local-csv-night-profile",
                    "summary": "Calibrated downwelling irradiance spectra from the city and rural measurement sites.",
                    "reportingPeriod": "June 30-July 19, 2014",
                    "source": chart_payload["source"],
                    "columns": [
                        {"field": "band", "label": "Band"},
                        {"field": "range_nm", "label": "Range (nm)"},
                        {
                            "field": "cherry_springs_median_w_m2",
                            "label": "Cherry Springs median (W m^-2)",
                        },
                        {
                            "field": "philadelphia_median_w_m2",
                            "label": "Philadelphia median (W m^-2)",
                        },
                        {"field": "city_to_rural_ratio", "label": "City/rural ratio"},
                    ],
                    "rows": band_summary,
                    "preview": {
                        "kind": "aggregate",
                        "note": "Band-integrated medians for astronomical-night spectra.",
                        "totalRows": len(band_summary),
                    },
                }
            ],
            "assumptions": [
                "The wavelength step is 1 nm, so summing spectral irradiance over a band approximates the band-integrated irradiance.",
                "Band totals are ecological exposure proxies and are not species-specific biological response predictions.",
            ],
        }
    ],
}


summary = {
    "quality": quality,
    "band_summary": band_summary,
    "visible_peaks": visible_peaks,
    "night_sample_counts": {
        location: int(mask.sum()) for location, mask in night_masks.items()
    },
}

VIZ_DIR.mkdir(parents=True, exist_ok=True)
(VIZ_DIR / "night-spectrum-reviewed.json").write_text(
    json.dumps(chart_payload, indent=2), encoding="utf-8"
)
(VIZ_DIR / "night-spectrum-sources-reviewed.json").write_text(
    json.dumps(receipt_payload, indent=2), encoding="utf-8"
)
(VIZ_DIR / "light-spectra-analysis-summary.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)

print(json.dumps(summary, indent=2))
