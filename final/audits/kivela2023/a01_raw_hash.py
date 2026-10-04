import hashlib,csv,sys,json,os
base='data/raw/impacts/'
rows=list(csv.DictReader(open(base+'MANIFEST.csv')))
out={}
for r in rows:
    k=[c for c in r if c.startswith('sha256') or c=='sha256']
    f=r['file'] if 'file' in r else list(r.values())[0]
    if 'Kivela' in f:
        h=hashlib.sha256(open(base+f,'rb').read()).hexdigest()
        man=[v for v in r.values() if len(v)==64 and all(c in '0123456789abcdef' for c in v)]
        out[f]={'actual':h,'manifest':man,'match':h in man}
print(json.dumps(out,indent=1))
