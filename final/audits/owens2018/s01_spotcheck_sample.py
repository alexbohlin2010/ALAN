"""RULES 3.2: draw N = 20 random values from data/derived/impacts/owens2018_results.json for a HUMAN to compare with
the PDF by hand. Usage (from final/): python3 audits/owens2018/s01_spotcheck_sample.py [seed]
Writes audits/owens2018/results/s01_spotcheck.md (human column left empty). The agent does not perform or report the
human check.

Population (fixed order, then sampled without replacement): every Table 1 cell (16 rows x 8 numbers), every Results-
text p-value (20), every number read from a statement (statements.*.<field>.value)."""
import json
import random
import sys
from pathlib import Path

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261004
N = 20
SRC = Path('data/derived/impacts/owens2018_results.json')
OUT = Path('audits/owens2018/results/s01_spotcheck.md')

J = json.loads(SRC.read_text(), parse_float=str, parse_int=str)  # values as their literal text
pop = []
for r in J['table1']['rows']:
    for m in ('flash_intensity', 'flash_frequency'):
        for f in ('mean', 'sd', 'ratio_to_dark', 'p'):
            pop.append(('Table 1', '6', f"{r['exposure']} block, row λ = {r['wavelength_nm']} nm", f'{m} {f}', r[m][f]))
for t in J['text_p_values']:
    pop.append(('Results text', t['page'], f"{t['exposure']} {t['measure']}, {t['wavelength_nm']} nm",
                f"p ({t['comparator']})", t['p']))
for k, s in J['statements'].items():
    for f, v in s.items():
        if isinstance(v, dict) and 'value' in v:
            pop.append(('statement ' + k, s['page'], f'quote: "{s["quote"][:70]}…"', f"{f} ({v['unit']})", v['value']))

rng = random.Random(SEED)
pick = sorted(rng.sample(range(len(pop)), N))
L = ['# Human spot check, Owens et al. 2018 results (RULES 3.2)', '',
     f'Random seed: **{SEED}** (python `random.Random(seed).sample(range({len(pop)}), {N})`, sorted). '
     f'Population: {len(pop)} values in fixed order (Table 1 cells, then Results-text p-values, then statement numbers).', '',
     'For each row open the PDF `data/raw/impacts/narrative of fireflies/Owens_MeyerRochow_Yang_2018_PLoSONE_Aquatica_ficta.pdf`',
     '(read only) at the page given and find the place described. The output value should equal the printed number',
     '(Table 1: in that block and row, that column; JSON drops trailing zeros, e.g. printed 0.010 = 0.01, 54.00 = 54.0).',
     'Mark y if it matches.', '',
     '| # | population index | where | page | locate | field | output value | human match? (y/n) |',
     '|---|---|---|---|---|---|---|---|']
for n, i in enumerate(pick, 1):
    w, p, loc, f, v = pop[i]
    L.append(f'| {n} | {i} | {w} | {p} | {loc} | {f} | {v} | |')
L += ['', 'Match rate: pending (human)', '']
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text('\n'.join(L))
print('\n'.join(L))
