"""Explicit root decisions on additional Opus findings and source proofs."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/definition-completion-20261004'
def read(p):return json.loads(p.read_text())
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
f=next((P/'boundary-review').glob('*/proposal.json'));O=read(f)['proposal'];L=read(R/'data/operation-backbone-dispositions.json');D=read(R/'data/product-profiles-review.json');N=read(R/'data/business-backbone-review.json');Q=read(R/'data/definition-completion-dispositions.json');W={w['id']:w for w in read(R/'dist/data/operations.json')['works']};profiles={p['id']:p for p in D['product_profiles']}
assert not Q.get('boundary_review_decisions'),'Already applied'
sid='shinhan-revolving-guide';base=R/'research/source-store/products-20261004';raw=(base/(sid+'.html')).read_bytes()
D['product_sources'].append({'id':sid,'title':'신한카드 리볼빙 · 결제비율 안내','url':'https://www.shinhancard.com/pconts/html/finance/revolving/CONFM60032/CONFM60032R02.html','locator':'일부결제금액이월약정 안내 > 결제비율','checked_at':'2026-10-04','sha256':hashlib.sha256(raw).hexdigest(),'source_kind':'official_public_product_explanation','benchmark_admitted':False,'scope':'공개 안내의 결제비율 권한·조건 연구. 페이지의 예시 약정일·잔액은 실제 회원 화면으로 채택하지 않습니다.'});profiles['payment-revolving']['source_ids'].append(sid)
decisions=[]
norm=lambda t:re.sub(r'\s+','',t)
def add(cid,suffix,family,layer='customer',**changes):
 d=next(d for d in O['candidate_definitions'] if d['local_id']==cid);wid='WGSS-COMPLETION-'+suffix;refs=[]
 for p in d['source_proofs']:
  s=next(s for s in D['product_sources'] if s['id']==p['source_id']);text=(base/(s['id']+'.txt')).read_text();assert norm(p['exact_quote']) in norm(text),(cid,'quote mismatch')
  at=norm(text).index(norm(p['exact_quote']));refs.append({'id':'product-definition:'+s['id'],'name':s['title'],'url':s['url'],'locator':p['locator'],'rationale':p['proof_scope'],'source_snapshot_id':'product-definition:'+s['id']+':'+s['sha256'][:12],'context_requires_review':False})
 w={'id':wid,'title':d['title_ko'],'layer':layer,'category':{'customer':'identity-support','payments':'payments-cards','cards':'payments-cards'}[family],'actor_role':d['actor_role'],'actor_label':'이용자·권리자 · '+d['actor_role'].replace('_',' '),'object_key':d['object_key'],'outcome_key':d['outcome_key'],'outcome':d['outcome_key'].replace('_',' '),'discriminator':d['discriminator'],'definition':d['definition'],'includes':d['includes'],'excludes':d['excludes'],'boundary':{'related_ids':d['existing_work_ids'],'distinction':d['role_result_boundary']},'refs':refs,'status':'edited','source_gaps':[],'input_ids':[],'origin_unit_id':'COMPLETION-'+suffix,'review_note':'추가 Opus 반례 제안의 원문·기존 업무·권한 차이를 대조한 WGSS 편집 정의. 전체 금융 MECE·기업 UI 사례 승인 아님.','definition_is_wgss_editorial':True,'independent_human_review':False,'mece_approved':False,'aliases':[],'applicability_conditions':d['scope_conditions']};w.update(changes);L['additions'].append(w);N['assignments'].append({'id':wid,'family_id':family,'ambiguous':False,'reason':d['role_result_boundary']});decisions.append({'id':cid,'decision':'corrected_addition','work_ids':[wid],'reason':w['definition']});return wid
credit=add('C1','CREDIT-INFORMATION-LOOKUP','customer',definition='이용자가 본인 또는 적법한 조회권한을 가진 소유 사업장의 신용점수·거래 상세내역을 제공받아 확인한다. 신용평가사의 점수 산정·기관의 내부 신용등급 판정·개인 대출조건 조회와 다른 정보 결과다.',aliases=['내 신용정보','신용점수 조회','사업장 신용정보'])
prepaid=add('C2','PREPAID-ENROLLMENT','payments',actor_role='prepaid_service_counterparty',definition='이용자와 제공자가 선불전자지급수단 서비스의 이용관계를 성립시켜 해당 계약 조건에 따라 충전·사용할 수 있게 한다. 예금계좌 개설·일반 디지털 가입자 계정 생성·지급 카드 발급·충전 실행과 별개 결과다.',includes=['선불 지급수단 서비스 이용계약 성립'],applicability_conditions=['한국 공식 mini 상품의 선불전자지급수단 개설 설명을 근거로 합니다. 다른 국가의 전자화폐·선불서비스 동치와 권리를 자동 승인하지 않습니다.','인당 개설 수·보유한도·연령·동의·이자 제공 여부는 개별 상품 조건입니다.'])
refund=add('C3','PREPAID-REFUND','payments',definition='선불 지급수단 보유자가 해당 서비스의 환급 권리에 따라 선불 잔액의 금전가치를 반환받는다. 선불 서비스 종료·예금계좌 현금 출금·EU 전자화폐토큰 상환은 각각 대상과 적용 법역이 달라 자동 동일시하지 않는다.',includes=['선불 잔액 금전가치의 환급 수령'],applicability_conditions=['KR mini의 환급 설명을 근거로 합니다. 환급 가능 범위·수단·거래제한은 해당 선불 서비스의 계약·관할 조건을 확인합니다.'])
ratio=add('C7','MEMBER-PAYMENT-RATIO','cards',actor_role='revolving_cardholder',definition='이월약정 회원이 카드사가 정한 최소결제비율 이상의 허용 범위에서 자신의 약정결제비율을 변경하여 청구금액 산정에 쓰이는 선택 비율을 확정한다. 실제 적용 결제주기는 상품 조건이며 변경 성공만으로 당월 청구금액까지 변경되었다고 단정하지 않는다.')
def setstep(pid,sid,ids,note):
 s=next(s for s in profiles[pid]['steps'] if s['id']==sid);s.update(work_ids=ids,gap=None,mapping_note=note)
setstep('credit-information','information',[credit],'점수·상세내역 정보 조회. 점수 상승·내부 평가 산정·대출 조건 확정을 뜻하지 않습니다.')
setstep('prepaid-mini','open',[prepaid],'선불 서비스 이용계약 성립. 예금계약·일반 앱 가입·카드 발급은 별도 결과입니다.')
profiles['prepaid-mini']['aliases']=['mini','카카오뱅크 미니'];profiles['prepaid-mini']['steps'].append({'id':'refund','title':'선불 잔액 환급','aliases':['환급'],'work_ids':[refund],'gap':None,'mapping_note':'선불 잔액의 금전 반환. 서비스 종료와 환급 수령을 동일 완료 상태로 합치지 않습니다.'})
setstep('payment-revolving','ratio',[ratio],'회원이 선택하는 약정결제비율입니다. 카드사가 정하는 최소결제비율과 다릅니다. 적용 결제주기는 상품별 조건입니다.')
# Fix the contradictory editorial boundary, rather than introducing a clone.
a=next(a for a in L['additions'] if a['id']=='WGSS-COMPLETION-SAVINGS-CONTRIBUTION');a['boundary']['distinction']='고객의 계약상 적립 원금 증가와 이체 지시·기관 기장은 다른 책임·결과입니다. 자유적립은 납입 의무 이행으로 간주하지 않습니다.';a['discriminator']='contribution_to_deposit_contract_not_loan_repayment_or_transfer_instruction';a['applicability_conditions']=['자유·정액 적립의 의무성·납입 주기·최소 납입 조건은 계약별로 확인합니다.']
def edit(wid,fields,reason):L['edits'].append({'id':wid,'fields':fields,'reason':reason,'phase':'definition-completion-v16-boundary-review','model_proposal_adopted_after_source_check':True})
edit('WGSS-860722E7067D',{'title':'약정 채무상환금 납입','actor_role':'borrower','object_key':'credit_agreement_repayment_obligation','outcome_key':'pay_credit_agreement_amount_due','discriminator':'borrower_payment_not_creditor_collection_posting_or_acceleration','definition':'차주·신용이용자가 대출 또는 카드 신용약정에 따라 기일이 도래한 상환금을 납입하여 해당 금전 채무를 이행한다. 분할 납입·만기 일시상환·카드 청구대금은 계약 조건이다. 기관의 자동출금 처리·수납 기장·계약 종료는 별개 책임 결과다.','includes':['약정 회차 상환금 납입','약정 만기 원금·이자 납입','카드 신용약정의 청구 대금 납입'],'excludes':['기일 전 임의 원금 상환','기관의 상환금 수납·기장만 수행','기관의 채권 즉시상환 선언','증권 발행자의 원리금 배분·지급','계약 종료 또는 담보 반환'],'aliases':['약정 상환금 납입','만기 일시상환','카드대금 납입'],'refs':W['WGSS-860722E7067D']['refs']+[{'id':'product-definition:kakao-credit-correct','name':'카카오뱅크 신용대출 · 상환방법','url':'https://www.kakaobank.com/products/loanCredit','locator':'상환방법 > 만기일시상환 및 분할상환','rationale':'약정 상환 시점·방법의 결과를 대조하여 원문 합쳐진 입력 범위와 포함·제외의 충돌을 정정합니다.','source_snapshot_id':'product-definition:kakao-credit-correct:4ebbddf03431','context_requires_review':False}]},'원 입력의 카드·만기 상환 병합과 기존 정의의 분할상환 전용 문장이 충돌했습니다. 독립 계약 종료·기관 수납과 구분하며 고객 채무 납입이라는 직접 결과로 정정합니다.')
edit('WGSS-98A5154146C4',{'discriminator':'combined_cash_management_agreement_not_individual_account_or_service_enrollment','excludes':['개별 부가서비스 등록','개별 예금·투자계좌 계약 성립','연결 계좌끼리 자금 이동']},'결합형 현금관리 계약과 개별 계좌·서비스의 성립은 계약 대상이 다릅니다. 연결형 보관함이라는 이름만으로 결합 계약을 추가하지 않습니다.')
finding_reasons={
 'WGSS-COMPLETION-MINIMUM-PAYMENT-RATIO':('rejected_packet_limitation','원래 심사에 사용한 공개 약관 제37조에는 연체 등 신용상태 악화 시 최소결제비율 상향 권한이 명시돼 있습니다. 반례 패킷에 본문이 없다는 이유로 입증된 상향 결과를 제거하지 않습니다.'),
 'WGSS-COMPLETION-SAVINGS-CONTRIBUTION':('corrected','의무 이행을 되살린 경계 문구를 삭제했습니다. 자유적립은 의무 회차 상환이 아닙니다.'),
 'WGSS-COMPLETION-GROUP-SERVICE-TERMINATION':('rejected_product_mismatch','기록통장 섹션 종료와 모임통장 서비스 종료는 다른 직접 대상입니다. 계좌 유지 보편 권리를 주장하지 않고 해당 모임 서비스 종료 결과를 유지합니다.'),
 'WGSS-860722E7067D':('corrected_without_clone','고객 채무 납입과 기관 자동출금·수납을 분리해 문장을 정정했습니다. 카드라는 상품명만으로 동일 차주 납입을 복제하지 않습니다.'),
 'WGSS-98A5154146C4':('corrected','결합 계약과 개별 부가 계좌·서비스 성립의 경계를 명시했습니다.'),
 'WGSS-F92805EAE41E':('source_condition_retained','법적 계좌 두 개 사이의 이체만 실행 정의에 적용합니다. 같은 계좌 안의 기록 섹션 할당은 자동 포함하지 않습니다.')}
for x in O['changed_definition_findings']:
 decision,reason=finding_reasons[x['work_id']];decisions.append({'id':x['work_id'],'decision':decision,'reason':reason})
for cid,reason in [('C4','저금 목표·내부 잔액 구분이 독립 금융 권리·계약 결과를 만들었다는 직접 근거는 없습니다. 탐색 설정 단계로 보존하되 금융업무 총수를 늘리지 않습니다.'),('C5','기록 섹션은 계약 내부 관리 단위입니다. 금융 계좌 계약·자금이동 결과로 복제하지 않습니다.'),('C6','원문의 연결 계좌 자동 모으기는 기존 스윕 지시의 적용 조건으로 검토합니다. 실행 잔액 부족을 규칙 등록 실패와 혼동하지 않습니다.'),('C8','전자서명용 인증서 발급의 결과를 로그인 인증수단 바인딩과 같은 것으로 확정할 원문이 부족합니다. 발급 대상의 본인확인은 일부 과정의 증거입니다.')]:decisions.append({'id':cid,'decision':'needs_boundary_source' if cid in ['C4','C8'] else 'rejected_duplicate','reason':reason})
Q['boundary_review_decisions']=decisions;Q['boundary_prompt_sha256']=read(f)['prompt_sha256'];Q['boundary_tests']=O['boundary_tests']
for p in D['product_profiles']:p['status']='partial' if any(s['gap'] or not s['work_ids'] for s in p['steps']) else 'registered_steps_linked'
write(R/'data/operation-backbone-dispositions.json',L);write(R/'data/business-backbone-review.json',N);write(R/'data/product-profiles-review.json',D);write(R/'data/definition-completion-dispositions.json',Q);print(json.dumps({'source_checked_additions':4,'boundary_dispositions':len(decisions)},ensure_ascii=False))
