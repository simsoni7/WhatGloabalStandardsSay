"""Audit every active proof and exercise admission constraints against bad data."""
import hashlib,json,sqlite3,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist/data';OUT=ROOT/'research/ui-v10';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=read(D/'library.json');s=read(D/'standards.json');checks=[]
def check(name,condition):
 assert condition,name
 checks.append(name)
records={r['id']:r for r in b['records']};nodes={n['id']:n for n in s['nodes']};sources={x['id']:x for x in b['sources']}
features={f['id']:f for f in b['features']};contexts={f['id']:f for f in b['policy_contexts']};entities=features|contexts
check('primary database fingerprint',digest(ROOT/'data/wgss.sqlite')==b['database_sha256'])
for path,h in b['build_inputs'].items():check('reviewed input fingerprint '+path,digest(ROOT/path)==h)
check('archive and active corpus disjoint',not set(records)&{r['id'] for r in b['archived_records']})
check('active graph has no legacy scenario keys',all(k not in json.dumps([b['features'],b['tasks'],b['mappings']]) for k in ['legacy_case_id','case_ids','case_id']))
def proof(p):
 source=sources[p['source_id']];check('source available '+p['source_id'],source['source_state']=='retrieved' and source['http_status']==200)
 check('source revision '+p['source_id'],p['source_sha256']==source['sha256'])
 path=ROOT/'research/data-v10/source-texts'/(p['source_id']+'.normalized.txt')
 text=path.read_text().strip() if path.exists() else ' '.join(path.with_name(p['source_id']+'.txt').read_text().split())
 check('normalized revision '+p['source_id'],hashlib.sha256(text.encode()).hexdigest()==p['normalized_text_sha256'])
 loc=p['locator'];check('exact quote location '+p['source_id'],text[loc['start']:loc['end']]==p['excerpt'])
 check('short source quote '+p['source_id'],len(p['excerpt'].split())<=25)
for r in records.values():
 check('reference entity '+r['id'],r['reference_entity_id'] in entities)
 check('no fabricated UI or human review '+r['id'],r['ui_version'] is None and r['independent_human_review'] is False)
 if r['type']=='document':
  check('document channel remains unknown '+r['id'],r['channel']=='unknown');proof(r['function_support'])
  if r['expression']:
   proof(r['expression_proof']);check('expression separately proved '+r['id'],r['expression']==r['expression_proof']['excerpt'])
  for c in r['claims']:
   if c['status']=='source_checked':
    check('editorial interpretation separately labelled '+r['id']+c['field'],c['state']=='known' and c['semantic_assessment']=='editor_assessed');proof(c['proof'])
   else:check('unproven claim withheld '+r['id']+c['field'],c['value'] is None and c['state']=='unknown' and c['proof'] is None)
 else:
  check('preserved source image '+r['id'],digest(ROOT/'dist'/r['image_path'])==r['image_sha256'])
  check('screen evidence scope '+r['id'],r['evidence_kind'] in ['official_guide_screen','official_product_image','live_public_web'])
for f in features.values():check('policy publishers excluded from provider features '+f['id'],f['entity_kind']=='provider_function' and f['product_id']!='PAYUK' and bool(f['function_proofs']))
for t in b['tasks']:
 check('heading membership separated '+t['id'],set(t['feature_ids'])<=features.keys() and set(t['policy_context_ids'])<=contexts.keys())
for e in b['examples']:
 check('example uses admitted source records '+e['id'],set(e['record_ids'])<=records.keys())
 check('example consistently scoped '+e['id'],all(records[r]['reference_entity_id']==e['reference_entity_id'] for r in e['record_ids']))
for m in b['mappings']:
 n=nodes[m['concept_id']];check('qualified original definition '+m['id'],m['equivalence_asserted'] is False and m['status']=='editor_assessed' and m['concept_definition_evidence']['definition']==n['definition'] and bool(m['rationale']) and bool(m['scope_caveat']))
 check('mapping target distinction '+m['id'],(m['feature_id'] in features and m['policy_context_id'] is None) if m['target_entity_kind']=='provider_function' else (m['feature_id'] is None and m['policy_context_id'] in contexts))
check('FIBO imported modules are released',all(n['maturity']=='Release' for n in s['nodes'] if n['standard']=='FIBO'))
check('glossary does not invent native NIST IDs',all(n['native_id'] is None for n in s['nodes'] if n['kind']=='InformativeGlossaryTerm' and n['standard']=='NIST'))
check('distinct relation endpoints resolve',all(r['from_id'] in nodes and r['to_id'] in nodes for r in s['relations']))
check('new identity evidence avoids legacy case basis','O42' in records and 'O43' in records and records['O42']['task_id']!=records['O43']['task_id'])
check('recommendation not fabricated as effective time',all(c['state']=='unknown' for rid in ['O39','O40'] for c in records[rid]['claims'] if c['field']=='effective_at'))
check('out of scope and unreachable material excluded',all(r not in records for r in ['O04','O05','O10','O11','O12','O36']))
check('targets awaiting evidence remain empty',next(p for p in b['products'] if p['id']=='TOSS')['record_count']==0)
db=sqlite3.connect('file:'+str(ROOT/'data/wgss.sqlite')+'?mode=ro',uri=True)
check('database structural integrity',db.execute('pragma integrity_check').fetchall()==[('ok',)] and not db.execute('pragma foreign_key_check').fetchall())
for field,sql in [('provider_features',"select count(*) from reference_entity where entity_kind='provider_function'"),('scheme_policy_contexts',"select count(*) from reference_entity where entity_kind='scheme_policy_context'"),('records','select count(*) from record'),('application_mappings','select count(*) from mapping'),('claims_source_checked',"select count(*) from claim where status='source_checked'")]:check('SQL-derived '+field,db.execute(sql).fetchone()[0]==b['counts'][field])
db.close()
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)/'adversarial.sqlite';shutil.copyfile(ROOT/'data/wgss.sqlite',p);con=sqlite3.connect(p);con.execute('pragma foreign_keys=on')
 def rejects(name,sql,args=()):
  try:con.execute(sql,args)
  except sqlite3.IntegrityError:check(name,True);con.rollback()
  else:raise AssertionError(name)
 mid=b['mappings'][0]['id'];rid=b['records'][0]['id']
 rejects('reject cross-standard equivalence',"update mapping set equivalence=1 where id=?",(mid,))
 rejects('reject dangling concept mapping',"update mapping set concept_id='fabricated' where id=?",(mid,))
 rejects('reject dangling reference entity',"update record set reference_entity_id='fabricated' where id=?",(rid,))
 cid=con.execute("select id from claim where status='source_checked' limit 1").fetchone()[0]
 rejects('reject known claim missing proof',"update claim set data=json_remove(data,'$.proof') where id=?",(cid,))
 rejects('reject known claim with null value',"update claim set data=json_set(data,'$.value',NULL) where id=?",(cid,))
 rejects('reject unsupported claim carrying accepted value',"update claim set status='unsupported' where id=?",(cid,))
 con.close()
report={'status':'passed','checks':len(checks),'items':checks,'counts':b['counts'],'limitations':'Structural and source-locator checks; semantics remain editorial assessments, independent human reviews zero.'}
(OUT/'data-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','checks':len(checks),'counts':b['counts']},ensure_ascii=False))
