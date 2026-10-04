# Human spot check, Owens et al. 2018 results (RULES 3.2)

Random seed: **20261004** (python `random.Random(seed).sample(range(178), 20)`, sorted). Population: 178 values in fixed order (Table 1 cells, then Results-text p-values, then statement numbers).

For each row open the PDF `data/raw/impacts/narrative of fireflies/Owens_MeyerRochow_Yang_2018_PLoSONE_Aquatica_ficta.pdf`
(read only) at the page given and find the place described. The output value should equal the printed number
(Table 1: in that block and row, that column; JSON drops trailing zeros, e.g. printed 0.010 = 0.01, 54.00 = 54.0).
Mark y if it matches.

| # | population index | where | page | locate | field | output value | human match? (y/n) |
|---|---|---|---|---|---|---|---|
| 1 | 13 | Table 1 | 6 | dim block, row λ = 463 nm | flash_frequency sd | 15.02 | y|
| 2 | 24 | Table 1 | 6 | dim block, row λ = 515 nm | flash_intensity mean | 9879 | y|
| 3 | 32 | Table 1 | 6 | dim block, row λ = 533 nm | flash_intensity mean | 8584 | y|
| 4 | 37 | Table 1 | 6 | dim block, row λ = 533 nm | flash_frequency sd | 13.93 | y|
| 5 | 44 | Table 1 | 6 | dim block, row λ = 597 nm | flash_frequency mean | 44.89 | y|
| 6 | 45 | Table 1 | 6 | dim block, row λ = 597 nm | flash_frequency sd | 6.504 | y|
| 7 | 48 | Table 1 | 6 | dim block, row λ = 628 nm | flash_intensity mean | 6605 |y |
| 8 | 53 | Table 1 | 6 | dim block, row λ = 628 nm | flash_frequency sd | 17.28 | y|
| 9 | 54 | Table 1 | 6 | dim block, row λ = 628 nm | flash_frequency ratio_to_dark | 0.988 |y |
| 10 | 63 | Table 1 | 6 | dim block, row λ = 663 nm | flash_frequency p | 0.43 | y|
| 11 | 68 | Table 1 | 6 | bright block, row λ = 444 nm | flash_frequency mean | 14.44 | y|
| 12 | 70 | Table 1 | 6 | bright block, row λ = 444 nm | flash_frequency ratio_to_dark | 0.335 | y|
| 13 | 77 | Table 1 | 6 | bright block, row λ = 463 nm | flash_frequency sd | 11.29 | y|
| 14 | 92 | Table 1 | 6 | bright block, row λ = 515 nm | flash_frequency mean | 14.89 | y|
| 15 | 100 | Table 1 | 6 | bright block, row λ = 533 nm | flash_frequency mean | 27.11 | y|
| 16 | 101 | Table 1 | 6 | bright block, row λ = 533 nm | flash_frequency sd | 15.7 |y |
| 17 | 121 | Table 1 | 6 | bright block, row λ = 663 nm | flash_intensity sd | 3351 | y|
| 18 | 133 | Results text | 5-6 | dim flash_frequency, 444 nm | p (=) | 0.0042 | y|
| 19 | 152 | statement courtship_flash | 3 | quote: "periodic single yel- low-green flashes (peak wavelength: 565 nm; bandw…" | n (flashes or individuals (not stated)) | 6 |y |
| 20 | 171 | statement exposure_order_anova | 6 | quote: "number of previous exposures had a significant negative effect on flas…" | frequency_dim_chi2 (χ²) | 15.205 |y |

Match rate: **20/20 (100 %)**, human check (rows marked y by the human in this file; recorded by the agent, AI_LOG round 4h).
