# Human spot check: radiance COGs + tiles (RULES §3.2)

Drawn 2026-10-03 by `audits/radiance/a05_spot_sample.py` with **seed 187824061** (numpy `default_rng`). Rerun: `.venv/bin/python audits/radiance/a05_spot_sample.py 187824061`.

The agent did **not** read raw values for these samples. The derived values listed are what the COGs and tiles claim; the human looks up the raw values and fills in the blank columns of `a05_spot_check_sample.csv`.

## Strata (agent's choice; can be changed)
- **A** (20) native pixels, uniform over the pixel grid, kept only if > 0 in either year
- **B** (5) native pixels, uniform over the whole pixel grid (mostly 0)
- **C** (5) native pixels, uniform over pixels that are −1.5 in either year
- **D** (5) level-8 tile pixels (2×2 native block), kept only if any pixel > 0 in either year

## Raw files (read-only)
- 2015: `data/raw/radiance/eog/VNL_v21_npp_2015_global_vcmslcfg_c202205302300.average_masked.dat.tif.gz`
- 2025: `data/raw/radiance/eog/VNL_npp_2025_global_vcmslcfg_v2_c202604011200.average_masked.dat.tif.gz`

## How to check one sample (suggested; from `final/`)
1. Raw value at (col, row), 0-based, without writing anything next to the raw file:
   `gdallocationinfo -valonly --config GDAL_PAM_ENABLED NO /vsigzip/<raw file> <col> <row>`
   (or in QGIS: Identify at the listed lon/lat, which is the pixel centre, EPSG:4326). Each call decompresses the file, so expect up to ~1 min per call.
2. Compare it with the COG value listed (should be identical).
3. Tile pixel: `gdallocationinfo -valonly <tile path> <px> <py>` prints R, G, B. R/G should equal the curve grey of the raw value: 0 if ≤ 0, else `round(255·interp(min(v, top), edges, cdf))` from `data/derived/radiance/curve/hist_eq_p9999.json`. Helper: `.venv/bin/python audits/radiance/curve_grey.py <v> [<v> ...]`. Reference: 0.5→46, 1→127, 2→184, 5→221, 10→236, 20→245, 50→253, ≥100→255.
4. For **D** (level 8): mean of the 4 raw pixels per year, leaving out −1.5 and counting other negatives as 0, then the curve. If all 4 are −1.5 the grey is 0 and the flag is set.
5. B flags: 1 = 2015 is −1.5 (all of the block), 2 = 2025 is −1.5, 4 = outside the raster; values add up.

Tile paths are relative to `data/derived/radiance/tiles/v1/`.

## Samples

