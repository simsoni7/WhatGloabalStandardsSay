"""Root correction of semantic review, keeping explicit rejected mappings visible."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-priority-v27-20261012'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not (RUN/'root-final-candidates.json').exists();candidate=read(RUN/'root-candidates.json');rows=copy.deepcopy(candidate['examples']);by={b['id']:b for b in rows};src={prefix+':'+s['id']:s for prefix,name in [('V27','bank-priority-v27-20261012'),('F27','bank-kakao-faq-v27-20261012'),('X27','bank-kakao-faq-v27-extra-20261012'),('W27','bank-public-capture-v27-clean-final-20261012')] for s in read(R/'research/source-store'/name/'sources.json')}
 critic=read(next((RUN/'reviews/v27-evidence-steward').glob('*/proposal.json')))
 def pf(b,q):
  t=src[b['source_id']]['text'];at=t.index(q);return {'kind':'normalized_text_character_range','start':at,'end':at+len(q),'excerpt':q}
 def claim(b,desc,q):return {'description_ko':desc,'proof':pf(b,q)}
 b=by['BANK-BENCH-112'];t=src[b['source_id']]['text'];at=t.find('active');q=t[at:at+150];print('account qualifier',q[:100])
 # Exact native clause, with no inference from product-navigation text.
 q=next(x for x in ['active HSBC current account (excluding Basic Bank Account)'] if x in t)
 b['policy_claims'].append(claim(b,'활성 HSBC 당좌계좌 보유 필요, Basic Bank Account는 제외',q));b['conditions']=' '.join(x['description_ko'] for x in b['policy_claims'])
 b=by['BANK-BENCH-114'];b['meaning']='기존 정기지급 지시를 유지하는 변경 요청 접수 경로. 변경 확정·적용 시점은 이 자료에서 확인하지 못함';b['wgss_mapping_note']='분행의 변경 서식 제출·앱 채팅·전화 경로를 확인했습니다. 기존 지시를 그대로 유지하는 변경의 적용 시점은 미확인입니다. 앱·웹의 새 지시 등록 후 기존 지시 삭제는 대체 경로이며 동일 지시 변경 완료와 다릅니다.'
 b=by['BANK-BENCH-115'];q='請向您的受款人核實其用於登記戶口的姓名。然後您可透過香港滙豐流動理財應用程式的「管理預設指示」或滙豐網上理財的「查閱或刪除預設指示 」刪除現有的常行指示，並使用與銀行或「轉數快」參與者紀錄相符的受款人姓名設立新的常行指示。';b['function_proof']=pf(b,q);b['flow_steps']=['在 앱의 예정 지시 관리 또는 웹의 예정 지시 조회·삭제에서 기존 정기지급 지시 삭제'.removeprefix('在 ')];b['flow_step_proofs']=[pf(b,q)];b['wgss_mapping_note']='정기지급(常行指示) 삭제를 명시한 문답의 삭제 단계만 연결합니다. 단일 예약 이체 취소·실행된 이체 반환·직접출금 동의 철회가 아닙니다.'
 for id in ['BANK-BENCH-118','BANK-BENCH-119']:
  b=by[id];b['policy_claims'] += [claim(b,'법인사업자·공동대표는 영업점에서 발급 진행','법인사업자 및 공동대표의 경우 영업점에서 인증서 발급을 진행해 주시기 바랍니다.'),claim(b,'현재 로그인한 계정에 연결되며 다른 계정으로 발급하려면 그 계정으로 다시 로그인','현재 로그인 중인 계정으로 우리WON인증서(기업)가 발급됩니다.')];b['conditions']=' '.join(x['description_ko'] for x in b['policy_claims'])
 rejected={'BANK-BENCH-121':'배송 물류 상태·신청완료 메시지만으로 금융 발급 심사 상태 조회를 입증하지 않음','BANK-BENCH-130':'기존 이용 이력의 즐겨찾기 토글은 신규 수취인 정보·별칭의 등록 결과와 다름. 수취인 등록 사례로는 보류'}
 retained=[b for b in rows if b['id'] not in rejected];original={b['id']:b for b in candidate['examples']};changed=[{'id':b['id'],'before':original[b['id']],'after':b,'automatic_adoption':False} for b in rows if b!=original[b['id']]]
 dispositions=[{'id':b['id'],'root_decision':'reject' if b['id'] in rejected else 'retain_after_source_review','reason_ko':rejected.get(b['id'],'직접 결과·같은 금융상품의 근거 구간·채널 조건·제공자 신원을 확인'),'model_finding':next(x for x in critic['result']['rows'] if x['id']==b['id']),'automatic_adoption':False} for b in rows];write(RUN/'root-final-candidates.json',{'examples':retained,'row_dispositions':dispositions,'changed_rows':changed,'rejected_findings':candidate['rejected_findings'],'critic_run':{k:critic[k] for k in ['job_id','model','prompt_sha256','usage']},'automatic_adoption':False})
 job=read(RUN/'inputs/v27-evidence-steward.json');old={x['candidate']['id']:x for x in job['input']['rows']};compact=[]
 for b in retained:
  entry=copy.deepcopy(old[b['id']]);entry['candidate']=b;t=src[b['source_id']]['text'];qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']];entry['own_source_contexts']=[t[max(0,q['start']-150):min(len(t),q['end']+250)] for q in qs];compact.append(entry)
 job.update(id='v27-final-source-review',model='claude-sonnet-5',expected_ids=[b['id'] for b in retained],input={'rows':compact},max_tokens=15000);write(RUN/'inputs/v27-final-source-review.json',job);print({'retained':len(retained),'rejected':len(rejected),'corrected':len(changed)})
if __name__=='__main__':main()
