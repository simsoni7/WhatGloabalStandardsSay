"""Record explicitly reviewed model dispositions and actual local checks."""
import json,collections,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/mece-closure-v20-20261011'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
progress=read(R/'data/mece-closure-review.json');assert not progress.get('v20_delta_review'),'Already recorded'
root=read(R/'data/mece-v20-root-dispositions.json');expected=set(root['added_work_ids']+root['edited_work_ids']);reviews={}
for name in ['current-delta-v20-01','current-delta-v20-02','current-delta-v20-03','current-delta-v20-fixes-grounded']:
 paths=list((RUN/'reviews'/name).glob('*/proposal.json'));assert len(paths)==1
 d=read(paths[0])
 for row in d['result']['rows']:reviews[row['id']]={'id':row['id'],'decision':row['decision'],'job_id':d['job_id'],'prompt_sha256':d['prompt_sha256'],'reason':row['reason'],'root_state':'retained_conditional_function_after_source_check','automatic_adoption':False,'global_mece_approval':False}
assert set(reviews)==expected and all(r['decision']=='retain' for r in reviews.values())
progress['v20_delta_review']=dict(reviewed_rows=len(reviews),rows=list(reviews.values()),automatic_adoption=False,independent_human_review=False,global_mece_approved=False)
steward=read(next((RUN/'reviews/quality-steward-v20-bounded').glob('*/proposal.json')))
root_states={
 'WGSS-MECE-FUND-SERIES-ESTABLISHMENT':('qualified_not_new_defect','시리즈 책임재산 설정과 투자정책 헌장은 직접 권리 대상이 다릅니다. 정책 원문 쟁점과 전체 CE는 미해결로 보존하며 이미 입증한 시리즈 설정을 그 이유로 제거하지 않습니다.'),
 'WGSS-MECE-FUND-NAV':('accepted_boundary_clarification','최종 판매수수료·환매비용 적용 거래가격을 제외에 추가했습니다. 기존 적용조건도 같은 차이를 명시했습니다. 수정된 현재 정의를 Opus로 다시 대조했습니다.'),
 'WGSS-MECE-MASTER-AGREEMENT-AMENDMENT':('qualified_scope_retained','합의형 마스터 변경의 기능 정의이며 ISDA의 서면 효력 조건을 모든 소매금융 일방 변경권으로 일반화하지 않습니다. 전체 마스터 종료·다른 변경 방식은 원문 추가 검토 그룹에 남겼습니다.'),
 'WGSS-DF3339F2234C':('rejected_context_as_function_inference','원문 문맥 참조는 이미 context_requires_review로 격리했습니다. 직접 기능 근거는 BIAN 36225의 목적에 따른 방법 선택·현재가치 산출입니다. 문맥만으로 특정 자산을 모두 검증했다고 주장하지 않습니다.'),
}
rows=[]
for row in steward['result']['rows']:
 state,reason=root_states.get(row['id'],('retained_after_counterexample_review','새 직접 결과 결함을 확인하지 않았습니다. 원문 조건·현재 목록의 MECE 미확정 상태를 유지합니다.'))
 rows.append(dict(id=row['id'],model_decision=row['decision'],root_state=state,reason=reason,automatic_adoption=False))
write(R/'data/quality-steward-v20-dispositions.json',dict(version='WGSS-quality-steward-v20-20261011',job_id=steward['job_id'],prompt_sha256=steward['prompt_sha256'],rows=rows,automatic_adoption=False,independent_human_review=False,global_mece_approved=False))
progress['current_stage']='v20_current_delta_and_regression_passed_source_and_scope_pending'
progress['technical_validation']=dict(state='passed',scope='current 394 definitions and affected search/navigation/browser flows only',product_queries=145,product_query_checks=159,product_browser_checks=122,management_browser_checks=23,mece_boundary_checks=32,independent_human_review=False,global_mece_approved=False)
write(R/'data/mece-closure-review.json',progress)
jobs=[read(p) for p in (RUN/'reviews').glob('*/*/proposal.json')]
print(json.dumps({'current_delta_rows':len(reviews),'paid_successful_jobs':len(jobs),'models':dict(collections.Counter(j['model'] for j in jobs))}))
