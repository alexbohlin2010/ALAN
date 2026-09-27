from __future__ import annotations

import csv
import html
from pathlib import Path


SOURCE = Path(
    "/Users/lindaxiangyideng/Documents/FA26 studio A2/data/"
    "philadelphia and cherry springs data/CSSP_spectra.csv"
)
SVG_OUTPUT = Path(
    "/Users/lindaxiangyideng/Documents/FA26 studio A2/analysis/"
    "cssp-timestamp-column-explainer.svg"
)
TARGET = "01-Jul-2014 02:00:39"


def text(x, y, value, size=24, weight=400, fill="#27313a", anchor="start", rotate=None):
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{transform}>{html.escape(str(value))}</text>'
    )


def rect(x, y, w, h, fill, stroke="none", sw=1, rx=0):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}" rx="{rx}"/>'
    )


with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.reader(handle))

timestamps = [value for value in rows[0] if value]
column = timestamps.index(TARGET)
values = []
for row in rows[1:]:
    raw = row[column]
    values.append(float(raw) if raw not in ("", "NaN") else None)

date_number, solar_elevation, lunar_elevation, lunar_fraction = values[:4]
irradiance = values[4:]
wavelengths = list(range(280, 841))

width, height = 1800, 1000
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
    '<defs>',
    '<linearGradient id="spectrum" x1="0" x2="1" y1="0" y2="0">',
    '<stop offset="0%" stop-color="#6d3fc0"/><stop offset="12%" stop-color="#3155d8"/>',
    '<stop offset="27%" stop-color="#1aa3d6"/><stop offset="42%" stop-color="#2eaa65"/>',
    '<stop offset="58%" stop-color="#e1c22f"/><stop offset="73%" stop-color="#ee8a25"/>',
    '<stop offset="87%" stop-color="#d74a39"/><stop offset="100%" stop-color="#8f2d38"/>',
    '</linearGradient>',
    '<marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">',
    '<path d="M0,0 L12,6 L0,12 z" fill="#1f5f99"/></marker>',
    '</defs>',
    rect(0, 0, width, height, "#fbfcfe"),
    text(900, 62, "One timestamp column contains one complete spectrum", 38, 700, anchor="middle"),
    text(900, 101, "Actual CSSP example: 01-Jul-2014 02:00:39  •  DRL uses the same structure", 20, 400, "#5f6b76", "middle"),
]

# Panel headings.
parts += [
    text(55, 155, "1. Find a timestamp column", 24, 700),
    text(535, 155, "2. Read that column", 24, 700),
    text(940, 155, "3. Connect the wavelength values", 24, 700),
]

# Panel 1: schematic wide matrix.
mx, my = 108, 245
cw, ch = 62, 48
ncols, nrows = 6, 11
highlight = 2
parts.append(text(mx, 205, "TIMESTAMPS →", 17, 700, "#687580"))
row_labels = ["date #", "sun °", "moon °", "moon frac.", "280 nm", "281 nm", "…", "400 nm", "…", "700 nm", "840 nm"]
for c in range(ncols):
    x = mx + c * cw
    fill = "#1f5f99" if c == highlight else "#dbe3ea"
    parts.append(rect(x, my, cw, 66, fill, "#ffffff", 2))
    parts.append(text(x + cw / 2, my + 28, "selected" if c == highlight else f"time {c+1}", 13, 700,
                      "#ffffff" if c == highlight else "#43515d", "middle"))
    parts.append(text(x + cw / 2, my + 48, "time" if c == highlight else "column", 12, 400,
                      "#ffffff" if c == highlight else "#43515d", "middle"))
    for r in range(nrows):
        y = my + 66 + r * ch
        if c == highlight:
            cell_fill = "#d8ebfb" if r < 4 else "#eaf4fc"
        else:
            cell_fill = "#f0f3f6" if r < 4 else "#f7f9fb"
        parts.append(rect(x, y, cw, ch, cell_fill, "#ffffff", 2))

for r, label in enumerate(row_labels):
    y = my + 66 + r * ch + 30
    parts.append(text(mx - 10, y, label, 13, 400, "#52606d", "end"))

parts.append(text(25, my + 162, "METADATA", 14, 700, "#667681", "middle", -90))
parts.append(text(25, my + 418, "WAVELENGTH ROWS", 14, 700, "#667681", "middle", -90))
parts.append(text(mx + highlight * cw + cw / 2, 888, "one vertical slice", 17, 700, "#1f5f99", "middle"))
parts.append(text(mx + highlight * cw + cw / 2, 914, "= one observation", 17, 700, "#1f5f99", "middle"))

# Panel 2: actual selected column values.
cx, col_w = 535, 330
parts.append(rect(cx, 205, col_w, 74, "#1f5f99", rx=8))
parts.append(text(cx + col_w / 2, 236, "01-Jul-2014", 18, 700, "#ffffff", "middle"))
parts.append(text(cx + col_w / 2, 262, "02:00:39", 18, 700, "#ffffff", "middle"))

metadata = [
    ("Date number", f"{date_number:.0f}"),
    ("Solar elevation", f"{solar_elevation:.1f}°"),
    ("Lunar elevation", f"{lunar_elevation:.1f}°"),
    ("Moon illuminated", f"{lunar_fraction:.3f}"),
]
y = 289
for label, value in metadata:
    parts.append(rect(cx, y, col_w, 55, "#d8ebfb", "#ffffff", 2))
    parts.append(text(cx + 14, y + 35, label, 15, 400))
    parts.append(text(cx + col_w - 14, y + 35, value, 15, 700, anchor="end"))
    y += 55

