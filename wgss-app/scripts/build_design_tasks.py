"""Build author-reviewed task scaffolds; never ingest raw model responses."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist/data'
load=lambda p:json.loads(p.read_text())
definitions={c['id']:c for c in load(D/'cases.json')}
seeds=load(R/'research/v04-task-proposals.json')['tasks']
scope_copy={
 'arrangement':('앞으로의 반복 설정을 중단','출금 권한 또는 정기 송금 지시','각 회차의 지급을 누가 시작하나요?'),
 'occurrence':('이번 실행 한 건을 처리','식별 가능한 송금·지급 한 건','확인된 지급 유형과 처리 단계는 무엇인가요?'),
 'card_control':('한 카드의 이용 제한을 확인','계좌 전체 동결과 구분','사용자가 새로 요청하나요, 이미 기관이 제한했나요?'),
 'calculation':('예상 이자를 계산·설명','실제 기장·입금 결과와 구분','상품 약관에서 확인한 계산 방식은 무엇인가요?')
}
signals={
 'D03':('요금 청구 업체, 출금 동의, mandate','사용자가 은행에 반복 송금을 지시한 경우'),
 'S03':('정기 송금, standing order, 다음 실행일','업체에 출금 권한을 준 경우'),
 'T06':('개별 송금 식별자, 취소 가능 조건','출금 권한 또는 반복 설정 전체의 종료'),
 'C01':('사용자 요청, 일시 제한, 특정 카드','기관이 적용한 제한 또는 영구 차단'),
 'C04':('기관 제한 사유, 확인·문의 절차','사용자가 직접 설정한 임시 잠금'),
 'T03':('발송 단계가 확인된 동일 송금 한 건','수취 계정 반영까지 확인된 결과'),
 'T04':('수취 계정 반영과 계정 유형','completed라는 문자열만 확인한 경우'),
 'I01':('원금에만 이자를 계산하는 약관','연이율 표기만 있고 계산 방식은 모르는 경우'),
 'I02':('이자 재투입 약정과 복리 주기','예상액을 실제 지급 결과로 표시하는 경우')
}
tasks=[]
for seed in seeds:
 t={k:seed[k] for k in ('id','title','query','status')}
 t['why_this_task']=seed.get('why_this_task',seed['decision_question'])
 t['default_role']={'TRANSFER_RESULT':'result','INTEREST_PREVIEW':'detail'}.get(t['id'],'confirmation')
 t['scope_question']=seed['decision_question']
 t['unknown_help']='상태 변경 요청인지 결과·예상 조회인지 먼저 확인하고, 업무 객체와 실제 처리 신호를 찾아보세요. 표현만으로 상황을 확정하지 않습니다.'
 t['scopes']=[]
 for s in seed['scope_options']:
  label,description,question=scope_copy[s['value']]
  item={'id':s['value'],'label':label,'description':description,'route_question':question}
  if t['id']=='TRANSFER_RESULT':item.update(label='이번 송금 한 건의 상태',description='같은 거래의 발송·반영 시점을 확인',route_question='실제 확인한 송금 단계는 어디까지인가요?')
  if t['id']=='AUTOPAY_CANCEL' and s['value']=='occurrence':item['gap_warning']='개별 자동출금 중지·이의제기는 현재 정의 공백입니다. 개별 송금 취소 T06으로 분류하지 않습니다.'
  t['scopes'].append(item)
 t['definition_gaps']=[{'selector':g['when'],'reason':g['reason']} for g in seed.get('gaps',[]) if g['status']=='definition_gap']
 t['routes']=[]
 for x in seed['routes']:
  c=definitions[x['case_id']]
  assert x['selector']==c['selector'] and x['selector_ref']['version']==c['version']
  r={k:x[k] for k in ('case_id','target_scope','label','description','screen_goal','unsafe_claims','selector_ref')}
  r['selector']=dict(c['selector']);r['match_conditions']=x.get('extra_conditions',{})
  r['signal'],r['not_this']=signals[c['id']]
  r['templates']={};r['role_fields']={}
  for role in x['allowed_screen_roles']:
   role='detail' if role=='explanation' else role
   # T06 remains a cancellation-eligibility explanation until request phase is separately modeled.
   if c['id']=='T06' and role=='confirmation':continue
   r['templates'][role]={'title':x['draft_title'],'action':x['draft_action'],'body':x['screen_goal']}
   extra=x.get('recommendation_required_additions',[])
   r['role_fields'][role]=extra+(['status_signal'] if role=='result' else [])
  if c['id']=='T06':
   r['templates']['detail']['action']='취소 조건 확인';r['description']='개별 송금의 취소 가능성과 경로를 확인합니다. 취소 요청 접수·완료 결과는 별도로 확인합니다.'
   r['screen_goal']='현재 송금 단계에서 취소할 수 있는지 확인하고 필요한 경로를 안내'
   r['templates']['detail']['body']=r['screen_goal']
  if c['id'] in ('I01','I02') and 'rate_basis' not in r['role_fields']['detail']:r['role_fields']['detail'].append('rate_basis')
  t['routes'].append(r)
 tasks.append(t)
# Preserve the existing entry task; the other tasks are equally available in the picker.
tasks.sort(key=lambda t:0 if t['id']=='AUTOPAY_CANCEL' else 1)
(D/'design-tasks.json').write_text(json.dumps(tasks,ensure_ascii=False,indent=2)+'\n')
print(f'{len(tasks)} tasks; {sum(len(t["routes"]) for t in tasks)} routes')
