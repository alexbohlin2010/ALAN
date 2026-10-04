# Human spot check, Kivelä et al. 2023 (RULES 3.2)

Random seed: **20261004** (python `random.Random(seed)`: first `.sample(range(110), 10)` over paper values, then `.sample(range(299), 10)` over trap rows; each sorted). N = 20.

**Paper rows:** open `data/raw/impacts/narrative of fireflies/Kivela_Elgert_Lehtonen_Candolin_2023_STOTEN_glowworm.pdf`
(read only; PDF page 1 is a cover page, so PDF page = printed page + 1). Photons are shown as printed (m ∗ 10^e).
JSON drops trailing zeros (e.g. printed 5.0 = 5).

| # | index | where | field | output value | human match? (y/n) |
|---|---|---|---|---|---|
| 1 | 6 | Table 1 (PDF p. 4, printed p. 3), row yellow | peak_nm | 575 | |
| 2 | 22 | Table 2 (PDF p. 5), row yellow vs control | z | -1.157 | |
| 3 | 24 | Table 2 (PDF p. 5), row red vs control | estimate | -0.049 | |
| 4 | 35 | Table 2 (PDF p. 5), row red vs blue | p | <0.001 | |
| 5 | 38 | Table 2 (PDF p. 5), row yellow vs white | p | <0.001 | |
| 6 | 50 | Table 4 (PDF p. 5), row white vs control | p | <0.001 | |
| 7 | 66 | Table 4 (PDF p. 5), row yellow vs white | estimate | 1.653 | |
| 8 | 95 | statement dummy_led (PDF p. 3): "Its peak wavelength was 562 nm, which matches the glow of fe…" | peak_nm | 562 | |
| 9 | 96 | statement dummy_led (PDF p. 3): "Its peak wavelength was 562 nm, which matches the glow of fe…" | female_glow_from | 550 | |
| 10 | 105 | statement design (PDF p. 4): "We ran 3 repli- cates of each of the 5 treatments per night.…" | sites | 15 | |

**Trap rows:** open `data/raw/impacts/narrative of fireflies/Data_Kivela2022.xlsx` (read only), sheet 1. Excel row = trap index + 2 for indices before 137, + 3 from 137 on (header row; the all-"NA" row is Excel row 139, excluded from `traps`). Check every field of that row.

| # | trap index | Excel row | date | night | site | treatment | lux | photons | males | males_binary | human match? (y/n) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 48 | 50 | 15.-16.6. | 4 | 4 | white | 5.6 | 5272000000000 | 1 | 1 | |
| 12 | 64 | 66 | 16.-17.6. | 5 | 5 | control | 0 | 0 | 5 | 1 | |
| 13 | 74 | 76 | 16.-17.6. | 5 | 15 | control | 0 | 0 | 0 | 0 | |
| 14 | 91 | 93 | 18.-19.6. | 7 | 2 | yellow | 6 | 4214000000000 | 4 | 1 | |
| 15 | 106 | 108 | 19.-20.6. | 8 | 2 | control | 0 | 0 | 10 | 1 | |
| 16 | 109 | 111 | 19.-20.6. | 8 | 5 | red | 8 | 12650000000000 | 14 | 1 | |
| 17 | 127 | 129 | 20.-21.6. | 9 | 8 | red | 8 | 12650000000000 | 10 | 1 | |
| 18 | 184 | 187 | 24.-25.6. | 13 | 6 | blue | 5 | 6448000000000 | 1 | 1 | |
| 19 | 201 | 204 | 25.-26.6. | 14 | 8 | blue | 5 | 6448000000000 | 1 | 1 | |
| 20 | 243 | 246 | 29.-30.6. | 17 | 5 | yellow | 6 | 4214000000000 | 2 | 1 | |

Match rate: **20/20 (100 %)**, human check (reported by the human in chat, AI_LOG round 5g; per-row marks not entered in this file).