| # | S | tile (level/x/y) | px,py | tile R/G/B | raw col,row | lon,lat (centre) | COG 2015 | COG 2025 |
|---|---|---|---|---|---|---|---|---|
| 1 | A | `9/237/50.webp` | 133,65 | 60/0/0 | 60805,12865 | 73.354169,21.395833 | 0.573735416 | 0 |
| 2 | A | `9/80/35.webp` | 172,144 | 0/68/0 | 20652,9104 | -93.949999,37.066666 | 0 | 0.616102993 |
| 3 | A | `9/276/41.webp` | 53,156 | 0/193/0 | 70709,10652 | 114.620836,30.616666 | 0 | 2.31972623 |
| 4 | A | `9/239/33.webp` | 251,134 | 0/132/0 | 61435,8582 | 75.979169,39.241666 | 0 | 1.0484947 |
| 5 | A | `9/95/29.webp` | 194,208 | 194/192/0 | 24514,7632 | -77.858333,43.200000 | 2.39063239 | 2.27351046 |
| 6 | A | `9/277/46.webp` | 229,162 | 165/241/0 | 71141,11938 | 116.420836,25.258333 | 1.5066551 | 13.9604416 |
| 7 | A | `9/122/89.webp` | 154,109 | 0/42/0 | 31386,22893 | -49.224999,-20.387501 | 0 | 0.480275214 |
| 8 | A | `9/238/40.webp` | 73,250 | 243/250/0 | 61001,10490 | 74.170835,31.291666 | 16.9669991 | 31.6501446 |
| 9 | A | `9/177/61.webp` | 23,62 | 0/65/0 | 45335,15678 | 8.895835,9.674999 | 0 | 0.601874948 |
| 10 | A | `9/100/31.webp` | 245,92 | 98/160/0 | 25845,8028 | -72.312499,41.550000 | 0.787293315 | 1.42238462 |
| 11 | A | `9/189/23.webp` | 2,93 | 134/199/0 | 48386,5981 | 21.608335,50.079166 | 1.06771636 | 2.61855888 |
| 12 | A | `9/86/34.webp` | 228,222 | 52/114/0 | 22244,8926 | -87.316666,37.808333 | 0.536655784 | 0.894322038 |
| 13 | A | `9/181/30.webp` | 61,164 | 163/192/0 | 46397,7844 | 13.320835,42.316666 | 1.47787917 | 2.26823521 |
| 14 | A | `9/190/13.webp` | 243,250 | 48/124/0 | 48883,3578 | 23.679168,60.091667 | 0.511587381 | 0.977027059 |
| 15 | A | `9/70/42.webp` | 216,161 | 209/217/0 | 18136,10913 | -104.433333,29.529166 | 3.36080194 | 4.24708319 |
| 16 | A | `9/241/44.webp` | 218,47 | 0/156/0 | 61914,11311 | 77.975002,27.870833 | 0 | 1.34463418 |
| 17 | A | `9/188/24.webp` | 173,212 | 56/129/0 | 48301,6356 | 21.254168,48.516666 | 0.556842864 | 1.02034199 |
| 18 | A | `9/223/48.webp` | 91,87 | 105/163/0 | 57179,12375 | 58.245835,23.437500 | 0.831649244 | 1.46856213 |
| 19 | A | `9/304/29.webp` | 75,42 | 19/72/0 | 77899,7466 | 144.579169,43.891666 | 0.31880796 | 0.635254204 |
| 20 | A | `9/187/22.webp` | 177,242 | 83/231/0 | 48049,5874 | 20.204168,50.525000 | 0.698448598 | 7.82691574 |
| 21 | B | `9/0/87.webp` | 232,184 | tile not written (pipeline skipped it as empty) | 232,22456 | -179.033333,-18.566667 | 0 | 0 |
| 22 | B | `9/165/110.webp` | 233,161 | tile not written (pipeline skipped it as empty) | 42473,28321 | -3.029165,-43.004168 | 0 | 0 |
| 23 | B | `9/132/22.webp` | 84,118 | tile not written (pipeline skipped it as empty) | 33876,5750 | -38.849999,51.041666 | 0 | 0 |
| 24 | B | `9/176/53.webp` | 79,97 | 0/0/0 | 45135,13665 | 8.062502,18.062500 | 0 | 0 |
| 25 | B | `9/113/80.webp` | 226,111 | 0/0/0 | 29154,20591 | -58.524999,-10.795834 | 0 | 0 |
| 26 | C | `9/33/131.webp` | 99,64 | 0/144/1 | 8547,33600 | -144.387500,-65.000001 | -1.5 | 1.18307698 |
| 27 | C | `9/29/131.webp` | 52,64 | 0/150/1 | 7476,33600 | -148.850000,-65.000001 | -1.5 | 1.2635715 |
| 28 | C | `9/19/131.webp` | 61,64 | 0/186/1 | 4925,33600 | -159.479167,-65.000001 | -1.5 | 2.04172421 |
| 29 | C | `9/315/131.webp` | 92,64 | 0/80/1 | 80732,33600 | 156.383336,-65.000001 | -1.5 | 0.682432413 |
| 30 | C | `9/303/131.webp` | 212,64 | 0/71/1 | 77780,33600 | 144.083336,-65.000001 | -1.5 | 0.629999995 |
| 31 | D | `8/101/11.webp` | 185,85 | 119/20/0 | 52082,5802<br>52083,5802<br>52082,5803<br>52083,5803 | 37.008335,50.825000<br>37.012502,50.825000<br>37.008335,50.820833<br>37.012502,50.820833 | 1.12559438<br>1.10012853<br>0.758119941<br>0.764061511 | 0.654999971<br>0.647962928<br>0<br>0 |
| 32 | D | `8/137/24.webp` | 146,21 | 7/174/0 | 70436,12330<br>70437,12330<br>70436,12331<br>70437,12331 | 113.483336,23.625000<br>113.487502,23.625000<br>113.483336,23.620833<br>113.487502,23.620833 | 0<br>0<br>0.801030219<br>0 | 1.60385716<br>1.59085715<br>1.86916649<br>1.77814293 |
| 33 | D | `8/39/13.webp` | 144,250 | 3/0/0 | 20256,7156<br>20257,7156<br>20256,7157<br>20257,7157 | -95.599999,45.183333<br>-95.595833,45.183333<br>-95.599999,45.179166<br>-95.595833,45.179166 | 0.295916885<br>0<br>0.297222614<br>0 | 0<br>0<br>0<br>0 |
| 34 | D | `8/91/7.webp` | 217,116 | 0/4/0 | 47026,3816<br>47027,3816<br>47026,3817<br>47027,3817 | 15.941668,59.100000<br>15.945835,59.100000<br>15.941668,59.095833<br>15.945835,59.095833 | 0<br>0<br>0<br>0 | 0<br>0<br>0.661363602<br>0 |
| 35 | D | `8/47/12.webp` | 101,121 | 0/13/0 | 24266,6386<br>24267,6386<br>24266,6387<br>24267,6387 | -78.891666,48.391666<br>-78.887499,48.391666<br>-78.891666,48.387500<br>-78.887499,48.387500 | 0<br>0<br>0<br>0 | 0.512597442<br>0<br>0.537671208<br>0 |

## Human results
Fill in `a05_spot_check_sample.csv` (columns `human_*`). Match rate = samples where every check matched / samples checked. Recorded by the human, not by an agent.

- Checked by: 
- Date: 
- Samples checked: 
- Matches: 
- Match rate: 
- Notes: 
