"""Freeze root corrections and rejections before final source-grounded critique."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-priority-v26-20261011'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 out=RUN/'root-final-candidates.json';assert not out.exists()
 candidates=read(RUN/'root-candidates.json');rows=copy.deepcopy(candidates['examples']);by={b['id']:b for b in rows};sources={p+':'+s['id']:s for p,run in [('V26',RUN),('V26S',R/'research/source-store/bank-priority-v26-supplement-20261011')] for s in read(run/'sources.json')}
 critique=read(next((RUN/'reviews/v26-evidence-steward').glob('*/proposal.json')))
 def pf(b,q,after=0):
  t=sources[b['source_id']]['text'];start=t.index(q,after);return {'kind':'normalized_text_character_range','start':start,'end':start+len(q),'excerpt':q}
 b=by['BANK-BENCH-093'];b['function_proof']=pf(b,'That’s it! You’re ready to use Monzo to spend, save and manage your money.');b['meaning']='앱의 정보 입력·신원확인·계좌 유형 선택을 거치는 개인 계좌 개설 안내. 신청만으로 즉시 승인·개설되는지는 보장하지 않음';b['wgss_mapping_note']='원문은 전체 가입 절차 끝에 계좌 이용 가능을 설명합니다. 계좌 유형 선택만을 개설 완료 근거로 삼지 않았습니다. 카드 수령·활성화는 별도의 후속 업무입니다.'
 b=by['BANK-BENCH-097'];t=sources[b['source_id']]['text'];at=t.index('How to catch up on missed payments with an Easy Bank Transfer');b['flow_step_proofs']=[pf(b,q['excerpt'],at) for q in b['flow_step_proofs']]
 b=by['BANK-BENCH-106'];b['function_proof']=pf(b,'收到扣賬卡後，您可以在HSBC HK App內輕鬆啟動扣賬卡：');at=sources[b['source_id']]['text'].index('如何透過HSBC HK App啟動我的滙豐Mastercard®扣賬卡？');b['flow_step_proofs']=[pf(b,q['excerpt'],at) for q in b['flow_step_proofs']]
 b=by['BANK-BENCH-107'];b['expression']='MDC';b['proof']=pf(b,'MDC');b['function_proof']=pf(b,'您亦可在香港滙豐流動理財應用程式、網上理財或致電我們查詢交易詳情。');b['expression_type']='공식 본문에서 설명한 거래 식별 표기 · 화면 메뉴 문구 미확인';b['meaning']='통합 계좌 거래내역에서 Mastercard 체크카드 거래를 MDC로 식별하는 방법';b['wgss_mapping_note']='앱·웹·전화 거래 상세 조회가 본문에 명시되어 있습니다. 구체 메뉴 경로는 미확인이고 MDC는 거래 식별 표기이며 조회 버튼명이 아닙니다.'
 b=by['BANK-BENCH-109'];first=b['screen_evidence'];second=b['additional_screen_evidence'][0];b['screen_evidence']=second;b['additional_screen_evidence']=[first];b['expression']='출금가능금액';b['expression_type']='공식 설명용 이미지에서 시각 확인한 출금 가능 금액 필드';b['function_proof'].update(bbox_xyxy=[385,518,640,558],coordinate_basis='original 1200x1423 image pixels');b['proof']=copy.deepcopy(b['function_proof']);b['meaning']='계좌 관리의 출금가능금액 필드와 통장 화면의 현재 잔액을 보여주는 공식 예시';b['conditions']='공식 설명용 이미지에서 출금가능금액을 시각 확인했습니다. 금액·계좌 정보는 예시입니다. 남은 월 입금 한도는 현재 잔액과 다릅니다.'
 b=by['BANK-BENCH-102'];b['additional_screen_evidence'][2]['labels']=['您的居住地址是']
 rejected={'BANK-BENCH-096':'월 상환 출금원 등록·설정을 납입 의무 이행으로 연결하지 않음. 개별 미납금 납부는 별도 097로 연결','BANK-BENCH-111':'증명서 발급 메뉴 진입만으로 발급·수령 결과를 입증하지 않음; 추가 근거 확보까지 보류'}
 retained=[b for b in rows if b['id'] not in rejected];changed=[]
 original={b['id']:b for b in candidates['examples']}
 for b in rows:
  if b!=original[b['id']]:changed.append({'id':b['id'],'before':original[b['id']],'after':b,'automatic_adoption':False})
 dispositions=[{'id':b['id'],'root_decision':'reject' if b['id'] in rejected else 'retain_after_source_review','reason_ko':rejected.get(b['id'],'고객 결과·동일 상품/예시의 원문 구간·조건·원본 안내 화면을 확인'),'model_finding':next(x for x in critique['result']['rows'] if x['id']==b['id']),'automatic_adoption':False} for b in rows]
 write(out,{'examples':retained,'row_dispositions':dispositions,'changed_rows':changed,'rejected_findings':candidates['rejected_findings'],'critic_run':{k:critique[k] for k in ['job_id','model','prompt_sha256','usage']},'automatic_adoption':False})
 base=read(RUN/'inputs/v26-evidence-steward.json');by_input={x['candidate']['id']:x for x in base['input']['rows']};compact=[]
 for b in retained:
  item=copy.deepcopy(by_input[b['id']]);item['candidate']=b
  t=sources[b['source_id']]['text'];qs=[q for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']] if q['kind']=='normalized_text_character_range'];item['own_source_contexts']=[t[max(0,q['start']-150):min(len(t),q['end']+220)] for q in qs];compact.append(item)
 base.update(id='v26-final-source-review',model='claude-sonnet-5',expected_ids=[b['id'] for b in retained],input={'rows':compact},max_tokens=13000);write(RUN/'inputs/v26-final-source-review.json',base)
 print(json.dumps({'root_retained':len(retained),'root_rejected':len(rejected),'root_corrected':len(changed)}))
if __name__=='__main__':main()
