# ALAN / Nighttime Lights — Project Handoff

Artificial Light at Night (ALAN) research + data visualisation. Harvard MDE.
Everything below is built and working; this document is the context for picking
it up in a fresh session.

---

## 1. The core scientific point

**The dominant global nightlights sensor cannot see colour, and that is the
whole problem.**

VIIRS **DNB** (Day/Night Band) is *one panchromatic band*, 500–900 nm, centred
at **705 nm**. It is the only one of VIIRS' 22 bands that sees city lights at
night — the rest are reflective-solar (daylight only) or thermal.

| | Wavelength |
|---|---|
| DNB band centre | **705 nm** |
| Human photopic peak | 555 nm |
| Melanopic (circadian) peak | ~480 nm |
| Blue LED pump peak | ~450 nm |

Consequences, all load-bearing:

- **~34% of a white LED's radiant power** sits in the ~450 nm blue pump, outside
  DNB's response. Sodium emits almost entirely *inside* it.
- So a **sodium→LED conversion registers as dimming** even at constant visual
  brightness. Tucson measured −20% on DNB where the real change was ~−7%.
- Radiance is comparable between two cities with similar lighting tech, and
  across time only while a city's lighting stock is stable. **A city mid-retrofit
  appears to dim.** Madrid's −23% in our data is partly this artefact.
- Radiance **does not convert to lumens**. Three gaps: radiometric→photometric
  needs the spectrum; radiance→flux needs the angular distribution; escaping
  light ≠ installed light (fixture shielding, tree cover, ground albedo).
  Get lumens from **streetlight inventories**, not from orbit.

**Framing that works:** radiance measures *light thrown at the sky* — i.e. light
pollution, the wasted fraction — not lighting provision. Stated that way no
conversion is needed and no fixture assumption is smuggled in.

**The collaborator's spectral data fills exactly this hole.** Join key is `city`
in `city_summary.csv`.

---

## 2. What is built

### A. Tidy dataset — 50 cities, nightly, 2012–2024

`nighttime-lights-50-cities/` (8.8 MB) — also zipped as
`nighttime-lights-50-cities.zip`. **106,755 nightly rows.**

```
README.md                 units, columns, caveats, sources
city_summary.csv          50 rows, 2012->2024 change. START HERE.
all_cities_annual.csv     650 rows, for time series
cities/<City>.csv         50 files, one row per night
cities.csv                metadata, bounds, centroids
Philadelphia_city_limits.csv   admin-boundary version (mean ~57-68 not ~11-14)
build_dataset.py          reproducible
starter_charts.py         three ready charts
chart_*.png
```

**The metric that makes cross-city comparison work:**

    total  ≈  lit_km2  ×  mean_lit

A city brightens by **spreading** (lit area) or **intensifying** (brightness
where already lit). Raw `mean` is NOT comparable across cities — each city's
raster is a differently-sized box including rural edge. Use `total`,
`lit_km2`, `mean_lit`.

Key findings already in the data:
- **Baghdad +283%** — area ×2.9 AND intensity +54%. Post-conflict rebuild.
- **Dar es Salaam +186%** — area **+324%**, intensity **+1.7%**. Pure
  electrification, opposite mechanism, same headline number.
- **US cities grow only by sprawl** — Phoenix intensity +1.2% over 13 years.
- **Hong Kong +14%** — geographically capped, lit area +4.3%; behaves like
  Boston, not like Dongguan.
- **Four cities declined**, with diagnostic shapes:
  - Madrid — **step** (2013–15 then flat a decade) → one-off LED retrofit
  - Johannesburg — **ratchet** (progressive from 2018) → load shedding
  - Khartoum — **cliff** (185→152→68) → war from April 2023
  - New Taipei — ambiguous, −7.5%
  These are hypotheses matching known events, NOT demonstrated causes.

### B. Interactive globe

Published artifact: **https://claude.ai/artifact/QacwehG31JovQkgz7Lfmju**
Source: `web/index.html` (single file). Assets: `web/mid/*.webp` (4096px,
animation tier), `web/hi/*.webp` (8192px, shown when settled), `web/cities.json`.

