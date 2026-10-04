"""Study 278 (Wang et al. 2023): the two LED spectra, read from the vector drawing of S. Fig. 1.

Run from final/:  .venv/bin/python pipeline/impacts/05_spectra_278.py
Input:  data/raw/impacts/mice/Wang_2023_NeurobiolDis_study278_supplement_mmc1.pdf, page 1 (read-only;
        see MANIFEST.csv). Needs poppler's `pdftocairo` and `pdftotext` on PATH (no Python PDF library).
Output: data/derived/impacts/spectra_278.json

Human decisions (AI_LOG "Impacts task"): step 74, extract the S. Fig. 1 curves; label `inferred`
(values read deterministically from the published figure's vector paths; no table was supplied).

What the figure is (supplement page 1, legend + caption, documented): spectral irradiance of the LED
array, short-wavelength enriched (10 lx, peak 478 nm) and long-wavelength enriched (10 lx, peak 608 nm).
Y axis printed as "Spectral Irradiance (mW/m2)"; X axis "Wavelength (nm)".

Rules (all deterministic):
- pdftocairo -svg writes the page as SVG; every path keeps its PDF coordinates and a transform
  matrix(a,0,0,d,0,f). Points are mapped to page space as X = a*x, Y = d*y + f (top-left origin,
  the same frame as `pdftotext -bbox`).
- Curves = the two stroked paths in the figure's two colours with more than 10 vertices (the 2-vertex
  paths of the same colours are the legend swatches). Which curve is which: the swatch whose Y is
  nearest the legend word "Short" is short-λ, nearest "Long" is long-λ.
- Axis ticks = black 2-vertex strokes of length < 5 pt: vertical ones below the plot = X ticks,
  horizontal ones left of the plot = Y ticks. Each tick is paired with the nearest numeric tick label
  of the text layer (X: label centre X; Y: label centre Y); pairs farther than 8 pt are an error.
- Calibration: least-squares line value = m*coord + c per axis over the paired ticks; the largest tick
  residual is written to the output.
- Every path vertex becomes one sample (no resampling, smoothing or clipping). Path commands other than
  M and L stop the script.
- Output rounding: wavelength to 0.01 nm, value to 1e-5. Values are not clipped at 0: five long-λ samples
  near 380-403 nm are -8e-5, within the calibration residual (audits/impacts_spectra/AUDIT_2026-10-03.md).
- `peak_nm_extracted` is the curve's global maximum. For the long-λ curve that is 641 nm, while the
  caption's 608 nm is a local maximum (607.96 nm); both are kept, the source is not corrected.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

SRC = Path('data/raw/impacts/mice/Wang_2023_NeurobiolDis_study278_supplement_mmc1.pdf')
OUT = Path('data/derived/impacts/spectra_278.json')
BLACK = 'rgb(0%, 0%, 0%)'


def page_svg():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / 'p1.svg'
        subprocess.run(['pdftocairo', '-svg', '-f', '1', '-l', '1', str(SRC), str(out)], check=True)
        return out.read_text()


def words():
    xml = subprocess.run(['pdftotext', '-bbox', '-f', '1', '-l', '1', str(SRC), '-'],
                         check=True, capture_output=True, text=True).stdout
    pat = r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>'
    return [(float(a), float(b), float(c), float(e), w) for a, b, c, e, w in re.findall(pat, xml)]


def paths(svg):
    out = []
    for m in re.finditer(r'<path ([^>]*)/>', svg):
        attrs = m.group(1)
        stroke = re.search(r'stroke="([^"]*)"', attrs)
        d = re.search(r' d="([^"]*)"', attrs)
        tr = re.search(r'transform="matrix\(([^)]*)\)"', attrs)
        if not (stroke and d and tr):
            continue
        a, b, c, dd, e, f = (float(v) for v in tr.group(1).split(','))
        assert b == 0 and c == 0 and e == 0, 'unexpected transform'
        cmds = re.findall(r'([A-Za-z])\s*([-\d.]+)\s+([-\d.]+)', d.group(1))
        if any(k not in 'ML' for k, _, _ in cmds):
            raise SystemExit('path command other than M/L found')
        pts = [(a * float(x), dd * float(y) + f) for _, x, y in cmds]
        out.append((stroke.group(1), pts))
    return out


def fit(pairs):
    n = len(pairs)
    mx = sum(p for p, _ in pairs) / n
    my = sum(v for _, v in pairs) / n
    m = sum((p - mx) * (v - my) for p, v in pairs) / sum((p - mx) ** 2 for p, _ in pairs)
    c = my - m * mx
    return m, c, max(abs(m * p + c - v) for p, v in pairs)


def main():
    ps = paths(page_svg())
    ws = words()
    nums = [(w, (x0 + x1) / 2, (y0 + y1) / 2) for x0, y0, x1, y1, w in ws if re.fullmatch(r'\d+(\.\d+)?', w)]

    ticks = [pts for col, pts in ps if col == BLACK and len(pts) == 2
             and 0 < abs(pts[0][0] - pts[1][0]) + abs(pts[0][1] - pts[1][1]) < 5]
    xt = [pts[0][0] for pts in ticks if pts[0][0] == pts[1][0]]
    yt = [pts[0][1] for pts in ticks if pts[0][1] == pts[1][1]]

    def pair(coords, axis):
        res = []
        for t in coords:
            if axis == 'x':
                w, dist = min(((w, abs(cx - t)) for w, cx, cy in nums if float(w) >= 100), key=lambda z: z[1])
            else:
                w, dist = min(((w, abs(cy - t)) for w, cx, cy in nums if float(w) < 1), key=lambda z: z[1])
            if dist > 8:
                raise SystemExit(f'{axis} tick at {t:.2f} has no label within 8 pt')
            res.append((t, float(w)))
        return res

    xp, yp = pair(xt, 'x'), pair(yt, 'y')
    mx, cx, rx = fit(xp)
    my, cy, ry = fit(yp)

    colours = {col for col, pts in ps if col != BLACK}
    swatch = {col: pts[0][1] for col, pts in ps if col in colours and len(pts) == 2}
    curve = {col: pts for col, pts in ps if col in colours and len(pts) > 10}
    assert len(colours) == 2 and set(swatch) == colours and set(curve) == colours
    wy = {w: (y0 + y1) / 2 for x0, y0, x1, y1, w in ws if w in ('Short', 'Long')}
    name = {col: min(wy, key=lambda w: abs(wy[w] - y)) for col, y in swatch.items()}
    assert sorted(name.values()) == ['Long', 'Short']

    out_curves = {}
    for col, pts in curve.items():
        key = 'short' if name[col] == 'Short' else 'long'
        samples = [[round(mx * X + cx, 2), round(my * Y + cy, 5)] for X, Y in pts]
        peak = max(samples, key=lambda s: s[1])
        out_curves[key] = {
            'stroke': col, 'n': len(samples), 'peak_nm_extracted': peak[0], 'peak_value_extracted': peak[1],
            'samples': samples,
        }

    doc = {
        'study_id': '278',
        'label': 'inferred',
        'rule': 'S. Fig. 1 vector path vertices mapped to axis values by a least-squares fit of tick marks '
                'to their printed labels (pipeline/impacts/05_spectra_278.py)',
        'source': 'Wang et al. 2023, Neurobiology of Disease 176, Supplementary S. Fig. 1 '
                  '(doi:10.1016/j.nbd.2022.105944); file ' + str(SRC),
        'units': {'wavelength': 'nm', 'value': 'mW/m2 as printed on the y axis ("Spectral Irradiance (mW/m2)")'},
        'documented': {'short': {'peak_nm': 478, 'lux': 10.0, 'melanopic_EDI_mel_lx': 15, 'irradiance_W_m2': 0.03},
                       'long': {'peak_nm': 608, 'lux': 10.4, 'melanopic_EDI_mel_lx': 1, 'irradiance_W_m2': 0.05}},
        'calibration': {'x_ticks': xp, 'y_ticks': yp, 'x_max_residual_nm': round(rx, 4),
                        'y_max_residual': round(ry, 6)},
        'curves': out_curves,
    }
    OUT.write_text(json.dumps(doc, indent=1))
    for k, c in out_curves.items():
        print(k, c['n'], 'samples, peak', c['peak_nm_extracted'], 'nm, value', c['peak_value_extracted'],
              '| range', c['samples'][0][0], '-', c['samples'][-1][0], 'nm')
    print('residuals', rx, ry)


if __name__ == '__main__':
    main()
