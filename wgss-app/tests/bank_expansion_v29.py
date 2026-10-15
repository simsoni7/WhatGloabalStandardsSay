# Historical v29 release oracle; current delta is independently checked by bank_gaps_v30.py.
"""Current scope revision, financial result boundaries and source-image provenance."""
import csv,hashlib,json,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v29.json');base=read(R/'data/bank-ui-baseline-v28.json');scope=read(R/'data/bank-ui-scope-v1_1-decisions.json');root=read(R/'data/bank-ui-collection-v29-decisions.json');private=read(R/'data/bank-ui-benchmark-dispositions.json');works={w['id']:w for w in d['works']};allrows={b['id']:b for b in private['examples'] if b['id'] in {x['id'] for x in d['benchmarks']}};checks=[]
def check(n,ok):assert ok,n;checks.append(n)
new={'WGSS-UI-A0E391E8134E','WGSS-UI-05004E3900EF'}
check('versioned scope adds only two direct results and preserves old214 identities',d['version']=='bank-customer-ui-v1.1' and len(works)==216 and set(works)-{w['id'] for w in base['works']}==new and len({tuple(w['semantic_key']) for w in works.values()})==216)
check('216 work count excludes states, country clones and standard object totals',d['counts']=={'total':216,'core':119,'extension':51,'support':46,'by_domain':dict(collections.Counter(w['domain_id'] for w in works.values()))} and not d['global_financial_industry_mece_approved'] and not d['independent_human_review'])
for c in scope['metadata_corrections']:
 w=works[c['work_id']];assert all(w[k]==v for k,v in c['after'].items())
check('three actual metadata conflicts resolved under stable IDs and meaning aliases',len(scope['metadata_corrections'])==3 and works['WGSS-UI-1C6D9879F35A']['outcome_key']=='deposit_termination_and_return_right_confirmed' and works['WGSS-UI-C35D818932FB']['outcome_key']=='submit_estate_account_distribution_request')
check('bank-imposed review request differs from user self-imposed and channel limits',works['WGSS-UI-A0E391E8134E']['object_key']=='bank_imposed_account_usage_restriction_review' and works['WGSS-UI-05004E3900EF']['object_key']=='payment_channel_usage_limit_profile' and len({works[x]['object_key'] for x in new|{'WGSS-UI-DFEB572279B8'}})==3)
check('source-backed scope additions have own positive benchmark proof',all(any(wid in b['ui_work_ids'] for b in d['benchmarks']) for wid in new) and not d['collection_plan']['definition_review_gaps'])
check('historical188 admission IDs unique, prior166 rows remain unchanged',len(allrows)==188 and len(d['benchmarks'])==188 and all(next(b for b in d['benchmarks'] if b['id']==x['id'])==x for x in base['benchmarks']))
check('different progress units retain 95 works,12 providers,46 guides,0 installed app observations',d['benchmark_counts']=={'works_with_function_documents':95,'examples':188,'providers':12,'countries':3,'official_guide_screens':46,'public_web_captures':2,'works_with_screen_references':19,'observed_app_captures':0,'verified_app_ui_versions':0,'unlinked_works':121})
check('whole denominator includes all648 cells, primary markets stay KR GB HK',len(d['collection_matrix'])==648 and len({(c['country'],c['ui_work_id']) for c in d['collection_matrix']})==648 and d['collection_counts']['linked_country_work_cells']==146 and d['collection_counts']['empty_country_work_cells']==502 and d['collection_counts']['screen_country_work_cells']==27)
check('pilot compatibility retained without presenting it as whole scope',d['priority_collection']=={'works':32,'cells':96,'reviewed_cells':96,'works_with_examples':32,'linked_cells':78,'screen_cells':18,'flow_and_condition_cells':40} and root['priority_audit_scope_version']=='bank-customer-ui-v1' and root['priority_audit_compatible_work_ids_preserved'])
sources={p['prefix']+':'+s['id']:s for p in root['source_batches'] for s in read(R/p['manifest'])};assets={a['id']:a for a in read(R/'research/source-store/bank-screen-assets-v29-20261012/assets.json')};newids={x['example_id'] for x in root['admitted_examples']};rows=[allrows[x] for x in sorted(newids)];hashes=set()
for b in rows:
 s=sources[b['source_id']];assert b['country']==s['country'];assert b['provider_id']==root['provider_id_aliases'].get(s['provider_id'],s['provider_id']);assert b['raw_sha256']==s['raw_sha256'];t=s['text'];assert b['text_sha256']==hashlib.sha256(t.encode()).hexdigest()
 if s.get('snapshot_path'):assert hashlib.sha256((R/s['snapshot_path']/s.get('raw_filename','source.html')).read_bytes()).hexdigest()==b['raw_sha256']
 assert not b['observed_app_screen'] and b['verified_ui_version'] is None and not b['current_ui_verified']
 for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']]:
  if q['kind']=='normalized_text_character_range':assert t[q['start']:q['end']]==q['excerpt']
  else:assert q['kind']=='official_image_region' and q['page']==5 and q['image_sha256']==b['screen_evidence']['image_sha256'] and q['review']=='root_visual_checked'
 for e in ([b['screen_evidence']]+b.get('additional_screen_evidence',[])) if b.get('screen_evidence') else []:
  a=assets[e['source_asset_id']];assert a['source_id']==b['source_id'];assert hashlib.sha256((R/'dist'/e['image_path']).read_bytes()).hexdigest()==a['image_sha256']==e['image_sha256'];assert e['image_derivation'] in ['original_official_guide_asset','original_official_pdf_page_render'];hashes.add(e['image_sha256'])
  if e.get('display_region'):
   rg=e['display_region'];assert [rg['original_width'],rg['original_height']]==[a['width'],a['height']];x0,y0,x1,y1=rg['bbox_xyxy'];assert 0<=x0<x1<=a['width'] and 0<=y0<y1<=a['height']
  if e.get('pdf_page'):assert e['raw_pdf_sha256']==b['raw_sha256'] and e['pdf_page']==a['page']
 assert any(c['id']==b['id'] and (c['source_id'],c['work_id'],c['native_expression'])==(b['source_id'],b['ui_work_ids'][0],b['expression']) for c in root['final_source_review'])
 assert any(r['example_id']==b['id'] and not r['automatic_adoption'] for r in root['root_final_model_dispositions'])