parts.append(text(cx, 536, "561 irradiance values", 18, 700, "#1f5f99"))
samples = [280, 360, 400, 450, 500, 558, 600, 700, 840]
y = 552
for i, wavelength in enumerate(samples):
    value = irradiance[wavelength - 280]
    fill = "#eef6fc" if i % 2 == 0 else "#f7fafc"
    shown = "NaN" if value is None else ("0" if value == 0 else f"{value:.2e}")
    parts.append(rect(cx, y, col_w, 39, fill, "#ffffff", 1))
    parts.append(text(cx + 14, y + 26, f"{wavelength} nm", 14, 400))
    parts.append(text(cx + col_w - 14, y + 26, shown, 14, 400, anchor="end"))
    y += 39

parts.append(text(cx + col_w / 2, 930, "All wavelength rows form the curve →", 17, 700, "#1f5f99", "middle"))
parts.append('<line x1="870" y1="520" x2="925" y2="520" stroke="#1f5f99" stroke-width="4" marker-end="url(#arrow)"/>')

# Panel 3: actual spectrum.
px0, py0, pw, ph = 1015, 250, 690, 540
parts += [
    rect(px0, py0, pw, ph, "#ffffff", "#ccd5dc", 2),
    rect(px0, py0, pw * (400 - 280) / 560, ph, "#6f5bd3", rx=0),
]
# Redraw subtle spectral regions using opacity.
parts[-1] = f'<rect x="{px0}" y="{py0}" width="{pw * (400 - 280) / 560}" height="{ph}" fill="#6f5bd3" opacity="0.045"/>'
vis_x = px0 + pw * (400 - 280) / 560
vis_w = pw * (700 - 400) / 560
parts.append(f'<rect x="{vis_x}" y="{py0}" width="{vis_w}" height="{ph}" fill="#d9aa3f" opacity="0.035"/>')
ir_x = px0 + pw * (700 - 280) / 560
ir_w = pw * (840 - 700) / 560
parts.append(f'<rect x="{ir_x}" y="{py0}" width="{ir_w}" height="{ph}" fill="#b56a55" opacity="0.035"/>')

max_y = max(value for value in irradiance if value is not None)
top_y = max_y * 1.12
for tick in range(5):
    value = tick * 1e-8
    ytick = py0 + ph - (value / top_y) * ph
    parts.append(f'<line x1="{px0}" y1="{ytick:.1f}" x2="{px0+pw}" y2="{ytick:.1f}" stroke="#dce3e9" stroke-width="1"/>')
    label = "0" if tick == 0 else f"{tick}×10⁻⁸"
    parts.append(text(px0 - 16, ytick + 6, label, 14, 400, "#52606d", "end"))

for wavelength in [280, 360, 400, 500, 600, 700, 800, 840]:
    xtick = px0 + (wavelength - 280) / 560 * pw
    parts.append(f'<line x1="{xtick:.1f}" y1="{py0+ph}" x2="{xtick:.1f}" y2="{py0+ph+8}" stroke="#8c99a4"/>')
    parts.append(text(xtick, py0 + ph + 30, wavelength, 14, 400, "#52606d", "middle"))

points = []
for wavelength, value in zip(wavelengths, irradiance):
    if value is None:
        continue
    x = px0 + (wavelength - 280) / 560 * pw
    yv = py0 + ph - (value / top_y) * ph
    points.append(f"{x:.2f},{yv:.2f}")
parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#195b8f" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>')

for wavelength in [360, 450, 558, 700, 840]:
    value = irradiance[wavelength - 280]
    x = px0 + (wavelength - 280) / 560 * pw
    yv = py0 + ph - (value / top_y) * ph
    parts.append(f'<circle cx="{x:.2f}" cy="{yv:.2f}" r="5.5" fill="#ffffff" stroke="#195b8f" stroke-width="3"/>')

parts.append(text(px0 + pw * 60 / 560, py0 - 18, "UV", 16, 700, "#6655a8", "middle"))
parts.append(text(px0 + pw * 270 / 560, py0 - 18, "VISIBLE", 16, 700, "#8b681e", "middle"))
parts.append(text(px0 + pw * 490 / 560, py0 - 18, "NEAR INFRARED", 16, 700, "#8a5546", "middle"))
parts.append(rect(px0 + pw * (380 - 280) / 560, py0 + ph + 53, pw * 400 / 560, 18, "url(#spectrum)", rx=4))
parts.append(text(px0 + pw / 2, py0 + ph + 105, "Wavelength (nanometres)", 19, 700, anchor="middle"))
parts.append(text(px0 - 92, py0 + ph / 2, "Spectral irradiance (W m⁻² nm⁻¹)", 18, 700, anchor="middle", rotate=-90))

# Annotation near 558 nm.
aw = 558
av = irradiance[aw - 280]
ax = px0 + (aw - 280) / 560 * pw
ay = py0 + ph - (av / top_y) * ph
parts.append(f'<line x1="{ax+8:.1f}" y1="{ay-8:.1f}" x2="{ax+85:.1f}" y2="{ay-75:.1f}" stroke="#687580" stroke-width="2"/>')
parts.append(text(ax + 92, ay - 82, "airglow feature", 15, 700, "#53616c"))
parts.append(text(ax + 92, ay - 62, "near 558 nm", 15, 400, "#53616c"))

parts.append(text(900, 974, "One column = 4 metadata values + 561 irradiance values (280–840 nm, 1 nm spacing).  NaN = wavelength outside usable spectrometer range.", 17, 400, "#5f6b76", "middle"))
parts.append("</svg>")

SVG_OUTPUT.write_text("\n".join(parts), encoding="utf-8")
print(SVG_OUTPUT)
