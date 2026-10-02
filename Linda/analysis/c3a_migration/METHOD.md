# C3A — Migration Through Artificial Night

## Scientific question

This layer asks: **Where do real tracked migrating birds pass through darker
and brighter nighttime environments?** It does not test whether artificial
light caused route choice, avoidance, attraction, or a change in movement.

## Source adapters

The preparation script keeps the sources separate until the final display
payload:

- **Eastern Whip-poor-will** — GPS tracking of eastern whip-poor-will,
  Movebank Data Repository DOI `10.5441/001/1.k6s7916g`. Deployment metadata is
  joined from the supplied reference-data CSV.
- **American Robin GPS** — `ABoVE: Boelman Alberta American Robins`, GPS file.
- **American Robin Argos** — the same study's Argos Doppler-shift file. Argos
  remains labelled as lower spatial precision and is never treated as GPS.

## Cleaning rules

1. Remove records that Movebank marks invisible or as algorithm/manual
   outliers, records with missing/out-of-range coordinates, and duplicate
   individual + timestamp + sensor records.
   Original timestamp strings are preserved; the files do not provide a
   separate timezone field, so this revision does not silently relabel them as
   UTC.
2. Whip-poor-will uses only the source author's migration, stopover, and
   arrival classifications (`FM`, `SM`, `Stop1`, `Stop2`, `SM.stop1`,
   `SM.stop2`, `Arr`). Breeding, wintering, daytime roost, uncertain transition,
   and `rm` records are not reclassified as migration.
3. For American Robin, an Argos point within six hours of a GPS point for the
   same individual is excluded in favour of GPS. The six-hour window is small
   relative to the GPS sampling cadence but wide enough to cover the observed
   Argos pass timing.
4. A GPS movement above 120 km/h is treated as biologically impossible for
   these species. A point is removed as a spatial spike when it creates such a
   step while the direct movement between its two neighbours remains
   plausible. Argos uses a more tolerant 180 km/h check because its positional
   precision is lower.
5. Lines break after gaps larger than 14 days for Whip-poor-will GPS, 10 days
   for Robin GPS, and 24 hours for Robin Argos. These thresholds are above the
   observed 95th-percentile sampling interval for each adapter and prevent long
   missing periods from appearing as continuously observed travel.

## 2024 VIIRS display-brightness context

The original annual VIIRS rasters are not used in this revision. Each retained
point samples the red channel of the existing 2024 globe tile at zoom 9 and
divides it by 255. The result is named `viirs_relative_brightness`.

This value is a monotonic visual proxy after the globe's nonlinear display
transform and resampling. It is **not physical radiance**, is not reported in
`nW/cm²/sr`, and does not represent the tracking year (2016–2020).

“High relative brightness” is not hand-picked. Its threshold is the 90th
percentile of non-zero display brightness across all retained migration points.
Zero/dark points remain in the denominator when calculating each individual or
species proportion. The exact threshold is stored in the generated payload.

## Outputs

- `Linda/processed/c3a_migration/c3a_tracking_points.csv`
- `Linda/processed/c3a_migration/c3a_individual_summary.csv`
- `Linda/processed/c3a_migration/c3a_quality_summary.json`
- `Alexander/globe_v2/data/c3a_migration.json`

Rebuild with:

```sh
python3 Linda/analysis/c3a_migration/prepare_c3a_migration.py
```
