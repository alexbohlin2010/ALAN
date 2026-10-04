"""Philadelphia (City) and Cherry Springs (Rural) night spectra for the "Two measured nights" step.

Run from final/:  python3 pipeline/spectra/01_night_spectra.py      (stdlib only)
Input:  data/raw/spectra/spitschan2016/{DRL,CSSP}_spectra.csv and {DRL,CSSP}_dataquality.csv
        (read-only; SHA-256 checked against data/raw/spectra/MANIFEST.csv before anything is read).
Output: data/derived/spectra/philadelphia.json, data/derived/spectra/cherry_springs.json,
        data/derived/spectra/spectra_meta.json

Human decisions (AI_LOG "Firefly narrative" round 2 close, rounds 3a and 3h; handoffs 2026-10-04_two-nights-spectra.md,
2026-10-04_two-nights-built.md): reproduce the selection of the draft "3D Spectrum" view (rules written out below;
the draft script, Linda/visual tests/spatial/philadelphia-spectral-space/scripts/preprocess.ts, is not in git): all
astronomical-night spectra, 240 evenly sampled per site, 2 nm step, shared log10 display limits; the moon difference
is not considered; JSON per site + one meta file. Round 3h: audit findings F1-F6, R1, R2 fixed; R3 kept as is.
Round 3k: re-check notes C1 (state that source_column is 1-based) and C2 (no non-RULES label) fixed.

Source format (MANIFEST.csv notes; IlluminationSpectraDataset README Table S1): transposed CSV, one column per
spectrum (1 per minute). Row 1 timestamp `dd-MMM-yyyy HH:mm:ss` (no time zone; trailing empty field), row 2
date/night id, row 3 solar elevation (deg), row 4 lunar elevation (deg), row 5 lunar illuminated fraction,
rows 6-566 = 280..840 nm at 1 nm (the CSVs have no wavelength row; the grid is from the README / MANIFEST),
absolute downwelling spectral irradiance, W m^-2 nm^-1. `NaN` = no value in the source.

Rules (all deterministic, same as the draft's preprocess.ts):
- Night = solar elevation (row 3) < -18 deg, strictly.
- Even sampling in source column order: if a site has n > 240 night spectra, pick
  night[round_half_up(i * (n - 1) / 239)] for i = 0..239 (JS Math.round == floor(x + 0.5) for x >= 0).
  If n <= 240, all n are kept (audit R3: kept as is, human decision round 3h).
- Wavelengths: every 2nd source row, 280, 282, ..., 840 nm (281 values).
- Every number taken from the source (irradiance, night id, solar/lunar elevation, lunar fraction, data-quality
  counts) is written
  exactly as the source text (no re-formatting, no rounding); `NaN` -> null. Zeros are kept (the paper sets
  negatives after dark subtraction to 0).
- Display limits (shared by both sites): over all selected values > 0 of both sites, log10(value) sorted;
  p = linear-interpolation percentile (index = (N - 1) * q, as the draft's `percentile`);
  floor = floor(p(0.01)), ceil = ceil(p(0.99)).
- Output: each file is serialised in memory, parsed back strictly (no NaN/Infinity, no duplicate keys) and only
  then written.

Labels (RULES 2.3), every field of the site files: irradiance and timestamps `measured`; night id, solar/lunar
elevation, lunar fraction, place, paper label, unit and the copied data-quality counts `documented`; the selection
(source columns), counts, date ranges, cell counts, file checksum and the display limits `inferred` (rules above).
`site`, `source_file`, `meta_file` are names, not values: listed under `not_values`, with no label.
"""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

