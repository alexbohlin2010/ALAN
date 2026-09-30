# C1 location-resolution audit

This audit converts the C1 workbook's free-text `Location` field into an explicit,
reviewable geography layer. It does not treat every geocoder result as an exact
study coordinate.

## Coverage

- 4,905 total effect-size records.
- 3,930 records (80.12%) contain a location; 975 contain no location.
- The 3,930 located records reduce to 142 distinct source strings.
- All 142 source strings now have a geographic candidate or a source-backed
  correction.
- 36 locations, covering 630 effect records, are currently approved for point
  placement.
- 40 locations, covering 898 effect records, remain in the focused manual-review
  queue.

## Geometry rules for the globe

- `point`: city, campus, institution or source-confirmed study site. Only rows
  with `point_eligible = True` may be rendered as crisp points.
- `multi_point`: more than one named or source-listed study site. Preserve the
  individual positions stored in `multi_site_coordinates_json`.
- `region`: named natural area, state/province, directional region or otherwise
  areal place. Use an uncertainty halo or geographic extent, never an exact pin.
- `country_region`: country-only evidence. Use country-level coverage/counts or
  an outline, not the stored representative center as a study point.

Field and laboratory studies must remain visually distinct. A laboratory point
means “the experiment was conducted here”; it does not mean that the organism's
treatment exposure equals local VIIRS radiance.

## Important corrections

- `Libreville, Oregon, USA` conflicts with real geography. The associated source
  paper identifies the study site as the Boeckman Road Extension in Wilsonville,
  Oregon and supplies coordinates `45.316245, -122.783933`; the audit uses that
  source-backed location while preserving the workbook text.
- `Wainfleet bag, Ontario, Candada` is normalized to Wainfleet Bog Conservation
  Reserve using the official Canadian geographical-name record. It remains an
  areal protected-place location rather than an exact experimental point.
- The Seewiesen row contains four coordinates in the workbook itself. All four
  are retained rather than averaged into a single displayed study point.
- `Lebretshoeve, Radio Kootwijk and Klaterweg, Netherlands` is retained as three
  separately resolved named sites and remains medium-confidence pending source-
  paper confirmation of the exact sampling positions.

## Files

- `c1_location_resolution.csv`: complete 142-row audit table.
- `c1_location_review_needed.csv`: focused queue of candidates that still need
  manual confirmation before exact placement.
- `c1_location_geocode_cache.json`: cached raw OpenStreetMap Nominatim results
  for reproducibility; the visualization should never query the service live.
- `c1_location_resolution_summary.json`: machine-readable coverage summary.
- `resolve_c1_locations.py`: reproducible preparation script in
  `Linda/analysis/c1_effects/`.

The next visualization revision should join this table to C1 records by the
preserved source `Location` string, create map anchors at the `study + resolved
location` grain, and then expand individual effect records only after a user
selects a location.
