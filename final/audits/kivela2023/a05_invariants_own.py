"""Independent invariants on the raw xlsx rows (from a04 output)."""
import json,collections,itertools
r=json.load(open('audits/kivela2023/results/a04_xlsx_rows_own.json'))
data=[x for x in r[1:] if x['types'].get('2')=='n']
out={}
out['n_data_rows_all']=len(data)
na=[x['row'] for x in data if x['cells']['4']=='NA']
out['NA_rows']=na
good=[x for x in data if x['cells']['4']!='NA']
out['n_good']=len(good)
def f(x,k): return x['cells'][str(k)]
by=collections.defaultdict(list)
for x in good: by[f(x,4)].append(x)
tab={}
for t,xs in by.items():
    m=[float(f(x,7)) for x in xs]
    tab[t]={'n':len(xs),'zero':sum(1 for v in m if v==0),'ge1':sum(1 for v in m if v>=1),'sum_males':sum(m),
            'bin1':sum(1 for x in xs if f(x,8)=='1'),'lux':sorted({f(x,5) for x in xs}),'photons':sorted({f(x,6) for x in xs})}
    med=sorted(m); n=len(m); tab[t]['median']=(med[n//2] if n%2 else (med[n//2-1]+med[n//2])/2)
    tab[t]['pct']=round(100*tab[t]['ge1']/n,1)
out['by_treatment']=tab
out['total_males_good']=sum(float(f(x,7)) for x in good)
out['bin_consistent']=all((float(f(x,7))>0)==(f(x,8)=='1') for x in good)
out['males_nonint']=[f(x,7) for x in good if float(f(x,7))!=int(float(f(x,7)))]
keys=collections.Counter((f(x,2),f(x,3),f(x,4)) for x in data)
out['dup_night_site_treatment']=[k for k,v in keys.items() if v>1]
ns=collections.Counter((f(x,2),f(x,3)) for x in data)
out['dup_night_site']=[k for k,v in ns.items() if v>1]
out['nights']=sorted({int(f(x,2)) for x in data})
out['sites']=sorted({int(f(x,3)) for x in data})
pernight=collections.Counter(f(x,2) for x in data)
out['rows_per_night']=dict(sorted(pernight.items(),key=lambda k:int(k[0])))
pn=collections.defaultdict(collections.Counter)
for x in good: pn[f(x,2)][f(x,4)]+=1
out['night_treatment_counts_not_3']={n:dict(c) for n,c in pn.items() if set(c.values())!={3} or len(c)!=5}
site=collections.defaultdict(collections.Counter)
for x in good: site[f(x,3)][f(x,4)]+=1
out['site_treatment_counts_not_4']={s:dict(c) for s,c in site.items() if set(c.values())!={4} or len(c)!=5}
out['dates']={n:sorted({f(x,1) for x in data if f(x,2)==n}) for n in out['rows_per_night']}
out['dates_multi']={n:d for n,d in out['dates'].items() if len(d)!=1}
out['raw_row_numbers_range']=[data[0]['row'],data[-1]['row']]
out['max_males_by_treatment']={t:max(float(f(x,7)) for x in xs) for t,xs in by.items()}
# missing-row accounting: night-10 site 3 NA row; which treatment cell missing in night 10
out['night10_counts']=dict(collections.Counter(f(x,4) for x in data if f(x,2)=='10'))
out['row139']=[x for x in data if x['row']==139][0]['cells']
# photons rounding vs paper
paper={'blue':6.45e12,'white':5.27e12,'yellow':4.21e12,'red':1.27e13}
out['photon_vs_paper']={t:{'sheet':tab[t]['photons'],'paper':v,'rel_diff':[abs(float(p)-v)/v for p in tab[t]['photons']]} for t,v in paper.items()}
json.dump(out,open('audits/kivela2023/results/a05_invariants_own.json','w'),indent=1)
print(json.dumps(out,indent=1))
