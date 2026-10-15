"""Apply explicit root dispositions, never automatically approve Bedrock proposals.

This is a versioned editorial migration. Exact quote checks are necessary but
do not replace the responsibility/result decisions recorded below.
"""
import hashlib,json,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/definition-completion-20261004'
def read(p):return json.loads(p.read_text())
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def norm(t):return re.sub(r'\s+','',t)
reg=read(R/'research/source-store/operation-v12/catalogue/reference-registry.json');reg.update(read(R/'research/source-store/operation-v12/review/external-reference-disposition.json')['refs'])
proposals={}
for f in (P/'reviews').glob('*/*/proposal.json'):
 o=read(f);proposals[o['job_id']]=o
ledger=read(R/'data/operation-backbone-dispositions.json');products=read(R/'data/product-profiles-review.json');nav=read(R/'data/business-backbone-review.json')
assert ledger['new_version']=='WGSS-operation-v1.5-review-20261004','Migration already applied or wrong base'
by={w['id']:w for w in read(R/'dist/data/operations.json')['works']};profiles={p['id']:p for p in products['product_profiles']};decisions=[]
def proposal(job,pid):return next(d for d in proposals[job]['proposal']['definition_proposals'] if d['local_id']==pid)
def refs(job,pid):
 out=[]
 for s in proposal(job,pid)['source_proofs']:
  sid=s['source_id'];f=R/'research/source-store/products-20261004'/(sid+'.txt')
  content=f.read_text() if f.exists() else json.dumps(reg.get(sid,{}),ensure_ascii=False)
  assert norm(s['exact_quote']) in norm(content),(job,pid,sid,'quote mismatch')
  if sid in reg:
   x=reg[sid];ref={'id':sid,'name':x['name'],'url':x['source_url'],'locator':x['source_locator'],'source_snapshot_id':x.get('source_snapshot_id')}
  else:
   x=next(x for x in products['product_sources'] if x['id']==sid);ref={'id':'product-definition:'+sid,'name':x['title'],'url':x['url'],'locator':s['locator'],'source_snapshot_id':'product-definition:'+sid+':'+x['sha256'][:12]}
  ref.update(rationale=s['proof_scope'],context_requires_review=False);out.append(ref)
 return out
def decide(job,pid,decision,reason,ids=()):
 decisions.append({'job_id':job,'proposal_id':pid,'decision':decision,'reason':reason,'work_ids':list(ids),'automatic_adoption':False})
def edit(wid,fields,reason,job=None,pid=None):
 if job:fields['refs']=list({x['id']:x for x in by[wid]['refs']+refs(job,pid)}.values())
 fields.update(review_note=reason,definition_is_wgss_editorial=True,independent_human_review=False,mece_approved=False)
 ledger['edits'].append({'id':wid,'fields':fields,'reason':reason,'phase':'definition-completion-v16','model_proposal_adopted_after_source_check':bool(job)})
 if job:decide(job,pid,'corrected_edit',reason,[wid])
def add(job,pid,suffix,family,**overrides):
 d=proposal(job,pid);wid='WGSS-COMPLETION-'+suffix
 w={'id':wid,'title':d['title_ko'],'layer':'customer','category':{'accounts':'accounts-deposits','cards':'payments-cards','lending':'lending-trade'}[family],'actor_role':d['actor_role'],'actor_label':'이용자·권리자','object_key':d['object_key'],'outcome_key':d['outcome_key'],'outcome':d['outcome_key'].replace('_',' '),'discriminator':d['discriminator'],'definition':d['definition'],'includes':d['includes'],'excludes':d['excludes'],'boundary':{'related_ids':d['existing_work_ids'],'distinction':d['role_result_boundary']},'refs':refs(job,pid),'status':'edited','source_gaps':[],'input_ids':[],'origin_unit_id':'COMPLETION-'+suffix,'review_note':'원문과 기존 정의를 대조한 WGSS 편집 정의입니다. 전체 금융 MECE 승인이 아닙니다.','definition_is_wgss_editorial':True,'independent_human_review':False,'mece_approved':False,'aliases':[],'applicability_conditions':d['scope_conditions']}
 w.update(overrides);w['actor_label']={'customer':'이용자·권리자','institution':'금융기관 처리 담당자','support':'서비스 이용자 또는 지원 담당자'}[w['layer']]+' · '+w['actor_role'].replace('_',' ')
 w['review_note']='원문·기존 정의·독립 실패 결과를 대조한 WGSS 편집 정의입니다. 전체 금융 MECE 또는 금융사 UI 승인이 아닙니다.'
 ledger['additions'].append(w);nav['assignments'].append({'id':wid,'family_id':family,'ambiguous':False,'reason':w['boundary']['distinction']});decide(job,pid,'corrected_addition',w['boundary']['distinction'],[wid]);return wid
