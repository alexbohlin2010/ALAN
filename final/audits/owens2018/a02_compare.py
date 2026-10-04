"""a02: independent parse of Table 1 / Results-text p-values / dark base values from the PDFKit text
(results/page5.txt, page6.txt written by a01_extract_text.js) and field-by-field comparison with
data/derived/impacts/owens2018_results.json. stdlib only. Writes results/a02_compare.txt and .json"""
import json, re, os
H = os.path.dirname(os.path.abspath(__file__)); R = H + '/results'
ROOT = os.path.abspath(H + '/../..')
J = json.load(open(ROOT + '/data/derived/impacts/owens2018_results.json'))
out = []
def log(s): out.append(s); print(s)

p6 = open(R + '/page6.txt', encoding='utf-8').read()
p5 = open(R + '/page5.txt', encoding='utf-8').read()

# ---- Table 1 independent parse
lines = p6.split('\n')
rowre = re.compile(r'^(\d{3}) (\d+) ±(\d+) ([\d.]+) ([\d.]+) ([\d.]+) ±([\d.]+) ([\d.]+) ([\d.]+)$')
rows = []; block = None
for ln in lines:
    if ln.startswith('Dim (1×)'): block = 'dim'
    if ln.startswith('Bright (10×)'): block = 'bright'
    m = rowre.match(ln.strip())
    if m and block:
        g = m.groups()
        rows.append(dict(exposure=block, wl=int(g[0]), i_mean=g[1], i_sd=g[2], i_ratio=g[3], i_p=g[4],
                         f_mean=g[5], f_sd=g[6], f_ratio=g[7], f_p=g[8], line=ln.strip()))
log('A. Table 1 rows parsed: %d (dim %d, bright %d)' % (len(rows), sum(r['exposure']=='dim' for r in rows), sum(r['exposure']=='bright' for r in rows)))
wl_d = [r['wl'] for r in rows if r['exposure']=='dim']; wl_b = [r['wl'] for r in rows if r['exposure']=='bright']
log('   wavelengths dim %s ; bright %s ; identical=%s ; unique=%s' % (wl_d, wl_b, wl_d == wl_b, len(set(wl_d)) == 8))
base = re.search(r'average flash intensity: (\d+) counts; frequency: ([\d.]+) peaks/min', p6)
BI, BF = float(base.group(1)), float(base.group(2))
log('   dark base: intensity %s counts, frequency %s peaks/min (page 6 note)' % (BI, BF))

jrows = J['table1']['rows']
log('   JSON rows: %d' % len(jrows))
bad = 0
for r in rows:
    j = [x for x in jrows if x['exposure']==r['exposure'] and x['wavelength_nm']==r['wl']]
    if len(j) != 1: log('   MISSING/DUP in JSON %s %s' % (r['exposure'], r['wl'])); bad += 1; continue
    j = j[0]
    pairs = [('i_mean', j['flash_intensity']['mean']), ('i_sd', j['flash_intensity']['sd']), ('i_ratio', j['flash_intensity']['ratio_to_dark']),
             ('i_p', j['flash_intensity']['p']), ('f_mean', j['flash_frequency']['mean']), ('f_sd', j['flash_frequency']['sd']),
             ('f_ratio', j['flash_frequency']['ratio_to_dark']), ('f_p', j['flash_frequency']['p'])]
    for k, v in pairs:
        if float(r[k]) != float(v): log('   MISMATCH %s %s %s: pdf %s json %r' % (r['exposure'], r['wl'], k, r[k], v)); bad += 1
    # printed string check
    norm = r['line'].replace('  ', ' ')
    if j['printed'] != norm: log('   printed-string differs %s %s: %r vs %r' % (r['exposure'], r['wl'], j['printed'], norm)); bad += 1
log('   field mismatches Table 1: %d (8 numeric fields x 16 rows = 128 compared + 16 printed strings)' % bad)

# order of JSON rows
log('   JSON row order: ' + ', '.join('%s%d' % (x['exposure'][0], x['wavelength_nm']) for x in jrows))

