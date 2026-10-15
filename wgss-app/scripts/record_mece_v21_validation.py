"""Record reviewed actual deltas; technical checks are recorded separately."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/mece-closure-v21-20261011'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=read(R/'data/mece-closure-review.json');assert not p.get('v21_delta_review'),'Already recorded'
root=read(R/'data/mece-v21-root-dispositions.json');ids=set(root['added_work_ids']+root['edited_work_ids']);actual={}
for name in ['current-delta-v21-eight','current-delta-v21-source-fixes','quality-steward-v21-policy-qualified']:
    paths=list((RUN/'reviews'/name).glob('*/proposal.json'));assert len(paths)==1
    d=read(paths[0])
    for row in d['result']['rows']:
        assert row['decision']=='retain',(row['id'],row['decision'])
        actual[row['id']]=dict(id=row['id'],decision=row['decision'],job_id=d['job_id'],prompt_sha256=d['prompt_sha256'],reason=row['reason'],root_state='retained_after_source_and_counterexample_review',automatic_adoption=False,global_mece_approval=False)
assert set(actual)==ids and len(actual)==8
p['v21_delta_review']=dict(reviewed_rows=8,rows=list(actual.values()),snapshot_sha256=hashlib.sha256((RUN/'catalogue-policy-qualified.json').read_bytes()).hexdigest(),automatic_adoption=False,independent_human_review=False,global_mece_approved=False)
p['current_stage']='v21_delta_review_complete_regression_pending';write(R/'data/mece-closure-review.json',p)
observations=[]
for name in ['quality-steward-v21-actual-delta','quality-steward-v21-source-fixes','quality-steward-v21-policy-qualified']:
    d=read(next((RUN/'reviews'/name).glob('*/proposal.json')))
    for row in d['result']['rows']:
        changed=row['decision']!='retain'
        reason=('요청 신청과 계약상 일방권 행사 통지를 구분하고 직접 근거를 HSBC 신청 원문으로 제한했습니다.' if row['id'] in ['WGSS-9A4B541DD443','WGSS-9EAFFE368698'] else '지분권자 승인권과 펀드 운영 책임을 구분하고, 정의 본문에서도 의결은 적용 규칙이 요구하는 경우에만 필요하도록 교정했습니다.') if changed else '원문 조건과 실제 직접 결과를 보존했습니다. 전체 MECE 승인이 아닙니다.'
        observations.append(dict(id=row['id'],job_id=d['job_id'],prompt_sha256=d['prompt_sha256'],model_decision=row['decision'],root_state='accepted_and_current_definition_corrected' if changed else 'retained_after_qualified_review',reason=reason,automatic_adoption=False))
write(R/'data/quality-steward-v21-dispositions.json',dict(version='WGSS-quality-steward-v21-20261011',rows=observations,automatic_adoption=False,independent_human_review=False,global_mece_approved=False))
print(json.dumps({'current_unique_delta_rows':len(actual),'critique_observations':len(observations),'technical_validation':'pending'}))
