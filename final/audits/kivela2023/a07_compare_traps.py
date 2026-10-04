"""Field-by-field comparison: JSON traps vs own raw xlsx read (a04), + paper values vs my transcription of the rendered pages."""
import json,collections
r=json.load(open('audits/kivela2023/results/a04_xlsx_rows_own.json'))
raw=[x for x in r[1:] if x['types'].get('2')=='n' and x['cells']['4']!='NA']
d=json.load(open('data/derived/impacts/kivela2023.json'))
tr=d['traps']
res={'n_raw':len(raw),'n_json':len(tr),'mismatches':[]}
m={'date':'1','night':'2','site':'3','treatment':'4','lux':'5','photons_cm2_s':'6','males':'7','males_binary':'8'}
for x,t in zip(raw,tr):
    for k,c in m.items():
        rv=x['cells'][c]
        jv=t[k]
        ok = (jv==rv) if k in('date','treatment') else (float(rv)==float(jv))
        if not ok: res['mismatches'].append((x['row'],k,rv,jv))
    # type checks
res['order_preserved']=True
res['key_sets']=sorted({tuple(sorted(t)) for t in tr})
res['types']={k:sorted({type(t[k]).__name__ for t in tr}) for k in m}
res['json_per_treatment']=dict(collections.Counter(t['treatment'] for t in tr))
res['excluded_vs_raw']=d['traps_excluded']
# check source row number correspondence: no row number kept in JSON
res['has_source_row_field']=any('row' in t for t in tr)
# Paper transcription (by eye from rendered pages 4,5)
T1={'blue':(452,6.45e12,5.0),'white':(449,5.27e12,5.6),'yellow':(575,4.21e12,6.0),'red':(625,1.27e13,8.0)}
T2=[('blue vs control',-1.372,-6.601,'<',.001),('white vs control',-1.891,-7.735,'<',.001),('yellow vs control',-0.203,-1.157,'=',.247),('red vs control',-0.049,-0.287,'=',.774),('white vs blue',-0.519,-1.905,'=',.057),('yellow vs blue',1.168,5.461,'<',.001),('red vs blue',1.3225,6.231,'<',.001),('yellow vs white',1.687,6.768,'<',.001),('red vs white',1.842,7.435,'<',.001),('red vs yellow',0.1542,0.871,'=',.384)]
T4=[('blue vs control',-1.573,-3.769,'<',.001),('white vs control',-1.491,-3.594,'<',.001),('yellow vs control',0.1627,0.386,'=',.699),('red vs control',0.270,0.636,'=',.525),('white vs blue',0.082,0.202,'=',.840),('yellow vs blue',1.735,4.075,'<',.001),('red vs blue',1.843,4.294,'<',.001),('yellow vs white',1.653,3.906,'<',.001),('red vs white',1.761,4.128,'<',.001),('red vs yellow',0.107,0.249,'=',.803)]
T3=[('control',19,41,68.3,'A'),('blue',39,21,35.0,'B'),('white',38,22,36.7,'B'),('yellow',17,42,71.2,'A'),('red',16,44,73.3,'A')]
pm=[]
for row in d['paper']['table1']['rows']:
    if row['treatment'] in T1:
        e=T1[row['treatment']]
        if (row['peak_nm'],row['photons_cm2_s'],row['lux'])!=e: pm.append(('t1',row['treatment'],row))
for name,T in (('table2',T2),('table4',T4)):
    rows=d['paper'][name]['rows']
    if len(rows)!=10: pm.append((name,'len'))
    for a,b in zip(rows,T):
        if (a['comparison'],a['estimate'],a['z'],a['p_comparator'],a['p'])!=b: pm.append((name,a,b))
for a,b in zip(d['paper']['table3']['rows'],T3):
    if (a['treatment'],a['n_zero'],a['n_at_least_one'],a['success_percent'],a['letter'])!=b: pm.append(('t3',a,b))
res['paper_mismatches_vs_my_transcription']=pm
json.dump(res,open('audits/kivela2023/results/a07_compare.json','w'),indent=1,default=str)
print(json.dumps(res,indent=1,default=str))
