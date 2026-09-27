from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle


SOURCE = Path(
    "/Users/lindaxiangyideng/Documents/FA26 studio A2/data/"
    "philadelphia and cherry springs data/CSSP_spectra.csv"
)
OUTPUT = Path(
    "/Users/lindaxiangyideng/Documents/FA26 studio A2/analysis/"
    "cssp-timestamp-column-explainer.png"
)
TARGET_TIMESTAMP = "01-Jul-2014 02:00:39"


def wavelength_to_rgb(wavelength: float) -> tuple[float, float, float]:
    """Approximate visible-spectrum color for a wavelength in nanometres."""
    if wavelength < 380 or wavelength > 780:
        return (0.75, 0.75, 0.75)
    if wavelength < 440:
        red, green, blue = -(wavelength - 440) / 60, 0.0, 1.0
    elif wavelength < 490:
        red, green, blue = 0.0, (wavelength - 440) / 50, 1.0
    elif wavelength < 510:
        red, green, blue = 0.0, 1.0, -(wavelength - 510) / 20
    elif wavelength < 580:
        red, green, blue = (wavelength - 510) / 70, 1.0, 0.0
    elif wavelength < 645:
        red, green, blue = 1.0, -(wavelength - 645) / 65, 0.0
    else:
        red, green, blue = 1.0, 0.0, 0.0
    if wavelength < 420:
        factor = 0.3 + 0.7 * (wavelength - 380) / 40
    elif wavelength <= 700:
        factor = 1.0
    else:
        factor = 0.3 + 0.7 * (780 - wavelength) / 80
    return (red * factor, green * factor, blue * factor)


with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.reader(handle))

timestamps = [value for value in rows[0] if value]
column_index = timestamps.index(TARGET_TIMESTAMP)
column_values = []
for row in rows[1:]:
    raw = row[column_index]
    column_values.append(float(raw) if raw not in ("", "NaN") else np.nan)

date_number, solar_elevation, lunar_elevation, lunar_fraction = column_values[:4]
wavelengths = np.arange(280, 841)
irradiance = np.asarray(column_values[4:], dtype=float)

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.titleweight": "bold",
        "axes.labelcolor": "#27313a",
        "text.color": "#27313a",
        "xtick.color": "#52606d",
        "ytick.color": "#52606d",
    }
)

fig = plt.figure(figsize=(16, 9), dpi=170, facecolor="#fbfcfe")
grid = fig.add_gridspec(1, 3, width_ratios=[0.95, 1.12, 2.15], wspace=0.25)
ax_matrix = fig.add_subplot(grid[0, 0])
ax_column = fig.add_subplot(grid[0, 1])
ax_plot = fig.add_subplot(grid[0, 2])

fig.suptitle(
    "One timestamp column contains one complete spectrum",
    fontsize=24,
    fontweight="bold",
    x=0.5,
    y=0.965,
)
fig.text(
    0.5,
    0.925,
    "Actual CSSP example: 01-Jul-2014 02:00:39  •  The DRL file uses the same structure",
    ha="center",
    color="#5f6b76",
    fontsize=12.5,
)

# Panel 1: schematic of the wide CSV matrix.
ax_matrix.set_xlim(0, 7)
ax_matrix.set_ylim(0, 14)
ax_matrix.axis("off")
ax_matrix.set_title("1. Find a timestamp column", loc="left", fontsize=15, pad=16)

left, bottom = 0.55, 2.15
cell_w, cell_h = 0.95, 0.72
n_cols, n_rows = 6, 11
highlight = 2

