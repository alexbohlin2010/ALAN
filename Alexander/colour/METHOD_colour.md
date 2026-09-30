# Estimated night-light colour: method and audit trail

Version 3 · 2026-09-25 (see changelog) · applies to `globe_v2/tiles_rgba/2012` and `globe_v2/tiles_rgba/2024`

## 1. What is measured and what is estimated

| Quantity | Status | Source |
|---|---|---|
| Brightness of every 500 m pixel | **Measured** | VIIRS DNB, VNL v2.1 annual composites |
| Colour (chromaticity) of every pixel | **Estimated** | Rules below; no satellite colour data is used in v1 |

VIIRS DNB is a single panchromatic band (≈500–900 nm). It records no colour. Every hue on the globe is
an estimate. Each pixel stores a **source code** saying which rule produced its colour, and the Source
view in the interface displays that code directly.

## 2. Pixel encoding (`tiles_rgba`, lossless WebP)

| Channel | Content | Decode |
|---|---|---|
| R | VIIRS brightness, identical to the greyscale tile | `g = (log1p(L/0.12)/8.3)^0.62`, L in nW/cm²/sr (tiler.py) |
| G | CIE 1931 x of estimated light mix | `x = G/255 · 0.35 + 0.25` (quantisation 0.0014) |
| B | CIE 1931 y | `y = B/255 · 0.20 + 0.25` (quantisation 0.0008) |
| A | Source code | `code = 255 − A` |

Source codes: **3** documented city mix · **2** inferred city mix · **1** era prior · **0** unknown.
(4 is reserved for measured colour, e.g. SDGSAT-1 or calibrated ISS, if added later.)

## 3. Decision rules, in priority order

For each pixel and year the first applicable rule wins.

1. **City mix** (codes 3/2). If the pixel lies within a city's colour radius (§5) and that city has a
   row for this year in `city_colour_compositions.csv`, the colour is the luminance-weighted mixture (§4)
   of the lamp classes in that row. The code is 3 if the row's `colour_confidence` is `documented`,
   2 if `inferred`. 2012 rows describe the pre-retrofit stock (rule R7); 2024 rows the mid-2024 stock.
2. **Unknown** (code 0), **in both years**, everywhere else. Rendered in a fixed *typical night-light*
   colour with a faint diagonal hatch: the midpoint of the median 2012 city mix (0.5363, 0.4151) and the
   median 2024 city mix (0.4401, 0.3917), moved 60 % toward D65 → **xy (0.3829, 0.3588)**, ≈ `#ffc5a8`.
   It is identical in both years, so it creates no apparent change, and it is deliberately paler than any
   documented mix so it cannot be read as one. It is a display choice grounded in the sample, not an
   estimate for any particular place (computed in `colorize.py: typical_unknown_xy`).

**Why evidence-only (v2).** v1 coloured all of 2012 with an HPS era prior but left 2024 unknown outside
cities. In a 2012 | 2024 swipe that showed amber → neutral almost everywhere — a change of *rule*, not
of light. v2 applies the same rule to both years, so any colour difference in the swipe comes from
city-level evidence. Consequences: Boston is unknown in 2012 (its conversion began in 2010 and the
2012 share is undocumented), and cities without a composition row are unknown in both years. The era
prior (code 1) remains defined for reference but is not written to the tiles.

Composition rules used in the city table (the `rule` column):

| Rule | Meaning |
|---|---|
| R1 documented | Lamp type, CCT and share all documented |
| R2 documented share + spec | Share documented; CCT from a tender/standard/specification |
| R3 share from evidence | Share triangulated between conflicting sources (stated in `basis`) |
| R4 linear retrofit progress | Share at the composite's mid-point interpolated linearly between documented start/end or two documented shares |
| R5 CCT prior | CCT not documented; taken from era/regional practice (pre-2016 conversions ≈ 4000 K; China ≈ 4000 K under the 5000 K cap of CJJ 45-2015; Brazil PPPs ≈ 4000 K) |
| R6 bracket midpoint | CCT documented as a set/range with unknown split; equal weights |
| R7 back-cast | Earlier-year composition inferred from a later inventory |

Composite mid-points used by R4: **2012 → 2012.75** (the VNL "2012" file covers Apr 2012–Mar 2013),
**2024 → 2024.5**.

## 4. Colour science

- **Lamp-class chromaticity** (`lamp_class_xy.csv`, `lamp_class_xy.py`). Each measured spectrum is
  interpolated to 1 nm, truncated to 380–780 nm, integrated against the CIE 1931 2° observer, and
  reduced to xy. A class's xy is the per-coordinate **median** over its member spectra (3–20 per class,
  from LICA-UCM, LSPDD and CIE 015:2018 tables). Class membership is defined in `lamp_classes.py` (lamp
  type in the spectrum name + CCT computed from the spectrum).
