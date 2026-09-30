"""Aggregate lamp_spectra_all.csv into per-technology reference values (median, min-max).

Class membership uses the lamp type in the spectrum name plus the CCT computed from the SPD.
Decorative/coloured/indoor-only oddities are excluded. DNB factors use LICA only (>=900 nm).
"""
import pandas as pd, numpy as np

d = pd.read_csv('lamp_spectra_all.csv')
d = d[~d.spectrum.str.contains('Animal|Flame|LED_Color_|Incand|Halogen|Neon|Thorium|Pen_Ray|23223K|25000K'
                               '|blue-color|red-color|green-color|yellow-color|CIE A$|CIE D65|Deco_LED|Projector'
                               '|filtered', case=False)]
name = d.spectrum
is_led = name.str.contains(r'LED') & ~name.str.contains('Amber|Ambar')
c = d.cct_calc

CLASSES = {
    'HPS':            name.str.contains(r'HPS|HP1$') & ~name.str.contains('HP2'),
    'LED 2200K':      is_led & c.between(2000, 2350),
    'LED 2700K':      is_led & c.between(2550, 2850),
    'LED 3000K':      is_led & c.between(2850, 3250),
    'LED 3500K':      is_led & c.between(3250, 3750),
    'LED 4000K':      is_led & c.between(3750, 4400),
    'LED 5000K':      is_led & c.between(4400, 5500),
    'LED 5700-6500K': is_led & c.between(5500, 7000),
    'PC amber LED':   name.str.contains('Amber|Ambar'),
    'MH (quartz)':    name.str.contains(r'LICA MH_|LSPDD \d+ MH_|CIE HP[345]'),
    'CMH warm':       name.str.contains('CMH') & (c < 3500),
    'Mercury vapour': name.str.contains('MV_Mercury'),
    'Fluorescent/CFL cool': name.str.contains(r'FL_Fluor|CFL|CIE FL') & (c > 3500),
    'LPS':            name.str.contains('LPS'),
}

def agg(s):
    s = s.dropna()
    if not len(s): return ''
    return f"{s.median():.2f} ({s.min():.2f}-{s.max():.2f})"

rows = []
for cls, m in CLASSES.items():
    sub = d[m]
    lica = sub[sub.library == 'LICA']
    rows.append(dict(
        lamp_class=cls, n_spectra=len(sub), n_lica=len(lica),
        mel_der_median=round(sub.mel_der.median(), 3), mel_der_range=agg(sub.mel_der),
        blue_frac_450_median=round(sub.blue_frac_450.median(), 3), blue_frac_450_range=agg(sub.blue_frac_450),
        dnb_per_lm_rel_hps_snpp=agg(lica.dnb_rel_hps_snpp),
        dnb_per_lm_rel_hps_n20=agg(lica.dnb_rel_hps_n20),
        members='; '.join(sub.spectrum.str.slice(0, 70))))
out = pd.DataFrame(rows)
out.to_csv('lamp_class_reference.csv', index=False)
pd.set_option('display.width', 250)
print(out.drop(columns='members').to_string(index=False))
