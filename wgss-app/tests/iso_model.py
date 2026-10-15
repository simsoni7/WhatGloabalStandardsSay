"""Check published semantic data against the pinned upstream XMI, plus WGSS integrity."""
import sys,json,hashlib,zipfile,xml.etree.ElementTree as ET
from itertools import combinations
from pathlib import Path
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1];D=R/'dist/data';read=lambda n:json.loads((D/(n+'.json')).read_text())
m=read('business-model');cases=read('cases');links=read('case-concept-links');checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name)
concepts={c['id']:c for c in m['concepts']};names={c['name']:c for c in m['concepts']};edges={e['id']:e for e in m['relations']}
check('Unique concept and relation IDs',len(concepts)==len(m['concepts']) and len(edges)==len(m['relations']))
check('No MessageComponent imported as BusinessComponent',all(c['kind']=='BusinessComponent' for c in concepts.values()))
check('Selected concepts registered in this snapshot',all(c['registration_status']=='Registered' for c in concepts.values()))
check('All edge endpoints resolve',all(e['from'] in concepts and e['to'] in concepts for e in edges.values()))
check('Association end opposite is preserved and reciprocal',all(e['opposite_id'] in edges and edges[e['opposite_id']]['opposite_id']==e['id'] and edges[e['opposite_id']]['to']==e['from'] and edges[e['opposite_id']]['from']==e['to'] for e in edges.values() if e['kind']=='association_end'))
check('Exactly one mapping row per case',len(links)==len(cases) and {l['case_id'] for l in links}=={c['id'] for c in cases})
check('Mappings use real concept names and source',all(l['concept_names'] and all(n in names for n in l['concept_names']) and l['source_id']==m['source']['id'] for l in links))
check('UI mappings never assert ISO equivalence or approval',all(l['mapping_kind'] in ['contextual','wgss_application'] and l['review_status']=='proposed' and not l['independent_review'] for l in links))
check('New definitions have no fabricated provider observations',not any(o['case_id'] and o['case_id'][0] not in 'CTR' for o in read('observations')))
def compatible(a,b):
 return all(set(a[k] if isinstance(a[k],list) else [a[k]]) & set(b[k] if isinstance(b[k],list) else [b[k]]) for k in a.keys() & b.keys())
overlaps=[(a['id'],b['id']) for a,b in combinations(cases,2) if compatible(a['selector'],b['selector'])]
check('No pair of case selectors admits the same complete facts',not overlaps)
check('All required fields have display labels',all(k in read('field-labels') for c in cases for k in c['critical_fields']))
check('Scope counts reconcile',read('manifest')['case_count']==len(cases) and read('manifest')['business_concept_count']==len(concepts) and read('manifest')['business_relation_count']==len(edges))
def edge(a,name,b):return any(e['from']==names[a]['id'] and e['name']==name and e['to']==names[b]['id'] for e in edges.values())
check('Cash account / entry link exists independently of UI wording',edge('CashAccount','CashEntry','CashEntry'))
check('Mandate and collection remain different components',edge('DirectDebit','DirectDebitMandate','DirectDebitMandate'))
check('Recurring instruction relates to credit transfer',edge('CashStandingOrder','CreditTransfer','CreditTransfer'))
check('Return payment relates to original payment',edge('Payment','ReturnPayment','Payment') and edge('Payment','OriginalPayment','Payment'))
check('Interest relates to calculation and booked entries',edge('Interest','InterestCalculation','InterestCalculation') and edge('Interest','CashEntry','CashEntry'))
# A second parser checks the exported subset against actual upstream identifiers and fields.
archive=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/wgss-iso-repository.zip')
check('Upstream archive hash matches recorded source',hashlib.sha256(archive.read_bytes()).hexdigest()==m['source']['archive_sha256'])
xid='{http://www.omg.org/XMI}id';xtype='{http://www.w3.org/2001/XMLSchema-instance}type';raw={};count=0
with zipfile.ZipFile(archive) as z:
 check('Upstream archive member exact',m['source']['archive_member'] in z.namelist())
 for _,e in ET.iterparse(z.open(m['source']['archive_member']),events=['end']):
  if e.tag=='topLevelDictionaryEntry':
   if e.get(xtype)=='iso20022:BusinessComponent':
    count+=1
    if e.get(xid) in concepts:raw[e.get(xid)]=(dict(e.attrib),{x.get(xid):dict(x.attrib) for x in e})
   e.clear()
check('Total BusinessComponent coverage accurate',count==m['source']['total_business_components'])
check('Names and original definitions exact',all(raw[c['id']][0]['name']==c['name'] and raw[c['id']][0]['definition']==c['definition_en'] for c in concepts.values()))
check('Association names, targets, opposites, multiplicity preserved',all((lambda a:a['name']==e['name'] and a['type']==e['to'] and a.get('opposite')==e['opposite_id'] and a.get('minOccurs')==e['min_occurs'] and a.get('maxOccurs')==e['max_occurs'])(raw[e['from']][1][e['id']]) for e in edges.values() if e['kind']=='association_end'))
check('Inheritance taken from upstream, not inferred',all(raw[e['from']][0]['superType']==e['to'] for e in edges.values() if e['kind']=='generalization'))
check('Direct business attributes have upstream identities',all(raw[c['id']][1][a['id']][xtype]=='iso20022:BusinessAttribute' and raw[c['id']][1][a['id']]['name']==a['name'] and raw[c['id']][1][a['id']].get('definition','')==a['definition_en'] for c in concepts.values() for a in c['attributes']))
# Detect inheritance cycles (association cycles are valid).
def ancestors(uid,trail=()):
 assert uid not in trail,'Cyclic generalization'
 for e in edges.values():
  if e['from']==uid and e['kind']=='generalization':ancestors(e['to'],trail+(uid,))
for uid in concepts:ancestors(uid)
checks.append('No cyclic generalization')
report=dict(version='0.2.0',status='passed',checks=len(checks),items=checks,source_archive_sha256=m['source']['archive_sha256'],independent_review=False)
(D/'iso-validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
