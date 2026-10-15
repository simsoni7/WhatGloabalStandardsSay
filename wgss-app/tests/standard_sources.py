"""Check the full ISO object index against original bytes and pinned catalogues."""
import hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];cache=ROOT/'research/source-store/standards';D=ROOT/'dist/data';checks=[]
def check(name,condition):
 assert condition,name
 checks.append(name)
iso=json.loads((D/'iso-concept-index.json').read_text());exported={n['id']:n for n in iso['concepts']};archive=cache/'raw/iso.zip'
check('ISO archive fingerprint',hashlib.sha256(archive.read_bytes()).hexdigest()==iso['source']['archive_sha256'])
XMI='{http://www.omg.org/XMI}id';TYPE='{http://www.w3.org/2001/XMLSchema-instance}type';raw={}
with zipfile.ZipFile(archive) as z:
 for _,element in ET.iterparse(z.open(z.namelist()[0]),events=['end']):
  if element.tag=='topLevelDictionaryEntry':
   if element.get(TYPE)=='iso20022:BusinessComponent':raw[element.get(XMI)]=(dict(element.attrib),[dict(c.attrib) for c in element])
   element.clear()
check('full BusinessComponent roster, not legacy selected cases',raw.keys()==exported.keys())
raw_relations={}
for uid,(a,children) in raw.items():
 n=exported[uid];check('ISO original name, definition and registration '+uid,n['name']==a['name'] and n['definition_en']==a.get('definition','') and n['registration_status']==a.get('registrationStatus'))
 attrs={c[XMI]:c for c in children if c.get(TYPE)=='iso20022:BusinessAttribute'}
 check('ISO attribute roster '+uid,{x['id'] for x in n['attributes']}==attrs.keys())
 for x in n['attributes']:
  c=attrs[x['id']];check('ISO original attribute '+x['id'],x['name']==c.get('name') and x['definition_en']==c.get('definition') and x['min_occurs']==c.get('minOccurs') and x['max_occurs']==c.get('maxOccurs'))
 if a.get('superType') in raw:raw_relations[uid+'::superType']={'from':uid,'to':a['superType'],'kind':'generalization'}
 for c in children:
  if c.get(TYPE)=='iso20022:BusinessAssociationEnd' and c.get('type') in raw:raw_relations[c[XMI]]={'from':uid,'to':c['type'],'kind':'association_end','name':c.get('name'),'opposite_id':c.get('opposite'),'definition_en':c.get('definition')}
check('ISO direct relation roster',raw_relations.keys()=={r['id'] for r in iso['relations']})
for r in iso['relations']:check('ISO original relation '+r['id'],all(r.get(k)==v for k,v in raw_relations[r['id']].items()))
for name in ['bian','fibo','nist']:
 check('reviewed '+name+' catalogue fingerprint',hashlib.sha256((cache/(name+'-catalogue.json')).read_bytes()).hexdigest()==hashlib.sha256((ROOT/'research/data-v10/inputs'/(name+'-catalogue.json')).read_bytes()).hexdigest())
 env=os.environ|{'WGSS_STANDARD_WORKDIR':str(cache)}
subprocess.run([sys.executable,str(ROOT/'research/data-v10/reproduce/standards/validate_catalogues.py')],env=env,check=True)
report={'status':'passed','checks':len(checks),'items':checks,'scope':'Full original ISO roster, attributes and direct relations; separate upstream catalogue validation in private cache.'}
(ROOT/'research/ui-v10/standard-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','checks':len(checks)}))
