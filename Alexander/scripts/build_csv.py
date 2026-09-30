"""Merge research rows with spectral reference values -> alan_streetlight_cct_50cities.csv"""
import csv, glob, json
import pandas as pd

ref = pd.read_csv('lamp_class_reference.csv').set_index('lamp_class')
def val(cls, col):
    return float(ref.loc[cls, col].split(' ')[0]) if isinstance(ref.loc[cls, col], str) else float(ref.loc[cls, col])

MEL = {c: ref.loc[c, 'mel_der_median'] for c in ref.index}
BLUE = {c: ref.loc[c, 'blue_frac_450_median'] for c in ref.index}
DNB = {c: val(c, 'dnb_per_lm_rel_hps_snpp') for c in ref.index if isinstance(ref.loc[c, 'dnb_per_lm_rel_hps_snpp'], str)}

H, L27, L30, L40, L50, L57, MH = 'HPS', 'LED 2700K', 'LED 3000K', 'LED 4000K', 'LED 5000K', 'LED 5700-6500K', 'MH (quartz)'

# city -> (point composition or None, [alternative compositions spanning the uncertainty], basis)
# compositions are {class: share}; shares are fixture shares used as lumen-share proxy.
C = {
 'Beijing':      ({L30: .6, H: .4}, [{L30: .46, H: .54}, {L30: .9, H: .1}], 'LED 3000K share 46-90% (Phase 1 done Jan 2026; Phase 2 due end-2026); point at the plan\'s 60%'),
 'Hefei':        ({L30: .15, H: .85}, [{L30: .15, H: .85}, {L57: .15, H: .85}], '14.6% LED (CCT 3000-5700K bracket) + HPS; HPS-dominated so mel-DER is tightly bounded'),
 'Hong Kong':    ({L30: .9, H: .1}, [{L30: .9, H: .1}, {L30: .8, L40: .1, H: .1}], '>90% LED 3000K (roads) with 4000K footbridges/subways, residual HPS'),
 'New Taipei':   (None, [{L27: 1}, {L30: 1}], '100% LED, "yellow"/low-CCT policy: bracket 2700-3000K'),
 'Belo Horizonte': ({L40: 1}, [{L40: 1}], '~100% LED at 4000K (inferred from Brazilian PPP practice)'),
 'Sao Paulo':    ({L40: .9, H: .1}, [{L40: .75, H: .25}, {L40: .9, H: .1}], 'LED 4000K (spec 4000+/-300K), 75-90% LED'),
 'Madrid':       ({L30: .669, H: .331}, [{L30: .669, H: .331}, {L30: .5, L40: .169, H: .331}], '66.9% LED (2025) mostly 3000K, remainder HPS'),
 'Dallas':       ({H: .9, L30: .05, L40: .05}, [{H: .9, L30: .1}, {H: .9, L40: .1}], '~90% HPS, ~10% LED of unknown CCT (3000-4000K bracket)'),
 'Houston':      ({L40: 1}, [{L40: 1}], 'LED 4000K assumed for the whole CenterPoint stock (pre-2016 conversion)'),
 'Toronto':      ({H: .69, MH: .21, L30: .10}, [{H: .69, MH: .21, L30: .10}], 'Toronto Hydro 2026 inventory: 69% HPS, 21% MH 4000K acorns, 10% LED 3000K'),
 'Philadelphia': ({L30: 1}, [{L30: 1}], '100% LED 3000K (completed Oct 2025)'),
 'New York':     ({L40: .5, L30: .5}, [{L40: 1}, {L30: 1}], 'LED; 4000K in Brooklyn/Queens, 3000K elsewhere post-2017; split unknown (point = 50/50)'),
 'Boston':       ({L40: .79, H: .21}, [{L40: .79, H: .21}, {L30: .79, H: .21}], '~79% LED (CCT 4000K inferred; 3000K bracket), remainder assumed HPS'),
 'Phoenix':      ({L27: 1}, [{L27: 1}], '100% LED 2700K'),
 'Jaipur':       ({L57: .88, H: .12}, [{L50: .88, H: .12}, {L57: .88, H: .12}], '88% LED at EESL spec 5000/5700K, remainder HPS'),
 'Mumbai':       (None, [{L27: .998}, {L57: .998}], '99.8% LED, warm (2700-3300K) and cool (4500-5700K) zones, split unknown'),
 'Delhi':        ({L57: 1}, [{L50: 1}, {L57: 1}], 'LED at EESL spec 5000/5700K (documented for South Delhi only)'),
 'Singapore':    (None, [{L30: .99, H: .01}, {L40: .99, H: .01}], '99% LED, mix of 3000K and 4000K, split unknown'),
 'Abidjan':      ({H: 1}, [{H: 1}, {H: .9, L40: .1}], 'HPS-dominated; small LED 4000K fraction (0-10% bracket)'),
 'Johannesburg': (None, [{H: 1}, {H: .7, MH: .3}], 'HPS with unquantified MH share; LED ~1% (2022)'),
}