def step(profile,sid,ids,condition,gap=None,title=None):
 s=next(s for s in profiles[profile]['steps'] if s['id']==sid);s.update(work_ids=ids,gap=gap,mapping_note=condition)
 s.pop('review_candidate_ids',None)
 if title:s['title']=title
def extra(profile,sid,title,aliases,ids,condition,gap=None):
 assert sid not in {s['id'] for s in profiles[profile]['steps']};profiles[profile]['steps'].append({'id':sid,'title':title,'aliases':aliases,'work_ids':ids,'gap':gap,'mapping_note':condition})

# Cards: one contractual deferral, one institution carry-over, and two distinct
# authorities over ratios. Repaying a card debt reuses the existing debt unit.
card_contract=add('card-credit','P4','REVOLVING-AGREEMENT','cards',aliases=['리볼빙 약정 체결','일부결제금액이월약정 체결'])
card_min=add('card-credit','P5','MINIMUM-PAYMENT-RATIO','cards',layer='institution')
card_carry=add('card-credit','P6','STATEMENT-CARRYOVER','cards',layer='institution',includes=['미결제 잔여대금의 이월 잔액 확정'],definition='카드사가 이월약정과 실제 결제 결과에 따라 미결제 잔여대금을 다음 주기의 이월 잔액으로 확정한다. 약정 체결, 회원의 대금 납입, 수수료 계산과 별개의 결과다.')
card_end=add('card-credit','P7','REVOLVING-TERMINATION','cards')
step('payment-revolving','contract',[card_contract],'일부결제금액이월약정이 실제 성립하는 결과. 카드 발급·한도 승인과 분리합니다.')
step('payment-revolving','min-ratio',[card_min],'기관이 정하는 최소 비율입니다. 회원의 변경 입력으로 구현하지 않습니다.',title='카드사 최소결제비율 변경')
step('payment-revolving','close',[card_end],'약정 종료 후에도 잔여채무가 남을 수 있습니다. 카드 해지·상환 완료를 뜻하지 않습니다.')
step('payment-revolving','repay',['WGSS-860722E7067D'],'청구된 채무의 약정 납입 결과를 재사용합니다. 남은 금액의 이월은 별도 기관 결과입니다.')
step('credit-card','repay',['WGSS-860722E7067D'],'카드 청구대금 납입. 지급 수단, 결제일, 최소 납입 조건은 상품별 조건입니다.')
extra('payment-revolving','carryover','잔여대금 이월 확정',['이월','이월금액'],[card_carry],'회원 납입이 성공했더라도 이월 잔액 확정은 별도 처리 결과입니다.')
decide('card-credit','P9','rejected_duplicate','기존 약정 상환금 납입에 카드대금 원 후보가 이미 병합되어 있습니다. 카드라는 상품명으로 채무 납입 결과를 복제하지 않습니다.',['WGSS-860722E7067D'])
decide('card-credit','P8','needs_boundary_source','해지 후 전액 청구 권리는 확인했지만 모든 해지를 부도·기한이익상실과 동일시할 수 없습니다. 독립 청구 확정의 원자 경계를 추가 검토합니다.')
decide('card-credit','P1','needs_direct_function_source','사전 한도의 존재는 개인 이용가능금액 조회 기능의 직접 증거가 아닙니다. 한도 정보 객체와 조회 책임을 혼동하지 않습니다.')
decide('card-credit','P2','needs_direct_request_source','한도 이용 설명만으로 독립 인출요청 접수 기능을 확정하지 않습니다. 지급 집행과의 분리는 유지합니다.')
decide('card-credit','P3','conditional_reuse','인용된 분할상환 설명은 장기카드대출 설명입니다. 현금서비스의 회차·선결제 조건은 개별 단기 상품 원문이 필요합니다.',['WGSS-860722E7067D'])