- **Mixing.** Light adds in XYZ. For weights wᵢ with Y normalised to wᵢ:
  `X = Σ wᵢ xᵢ/yᵢ`, `Z = Σ wᵢ (1−xᵢ−yᵢ)/yᵢ`, `Y = Σ wᵢ` → xy. **Assumption:** composition shares
  are fixture counts, used as a proxy for luminous-flux shares.
- **Rendering** (`globe_v2/index.html`, fragment shader). xy → XYZ (Y = 1) → linear sRGB (IEC 61966-2-1
  matrix), negatives clipped, normalised so the largest channel = 1, then multiplied by the display
  brightness from R. So hue and saturation come from the estimate; brightness comes only from VIIRS.

| Class | x | y | sRGB | n spectra |
|---|---|---|---|---|
| HPS | 0.5363 | 0.4151 | `#ff8700` | 12 |
| LED 2700 K | 0.4547 | 0.4079 | `#ffae5e` | 11 |
| LED 3000 K | 0.4310 | 0.3881 | `#ffb279` | 14 |
| LED 4000 K | 0.3780 | 0.3773 | `#ffd6a7` | 9 |
| LED 5700–6500 K | 0.3135 | 0.3195 | `#fff5ff` | 5 |
| MH (quartz) | 0.3668 | 0.3806 | `#ffe4b1` | 20 |

## 5. Spatial rule

A city's mix is applied within a circle centred on the city centroid (`globe_v2/cities.json`):

- full weight to `r = 1.2 · √(lit_km² / π)`, using the **larger** of the 2012 and 2024 lit areas, so the
  circle is identical in both years and its edge cannot create apparent change;
- linear fade to `1.5 r`;
- the fade blends toward the unknown colour, so no new hue is created outside the city;
- the pixel's source code switches where the weight crosses 0.5.

Radii actually used are recorded per city-year in `city_colour_audit.csv`.

## 6. Known limitations and biases (read before citing)

1. **Street lighting ≠ all upward light.** Streetlights are roughly a third to a half of a city's upward
   light. Signage, buildings, sports venues, car parks and vehicles are not modelled; they are generally
   whiter than HPS, so 2012 colours are probably too orange in commercial districts.
2. **No within-city variation.** One mix per city; real cities mix HPS arterials with LED side streets.
3. **Jurisdiction mismatch.** Documented shares often cover the municipality only; the circle covers
   the lit metropolitan area. Extrapolation is flagged in each row's `basis`.
4. **Fixture share used as luminous share.** High-wattage arterial fixtures dominate luminous flux, so
   where arterials were converted last (e.g. Beijing) LED contribution is overstated.
5. **2012 city rows assume HPS pre-retrofit stock** and so ignore regional practice (mercury vapour and fluorescent in parts of Asia
   and Africa; metal halide in city centres). Tokyo (partly mercury pre-LED) has no row and is
   unknown in both years.
6. **5700 K class spectra are 5900–6800 K**, so Jaipur/Delhi render slightly too cool.
7. **Snippet-only sources** underlie several rows (Madrid LED CCT, Shanghai share, Hefei share,
   Beijing SDGSAT-1 figure); these are named in `basis`.
8. **Brightness is itself spectrally biased.** DNB under-reads white LED relative to HPS by ~28 % at
   equal lumens (3000 K) — see `../lamp_class_reference.csv`. The colour layer does not correct brightness.
9. **Display.** sRGB cannot represent the most saturated sodium/amber chromaticities exactly; the
   brightness transfer curve is a display choice (`uCurve = 1.2` in the shader).

## 7. Validation status

No measured colour enters v1. One consistency check has been run.

**ISS calibrated frames, Madrid** (Sánchez de Miguel et al., Zenodo 10.5281/zenodo.6638505, CC-BY-4.0).
The two published mosaics in that record are unusable (byte-identical, NaN-filled, extent over the
Americas; SHA-256 `9eba70e1…`). The per-frame calibrated channels in `pre2013.zip`/`post2013.zip` were
scanned remotely (`find_madrid.py` → `find_madrid.log`: 12 pre-2013 and 19 post-2013 frames contain
Madrid). Three sharp frames were extracted to `inputs/iss/` and analysed with `validate_madrid_iss.py`
→ `validation_madrid_iss.csv`. Metric: radiance-weighted camera G/R over the brighter half of pixels
within the 28.8 km Madrid circle.

| Period | Frame | Pixel | G/R | Documented LED share |
|---|---|---|---|---|
| 2012 | iss030e082053 | ~43 m | 0.447 | ≈0 (retrofit begins late 2014) |
| 2014–15 | iss042e183298 | ~250 m | 0.529 | 84,000 LED installed 2014–15 |
| 2019–20 | iss061e035301 | ~390 m | 0.554 | 35.6 % (2019) |

