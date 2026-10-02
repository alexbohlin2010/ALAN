# Body data preparation quality report

## Result

The supplied files cover behaviour, hypothalamus and liver clock-gene expression, and melatonin. The processed outputs are suitable for Step 9 with the caveats below.

## Dataset grain

- Behaviour: mechanized-perch hop counts per cage and minute. Social cages contain multiple birds, so these records are not individual trajectories.
- Clock genes: one sampled bird, tissue, gene and ZT marker per record.
- Melatonin: one sampled bird and ZT marker per record in the supplied combined CSV.
- Activity onset and offset: cage-level values supplied in `on1`–`on9` and `off1`–`off9`, measured relative to lights on/off.

## Coverage

- Social_ALAN.csv rows: 144
- Behaviour files: 37
- Behaviour hourly records: 21072
- Valid clock-gene measurements: 712
- Valid melatonin measurements across all supplied cohorts: 134
- Dedicated melatonin-cohort measurements in the primary social comparison: 24
- Valid cage-day onset/offset rows: 400

## Quality findings

- Behaviour matrix blank/zero separators checked: 888; non-zero separator values: 0.
- Invalid behaviour file shapes: 0.
- Composite subject-ID duplicates: 0.
- Bird labels reused across experiments: 26. The output therefore uses `experiment_start|bird_id` as the stable subject key.
- Missing sampling times: 5; these rows are retained in subject metadata but excluded from time-point summaries.
- Conflicting onset/offset values within a cage-day: 0.
- Fall PER2 records excluded from normalized analysis to match the supplied R workflow: 57.
- Metadata treatment fills: 1. Cage 4 in the fourth cohort is filled as SLD from the unanimous Social_ALAN.csv records; cage 5 remains unused.

## Interpretation limits

- Raw melatonin units are not stated in Social_ALAN.csv, so the scene data uses clearly labelled 0–1 analysis values and retains the raw value without inventing a unit.
- The Body scene melatonin series uses only the dedicated 10/13/2023 melatonin cohort. Values from molecular cohorts remain available in the long table and the by-cohort summary but are not silently pooled.
- The supplied R code normalizes some molecular cohorts separately and excludes fall PER2. The processed data reproduces those choices and records the normalization key for every value.
- Brain–liver correlations are exported only for the paper-aligned ALAN comparison (A versus SA) at ZT1 and ZT13. They must not be presented as an SA-versus-SLD result.
- Molecular and melatonin values are discrete measurements. Step 9 may animate between them only with a visible interpolation label.

## Validation checks

- PASS: all behaviour files have 24 × 60 data rows plus one separator per cage
- PASS: all cage separator rows are blank or zero
- PASS: subject composite keys are unique
- PASS: all non-missing molecular sampling times are ZT1/7/13/19
- PASS: onset/offset duplicates agree within cage and experimental day
- PASS: both primary social treatments have 1,440 minute profile values
- PASS: both primary social treatments have all four molecular ZT markers
- PASS: both primary social treatments have all four melatonin ZT markers