for col in range(n_cols):
    x = left + col * cell_w
    header_color = "#1f5f99" if col == highlight else "#dbe3ea"
    text_color = "white" if col == highlight else "#43515d"
    ax_matrix.add_patch(
        Rectangle((x, bottom + n_rows * cell_h), cell_w, 1.35, facecolor=header_color, edgecolor="white")
    )
    header_text = "selected\ntime" if col == highlight else f"time\n{col + 1}"
    ax_matrix.text(x + cell_w / 2, bottom + n_rows * cell_h + 0.67, header_text,
                   ha="center", va="center", fontsize=9, color=text_color, fontweight="bold")
    for row in range(n_rows):
        y = bottom + (n_rows - 1 - row) * cell_h
        if col == highlight:
            fill = "#d8ebfb" if row < 4 else "#eaf4fc"
        else:
            fill = "#f0f3f6" if row < 4 else "#f7f9fb"
        ax_matrix.add_patch(Rectangle((x, y), cell_w, cell_h, facecolor=fill, edgecolor="white"))

ax_matrix.text(left, bottom + n_rows * cell_h + 1.75, "TIMESTAMP COLUMNS →", fontsize=10,
               fontweight="bold", color="#5f6b76")
ax_matrix.text(0.05, bottom + 8.4 * cell_h, "metadata", rotation=90, va="center",
               fontsize=10, color="#5f6b76")
ax_matrix.text(0.05, bottom + 3.3 * cell_h, "wavelength rows", rotation=90, va="center",
               fontsize=10, color="#5f6b76")

row_labels = ["date #", "sun °", "moon °", "moon fraction", "280 nm", "281 nm", "…", "400 nm", "…", "700 nm", "840 nm"]
for row, label in enumerate(row_labels):
    y = bottom + (n_rows - 1 - row) * cell_h + cell_h / 2
    ax_matrix.text(left - 0.08, y, label, ha="right", va="center", fontsize=9, color="#52606d")

ax_matrix.text(
    left + highlight * cell_w + cell_w / 2,
    1.2,
    "One vertical slice\n= one observation",
    ha="center",
    va="center",
    fontsize=11,
    fontweight="bold",
    color="#1f5f99",
)

# Panel 2: the selected real column expanded.
ax_column.set_xlim(0, 1)
ax_column.set_ylim(0, 14)
ax_column.axis("off")
ax_column.set_title("2. Read that column", loc="left", fontsize=15, pad=16)

ax_column.add_patch(
    Rectangle((0.07, 12.15), 0.86, 1.18, facecolor="#1f5f99", edgecolor="none")
)
ax_column.text(0.5, 12.74, TARGET_TIMESTAMP.replace(" ", "\n"), ha="center", va="center",
               color="white", fontweight="bold", fontsize=11)

metadata = [
    ("Date number", f"{date_number:.0f}"),
    ("Solar elevation", f"{solar_elevation:.1f}°"),
    ("Lunar elevation", f"{lunar_elevation:.1f}°"),
    ("Moon illuminated", f"{lunar_fraction:.3f}"),
]
y = 11.55
for label, value in metadata:
    ax_column.add_patch(Rectangle((0.07, y - 0.48), 0.86, 0.62, facecolor="#d8ebfb", edgecolor="white"))
    ax_column.text(0.11, y - 0.17, label, ha="left", va="center", fontsize=9.5)
    ax_column.text(0.89, y - 0.17, value, ha="right", va="center", fontsize=9.5, fontweight="bold")
    y -= 0.68

ax_column.text(0.07, 8.55, "561 measured wavelength values", fontsize=10.5,
               fontweight="bold", color="#1f5f99")

sample_wavelengths = [280, 360, 400, 450, 500, 558, 600, 700, 840]
y = 8.1
for index, wavelength in enumerate(sample_wavelengths):
    value = irradiance[wavelength - 280]
    fill = "#eef6fc" if index % 2 == 0 else "#f7fafc"
    ax_column.add_patch(Rectangle((0.07, y - 0.45), 0.86, 0.54, facecolor=fill, edgecolor="white"))
    ax_column.text(0.11, y - 0.18, f"{wavelength} nm", ha="left", va="center", fontsize=9.2)
    shown = "0" if value == 0 else f"{value:.2e}"
    ax_column.text(0.89, y - 0.18, shown, ha="right", va="center", fontsize=9.2,
                   family="DejaVu Sans Mono")
    y -= 0.57