Dark rotating globe, 13 annual frames cross-faded, 50 clickable cities.

**Hard-won implementation notes — do not regress these:**

1. **globe.gl 2.46.2 from jsdelivr** (not on cdnjs). Bundles three r185 and does
   NOT expose THREE. Constructors are borrowed from live instances:
   `m.map.constructor` for Texture, `m.emissive.constructor` for Color.
2. **`material.color` is `null`** on globe.gl's globe material, which makes
   `clone()` throw. Set it to white before cloning.
3. **Cross-fade = two spheres.** A clone of the globe mesh at scale 1.0015 with
   `transparent, depthWrite:false`; animate its `opacity`. GPU blends, zero
   per-frame cost. A shader would be cleaner but THREE isn't reachable.
4. **NEVER set `material.needsUpdate` on a map swap.** Measured: 0.1 ms/frame
   normally, **85.5 ms** with the flag (shader recompile). The uniform refreshes
   on its own — verified by pixel readback.
5. **Texture upload costs ~100 ms** (mipmap generation at 4096×2048). All 13
   are uploaded up front behind the loader (`preupload()`), ~580 MB resident,
   skipped when `navigator.deviceMemory < 8`.
6. **Playback must NOT use requestAnimationFrame.** rAF is suspended when the
   embedded artifact is considered hidden — measured 0 frames/sec in one run and
   84/700 ms in another, same page. Playback is a `setInterval` against the wall
   clock that forces its own `renderer.render()`. This was the cause of the
   long-running "play stutters / doesn't run" bug.
7. **Rotation scheme:** still at rest; drifts only during playback; stops
   permanently the moment the user grabs the globe.
9. **The colour on the globe is imposed, not measured.** Every source pixel is a
   single int16 — `bands per pixel: 1`. There is no red, green or blue anywhere
   in the data. The amber comes from one scalar fanned through three staggered
   ramps in `clean_render.py`:

   ```python
   v = np.clip(np.log1p(st[i]/0.12)/hi, 0, 1) ** 0.62   # one scalar, 0..1
   rgb[...,0] = np.clip( v         * 1.55, 0, 1)   # red   rises from v=0
   rgb[...,1] = np.clip((v - 0.06) * 1.30, 0, 1)   # green rises from v=0.06
   rgb[...,2] = np.clip((v - 0.42) * 1.45, 0, 1)   # blue  only above v=0.42
   ```

   Dim → red only; mid → amber; bright → white-hot. A black-body-style heat ramp.
   NASA's own Black Marble imagery is false-colour for the same reason.

   **This is a live problem, not just a footnote.** The globe renders everything
   in sodium amber while the project's whole argument is that cities are shifting
   to blue-rich LED — so the colour depicts roughly the *opposite* of the trend,
   and a viewer could reasonably read meaning into it. The page footer currently
   says the sensor cannot see colour but does NOT say the amber is invented.

   The colour channel is therefore **free real estate**: it currently carries
   redundant brightness information. Hand it to a real variable — rate of change,
   or ideally measured/estimated **CCT** — and the globe would show the thing the
   project is actually about. See `PROMPT_cct_task.md`.

8. Linear cross-fade is deliberate. A spline would ease at each keyframe, driving
   the rate of change to zero there — it reads as MORE stepped, not less.

### C. Aurora labelling

`detect_aurora.py` → `aurora_events.csv`, `aurora_summary.csv`,
`globe/aurora_mask.npy`. `clean_render.py` re-renders textures with aurora
removed (infilled with the per-pixel median across years).

**Aurora is not artificial light and must be excluded from ALAN analysis.**

Detection — four tests, all must pass:
1. geomagnetic latitude > 55° (both ovals)
2. year value − pixel's own median across years > 0.10
3. pixel median < 0.15 (not a real settlement)
4. part of a connected blob ≥ 40 px (~3,400 km²) — rules out flares and fires

