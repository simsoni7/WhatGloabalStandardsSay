# Historical v30 oracle, frozen before v31 admissions. Current evidence tested separately.
"""Current source admissions: financial outcomes, channel ownership and immutable proof."""
import json,csv,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v30.json');base=read(R/'data/bank-ui-baseline-v29.json');root=read(R/'data/bank-ui-collection-v30-decisions.json');private={b['id']:b for b in read(R/'data/bank-ui-benchmark-dispositions.json')['examples'] if b['id'] in {x['id'] for x in d['benchmarks']}};newids={x['example_id'] for x in root['admitted_examples']};rows=[private[id] for id in sorted(newids)];checks=[]
def check(n,ok):assert ok,n;checks.append(n)
check('scope216 unchanged, country and illustration variants never create work IDs',len(d['works'])==216 and d['works']==base['works'] and d['version']=='bank-customer-ui-v1.1' and not root['scope_change'])
check('old188 public examples untouched,14 qualified root admissions only',len(rows)==14 and len(d['benchmarks'])==202 and all(next(b for b in d['benchmarks'] if b['id']==x['id'])==x for x in base['benchmarks']) and not newids&{x['id'] for x in base['benchmarks']})
check('progress separates104 works,15 providers,56 guides and no observed app',d['benchmark_counts']=={'works_with_function_documents':104,'examples':202,'providers':15,'countries':3,'official_guide_screens':56,'public_web_captures':2,'works_with_screen_references':22,'observed_app_captures':0,'verified_app_ui_versions':0,'unlinked_works':112})
check('all648 country cells and96 pilot tasks retained',len(d['collection_matrix'])==648 and d['collection_counts']['linked_country_work_cells']==157 and d['collection_counts']['empty_country_work_cells']==491 and d['collection_counts']['screen_country_work_cells']==30 and d['priority_collection']==base['priority_collection'])
sources={p['prefix']+':'+s['id']:s for p in root['source_batches'] for s in read(R/p['manifest'])};assets={a['id']:a for a in read(R/'research/source-store/bank-gap-assets-v30-20261012/assets.json')};sha=set()
for b in rows:
 s=sources[b['source_id']];t=s['text'];assert b['country']==s['country'] and b['provider_id']==s['provider_id'];assert hashlib.sha256((R/s['snapshot_path']/s['raw_filename']).read_bytes()).hexdigest()==b['raw_sha256'];assert hashlib.sha256(t.encode()).hexdigest()==b['text_sha256'];assert not b['observed_app_screen'] and b['verified_ui_version'] is None and not b['current_ui_verified']
 for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']]:assert t[q['start']:q['end']]==q['excerpt']
 for e in ([b['screen_evidence']]+b.get('additional_screen_evidence',[])) if b.get('screen_evidence') else []:
  a=assets[e['source_asset_id']];assert a['source_id']==b['source_id'];assert hashlib.sha256((R/'dist'/e['image_path']).read_bytes()).hexdigest()==hashlib.sha256((R/a['private_path']).read_bytes()).hexdigest()==e['image_sha256'];sha.add(e['image_sha256']);assert e['visual_review']=='root_visual_checked'
  if e.get('pdf_page'):assert e['raw_pdf_sha256']==b['raw_sha256'] and e['pdf_page']==a['page']
  if e.get('display_region'):
   r=e['display_region'];assert [r['original_width'],r['original_height']]==[a['width'],a['height']];x0,y0,x1,y1=r['bbox_xyxy'];assert 0<=x0<x1<=a['width'] and 0<=y0<y1<=a['height']
 assert any((c['id'],c['source_id'],c['work_id'],c['native_expression'])==(b['id'],b['source_id'],b['ui_work_ids'][0],b['expression']) for c in root['final_source_review'])
