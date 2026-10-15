"""Verify discovery counts, provenance and that no inventory can become accepted."""
import hashlib,json,sqlite3,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research/definition-v11/collection'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(ROOT/'dist/data/definition-audit.json'); checks=[]
def check(name,value):
 assert value,name
 checks.append(name)
check('global denominator not invented',r['global_mece_total'] is None and r['collection']['summary']['global_mece_total'] is None)
check('new benchmarks not inferred from fetch success',r['collection']['summary']['accepted_new_benchmarks']==0)
check('database corresponds to report',r['database_sha256']==sha(ROOT/'data/collection.sqlite'))
for filename,digest in r['input_hashes'].items():check('input '+filename,sha(P/filename)==digest)
con=sqlite3.connect(ROOT/'data/collection.sqlite');con.execute('PRAGMA foreign_keys=ON')
check('no orphan references',not con.execute('PRAGMA foreign_key_check').fetchall())
s=r['collection']['summary'];check('source rows count',con.execute('select count(*) from source_snapshot').fetchone()[0]==s['source_count'])
check('inventory rows count',con.execute('select count(*) from discovered_candidate').fetchone()[0]==s['candidate_inventory_rows'])
check('distinct URL count',con.execute('select count(distinct url) from discovered_candidate').fetchone()[0]==s['distinct_candidate_urls'])
check('procedure candidates count',con.execute('select count(*) from procedure_candidate').fetchone()[0]==s['procedure_candidate_count'])
check('FAQ body candidates count',con.execute('select count(*) from faq_document_candidate').fetchone()[0]==s['faq_document_candidates'])
check('FAQ original response count',con.execute('select count(*) from faq_source').fetchone()[0]==s['faq_api_sources'])
check('rendered source count',con.execute('select count(*) from rendered_source').fetchone()[0]==s['rendered_index_snapshots'])
check('rendered discovery count',con.execute('select count(*) from rendered_candidate').fetchone()[0]==s['rendered_candidate_rows'])
raw=ROOT/'research/source-store/definition-v11/collection'
for name in ['source-manifest.json','rendered-source-manifest.json','toss-faq-api-source-manifest.json']:
 for source in read(P/name):
  check('preserved original hash '+source['id'],sha(raw/source['raw_path'])==source['raw_sha256'])
for row in read(P/'toss-faq-document-candidates.json'):
 check('FAQ stable native identity '+row['id'],con.execute('select count(*) from faq_document_candidate where id=?',(row['id'],)).fetchone()[0]==1)
 check('FAQ text hash '+row['id'],sha(raw/row['text_path'])==row['normalized_title_and_body_sha256'])
 for obs in row['observations']:
  obj=read(raw/obs['source_raw_path'])
  for part in obs['json_pointer'].lstrip('/').split('/'):
   obj=obj[int(part)] if isinstance(obj,list) else obj[part.replace('~1','/').replace('~0','~')]
  check('FAQ exact JSON title '+row['id'],obj['title']==row['title'])
check('unresolved category cardinality remains visible',len(r['collection']['category_gaps'])==2 and any('완전성은 미승인' in x for x in r['discrepancies']))
for p in r['collection']['providers']:
 check('provider source count '+p['id'],con.execute('select count(*) from source_snapshot where provider_id=?',(p['id'],)).fetchone()[0]==p['source_count'])
 check('provider URL count '+p['id'],con.execute('select count(distinct url) from discovered_candidate where provider_id=?',(p['id'],)).fetchone()[0]==p['discovered_urls'])
check('provider totals reconcile',sum(p['source_count'] for p in r['collection']['providers'])==s['source_count'])
con.close()
with tempfile.TemporaryDirectory() as d:
 tmp=Path(d)/'test.sqlite';shutil.copy(ROOT/'data/collection.sqlite',tmp);c=sqlite3.connect(tmp);c.execute('PRAGMA foreign_keys=ON')
 for name,sql in [('inventory cannot claim approved',"update discovered_candidate set status='accepted'"),('fetch cannot claim admitted',"update source_snapshot set admission_status='source_checked'"),('procedure cannot claim approved',"update procedure_candidate set status='accepted'"),('FAQ cannot claim approved',"update faq_document_candidate set status='accepted'"),('FAQ orphan source rejected',"update faq_observation set source_id='absent'"),('orphan discovery rejected',"update discovered_candidate set source_id='absent'")]:
  try:c.execute(sql)
  except sqlite3.IntegrityError:check(name,True);c.rollback()
  else:raise AssertionError(name)
 c.close()
out={'status':'passed','checks':len(checks),'items':checks,'limits':'Structural checks do not establish semantic MECE or current app UI verification.'}
(ROOT/'research/definition-v11/validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','checks':len(checks)}))