Geomagnetic latitude uses a dipole pole at **80.4°N, 72.8°W**.

Events found: **7**, in 2012 (1), 2023 (4), 2024 (2) — consistent with solar
cycle 24 rise and cycle 25 maximum.

The big one: **northern Quebec, 2012** — 1,404 km E–W × 623 km N–S, 47,913 km²,
**114× brighter than any later year**, diffuse (peak/mean 3.1). Quebec sits at
**63.1° geomagnetic** despite 53.5° geographic, because the geomagnetic pole is
almost on its meridian. Control: Alberta at the *same geographic latitude*
(60.1° geomagnetic) shows nothing. Scandinavia, Siberia, Patagonia show no 2012
spike either — so it is not a global processing artefact.

**The 50-city dataset is unaffected** — the highest geomagnetic latitude among
them is Toronto at 53.2°, below the ~55° threshold.

---

## 3. Data sources and their limits

| Source | What | Coverage | Access |
|---|---|---|---|
| **VNL v2.1 annual** (EOG, Colorado School of Mines) via OpenGeoHub Zenodo `17294744` | global annual rasters, 500 m, 86400×35849 | **2012–2024** | no account, COG |
| **HDNTL** Zenodo `17079409` (Chinese team) | daily NTL, 653 cities | **2012–2024** | no account, 33 GB |
| EOG monthly (`NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` on GEE) | global monthly | **through June 2026** | GEE account |
| NASA Black Marble VNP46A2/A3/A4 | daily/monthly/annual, 500 m | 2012– | Earthdata token |
| EOG direct | VNL v2.2 | 2012–2024 | free registration (Keycloak) |

**Annual data stops at 2024 everywhere** — no 2025 annual exists yet. Monthly
runs to June 2026. A synthetic 2025 could be made by averaging 12 monthlies, but
it is a *different product* (annual applies outlier removal, background
suppression, a lit mask) and would be visibly noisier. 2026 is only half a year
and that half is northern winter — snow-inflated, not comparable.

### CRITICAL data trap — the packing inconsistency

In Zenodo `17294744` the years are packed **inconsistently**:

| Years | `scales` tag | Raw range |
|---|---|---|
| 2012–2021 | 1.0 | 0–3250 |
| 2022–2024 | 10.0 | 0–282 |

Correct handling: **apply each file's own `scales` tag, then divide by 10** to
get nW/cm²/sr. Read naively, 2022–2024 come out 10× too low and Philadelphia
appears to collapse by 90% in 2022. That is an artefact.

**Worse, the internal overview pyramids are built on the raw integers**, so
decimated reads silently drop dim pixels in the later years — lit-pixel counts
halve at the 2021/2022 boundary at *every* overview level (ratio 0.59 even at
1/4). **Always read these at full resolution and box-average in float.** The
files are only ~70 MB each compressed; download them rather than streaming
decimated.

### Other gotchas
- HDNTL is VNP46A2-derived → **scale factor 0.1** for nW/cm²/sr.
- HDNTL flag rasters sometimes differ in extent from the data raster; guard it.
- Night counts vary 2.5× by cloud climatology (Phoenix 3,010 vs New Taipei
  1,179). Affects noisiness, not means.
- **The seasonal cycle is mostly not lighting.** ±15% winter peak = snow albedo
  (fresh snow reflects ~80% up, asphalt ~10%) + leaf-off. For Philadelphia it is
  about the size of the entire 13-year trend. Compare like months, or use annual.
- Filter on `n_pix` before plotting daily data — cloudy nights give partial
  coverage that masquerades as dimming.
- Global rasters cover −62°S to 87.4°N, not the full sphere. Pad for a globe.

---

## 4. Ground-truth lighting inventories (for the lumens side)

- **Cambridge MA** — live ArcGIS layer, 6,157 city-owned lights with fixture
  archetype (Cobrahead 78%, "1907" 8.9%, Acorn 5.4%, **Ornamental Gas ×5**).
  Citywide conversion was **4000 K**; 3000–3500 K for pedestrian-scale in Phase
  Two. One of very few US cities that implemented dimming.
  `services1.arcgis.com/WnzC35krSYGuYov4/arcgis/rest/services/Street_Lights/FeatureServer/0`
