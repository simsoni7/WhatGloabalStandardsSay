"""Record root-accepted distinctions; preserve original model inputs unchanged."""
import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
ledger=read(R/'data/operation-backbone-dispositions.json');assert not ledger.get('v21_source_fixes_applied'),'Already applied'
by={w['id']:w for w in read(R/'dist/data/operations.json')['works']};existing={e['id']:e for e in ledger['edits']}
ids=['WGSS-9A4B541DD443','WGSS-9EAFFE368698','WGSS-MECE-FUND-POLICY-AMENDMENT']
for i in ids[:2]:
    w=by[i];e=existing[i]
    e['fields']['refs']=[r for r in w['refs'] if r['id']!='WGSS-PROCESS-SEC_LOAN_MATURITY_SELECTED']
    e['fields']['definition']=('약정 신용한도 보유자가 제공자의 판단·승인을 구하는 전부 해지 신청을 제출하는 결과. 직접 완료는 신청 제출이며, 이후 승인·이용권 종료·원리금 정산을 포함하지 않는다.' if i==ids[0] else '약정 신용한도 보유자가 제공자의 판단·승인을 구하는 한도 증액·감액 신청을 제출하는 결과. 직접 완료는 신청 제출이며, 이후 승인·약정 금액 변경·실제 자금 이용을 포함하지 않는다.')
    e['fields']['discriminator']='application_for_provider_decision_not_binding_exercise_of_contractual_option'
    e['fields']['includes']=[('계좌 연계 당좌대월 등 약정 신용한도의 전부 해지 신청 제출' if i==ids[0] else '계좌 연계 당좌대월 등 약정 신용한도 금액 변경 신청 제출')]
    e['fields']['excludes']=w['excludes']+['차주가 계약상 일방 종료·감액권을 행사하는 구속적 통지; 해당 유효 권리 변경 결과의 수행 조건으로 처리']
    e['fields']['applicability_conditions']=['HSBC 안내의 ask to increase, decrease or remove라는 요청 기능을 근거로 합니다. 특정 상품의 승인 결과·모든 신용한도의 요청 경로를 주장하지 않습니다.','제공자의 결정을 구하는 신청과 계약상 허용된 일방적 종료·감액권 행사 통지를 구분합니다. §2.9의 통지는 이 신청 행의 직접 기능 근거로 쓰지 않습니다.','신청 제출을 승인·권리 변경으로 표시하지 않습니다. 어떤 상품에 신청 방식이 적용되는지는 실제 계약·시장 조건을 확인해야 합니다.']
    e['reason']='HSBC 신청과 계약상 구속적 권리행사를 같은 제출 결과로 오인하지 않도록 의미 구분자를 교정했습니다.'
w=next(w for w in ledger['additions'] if w['id']==ids[2])
w['definition']='펀드의 권한 있는 운영주체가 기존 투자정책 변경안에 필요한 지분권자 의결 등 필수 승인을 받은 뒤 이를 반영하여 변경된 허용·배제 자산, 차입·집중 등 운용 규칙을 유효하게 확정하는 결과. 운영주체가 지분권자의 승인권을 대신 행사하는 것을 뜻하지 않으며, 의결은 해당 정책 변경의 효력 조건으로 보존한다.'
w['applicability_conditions']+=['미국법전 사례에서 지분권자는 필요한 변경을 승인하고 펀드의 권한 있는 운영주체는 그 승인에 따라 변경 정책을 반영합니다. 승인권자와 정책 적용 책임을 같은 사람으로 단정하지 않습니다.']
ledger['v21_source_fixes_applied']=True;write(R/'data/operation-backbone-dispositions.json',ledger)
write(R/'data/mece-v21-source-fixes.json',dict(version='WGSS-v21-source-fixes-20261011',work_ids=ids,root_decisions=[dict(id=i,state='accepted_scope_or_role_clarification',reason='구속적 통지와 승인 신청, 지분권자의 승인권과 펀드 운영 책임을 실제 결과로 구분합니다.') for i in ids],automatic_adoption=False,global_mece_approved=False))
print(json.dumps({'corrected_current_definitions':len(ids),'frozen_inputs_overwritten':False}))