ax_column.text(0.5, 2.25, "⋮", ha="center", va="center", fontsize=25, color="#8a98a5")
ax_column.text(0.5, 1.45, "Connect all 561 values\nin wavelength order", ha="center", va="center",
               fontsize=11, fontweight="bold", color="#1f5f99")

# Arrow between the expanded column and the spectrum plot.
fig.add_artist(
    FancyArrowPatch(
        (0.472, 0.52),
        (0.535, 0.52),
        transform=fig.transFigure,
        arrowstyle="-|>",
        mutation_scale=22,
        linewidth=2,
        color="#1f5f99",
    )
)

# Panel 3: actual complete spectrum.
ax_plot.set_title("3. The complete spectrum is a wavelength curve", loc="left", fontsize=15, pad=16)
ax_plot.set_facecolor("white")
ax_plot.axvspan(280, 400, color="#6f5bd3", alpha=0.055, lw=0)
ax_plot.axvspan(400, 700, color="#e8b04a", alpha=0.045, lw=0)
ax_plot.axvspan(700, 840, color="#b56a55", alpha=0.04, lw=0)
ax_plot.plot(wavelengths, irradiance, color="#195b8f", lw=2.1)

gradient_wavelengths = np.linspace(380, 780, 401)
gradient = np.array([[wavelength_to_rgb(value) for value in gradient_wavelengths]])
ymax = np.nanmax(irradiance)
ax_plot.imshow(
    gradient,
    aspect="auto",
    extent=(380, 780, -0.072 * ymax, -0.038 * ymax),
    interpolation="bicubic",
    clip_on=False,
    zorder=0,
)

for wavelength in [360, 450, 558, 700, 840]:
    value = irradiance[wavelength - 280]
    ax_plot.scatter([wavelength], [value], s=34, color="#f7f9fb", edgecolor="#195b8f", linewidth=1.5, zorder=4)

ax_plot.annotate(
    "airglow feature\nnear 558 nm",
    xy=(558, irradiance[558 - 280]),
    xytext=(585, ymax * 0.76),
    arrowprops=dict(arrowstyle="->", color="#6b7780", lw=1.2),
    fontsize=10,
    color="#53616c",
)

ax_plot.text(340, ymax * 1.045, "UV", ha="center", fontsize=10, color="#6655a8", fontweight="bold")
ax_plot.text(550, ymax * 1.045, "VISIBLE", ha="center", fontsize=10, color="#8b681e", fontweight="bold")
ax_plot.text(770, ymax * 1.045, "NEAR INFRARED", ha="center", fontsize=10, color="#8a5546", fontweight="bold")

ax_plot.set_xlim(280, 840)
ax_plot.set_ylim(0, ymax * 1.12)
ax_plot.set_xlabel("Wavelength (nanometres)", fontsize=12, fontweight="bold", labelpad=12)
ax_plot.set_ylabel("Spectral irradiance (W m⁻² nm⁻¹)", fontsize=12, fontweight="bold", labelpad=10)
ax_plot.grid(axis="y", color="#dce3e9", linewidth=0.8)
ax_plot.spines[["top", "right"]].set_visible(False)
ax_plot.spines[["left", "bottom"]].set_color("#9daab5")
ax_plot.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))

fig.text(
    0.5,
    0.045,
    "One timestamp column = 4 metadata values + 561 irradiance values (280–840 nm, 1 nm spacing).  "
    "Across the dataset, NaN means that wavelength was outside the spectrometer’s usable range.",
    ha="center",
    va="center",
    fontsize=10.5,
    color="#5f6b76",
)

fig.subplots_adjust(left=0.045, right=0.975, top=0.865, bottom=0.105)
fig.savefig(OUTPUT, bbox_inches="tight", facecolor=fig.get_facecolor())
print(OUTPUT)
