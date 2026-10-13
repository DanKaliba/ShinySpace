import zipfile,re,sys,json,os
d=sys.argv[1]
f=[x for x in os.listdir(d) if x.startswith('Okrsky')][0]
xml=zipfile.ZipFile(os.path.join(d,f)).read('word/document.xml').decode('utf8')
paras=[re.sub(r'<[^>]+>','',p) for p in re.findall(r'<w:p[ >].*?</w:p>',xml)]
t='\n'.join(paras)
t=re.sub(r'ÚMČ Praha 5\n31\.5\.2022\nStrana \d+ /\n\d+\nVOLEBNÍ OKRSKY JEDNOTLIVÝCH MĚSTSKÝCH ČÁSTÍ\n','',t)
parts=re.split(r'V okrsku č\.: (\d+) je místnost ',t)
out={}
for i in range(1,len(parts),2):
    body=parts[i+1].strip().split('\n')
    out[int(parts[i])]={'mistnost':body[0],'adresa':body[1] if len(body)>1 else '','ulice':' '.join(body[2:])}
json.dump(out,open(sys.argv[2],'w',encoding='utf8'),ensure_ascii=False,indent=0)
for k in sorted(out):
    o=out[k]; streets=sorted(set(re.findall(r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽa-záčďéěíňóřšťúůýž\. 0-9]+?) \d+/',o['ulice'])))
    print(k,'|',o['mistnost'][:45],'|',o['adresa'][:45],'|',', '.join(s.strip() for s in streets)[:150])
