# Historical v1/v28 oracle retained; current v1.1 is independently checked in bank_expansion_v29.py.
"""Whole-scope evidence, source-work binding and practical readiness separation."""
import collections,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v28.json');root=read(R/'data/bank-ui-collection-v28-decisions.json');bank=read(R/'data/bank-ui-benchmark-dispositions.json');newids={x['example_id'] for x in root['admitted_examples']};rows=[b for b in bank['examples'] if b['id'] in newids];sources={x['prefix']+':'+s['id']:s for x in root['source_batches'] for s in read(R/x['manifest'])};checks=[]
def check(n,ok):assert ok,n;checks.append(n)
check('39 admissions increase distinct work breadth, not just pilot duplicates',len(rows)==39 and d['benchmark_counts']['examples']==166 and d['benchmark_counts']['works_with_function_documents']==85 and d['benchmark_counts']['unlinked_works']==129 and len(d['works'])==214 and not root['scope_change'])
for b in rows:
 s=sources[b['source_id']];p=R/s['snapshot_path'];t=(p/'normalized.txt').read_text();assert hashlib.sha256((p/s.get('raw_filename','source.html')).read_bytes()).hexdigest()==b['raw_sha256'];assert hashlib.sha256(t.encode()).hexdigest()==b['text_sha256'];assert b['country']==s['country'] and b['provider_id']==s['provider_id']
 for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']]:assert t[q['start']:q['end']]==q['excerpt']
 assert b['root_function_admitted'] and not b['observed_app_screen'] and b['verified_ui_version'] is None
 if b.get('native_faq_id'):
  obj=json.loads((p/'source.json').read_bytes())['result'];assert obj['title']==b['faq_title'];actual=' '.join((obj['title']+' '+BeautifulSoup(obj['content'],'html.parser').get_text(' ',strip=True)).split());assert actual==t
check('every source and qualification belongs to its own original body and provider',True)
check('all assigned final reviews bind source, work and label, not only row ID',len(root['final_source_review'])==39 and all(any(x['id']==b['id'] and x['source_id']==b['source_id'] and x['work_id']==b['ui_work_ids'][0] and x['native_expression']==b['expression'] for x in root['final_source_review']) for b in rows))
check('incorrect swapped critiques preserved and never treated as independent approval',len(root['model_assignment_errors'])==1 and root['independent_human_review'] is False and root['automatic_adoption'] is False)
check('whole214 routing is not a count of FAQ questions or exhaustive provider support',root['breadth_discovery']['frozen_work_ids']==214 and root['breadth_discovery']['deduplicated_questions']==2079 and not root['breadth_discovery']['provider_exhaustiveness_claimed'])
expected={}
for run in ['bank-breadth-v28-20261012','bank-breadth-additional-v28-20261012']:
 p=R/'research/source-store'/run
 for f in p.glob('inputs/*discovery-*.json'):
  job=read(f);prop=read(next((p/'reviews'/job['id']).glob('*/proposal.json')));assert {x['source_id'] for x in prop['result']['rows']}==set(job['expected_ids']);assert len(prop['result']['rows'])==len(job['expected_ids']);expected.update({x['source_id']:True for x in prop['result']['rows']})
check('all2079 assigned unique questions actually reviewed, no invisible dropped batches',len(expected)==2079 and len(root['failed_jobs_replaced'])==3)
check('67 actual successful gateway jobs have raw provenance',len(root['model_runs'])==67 and all(read(R/x['run_manifest'])['model']==x['model'] and x['model'] in ['claude-opus-5','claude-sonnet-5'] for x in root['model_runs']))
check('request-only, amountless and channel-limit substitutions not forced into work cells',not any(b['id'] in ['BANK-BENCH-149','BANK-BENCH-150','BANK-BENCH-159','BANK-BENCH-169'] for b in bank['examples']) and len(d['collection_plan']['definition_review_gaps'])==2)
byid={b['id']:b for b in rows};check('certificate access history and sweep branch scopes narrowed', '외부기관' in byid['BANK-BENCH-134']['meaning'] and byid['BANK-BENCH-153']['expression']=='10%씩 모으기' and '고정 금액' in byid['BANK-BENCH-153']['wgss_mapping_note'])
check('loan electronic contract distinct from loan application and credit-capacity termination',byid['BANK-BENCH-173']['ui_work_ids']==['WGSS-UI-0DD0B76C851C'] and '전자서명' in byid['BANK-BENCH-173']['function_proof']['excerpt'] and byid['BANK-BENCH-175']['source_id']=='N28:kr-faq-7990')
for b in rows:
 if not b.get('screen_evidence'):continue
 for e in [b['screen_evidence']]+b.get('additional_screen_evidence',[]):
  assert e['source_locator']['image_ordinal'] in [6,8];assert hashlib.sha256((R/'dist'/e['image_path']).read_bytes()).hexdigest()==e['image_sha256'];assert e['image_derivation']=='original_official_guide_asset'
check('only2 source-matching rates guides admitted, currency-execution images staged',d['benchmark_counts']['official_guide_screens']==28 and d['benchmark_counts']['public_web_captures']==2 and d['benchmark_counts']['observed_app_captures']==0 and root['guide_images_staged_not_counted']==4)
for dom in d['breadth_progress']['domains']:
 ws={w['id'] for w in d['works'] if w['domain_id']==dom['id']};linked={id for b in d['benchmarks'] for id in b['ui_work_ids']};assert dom['works']==len(ws) and dom['linked_works']==len(ws&linked) and dom['unlinked_works']==len(ws-linked)
check('domain arithmetic preserves all214, including unlinked optional functions',sum(x['works'] for x in d['breadth_progress']['domains'])==214 and sum(x['linked_works'] for x in d['breadth_progress']['domains'])==85 and len(d['breadth_progress']['work_queue'])==214)
plan=d['capture_plan'];check('capture plans cover all642 distinct cells, 32 pilot remains96',len(plan['cells'])==642 and len({(x['work_id'],x['country']) for x in plan['cells']})==642 and plan['counts']['planned_works']==214 and d['priority_collection']['cells']==96 and plan['counts']['function_linked_cells']==133 and plan['counts']['cells_without_screen']==623)
check('inapplicability and full-flow readiness are never inferred from empty/reference cells',all(x['market_applicability']=='not_assessed' and x['ready_for_use_review']=='not_assessed' for x in plan['cells']) and not d['breadth_progress']['practitioner_utility_measured'])
check('real completion metadata conflicts remain explicit and do not silently change scope',len(root['semantic_field_review_queue'])==3 and root['denominator']==214 and not root['scope_change'])
print(json.dumps({'bank_breadth_v28':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