def mix(comp, table):
    if any(k not in table for k in comp): return None
    tot = sum(comp.values())
    return sum(table[k] * s for k, s in comp.items()) / tot

def fmt(x, n=2): return '' if x is None else f'{x:.{n}f}'

rows = {}
for f in sorted(glob.glob('rows/*.json')):
    for r in json.load(open(f)):
        rows[r['city'].replace('Santiago (Chile)', 'Santiago')] = r

ORDER = ['Baghdad', 'Addis Ababa', 'Dar es Salaam', 'Abidjan', 'Shantou', 'Nairobi', 'Pune', 'Hefei', 'Yangon',
 'Jinan', 'Shijiazhuang', 'Qingdao', 'Zhengzhou', 'Beijing', 'Jaipur', 'Mumbai', 'Ningbo', 'Kano', 'Dongguan',
 'Foshan', 'Riyadh', 'Santiago', 'Dalian', 'Delhi', 'Shenyang', 'Dhaka', 'Shanghai', 'Singapore', 'Tel Aviv',
 'Dallas', 'Mexico City', 'Houston', 'Harbin', 'Miami', 'Toronto', 'Cairo', 'Belo Horizonte', 'Tokyo',
 'Philadelphia', 'New York', 'Hong Kong', 'Boston', 'Phoenix', 'Atlanta', 'Sao Paulo', 'New Taipei',
 'Alexandria', 'Madrid', 'Johannesburg', 'Khartoum']

NOT_RESEARCHED = 'NOT RESEARCHED: session web-search quota exhausted before this city was reached. Blank = no evidence gathered, not evidence of absence.'

out = []
for city in ORDER:
    r = rows[city]
    point, alts, basis = C.get(city, (None, [], ''))
    mel = mix(point, MEL) if point else None
    blue = mix(point, BLUE) if point else None
    dnb = mix(point, DNB) if point else None
    mels = [mix(a, MEL) for a in alts]
    dnbs = [x for x in (mix(a, DNB) for a in alts) if x is not None]
    blues = [mix(a, BLUE) for a in alts]
    mel_rng = f'{min(mels):.2f}-{max(mels):.2f}' if mels else ''
    blue_rng = f'{min(blues):.2f}-{max(blues):.2f}' if blues else ''
    dnb_rng = f'{min(dnbs):.2f}-{max(dnbs):.2f}' if dnbs else ''
    notes = r.get('notes') or ''
    if not r.get('source_url') and not r.get('dominant_tech') and not r.get('spd_hint'):
        notes = NOT_RESEARCHED + (' ' + notes if notes else '')
    if basis:
        notes = f'[SPECTRAL: {basis}. mel-DER/blue/DNB are lumen-weighted mixes of measured lamp-class medians (lamp_class_reference.csv).] ' + notes
    out.append(dict(
        city=city,
        cct_k=r.get('cct_k') or '',
        cct_range=r.get('cct_range') or '',
        dominant_tech=r.get('dominant_tech') or '',
        led_share_pct=r.get('led_share_pct') if r.get('led_share_pct') is not None else '',
        retrofit_start=r.get('retrofit_start') or '',
        retrofit_end=r.get('retrofit_end') or '',
        melanopic_der=fmt(mel),
        blue_frac_450=fmt(blue),
        confidence='' if (r.get('dominant_tech') in (None, '', 'unknown') and not r.get('cct_range')) else (r.get('confidence') or ''),
        source_url=r.get('source_url') or '',
        notes=notes,
        melanopic_der_range=mel_rng,
        blue_frac_450_range=blue_rng,
        dnb_per_lumen_rel_hps=fmt(dnb),
        dnb_per_lumen_rel_hps_range=dnb_rng,
        spd_hint=r.get('spd_hint') or '',
    ))

keys = list(out[0].keys())
with open('alan_streetlight_cct_50cities.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, keys); w.writeheader(); w.writerows(out)
df = pd.DataFrame(out)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 60)
print(df[['city', 'cct_k', 'dominant_tech', 'led_share_pct', 'melanopic_der', 'melanopic_der_range',
          'blue_frac_450', 'dnb_per_lumen_rel_hps', 'dnb_per_lumen_rel_hps_range', 'confidence']].to_string(index=False))
print(df.confidence.value_counts())