# Savings: free contributions do not create an obligatory periodic debt.
saving_open=add('savings-accounts','P1','SAVINGS-AGREEMENT','accounts',actor_role='deposit_contract_counterparty',definition='예금주와 제공자가 기간 중 나누어 납입하는 적립식 예금계약을 성립시켜 납입·만기 원리금 반환 조건을 정한다. 회차 납입이 반드시 의무라는 뜻은 아니며 자유·정액 적립 조건을 따로 확인한다.',includes=['적립식 예금계약의 성립'],aliases=['적금 가입','적금 계약'])
saving_pay=add('savings-accounts','P2','SAVINGS-CONTRIBUTION','accounts',actor_role='deposit_contract_holder',outcome_key='make_contribution_to_installment_savings_contract',definition='적립식 예금 계약자가 납입금을 계약상 적립금으로 반영하여 보유 적립 원금을 증가시킨다. 자유적립은 의무 회차 상환으로 해석하지 않으며, 현금 입금·송금 지시는 납입의 수단과 구분한다.',includes=['계약상 적립 원금으로 납입 반영'],excludes=['대출 원리금 상환','송금 지시 제출만 완료한 상태','실물현금 입금 자체'],aliases=['적금 납입','적금 입금'])
saving_partial=add('savings-accounts','P3','DEPOSIT-PARTIAL-RETURN','accounts',actor_role='deposit_contract_holder',object_key='retained_term_deposit_contract_principal',outcome_key='receive_partial_principal_return_with_contract_retained',title='기간부 예금 일부 원금 반환',definition='기간부 예금 계약자가 계약을 유지하면서 예치 원금 일부를 반환받는다. 실물 현금 출금·전체 계약 중도해지와 구분하며 일부 반환 권리와 이자 적용은 상품 조건이다.',includes=['계약을 유지한 일부 원금 반환'],aliases=['적금 긴급출금','적금 일부 출금'])
edit('WGSS-3C1CDD682461',{'title':'기간부 예금 만기정산','object_key':'matured_time_bound_deposit','definition':'제공자가 만기에 도달한 기간부 예금의 원금과 확정 이자를 지급하여 만기 반환 채무를 이행한다. 거치식·적립식은 계약 조건이며, 자동 재가입 계약 성립은 별도 결과다.'},'거치식과 적립식의 만기 반환 결과를 중복 신설하지 않고 동일 책임·결과로 재사용합니다.','savings-accounts','P4')
edit('WGSS-12ABDDD6A417',{'title':'기간부 예금 중도해지','object_key':'time_bound_deposit_contract','definition':'예금 계약자가 만기 전에 기간부 예금계약을 종료시켜 원금·이자 반환 권리를 확정한다. 거치식·적립식의 차이는 적용 조건이며 일부 인출로 계약이 유지되는 결과와 구분한다.'},'적립식 중도해지 원문을 대조하여 계약 종료 결과의 범위를 보강했습니다.','savings-accounts','P5')
decide('savings-accounts','P6','rejected_duplicate','재예치로 새 계약이 성립하는 결과는 신규 예치 또는 적립 계약을 자동 재가입 조건으로 재사용합니다. 처리 주체만 바꿔 같은 계약 성립을 이중 계산하지 않습니다.',['WGSS-BEA6E0F20512',saving_open])
group_open=add('savings-accounts','P7','GROUP-SERVICE-REGISTRATION','accounts',actor_role='account_owner',definition='계좌 소유자가 기존 단독명의 예금계좌에 모임 관리 서비스를 등록하여 참여자·회비 조회 기능을 이용할 수 있게 한다. 기초 계좌 개설이나 공동명의 등록과 별개로 완료·실패할 수 있는 서비스 계약 결과다.')
group_end=add('savings-accounts','P9','GROUP-SERVICE-TERMINATION','accounts',actor_role='account_owner',definition='계좌 소유자가 기초 예금계좌에 연결된 모임 관리 서비스 계약을 종료한다. 기초 계좌 자체의 해지·잔액 지급과 구분하며 참여자·연결 카드의 선행 정리 조건은 제공자마다 확인한다.',includes=['모임 관리 서비스 종료'],applicability_conditions=['한국 공개 상품의 계좌 연계 서비스 종료를 근거로 합니다. 멤버 퇴장·연결 카드 조건을 전세계 공통 조건으로 적용하지 않습니다.'])
step('installment-savings','open',[saving_open],'적립 계약 성립. 목돈 거치식 예치와 구별하고 자유·정액 적립 조건을 확인합니다.')
step('installment-savings','pay',[saving_pay],'자유적립 납입은 의무 회차 상환이 아닙니다. 실제 적립 반영 결과를 확인합니다.')
step('installment-savings','maturity',['WGSS-3C1CDD682461'],'만기 원리금 반환. 자동 재가입을 선택했다면 새 적립 계약 성립도 별도로 확인합니다.')
step('installment-savings','close',['WGSS-12ABDDD6A417'],'전체 계약 중도 종료와 일부 인출은 다릅니다. 적용 이자 산출은 별도 계산 결과입니다.')
extra('installment-savings','partial-return','적금 일부 출금',['긴급출금','일부 출금'],[saving_partial],'계약이 유지되는 상품에서만 사용합니다. 지급 수단은 현금으로 고정하지 않습니다.')
step('group-account','open',[group_open],'단독명의 계좌에 서비스를 등록합니다. 공동명의 계좌 개설로 표시하지 않습니다.')
step('group-account','balance',['WGSS-FA9269F76FBE'],'조회자의 정보 접근권한을 확인합니다. 잔액 조회는 계좌 소유권을 이전하지 않습니다.')
step('group-account','invite',['WGSS-E3A2F4446585'],'참여자의 동의 후 정보 조회권한이 실제 부여되는 결과. 초대 링크 발송만 완료한 상태와 구분합니다.',gap='초대 발송·동의와 최종 조회권한 부여를 동일 완료 상태로 표시하지 않습니다.')
extra('group-account','close','모임 서비스 종료',['서비스 종료','해지'],[group_end],'멤버·카드 정리 조건을 확인하고 기초 계좌 해지와 분리합니다.')
step('fx-account','open',['WGSS-90894A4B1D44'],'외화보통예금의 통화·자격 조건으로 예금계좌 개설을 재사용합니다. 환전·송금을 자동 포함하지 않습니다.')
decide('savings-accounts','P8','conditional_reuse','정보 접근권한은 재사용하되 초대 발송만으로 권한 부여가 완료됐다고 추정하지 않습니다.',['WGSS-E3A2F4446585'])
decide('savings-accounts','P10','reuse','통화 종류로 계좌 개설 결과를 복제하지 않습니다.',['WGSS-90894A4B1D44'])
decide('savings-accounts','P11','needs_legal_scope','위법계약 해지 요구는 단순 해지와 다르지만 법정 권리의 적용 계약·시장 범위를 추가 원문과 대조해야 합니다.')