RAW = Path('data/raw/spectra/spitschan2016')
MANIFEST = Path('data/raw/spectra/MANIFEST.csv')
OUT = Path('data/derived/spectra')
SITES = [  # (output id, file prefix, label in paper, place)
    ('philadelphia', 'DRL', 'City', 'Philadelphia, PA'),
    ('cherry_springs', 'CSSP', 'Rural', 'Cherry Springs State Park, PA'),
]
TARGET = 240
STRIDE = 2
NIGHT_BELOW_DEG = -18.0
WL_START, WL_END = 280, 840
N_WL_SOURCE = WL_END - WL_START + 1  # 561
UNIT = 'W m^-2 nm^-1'
SOURCE_URL = 'https://github.com/spitschan/IlluminationSpectraDataset/tree/1d2ecc69cb15885b147d2831cae89fbd15d471fa/data/'
CITATION = ('Spitschan M, Aguirre GK, Brainard DH, Sweeney AM (2016). Variation of outdoor illumination as a function '
            'of solar elevation and light pollution. Scientific Reports 6: 26756, doi:10.1038/srep26756 '
            '(correction: Sci Rep 7: 46930, 2017)')
JSON_NUMBER = re.compile(r'-?(0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?')


class Raw(str):
    """A number kept as its source text; written unquoted as a JSON number."""


def raw(token):
    if token == 'NaN':
        return None
    if not JSON_NUMBER.fullmatch(token):
        raise SystemExit(f'not a JSON number: {token!r}')
    return Raw(token)


def dump(obj):
    """JSON text; Raw values are written as their source text (independent of key order)."""
    if isinstance(obj, Raw):
        return str(obj)
    if isinstance(obj, dict):
        return '{' + ','.join(json.dumps(k) + ':' + dump(v) for k, v in obj.items()) + '}'
    if isinstance(obj, (list, tuple)):
        return '[' + ','.join(dump(v) for v in obj) + ']'
    if isinstance(obj, float) and not math.isfinite(obj):
        raise SystemExit(f'non-finite number: {obj}')
    return json.dumps(obj)


def strict_parse(text):
    def no_constant(name):
        raise SystemExit(f'non-standard JSON constant: {name}')

    def no_duplicates(pairs):
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            raise SystemExit(f'duplicate keys: {keys}')
        return dict(pairs)
    return json.loads(text, parse_constant=no_constant, object_pairs_hook=no_duplicates)


def write_checked(path, text):
    strict_parse(text)  # before anything is written
    path.write_text(text)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def check_manifest():
    rows = {r['filename']: r for r in csv.DictReader(open(MANIFEST, newline='', encoding='utf-8'))}
    for _, prefix, _, _ in SITES:
        for name in (f'{prefix}_spectra.csv', f'{prefix}_dataquality.csv'):
            got = sha256(RAW / name)
            if got != rows[name]['sha256']:
                raise SystemExit(f'{name}: SHA-256 {got} does not match MANIFEST.csv')
    return {name: r['sha256'] for name, r in rows.items()}


def parse(path):
    lines = path.read_text(encoding='utf-8').replace('\r', '').rstrip('\n').split('\n')
    if len(lines) != 5 + N_WL_SOURCE:
        raise SystemExit(f'{path}: expected {5 + N_WL_SOURCE} rows, found {len(lines)}')
    ts = lines[0].split(',')
    while ts and ts[-1] == '':
        ts.pop()
    ts = [t.strip() for t in ts]
    if len(set(ts)) != len(ts):
        raise SystemExit(f'{path}: duplicate timestamps')
    rows = [line.split(',') for line in lines[1:]]
    for i, r in enumerate(rows):
        if len(r) != len(ts):
            raise SystemExit(f'{path}: row {i + 2} has {len(r)} fields, expected {len(ts)}')
    return ts, rows[:4], rows[4:]


def even_sample(indices, target):
    if len(indices) <= target:
        return list(indices)
    n = len(indices)
    return [indices[math.floor(i * (n - 1) / (target - 1) + 0.5)] for i in range(target)]


def percentile(sorted_vals, q):
    idx = (len(sorted_vals) - 1) * q
    lo = math.floor(idx)
    if lo + 1 >= len(sorted_vals):
        return sorted_vals[lo]
    return sorted_vals[lo] + (idx - lo) * (sorted_vals[lo + 1] - sorted_vals[lo])


