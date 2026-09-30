# C3B radar response field

## What the source measures

`EL_data.csv` accompanies McLaren et al. (2018), *Artificial light at night
confounds broad-scale habitat use by migrating birds*. The response,
`meanVIR`, is the geometric mean vertically integrated radar reflectivity of
birds at peak nocturnal exodus. The study uses it as a community-level proxy
for autumn migrant stopover density. It is not an individual trajectory.

The radar response combines seven autumn migration seasons (2008–2014) from
16 weather-radar stations. The ALAN predictor is the 2014 artificial:natural
zenith sky-luminance ratio averaged within 2 km. Distance to a bright source
uses source cells with an ALAN ratio of at least five.

## Data-quality decisions

- The file has 628,603 predictor-grid rows. `meanVIR` is present for 166,296
  model cells and is `NaN` for the remaining 462,307 rows. Missing response
  rows are retained in the source audit but are not drawn as measured response.
- All predictor fields used by this layer are finite and within the ranges in
  the supplied README; there are no exact duplicate rows.
- The source study analysed 1×1 km cells, but the supplied CSV serializes UTM
  coordinates with unequal precision: X is mostly spaced at 1 km and Y at
  10 km. Consequently, many distinct source cells share the same displayed
  coordinate. Reconstructing the lost coordinates would invent geography.
- For display only, valid source cells sharing a serialized coordinate are
  collapsed with the median. The result is 20,823 approximate display
  coordinates. Tooltips report how many source cells each coordinate contains.
- UTM zone 18N coordinates are converted to WGS84. The mapped positions are
  explicitly labelled approximate because of the serialization issue above.

## Visual encoding

The C3B globe is one radar response field with two lenses:

- **Regional proximity**: hue shows proximity to a bright source; warmer cells
  are closer. The published model found higher stopover density nearer bright
  regions, with the distance response most pronounced beyond 50–100 km.
- **Local brightness**: hue shows the 2014 2-km ALAN ratio; warmer cells are
  brighter. The published model found lower stopover density at the highest
  local light intensities.
- In both lenses, hex height and luminosity show the percentile of the observed
  `meanVIR` response field. Globe hexagons are H3 resolution 5 display bins;
  they do not replace the source model grain.

The globe's 2024 VIIRS tiles remain visible as present-day geographic context.
They are not substituted for the study's 2014 sky-luminance predictor.

The two directional findings are taken from the published adjusted model. Raw
display-cell summaries are not presented as a new causal or adjusted analysis.

## Interpretation boundary

C3B supports the statement that population/community-level migrant stopover
distribution was associated with ALAN at different spatial scales. It does not
show individual routes, does not prove that a given bird changed its route, and
does not establish causality from a randomized experiment.

Sources:

- Paper: https://doi.org/10.1111/ele.12902
- Data: https://doi.org/10.5061/dryad.18v5d

Run:

```bash
python3 Linda/analysis/c3b_radar/prepare_c3b_radar.py
```
