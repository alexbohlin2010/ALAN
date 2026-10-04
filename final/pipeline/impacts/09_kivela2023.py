"""Kivelä, Elgert, Lehtonen & Candolin 2023 (Lampyris noctiluca, study 243): the paper's reported results and the
deposited trap table, in one labelled file.

Run from final/:  python3 pipeline/impacts/09_kivela2023.py
Input:  data/raw/impacts/narrative of fireflies/Kivela_Elgert_Lehtonen_Candolin_2023_STOTEN_glowworm.pdf
        data/raw/impacts/narrative of fireflies/Data_Kivela2022.xlsx
        (both read-only; sha256 checked against data/raw/impacts/MANIFEST.csv). macOS (PDFKit via osascript).
Output: data/derived/impacts/kivela2023_pdftext.txt  page-marked text layer (gitignored; for audits)
        data/derived/impacts/kivela2023.json         `paper` (documented), `traps` (measured), `checks` (inferred)

Human decisions (AI_LOG Firefly tabs rounds 5a-5b): paper reported results + the deposited trap table, read by
script, shown as counts per trap, no new statistics; one file; impacts folders.

Rules (all deterministic):
- Text layer as in 08_owens2018.py ("=== page N ===", N = PDF page, 1-based). PDF page 1 is the repository cover
  page, so the journal's printed page = PDF page - 1. `page` fields below are PDF pages.
- The text layer drops the "fi"/"fl" ligatures ("arti cial" = "artificial"). Quotes are kept as in the text layer.
  Superscript exponents are flattened ("6.45 ∗ 1012" printed as 6.45 ∗ 10^12, checked on the rendered page by the
  agent, AI_LOG round 5c); values are written as numbers (6.45e12) with the printed text alongside.
- Table 1 (PDF p. 4): the four lines "NNN m.mm ∗ 10EE lux" in page order are blue, white, yellow, red (the order of
  the colour names on that page); control row "Control None None 0 0".
- Tables 2 and 4 (PDF p. 5): rows "A vs B <estimate> <z> <p>" (minus sign U+2212); the first 10 rows after the
  "Table 2" caption line (it shares a line with the running header) are Table 2, the 10 after "Table 4" are Table 4. Table 3: rows
  "<Treatment> <n0> <n≥1> <success> % <letter>".
- Statements: each quote must occur exactly once in the collapsed text of its page; numbers read by regex.
- Traps: every sheet row whose Color is blue/white/yellow/red/control (299 rows); the row with Color "NA" is kept
  under `traps_excluded` (all fields "NA" in the source); fully empty rows are skipped (counted). Cell text kept as
  stored; numbers parsed from it. The sheet's own variable table (columns K-M) is copied to `trap_variables`.
- Checks (`inferred`, inputs named in each): per treatment from the traps: n traps, sum of males, traps with 0 and
  ≥ 1 male, success % = 100 × n≥1 / n rounded to 1 decimal, median males; totals; Males_binary == (Males ≥ 1);
  Lux per treatment vs Table 1 (equal); Photons vs Table 1: within half a unit of the printed last digit (Table 1
  prints 3 significant digits, e.g. 1.27 ∗ 10^13 for the stored 12650000000000). Each check records the two values and whether they agree.
"""
import csv
import hashlib
import json
import re
import statistics
import subprocess
from pathlib import Path

from xlsx import read_first_sheet

RAW = Path('data/raw/impacts/narrative of fireflies')
PDF = RAW / 'Kivela_Elgert_Lehtonen_Candolin_2023_STOTEN_glowworm.pdf'
XLSX = RAW / 'Data_Kivela2022.xlsx'
MANIFEST = Path('data/raw/impacts/MANIFEST.csv')
TXT = Path('data/derived/impacts/kivela2023_pdftext.txt')
OUT = Path('data/derived/impacts/kivela2023.json')
CITATION = ('Kivelä L, Elgert C, Lehtonen TK, Candolin U (2023). The color of artificial light affects mate attraction '
            'in the common glow-worm. Science of the Total Environment 857: 159451')
DOI = 'https://doi.org/10.1016/j.scitotenv.2022.159451'
DATA_DOI = 'https://doi.org/10.7910/DVN/QWQPLJ'
COLOURS = ['blue', 'white', 'yellow', 'red']
TREATMENTS = ['control', 'blue', 'white', 'yellow', 'red']