# Loan lifecycle: extension request is new; judgement and scheduled maturity
# repayment already exist. Do not invent a cardloan extension from another bank.
extension=add('loan-lifecycle','P1','LOAN-EXTENSION-REQUEST','lending',actor_role='borrower',object_key='existing_loan_term_extension_application',outcome_key='submit_term_extension_application',discriminator='existing_contract_not_initial_borrowing_application',aliases=['대출 연장 신청','대출 만기 연장'])
withdrawal=add('loan-lifecycle','P4','LOAN-COOLING-OFF','lending',title='대출계약 철회권 행사',actor_role='borrower',includes=['법정 철회 의사 행사 및 필요한 반환 조건 이행'],excludes=['일반 중도상환','보험계약 청약철회','대환으로 상환한 기존 계약을 자동 복원'],applicability_conditions=['한국 공개 대출상품에 적용되는 법정 숙려기간 철회권입니다. 계약·관할별 적용 권리와 완료 요건을 확인합니다.','대환 신규계약을 철회해도 이미 상환된 기존 계약이 복원되는 것은 아닙니다.'])
refi_confirm=add('loan-lifecycle','P5','REFINANCE-REPAYMENT-VERIFICATION','lending',layer='institution',actor_role='refinancing_lender',object_key='prior_loan_repayment_execution_result',outcome_key='verify_prior_loan_repayment_result',definition='대환을 제공하는 기관이 기존 대출의 실제 상환 결과를 확인하여 후속 대출 지급·유지 판단에 필요한 확인 결과를 만든다. 확인은 차주의 상환 이행이나 신규 지급 자체와 별개다.',includes=['기존 대출 상환 성공·실패 결과 확인'],excludes=['상환 이행 자체','신규 대출금 지급','확인 불가를 상환 실패로 단정'])
decide('loan-lifecycle','P2','rejected_duplicate','신규·갱신의 계약 상태는 심사 적용 조건입니다. 같은 인수심사 판정 책임을 별도 업무로 복제하지 않습니다.',['WGSS-1740AFFB2840'])
decide('loan-lifecycle','P3','rejected_duplicate','만기 일시상환도 약정 상환금 납입입니다. 완제 후 계약 종료·담보 반환을 자동 포함하지 않습니다.',['WGSS-860722E7067D'])
decide('loan-lifecycle','P6','rejected_duplicate','담보권 등록 말소는 담보 해지·반환 업무의 조건으로 대조하며 문구만으로 독립 업무를 추가하지 않습니다.',['WGSS-FBB0BA7E3E22'])
decide('loan-lifecycle','P7','needs_direct_request_source','기관 지급 정의와 수시 사용 가능성은 차주의 독립 인출요청 접수를 입증하지 않습니다.')
decide('loan-lifecycle','P8','conditional_reuse','보증 거절이 대출 진행을 막는 조건은 확인했습니다. 차주의 보증신청 화면이 항상 존재하는 것은 아닙니다.',['WGSS-246D8F3D02B8'])
for pid in ['overdraft','unsecured-loan','emergency-loan','guaranteed-loan']:
 step(pid,'renew',[extension,'WGSS-1740AFFB2840','WGSS-671FA819885C'],'연장 신청·심사 판정·약정 변경을 각각 구분합니다. 거절될 수 있으므로 신청 완료를 연장 완료로 표시하지 않습니다.')