SITE_LABELS = {
    'place': 'documented', 'paper_label': 'documented', 'unit': 'documented', 'source_sha256': 'inferred',
    'n_source_spectra': 'inferred', 'n_night_spectra': 'inferred', 'n_selected': 'inferred',
    'source_date_range': 'inferred', 'selected_date_range': 'inferred', 'source_dataquality': 'documented',
    'selected_cells': 'inferred', 'source_column': 'inferred', 'timestamp': 'measured', 'night_id': 'documented',
    'solar_elevation_deg': 'documented', 'lunar_elevation_deg': 'documented',
    'lunar_illuminated_fraction': 'documented', 'irradiance': 'measured',
}
LABEL_NOTES = {
    'documented': 'stated by the dataset authors / paper (night id, elevations and lunar fraction are computed and '
                  'published by the authors, not instrument readings; source_dataquality copied from '
                  '*_dataquality.csv; place and paper_label from the paper; unit from the paper Methods)',
    'inferred': 'derived by this script from the source by the rules in spectra_meta.json (counts, date ranges, '
                'cell counts, selected source columns, SHA-256 of the source file)',
    'measured': 'spectrometer readings (irradiance) and their recorded timestamps, copied as source text',
}
NOT_VALUES = {'site': 'site id', 'source_file': 'path of the raw file', 'meta_file': 'path of the meta file'}


