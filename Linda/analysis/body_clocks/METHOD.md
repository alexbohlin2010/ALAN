# Body data preparation method

This directory prepares Step 8, **Body data preparation: internal clocks lose alignment**.

## Sources

- `Linda/data/body data/Raw Data*/*.txt`: mechanized-perch activity relayed every minute.
- `Linda/data/body data/meta*.csv`: cage treatment and 09:00–21:00 light schedule.
- `Linda/data/body data/Social_ALAN.csv`: bird metadata, hypothalamus and liver clock-gene expression, melatonin, and author-derived activity onset/offset.
- `Linda/data/body data/Behavior_Code.R` and `codes.R`: source analysis logic and normalization choices.
- Hui, Zhang & Ouyang (2025), *Birds of a feather flock together: social context exacerbates the effects of light pollution on circadian disruption*, DOI 10.1098/rspb.2025.0724.

## Primary comparison

The Body scene will initially compare Social Control (`SLD`) with Social ALAN (`SA`). Isolated Control (`LD`) and Isolated ALAN (`A`) remain in the processed evidence where needed for provenance and the paper-aligned brain–liver correlation analysis.

## Behaviour parsing

Each daily activity file contains 24 cage blocks. Each block has 25 rows: 24 clock-hour rows containing 60 one-minute hop counts, followed by a blank separator row. The script validates all 600 row positions and confirms that every data row has 60 values and every separator is blank or zero.

Activity is cage-level. A social cage contains multiple birds, so the data is never described as individual activity. The browser-ready profile averages cage-day values at each minute of the 24-hour cycle. ZT0 is 09:00, lights off is ZT12/21:00.

## Molecular data

Hypothalamus source columns are `BMAL`, `CRY`, `PER2`, and `PER3`. Liver source columns carry the `L_` prefix. Output names use bmal1, cry1, per2, and per3, following the paper and the supplied plotting labels.

Raw 2^-ΔΔCT expression is retained. The 0–1 analysis value reproduces the supplied R workflow:

- spring and fall are scaled separately for bmal1, cry1 and hypothalamic per3, plus liver bmal1 and cry1;
- fall per2 is excluded;
- liver per3 is scaled across the combined molecular records.

The normalization key and quality flag remain on every long-format row. Values are summarized only at the measured ZT1, ZT7, ZT13 and ZT19 markers. No interpolated molecular records are created.

## Melatonin

Raw melatonin values are retained, but their units are not stated in the supplied CSV. The 0–1 analysis value is therefore used for display and is scaled within source cohort. The Body scene summary uses the dedicated 10/13/2023 melatonin-only cohort; other cohorts remain separate in `body_melatonin_by_cohort_summary.csv` rather than being silently pooled. The visualization must not attach an invented physical unit or imply that melatonin rhythmicity disappears.

## Brain–liver relationships

The paper's brain–liver desynchronization comparison is between isolated and social birds under ALAN. Correlations are therefore exported for `A` and `SA` at ZT1 and ZT13. They are exploratory display support and must not be relabelled as a Social Control versus Social ALAN result.

## Run

```bash
python3 Linda/analysis/body_clocks/prepare_body_clocks.py
```

Outputs are written to `Linda/processed/body_clocks/`.