Findings:
- **Direction and timing agree** with the composition table: a step toward whiter light across the
  2014–15 retrofit, then little change to 2019, matching both the documented LED share and the flat
  VIIRS radiance after 2015.
- **A uniform HPS 2012 colour would be too uniform** (one reason v2 no longer paints it globally). In 2012 the G/R spread is wide (p10 0.15, p90 0.75): most of the
  city is sodium-red, but a minority of pixels is much whiter (metal halide, commercial and non-street
  light). This is limitation 1 in §6, now observed.
- **Not an absolute test.** The DSLR spectral sensitivities are not available here, so G/R cannot be
  converted to CIE xy. Frames differ in lens, exposure, viewing angle and atmosphere; the 2014–15 and
  2019–20 frames are 6–9× coarser than the 2012 frame.

**Absolute 'eyedropper' test (failed, not used).** The same frames were converted to CIE xy with each
camera's Adobe/LibRaw colour matrix (Nikon D3S 2012-02-12, D4 2015-01-24, D5 2019-11-08; cameras and
dates from eol.jsc.nasa.gov; matrices from LibRaw `colordata.cpp`) → `iss_chromaticity.py`,
`iss_chromaticity.csv`. Result: 2012 Madrid = (0.576, 0.362) vs documented sodium ≈ (0.536, 0.415), and
2019 is *less* white than 2015, contradicting the G/R trend. Conclusion: the `cal2N` channels are rescaled
per channel, so camera matrices do not apply; the frames support relative ratios only. Absolute colour
would need the authors' per-channel calibration constants.

Not used: **SDGSAT-1 Glimmer Imager** (2022–), access approval not pursued.

## 8. How to audit a pixel

1. Switch the globe to **Source** view, or decode A for that pixel: `code = 255 − A`.
2. Codes 2/3: find the city whose circle contains the pixel in `city_colour_audit.csv` (radius, centre,
   composition, xy). Look up the same city-year in `city_colour_compositions.csv` for rule and basis.
3. Follow `basis` to the row in `../alan_streetlight_cct_50cities.csv` and its `source_url`s.
4. Lamp-class xy → `lamp_class_xy.csv` → member spectra listed in its `members` column.

## 9. Reproduce

```
cd ~/alan-streetlight-cct
python scripts/compute_spectra.py && python scripts/lamp_classes.py   # needs numpy, pandas, colour-science, openpyxl
cd colour && python lamp_class_xy.py && cd ..                        # class chromaticities
globe_v2/venv/bin/python globe_v2/tiler.py 2012 --out globe_v2/tiles   # and 2024
globe_v2/venv/bin/python colour/colorize.py 2012 2024
```

Input SHA-256:

| File | SHA-256 |
|---|---|
| vnl/vnl_2012.tif | `cd19ce2dd6638d0620bf3a12bb1e5802111810a4348d6fbe3a45613c1abaacd2` |
| vnl/vnl_2024.tif | `e6edde68952052f8c53050e2ce7082bab08ddd0e15a696f999215e2d57194c53` |
| alan_streetlight_cct_50cities.csv | `061d039f404c9c8c826915d934985719a06a26d25ceeb5339bf2cd3a9bc0e4b8` |
| lamp_class_reference.csv | `49db0f850cfd74010a46c06db2a09f3b4a75800b3ef67c19b9613bf01a42ef24` |
| colour/city_colour_compositions.csv | `7aab67689999e067e2defa03508612d407852654a9ea07ddea87577583895973` |
| colour/lamp_class_xy.csv | `733be6a07c2f4a2be567462498d088181638fd9673ad391bde68b8e748045925` |
| globe_v2/cities.json | `4ced6958fb23e3f8c3046bc598532f6a071d187099b3fc2623402fe6944dfbc4` |

## 10. Changelog

- **v3 (2026-09-25).** Unknown pixels rendered in a sample-derived typical night-light colour
  (xy 0.3829, 0.3588) instead of D65 grey; stored in the tiles so the city-edge fade blends into it.
  ISS absolute-colour test documented (§7).

- **v2 (2026-09-25).** Evidence-only rule: the HPS era prior is no longer painted outside cities in 2012;
  both years are unknown outside city circles. Added 21 pre-retrofit 2012 city rows (rule R7). City
  circles use the larger of the 2012/2024 lit areas. Display: saturation scales with evidence
  (documented 1.0, inferred 0.8); unknown hatch lightened.
- **v1 (2026-09-25).** First release: HPS era prior for 2012, city mixes for 2024, unknown elsewhere.