check('all22 root admissions have original exact sources, bound model review and explicit root disposition',len(rows)==22 and len(root['final_source_review'])==22 and len(root['root_final_model_dispositions'])==22 and not root['independent_human_review'])
check('61 raw assets do not become61 UI screens;18 selected unique images admitted',len(assets)==61 and len(hashes)==18 and root['guide_images_admitted']==18)
check('brokerage bank payout is payment instruction, never physical cash',allrows['BANK-BENCH-198']['ui_work_ids']==['WGSS-UI-E7352823594F'] and '지폐' in allrows['BANK-BENCH-198']['meaning'] and allrows['BANK-BENCH-198']['screen_evidence']['platform_kind']=='web')
check('forgotten login recovery not voluntary password change',allrows['BANK-BENCH-199']['ui_work_ids']==['WGSS-UI-0A65B1936347'] and '로그인 비밀번호를 잊은' in allrows['BANK-BENCH-199']['meaning'])
check('insurer, bank publisher and two app platforms are distinguished',allrows['BANK-BENCH-203']['provider_id']=='hsbc-life-hk' and allrows['BANK-BENCH-203']['source_publisher_id']=='hsbc-hk' and allrows['BANK-BENCH-203']['platform_name']=='HSBC HK App 보험 서비스' and all(allrows[x]['platform_name']=='HealthyLife App' and allrows[x]['function_proof']['kind']=='official_image_region' for x in ['BANK-BENCH-208','BANK-BENCH-209']))
check('stale2013 UI and blocked sources never counted as current benchmark evidence',not any(b['source_id'] in ['S29:kr-samsungpop-pdf','S29:kr-samsungfire-claims','S29:hk-manulife-eclaims','S29:hk-manulife-claims-guide'] for b in d['benchmarks']) and len(root['source_failures'])==3 and len(root['historical_sources_excluded'])==1)
check('17 research providers include4 newly admitted, Malaysian candidate separate',len(d['collection_plan']['provider_targets'])==17 and {t['country'] for t in d['collection_plan']['provider_targets']}=={'KR','GB','HK'} and d['collection_plan']['secondary_market_targets'][0]['country']=='MY' and not any(b['country']=='MY' for b in d['benchmarks']))
check('source-specific false semantic routes explicitly rejected, no silent forced matches',len(root['rejected_source_routes'])==11 and not any(b['source_id']=='S29:kr-shinhan-openbank' and 'WGSS-UI-0591BE47D0EE' in b['ui_work_ids'] for b in d['benchmarks']) and not any(b['source_id']=='S29:hk-hsbclife-existing' and 'WGSS-UI-58A48889FF96' in b['ui_work_ids'] for b in d['benchmarks']))
check('28 successful actual gateway jobs retained with model provenance',len(root['model_runs'])==28 and all(read(R/x['run_manifest'])['model']==x['model'] and x['model'] in ['claude-opus-5','claude-sonnet-5'] for x in root['model_runs']))
for fname,total in [('bank-ui-works.csv',216),('bank-ui-collection-matrix.csv',648),('bank-ui-priority-matrix.csv',96)]:
 csvrows=list(csv.DictReader(__import__('io').StringIO(d['csv_artifacts'][fname].lstrip('\ufeff'))));assert len(csvrows)==total and all(x['scope_version']=='bank-customer-ui-v1.1' for x in csvrows)
check('current downloads match full scope and all-country gaps',True)
# Full long quotes stay private, nested visual proof retains only source-specific statements.
def check_redaction(value):
 if isinstance(value,dict):
  if value.get('kind')=='normalized_text_character_range':assert 'excerpt' not in value
  for v in value.values():check_redaction(v)
 elif isinstance(value,list):
  for v in value:check_redaction(v)
check_redaction(d['benchmarks']);check('long publisher excerpts not exposed by public dataset',True)
print(json.dumps({'bank_expansion_v29':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