JXA = r'''
ObjC.import('Foundation'); ObjC.import('PDFKit');
function run(argv) {
  var doc = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0]));
  var out = [];
  for (var i = 0; i < doc.pageCount; i++) {
    out.push('=== page ' + (i + 1) + ' ===');
    out.push(doc.pageAtIndex(i).string.js);
  }
  return out.join('\n');
}
'''

T1_RE = re.compile(r'^(\d{3}) (\d\.\d+) ∗ 10(\d{2}) (\d+\.\d)$')
PAIR_RE = re.compile(r'^(Blue|White|Yellow|Red) vs (control|blue|white|yellow)\s*(−?[\d.]+)\s*(−?[\d.]+)\s+(<?[\d.]+)$')
T3_RE = re.compile(r'^(Control|Blue|White|Yellow|Red) (\d+) (\d+) ([\d.]+) % ([AB])$')

# key -> (pdf page, verbatim text-layer quote, {field: (regex, unit)})
SCALARS = {
    'abstract_treatments': (2, 'Each dummy was illuminated from above by either a blue (peak wavelength: 452 nm), '
                               'white (449 nm), yellow (575 nm), or red (625 nm) LED lighting, or light switched off '
                               'in the control.',
                            {'blue_nm': (r'blue \(peak wavelength: (\d+) nm\)', 'nm'),
                             'white_nm': (r'white \((\d+) nm\)', 'nm'), 'yellow_nm': (r'yellow \((\d+) nm\)', 'nm'),
                             'red_nm': (r'red \((\d+) nm\)', 'nm')}),
    'abstract_result': (2, 'with short wavelengths (blue and white) decreasing it more than long wavelengths (yellow '
                           'and red).', {}),
    'site_and_dates': (3, 'All work was conducted in Southern Finland in the proximity of Tvärminne Zoological Station '
                          '(N 59°51′, E 23°14′), during the glow-worm breeding season, between 12th June and 4th July '
                          'in 2020.', {}),
    'nights': (3, 'The experiment was run only on nights of good weather (N = 20 nights)',
               {'n_nights': (r'N = (\d+) nights', 'nights')}),
    'dummy_led': (3, 'Its peak wavelength was 562 nm, which matches the glow of female glow-worms (550–570 nm)',
                  {'peak_nm': (r'was (\d+) nm', 'nm'), 'female_glow_from': (r'\((\d+)–', 'nm'),
                   'female_glow_to': (r'–(\d+) nm\)', 'nm')}),
    'dummy_intensity': (3, 'to adjust the intensity to 0.065–0.075 μWnm−1 (microwatts per nanometer)',
                        {'from': (r'to (0\.\d+)–', 'μW nm−1'), 'to': (r'–(0\.\d+) μW', 'μW nm−1')}),
    'light_heights': (4, 'the light sources were attached at the following heights above the ground: 100 cm (blue), '
                         '110 cm (yellow), 120 cm (white), and 120 cm (red)',
                      {'blue_cm': (r'(\d+) cm \(blue\)', 'cm'), 'yellow_cm': (r'(\d+) cm \(yellow\)', 'cm'),
                       'white_cm': (r'(\d+) cm \(white\)', 'cm'), 'red_cm': (r'(\d+) cm \(red\)', 'cm')}),
    'design': (4, 'We ran 3 repli- cates of each of the 5 treatments per night. Over the course of the exper- iment, we '
                  'completed 4 replicates of each treatment at each of the 15 sites. This resulted in 60 replicates '
                  'per treatment (over 20 nights), except for the yellow treatment, in which one replicate was '
                  'discarded due to battery failure.',
               {'replicates_per_treatment': (r'resulted in (\d+) replicates', 'replicates'),
                'sites': (r'each of the (\d+) sites', 'sites')}),
    'timing': (4, 'We activated the arti cial lights and dummy females each night be- tween 23:45 and 00:15 and turned '
                  'them off between 01:45 and 02:15.', {}),
    'recaptures': (4, 'recaptured males were not in- cluded in the data analyses', {}),
    'total_males': (4, 'The dummy females attracted a total of 624 male glow-worms during the experiment.',
                    {'males': (r'total of (\d+) male', 'males')}),
    'medians': (4, 'The median number of males attracted was two in the control, yel- low and red light treatments, '
                   'and zero in the blue and white light treat- ments (Fig. 2).', {}),
    'success_total': (4, 'Over the whole experiment, 56.9 % (170/299) of the dummy females attracted at least one male.',
                      {'percent': (r'([\d.]+) %', '%'), 'successes': (r'\((\d+)/', 'traps'),
                       'traps': (r'/(\d+)\)', 'traps')}),
    'count_result': (4, 'Dummy females in the blue and white light treatments attracted signi cantly fewer males than '
                        'dummy females in the yellow, red and control treatments (Fig. 2, Table 2).', {}),
    'fig2_n': (4, 'N = 60 in all treatments except N = 59 in the yellow light treatment.', {}),
}

