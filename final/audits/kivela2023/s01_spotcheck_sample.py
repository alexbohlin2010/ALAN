"""RULES 3.2: draw N = 20 random values from data/derived/impacts/kivela2023.json for a HUMAN to compare with the
sources by hand (10 from the paper, 10 trap rows). Usage (from final/): python3 audits/kivela2023/s01_spotcheck_sample.py [seed]
Writes audits/kivela2023/results/s01_spotcheck.md (human column left empty). The agent does not perform or report the
human check.

Paper population (fixed order): Table 1 numbers (peak_nm, photons, lux per row), Tables 2 and 4 (estimate, z, p per
row), Table 3 (n_zero, n_at_least_one, success_percent per row), statement numbers. Trap population: the 299 rows."""
import json
import random
import sys
from pathlib import Path

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 20261004
SRC = Path('data/derived/impacts/kivela2023.json')
OUT = Path('audits/kivela2023/results/s01_spotcheck.md')

J = json.loads(SRC.read_text(), parse_float=str, parse_int=str)
P = J['paper']
paper = []
for r in P['table1']['rows']:
    for f in ('peak_nm', 'photons_cm2_s', 'lux'):
        paper.append((f"Table 1 (PDF p. 4, printed p. 3), row {r['treatment']}", f, r.get('printed_as', r[f]) if f == 'photons_cm2_s' else r[f]))
for t in ('table2', 'table4'):
    for r in P[t]['rows']:
        for f in ('estimate', 'z', 'p'):
            v = ('<' if f == 'p' and r['p_comparator'] == '<' else '') + str(r[f])
            paper.append((f"{t.replace('table', 'Table ')} (PDF p. 5), row {r['comparison']}", f, v))
for r in P['table3']['rows']:
    for f in ('n_zero', 'n_at_least_one', 'success_percent'):
        paper.append((f"Table 3 (PDF p. 5), row {r['treatment']}", f, r[f]))
for k, s in P['statements'].items():
    for f, v in s.items():
        if isinstance(v, dict) and 'value' in v:
            paper.append((f"statement {k} (PDF p. {s['page']}): \"{s['quote'][:60]}…\"", f, v['value']))

rng = random.Random(SEED)
pp = sorted(rng.sample(range(len(paper)), 10))
tp = sorted(rng.sample(range(len(J['traps'])), 10))
L = ['# Human spot check, Kivelä et al. 2023 (RULES 3.2)', '',
     f'Random seed: **{SEED}** (python `random.Random(seed)`: first `.sample(range({len(paper)}), 10)` over paper values, '
     f'then `.sample(range({len(J["traps"])}), 10)` over trap rows; each sorted). N = 20.', '',
     '**Paper rows:** open `data/raw/impacts/narrative of fireflies/Kivela_Elgert_Lehtonen_Candolin_2023_STOTEN_glowworm.pdf`',
     '(read only; PDF page 1 is a cover page, so PDF page = printed page + 1). Photons are shown as printed (m ∗ 10^e).',
     'JSON drops trailing zeros (e.g. printed 5.0 = 5).', '',
     '| # | index | where | field | output value | human match? (y/n) |', '|---|---|---|---|---|---|']
for n, i in enumerate(pp, 1):
    w, f, v = paper[i]
    L.append(f'| {n} | {i} | {w} | {f} | {v} | |')
L += ['', '**Trap rows:** open `data/raw/impacts/narrative of fireflies/Data_Kivela2022.xlsx` (read only), sheet 1. Excel row = '
      'trap index + 2 for indices before 137, + 3 from 137 on (header row; the all-"NA" row is Excel row 139, '
      'excluded from `traps`). Check every field of that row.', '',
      '| # | trap index | Excel row | date | night | site | treatment | lux | photons | males | males_binary | human match? (y/n) |',
      '|---|---|---|---|---|---|---|---|---|---|---|---|']
for n, i in enumerate(tp, 11):
    t = J['traps'][i]
    row = i + 2 if i < 137 else i + 3
    L.append(f"| {n} | {i} | {row} | {t['date']} | {t['night']} | {t['site']} | {t['treatment']} | {t['lux']} | "
             f"{t['photons_cm2_s']} | {t['males']} | {t['males_binary']} | |")
L += ['', 'Match rate: pending (human)', '']
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text('\n'.join(L))
print('\n'.join(L))
