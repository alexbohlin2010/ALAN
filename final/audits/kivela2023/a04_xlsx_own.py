"""Independent read of Data_Kivela2022.xlsx (zipfile + xml, own code)."""
import zipfile, re, json, hashlib
import xml.etree.ElementTree as ET
P='data/raw/impacts/narrative of fireflies/Data_Kivela2022.xlsx'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
z=zipfile.ZipFile(P)
names=z.namelist()
wb=ET.fromstring(z.read('xl/workbook.xml'))
sheets=[(s.get('name'),s.get('{%s}id'%NS['r'])) for s in wb.find('m:sheets',NS)]
rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
rmap={r.get('Id'):r.get('Target') for r in rels}
ss=[]
if 'xl/sharedStrings.xml' in names:
    for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS):
        ss.append(''.join(t.text or '' for t in si.iter('{%s}t'%NS['m'])))
def col(ref):
    s=re.match(r'[A-Z]+',ref).group(); n=0
    for c in s:n=n*26+ord(c)-64
    return n
res={'files':names,'sheets':[s[0] for s in sheets]}
allrows={}
for nm,rid in sheets:
    t=rmap[rid]; t=t.lstrip('/'); t=t if t.startswith('xl/') else 'xl/'+t
    root=ET.fromstring(z.read(t))
    rows=[]
    for r in root.find('m:sheetData',NS):
        d={}
        for c in r:
            ty=c.get('t'); v=c.find('m:v',NS); isv=c.find('m:is',NS)
            if ty=='s' and v is not None: val=('s',ss[int(v.text)])
            elif ty=='inlineStr': val=('s',''.join(x.text or '' for x in isv.iter('{%s}t'%NS['m'])))
            elif v is not None: val=(ty or 'n',v.text)
            else: val=None
            d[col(c.get('r'))]=val
        rows.append((int(r.get('r')),d,c.get('s') if len(r) else None))
    allrows[nm]=rows
    res.setdefault('dims',{})[nm]=root.find('m:dimension',NS).get('ref') if root.find('m:dimension',NS) is not None else None
json.dump(res,open('audits/kivela2023/results/a04_xlsx_structure.json','w'),indent=1)
rows=allrows['Data']
print(res['dims'], len(rows))
hdr=rows[0][1]; print(hdr)
# write rows as raw strings (cell text exactly as stored)
out=[]
for rn,d,_ in rows:
    out.append({'row':rn,'cells':{str(k):(v[1] if v else None) for k,v in d.items()},'types':{str(k):(v[0] if v else None) for k,v in d.items()}})
json.dump(out,open('audits/kivela2023/results/a04_xlsx_rows_own.json','w'))