check('every own quote, country, actor, guide hash and final binding verified',True)
check('95 raw assets become only10 selected distinct financial guide images',len(assets)==95 and len(sha)==10 and root['guide_images_admitted']==10)
check('NatWest payment request Sent is not actual disbursement',private['BANK-BENCH-210']['ui_work_ids']==['WGSS-UI-2DB1D4844DD5'] and 'Sent' in private['BANK-BENCH-210']['conditions'] and private['BANK-BENCH-210']['screen_evidence']['platform_kind']=='web')
check('trade collection branch not DC negotiation; guarantee request not issuance',private['BANK-BENCH-213']['ui_work_ids']==['WGSS-UI-331D28E565D3'] and 'Documents for Collection' in private['BANK-BENCH-213']['context_ko'] and private['BANK-BENCH-214']['ui_work_ids']==['WGSS-UI-612DC2279226'])
check('future money mandate separate example, not extra pension work; web meaning narrowed',private['BANK-BENCH-218']['ui_work_ids']==private['BANK-BENCH-219']['ui_work_ids']==private['BANK-BENCH-220']['ui_work_ids']==['WGSS-UI-58A48889FF96'] and '향후' in private['BANK-BENCH-219']['context_ko'] and '기존 적립금' in private['BANK-BENCH-220']['meaning'])
check('Permanent Departure only early claim, not normal retirement or observed payment',private['BANK-BENCH-221']['ui_work_ids']==['WGSS-UI-A12F4C4E3669'] and private['BANK-BENCH-221']['expression']=='Permanent Departure from Hong Kong' and '65세 정상 수급' in private['BANK-BENCH-221']['meaning'])
check('pension administration operator distinct from issuer, trustee and HSBC distribution',all(b['provider_kind']=='pension_administration_platform_operator' for b in rows if b['provider_id']=='empf-hk') and len(root['current_channel_corrections'])==1 and not any(b['provider_id']=='hsbc-hk' and 'WGSS-UI-58A48889FF96' in b['ui_work_ids'] for b in d['benchmarks']))
check('group pension insurance application not pension-plan registration or approved contract',all(private[id]['ui_work_ids']==['WGSS-UI-E6ECD0996B28'] and private[id]['function_observation']=='official_public_frontend_template_described_flow' for id in ['BANK-BENCH-225','BANK-BENCH-226']) and not any(b['source_id']=='S30:kr-samsung-restoration' for b in d['benchmarks']))
check('unsupported completion, third-party voting and incomplete MPF membership staged',not any(x in private for x in ['BANK-BENCH-211','BANK-BENCH-217','BANK-BENCH-222']) and len(root['staged_semantic_routes'])==5 and root['new_staged_semantic_routes']==3 and len(d['collection_plan']['definition_review_gaps'])==1)
check('payment-data submission and TradePay loan are not invoice-payout/pension-receipt equivalents',len(root['rejected_source_routes'])==6 and not any(b['source_id']=='S30:hk-hsbc-tradepay' for b in d['benchmarks']) and not any(b['source_id']=='S30:hk-empf-contribution-web' for b in d['benchmarks']))
check('43 real gateway successes and4 failed groups retained and replaced',len(root['model_runs'])==43 and len(root['failed_jobs_replaced'])==4 and all(read(R/r['run_manifest'])['model']==r['model'] and r['model'] in ['claude-sonnet-5','claude-opus-5'] for r in root['model_runs']))
check('19 primary research targets, staged Malaysia not silently fourth market',len(d['collection_plan']['provider_targets'])==19 and {t['country'] for t in d['collection_plan']['provider_targets']}=={'KR','GB','HK'} and not any(b['country']=='MY' for b in d['benchmarks']))
for name,count in [('bank-ui-works.csv',216),('bank-ui-collection-matrix.csv',648),('bank-ui-priority-matrix.csv',96)]:assert len(list(csv.DictReader(__import__('io').StringIO(d['csv_artifacts'][name].lstrip('\ufeff')))))==count
check('downloads retain all works and empty country cells',True)
check('global MECE, human approval and measured utility never inferred',not d['global_financial_industry_mece_approved'] and not root['independent_human_review'] and not d['breadth_progress']['practitioner_utility_measured'])
print(json.dumps({'bank_gaps_v30':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
