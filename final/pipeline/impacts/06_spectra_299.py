"""Study 299 (Owens & Lewis 2021): the five LED spectra and the P. scintillans sensitivity curve,
read from the vector drawing of Fig. 1.

Run from final/:  .venv/bin/python pipeline/impacts/06_spectra_299.py
Input:  data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf, page 3 (read-only; see MANIFEST.csv).
        Needs poppler's `pdftocairo` on PATH (no Python PDF library).
Output: data/derived/impacts/spectra_299.json

Human decisions (AI_LOG "Impacts task"): step 75, use 299's Fig. 1 now (option c: build now, swap in the
authors' data if they send it); sensitivity curve = P. scintillans. The human approved digitising Fig. 1
(`estimated`); the figure turned out to be vector, so values are read deterministically from its paths,
as for study 278 (05_spectra_278.py, label `inferred`). The label is written as `inferred` and was put
to the human for confirmation in step 75.

What the figure is (caption, documented): spectral distribution of the cool white, warm white, blue,
amber and red LEDs used in 2018, plotted against the spectral sensitivity of males of crepuscular
P. scintillans (white curve, from Lall et al. 1988). Y axis "Relative intensity"; X axis "Wavelength (nm)".
The caption says the area under each LED curve (total photons) was standardised across treatments;
whether the y axis is in photon or energy units is not stated.

Rules (all deterministic):
- pdftocairo -svg writes the page as SVG; the figure's paths carry page coordinates (no transform).
  Cubic Bézier segments are flattened to 8 chords each.
- Axis ticks = the small filled rectangles of colour rgb(20%,20%,20%) next to the plot panel: those left of
  the panel are y ticks (centre y), those below it are x ticks (centre x). Tick labels are outlined glyphs,
  not text, so their values are taken as printed, in order: x 400, 500, 600, 700 nm; y 0.00, 0.25, 0.50,
  0.75, 1.00. Calibration = least-squares line per axis; the largest tick residual is written out.
- LED curves: each is drawn as a stroked line that the PDF stores as the closed outline of the stroke
  (one subpath, > 1000 vertices, spanning the plot). The curve value at wavelength λ is the midpoint of the
  highest and lowest crossings of that outline with the vertical line at λ. Sampled at every whole nm
  inside the outline's x range. The median stroke height (highest minus lowest crossing) is written out
  as the line's thickness in y units.
- LED names: the legend swatches (top to bottom: cool white, warm white, blue, amber, red, as printed)
  are each line colour blended with the legend background. Each line colour L is paired with the swatch S
  that minimises the residual of the least-squares fit S = a*L + (1 - a)*background; pairs must be 1:1.
- P. scintillans: the one white-filled polygon with > 100 vertices (drawn whole, under the LED fills).
  Its value at λ = the highest crossing of its outline with the vertical line at λ; every whole nm inside
  its x range.
- Output rounding: wavelength 1 nm grid (exact), values to 1e-4.
- Known limit (audits/impacts_spectra_299/AUDIT_2026-10-03.md): at sharp peak tips the midpoint rule reads
  slightly low (red 0.9982 vs apex 1.0000, blue 0.9246 vs 0.9319); amber and blue end at 774 nm because
  their outlines end at 774.84 nm.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

SRC = Path('data/raw/impacts/fireflies/Owens_Lewis_2021_ICD_study299.pdf')
OUT = Path('data/derived/impacts/spectra_299.json')
TICK = 'rgb(19.999695%, 19.999695%, 19.999695%)'
WHITE = 'rgb(100%, 100%, 100%)'
LEGEND_ORDER = ['cool_white', 'warm_white', 'blue', 'amber', 'red']
X_LABELS = [400, 500, 600, 700]
Y_LABELS = [0.0, 0.25, 0.5, 0.75, 1.0]
DOCUMENTED_PEAK = {'cool_white': 453.2, 'warm_white': 616.43, 'blue': 455.31, 'amber': 613.41, 'red': 658.06}


def page_svg():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / 'p3.svg'
        subprocess.run(['pdftocairo', '-svg', '-f', '3', '-l', '3', str(SRC), str(out)], check=True)
        return out.read_text()


def rgb(s):
    return [float(v) for v in re.findall(r'[\d.]+', s)]


def polyline(d):
    """Vertices of an M/L/C path; each C flattened to 8 chords."""
    pts = []
    for cmd, args in re.findall(r'([MLCZ])([^MLCZ]*)', d):
        v = [float(x) for x in args.split()]
        if cmd in 'ML':
            pts.append((v[0], v[1]))
        elif cmd == 'C':
            x0, y0 = pts[-1]
            x1, y1, x2, y2, x3, y3 = v
            for i in range(1, 9):
                t = i / 8
                u = 1 - t
                pts.append((u**3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t**3 * x3,
                            u**3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t**3 * y3))
    return pts


def paths(svg):
    out = []
    for m in re.finditer(r'<path ([^>]*)/>', svg):
        a = m.group(1)
        d = re.search(r' d="([^"]*)"', a)
        fill = re.search(r'fill="([^"]*)"', a)
        if not d or not fill or 'transform=' in a:
            continue
        # cairo ends a closed shape with "Z M x y" (a moveto back to the start): drop that trailing moveto.
        dd = re.sub(r'Z\s*M\s*[-\d.]+\s+[-\d.]+\s*$', 'Z', d.group(1))
        if dd.count('M') != 1:
            continue
        out.append((fill.group(1), polyline(dd)))
    return out


def crossings(pts, x):
    ys = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if x1 != x2 and (x1 - x) * (x2 - x) <= 0:
            ys.append(y1 + (y2 - y1) * (x - x1) / (x2 - x1))
    return ys


def fit(pairs):
    n = len(pairs)
    mx = sum(p for p, _ in pairs) / n
    my = sum(v for _, v in pairs) / n
    m = sum((p - mx) * (v - my) for p, v in pairs) / sum((p - mx) ** 2 for p, _ in pairs)
    c = my - m * mx
    return m, c, max(abs(m * p + c - v) for p, v in pairs)


def main():
    ps = paths(page_svg())

    # Plot panel = the largest rectangle filled with the panel grey; ticks sit just outside it.
    def bbox(pts):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return min(xs), max(xs), min(ys), max(ys)

    panel = max((bbox(p) for f, p in ps if f == 'rgb(49.803162%, 49.803162%, 49.803162%)' and len(p) <= 5),
                key=lambda b: (b[1] - b[0]) * (b[3] - b[2]))
    px0, px1, py0, py1 = panel
    ticks = [bbox(p) for f, p in ps if f == TICK and len(p) <= 5]
    yt = sorted(((b[2] + b[3]) / 2 for b in ticks if b[1] <= px0 + 0.01), reverse=True)  # bottom → top
    xt = sorted((b[0] + b[1]) / 2 for b in ticks if b[2] >= py1 - 0.01)
    assert len(xt) == len(X_LABELS) and len(yt) == len(Y_LABELS), (xt, yt)
    mx, cx, rx = fit(list(zip(xt, X_LABELS)))
    my, cy, ry = fit(list(zip(yt, Y_LABELS)))
    nm = lambda X: mx * X + cx
    val = lambda Y: my * Y + cy
    X_of = lambda w: (w - cx) / mx

    # Legend swatches: coloured squares right of the panel; the legend background is the colour drawn
    # first at each swatch position.
    sw = [(f, bbox(p)) for f, p in ps if len(p) <= 5 and bbox(p)[0] > px1]
    sw_pos = sorted({(round(b[2], 1), round(b[3], 1)) for f, b in sw if abs((b[1] - b[0]) - (b[3] - b[2])) < 0.5})
    background = None
    swatches = []
    for y0, y1 in sw_pos:
        here = [f for f, b in sw if (round(b[2], 1), round(b[3], 1)) == (y0, y1)]
        background = background or here[0]
        assert here[0] == background and len(here) == 2, here
        swatches.append(here[1])
    assert len(swatches) == len(LEGEND_ORDER), swatches
    bg = rgb(background)

    leds = [(f, p) for f, p in ps if len(p) > 1000 and f != WHITE
            and bbox(p)[1] - bbox(p)[0] > 0.5 * (px1 - px0)]
    assert len(leds) == 5, [f for f, _ in leds]

    def blend_residual(L, S):
        num = sum((s - b) * (l - b) for l, s, b in zip(L, S, bg))
        den = sum((l - b) ** 2 for l, b in zip(L, bg))
        a = num / den
        return sum((a * l + (1 - a) * b - s) ** 2 for l, s, b in zip(L, S, bg)) ** 0.5, a

    names, alphas = {}, {}
    for f, _ in leds:
        res = [(blend_residual(rgb(f), rgb(s)), i) for i, s in enumerate(swatches)]
        (r, a), i = min(res)
        names[f], alphas[f] = LEGEND_ORDER[i], round(a, 4)
    assert sorted(names.values()) == sorted(LEGEND_ORDER), names

    curves = {}
    for f, pts in leds:
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        samples, heights = [], []
        for w in range(int(nm(x0)) + 1, int(nm(x1)) + 1):
            ys = crossings(pts, X_of(w))
            if len(ys) < 2:
                continue
            samples.append([w, round(val((min(ys) + max(ys)) / 2), 4)])
            heights.append(val(min(ys)) - val(max(ys)))
        heights.sort()
        peak = max(samples, key=lambda s: s[1])
        n = names[f]
        curves[n] = {'kind': 'led', 'line_colour': f, 'legend_blend_alpha': alphas[f],
                     'line_thickness_y_median': round(heights[len(heights) // 2], 4),
                     'peak_nm_extracted': peak[0], 'peak_value_extracted': peak[1],
                     'peak_nm_documented': DOCUMENTED_PEAK[n], 'n': len(samples), 'samples': samples}

    whites = [p for f, p in ps if f == WHITE and len(p) > 100]
    assert len(whites) == 1, len(whites)
    pts = whites[0]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    samples = []
    for w in range(int(nm(x0)) + 1, int(nm(x1)) + 1):
        ys = crossings(pts, X_of(w))
        if ys:
            samples.append([w, round(val(min(ys)), 4)])
    peak = max(samples, key=lambda s: s[1])
    curves['p_scintillans'] = {'kind': 'sensitivity', 'species': 'Photinus scintillans (males, crepuscular)',
                               'source_cited_in_299': 'Lall et al. 1988 (ERG)',
                               'peak_nm_extracted': peak[0], 'peak_value_extracted': peak[1],
                               'n': len(samples), 'samples': samples}

    doc = {
        'study_id': '299',
        'label': 'inferred',
        'label_note': 'human approved digitising (estimated) in step 75; the figure is vector, so values are read '
                      'deterministically from its paths as for study 278; label inferred put to the human for confirmation',
        'rule': 'Fig. 1 vector paths mapped to axis values by a least-squares fit of tick marks to their printed '
                'labels; LED value = midpoint of the stroke outline; P. scintillans = top edge of the white polygon '
                '(pipeline/impacts/06_spectra_299.py)',
        'source': 'Owens & Lewis 2021, Insect Conservation and Diversity 14:199-210, Fig. 1 '
                  '(doi:10.1111/icad.12487); file ' + str(SRC),
        'units': {'wavelength': 'nm', 'value': 'relative intensity as printed on the y axis (0-1); photon or energy '
                  'basis not stated'},
        'documented': {'dim_photons_cm2_s': 2.079e19, 'bright_photons_cm2_s': 2.079e20,
                       'distance_cm': 60.8, 'flash_peak_nm': 567.47,
                       'flash_peak_source': 'Hall et al. 2016, cited in 299 Methods'},
        'calibration': {'x_ticks': list(zip(xt, X_LABELS)), 'y_ticks': list(zip(yt, Y_LABELS)),
                        'x_max_residual_nm': round(rx, 4), 'y_max_residual': round(ry, 6)},
        'curves': curves,
    }
    OUT.write_text(json.dumps(doc, indent=1))
    for k, c in curves.items():
        print(f"{k:14s} n={c['n']:3d} {c['samples'][0][0]}-{c['samples'][-1][0]} nm  peak {c['peak_nm_extracted']} nm "
              f"({c.get('peak_nm_documented', '-')}) value {c['peak_value_extracted']}  "
              f"thick {c.get('line_thickness_y_median', '-')}  alpha {c.get('legend_blend_alpha', '-')}")
    print('residuals', rx, ry)


if __name__ == '__main__':
    main()