for pid in ['overdraft','card-loan','unsecured-loan','mortgage','rent-loan','emergency-loan','secured-loan','guaranteed-loan']:
 step(pid,'close',['WGSS-860722E7067D','WGSS-B84D1142DF0C'],'만기 약정 납입과 기한 전 상환은 시점에 따라 선택합니다. 계약 종료·한도 소멸·담보 반환은 별도 결과입니다.',gap='잔액 상환과 계약 종료 확정은 다릅니다. 종료 책임·조건은 해당 상품 원문을 추가 확인합니다.',title='잔액 상환·계약 종료 확인')
step('overdraft','repay',['WGSS-B84D1142DF0C'],'만기 전 사용 원금 수시 상환. 가용 한도의 재사용 조건은 약정에서 확인하며 복원을 보장하지 않습니다.')
step('overdraft','interest',['WGSS-7DBD4CFD2150','WGSS-A2519AEF5C19'],'이미 발생한 이자 조회와 기관 이자 계산은 다른 역할·결과입니다.')
step('refinance','repay',['WGSS-B84D1142DF0C'],'기존 계약의 기한 전 채무 상환. 송금 지시·신규 지급만으로 상환 완료를 표시하지 않습니다.')
step('refinance','completion',[refi_confirm],'상환결과 확인이 불가한 상태와 실제 실패를 구분합니다. 상품별 신규계약 취소 조건을 확인합니다.')
extra('refinance','withdrawal','신규 대환계약 철회',['철회'],[withdrawal],'신규 계약 철회는 기존 대출 상환 취소가 아닙니다.')

