"""Melanopic DER, blue fraction and VIIRS-DNB response for reference lamp spectra.

Inputs (all under spectra/):
  s026_toolbox.xlsx   CIE S 026 alpha-opic Toolbox v1.049a: s_mel(lambda), V(lambda), K_D65 mel ELR
  colour-science      CIE 015:2018 illuminant tables HP1-5, LED-B1..B5, LED-V*, FL*
  lspdd/*.json        LSPDD (Univ. de Sherbrooke) measured SPDs, 380-780 nm
  lica/*.txt          LICA-UCM (Univ. Complutense Madrid) measured SPDs, 300-900 nm, flux-corrected
  dnb_*.csv           VIIRS DNB relative spectral response (S-NPP, NOAA-20) via pyspectral

Definitions:
  mel_der        melanopic daylight (D65) efficacy ratio, CIE S 026:2018
  blue_frac_450  radiant power 400-500 nm / radiant power 380-780 nm
  dnb_rel_hps    DNB signal per photopic lumen, relative to the median LICA HPS spectrum.
                 Only computed for spectra that extend to >=890 nm (LICA); CIE/LSPDD stop at
                 780 nm and would omit HPS's 819 nm Na doublet, which DNB sees.
"""
import csv, glob, json, re, warnings
import numpy as np, openpyxl
warnings.filterwarnings('ignore')
import colour

WL = np.arange(380, 901, 1.0)
VIS = WL <= 780
SP = 'spectra/'
wb = openpyxl.load_workbook(SP + 's026_toolbox.xlsx', data_only=True, read_only=True)

def col(sheet, wl_col, val_col):
    rows = list(wb[sheet].iter_rows(values_only=True))[20:421]
    w = np.array([r[wl_col] for r in rows], float)
    v = np.array([r[val_col] if isinstance(r[val_col], (int, float)) else np.nan for r in rows], float)
    ok = ~np.isnan(w) & ~np.isnan(v)
    return np.interp(WL, w[ok], v[ok], left=0, right=0)

MEL = col('Action spectra', 1, 6)
V = col('Photobiology', 8, 9)
K_MEL_D65 = 1.32621318911359e-3   # W/lm
KM = 683.0015477902268

def load_rsr(name):
    d = np.loadtxt(SP + f'dnb_{name}.csv', delimiter=',', skiprows=1)
    return np.interp(WL, d[:, 0], d[:, 1], left=0, right=0)
DNB = {'snpp': load_rsr('Suomi-NPP'), 'n20': load_rsr('NOAA-20')}

def cct_of(S):
    s = S[VIS]
    sd = colour.SpectralDistribution(dict(zip(WL[VIS], s)))
    xy = colour.XYZ_to_xy(colour.sd_to_XYZ(sd))
    return float(colour.uv_to_CCT(colour.xy_to_UCS_uv(xy), method='Ohno 2013')[0])

def metrics(S, full_range):
    S = np.clip(S, 0, None)
    lum = KM * np.sum(S * V)
    tot = np.sum(S[VIS])
    out = dict(cct_calc=cct_of(S),
               mel_der=np.sum(S * MEL) / lum / K_MEL_D65,
               blue_frac_450=np.sum(S[(WL >= 400) & (WL < 500)]) / tot,
               frac_below_500=np.sum(S[WL < 500]) / tot)
    for k, R in DNB.items():
        out[f'dnb_per_lm_{k}'] = np.sum(S * R) / lum if full_range else np.nan
    return out

spectra = {}
for name in ['HP1', 'HP2', 'HP3', 'HP4', 'HP5', 'LED-B1', 'LED-B2', 'LED-B3', 'LED-B4', 'LED-B5',
             'LED-BH1', 'LED-V1', 'LED-V2', 'FL2', 'FL11', 'A', 'D65']:
    sd = colour.SDS_ILLUMINANTS[name]
    spectra[f'CIE {name}'] = dict(S=np.interp(WL, sd.wavelengths, sd.values, left=0, right=0),
                                  src='CIE 015:2018 table (colour-science)', full=False, lib='CIE')

for f in sorted(glob.glob(SP + 'lspdd/*.json')):
    for c in json.load(open(f)):
        for sc in c.get('spectral_captures') or []:
            if not sc.get('spectral_datas'): continue
            a = np.array(sc['spectral_datas'], float)
            spectra[f"LSPDD {c['lamp_id']} {c['lamps']['name']}"] = dict(
                S=np.interp(WL, a[:, 0], a[:, 1], left=0, right=0),
                src=f"https://lspdd.org/app/en/lamps/{c['lamp_id']}", full=False, lib='LSPDD')
            break

for f in sorted(glob.glob(SP + 'lica/*.txt')):
    pts = []
    for line in open(f, encoding='latin-1'):
        p = line.split()
        try: pts.append((float(p[0]), float(p[1])))
        except (ValueError, IndexError): pass
    a = np.array(pts)
    if len(a) < 100: continue
    base = f.split('/')[-1]
    spectra['LICA ' + re.sub(r'_cor+\.txt$', '', base)] = dict(
        S=np.interp(WL, a[:, 0], a[:, 1], left=0, right=0),
        src='https://guaix.fis.ucm.es/sites/default/files/lamps_spectra/' + base,
        full=a[:, 0].max() >= 890, lib='LICA')

rows = []
for k, d in spectra.items():
    rows.append(dict(spectrum=k, library=d['lib'], source=d['src'], **metrics(d['S'], d['full'])))

hps = [r for r in rows if r['library'] == 'LICA' and r['spectrum'].startswith('LICA HPS')]
for k in DNB:
    ref = np.median([r[f'dnb_per_lm_{k}'] for r in hps])
    for r in rows:
        r[f'dnb_rel_hps_{k}'] = r[f'dnb_per_lm_{k}'] / ref

keys = ['spectrum', 'library', 'cct_calc', 'mel_der', 'blue_frac_450', 'frac_below_500',
        'dnb_rel_hps_snpp', 'dnb_rel_hps_n20', 'source']
with open('lamp_spectra_all.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, keys, extrasaction='ignore'); w.writeheader()
    for r in rows:
        w.writerow({k: ('' if isinstance(v, float) and np.isnan(v) else round(v, 4) if isinstance(v, float) else v)
                    for k, v in r.items()})
print(len(rows), 'spectra written')
