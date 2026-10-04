"""Owens, Meyer-Rochow & Yang 2018 (Aquatica ficta): the paper's reported results, read from the PDF text.

Run from final/:  python3 pipeline/impacts/08_owens2018.py
Input:  data/raw/impacts/narrative of fireflies/Owens_MeyerRochow_Yang_2018_PLoSONE_Aquatica_ficta.pdf
        (read-only; MANIFEST.csv row, sha256 checked below). Needs macOS (PDFKit via `osascript -l JavaScript`).
Output: data/derived/impacts/owens2018_pdftext.txt   page-marked text layer (gitignored; for audits)
        data/derived/impacts/owens2018_results.json  the labelled results

Human decisions (AI_LOG rounds 4a-4b): reported results only, no re-analysis of the raw recordings in
data/raw/impacts/narrative of fireflies/Aquatica_ficta/; script and outputs in the impacts folders; the
PDF text is saved but not committed.

Rules (all deterministic):
- Text layer: PDFKit `PDFPage.string`, page by page, a "=== page N ===" line before each page (N 1-based).
  Nothing else is changed in the saved text. For matching, runs of whitespace are collapsed to one space.
- Table 1 (page 6): the 16 data lines (8 under "Dim (1×) Exposure", 8 under "Bright (10×) Exposure") must
  each match ROW_RE; the same 8 wavelengths must appear in both blocks. Each row keeps its line as printed.
- Results text (pages 5-6): the four p-value lists are cut between fixed anchor phrases (P_LISTS); Table 1's
  block (from "Table 1." to the line ending "t001") and the page headers/footers are removed first, because
  the third list runs across the page break and the table. Each "NNN nm: p = x" / "p < x" is read by P_RE;
  each list must give the five wavelengths 444, 463, 488, 515, 533. `page` per value = the page holding the
  matched "NNN nm: p … x" text (5 or 6); "5-6" only if the match runs across the page break.
- Single statements (SCALARS): each quote must occur exactly once in the collapsed text of the stated page;
  numbers are read from the quote by the given regex.
- Glyphs: the text layer drops "≤" and "≥" (checked: absent, not mapped to other code points). Where a quote
  loses one, `as_printed` gives the phrase as it appears on the rendered page (checked by eye by the agent on
  a PDFKit render, AI_LOG round 4c) and `glyph_from_rendered_page` is true.
- Text vs Table 1 (`inferred`): for each Results p-value, the Table 1 p for the same exposure, measure and
  wavelength; "=" agrees if the two numbers are equal, "<" agrees if the table number is below the bound.
  Disagreements are listed, not resolved.

Labels: every number and statement from the paper is `documented` (citation + page). The text-vs-table
comparison is `inferred`. Nothing is estimated; gaps are listed under `not_reported`.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

SRC = Path('data/raw/impacts/narrative of fireflies/Owens_MeyerRochow_Yang_2018_PLoSONE_Aquatica_ficta.pdf')
SRC_SHA256 = '9272dd5507fd51ea34a9f42d7e2e7e71c9082d08aca4ce4ea06f7e0f36d5f51a'  # MANIFEST.csv
TXT = Path('data/derived/impacts/owens2018_pdftext.txt')
OUT = Path('data/derived/impacts/owens2018_results.json')
CITATION = ('Owens ACS, Meyer-Rochow VB, Yang E-C (2018). Short- and mid-wavelength artificial light influences '
            'the flash signals of Aquatica ficta fireflies (Coleoptera: Lampyridae). PLoS ONE 13(2): e0191576')
DOI = 'https://doi.org/10.1371/journal.pone.0191576'

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

ROW_RE = re.compile(r'^(\d{3}) (\d+) ±(\d+) ([\d.]+) ([\d.]+) ([\d.]+) ±([\d.]+) ([\d.]+) ([\d.]+)$')
P_RE = re.compile(r'(\d{3})\s*nm:\s*p\s*(?:=\s*p\s*)?(=|<)\s*([\d.]+)')
SHORT_MID = [444, 463, 488, 515, 533]

# (exposure, measure, start anchor, end anchor), all on pages 5-6 of the Results.
P_LISTS = [
    ('dim', 'flash_intensity', 'exposed to dim intensities of short- and mid-wavelength light',
     'Increases in flash intensity under dim'),
    ('dim', 'flash_frequency', 'significant reductions in flash frequency', 'The decline is due'),
    ('bright', 'flash_frequency', 'exposed to bright intensities of the same wavelengths', 'In fact, under bright'),
    ('bright', 'flash_intensity', 'became erratic under bright short- and mid-wavelength illumination',
     'Notably,'),
]

# key -> (page, verbatim quote from the text layer, {field: (regex, unit)}, as_printed or None)
SCALARS = {
    'species': (3, 'Three male A. fictafireflies were collected three times from Yongjian Eco Park', {}, None),
    'collection_site': (3, 'Yongjian Eco Park (24.990195, 121.555824; May 4, May 7, and May 11, 2016)',
                        {'latitude': (r'\((24\.\d+),', 'degrees (as printed)'),
                         'longitude': (r', (121\.\d+);', 'degrees (as printed)')}, None),
    'courtship_flash': (3, 'periodic single yel- low-green flashes (peak wavelength: 565 nm; bandwidth: 60 nm; n = 6)',
                        {'peak_wavelength': (r'peak wavelength: (\d+) nm', 'nm'),
                         'bandwidth': (r'bandwidth: (\d+) nm', 'nm'),
                         'n': (r'n = (\d+)', 'flashes or individuals (not stated)')}, None),
    'alarm_flash': (4, 'fast (approx. 200 ms duration, 200–300 ms flash interval) alarm flashes',
                    {'duration_approx': (r'approx\. (\d+) ms duration', 'ms')}, None),
    'recorded_band': (4, 'average relative intensity (counts) of wavelengths from 565 nm to 569 nm over 32 min',
                      {'from': (r'from (\d+) nm', 'nm'), 'to': (r'to (\d+) nm', 'nm')}, None),
    'sampling': (4, 'Averages were calculated and saved every 100 ms.', {'interval': (r'every (\d+) ms', 'ms')}, None),
    'leds': (3, 'Puck wavelengths were semi-evenly distributed across a range from near-UV to red (444 nm to 663 nm)',
             {}, None),
    'exposure_protocol': (4, 'exposures lasted 1 min and were always preceded by 1 min dark recordings', {}, None),
    'dim_bright_flux': (4, 'ranging from 0.107 ±0.02 μmol m-2 s-1 and from 1.075 ±0.212 μmol m-2 s-1 for dim and '
                           'bright exposures, respectively',
                        {'dim': (r'from (0\.107) ±', 'μmol m-2 s-1'), 'dim_pm': (r'0\.107 ±([\d.]+)', 'μmol m-2 s-1'),
                         'bright': (r'from (1\.075) ±', 'μmol m-2 s-1'),
                         'bright_pm': (r'1\.075 ±([\d.]+)', 'μmol m-2 s-1')}, None),
    'dim_bright_lux': (8, '1×and 10×exposures roughly correspond to 20 and 200 lux, respectively, although '
                          'photometric units are not suited to the analysis of monochro- matic light',
                       {'dim': (r'correspond to (\d+) and', 'lux (rough)'),
                        'bright': (r'and (\d+) lux', 'lux (rough)')}, None),
    'sample': (4, 'Eight sets of data were collected from eight A. fictamales on the evenings of May 5–9 and May '
                  '12–14, 2016 (S2 Fig; one male died before it could be tested). Of these, two recordings (May 5 '
                  'and May 13) were disregarded', {}, None),
    'n_analysed': (4, 'Flash intensity and frequency data from six individuals', {}, None),
    'noise_threshold': (4, 'Measurements 200 counts were excluded as noise',
                        {'threshold': (r'Measurements (\d+) counts', 'counts')},
                        'Measurements ≤ 200 counts were excluded as noise'),
    'adaptation': (4, 'The first 15 s of each recording was defined as the “adapta- tion period”', {}, None),
    'model': (4, 'Average flash intensity and frequency under each wavelength of exposure was compared using '
                 'generalized linear mixed models (GLMM)', {}, None),
    'baseline_table1': (6, '(average flash intensity: 5420 counts; frequency: 43.167 peaks/min)',
                        {'flash_intensity': (r'intensity: (\d+) counts', 'counts'),
                         'flash_frequency': (r'frequency: ([\d.]+) peaks/min', 'peaks/min')}, None),
    'baseline_fig2': (7, 'Base values for average flash intensity (5420 counts) and flash frequency (43.167 '
                         'peaks/min) obtained from 1 min dark recordings',
                      {'flash_intensity': (r'\((\d+) counts\)', 'counts'),
                       'flash_frequency': (r'\(([\d.]+) peaks/min\)', 'peaks/min')}, None),
    'fig2_error_bars': (7, 'Change in average (±1 SE) flash intensity (A) and frequency (B)', {}, None),
    'abstract_short_mid': (1, 'When exposed to wavelengths at or below 533 nm, males emitted brighter signals with '
                              'decreased frequency.', {'wavelength_bound': (r'at or below (\d+) nm', 'nm')}, None),
    'abstract_long': (1, 'long wavelength ambient light ( 597 nm) did not affect signal morphology',
                      {'wavelength_bound': (r'\( (\d+) nm\)', 'nm')},
                      'long wavelength ambient light (≥ 597 nm) did not affect signal morphology'),
    'exposure_order_models': (5, 'Exposure order explained a large amount of observed variation in flash frequency. '
                                 'However, it did not have an observable impact on flash intensity and was '
                                 'subsequently dropped from that set of models.', {}, None),
    'frequency_decline_cause': (5, 'The decline is due to increases in interpulse interval [58] and, to a lesser '
                                   'extent, flash duration (S2 Table)', {}, None),
    'pauses': (5, 'sporadic periods without flashing were more common under illumination, sometimes continuing for '
                  '10 or more seconds', {'pause_at_least': (r'continuing for (\d+) or more seconds', 's')}, None),
    'intensity_increase': (5, 'average peak inten- sity of flash signals significantly increased, sometimes more '
                              'than 100%, when individuals were exposed to dim intensities of short- and '
                              'mid-wavelength light', {}, None),
    'ceased_signalling': (6, 'under bright short- and mid-wavelength illumination, three of six males ceased '
                             'signaling entirely', {}, None),
    'long_wavelength_no_effect': (6, 'neither dim nor bright intensities of long wavelength ( 597 nm) illumination '
                                     'had a signifi- cant effect on flash intensity or frequency (p 0.3 in all '
                                     'instances; Fig 2)',
                                  {'wavelength_bound': (r'\( (\d+) nm\)', 'nm'),
                                   'p_bound': (r'\(p ([\d.]+) in all', 'p')},
                                  'neither dim nor bright intensities of long wavelength (≥ 597 nm) illumination '
                                  'had a signifi- cant effect on flash intensity or frequency (p ≥ 0.3 in all '
                                  'instances; Fig 2)'),
    'exposure_order_anova': (6, 'number of previous exposures had a significant negative effect on flash frequency '
                                '(1×: p <0.0001, χ2 = 15.205; 10×: p = 0.0012, χ2 = 14.668), but not flash intensity '
                                '(p = 1.0 and χ2 = 0 in both 1×and 10×models)',
                             {'frequency_dim_p_below': (r'1×: p <([\d.]+)', 'p'),
                              'frequency_dim_chi2': (r'1×: p <[\d.]+, χ2 = ([\d.]+)', 'χ²'),
                              'frequency_bright_p': (r'10×: p = ([\d.]+)', 'p'),
                              'frequency_bright_chi2': (r'10×: p = [\d.]+, χ2 = ([\d.]+)', 'χ²'),
                              'intensity_p': (r'not flash intensity \(p = ([\d.]+)', 'p'),
                              'intensity_chi2': (r'and χ2 = (\d+) in both', 'χ²')}, None),
    'intensity_frequency_correlation': (8, 'this potentially beneficial behavior may require some decrease in '
                                           'average flash frequency [correlation coefficient: -0.9655009 (1×), '
                                           '-0.8027756 (10×)]',
                                        {'dim': (r'coefficient: (-[\d.]+) \(1×\)', 'r (type not stated)'),
                                         'bright': (r'(-[\d.]+) \(10×\)', 'r (type not stated)')}, None),
    'half_stopped_bright': (8, 'half of the A. fictaspecimens stopped flashing under bright (10×) exposures', {},
                            None),
    'red_not_responsive': (6, 'Our results suggest that A. fictais not visually responsive to red wavelengths.', {},
                           None),
    'recommendation': (9, 'Our results suggest artificial light sources emitting the majority of their light in '
                          'wavelengths 597 nm, including a range of yellow to red wavelengths visible to humans, '
                          'would be most suitable for A. fictahabitats.', {},
                       'Our results suggest artificial light sources emitting the majority of their light in '
                       'wavelengths ≥ 597 nm, including a range of yellow to red wavelengths visible to humans, '
                       'would be most suitable for A. fictahabitats.'),
}

NOT_REPORTED = [
    'Per-male values: the paper gives means ± SD (Table 1), not the individual values.',
    'Fig 1 (p. 5): example recordings of two males (counts per 100 ms over 4 min; dark / dim / bright 533 nm); '
    'drawn only, not digitised (not requested).',
    'Fig 2 means and SE: drawn only (bars, ±1 SE); no numbers in the text. Not digitised (not requested).',
    'S1 Table (exposure sequence, μW/cm2), S2 Table (flash duration, interpulse interval), S1 Text, S1-S2 Fig: '
    'separate supplementary files, not in this PDF and not obtained.',
    'Bold p-values in Table 1: the rendered page shows some p-values in bold; the text layer carries no bold and '
    'the paper does not state what bold means. Not recorded.',
    'What "±" means for the dim/bright photon flux (SD or other) is not stated.',
    'Table 1 headers read "degree of change relative to dark (bright/dark)" in both the dim and the bright block, '
    'as printed.',
    'The correlation coefficients (p. 8) do not say which correlation statistic or which variables per se; '
    'kept as the quote.',
]


def pdf_text():
    r = subprocess.run(['osascript', '-l', 'JavaScript', '-e', JXA, str(SRC.resolve())],
                       check=True, capture_output=True, text=True)
    return r.stdout


def collapse(s):
    return re.sub(r'\s+', ' ', s).strip()


def split_pages(text):
    parts = re.split(r'^=== page (\d+) ===$', text, flags=re.M)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def num(s):
    return int(s) if re.fullmatch(r'-?\d+', s) else float(s)


def table1(page6):
    rows, block = [], None
    for line in page6.splitlines():
        line = line.strip()
        if line == 'Dim (1×) Exposure':
            block = 'dim'
        elif line == 'Bright (10×) Exposure':
            block = 'bright'
        m = ROW_RE.match(line)
        if m and block:
            g = m.groups()
            rows.append({
                'exposure': block,
                'wavelength_nm': num(g[0]),
                'flash_intensity': {'mean': num(g[1]), 'sd': num(g[2]), 'ratio_to_dark': num(g[3]), 'p': num(g[4])},
                'flash_frequency': {'mean': num(g[5]), 'sd': num(g[6]), 'ratio_to_dark': num(g[7]), 'p': num(g[8])},
                'printed': line,
            })
    dim = [r['wavelength_nm'] for r in rows if r['exposure'] == 'dim']
    bright = [r['wavelength_nm'] for r in rows if r['exposure'] == 'bright']
    assert len(dim) == 8 and dim == bright, (dim, bright)
    return rows


def results_text(pages):
    """Pages 5-6 without headers/footers and without the Table 1 block, whitespace collapsed.
    Returns (text, offset where page 6 starts in text)."""
    parts = []
    for n in (5, 6):
        keep, in_table = [], False
        for line in pages[n].splitlines():
            if line.startswith('Table 1.'):
                in_table = True
            if in_table:
                if line.rstrip().endswith('t001'):
                    in_table = False
                continue
            if line.startswith('PLOS ONE |') or line == 'Fireflies flash more brightly in illuminated environs':
                continue
            keep.append(line)
        parts.append(collapse('\n'.join(keep)))
    return parts[0] + ' ' + parts[1], len(parts[0]) + 1


def p_lists(res, p6):
    out = []
    for exposure, measure, a, b in P_LISTS:
        assert res.count(a) == 1 and res.count(b) == 1, (a, b)
        start = res.index(a) + len(a)
        found = list(P_RE.finditer(res, start, res.index(b)))
        assert [int(m.group(1)) for m in found] == SHORT_MID, (exposure, measure, [m.group(0) for m in found])
        for m in found:
            page = 6 if m.start() >= p6 else 5 if m.end() <= p6 else '5-6'
            out.append({'exposure': exposure, 'measure': measure, 'wavelength_nm': int(m.group(1)),
                        'comparator': m.group(2), 'p': num(m.group(3)), 'printed': m.group(0), 'page': page})
    return out


def compare(text_ps, rows):
    out = []
    for t in text_ps:
        row = next(r for r in rows if r['exposure'] == t['exposure'] and r['wavelength_nm'] == t['wavelength_nm'])
        tp = row[t['measure']]['p']
        agree = (tp == t['p']) if t['comparator'] == '=' else (tp < t['p'])
        out.append({'exposure': t['exposure'], 'measure': t['measure'], 'wavelength_nm': t['wavelength_nm'],
                    'text': f"p {t['comparator']} {t['p']}", 'table1_p': tp, 'agree': agree})
    return out


def scalars(pages):
    out = {}
    for key, (page, quote, fields, as_printed) in SCALARS.items():
        hay = collapse(pages[page])
        assert hay.count(quote) == 1, (key, page, quote)
        item = {'page': page, 'quote': quote, 'label': 'documented'}
        if as_printed:
            item['as_printed'] = as_printed
            item['glyph_from_rendered_page'] = True
        for f, (rx, unit) in fields.items():
            m = re.search(rx, quote)
            assert m, (key, f)
            item[f] = {'value': num(m.group(1)), 'unit': unit}
        out[key] = item
    return out


def main():
    assert hashlib.sha256(SRC.read_bytes()).hexdigest() == SRC_SHA256, 'raw PDF differs from MANIFEST'
    text = pdf_text()
    TXT.parent.mkdir(parents=True, exist_ok=True)
    TXT.write_text(text)
    pages = split_pages(text)
    assert sorted(pages) == list(range(1, 15)), sorted(pages)

    rows = table1(pages[6])
    text_ps = p_lists(*results_text(pages))
    checks = compare(text_ps, rows)
    sc = scalars(pages)
    b1, b2 = sc['baseline_table1'], sc['baseline_fig2']
    assert all(b1[k]['value'] == b2[k]['value'] for k in ('flash_intensity', 'flash_frequency'))

    out = {
        'source': {'citation': CITATION, 'doi': DOI, 'file': str(SRC), 'sha256': SRC_SHA256,
                   'licence': 'CC BY 4.0', 'pages': 14},
        'scope': 'Reported results of the paper only; no re-analysis of the raw recordings (human decision, '
                 'AI_LOG round 4a). Values are copied as printed.',
        'labels': {'table1': 'documented', 'text_p_values': 'documented', 'statements': 'documented',
                   'text_vs_table1': 'inferred'},
        'label_notes': {
            'documented': f'{CITATION}, {DOI}; page given per item.',
            'inferred': 'text_vs_table1: rule in pipeline/impacts/08_owens2018.py docstring; inputs = '
                        'text_p_values and table1.',
        },
        'units': {
            'flash_intensity': 'counts (spectrometer, average relative intensity 565-569 nm per 100 ms; average '
                               'peak intensity per 1 min recording, first 15 s omitted)',
            'flash_frequency': 'peaks/min',
            'ratio_to_dark': 'Table 1 "degree of change relative to dark": mean divided by the 1 min dark base '
                             'value (5420 counts; 43.167 peaks/min)',
            'sd': 'standard deviation, as printed ("x̄ ± SD" in the Table 1 header); Fig 2 caption: N = 6',
            'p': 'Table 1 "p-value" column, as printed. The table does not name the test; the Methods (p. 4) '
                 'compare intensity and frequency per wavelength with GLMMs, dim and bright analysed separately',
            'wavelength_nm': 'LED peak wavelength, nm',
            'exposure': 'dim = 1×, bright = 10× quantum flux (see statements.dim_bright_flux)',
        },
        'table1': {'page': 6, 'caption': 'Table 1. Average peak intensity and frequency of light signals produced '
                                         'by A. ficta under exposure to varying wavelengths and intensities of '
                                         'ambient light.',
                   'columns_printed': 'λ (nm) | flash intensity x̄ ± SD (counts) | degree of change relative to dark '
                                      '(bright/dark) | p-value | flash frequency x̄ ± SD (peaks/min) | degree of '
                                      'change relative to dark (bright/dark) | p-value',
                   'rows': rows},
        'text_p_values': text_ps,
        'text_vs_table1': {'rule': 'same exposure, measure, wavelength; "=" agrees if equal, "<" agrees if the '
                                   'Table 1 p is below the bound',
                           'checks': checks,
                           'disagreements': [c for c in checks if not c['agree']]},
        'statements': sc,
        'not_reported': NOT_REPORTED,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(f'{TXT}: {len(pages)} pages, {len(text)} characters')
    print(f'{OUT}: {len(rows)} Table 1 rows, {len(text_ps)} text p-values, {len(sc)} statements, '
          f'{len(out["text_vs_table1"]["disagreements"])} text/table disagreements')
    for d in out['text_vs_table1']['disagreements']:
        print('  disagree:', d)


if __name__ == '__main__':
    main()
