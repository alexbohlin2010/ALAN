"""a04: check every JSON `statements` entry (quote on stated page, numbers in quote), compare owens2018_pdftext.txt with the
independent PDFKit text (results/page*.txt), and check JSON-level invariants. stdlib only. Output results/a04_statements.txt"""
import json, re, os
H = os.path.dirname(os.path.abspath(__file__)); R = H + '/results'; ROOT = os.path.abspath(H + '/../..')
J = json.load(open(ROOT + '/data/derived/impacts/owens2018_results.json'))
out = []
def log(s): out.append(s); print(s)
def norm(s): return re.sub(r'\s+', ' ', s).replace('- ', '-') if False else re.sub(r'\s+', ' ', s)
pages = {i: norm(open('%s/page%d.txt' % (R, i), encoding='utf-8').read()) for i in range(1, 15)}
def squash(s): return re.sub(r'\s+', '', s)
sp = {i: squash(pages[i]) for i in pages}
# pdftext.txt vs own extraction
pt = open(ROOT + '/data/derived/impacts/owens2018_pdftext.txt', encoding='utf-8').read()
parts = re.split(r'^=== page (\d+) ===\n', pt, flags=re.M)
mine = {int(parts[i]): parts[i+1] for i in range(1, len(parts), 2)}
log('pdftext.txt pages: %d ; page numbers %s' % (len(mine), sorted(mine) == list(range(1, 15))))
diffs = 0
for i in range(1, 15):
    a = squash(mine[i]); b = sp[i]
    if a != b: diffs += 1; log('  page %d differs from independent PDFKit text (whitespace-insensitive): %d vs %d chars' % (i, len(a), len(b)))
log('  pages differing (whitespace-insensitive): %d' % diffs)

log('\nStatements: %d entries' % len(J['statements']))
for k, v in J['statements'].items():
    q = v['quote']; pg = v['page']
    found = [i for i in sp if squash(q) in sp[i]]
    ok = pg in found
    log('%-28s page %s quote_on_stated_page=%s (found on %s)' % (k, pg, ok, found))
log('')
# numbers read from quotes
def has(k, *nums):
    q = J['statements'][k]['quote']
    for n in nums:
        if str(n) not in q: log('  NUMBER NOT IN QUOTE %s: %s' % (k, n))
chk = {
 'collection_site': [('latitude', 24.990195), ('longitude', 121.555824)],
 'courtship_flash': [('peak_wavelength', 565), ('bandwidth', 60), ('n', 6)],
 'alarm_flash': [('duration_approx', 200)],
 'recorded_band': [('from', 565), ('to', 569)],
 'sampling': [('interval', 100)],
 'dim_bright_flux': [('dim', 0.107), ('dim_pm', 0.02), ('bright', 1.075), ('bright_pm', 0.212)],
 'dim_bright_lux': [('dim', 20), ('bright', 200)],
 'noise_threshold': [('threshold', 200)],
 'baseline_table1': [('flash_intensity', 5420), ('flash_frequency', 43.167)],
 'baseline_fig2': [('flash_intensity', 5420), ('flash_frequency', 43.167)],
 'long_wavelength_no_effect': [('wavelength_bound', 597), ('p_bound', 0.3)],
 'exposure_order_anova': [('frequency_dim_p_below', 0.0001), ('frequency_dim_chi2', 15.205), ('frequency_bright_p', 0.0012), ('frequency_bright_chi2', 14.668), ('intensity_p', 1.0), ('intensity_chi2', 0)],
 'intensity_frequency_correlation': [('dim', -0.9655009), ('bright', -0.8027756)],
}
nbad = 0
for k, fl in chk.items():
    s = J['statements'][k]
    for f, expect in fl:
        got = s[f]['value']
        qt = s['quote']
        txt = repr(abs(expect)) if isinstance(expect, float) else str(expect)
        txt = txt.rstrip('0').rstrip('.') if False else txt
        present = (str(expect).replace('-', '') in qt.replace('-', '')) or (expect == 1.0 and '1.0' in qt)
        if got != expect or not present: nbad += 1; log('  CHECK %s.%s json=%r expected=%r present_in_quote=%s' % (k, f, got, expect, present))
log('numeric fields checked in statements: %d ; problems: %d' % (sum(len(v) for v in chk.values()), nbad))
# sign of correlation in rendering? text layer shows hyphen-minus; check unit/type notes
log('correlation sign in text layer: %r' % re.search(r'correlation coefficient: ([^\]]*)\]', pages[8]).group(1))
# as_printed entries
for k, v in J['statements'].items():
    if 'as_printed' in v:
        a = v['as_printed']; q = v['quote']
        diffchars = [c for c in a if c not in q]
        log('as_printed %-28s glyphs added vs quote: %s ; glyph_from_rendered_page=%s' % (k, sorted(set(diffchars)), v.get('glyph_from_rendered_page')))
log('')
# Table1 caption/columns text
cap = J['table1']['caption']
log('table1 caption in page 6 text: %s' % (squash(cap).replace('A.ficta', 'A.ficta') in sp[6] or squash(cap.replace('A. ficta', 'A. fictaunder').split(' under')[0]) in sp[6]))
open(R + '/a04_statements.txt', 'w').write('\n'.join(out) + '\n')
