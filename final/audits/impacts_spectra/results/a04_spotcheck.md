# Human spot check, study 278 spectra (RULES 3.2)

Random seed: **20261003** (python `random.Random(seed).sample`, 10 sample indices per curve, short drawn first). N = 20.

Compare each (wavelength, value) with S. Fig. 1 (page 1 of `data/raw/impacts/mice/Wang_2023_NeurobiolDis_study278_supplement_mmc1.pdf`):
find the wavelength on the x axis, read the height of the named curve (blue = short-lambda, magenta = long-lambda) on the y axis
(mW/m2 as printed). Value is read from a printed figure, so allow about +/-0.01 for eyeballing. Tick the row y if the curve passes through the point.

| # | curve | sample index | wavelength (nm) | value (mW/m2) | human match? (y/n) |
|---|---|---|---|---|---|
| 1 | short | 2 | 384.00 | 0.00062 | |
| 2 | short | 14 | 396.06 | 0.00096 | |
| 3 | short | 54 | 452.05 | 0.00919 | |
| 4 | short | 73 | 471.05 | 0.37855 | |
| 5 | short | 147 | 545.04 | 0.13968 | |
| 6 | short | 173 | 572.04 | 0.12134 | |
| 7 | short | 254 | 654.95 | 0.02256 | |
| 8 | short | 268 | 668.99 | 0.01690 | |
| 9 | short | 312 | 715.98 | 0.01502 | |
| 10 | short | 317 | 721.02 | 0.01415 | |
| 11 | long | 9 | 397.05 | 0.00026 | |
| 12 | long | 26 | 416.04 | 0.00113 | |
| 13 | long | 63 | 457.00 | 0.00798 | |
| 14 | long | 152 | 553.05 | 0.06474 | |
| 15 | long | 192 | 593.02 | 0.30876 | |
| 16 | long | 198 | 598.96 | 0.33293 | |
| 17 | long | 243 | 643.97 | 0.37580 | |
| 18 | long | 264 | 665.03 | 0.26144 | |
| 19 | long | 324 | 728.04 | 0.15374 | |
| 20 | long | 340 | 744.97 | 0.10006 | |

Match rate: pending (human)