# ratio ~ mean / dark
log('B. Ratio vs mean/dark base (rounded to printed 3 dp):')
maxd = 0; nbad = 0
for r in rows:
    ri = float(r['i_mean']) / BI; rf = float(r['f_mean']) / BF
    di = abs(round(ri, 3) - float(r['i_ratio'])); df = abs(round(rf, 3) - float(r['f_ratio']))
    maxd = max(maxd, di, df)
    if di > 0.0011 or df > 0.0011:
        nbad += 1; log('   %s %d: intensity %.4f vs printed %s ; frequency %.4f vs printed %s' % (r['exposure'], r['wl'], ri, r['i_ratio'], rf, r['f_ratio']))
log('   max |recomputed - printed| = %.4f ; rows beyond 0.0011: %d' % (maxd, nbad))

# ---- Results text p-values
txt = (p5 + '\n' + p6).replace('\n', ' ')
txt = re.sub(r'\s+', ' ', txt)

def seg(a, b):
    i = txt.index(a); j = txt.index(b, i); return txt[i:j]
S = {
 ('dim','flash_intensity'): seg('exposed to dim intensities', 'Increases in flash intensity'),
 ('dim','flash_frequency'): seg('Increases in flash intensity under dim', 'The decline is due'),
 ('bright','flash_frequency'): seg('More extreme reductions', 'In fact, under bright'),
 ('bright','flash_intensity'): seg('Due to the consequent lack of data', 'Notably,'),
}
tp = {}
for (e, m), s in S.items():
    for mm in re.finditer(r'(\d{3}) nm: p\s*(=|<)?\s*(?:p\s*)?(<)?\s*(=)?\s*([\d.]+)|(\d{3}) nm: p (<)([\d.]+)', s):
        pass
    for mm in re.finditer(r'(\d{3}) nm: (p [^;,)]*?)(?=[;,)]|\s*nm|$)', s + ')'):
        tp[(e, m, int(mm.group(1)))] = mm.group(2).strip()
# page-break case: p5 ends '...515 nm: p = 0.0018, 533 nm:' and p6 continues 'p = 0.032). In fact'
assert p5.rstrip().endswith('5 / 14') and '533 nm:\nPLOS ONE' in p5 and 'p = 0.032). In fact' in p6
tp[('bright','flash_frequency',533)] = 'p = 0.032'
log('C. Text p-values parsed: %d (19 by regex + 1 across the page 5/6 break, handled explicitly)' % len(tp))
for k, v in sorted(tp.items()): log('   %s %s %d: %r' % (k[0], k[1], k[2], v))
jt = J['text_p_values']
log('   JSON text_p_values: %d' % len(jt))
bad = 0
for (e, m, w), v in tp.items():
    j = [x for x in jt if x['exposure']==e and x['measure']==m and x['wavelength_nm']==w]
    if len(j) != 1: log('   MISSING %s' % ((e,m,w),)); bad += 1; continue
    num = float(re.search(r'[\d.]+$', v).group()); cmp_ = '<' if '<' in v else '='
    if num != j[0]['p'] or cmp_ != j[0]['comparator']: log('   MISMATCH %s: pdf %r json %s %s' % ((e,m,w), v, j[0]['comparator'], j[0]['p'])); bad += 1
log('   text p mismatches: %d' % bad)

# ---- text vs table
dis = []
for (e, m, w), v in sorted(tp.items()):
    r = [x for x in rows if x['exposure']==e and x['wl']==w][0]
    tv = float(r['i_p'] if m == 'flash_intensity' else r['f_p'])
    num = float(re.search(r'[\d.]+$', v).group())
    ok = (tv < num) if '<' in v else (tv == num)
    if not ok: dis.append((e, m, w, v, tv))
log('D. Independent text-vs-Table disagreements (%d):' % len(dis))
for d in dis: log('   %s' % (d,))
jd = [(x['exposure'], x['measure'], x['wavelength_nm']) for x in J['text_vs_table1']['disagreements']]
log('   JSON lists %d: %s ; sets equal=%s ; JSON checks=%d' % (len(jd), jd, set(jd) == set(d[:3] for d in dis), len(J['text_vs_table1']['checks'])))
open(R + '/a02_compare.txt', 'w').write('\n'.join(out) + '\n')
