"""Import all BusinessComponents and direct original relations from a pinned ISO archive."""
import argparse,hashlib,json,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist/data'
XMI='{http://www.omg.org/XMI}id';TYPE='{http://www.w3.org/2001/XMLSchema-instance}type'
def import_archive(path):
 digest=hashlib.sha256(path.read_bytes()).hexdigest();previous=json.loads((D/'iso-concept-index.json').read_text());assert digest==previous['source']['archive_sha256'],'Source changed; review snapshot before import'
 with zipfile.ZipFile(path) as z:
  member=z.namelist()[0];rows=[]
  for _,e in ET.iterparse(z.open(member),events=['end']):
   if e.tag=='topLevelDictionaryEntry':
    if e.get(TYPE)=='iso20022:BusinessComponent':rows.append((dict(e.attrib),[dict(x.attrib) for x in e]))
    e.clear()
 ids={a[XMI] for a,_ in rows};nodes=[];edges=[]
 for a,children in rows:
  uid=a[XMI];nodes.append({'id':uid,'name':a['name'],'definition_en':a.get('definition',''),'registration_status':a.get('registrationStatus'),'kind':'BusinessComponent','source_id':'ISO-20260904','source_locator':f'{member} / BusinessComponent xmi:id={uid}','attributes':[{'id':c[XMI],'name':c.get('name'),'definition_en':c.get('definition'),'min_occurs':c.get('minOccurs'),'max_occurs':c.get('maxOccurs'),'registration_status':c.get('registrationStatus')} for c in children if c.get(TYPE)=='iso20022:BusinessAttribute']})
  if a.get('superType') in ids:edges.append({'id':uid+'::superType','from':uid,'to':a['superType'],'kind':'generalization','name':'superType','source_id':'ISO-20260904'})
  for c in children:
   if c.get(TYPE)=='iso20022:BusinessAssociationEnd' and c.get('type') in ids:edges.append({'id':c[XMI],'from':uid,'to':c['type'],'kind':'association_end','name':c.get('name'),'definition_en':c.get('definition'),'min_occurs':c.get('minOccurs'),'max_occurs':c.get('maxOccurs'),'opposite_id':c.get('opposite'),'registration_status':c.get('registrationStatus'),'source_id':'ISO-20260904'})
 assert {n['id'] for n in nodes}=={n['id'] for n in previous['concepts']}
 assert {e['id'] for e in edges}=={e['id'] for e in previous['relations']}
 source=previous['source']|{'retrieved_at':'2026-10-02','archive_sha256':digest,'scope':'All BusinessComponents with original definitions and direct attributes; intra-component association ends and generalizations. Does not enumerate customer tasks or the complete Business Process Catalogue.','definition_source':'original archive XML; no model-generated definition'}
 out={'version':previous['version'],'source':source,'concepts':sorted(nodes,key=lambda n:n['name']),'relations':edges};(D/'iso-concept-index.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'concepts':len(nodes),'relations':len(edges),'attributes':sum(len(n['attributes']) for n in nodes),'sha256':digest}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);import_archive(p.parse_args().archive)
