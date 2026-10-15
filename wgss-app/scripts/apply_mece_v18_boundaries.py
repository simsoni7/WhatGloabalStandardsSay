"""One-time application of the separately curated v1.8 boundary ledger."""
import copy,hashlib,json,re
from pathlib import Path
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
STORE=ROOT/'research/source-store/mece-closure-20261005/sources'
review=read(ROOT/'data/mece-v18-boundary-dispositions.json')
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
assert ledger['new_version']=='WGSS-operation-v1.7-review-20261005','Already applied; do not rerun'
by={w['id']:w for w in read(RUN/'catalogue-input.json')['works']}
sections=read(RUN/'root-boundary-sections.json')
progress=read(ROOT/'data/mece-closure-review.json')
write(RUN/'v17-root-progress.json',progress)

def reference(sid):
 s=sections[sid];quote=s['text'][:150]
 if sid.startswith('BIAN:'):
  native=sid.split(':')[1];source_id='BIAN:14.0.0:portal:'+native
  # Correct old frozen metadata's documentation[n] locator to the literal
  # original categories[index] path; do not alter the frozen model input.
  path=Path(s['source_file']);raw=json.JSONDecoder().raw_decode(path.read_text().split('var objectData =',1)[1].strip())[0]
  docs=[(n,c) for n,c in enumerate(raw[native]['data'][0]['categories']) if c['type']=='documentation']
  index=docs[int(sid.split(':')[-1])][0]
  locator=f'objectData[{json.dumps(native)}].data[0].categories[{index}].content.value'
  snapshot='BIAN-14-public-portal-2026-10-02';sha=s['source_file_sha256']
 elif sid.startswith('ISO20022:') or sid.startswith('https:'):
  return None  # Current references already preserve these context definitions.
 elif sid.startswith('OFAC_UNBLOCKING_RULE:'):
  source_id='OFAC_UNBLOCKING_RULE';locator=s['source_locator'];snapshot='closure-20261004';sha=s['source_file_sha256']
 else:
  key=sid.split(':')[0];meta=read(STORE/(key+'.json'))
  assert hashlib.sha256((STORE/meta['raw_path']).read_bytes()).hexdigest()==meta['sha256']
  assert hashlib.sha256((STORE/meta['text_path']).read_bytes()).hexdigest()==meta['text_sha256']
  assert quote in (STORE/meta['text_path']).read_text()
  source_id='WGSS-PROCESS-'+key;locator=s['source_locator'];snapshot='WGSS-primary-process-20261006';sha=meta['sha256']
 return dict(id=source_id,name=s['name'],url=s['source_url'],locator=locator,source_snapshot_id=snapshot,
  source_sha256=sha,exact_quote=quote,rationale='별도 root 판정에서 실제 절차·조건과 대조한 직접 결과 근거',
  context_requires_review=False,proof_scope='specified_process_not_global_right_or_ui_capture')

retired={a['work_id']:a.get('target_ids',[]) for a in review['actions'] if a['decision'] in ['merged','rejected_unproven_candidate']}
for a in review['actions']:
 i=a['work_id'];assert i in by
 if a['decision']=='corrected_edit':
  fields=copy.deepcopy(a['fields']);refs=copy.deepcopy(by[i]['refs'])
  # Do not leave explicitly rejected HR/general-market nouns as direct proof.
  for r in refs:
   if (i=='WGSS-BB9E69AF7B7D' and r['id'].endswith(':29866')) or (i=='WGSS-EAB16CB1D4C4' and r['id'].endswith((':38574',':44259'))):
    r.update(context_requires_review=True,proof_scope='context_not_functional_responsibility',rationale='원 입력 맥락으로 보존하되 현재 직접 결과의 절차 근거로 사용하지 않습니다.')
  refs += [r for sid in a['evidence_section_ids'] if (r:=reference(sid))]
  fields.update(refs=refs,status='edited',source_gaps=[],review_note=a['reason'])
  ledger['edits'].append(dict(id=i,fields=fields,reason=a['reason'],phase='mece-closure-v18-explicit-root-review',automatic_adoption=False))
 elif a['decision']=='merged':
  assert len(a['target_ids'])==1
  ledger['merges'].append({'from':i,'into':a['target_ids'][0],'reason':a['reason']})
 else:
  ledger['noncountable_contexts'].append(dict(id=i,targets=[],reason=a['reason'],retained_as='rejected_unproven_financial_responsibility_candidate'))
 progress['root_decisions'].append({k:v for k,v in a.items() if k!='fields'})

# Explicitly preserve the matching boundary on the generic conventional row.
i='WGSS-6CA6BDD01105'
ledger['edits'].append(dict(id=i,fields=dict(excludes=by[i]['excludes']+['참가자 위험을 상호보장 풀에서 공유하는 리타카풀 출재(WGSS-3DFF635AF396)']),reason='IFSB 위험 풀의 권리 구조를 일반 재보험자 인수와 상호 구분합니다.',phase='mece-closure-v18-explicit-root-review',automatic_adoption=False))
progress['root_decisions'].append(dict(work_id=i,decision='corrected_edit',reason=ledger['edits'][-1]['reason'],job_id='boundary-v18-02',automatic_adoption=False))
ledger['new_version']='WGSS-operation-v1.8-review-20261006'
progress.update(version='WGSS-mece-closure-v18-20261006',output_version=ledger['new_version'],v18_boundary_patch_applied=True,
 current_stage='full_source_advisory_complete_result_adjudication_running',technical_validation=dict(state='pending',note='v1.8 changes require fresh regression'),
 v18_boundary_decisions=review['actions'],v18_source_model_review=dict(expected_rows=927,reviewed_rows=927,automatic_adoption=False,root_adjudication_complete=False))
for r in progress.get('delta_root_dispositions',[]):
 if r['id'] in retired:r.update(state='resolved_v18',reason='별도 v1.8 원문 판정으로 해결했습니다.')
write(ROOT/'data/operation-backbone-dispositions.json',ledger);write(ROOT/'data/mece-closure-review.json',progress)

def replace(ids):return list(dict.fromkeys(t for i in ids for t in retired.get(i,[i])))
nav=read(ROOT/'data/business-backbone-review.json')
nav['operation_version']=ledger['new_version'];nav['assignments']=[a for a in nav['assignments'] if a['id'] not in retired]
for g in nav['goals']:
 for field in ['canonical_work_ids','optional_work_ids']:g[field]=replace(g[field])
write(ROOT/'data/business-backbone-review.json',nav)
products=read(ROOT/'data/product-profiles-review.json')
for p in products['product_profiles']:
 for step in p['steps']:
  for field in ['work_ids','review_candidate_ids']:
   if field in step:step[field]=replace(step[field])
write(ROOT/'data/product-profiles-review.json',products)
print('Applied explicit v1.8 edits, 2 merges, 1 unsupported candidate removal; no MECE approval')
