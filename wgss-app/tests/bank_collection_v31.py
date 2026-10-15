# Historical v31 oracle; current source admissions checked independently in v32.
"""Independent v31 evidence, exact source ranges, financial boundaries and transfer plan."""
import json,hashlib,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v31.json');base=read(R/'data/bank-ui-baseline-v30.json');root=read(R/'data/bank-ui-collection-v31-decisions.json');private={b['id']:b for b in read(R/'data/bank-ui-benchmark-dispositions.json')['examples']};ids={x['example_id'] for x in root['admitted_examples']};rows=[private[id] for id in sorted(ids)];checks=[]
def check(n,ok):assert ok,n;checks.append(n)
check('scope216 definitions unchanged, country-language illustrations do not multiply works',d['works']==base['works'] and len(d['works'])==216 and not root['scope_change'])
check('24 explicit admissions preserve prior202 public examples',len(rows)==24 and len(d['benchmarks'])==226 and all(next(b for b in d['benchmarks'] if b['id']==old['id'])==old for old in base['benchmarks']))
check('independent progress units reconcile',d['benchmark_counts']=={'works_with_function_documents':110,'examples':226,'providers':15,'countries':3,'official_guide_screens':74,'public_web_captures':2,'works_with_screen_references':24,'observed_app_captures':0,'verified_app_ui_versions':0,'unlinked_works':106} and d['collection_counts']['linked_country_work_cells']==167 and d['collection_counts']['empty_country_work_cells']==481 and d['collection_counts']['screen_country_work_cells']==32)
sources={p['prefix']+':'+s['id']:s for p in root['source_batches'] for s in read(R/p['manifest'])};hashes=set()
for b in rows:
 s=sources[b['source_id']];t=s['text'];assert b['country']==s['country'] and b['provider_id']==root['provider_id_aliases'].get(s['provider_id'],s['provider_id']);assert hashlib.sha256((R/s['snapshot_path']/s['raw_filename']).read_bytes()).hexdigest()==b['raw_sha256']==s['raw_sha256'];assert hashlib.sha256(t.encode()).hexdigest()==b['text_sha256'];assert b['root_function_admitted'] and not b['observed_app_screen'] and not b['current_ui_verified'] and b['verified_ui_version'] is None
 for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[c['proof'] for c in b['policy_claims']]:assert t[q['start']:q['end']]==q['excerpt']
 assert len(b['flow_steps'])==len(b['flow_step_proofs'])
 c=next(c for c in root['final_source_review'] if c['id']==b['id']);assert (c['source_id'],c['work_id'],c['native_expression'])==(b['source_id'],b['ui_work_ids'][0],b['expression'])
 for e in ([b['screen_evidence']]+b.get('additional_screen_evidence',[])) if b.get('screen_evidence') else []:
  assert e['visual_review']=='root_visual_checked' and e['raw_pdf_sha256']==b['raw_sha256'] and e['image_derivation']=='original_official_pdf_page_render';assert hashlib.sha256((R/'dist'/e['image_path']).read_bytes()).hexdigest()==e['image_sha256'];hashes.add(e['image_sha256']);assert not e.get('private_image_path')
  if e.get('display_region'):
   a=e['display_region'];x0,y0,x1,y1=a['bbox_xyxy'];assert 0<=x0<x1<=a['original_width'] and 0<=y0<y1<=a['original_height']
