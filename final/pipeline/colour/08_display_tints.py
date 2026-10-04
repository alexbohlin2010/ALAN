"""Display tints for the class layer: blackbody colour at each class's nominal CCT.

Planck spectrum (380-780 nm, 1 nm) x CIE 1931 2-degree colour-matching functions, using the
analytic multi-lobe fit of Wyman, Sloan & Shirley 2013 (JCGT 2(2), "Simple Analytic
Approximations to the CIE XYZ Color Matching Functions") -> XYZ -> linear sRGB
(IEC 61966-2-1 matrix, D65) -> negatives clipped to 0 -> scaled so the largest channel is 1
-> sRGB-encoded. A display choice (human, 2026-10-03), not data.
Also the display-ramp white tint at RAMP_WHITE_CCT_K (human 2026-10-04, "move white to 3200k", AI_LOG
colour step 65; used by app/src/tileLayer.js RAMP_TINTS). Writes data/derived/colour/display_tints.json.
Run from final/:  .venv/bin/python pipeline/colour/08_display_tints.py
"""
import json
import numpy as np
from config import *

RAMP_WHITE_CCT_K = 3200

def g(x, mu, s1, s2):
    return np.exp(-0.5 * ((x - mu) / np.where(x < mu, s1, s2)) ** 2)

def cmf(l):
    x = 1.056 * g(l, 599.8, 37.9, 31.0) + 0.362 * g(l, 442.0, 16.0, 26.7) - 0.065 * g(l, 501.1, 20.4, 26.2)
    y = 0.821 * g(l, 568.8, 46.9, 40.5) + 0.286 * g(l, 530.9, 16.3, 31.1)
    z = 1.217 * g(l, 437.0, 11.8, 36.0) + 0.681 * g(l, 459.0, 26.0, 13.8)
    return np.stack([x, y, z])

M = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])

def tint(cct):
    l = np.arange(380.0, 781.0)
    lm = l * 1e-9
    planck = 1 / (lm ** 5 * (np.exp(1.438776877e-2 / (lm * cct)) - 1))
    rgb = np.clip(M @ (cmf(l) @ planck), 0, None)
    rgb /= rgb.max()
    enc = np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)
    return [round(float(v), 4) for v in enc]

def main():
    out = {str(k): dict(cls=CLASSES[k], cct_k=t, srgb=tint(t)) for k, t in TINT_CCT_K.items()}
    out["ramp_white"] = dict(cct_k=RAMP_WHITE_CCT_K, srgb=tint(RAMP_WHITE_CCT_K))
    out["note"] = "display choice (human, 2026-10-03); not a measured colour"
    (DERIVED / "display_tints.json").write_text(json.dumps(out, indent=1))
    for k, v in out.items(): print(k, v)

if __name__ == "__main__":
    main()
