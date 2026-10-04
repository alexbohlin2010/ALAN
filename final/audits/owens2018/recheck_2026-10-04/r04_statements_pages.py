"""r04: independent checks of F2 statements, F4 pages, F3 wording. Uses only my own per-page PDFKit text (results/pageN.txt)."""
import json, re
R='audits/owens2018/recheck_2026-10-04/results/'
pg={n:open(R+f'page{n}.txt',encoding='utf-8').read() for n in range(1,15)}
col=lambda s: re.sub(r'\s+',' ',s).strip()
cp={n:col(t) for n,t in pg.items()}
a=json.load(open('data/derived/impacts/owens2018_results.json'))
print('== F2 statements')
for k in ['abstract_short_mid','abstract_long','exposure_order_models','frequency_decline_cause','pauses']:
    s=a['statements'][k]; q=s['quote']
    occ={n:cp[n].count(q) for n in cp if cp[n].count(q)}
    print(k,'stated page',s['page'],'occurrences by page',occ,'-> PASS' if occ=={s['page']:1} else '-> FAIL', {f:v for f,v in s.items() if isinstance(v,dict)})
# numbers
print('533 in abstract_short_mid quote:', '533 nm' in a['statements']['abstract_short_mid']['quote'])
print('597 in abstract_long quote:', re.search(r'\( (597)\s*nm\)',a['statements']['abstract_long']['quote']) is not None, '; PDFKit raw p1 around:', repr(re.search(r'long wavelength ambient light.{0,60}',pg[1],re.S).group(0)))
print('"10 or more seconds" ->', a['statements']['pauses']['pause_at_least'])
# as_printed: only differs from quote by inserted >= glyph
q=a['statements']['abstract_long']['quote']; ap=a['statements']['abstract_long']['as_printed']
print('as_printed minus quote chars: ',sorted(set(ap)-set(q)), '; as_printed with glyph removed equals quote:', ap.replace('≥ ','')==q.replace('( ','(').replace('(', '(') or ap.replace('≥','').replace('( ','(')==q.replace('( ','('))
print('quote prefix in p1 text layer:', q in cp[1])
print('== F4 pages')
# my own: locate each "NNN nm: p ... x" in per-page text, page of match; for page-spanning, join p5+p6 with table removed
P_RE=re.compile(r'(\d{3})\s*nm:\s*p\s*(?:=\s*p\s*)?(=|<)\s*([\d.]+)')
for i,t in enumerate(a['text_p_values']):
    pat=re.compile(re.escape(t['printed']).replace(r'\ ',r'\s+'))
    hits=[n for n in (5,6) if pat.search(cp[n])]
    # whole 'NNN nm: p' start tokens
    print(i,t['exposure'],t['measure'],t['wavelength_nm'],repr(t['printed']),'json page',t['page'],'| full-match pages',hits)
print('--- p5 tail / p6 post-table head')
print(repr(cp[5][-200:]))
i=cp[6].index('t001'); print(repr(cp[6][i:i+120]))
# each wavelength 'NNN nm:' tokens by page, in the Results lists
for n in (5,6):
    print(n,[ (m.group(0)) for m in re.finditer(r'\d{3}\s*nm:\s*p[^;,)]{0,30}',cp[n]) if True][:40])