- **Boston** — `bos_retrofit2014.csv`, 9,789 lamps with **rated lumens**:
  8,011 sodium + 1,778 mercury → LED. **189 million lumens** total, mean
  19,282 lm/lamp; ~1.3 billion lm scaled to Boston's 67,000 streetlights.
  LED replacements ≈ 68 Mlm replacing 189 Mlm — a 64% cut in *rated* output,
  because HPS wasted much of it sideways and up.
  Boston also has **~2,800 gas lamps** (~2000 K) — a real spectral outlier.
- **Philadelphia** — 130,000 HPS→LED, $91M, Ameresco. Broke ground **8 Aug
  2023**, 24 months. So the retrofit is NOT yet in the 2012–2024 record; 2024 is
  the brightest year. When 2025/26 land, that is the natural experiment.
- Municipal registers generally carry **lamp type but not CCT** — Kelvin lives
  in procurement documents. Dark Sky MA has a small town-by-town CCT table.
- **LSPDD** (lspdd.org, Université de Sherbrooke) — measured SPDs for real
  commercial lamps. This is how you turn "LED, 3000 K" into a spectrum.
- **Illumina** (Aubé) — radiative transfer: inventory + SPD + terrain →
  modelled *spectral* sky brightness.

---

## 5. Suggested next steps

0. **Estimate CCT per geography from fixture inventories** — the biggest open
   task. Brief written up in `PROMPT_cct_task.md`; start a fresh chat with it.
1. **Join the collaborator's spectral data** to `city_summary.csv` on `city`.
   Colour the spread-vs-intensity scatter by CCT → extent, intensity and colour
   on one figure. Madrid-type cases then read as "dropped on the sensor but got
   bluer", which is the argument the whole project is built around.
2. **City click-through at native resolution.** The globe is ~4.9 km/px; HDNTL
   city rasters are **463 m**, daily, georeferenced, one band per night. A
   zoomable local map or a day-by-day metro animation is a big step up.
3. **Synthetic 2025 frame** from 12 monthly composites — label it clearly as a
   different product.
4. **Extend to all 653 cities** — ~2.5–3 hrs, mostly download (32.9 GB).
5. Skyglow ground measurement if the project wants *measured* rather than
   modelled colour: SQM (400–650 nm) + TESS-W (400–740 nm) run together give a
   cheap two-band colour index of the sky. Review: Hänel et al.,
   arXiv:1709.09558. Directly comparable prior work: JQSRT 2025,
   `sciencedirect.com/science/article/pii/S0022407325001128`.

---

## 6. Environment

- `venv/` — numpy, rasterio (GDAL 3.12), matplotlib, pandas, Pillow, scipy.
  Python 3.14. **System python has broken SSL certs — use the venv.**
- Reading remote COGs needs:
  `GDAL_DISABLE_READDIR_ON_OPEN=EMPTY_DIR CPL_VSIL_CURL_USE_HEAD=NO`
- No ffmpeg, no aws CLI, no brew.
- Disk: ~16 GB in the scratchpad. `hdntl/` 7.3 GB + the five city zips 7.1 GB
  are both redundant once the CSVs are built and can be deleted.

### Scripts

| Script | Does |
|---|---|
| `build_dataset.py` | HDNTL rasters → the 50-city tidy CSVs |
| `hdntl_series.py` | one city → daily CSV (optional boundary mask) |
| `philly_vnl.py` | annual VNL for any GeoJSON boundary, global |
| `globe_hi.py` | global rasters → equirect globe textures |
| `clean_render.py` | same, with aurora removed |
| `detect_aurora.py` | aurora mask + event catalogue |
| `plot_daily.py`, `starter_charts.py` | figures |
| `httpzip.py` | range-read one member out of a remote zip |
