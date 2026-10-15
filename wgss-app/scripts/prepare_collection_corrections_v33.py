"""Cold verification of concrete corrections, without stale advisory text."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/collection-root-v33-20261013';RUN=R/'research/source-store/collection-root-corrections-v33-20261013'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def proof(s,q):
 i=s['text'].index(q);return dict(kind='normalized_text_character_range',start=i,end=i+len(q),excerpt=q)
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists();c=read(SRC/'root-candidates.json');ss={b['prefix']+':'+s['id']:s for b in c['source_batches'] for s in read(R/b['manifest'])};reviews=[v for p in SRC.glob('reviews/*/*/proposal.json') for v in read(p)['result']['rows']];assert len(reviews)==len(c['examples']);needed={v['id'] for v in reviews if v['status']!='pass'};rows=[];ws={w['id']:w for w in read(R/'data/bank-ui-baseline-v32.json')['works']}
 for original in c['examples']:
  if original['id'] not in needed:continue
  b=copy.deepcopy(original);s=ss[b['source_id']];id=b['id']
  # Keep original proposals/reviews in their immutable folders, not in the cold prompt.
  for k in list(b):
   if 'critic' in k or k=='review_recommendation':b.pop(k)
  if id=='BANK-BENCH-314':b['meaning']='기존 법적 대리·법원 관리 문서를 은행이 확인하고, 해당 문서에서 허용하는 대리 방식과 권한 범위를 확인하여 은행 서비스에 등록하는 기능입니다. 새로운 법정 대리권 창설을 의미하지 않습니다.'
  if id=='BANK-BENCH-322':b['flow_steps'][0]='계약자가 보험기간·납입조건·보험가입금액 등 보장조건의 변경사항을 제시합니다.'
  if id=='BANK-BENCH-325':b['wgss_mapping_note']=b['wgss_mapping_note'].replace('2024.4','2024.5')
  if id=='BANK-BENCH-298':b['wgss_mapping_note']+=' 글로벌 영문 공식 문서에 기술된 영국 Bacs 기능입니다. 영국 현지 UI 노출·앱 버전은 확인하지 않았습니다.'
  if id=='BANK-BENCH-306':b['meaning']='수취인 가맹점이 받은 결제를 특정 청구서에 대조·적용하는 기능을 설명합니다. Public preview 상태이며 계정별 실제 노출·이용 자격과 영국 현지 UI는 별도 확인이 필요합니다. 실제 수납 대조 실행은 관찰하지 않았습니다.'
  if id=='BANK-BENCH-331':b['meaning']='공식 처리 안내는 납입 데이터와 자금 수령 확인부터 회원 계정에 부담금이 반영되는 처리 범위를 설명합니다. 펀드유닛 반영은 납입금 반영의 근거로 한정하며 회원의 투자배분 변경 지시와 구분합니다. 특정 고객의 실제 납입은 관찰하지 않았습니다.';b['wgss_mapping_note']+=' 펀드유닛 반영을 투자배분 선택·변경 업무로 해석하지 않습니다. 안내된 처리 역량의 조건부 결과입니다.'
  if id=='BANK-BENCH-334':
   b['meaning']='공식 상품 안내는 고객의 해외선물 거래 기능을 설명합니다. Power Futures의 전자거래 설명은 해외선물에 한정하고, Web Futures Trading의 조회 전용 기능과 구분합니다. 특정 계약의 실제 체결은 관찰하지 않았습니다.';b['context_ko']='홍콩 플랫폼 · 해외선물 전자거래 · 조회 전용 채널과 구분';b['channel']='공식 해외선물 거래 기능 안내 · 현재 거래 UI 미확인';b['conditions']='원문의 전자거래 시간표는 해외선물·뉴욕 시간 기준입니다. 다른 선물·옵션의 공통 시간표로 적용하지 않습니다. '+b['conditions']
  if id=='BANK-BENCH-335':
   b['flow_steps']=[];b['flow_step_proofs']=[];b['channel']='공식 옵션 거래 기능 설명 · 옵션 전용 주문 화면 채널 미확인';b['wgss_mapping_note']+=' 거래 기능의 문서 근거만 연결하며 Power Futures·Options Master를 옵션 주문 화면으로 특정하지 않습니다. 옵션 전용 조작 절차는 미확보입니다.'
  if id=='BANK-BENCH-344':
   q='We will start to provide our service to you from the start date. From that date, as long as you keep to the agreement we will pay a settlement equal to the value of the payments (less any refunds or chargebacks) included in transaction data you send to us.';b['function_proof']=proof(s,q);b['meaning']='영국 은행의 가맹점 수납 계약은 은행의 서면 발효일 통지와 고객 신청서 서명 중 늦은 시점을 시작일로 정하고, 그날부터 약정상 수납 서비스·정산 조건이 적용되는 구조를 설명합니다. 특정 고객의 가맹계좌·계약 완료는 관찰하지 않았습니다.';b['policy_claims'].append(dict(description_ko='계약 시작일부터 약정을 준수하는 가맹점에 수납 금액에서 환불·차지백을 제외한 정산 대금을 지급하는 구조입니다.',proof=proof(s,q)));b['conditions']=' '.join(p['description_ko'] for p in b['policy_claims'])
  rows.append(b)
 write(RUN/'root-candidates.json',dict(examples=rows,automatic_adoption=False))
 for i in range(0,len(rows),4):
  shard=rows[i:i+4];compact=[]
  for b in shard:
   t=ss[b['source_id']]['text'];qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[v['proof'] for v in b['policy_claims']];w=ws[b['ui_work_ids'][0]];compact.append(dict(candidate=b,actual_definition={k:w[k] for k in ['id','title','definition','completion','includes','excludes']},own_source_context=[t[max(0,q['start']-180):q['end']+270] for q in qs]))
  jid='v33-root-cold-'+str(i//4+1);write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model='claude-opus-5',instructions='JSON only {"rows":[{"id":...,"source_id":...,"work_id":...,"native_expression":...,"status":"pass"|"correct"|"reject","findings_ko":[...],"correction_ko":...}]}. COLD independent verification: no prior critique provided; assess actual provided candidate/definition/sourcequotes, not hypothesized oldannotations. Preserve binding. Same actor/directobject/intendedresult REQUIRED. Publisher-described legal/operational function qualifies without observing execution/currentUI/appversion. An example can cover ONE PERMITTED BRANCH/subtype of a work includes alternatives (e.g. insuredpersonchange but not initialregistration, cardtypecreditbutnotalltypes); do NOT require every includes alternative in everybenchmark. But subsetcannot omit necessarysamebranch conditions/effect. Agency registerexistinglegalpower and confirm its allowedmode/scope valid, no newlycreatedpower. Insurer agreedchange/endorsementconditionalrights valid, not just unappprovedrequest. Editional2024.5contract notcurrent2026UI. MPF contribution servicepledge startreceivedfunds tofundunitscredited can describeprocessingcapability subjectconditions; distinguish fundunitcredit from memberinvestmentallocationchoice. If trulyonlygenericSLA/capabilityinsufficient or legaleffectmissing, rejectwithconcretegap, notabsenceofactualcustomerstatement alone. Merchantcontractstartdate+operativebankservice/settlementresponsibilities may qualifyconditionalservicecontract formation; ordinarydepositaccount creation mustnotinferred. Futuresowntradingcapability with overseas-specific channels/hours distinctread-onlyweb. Optiontradingfunctiondocument says tradeanyfuturesoroptions, no option-exclusive navigation asserted; donotrequireinventedproceduretoqualifyfunctiondoc; ifactualsourceonlyanalytics/ordernotexecution thenreject. GlobalPSPdocs cannotbeBritishlocalUI; Publicpreviewaccounteligibilityunverifiedmustremain, receivedpaymentapplytospecifiedinvoice notactualobservedpaid. No guaranteedreturns/policiesnotexactbranch. No automaticadoption/globalMECE/humanreview. Correct onlyREALunsupportedclaim or provenance mismatch; pass properlyqualifiednativefunction.',input=dict(rows=compact),expected_ids=[b['id'] for b in shard],row_key='id',work_ids=list(ws),candidate_bindings={b['id']:dict(source_id=b['source_id'],work_id=b['ui_work_ids'][0],native_expression=b['expression']) for b in shard},max_tokens=11000))
 (RUN/'FROZEN').write_text('Source-grounded corrections and cold audits; original failures and reviews retained.\n');print({'cold_candidates':len(rows),'jobs':(len(rows)+3)//4})
