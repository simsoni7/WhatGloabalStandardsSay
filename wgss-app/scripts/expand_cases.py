"""WGSS UI situations mapped to, but never equated with, ISO business concepts."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist/data'
read=lambda n:json.loads((D/n).read_text())
def write(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
cases=[c for c in read('cases.json') if c['id'][0] in 'CTR'];new=[]
links=[]
def add(id,name,domain,definition,selector,inc,exc,fields,aliases,related,question,concepts,reason):
 new.append(dict(id=id,version='0.2.0',status='proposed',name=name,domain=domain,definition=definition,
  selector=selector,includes=inc.split('|'),excludes=exc.split('|'),critical_fields=fields.split(),
  aliases=aliases.split('|'),related=related.split(),disambiguation_question=question,
  definition_owner='WGSS',review_status='agent_checked',independent_review=False))
 links.append(dict(case_id=id,concept_names=concepts.split(),mapping_kind='wgss_application',
  rationale=reason,source_id='ISO-20260904',review_status='proposed',independent_review=False))
add('A01','계좌 개설을 신청할 때','계좌','사용자가 현금 계좌 개설 의사를 제출하는 상황. 신청 수락과 계좌 이용 가능 여부는 구분한다.',
 {'object':'cash_account','action':'apply'},'신규 계좌 신청 제출','계좌 이용 가능 통지|로그인 계정 가입',
 'eligibility identity_check opening_fee','계좌 개설|통장 만들기|open account','A02 A03','신청을 접수한 단계인가요, 사용할 계좌가 만들어졌나요?',
 'CashAccount AccountContract','계좌와 계약 개념을 신청 화면에 연결. 신청 절차·심사 기준은 WGSS 적용 조건이다.')
add('A02','새 계좌가 사용 가능해졌을 때','계좌','기관이 계좌가 개설되고 사용 가능하다고 확인한 상태를 알리는 상황.',
 {'object':'cash_account','action':'status','milestone':'active'},'개설 및 이용 가능 확인','신청만 접수|본인확인만 완료',
 'account_identifier permitted_actions activation_required','계좌 개설 완료|계좌 활성화|account ready','A01 A03','이체·입금 등 실제 사용 권한까지 확인됐나요?',
 'CashAccount AccountStatus','계좌의 상태를 UI 단계로 구체화. active는 WGSS 판정값이며 ISO 코드가 아니다.')
add('A03','계좌 해지를 요청할 때','계좌','사용자가 현금 계좌 계약 종료를 요청하는 상황. 요청만으로 해지를 확정하지 않는다.',
 {'object':'cash_account','action':'close'},'계좌 해지 신청','계좌 잠금|로그인 탈퇴|카드 해지',
 'remaining_balance pending_entries linked_services closure_effective_at','계좌 해지|통장 해지|close account','A01 A04','미결 거래와 잔액 처리 후 해지가 확정되는 시점은 언제인가요?',
 'CashAccount CashAccountContract','계좌 계약의 종료 요청을 WGSS 상황으로 정의한다.')
add('A04','계좌 해지가 확정됐을 때','계좌','기관이 특정 현금 계좌의 종료를 확인한 결과를 알리는 상황.',
 {'object':'cash_account','action':'status','milestone':'closed'},'계좌 종료 확인','해지 요청 접수|휴면 전환',
 'closure_effective_at remaining_balance statement_access','계좌 해지 완료|계좌 종료|account closed','A03','종료일과 남은 잔액의 처리 결과가 확인됐나요?',
 'CashAccount AccountStatus','종료 상태 표시는 WGSS 정의. 모든 시장의 해지 규칙을 표준화하지 않는다.')
add('A05','장부에 반영된 잔액을 볼 때','계좌','기장된 거래를 기준으로 산정한 잔액을 표시하는 상황. 즉시 사용 가능한 금액과 구분한다.',
 {'object':'cash_balance','action':'view','balance_basis':'booked'},'기장 기준 잔액 조회','출금 가능액|예상 미래 잔액',
 'balance_timestamp currency pending_included overdraft_included','장부 잔액|현재 잔액|booked balance','A06 A07 A08','기장 기준인가요, 지금 사용할 수 있는 금액인가요?',
 'CashBalance CashAccount','CashBalance를 잔액 산정 기준별 UI 상황으로 세분화한다.')
add('A06','지금 사용할 수 있는 금액을 볼 때','계좌','상품의 이용 가능 기준으로 산정된 금액을 표시하는 상황. 보류금·한도 포함 여부를 함께 확인한다.',
 {'object':'cash_balance','action':'view','balance_basis':'available'},'출금 또는 지급 가능액 조회','기장 잔액만 표시|카드 신용 한도',
 'balance_timestamp currency holds_included overdraft_included','출금 가능액|사용 가능 잔액|available balance','A05','보류 중인 금액이나 마이너스 한도가 포함됐나요?',
 'CashBalance CashAccount','이용 가능 기준은 기관별 적용 조건. CashBalance 정의와 UI의 available을 동일시하지 않는다.')
add('A07','입금이 거래내역에 기장됐을 때','계좌','조회 대상 계좌에 증가 방향의 거래가 기장됐음을 보여주는 상황.',
 {'object':'cash_entry','action':'view','entry_direction':'credit','entry_status':'booked'},'입금 기장 내역','입금 예정|다른 계좌로 발송|사용 가능액 보장',
 'booking_date value_date availability currency','입금 내역|입금 반영|credit entry','A05 A08 T04','어느 계좌에 기장됐고, 자금 사용 가능 시점은 별도로 확인했나요?',
 'CashEntry CashAccount CashBalance','CashEntry와 계좌·잔액 관계를 이용한다. 기장과 사용 가능성은 분리한다.')
add('A08','출금이 거래내역에 기장됐을 때','계좌','조회 대상 계좌에 감소 방향의 거래가 기장됐음을 보여주는 상황.',
 {'object':'cash_entry','action':'view','entry_direction':'debit','entry_status':'booked'},'출금 기장 내역','승인 보류|미래 예약 이체|수취인 입금 완료',
 'booking_date value_date currency reversal_possible','출금 내역|출금 반영|debit entry','A05 A07','출금 기장 사실인가요, 수취인에게 도착했다는 사실인가요?',
 'CashEntry CashAccount','출금 계좌에 대한 기장 사실만 분류한다.')
add('P01','송금 지시를 제출할 때','송금','지급 실행을 시작하기 위한 사용자 지시를 제출하는 상황.',
 {'object':'transfer','action':'initiate'},'수취인·금액을 정해 송금 제출','기관 처리 완료|수취 계좌 입금',
 'debtor_account creditor_details amount currency fees execution_date','송금 시작|돈 보내기|송금 요청|initiate payment','P02 T01','지시가 제출된 것인지, 자금 이동이 시작된 것인지 확인했나요?',
 'PaymentInitiation Payment CreditTransfer','최초 지급 지시 개념을 UI 제출 행위에 연결한다.')
add('P02','송금 실행을 승인할 때','송금','정해진 송금 지시의 실행에 동의하거나 승인하는 상황.',
 {'object':'transfer','action':'authorise'},'지급 지시 승인','단순 로그인 인증|송금 완료 확인',
 'authoriser approval_scope approval_expires_at amount','송금 승인|송금 확인|authorise payment','P01 T02','본인인증인가요, 이 특정 거래의 실행 승인을 의미하나요?',
 'PaymentInitiation PaymentExecution','승인 UI 단계는 WGSS 적용. 인증 성공을 지급 실행과 합치지 않는다.')
add('P03','송금 지시가 거절됐을 때','송금','해당 지급 지시를 처리하지 않겠다는 결과가 확인된 상황.',
 {'object':'transfer','action':'status','milestone':'rejected'},'기관의 처리 거절 결과','아직 처리 중|사용자 취소|출금액 반환 완료',
 'rejection_reason retry_allowed funds_debited refund_credit','송금 거절|송금 실패|payment rejected','P01 P04 T07','어느 단계의 거절이며 이미 출금한 돈이 있나요?',
 'PaymentStatus Payment','거절과 자금 반환을 분리한 WGSS 상태 정의.')
add('P04','원래 송금에 대한 반환 지급이 생겼을 때','송금','원래 지급과 연결된 반환 지급이 확인된 상황. 원래 지급의 취소나 상점 환불과 자동으로 같게 보지 않는다.',
 {'object':'transfer','action':'status','milestone':'return_payment_created'},'원 지급과 연결된 반환 지급','단순 취소 요청|상품 구매 환불 일반|반환액 입금 완료',
 'original_payment_id return_reason returned_amount return_credit','송금 반환|반환 송금|payment return','P03 T07 R01','원 지급과 연결된 새 반환 지급인가요, 단순 취소 상태인가요?',
 'Payment PaymentStatus','Payment의 OriginalPayment / ReturnPayment 관계를 근거로 반환을 별도 상황으로 둔다.')
add('D01','계좌 출금 동의를 등록할 때','출금 동의','채무자가 채권자에게 자신의 계좌를 출금할 권한을 부여하는 상황.',
 {'object':'direct_debit_mandate','action':'create'},'채권자 주도 출금 권한 설정','송금인이 정한 정기 이체|카드 정기결제',
 'creditor mandate_scope amount_limit frequency valid_period','자동이체 동의|자동출금 등록|출금 동의|direct debit mandate','D02 D03 S01','누가 지급을 시작하나요? 수취인이 출금하나요, 내가 반복 송금하나요?',
 'DirectDebitMandate Mandate DirectDebit','동의와 실제 출금은 서로 연결되지만 다른 개념이다.')
add('D02','출금 동의를 변경할 때','출금 동의','기존 출금 권한의 조건을 변경하는 상황.',
 {'object':'direct_debit_mandate','action':'amend'},'동의 한도·범위 변경','이미 실행된 출금 수정|정기 이체 금액 변경',
 'amendment_effective_at reauthorisation pending_collections','출금 동의 변경|자동출금 한도 변경|amend mandate','D01 D03','변경이 다음 청구부터 적용되나요? 재동의가 필요한가요?',
 'Mandate DirectDebitMandate','Mandate의 OriginalMandate / Amendment 연결을 UI 변경 상황에 적용한다.')
add('D03','출금 동의를 철회할 때','출금 동의','앞으로의 출금 권한을 철회하도록 요청하는 상황. 진행 중 지급의 취소는 별개다.',
 {'object':'direct_debit_mandate','action':'revoke'},'향후 출금 권한 철회','이미 출금한 돈 환불|정기 송금 지시 해지',
 'revocation_effective_at pending_collections creditor_notification','자동출금 해지|출금 동의 철회|cancel direct debit','D01 D04 S03','권한 철회가 진행 중인 청구에도 적용되나요?',
 'DirectDebitMandate Mandate','철회 절차와 효력 범위는 WGSS의 조건이며 ISO 공통 정책이 아니다.')
add('D04','동의에 따른 출금 건을 확인할 때','출금 동의','특정 채권자가 시작한 출금 지급의 진행 상태를 조회하는 상황.',
 {'object':'direct_debit','action':'status'},'개별 출금 지급의 상태 조회','출금 동의 상태만 조회|직접 송금 진행 상태',
 'mandate_reference collection_date collection_status amount dispute_window','자동출금 내역|자동이체 출금|direct debit collection','D01 D03 A08','동의 상태인가요, 이번에 실제로 청구된 출금 건의 상태인가요?',
 'DirectDebit DirectDebitMandate PaymentStatus','DirectDebit과 DirectDebitMandate 관계를 개별 지급 조회에 연결한다.')
add('S01','정기 송금 지시를 설정할 때','정기 이체','송금인이 권한을 갖고 정해진 주기에 반복 지급하도록 지시하는 상황.',
 {'object':'standing_order','action':'create'},'반복 송금 주기 설정','수취인 주도 자동출금|일회성 예약',
 'frequency first_execution last_execution insufficient_funds amount','정기 이체 등록|자동이체 설정|standing order','S02 S03 D01','반복 송금 지시인가요, 수취인에게 출금 권한을 주는 건가요?',
 'CashStandingOrder CreditTransfer CashAccount','반복 지시와 개별 CreditTransfer를 구분한다.')
add('S02','정기 송금 조건을 바꿀 때','정기 이체','기존 반복 지급 지시의 금액이나 주기 등을 변경하는 상황.',
 {'object':'standing_order','action':'amend'},'정기 송금 지시 변경','이미 실행한 이체 수정|출금 동의 변경',
 'amendment_effective_at next_execution cutoff_time amount','정기 이체 변경|자동이체 금액 변경','S01 S03','변경이 어느 회차부터 적용되나요?',
 'CashStandingOrder CreditTransfer','변경 효력과 마감 시간은 기관별 근거가 필요하다.')
add('S03','앞으로의 정기 송금을 중단할 때','정기 이체','반복 지급 지시를 종료해 향후 실행을 멈추도록 요청하는 상황.',
 {'object':'standing_order','action':'cancel'},'미래 회차의 반복 지시 종료','실행된 이체 회수|출금 동의 철회',
 'cancellation_effective_at next_execution pending_execution','정기 이체 해지|자동이체 해지|cancel standing order','S01 D03 T06','다가오는 회차까지 멈추나요, 이미 실행된 건은 남나요?',
 'CashStandingOrder CreditTransfer','지시 종료와 개별 지급 취소를 분리한다.')
add('F01','환전 예상 금액을 비교할 때','환전','제시된 환율·기준 통화로 예상 환전 금액을 확인하는 상황. 실행 결과로 확정하지 않는다.',
 {'object':'currency_exchange','action':'quote'},'환율 견적 조회','이미 실행한 환전 결과|수취인 입금 확인',
 'source_currency target_currency rate rate_direction quote_expiry fees','환전 견적|환율 조회|환전 예상 금액|exchange quote','F02','어느 통화 1단위 기준이며, 적용이 보장되는 만료 시간이 있나요?',
 'CurrencyExchange','통화·환율·견적 식별 정보를 UI 견적 단계에 활용한다.')
add('F02','환전을 실행하도록 요청할 때','환전','선택한 통화와 금액에 대해 환전 실행을 요청하는 상황.',
 {'object':'currency_exchange','action':'execute'},'환전 실행 동의 및 제출','견적만 보기|환전 결과 확정|해외 송금 도착',
 'source_currency target_currency applied_rate fees quote_expiry cancellation','환전하기|환전 실행|convert currency','F01 P01','견적 시점과 실행 시점의 환율이 같은 조건인가요?',
 'CurrencyExchange PaymentExecution','환전 정보와 지급 실행의 관계를 연결하되 환전과 해외송금을 동일시하지 않는다.')
add('I01','단리 기준의 예상 이자를 볼 때','이자','원금에 대한 단리 조건으로 산정한 예상 이자를 표시하는 상황.',
 {'object':'interest','action':'preview','calculation_method':'simple'},'단리 이자 예상액','복리|실제 지급 완료|연이율만으로 계산 방식 추정',
 'principal rate day_count_basis accrual_period tax rounding','단리|단리 이자|simple interest','I02 I03 I04','일수 계산 방식·세금·반올림 조건까지 확인됐나요?',
 'Interest InterestCalculation','계산 매개변수 개념을 적용. simple은 WGSS 판정값이며 ISO 코드로 주장하지 않는다.')
add('I02','복리 기준의 예상 이자를 볼 때','이자','이자가 원금에 더해지는 주기를 적용한 예상 이자를 표시하는 상황.',
 {'object':'interest','action':'preview','calculation_method':'compound'},'복리 예상액 계산','단리|이자 실제 수령|명목 연이율과 실효 수익률 동일시',
 'principal rate compounding_frequency day_count_basis tax rounding','복리|복리 이자|compound interest','I01 I03 I04','이자가 재투입되는 주기와 이율 표시 기준이 무엇인가요?',
 'Interest InterestCalculation','이자 계산 개념에 WGSS의 복리 비교 조건을 추가한다.')
add('I03','이자 납부를 요청할 때','이자','사용자가 이자 금액을 지급하도록 요청하는 상황. 원금 상환과 납부 완료는 별개다.',
 {'object':'interest','action':'pay'},'이자 납부 실행 요청','원금만 상환|이자 발생 내역|납부 완료',
 'interest_amount due_date debit_account fees principal_included','이자 내기|이자 납부|pay interest','I01 I02 L01','원금이 포함됐나요? 납부 기한과 출금 계좌가 확인됐나요?',
 'Interest Payment','이자라는 대가와 지급 업무를 연결한 WGSS 적용이다.')
add('I04','받을 이자가 계좌에 반영됐을 때','이자','수령할 이자가 실제 계좌에 기장됐다는 결과를 보여주는 상황.',
 {'object':'interest','action':'status','milestone':'credited'},'이자 입금 기장 확인','예상 이자|미지급 발생 이자|지급 예정 알림',
 'gross_interest tax net_interest booking_date availability','이자 받기|이자 입금|이자 수령','I01 I02 A07','세전 예상액인가요, 세후 실제 기장 금액인가요?',
 'Interest CashEntry','Interest와 CashEntry의 실제 관계를 기장 결과 화면에 연결한다.')
add('L01','약정에 따른 대출 상환을 요청할 때','대출·예금','정해진 상환 일정에 따라 대출 채무를 상환하도록 요청하는 상황.',
 {'object':'loan','action':'repay','repayment_scope':'scheduled'},'약정 회차 상환 요청','중도 상환|이자만 별도 납부|대출 승인',
 'principal_component interest_component due_date fees remaining_principal','대출 상환|대출 갚기|정기 상환','L02 I03','원금·이자 구성과 상환 후 잔액이 확인됐나요?',
 'Loan Payment','대출 채무 개념을 상환 요청에 적용. 현지 상환 정책은 ISO에서 추론하지 않는다.')
add('L02','대출을 약정보다 일찍 상환할 때','대출·예금','계약상 예정 시점 전에 원금 일부 또는 전부를 상환하도록 요청하는 상황.',
 {'object':'loan','action':'repay','repayment_scope':'early'},'중도 상환 요청','정기 회차 납부|상환 완료 확정',
 'partial_or_full prepayment_fee quote_validity remaining_principal interest_adjustment','중도 상환|조기 상환|early repayment','L01','일부 상환인가요, 전액 상환인가요? 수수료 견적의 유효기간은요?',
 'Loan Charges','대출과 비용을 화면 조건으로 연결. 연결 자체는 WGSS 해석이며 ISO 관계 추가가 아니다.')
add('L03','예금 약정의 만기일이 도래했을 때','대출·예금','예치 약정의 만기일이 도래했음을 알리는 상황. 자동 재예치와 지급 완료 여부는 별도 조건이다.',
 {'object':'deposit','action':'status','milestone':'matured'},'약정 만기 도래','만기 전 예고|만기금 지급 완료|자동 해지 보장',
 'maturity_date renewal_policy payout_destination principal_amount interest_amount','예금 만기|만기일 도래|deposit maturity','I04 A07','만기가 되면 재예치하나요, 지급하나요? 지급 결과도 확인됐나요?',
 'Deposit CashLoanDeposit Interest','예치 약정에 WGSS 만기 상태를 연결. 모든 예금에 같은 만기 정책을 적용하지 않는다.')
for c in cases:
 names=('PaymentCard' if c['id'].startswith('C') else 'Payment PaymentStatus PaymentExecution' if c['id'].startswith('T') else 'Payment PaymentStatus')
 rationale=('카드 개념과 관련된 WGSS 사용 상황. 잠금·분실 교체 정책이 ISO에 정의됐다는 뜻은 아니다.' if c['id'].startswith('C') else '업체의 송금 상태를 WGSS가 세분화. 특정 ISO 상태 코드와의 동치 매핑은 하지 않는다.' if c['id'].startswith('T') else '환불은 지급과 관련된 UI 상황. 원 지급과의 ReturnPayment 관계는 업체 근거 없이는 확정하지 않는다.')
 links.append(dict(case_id=c['id'],concept_names=names.split(),mapping_kind='contextual',rationale=rationale,source_id='ISO-20260904',review_status='proposed',independent_review=False))
allcases=cases+new;write('cases.json',allcases);write('case-concept-links.json',links)
fields=read('field-labels.json')
extra='eligibility:신청 자격|identity_check:본인확인 조건|opening_fee:개설 비용|account_identifier:계좌 식별자|permitted_actions:허용 기능|activation_required:추가 활성화 필요|remaining_balance:남은 잔액|pending_entries:미결 거래|linked_services:연결 서비스|closure_effective_at:해지 효력 시점|statement_access:해지 후 내역 조회|balance_timestamp:잔액 기준 시점|currency:통화|pending_included:미결 거래 포함|overdraft_included:대출 한도 포함|holds_included:보류금 반영|booking_date:기장일|value_date:가치일|availability:사용 가능 시점|reversal_possible:정정·반전 가능성|debtor_account:출금 계좌|creditor_details:수취인 정보|amount:금액|fees:수수료|execution_date:실행일|authoriser:승인 주체|approval_scope:승인 범위|approval_expires_at:승인 유효기간|rejection_reason:거절 사유|retry_allowed:재시도 가능성|funds_debited:출금 여부|original_payment_id:원 지급 식별자|return_reason:반환 사유|returned_amount:반환 금액|return_credit:반환액 입금 여부|creditor:출금 권한 수취인|mandate_scope:동의 범위|amount_limit:금액 한도|frequency:주기|valid_period:유효기간|amendment_effective_at:변경 효력 시점|reauthorisation:재동의 필요|pending_collections:진행 중 출금|revocation_effective_at:철회 효력 시점|creditor_notification:수취인 통지|mandate_reference:동의 참조|collection_date:출금일|collection_status:출금 진행 단계|dispute_window:이의제기 기간|first_execution:첫 실행일|last_execution:마지막 실행일|insufficient_funds:잔액 부족 처리|next_execution:다음 실행일|cutoff_time:처리 마감 시간|cancellation_effective_at:취소 효력 시점|pending_execution:진행 중 실행 건|source_currency:원 통화|target_currency:대상 통화|rate:이율·환율|rate_direction:환율 표시 방향|quote_expiry:견적 만료|applied_rate:적용 환율|cancellation:취소 조건|principal:원금|day_count_basis:일수 계산 기준|accrual_period:발생 기간|tax:세금|rounding:반올림|compounding_frequency:복리 주기|interest_amount:이자 금액|due_date:납부 기한|debit_account:출금 계좌|principal_included:원금 포함|gross_interest:세전 이자|net_interest:세후 이자|principal_component:원금 부분|interest_component:이자 부분|remaining_principal:남은 원금|partial_or_full:일부·전액 상환|prepayment_fee:중도 상환 수수료|quote_validity:견적 유효기간|interest_adjustment:이자 조정|maturity_date:만기일|renewal_policy:재예치 정책|payout_destination:지급 목적지|principal_amount:원금 금액'
fields.update(dict(x.split(':') for x in extra.split('|')));write('field-labels.json',fields)
m=read('manifest.json');model=read('business-model.json');m.update(version='0.2.0',case_count=len(allcases),definition_only_count=len(new),business_concept_count=len(model['concepts']),business_relation_count=len(model['relations']),iso_snapshot='20260904',scope=list(dict.fromkeys(c['domain'] for c in allcases)))
m['known_gaps'].append('새 28개 상황은 정의 후보만 제공; 금융사 문구 관찰 없음');write('manifest.json',m)
# Retain previous fixtures. B36 is intentionally migrated because loans enter scope in v0.2.
fixtures=[f for f in read('boundary-fixtures.json') if not f['id'].startswith('X')]
for f in fixtures:
 if f['id']=='B36':f.update(name='대출 상환 방식이 빠지면 구분 보류',expected_status='needs_context',reason='v0.2에서 상환을 추가. 약정 상환과 중도 상환을 구분할 정보가 필요하다.')
newtests=[
 ('장부 잔액을 사용 가능액으로 오인하지 않기',{'object':'cash_balance','action':'view','balance_basis':'booked'},'A05'),
 ('잔액이라는 말만 있으면 판정 보류',{'object':'cash_balance','action':'view'},None),
 ('자동이체 용어만으로 동의와 반복 지시 확정 금지',{'label':'자동이체'},None),
 ('출금 권한 철회',{'object':'direct_debit_mandate','action':'revoke'},'D03'),
 ('반복 지시 종료',{'object':'standing_order','action':'cancel'},'S03'),
 ('반환 지급 생성은 원 계좌 입금 완료가 아님',{'object':'transfer','action':'status','milestone':'return_payment_created'},'P04'),
 ('송금 지시는 입금 결과가 아님',{'object':'transfer','action':'initiate'},'P01'),
 ('환전 견적은 실행이 아님',{'object':'currency_exchange','action':'quote'},'F01'),
 ('연이율만 있으면 단리 복리 추론 금지',{'object':'interest','action':'preview','rate':'5%'},None),
 ('만기는 지급 완료가 아님',{'object':'deposit','action':'status','milestone':'matured'},'L03'),
 ('중도 상환은 정기 상환과 별도',{'object':'loan','action':'repay','repayment_scope':'early'},'L02'),
 ('신청 접수는 개설 완료가 아님',{'object':'cash_account','action':'apply'},'A01'),
]
for i,(name,facts,case) in enumerate(newtests,1):fixtures.append(dict(id=f'X{i:02}',name=name,facts=facts,expected_status='matched' if case else 'needs_context',expected_case=case,reason='WGSS 확장 경계 시험',origin='synthetic_boundary_fixture',author='same_agent_as_rules',independent_holdout=False))
write('boundary-fixtures.json',fixtures)
queries=json.loads((R/'tests/search-fixtures.json').read_text());queries=[q for q in queries if not q.get('v02')]
for q,ids in [('계좌 개설',['A01','A02']),('자동이체',['D01','S01']),('잔액',['A05','A06']),('단리',['I01']),('복리',['I02']),('환전',['F01','F02']),('예금 만기',['L03']),('대출 상환',['L01']),('송금 반환',['P04'])]:queries.append(dict(query=q,expected_contains=ids,v02=True))
(R/'tests/search-fixtures.json').write_text(json.dumps(queries,ensure_ascii=False,indent=2))
lines=['# WGSS 금융상황 정의 v0.2','', '모든 상황은 WGSS 정의 후보. ISO 인증 UI 문구가 아니다. 새 28개 상황의 업체 사례는 미수집.','']
for c in allcases:
 link=next(x for x in links if x['case_id']==c['id'])
 lines += [f"## {c['id']} {c['name']}",c['definition'],f"- ISO 연결: {', '.join(link['concept_names'])} ({link['mapping_kind']})",'- 연결 이유: '+link['rationale'],'- 포함: '+' / '.join(c['includes']),'- 제외: '+' / '.join(c['excludes']),'- 먼저 확인: '+c['disambiguation_question'],'- 필수 조건: '+' / '.join(fields[k] for k in c['critical_fields']),'']
(R/'docs/case-definitions.md').write_text('\n'.join(lines))
print(f'{len(allcases)} cases; {len(new)} definition-only additions; {len(links)} concept mappings')
