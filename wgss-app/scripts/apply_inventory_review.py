"""Apply root-reviewed official product variants, distinct from work approval."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/definition-completion-20261004'
def read(p):return json.loads(p.read_text())
def write(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
D=read(R/'data/product-profiles-review.json');V=read(R/'data/product-vocabulary-inventory.json');profiles={x['id']:x for x in D['product_profiles']}
assert not any(x.get('target_source_id') for x in V['items']),'Already applied'
def step(sid,title,aliases,ids,condition,gap=None):return {'id':sid,'title':title,'aliases':aliases,'work_ids':ids,'gap':gap,'mapping_note':condition}
def profile(pid,title,family,definition,steps):
 p={'id':pid,'title':title,'aliases':[],'family_id':family,'market':'KR','definition':definition,'features':[],'distinguish_from':[],'source_ids':[],'steps':steps,'status':'partial','review_note':'공식 상세 상품 설명을 대조한 탐색 경로. 업무 전체 MECE·해당 앱 화면 증거·법정 권리의 국제 동치 승인이 아닙니다.'};D['product_profiles'].append(p);profiles[pid]=p
profile('cash-pocket','연결계좌 저축 보관함','accounts','입출금통장에 연결하여 자금을 따로 보관하는 상품·서비스입니다. 보통예금 계좌와 하나의 계좌 안의 기록 섹션을 구분합니다.',[
 step('open','보관 예금계좌 개설',['개설','가입'],['WGSS-90894A4B1D44'],'보통예금의 법적 계좌 관계가 성립할 때 적용합니다. 단순 기록 섹션 생성에 적용하지 않습니다.'),
 step('transfer','연결계좌 자금 이동',['입금','출금'],['WGSS-DF4BF34CD9B3','WGSS-F92805EAE41E'],'이체 지시 제출과 기관의 실제 계좌 잔액 이동은 별개 결과입니다.'),
 step('interest','예금 이자 계산·지급',['이자'],['WGSS-0CD0BFA08772','WGSS-B540F7F22F8A'],'이자 요청·계산·지급을 구분합니다. 이자지급주기·단리·복리 효과는 상품별 조건입니다.'),
 step('close','보관 예금계좌 해지',['해지'],['WGSS-B0DA64D7BCB4'],'보관 예금계좌의 종료. 연결된 기초 통장까지 종료한다고 추정하지 않습니다.')])
profile('loan-comparison','대출·할부 조건 비교','lending','여러 제휴 금융사의 대출·할부 조건 정보를 조회·비교하는 서비스입니다. 비교 조회는 개별 계약 수락이나 대출 지급이 아닙니다.',[
 step('eligibility','개인 한도·금리 조건 비교',['한도조회','금리조회','비교','조회'],['WGSS-PRODUCT-LENDING-TERMS-LOOKUP'],'개인에게 제시된 조건일 때 적용합니다. 가심사·확정 조건 여부와 제휴사 변경 가능성을 확인합니다.'),
 step('apply','선택 금융사에 신청',['신청'],['WGSS-9EDE2FF3C6A4'],'선택한 금융사의 신청 제출 단계. 비교 플랫폼이 심사·계약·지급 주체라고 추정하지 않습니다.',gap='할부계약과 대출계약의 직접 채무 대상·신청 주체는 선택한 금융사의 상품에서 확인합니다.')])
profile('credit-information','개인·사업장 신용정보','customer','이용자가 본인 또는 소유 사업장의 신용점수·상세내역을 열람하는 서비스입니다. 신용평가 산정·여신 승인·대출 조건 조회와 다릅니다.',[
 step('information','신용정보 조회',['조회','점수','내역'],[],'개인과 사업장의 정보 조회는 대상·권한 조건으로 구분합니다.',gap='신용정보 조회자의 독립 정보 결과 정의를 원문과 기존 평가·조회 업무에 대조 중입니다.'),
 step('supplement','신용평가 자료 제출',['자료 제출','점수 올리기'],[],'평가 자료 제출은 점수 증가나 대출 승인 완료를 뜻하지 않습니다.',gap='자료 제출·평가 반영 책임과 독립 결과의 원문 대조가 필요합니다.')])
profile('business-certificate','사업자 전자서명 인증서','identity','개인사업자에게 발급하여 전자세금계산서·전자입찰·전자계약에 사용하는 민간 인증서입니다. 로그인 인증수단 등록과 전자서명용 인증서 발급은 구분합니다.',[
 step('apply','인증서 발급 신청',['발급','신청'],[],'사업자·대표자 자격과 인증서 이용 목적을 확인합니다.',gap='인증서 발급 신청·신원 확인·키 바인딩·증명서 발행의 독립 책임을 추가 대조해야 합니다.'),
 step('sign','인증서로 전자서명',['서명','전자계약'],[],'서명으로 어떤 거래·계약 의사를 확정하는지 별도로 선택합니다.',gap='전자서명 기술 동작만으로 세금계산서 발급·계약 성립의 금융 결과가 모두 완료됐다고 추정하지 않습니다.')])
profile('prepaid-mini','mini 선불 잔액 서비스','payments','카카오뱅크 mini는 선불전자지급수단입니다. 예금계좌·이자 적립 상품·디지털자산 지갑으로 분류하지 않습니다.',[
 step('open','선불 서비스 가입',['가입','개설'],[],'선불 가치 이용 관계의 성립을 예금계좌 개설과 구분합니다.',gap='선불 서비스 이용계약·잔액 원장의 책임 결과 정의를 원문에 대조 중입니다.'),
 step('balance','선불 보유 잔액 조회',['잔액'],['WGSS-FA9269F76FBE'],'선불 지급수단의 보유 잔액 정보입니다. 은행 예금·예금보험 관계를 주장하지 않습니다.'),
 step('charge','선불 잔액 충전',['충전','입금'],[],'충전 요청·금전 수취·선불가치 발행을 구분합니다.',gap='선불가치 발행·충전의 직접 책임 및 기존 전자화폐 개념과의 관할 경계를 추가 검토합니다.')])
profile('prepaid-mini-card','mini 선불카드','cards','mini 선불 잔액 범위에서 사용하는 지급 매체입니다. 체크카드·신용카드 계약과 한도 대출로 분류하지 않습니다.',[
 step('apply','선불카드 발급 신청',['신청','발급'],['WGSS-C05AAC60166E'],'지급 매체의 발급 신청 결과를 재사용합니다. 신용공여 신청을 포함하지 않습니다.'),
 step('issue','선불카드 매체 발급',['매체 발급'],['WGSS-8DCD86B339D1'],'기관의 지급 매체 발급 결과이며 신청 접수와 다릅니다.'),
 step('replace','선불카드 재발급',['재발급'],['WGSS-C28BA1C1D0B3'],'기존 지급 매체의 재발급. 선불 잔액 계정이 새로 생성되는 결과로 간주하지 않습니다.')])
profile('prepaid-saving-pocket','mini 잔액 모으기','payments','mini 잔액 안에서 금액을 따로 모으는 서비스입니다. 적금 계약·이자 지급 또는 별도 예금계좌 개설로 분류하지 않습니다.',[
 step('open','저금 서비스 설정',['개설','시작'],[],'자동저금과 직접저금의 규칙이 다릅니다.',gap='같은 선불 잔액 안의 할당·목표 설정이 독립 금융 결과인지 추가 원문으로 검토합니다.'),
 step('pay','선불 잔액 내부 저금',['저금','납입','입금'],[],'예금계약 납입이나 실물 현금 입금에 자동 연결하지 않습니다.',gap='같은 원장 안의 할당인지 별도 자금이동인지 확인 전 장부이체 실행으로 확정하지 않습니다.'),
 step('withdraw','모은 금액 사용 가능 상태로 반환',['출금'],[],'선불 잔액 안의 반환과 은행계좌로 지급되는 환급을 구분합니다.',gap='가용 잔액 복원과 실제 금전 환급의 직접 결과를 추가 대조해야 합니다.')])

# Explicit root mapping, selected from actual target bodies, not copied model
# related-work IDs. Numbers/fees/tax rates deliberately stay in the original.
mapping={
 '003':('demand-account','생계비 보호 특례가 있는 보통예금입니다. 보호범위와 입출금 제한은 한국 해당 상품 조건입니다.'),
 '004':('demand-account','미성년자 명의와 법정대리인의 가입·관리 권한을 구분합니다.'),
 '005':('cash-pocket','기록통장은 보통예금이며 기록 섹션은 계좌 내부 관리 단위입니다. 섹션마다 계좌를 개설했다고 세지 않습니다.'),
 '006':('cash-pocket','세이프박스는 연결 통장으로만 입출금하는 보통예금입니다. 실제 이자 지급과 복리 효과를 구분합니다.'),
 '007':('cash-pocket','저금통의 자동모으기 규칙과 연결 통장의 자금 이동을 구분합니다.'),
 '010':('installment-savings','적립식 예금계약입니다. 주차별 자동납입 규칙을 목돈 예치와 구분합니다.'),
 '011':('installment-savings','자유적립식 예금이며 직접 납입 방식입니다. 자동이체가 가능하다고 추정하지 않습니다.'),
 '012':('installment-savings','자녀 명의의 적립식 예금과 법정대리인의 관리 권한을 확인합니다.'),
 '013':('installment-savings','정부지원 연계 적금입니다. 은행의 적립계약과 지원기관의 기여금 지급 책임은 별도 검토 대상입니다.'),
 '018':('cash-pocket','외화통장에 연결한 외화 보통예금입니다. 통화 교환·외화통장 자체 개설과 구분합니다.'),
 '020':(None,'송금인의 요청 제출과 수취인의 입금 신청·기관의 입금 처리는 다른 결과입니다. 해외송금 수취 상세 책임 정의는 보강 중입니다.'),
 '024':('unsecured-loan','중고차 구매자금 대출입니다. 자금용도와 차량 소유권 이전에 따른 지급 조건을 확인합니다.'),
 '025':('loan-comparison','여러 금융사의 할부·대출 조건을 비교합니다. 비교 결과가 확정 계약·지급은 아닙니다.'),
 '027':('refinance','전월세보증금 대환입니다. 기존 대출 상환분과 임대인 지급분의 지급 목적·수취인을 구분합니다.'),
 '028':('mortgage','분양잔금 목적 주택담보대출입니다. 대상 주택·사용검사·담보 설정 조건을 확인합니다.'),
 '029':('mortgage','보금자리론의 은행 대출 결과와 공사에 대한 채권·담보권 양도 책임을 구분합니다.'),
 '031':('loan-comparison','주택담보 조건에 따른 제휴사 한도·금리 정보를 비교합니다. 담보 설정은 별도 결과입니다.'),
 '032':('refinance','주택담보대출 대환입니다. 기존 대출 상환·담보 말소와 신규 담보 설정을 별도로 확인합니다.'),
 '033':('loan-comparison','여러 종류의 신용대출 정보를 비교합니다. 조회와 신청·심사·계약을 구분합니다.'),
 '035':('credit-information','개인의 신용정보 열람입니다. 점수 산정 주체와 조회 제공 주체는 다릅니다.'),
 '036':('debit-card','입출금 계좌에 연결한 체크카드의 지급 매체 신청·발급 결과를 재사용합니다.'),
 '037':('debit-card','모임통장과 연결한 체크카드입니다. 멤버 참여가 계좌 공동명의를 뜻하지 않습니다.'),
 '038':('credit-card','제휴 신용카드를 소개·비교하는 경로입니다. 발급·심사·계약 주체는 해당 카드사입니다.'),
 '039':('credit-card','제휴 신용카드입니다. 앱 운영사와 카드 발급·대금 청구 기관을 구분합니다.'),
 '040':('demand-account','개인사업자 보통예금입니다. 개인·사업자 자격은 계좌 개설의 적용 조건입니다.'),
 '041':('cash-pocket','개인사업자 통장에 연결한 보통예금입니다. 세금용 자금 보관이 부가세 계산·신고·납부 완료를 뜻하지 않습니다.'),
 '042':('unsecured-loan','개인사업자 신용대출입니다. 사업자 자격·소득 심사와 신청·계약·지급을 구분합니다.'),
 '045':('refinance','개인사업자 대환입니다. 지원 대상 기존 대출의 계약 종류를 먼저 확인합니다.'),
 '046':('debit-card','개인사업자통장과 연결한 체크카드입니다. 업종별 혜택은 카드사의 개별 정책입니다.'),
 '047':('credit-information','본인 소유 사업장의 신용정보 조회입니다. 본인 신용정보와 권한·대상을 확인합니다.'),
 '048':('business-certificate','사업자 전자서명용 민간 인증서입니다. 인증수단 등록·인증·전자서명·금융 계약 성립을 한 업무로 합치지 않습니다.'),
 '049':('prepaid-mini','선불전자지급수단입니다. 예금계좌나 이자 적금으로 분류하지 않습니다.'),
 '050':('prepaid-mini-card','mini 보유 잔액 안에서 사용하는 지급 매체입니다. 후불 신용한도가 아닙니다.'),
 '051':('prepaid-saving-pocket','자동으로 mini 잔액을 모으는 서비스이며 금리를 제공하지 않습니다. 적금 계약과 구분합니다.'),
 '052':('prepaid-saving-pocket','mini 잔액 안에서 직접 모으는 서비스이며 금리·자동저금을 제공하지 않습니다.'),
 '061':(None,'보존한 대상 페이지는 계좌 개설 안내입니다. 해외주식 주문·통화·결제 조건의 직접 설명을 확보하지 못했습니다.'),
 '062':(None,'보존한 대상 페이지는 계좌 개설 안내입니다. 신용융자·주식대주·증권담보대출의 의미와 신청 책임을 구분할 상세 원문이 필요합니다.')}
inventory_decisions=[];variants=[]
for item in V['items']:
 if item['disposition']!='gap':continue
 pid,condition=mapping[item['id'].rsplit('-',1)[1]];m=read(P/'inventory-sources'/item['id']/'manifest.json');assert not m.get('error') and m['body_chars']>200
 item['mapping_conditions']=[condition];item['target_source_id']=m['source_id'];item['target_source_sha256']=m['sha256']
 if pid:
  sid=m['source_id'];source={'id':sid,'title':item['term']+' · 공식 상품 상세','url':m['final_url'],'locator':'공식 상세 본문 · 상품·서비스 안내 및 기타 유의사항','checked_at':m['checked_at'],'sha256':m['sha256'],'source_kind':'official_public_product_definition','benchmark_admitted':False,'scope':'한국의 해당 상품 의미·조건 연구. 실제 개인 앱 화면 또는 국제 동치 인증 아님.'};D['product_sources'].append(source)
  shutil.copyfile(P/'inventory-sources'/item['id']/'source.html',R/'research/source-store/products-20261004'/(sid+'.html'));shutil.copyfile(P/'inventory-sources'/item['id']/'source.txt',R/'research/source-store/products-20261004'/(sid+'.txt'))
  item.update(profile_ids=[pid],goal_ids=[],disposition='mapped',gap_reason=None);profiles[pid]['source_ids'].append(sid)
  variant={'inventory_id':item['id'],'term':item['term'],'source_id':sid,'conditions':[condition]};profiles[pid].setdefault('source_variants',[]).append(variant);variants.append(variant)
 else:item['gap_reason']=condition
 inventory_decisions.append({'inventory_id':item['id'],'decision':'mapped_navigation' if pid else 'direct_result_source_pending','profile_id':pid,'source_sha256':m['sha256'],'body_chars':m['body_chars'],'reason':condition,'financial_work_approved':False,'ui_benchmark_admitted':False})
V['version']='WGSS-product-vocabulary-v1.6-20261004'
report=read(R/'data/definition-completion-dispositions.json');report['inventory_decisions']=inventory_decisions
report['bedrock_calls']=[{'job_id':json.loads(f.read_text())['job_id'],'model':json.loads(f.read_text())['model'],'prompt_sha256':json.loads(f.read_text())['prompt_sha256'],'usage':json.loads(f.read_text())['usage']} for f in (P/'reviews').glob('*/*/proposal.json')]
for p in D['product_profiles']:p['source_ids']=list(dict.fromkeys(p['source_ids']))
write(R/'data/product-profiles-review.json',D);write(R/'data/product-vocabulary-inventory.json',V);write(R/'data/definition-completion-dispositions.json',report)
print(json.dumps({'reviewed_target_bodies':len(inventory_decisions),'mapped_navigation':sum(x['profile_id'] is not None for x in inventory_decisions),'remaining_source_gaps':sum(x['profile_id'] is None for x in inventory_decisions),'product_profiles':len(profiles),'actual_ui_benchmarks_added':0},ensure_ascii=False))
