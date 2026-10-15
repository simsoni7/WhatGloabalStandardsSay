"""One-time root admission after retained provider evidence and two critiques."""
import copy,hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-priority-v26-20261011';SUP=R/'research/source-store/bank-priority-v26-supplement-20261011'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 dest=R/'data/bank-ui-collection-v26-decisions.json';assert not dest.exists(),'Do not rerun a recorded root batch'
 reviewed=read(RUN/'root-final-candidates.json');final=read(next((RUN/'reviews/v26-final-source-review').glob('*/proposal.json')))
 assert {x['id'] for x in final['result']['rows']}=={b['id'] for b in reviewed['examples']}
 assert not any(x['status']=='reject' for x in final['result']['rows'])
 bank=read(R/'data/bank-ui-benchmark-dispositions.json');assert len(bank['examples'])==92
 rows=reviewed['examples'];sources={p+':'+s['id']:s for p,run in [('V26',RUN),('V26S',SUP)] for s in read(run/'sources.json')};images={i['sha256']:i for i in read(RUN/'guide-images.json')}
 final_before=copy.deepcopy(rows);by={b['id']:b for b in rows}
 b=by['BANK-BENCH-094'];b['policy_claims'][0]['description_ko']='이 신원확인 과정의 사전 준비물로 휴대폰과 유효한 사진 신분증을 안내';b['conditions']=b['policy_claims'][0]['description_ko']
 by['BANK-BENCH-099']['meaning']='신분 자료 제출 이후 앱 접속용 PIN 설정. PIN 생성과 신분증 검증 성공은 서로 다른 단계'
 by['BANK-BENCH-098']['review_note']='금융사가 공개한 신원확인 설명용 원본 이미지입니다. 루트가 시각 확인했으며 Bedrock 검토자는 픽셀·앱 버전을 독립 검증하지 않았습니다.'
 by['BANK-BENCH-102']['review_note']='마지막 화면도 금융사의 설명용 개설 완료 예시입니다. 실제 고객 신청·승인·개설을 관찰한 결과가 아닙니다.'
 by['BANK-BENCH-109']['review_note']='본문의 입금 가능 여력 설명이 아니라 공식 원본 이미지에 표시된 출금가능금액 필드를 시각 확인한 근거입니다. 모델은 픽셀을 독립 검증하지 않았습니다.'
 final_root=[]
 for finding in final['result']['rows']:
  changed=by[finding['id']]!=next(b for b in final_before if b['id']==finding['id'])
  final_root.append({'id':finding['id'],'model_finding':finding,'root_decision':'retain_after_clarification' if changed else 'retain_existing_verified_scope','reason_ko':'준비물·독립 단계·이미지 검증 범위의 표현을 명료화' if changed else '원어·조건의 적용 범위, 미확인 조건, 미해결 연령 충돌과 안내 이미지 한정이 이미 본문 또는 펼침 정보에 명시됨. 추가 사실·새 기능을 모델 상태만으로 채택하지 않음','automatic_adoption':False})
 for b in rows:
  s=sources[b['source_id']];t=s['text']
  assert hashlib.sha256(t.encode()).hexdigest()==b['text_sha256']
  for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']]:
   if q['kind']=='normalized_text_character_range':assert t[q['start']:q['end']]==q['excerpt']
   else:assert q['kind']=='official_image_region' and q['review']=='root_visual_checked'
  if b.get('screen_evidence'):
   for e in [b['screen_evidence']]+b.get('additional_screen_evidence',[]):
    im=images[e['image_sha256']];assert im['source_id']==b['source_id'] and any(i['url']==e['asset_url'] for i in s['images'])
    assert hashlib.sha256((R/im['private_path']).read_bytes()).hexdigest()==e['image_sha256'];out=R/'dist'/e['image_path'];out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/im['private_path'],out)
  if b['provider_id']=='monzo':b['market_proof']={'country':'GB','proof':{'kind':'normalized_text_character_range','start':t.index('United Kingdom'),'end':t.index('United Kingdom')+len('United Kingdom'),'excerpt':'United Kingdom'},'basis_ko':'공식 사이트의 영국 지역 표시. 국가별 자격 조건은 각 사례에 별도 보존.'}
 bank['examples']+=rows;bank['collection_batches'].append({'batch':'collection-v26','root_ledger':str(dest.relative_to(R)),'scope_change':False})
 prior=read(R/'data/bank-ui-collection-v25-decisions.json');audits=copy.deepcopy(prior['priority_cell_dispositions'])
 for a in audits:
  own=[id for id,s in sources.items() if s['country']==a['country'] and s.get('text')];a['reviewed_source_ids']+=own;a['reviewed_provider_ids']=sorted(set(a['reviewed_provider_ids'])|{sources[id]['provider_id'] for id in own})
  own_rows=[b for b in bank['examples'] if b['country']==a['country'] and a['ui_work_id'] in b['ui_work_ids']];paired=any(b.get('flow_steps') and b.get('policy_claims') for b in own_rows)
  a['next_action_ko']='현지 금융사의 기능·정책 근거 추가 수집' if not own_rows else '공식 화면 예시 추가 수집' if not any(b.get('screen_evidence') for b in own_rows) else '상세 적용 조건·처리 결과 추가 확인' if not paired else '다른 현지 플랫폼과 비교·화면 버전 확인'
  a['method_ko']='v25의 제한된 공식 자료 검토에 v26의 새 공식 본문·동일 상품/예시 구간·시각 확인을 추가. 대상 금융사 전체의 완전 탐색은 아님.'
 runs=[]
 for prefix,directory in [('V26',RUN),('V26S',SUP)]:
  for p in sorted((directory/'reviews').glob('*/*/proposal.json')):
   d=read(p);runs.append({k:d[k] for k in ['job_id','model','prompt_sha256','usage']}|{'source_batch':prefix})
 dispositions=[dict(x,root_decision='admit' if x['root_decision']!='reject' else 'reject') for x in reviewed['row_dispositions']]
 ledger={'scope_version':'bank-customer-ui-v1','denominator':214,'scope_change':False,'reviewed_at':'2026-10-11','source_batches':prior['source_batches']+[{'prefix':p,'manifest':str((run/'sources.json').relative_to(R))} for p,run in [('V26',RUN),('V26S',SUP)]],'model_runs':runs,'admitted_examples':[{'example_id':b['id'],'source_id':b['source_id'],'work_id':b['ui_work_ids'][0],'root_decision':'admit','automatic_adoption':False} for b in rows],'row_dispositions':dispositions,'changed_rows':reviewed['changed_rows'],'rejected_findings':reviewed['rejected_findings'],'priority_cell_dispositions':audits,'automatic_adoption':False,'independent_human_review':False,'prior_root_ledger':'data/bank-ui-collection-v25-decisions.json','final_review':{k:final[k] for k in ['job_id','model','prompt_sha256','usage']},'critic_review':reviewed['critic_run'],'transport_retries_ko':'원문과 일치하지 않는 인용·표기를 검사해 거절한 응답은 보존하고, 별도 bounded 입력으로 재시도. 중단된 Opus 1회는 동일 입력 재시도로 완료. 모든 결과는 루트 검토 후 반영.'}
 ledger['final_root_dispositions']=final_root
 ledger['final_clarifications']=[{'id':b['id'],'before':old,'after':b,'automatic_adoption':False} for b,old in zip(rows,final_before) if b!=old]
 write(dest,ledger);write(R/'data/bank-ui-benchmark-dispositions.json',bank)
 plan=read(R/'data/bank-ui-collection-plan.json');plan.update(plan_version='collection-v26',priority_audit_ledger=str(dest.relative_to(R)),latest_execution={'batch':'collection-v26','new_source_targets':19,'reused_frozen_sources':7,'fetched_new_sources':19,'admitted_new_examples':len(rows),'root_rejected_candidates':len(dispositions)-len(rows),'bedrock_successful_jobs':len(runs),'actual_app_captures':0,'priority_work_country_cells':96,'root_reviewed_cells':96},release_quality_review={'batch':'collection-v26','reviewer':'claude-opus-5 + claude-sonnet-5','rows_reviewed':19,'final_retained_rows_reviewed':len(rows),'root_corrected_rows':len(reviewed['changed_rows']),'steward_ledger':str(dest.relative_to(R)),'independent_human_review':False});write(R/'data/bank-ui-collection-plan.json',plan)
 print(json.dumps({'admitted':len(rows),'total_examples':len(bank['examples']),'successful_model_jobs':len(runs)}))
if __name__=='__main__':main()
