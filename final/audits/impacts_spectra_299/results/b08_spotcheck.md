# Human spot check sample, study 299 spectra (RULES 3.2)

Seed: **20261003** (python `random.Random`, `sample` of 4 indices per curve, curves in the order below). N = 24.
Source figure: `data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf`, page 3, Fig. 1. Axes: x Wavelength (nm) ticks 400/500/600/700; y Relative intensity ticks 0.00/0.25/0.50/0.75/1.00.
Check by hand: find the curve at the given wavelength in the figure and read its relative intensity (for the LED lines: the centre of the drawn line, not its edge). Tick = match within about 0.01 (one pixel of a normal zoom).

| # | curve | wavelength (nm) | value (JSON) | human match? (y/n) |
|---|---|---|---|---|
| 1 | cool white (LED) | 402 | 0.0 | |
| 2 | cool white (LED) | 414 | 0.0003 | |
| 3 | cool white (LED) | 573 | 0.1175 | |
| 4 | cool white (LED) | 712 | 0.0121 | |
| 5 | warm white (LED) | 473 | 0.0142 | |
| 6 | warm white (LED) | 547 | 0.0747 | |
| 7 | warm white (LED) | 654 | 0.1133 | |
| 8 | warm white (LED) | 668 | 0.0916 | |
| 9 | blue (LED) | 454 | 0.9246 | |
| 10 | blue (LED) | 598 | 0.0 | |
| 11 | blue (LED) | 664 | 0.0 | |
| 12 | blue (LED) | 717 | 0.0 | |
| 13 | amber (LED) | 409 | 0.0 | |
| 14 | amber (LED) | 426 | 0.0 | |
| 15 | amber (LED) | 552 | 0.0 | |
| 16 | amber (LED) | 740 | 0.0 | |
| 17 | red (LED) | 463 | 0.0 | |
| 18 | red (LED) | 592 | 0.0012 | |
| 19 | red (LED) | 643 | 0.352 | |
| 20 | red (LED) | 724 | 0.0005 | |
| 21 | P. scintillans sensitivity (white area, top edge) | 379 | 0.7281 | |
| 22 | P. scintillans sensitivity (white area, top edge) | 415 | 0.7929 | |
| 23 | P. scintillans sensitivity (white area, top edge) | 611 | 0.3827 | |
| 24 | P. scintillans sensitivity (white area, top edge) | 667 | 0.009 | |

Match rate: pending (human)