# Credit agreement specialization does not add a second count.
edit('WGSS-CB2F5FE40642',{'title':'약정형 신용한도 계약 성립','layer':'customer','actor_role':'credit_facility_counterparty','status':'edited','boundary_review_required':False,'source_gaps':[],'definition':'차주와 제공자가 조건 충족 시 한도 내 자금을 사용할 수 있는 약정형 신용한도 계약을 성립시킨다. 계좌 연계 대월은 상품 조건이며, 기관의 여신한도 승인·고객의 실제 자금 사용·지급과 별개 결과다.','discriminator':'committed_access_under_agreement_conditions_not_uncommitted_offer','includes':['약정 조건부 자금 이용권 관계의 성립'],'excludes':['기관의 신용한도 승인만 완료','고객의 인출 요청 또는 실제 지급','거래·송금 한도 변경'],'applicability_conditions':['약정 조건 충족을 전제로 자금 제공 관계가 확인되는 경우에만 적용합니다. 재심사 생략·무조건 재사용을 보장하지 않습니다.']},'FIBO 약정 신용구조·BIAN 계약 및 공개 대월 약정을 대조했습니다. 계좌 연계 여부로 같은 계약 성립 결과를 중복 집계하지 않습니다.','credit-facility','P2')
ledger['merges'].append({'from':'WGSS-D8BBF2B1E899','into':'WGSS-CB2F5FE40642','reason':'계좌 연계 대월 약정은 약정형 신용한도 계약의 적용 조건입니다. 동일 계약 성립을 부모·상품 특수화로 이중 집계하지 않습니다.'})
nav['assignments']=[a for a in nav['assignments'] if a['id']!='WGSS-D8BBF2B1E899']
for g in nav['goals']:
 for key in ['canonical_work_ids','optional_work_ids']:g[key]=list(dict.fromkeys('WGSS-CB2F5FE40642' if x=='WGSS-D8BBF2B1E899' else x for x in g[key]))
step('overdraft','contract',['WGSS-CB2F5FE40642'],'계좌 연계 조건이 있는 약정형 신용한도 계약 성립. 한도 승인·사용·지급은 다른 결과입니다.')
step('credit-facility','contract',['WGSS-CB2F5FE40642'],'약정형일 때 적용합니다. 비약정형 한도나 사전 예상 한도는 동일한 자금 제공 약속으로 해석하지 않습니다.')
step('credit-facility','account-linked',['WGSS-CB2F5FE40642'],'계좌 연계가 있는 대월 약정의 조건으로 재사용합니다. 모든 신용한도에 해당하지 않습니다.')
decide('credit-facility','P1','corrected_merge','동일 약정 성립의 계좌 연계 특수화를 별도 업무로 유지하지 않습니다.',['WGSS-CB2F5FE40642'])
for pid,reason,ids in [('P3','독립 인출요청 접수의 직접 원문이 부족합니다.',[]),('P4','수시 상환은 기존 기한 전 잔존원금 상환의 조건입니다.',['WGSS-B84D1142DF0C']),('P5','재사용 가능성만으로 복원 확정이라는 독립 처리를 만들지 않습니다.',[]),('P6','금리 인하 요구 증거를 한도 변경 요청의 증거로 바꾸지 않습니다.',[]),('P7','연장 심사의 감액 조건만으로 모든 한도 변경 확정 책임을 입증하지 않습니다.',[]),('P8','다른 작업의 연장 신청 제안으로 합쳐 1회만 추가합니다.',[extension]),('P9A','기존 심사 판정 정의를 재사용합니다.',['WGSS-1740AFFB2840']),('P9B','위법계약 해지 요구를 일반 해지 신청으로 확장하지 않습니다.',[]),('P9C','해지 요구의 결과 통지에는 거절도 있으므로 계약 종료를 입증하지 않습니다.',[]),('P10','대출 생애주기 작업의 동일 철회권 제안으로 합칩니다.',[withdrawal])]:decide('credit-facility',pid,'corrected_reuse' if ids else 'needs_boundary_source',reason,ids)

