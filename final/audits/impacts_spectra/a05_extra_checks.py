"""Extra axis-linearity check: the printed 0.6 label (no tick mark) and the axis-line ends vs the fit from the 0.0-0.5 ticks."""
import json
A = json.load(open("audits/impacts_spectra/results/a01_extract.json"))
y06 = A["ay"]*0.6 + A["by"]; lab = 140.3248 + 0  # label '0.6' centre (a01_log)
print("predicted page y of 0.6: %.3f ; label centre - 3.99 (constant label offset seen for 0.0-0.5) = %.3f ; diff %.3f pt = %.2e value units"
      % (y06, lab - 3.99, lab - 3.99 - y06, (lab - 3.99 - y06)/A["ay"]))
# y axis line ends (from SVG: page y = 792 - 0.6*1092.851562 and 792 - 0.6*840.833333)
top = 792 - 0.6*1092.851562; print("y-axis top end page y %.3f -> value %.4f" % (top, (top - A["by"])/A["ay"]))
for k, c in A["curves"].items(): print(k, "first/last nm: %.3f %.3f" % (c["nm"][0], c["nm"][-1]))