def main():
    hashes = check_manifest()
    OUT.mkdir(parents=True, exist_ok=True)
    wl = list(range(WL_START, WL_END + 1, STRIDE))
    positive_logs = []
    site_docs, site_summary = {}, {}

    for sid, prefix, paper_label, place in SITES:
        ts, meta_rows, spec_rows = parse(RAW / f'{prefix}_spectra.csv')
        night_id, sun, moon_el, moon_frac = meta_rows
        if any(t == 'NaN' for t in sun):
            raise SystemExit(f'{prefix}: NaN solar elevation')
        night = [j for j in range(len(ts)) if float(sun[j]) < NIGHT_BELOW_DEG]
        cols = even_sample(night, TARGET)
        irr, n_nan, n_zero, n_pos = [], 0, 0, 0
        for j in cols:
            spectrum = []
            for k in range(len(wl)):
                v = raw(spec_rows[k * STRIDE][j])
                spectrum.append(v)
                if v is None:
                    n_nan += 1
                    continue
                f = float(v)
                if f < 0:
                    raise SystemExit(f'{prefix}: negative value {v} at column {j + 1}')
                if f == 0:
                    n_zero += 1
                else:
                    n_pos += 1
                    positive_logs.append(math.log10(f))
            irr.append(spectrum)
        q = dict(zip(*[r.split(',') for r in (RAW / f'{prefix}_dataquality.csv').read_text().strip().split('\n')]))
        doc = {
            'site': sid, 'place': place, 'paper_label': paper_label, 'unit': UNIT,
            'meta_file': 'spectra_meta.json',  # wavelengths, display limits, rules, source, time zone note
            'source_file': str(RAW / f'{prefix}_spectra.csv'),
            'source_sha256': hashes[f'{prefix}_spectra.csv'],
            'n_source_spectra': len(ts), 'n_night_spectra': len(night), 'n_selected': len(cols),
            'source_date_range': [ts[0], ts[-1]],
            'selected_date_range': [ts[cols[0]], ts[cols[-1]]],
            'source_dataquality': {k: raw(v) for k, v in q.items()},
            'selected_cells': {'total': len(cols) * len(wl), 'null_nan': n_nan, 'zero': n_zero, 'positive': n_pos},
            'labels': SITE_LABELS, 'label_notes': LABEL_NOTES, 'not_values': NOT_VALUES,
            'source_column': [j + 1 for j in cols],  # 1-based column in the source CSV
            'timestamp': [ts[j] for j in cols],
            'night_id': [raw(night_id[j]) for j in cols],
            'solar_elevation_deg': [raw(sun[j]) for j in cols],
            'lunar_elevation_deg': [raw(moon_el[j]) for j in cols],
            'lunar_illuminated_fraction': [raw(moon_frac[j]) for j in cols],
            'irradiance': irr,  # [spectrum][wavelength], W m^-2 nm^-1, wavelengths in spectra_meta.json
        }
        missing = set(doc) - set(SITE_LABELS) - set(NOT_VALUES) - {'labels', 'label_notes', 'not_values'}
        if missing:
            raise SystemExit(f'unlabelled fields: {sorted(missing)}')
        site_docs[sid] = doc
        site_summary[sid] = {k: doc[k] for k in ('n_source_spectra', 'n_night_spectra', 'n_selected', 'selected_cells')}

    positive_logs.sort()
    p01, p50, p99 = (percentile(positive_logs, x) for x in (0.01, 0.5, 0.99))
    floor, ceil = math.floor(p01), math.ceil(p99)

    meta = {
        'source': CITATION, 'source_url': SOURCE_URL, 'licence': 'data MIT (repository); article CC BY 4.0',
        'quantity': 'absolute downwelling spectral irradiance (radiance x pi, paper Methods)',
        'unit': UNIT,
        'timestamp_format': 'dd-MMM-yyyy HH:mm:ss, as in the source; no time zone in the source',
        'units_other': {'solar_elevation_deg': 'degrees', 'lunar_elevation_deg': 'degrees',
                        'lunar_illuminated_fraction': '0-1'},
        'wavelength_nm': wl, 'wavelength_step_nm': STRIDE,
        'wavelength_source': 'the source CSVs have no wavelength row; rows 6-566 = 280-840 nm at 1 nm per the '
                             'IlluminationSpectraDataset README (Table S1) and data/raw/spectra/MANIFEST.csv; '
                             '561 rows are consistent with this',
        'night_id_note': 'night_id = source row 2 ("date/night") as published. It changes at about 01:05 (source '
                         'time) inside one continuous night, so one night of measuring can carry two ids '
                         '(8 ids over 5 night blocks per site). Not used by the app.',
        'null_means': 'NaN in the source (no value)',
        'source_column_note': 'source_column in the site files is 1-based: column 1 = the first spectrum column of '
                              'the source CSV; the irradiance at wavelength w is in CSV row 6 + (w - 280)',
        'verbatim': 'every number taken from the source is written as its source text',
        'selection': {'label': 'inferred',
                      'rule': f'solar elevation < {NIGHT_BELOW_DEG:g} deg; then {TARGET} spectra evenly sampled in '
                              f'source column order (index round_half_up(i*(n-1)/{TARGET - 1})); every {STRIDE}nd '
                              f'wavelength {WL_START}-{WL_END} nm; values verbatim',
                      'moon': 'not considered (human decision, handoff 2026-10-04_two-nights-spectra.md)',
                      'rules_from': 'human decisions in handoff 2026-10-04_two-nights-spectra.md (reproducing the '
                                    'draft "3D Spectrum" view)',
                      'draft_reference': 'Linda/visual tests/spatial/philadelphia-spectral-space/scripts/'
                                         'preprocess.ts (not in git)'},
        'display_limits_log10': {'label': 'inferred', 'floor': floor, 'ceil': ceil,
                                 'rule': 'over all selected values > 0 of both sites: floor(p01), ceil(p99) of '
                                         'log10(value); linear-interpolation percentile, index (N-1)*q',
                                 'n_positive': len(positive_logs), 'p01': p01, 'p50': p50, 'p99': p99},
        'files': {sid: f'{sid}.json' for sid, _, _, _ in SITES},
        'script': 'pipeline/spectra/01_night_spectra.py',
        'sites': site_summary,
    }

    for sid, doc in site_docs.items():
        write_checked(OUT / f'{sid}.json', dump(doc) + '\n')
    write_checked(OUT / 'spectra_meta.json', json.dumps(meta, indent=1) + '\n')

    print(json.dumps({'display_limits_log10': meta['display_limits_log10'], 'sites': site_summary}, indent=1))
    for sid in site_docs:
        print(sid, (OUT / f'{sid}.json').stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