NOT_REPORTED = [
    'Table S1, Fig. S1 (treatment spectra), Fig. S2: supplementary files, not in this PDF and not obtained. The paper '
    'gives peak wavelengths only, no spectra.',
    'Fig. 2 (box plots of males per trap): drawn only; the trap table holds the underlying counts.',
    'Which source row is the discarded yellow replicate: the paper says one yellow replicate was discarded (battery '
    'failure); the trap table has one row with every field "NA" (night 10, site 3). The file does not say they are '
    'the same row.',
    'Model estimates are on the model scale (link function not restated in the tables); kept as printed.',
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def manifest_sha(name):
    with MANIFEST.open() as f:
        return next(r['sha256'] for r in csv.DictReader(f) if r['filename'] == name)


def collapse(s):
    return re.sub(r'\s+', ' ', s).strip()


def num(s):
    s = s.replace('−', '-')
    return int(s) if re.fullmatch(r'-?\d+', s) else float(s)


def pdf_pages():
    r = subprocess.run(['osascript', '-l', 'JavaScript', '-e', JXA, str(PDF.resolve())],
                       check=True, capture_output=True, text=True)
    parts = re.split(r'^=== page (\d+) ===$', r.stdout, flags=re.M)
    return r.stdout, {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def table1(page):
    lines = [l.strip() for l in page.splitlines()]
    hits = [m for m in map(T1_RE.match, lines) if m]
    assert len(hits) == 4, [m.group(0) for m in hits]
    order = [l.split()[0].lower() for l in lines if l.split()[:1] in (['Blue'], ['White'], ['Yellow'], ['Red'])]
    assert order == COLOURS, order
    rows = []
    for colour, m in zip(COLOURS, hits):
        nm, mant, exp, lux = m.groups()
        rows.append({'treatment': colour, 'peak_nm': num(nm), 'photons_cm2_s': float(f'{mant}e{exp}'),
                     'lux': num(lux), 'printed': m.group(0), 'printed_as': f'{mant} ∗ 10^{exp}'})
    assert 'Control None None 0 0' in lines
    rows.append({'treatment': 'control', 'peak_nm': None, 'photons_cm2_s': 0, 'lux': 0,
                 'printed': 'Control None None 0 0', 'note': 'peak wavelength printed "None"'})
    return rows


def pairs(page, caption):
    lines = [l.strip() for l in page.splitlines()]
    start = next(i for i, l in enumerate(lines) if l == caption or l.endswith(' ' + caption))  # p. 5 header shares a line
    out = []
    for l in lines[start:]:
        m = PAIR_RE.match(l)
        if m:
            a, b, est, z, p = m.groups()
            out.append({'comparison': f'{a.lower()} vs {b}', 'estimate': num(est), 'z': num(z),
                        'p': num(p.lstrip('<')), 'p_comparator': '<' if p.startswith('<') else '=', 'printed': l})
        if len(out) == 10:
            return out
    raise AssertionError(caption)


def table3(page):
    out = []
    for l in page.splitlines():
        m = T3_RE.match(l.strip())
        if m:
            t, n0, n1, pct, letter = m.groups()
            out.append({'treatment': t.lower(), 'n_zero': num(n0), 'n_at_least_one': num(n1), 'success_percent': num(pct),
                        'letter': letter, 'printed': l.strip()})
    assert [r['treatment'] for r in out] == TREATMENTS, out
    return out


def scalars(pages):
    out = {}
    for key, (page, quote, fields) in SCALARS.items():
        assert collapse(pages[page]).count(quote) == 1, (key, page, quote)
        item = {'page': page, 'quote': quote, 'label': 'documented'}
        for f, (rx, unit) in fields.items():
            m = re.search(rx, quote)
            assert m, (key, f)
            item[f] = {'value': num(m.group(1)), 'unit': unit}
        out[key] = item
    return out


def traps():
    header, rows = read_first_sheet(XLSX)
    cols = header[:8]
    assert cols == ['Date', 'Testnight', 'Site', 'Color', 'Lux', 'Photons', 'Males', 'Males_binary'], cols
    kept, excluded, empty = [], [], 0
    for r in rows:
        cells = r[:8]
        if all(c is None for c in cells):
            empty += 1
            continue
        rec = dict(zip(cols, cells))
        if rec['Color'] in TREATMENTS:
            kept.append({'date': rec['Date'], 'night': num(rec['Testnight']), 'site': num(rec['Site']),
                         'treatment': rec['Color'], 'lux': num(rec['Lux']), 'photons_cm2_s': num(rec['Photons']),
                         'males': num(rec['Males']), 'males_binary': num(rec['Males_binary'])})
        else:
            excluded.append({**rec, 'reason': 'Color is not a treatment name in the source (all fields "NA")'})
    variables = [{'name': r[10], 'definition': r[11], 'unit': r[12]} for r in rows if r[10] is not None]
    return kept, excluded, empty, variables


def checks(trap_rows, t1, t3, sc):
    out = []

    def add(name, inputs, ours, theirs, agree=None):
        out.append({'check': name, 'inputs': inputs, 'from_traps': ours, 'paper': theirs,
                    'agree': ours == theirs if agree is None else agree})
    for t in TREATMENTS:
        rs = [r for r in trap_rows if r['treatment'] == t]
        males = [r['males'] for r in rs]
        p3 = next(r for r in t3 if r['treatment'] == t)
        n1 = sum(1 for m in males if m >= 1)
        add(f'{t}: traps with 0 males', 'traps; Table 3', len(rs) - n1, p3['n_zero'])
        add(f'{t}: traps with ≥ 1 male', 'traps; Table 3', n1, p3['n_at_least_one'])
        add(f'{t}: success %', 'traps (100 × n≥1 / n, 1 decimal); Table 3', round(100 * n1 / len(rs), 1),
            p3['success_percent'])
        add(f'{t}: males_binary equals males ≥ 1', 'traps', all(r['males_binary'] == (r['males'] >= 1) for r in rs), True)
        add(f'{t}: median males', 'traps; statement `medians`', statistics.median(males),
            0 if t in ('blue', 'white') else 2)
        if t != 'control':
            r1 = next(r for r in t1 if r['treatment'] == t)
            lux, ph = {r['lux'] for r in rs}, {r['photons_cm2_s'] for r in rs}
            add(f'{t}: lux', 'traps; Table 1', sorted(lux), [r1['lux']], lux == {r1['lux']})
            half = 0.5 * 10 ** (int(r1['printed_as'].split('^')[1]) - 2)   # half a unit of the printed 3rd digit
            add(f'{t}: photons/cm2/s (within half a unit of Table 1\'s last printed digit)', 'traps; Table 1',
                sorted(ph), [r1['photons_cm2_s']], len(ph) == 1 and abs(next(iter(ph)) - r1['photons_cm2_s']) <= half)
    add('total traps', 'traps; statement `success_total`', len(trap_rows), sc['success_total']['traps']['value'])
    add('traps with ≥ 1 male', 'traps; statement `success_total`', sum(r['males'] >= 1 for r in trap_rows),
        sc['success_total']['successes']['value'])
    add('total males', 'traps; statement `total_males`', sum(r['males'] for r in trap_rows),
        sc['total_males']['males']['value'])
    add('nights', 'traps; statement `nights`', len({r['night'] for r in trap_rows}), sc['nights']['n_nights']['value'])
    add('sites', 'traps; statement `design`', len({r['site'] for r in trap_rows}), sc['design']['sites']['value'])
    for c in COLOURS:
        add(f'{c}: abstract peak nm vs Table 1', 'statement `abstract_treatments`; Table 1',
            sc['abstract_treatments'][f'{c}_nm']['value'], next(r['peak_nm'] for r in t1 if r['treatment'] == c))
    return out


def main():
    for p in (PDF, XLSX):
        assert sha(p) == manifest_sha(p.name), f'{p.name} differs from MANIFEST'
    text, pages = pdf_pages()
    TXT.parent.mkdir(parents=True, exist_ok=True)
    TXT.write_text(text)
    assert sorted(pages) == list(range(1, 8)), sorted(pages)

    t1 = table1(pages[4])
    t2, t4 = pairs(pages[5], 'Table 2'), pairs(pages[5], 'Table 4')
    t3 = table3(pages[5])
    sc = scalars(pages)
    trap_rows, excluded, empty, variables = traps()
    ch = checks(trap_rows, t1, t3, sc)

    out = {
        'source': {'paper': {'citation': CITATION, 'doi': DOI, 'file': str(PDF), 'sha256': sha(PDF),
                             'licence': 'CC BY 4.0', 'note': 'Jukuri repository reprint; PDF page 1 is a cover page '
                             '(printed page = PDF page - 1)'},
                   'traps': {'citation': 'Kivelä L, Elgert C, Lehtonen TK, Candolin U. Replication data for: The color '
                             'of artificial light affects mate attraction in the common glow-worm. Harvard Dataverse',
                             'doi': DATA_DOI, 'file': str(XLSX), 'sha256': sha(XLSX), 'licence': 'CC0 1.0'}},
        'scope': 'The paper\'s reported results and the deposited trap table, copied as stored; no new statistics '
                 '(human decision, AI_LOG Firefly tabs round 5a).',
        'labels': {'paper': 'documented', 'traps': 'measured', 'trap_variables': 'documented', 'checks': 'inferred'},
        'label_notes': {
            'documented': f'{CITATION}, {DOI}; PDF page per item. trap_variables: the deposit\'s own variable table.',
            'measured': f'field counts and the treatment light values per trap, {DATA_DOI} (sheet 1, columns A-H)',
            'inferred': 'checks: rules in the script docstring; inputs named per check.',
        },
        'units': {'peak_nm': 'nm', 'photons_cm2_s': 'photons/cm2/s (Table 1 header "Photons/cm2/s")', 'lux': 'lux',
                  'males': 'number of males attracted (trapped) per dummy female per night (2 h)',
                  'males_binary': '1 = at least one male', 'success_percent': '% of traps with ≥ 1 male',
                  'night': 'Testnight (1-20)', 'site': 'Site ID (1-15)', 'date': 'as stored, e.g. "12.-13.6." (2020)'},
        'text_layer_notes': 'Quotes are as in the PDF text layer, which drops the fi/fl ligatures (e.g. "arti cial", '
                            '"signi cantly") and joins hyphenated line breaks with a space.',
        'paper': {
            'table1': {'page': 4, 'caption': 'Light treatment details. Light intensities were measured at the vertical '
                                             'level of the dummy female.', 'rows': t1},
            'table2': {'page': 5, 'caption': 'Estimates, z-values and p-values of pairwise treatment comparisons of '
                                             'numbers of attracted males using a negative binomial GLMM, with replicate '
                                             'night and site included as random factors.', 'rows': t2},
            'table3': {'page': 5, 'caption': 'Male attraction success of dummy females in the different light '
                                             'treatments. Treatments with a different letter (A or B) were '
                                             'significantly different from each other (logistic regression). N = 60 '
                                             'in all treatments except in the yellow-light treatment N = 59.',
                       'rows': t3},
            'table4': {'page': 5, 'caption': 'Estimates, z-values and p-values of a binomial GLMM assessing whether the '
                                             'dummy female attracted at least one male, with replicate night and site '
                                             'included as random factors.', 'rows': t4},
            'statements': sc,
        },
        'traps': trap_rows,
        'traps_excluded': excluded,
        'traps_empty_rows_skipped': empty,
        'trap_variables': variables,
        'checks': ch,
        'not_reported': NOT_REPORTED,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    bad = [c for c in ch if not c['agree']]
    print(f'{TXT}: {len(pages)} pages, {len(text)} characters')
    print(f'{OUT}: Table 1 {len(t1)}, Table 2 {len(t2)}, Table 3 {len(t3)}, Table 4 {len(t4)}, {len(sc)} statements, '
          f'{len(trap_rows)} traps (+{len(excluded)} excluded, {empty} empty rows), {len(ch)} checks, '
          f'{len(bad)} disagree')
    for c in bad:
        print('  disagree:', c)


if __name__ == '__main__':
    main()
