"""r02: path-level diff of before/after owens2018_results.json."""
import json,sys
b=json.load(open('/private/tmp/claude-501/-Users-lindaxiangyideng-Documents-GitHub-ALAN--claude-worktrees-interesting-gagarin-73979e/a470d70f-1add-4247-9768-2c0710676294/scratchpad/owens2018_results.before_4i.json')); a=json.load(open('data/derived/impacts/owens2018_results.json'))
def walk(x,p=''):
    if isinstance(x,dict):
        for k,v in x.items(): yield from walk(v,p+'/'+k)
    elif isinstance(x,list):
        for i,v in enumerate(x): yield from walk(v,p+'[%d]'%i)
    else: yield p,x
B=dict(walk(b)); A=dict(walk(a))
for p in sorted(set(A)|set(B)):
    if p not in B: print('ADDED  ',p,'=',repr(A[p]))
    elif p not in A: print('REMOVED',p,'=',repr(B[p]))
    elif A[p]!=B[p] or type(A[p])!=type(B[p]): print('CHANGED',p,repr(B[p]),'->',repr(A[p]))
print('--- invariants')
print('table1 identical:',a['table1']==b['table1'])
ka=lambda t:[{k:v for k,v in x.items() if k!='page'} for x in t]
print('text_p_values identical ignoring page:',ka(a['text_p_values'])==ka(b['text_p_values']))
print('text_p_values value/comparator/printed identical:',all((x['p'],x['comparator'],x['printed'])==(y['p'],y['comparator'],y['printed']) for x,y in zip(a['text_p_values'],b['text_p_values'])), len(a['text_p_values']))
print('text_vs_table1 identical:',a['text_vs_table1']==b['text_vs_table1'])
print('source/scope/labels/label_notes identical:',all(a[k]==b[k] for k in ('source','scope','labels','label_notes')))
old=b['statements']; new=a['statements']
print('old statements unchanged:',all(new[k]==v for k,v in old.items()), 'old keys order preserved prefix:', [k for k in new if k in old]==list(old))
print('new statement keys:',[k for k in new if k not in old])
print('units changed keys:',[k for k in a['units'] if a['units'][k]!=b['units'].get(k)])
print('top-level key order same:',list(a)==list(b))
