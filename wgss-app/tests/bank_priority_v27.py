# Historical v1/v28 oracle retained; current v1.1 is independently checked in bank_expansion_v29.py.
"""Own FAQ records, public capture state fidelity, bounded gaps and provider identities."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v28.json');root=read(R/'data/bank-ui-collection-v27-decisions.json');private={b['id']:b for b in read(R/'data/bank-ui-benchmark-dispositions.json')['examples']};sources={b['prefix']+':'+s['id']:s for b in root['source_batches'] for s in read(R/b['manifest'])};checks=[]
def check(n,ok):assert ok,n;checks.append(n)
rows=[b for b in d['benchmarks'] if b['source_id'].startswith(('V27:','F27:','X27:','W27:'))]
check('scope 214 retained, 18 explicit admissions and 78 of 96 priority cells',len(d['works'])==214 and not root['scope_change'] and len(rows)==18 and d['priority_collection']=={'works':32,'cells':96,'reviewed_cells':96,'works_with_examples':32,'linked_cells':78,'screen_cells':16,'flow_and_condition_cells':39})
check('provider identity distinguishes bank from card subsidiary',d['benchmark_counts']['providers']==8 and len(d['collection_plan']['provider_targets'])==10 and next(b for b in d['benchmarks'] if b['id']=='BANK-BENCH-012')['provider_name']=='우리카드' and all(b['provider_name']=='우리은행' for b in rows if b['provider_id']=='woori-bank'))
for pub in rows:
 b=private[pub['id']];s=sources[b['source_id']];folder=R/s['snapshot_path'];t=(folder/'normalized.txt').read_text();raw=(folder/s.get('raw_filename','source.html')).read_bytes();assert hashlib.sha256(t.encode()).hexdigest()==b['text_sha256'] and hashlib.sha256(raw).hexdigest()==b['raw_sha256']
 for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']]:assert t[q['start']:q['end']]==q['excerpt']
 assert len(b['flow_steps'])==len(b['flow_step_proofs']) and not b['observed_app_screen'] and b['verified_ui_version'] is None
 if b['source_id'].startswith(('F27:','X27:')):
  record=json.loads(raw)['result'];assert record['title']==b['faq_title'] and str(record.get('post_id',record.get('id',b['native_faq_id'])))==str(b['native_faq_id'])
check('every outcome and condition belongs to its own HTML/FAQ/rendered snapshot',True)
check('index scope is explicit FAQ unit, not extra banking work',root['public_faq_census']['index_pages']==54 and root['public_faq_census']['unique_publisher_questions']==527 and root['public_faq_census']['own_records_resolved']==32 and root['public_faq_census']['count_unit'].startswith('publisher FAQ'))
check('completed discovery+extraction+critics have actual Bedrock provenance',len(root['model_runs'])==23 and all(x['prompt_sha256'] and x['usage'] for x in root['model_runs']) and {x['model'] for x in root['model_runs']}=={'claude-sonnet-5','claude-opus-5'})
check('shipping, existing favourites and unconfirmed instruction amendment not forced into gaps',not any(b['id'] in ['BANK-BENCH-114','BANK-BENCH-121','BANK-BENCH-130'] for b in d['benchmarks']) and sum(x['root_decision']=='reject' for x in root['row_dispositions'])==3)
b=private['BANK-BENCH-115'];t=sources[b['source_id']]['text'];check('standing order deletion references 常行 not single scheduled transfer',all('常行指示' in q['excerpt'] for q in [b['function_proof']]+b['flow_step_proofs']))
check('dues rules never become actual payer standing order by assumption',not any(b['source_id'] in ['F27:kr-faq-13259','F27:kr-faq-13265','V27:kr-apt'] for b in rows))
check('physical card rear is not promoted as a digital card detail view',not any(b['source_id']=='F27:kr-faq-8090' for b in rows))
captures={x['id']:x for x in read(R/root['public_capture_manifest'])};b=private['BANK-BENCH-132']
for e in [b['screen_evidence']]+b['additional_screen_evidence']:
 c=captures[e['source_locator']['capture_id']];assert hashlib.sha256((R/'dist'/e['image_path']).read_bytes()).hexdigest()==hashlib.sha256((R/c['image_path']).read_bytes()).hexdigest()==e['image_sha256'];assert not c['authenticated'] and not c['credentials_entered'] and not c['authentication_attempted'] and not c['financial_form_submitted'];assert e['image_derivation']=='original_playwright_screenshot' and e['browser_version'] and e['captured_at']
check('two original public web captures never counted as installed app observations',d['benchmark_counts']['public_web_captures']==2 and d['benchmark_counts']['official_guide_screens']==28 and d['benchmark_counts']['observed_app_captures']==0 and b['reference_role']=='observed_public_entry_controls_only')
plan=d['capture_plan'];check('capture plan expands beyond pilot while retaining public-first choice',plan['user_choice']=='public_web_and_official_guides_first' and len(plan['cells'])==642 and plan['counts']['function_linked_cells']==133 and plan['counts']['cells_without_screen']==623 and not plan['automatic_collection_scheduled'] and plan['environment']['connected_android_devices']==0)
check('article and FAQ screenshots excluded from financial UI reference capture types',not any(b['source_id'].endswith('kakao-public-faq') for b in rows) and any(x['id']=='document_page_screenshot' for x in plan['evidence_types']))
print(json.dumps({'bank_priority_v27':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
