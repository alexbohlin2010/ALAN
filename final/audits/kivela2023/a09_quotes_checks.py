import json,re
d=json.load(open('data/derived/impacts/kivela2023.json'))
txt=open('audits/kivela2023/results/a02_pdftext_own.txt').read()
pages={int(m.group(1)):m.group(2) for m in re.finditer(r'=====PAGE (\d+)=====\n(.*?)(?=\n=====PAGE|\Z)',txt,re.S)}
col=lambda s:re.sub(r'\s+',' ',s).strip()
res={'quotes':{}, 'checks':[]}
for k,v in d['paper']['statements'].items():
    p=col(pages[v['page']]); res['quotes'][k]={'count_on_stated_page':p.count(v['quote']),'on_other_pages':[q for q in pages if q!=v['page'] and v['quote'] in col(pages[q])]}
for c in d['checks']: res['checks'].append(c['check'])
# which treatments/fields have checks
res['n_checks']=len(d['checks'])
res['check_agree_all']=all(c['agree'] for c in d['checks'])
# photon check details
res['photon_checks']=[c for c in d['checks'] if 'photons' in c['check']]
# does any check cover control lux/photons?
res['control_lux_photon_check']=[c['check'] for c in d['checks'] if c['check'].startswith('control') and ('lux' in c['check'] or 'photons' in c['check'])]
json.dump(res,open('audits/kivela2023/results/a09_quotes_checks.json','w'),indent=1,ensure_ascii=False)
print(json.dumps(res,indent=1,ensure_ascii=False))