check('every native label, own-source quote, binding and full original image hash verified',True)
check('72 staged PDF renders produce only18 selected unique financial guide images',root['raw_asset_inventory']==72 and root['guide_images_admitted']==len(hashes)==18)
check('source-described deposit partial vs termination vs maturity instructions stay distinct',private['BANK-BENCH-241']['ui_work_ids']==['WGSS-UI-B85A9A562018'] and '100만원' in private['BANK-BENCH-241']['conditions'] and '10만원' in private['BANK-BENCH-245']['conditions'] and private['BANK-BENCH-242']['ui_work_ids']==['WGSS-UI-06FC495733F0'] and all(private[id]['ui_work_ids']==['WGSS-UI-1C6D9879F35A'] for id in ['BANK-BENCH-229','BANK-BENCH-243','BANK-BENCH-244']))
check('maturity-after reinvestment not included in before-maturity branch',private['BANK-BENCH-228']['ui_work_ids']==['WGSS-UI-D621DF37D64F'] and '만기 후' in private['BANK-BENCH-228']['wgss_mapping_note'] and len(private['BANK-BENCH-228']['policy_claims'])==1)
check('HK app2 and web4 renewal choices not blended into one UI',private['BANK-BENCH-234']['ui_work_ids']==['WGSS-UI-06FC495733F0'] and 'HSBC HK App은 원리금·원금만' in private['BANK-BENCH-234']['meaning'] and 'Online Banking은 추가로' in private['BANK-BENCH-234']['meaning'])
check('HL cancellation not broker expiry or settled-trade reversal',private['BANK-BENCH-232']['ui_work_ids']==['WGSS-UI-19FB8877A06C'] and '만기 경과 삭제' in private['BANK-BENCH-232']['wgss_mapping_note'] and '수락 여부' in ' '.join(private['BANK-BENCH-232']['flow_steps']))
check('four Chinese allocation branches retain one work; future existing assets unchanged',all(private['BANK-BENCH-'+str(n)]['ui_work_ids']==['WGSS-UI-58A48889FF96'] and private['BANK-BENCH-'+str(n)]['language']=='zh-Hant-HK' for n in range(246,250)) and all('바뀌지' in private['BANK-BENCH-'+str(n)]['meaning'] for n in [247,249]) and all('오후 4시 또는 그 이후' in private['BANK-BENCH-'+str(n)]['conditions'] for n in range(246,250)))
check('future submit proof is actual B5 instruction not success message',private['BANK-BENCH-247']['flow_step_proofs'][3]['excerpt']=='B5 核對資料並按 提交。')
check('Permanent Departure remains early request not normal65 pension payout',private['BANK-BENCH-250']['ui_work_ids']==['WGSS-UI-A12F4C4E3669'] and '영구 출국' in private['BANK-BENCH-250']['meaning'] and '이후' in private['BANK-BENCH-250']['flow_steps'][-1])
check('latest enrolment only application, not completion; prior5 review tickets retained',root['definition_boundary_review']['root_decision']=='keep_application_stage_separate_do_not_admit_membership_completion' and len(root['staged_semantic_routes'])==5 and len(d['collection_plan']['definition_review_gaps'])==1 and not any('enrolment' in b['source_id'] for b in rows))
check('all24 actual gateway jobs retained, one transport failure cannot auto approve',len(root['model_runs'])==24 and all(read(R/x['run_manifest'])['model']==x['model'] for x in root['model_runs']) and len(root['failed_jobs_replaced'])==2)
a=d['authenticated_collection'];check('integration synthetic checks41 separate from zero bank sessions',a['local_tool']['checks']==41 and a['local_tool']['validation_status']=='passed_synthetic_only' and not a['local_tool']['real_service_validated'] and a['environment']['live_authenticated_service_connections']==0)
check('chat image fallback pending, no official version or direct observation implied',a['chat_image_fallback']['evidence_type']=='user_supplied_image' and not a['chat_image_fallback']['automatic_adoption'] and not a['chat_image_fallback']['verified_version_implied'] and not a['chat_image_fallback']['installed_app_observation_implied'] and any(m['id']=='chat-image-fallback' for m in a['methods']))
with zipfile.ZipFile(R/'dist/tools/wgss-local-capture-v31.zip') as z:
 assert set(z.namelist())=={'local_session_capture.py','bank-ui.json','README.md','requirements.txt'};catalogue=json.loads(z.read('bank-ui.json'));assert len(catalogue['works'])==216 and {w['id'] for w in catalogue['works']}=={w['id'] for w in d['works']};assert '대화창에 이미지' in z.read('README.md').decode()
check('download bundle usable with current216 IDs, no source secrets/session exports',True)
check('globalMECE, independenthuman approval and practitionerutility not inferred',not d['global_financial_industry_mece_approved'] and not root['independent_human_review'] and not d['breadth_progress']['practitioner_utility_measured'] and d['priority_collection']==base['priority_collection'])
print(json.dumps({'bank_collection_v31':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
