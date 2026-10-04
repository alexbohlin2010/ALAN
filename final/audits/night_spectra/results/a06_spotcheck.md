# Human spot check, night spectra (RULES 3.2)

Random seed: **20261004** (python `random.Random(seed).sample(range(240*281), 10)` per site, philadelphia drawn first; cell = spectrum index * 281 + wavelength index). N = 20.

For each row open the raw CSV in `data/raw/spectra/spitschan2016/` (read only; it is transposed: one column per spectrum).
Go to the 1-based CSV column given, confirm that row 1 of that column shows the timestamp given, then read the cell at
the 1-based CSV row given (row = 6 + (wavelength - 280)). The output value should be the identical text
(W m^-2 nm^-1). Spectrum index is 0-based within the output's 240 spectra. Mark y if the text matches exactly.

| # | site | raw file | spectrum index | wavelength (nm) | output value | CSV row (1-based) | CSV column (1-based) | timestamp (row 1 of that column) | human match? (y/n) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | philadelphia | DRL_spectra.csv | 25 | 424 | 4.99887983e-07 | 150 | 306 | 06-Jul-2014 01:12:35 |y |
| 2 | philadelphia | DRL_spectra.csv | 59 | 348 | 1.089602644e-07 | 74 | 993 | 06-Jul-2014 22:57:52 | y|
| 3 | philadelphia | DRL_spectra.csv | 67 | 598 | 3.706590377e-06 | 324 | 1033 | 06-Jul-2014 23:37:52 | y|
| 4 | philadelphia | DRL_spectra.csv | 81 | 530 | 4.539125321e-07 | 256 | 1103 | 07-Jul-2014 01:15:11 |y |
| 5 | philadelphia | DRL_spectra.csv | 88 | 818 | 8.001562569e-06 | 544 | 1138 | 07-Jul-2014 01:50:11 |y |
| 6 | philadelphia | DRL_spectra.csv | 128 | 282 | 1.596359519e-07 | 8 | 1947 | 17-Jul-2014 00:01:37 |y |
| 7 | philadelphia | DRL_spectra.csv | 141 | 408 | 9.538334505e-07 | 134 | 2012 | 17-Jul-2014 01:06:37 | y|
| 8 | philadelphia | DRL_spectra.csv | 183 | 416 | 5.33325181e-07 | 142 | 2765 | 17-Jul-2014 23:10:03 |y |
| 9 | philadelphia | DRL_spectra.csv | 183 | 594 | 2.439335411e-06 | 320 | 2765 | 17-Jul-2014 23:10:03 | y|
| 10 | philadelphia | DRL_spectra.csv | 222 | 298 | 2.9075033e-08 | 24 | 2961 | 18-Jul-2014 02:26:03 | y|
| 11 | cherry_springs | CSSP_spectra.csv | 44 | 338 | 1.059876566e-08 | 64 | 455 | 01-Jul-2014 02:28:39 | y|
| 12 | cherry_springs | CSSP_spectra.csv | 83 | 644 | 9.42527192e-09 | 370 | 1077 | 02-Jul-2014 01:35:24 | y|
| 13 | cherry_springs | CSSP_spectra.csv | 88 | 534 | 8.92100067e-09 | 260 | 1104 | 02-Jul-2014 02:02:24 |y |
| 14 | cherry_springs | CSSP_spectra.csv | 97 | 334 | 7.86649526e-10 | 60 | 1151 | 02-Jul-2014 02:49:24 |y |
| 15 | cherry_springs | CSSP_spectra.csv | 99 | 768 | 1.489682525e-08 | 494 | 1162 | 02-Jul-2014 03:00:24 | y|
| 16 | cherry_springs | CSSP_spectra.csv | 116 | 346 | 0 | 72 | 1457 | 02-Jul-2014 23:30:33 |y |
| 17 | cherry_springs | CSSP_spectra.csv | 121 | 702 | 7.986187007e-09 | 428 | 1483 | 02-Jul-2014 23:56:33 | y|
| 18 | cherry_springs | CSSP_spectra.csv | 124 | 626 | 1.56673047e-08 | 352 | 1499 | 03-Jul-2014 00:12:33 |y |
| 19 | cherry_springs | CSSP_spectra.csv | 167 | 658 | 4.500595577e-07 | 384 | 2072 | 12-Jul-2014 22:59:01 | y|
| 20 | cherry_springs | CSSP_spectra.csv | 185 | 528 | 5.773104537e-09 | 254 | 2742 | 18-Jul-2014 23:06:16 |y |

Match rate: **20/20 (100 %)**, human-reported in chat 2026-10-04 ("20/20 matched"); recorded by the main session (AI_LOG round 3n); per-row y/n not given