# Account book transfer: execution responsibility derives from AccountEntry,
# while same-institution and customer-request assumptions are removed.
d=proposal('residual-definitions','P1-BOOKENTRY-SERVICER')
edit('WGSS-F92805EAE41E',{'title':'계좌 간 장부이체 실행','layer':'institution','actor_role':'account_servicer','definition':'계좌 기장 책임자가 두 계좌의 차변·대변을 반영하여 장부상 자금이동을 실행한다. 고객 요청 제출과 별개 기관 결과이며, 동일 기관이라는 제한이나 은행간 최종 결제 완료를 BookEntry 명사에서 추정하지 않는다.','includes':['두 계좌에 대한 자금 이동의 차변·대변 실행'],'excludes':['고객 지급지시 제출','결제용 자금 확보만 완료한 상태','실물 현금 입출금','기장 기록 생성만 완료한 상태'],'status':'edited','source_gaps':[],'boundary_review_required':False,'discriminator':'account_balance_transfer_execution_not_instruction_or_journal_document'},'ISO BookEntry의 자금이동 결과와 AccountEntry의 account servicer 장부 책임을 대조했습니다. 내부·동일 기관·고객 역할 가정을 제거했습니다.','residual-definitions','P1-BOOKENTRY-SERVICER')
for d in proposals['residual-definitions']['proposal']['definition_proposals']:
 if d['local_id']=='P1-BOOKENTRY-SERVICER':continue
 decide('residual-definitions',d['local_id'],'needs_direct_process_source','개념 객체·계약 당사자 정의만으로 신청 접수·조회 제공·지갑 개설 책임을 승인하지 않습니다. 증권 발행일과 실제 보장 개시는 다를 수 있어 자동 병합하지 않습니다.')

# Concrete fund result links, with primary/secondary market split retained.
step('mmf','settle',['WGSS-ADD-555BDFC74CD7'],'환매 주문 이행 결과. 지급 시점은 환매 유형별 조건이며 모든 증권거래 결제와 같다고 간주하지 않습니다.',title='환매대금 지급 확인')
step('etf','create',['WGSS-ADD-B059C7F3F94B','WGSS-ADD-F9EC19930F01','WGSS-ADD-D0A1ACA9428E','WGSS-ADD-555BDFC74CD7'],'발행시장의 지정참가회사(AP) 설정·해지 주문과 이행을 구분합니다. 일반투자자 거래소 매매주문에 자동 연결하지 않습니다.')
for d in proposals['securities-results']['proposal']['definition_proposals']:
 decide('securities-results',d['local_id'],'conditional_reuse' if d['local_id'] in ['P1','P2','P3','P4'] else 'needs_direct_process_source','MMF 환매·ETF 발행시장 결과는 기존 정의와 조건으로 연결합니다. 소매 RP·ELS·채권 원리금 지급은 메뉴명 또는 일반 개념만으로 책임을 승인하지 않습니다.',d['existing_work_ids'] if d['local_id'] in ['P1','P2','P3','P4'] else [])
for d in proposals['investment-wrappers']['proposal']['definition_proposals']:
 decide('investment-wrappers',d['local_id'],'needs_boundary_source','비교표의 상품명·자동매수·과세 조건은 확인했지만 자동운용 약정·처분 결과·세금 추징의 독립 책임 경계는 추가 계약·제도 원문과 대조해야 합니다. CMA를 요구불 예금 또는 RP를 펀드 환매로 자동 대응하지 않습니다.')

ledger['new_version']='WGSS-operation-v1.6-review-20261004';nav['version']='WGSS-backbone-v1.6-20261004';nav['operation_version']=ledger['new_version'];products['version']='WGSS-products-v1.6-20261004'
for p in products['product_profiles']:p['status']='partial' if any(s['gap'] or not s['work_ids'] for s in p['steps']) else 'registered_steps_linked'
report={'version':'WGSS-definition-completion-v16-20261004','input_version':'WGSS-operation-v1.5-review-20261004','output_version':ledger['new_version'],'root_adjudicated':True,'automatic_adoption':False,'independent_human_review':False,'global_mece_approved':False,'decisions':decisions,'completed_bedrock_jobs':list(proposals),'audit_note':'상품 탐색·원문 대조와 전체 금융 MECE 승인은 별도 검증입니다.'}
report['audit_note']='상품 탐색·원문 대조와 전체 금융 MECE 승인은 별도 검증입니다.'
write(R/'data/operation-backbone-dispositions.json',ledger);write(R/'data/business-backbone-review.json',nav);write(R/'data/product-profiles-review.json',products);write(R/'data/definition-completion-dispositions.json',report)
print(json.dumps({'explicit_dispositions':len(decisions),'additions':len([x for x in decisions if x['decision']=='corrected_addition']),'merge':'overdraft contract into committed facility'},ensure_ascii=False))
