"""Explicit root decisions after the full source and candidate comparison.

This is a one-time reviewed migration, not automatic model adoption.
"""
import copy, hashlib, json
from run_mece_closure import ROOT, read, write
from prepare_mece_v18 import plain
RUN=ROOT/'research/source-store/mece-closure-20261006'
STORE=ROOT/'research/source-store/mece-closure-20261005/sources'
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
assert not ledger.get('v18_source_results_applied'), 'Already applied; do not rerun'
by={w['id']:w for w in read(ROOT/'dist/data/operations.json')['works']}
assert len(by)==365, 'Expected reviewed pre-result snapshot'
advice=read(RUN/'candidate-consolidation-advisory.json')['rows']
sources=read(RUN/'source-input.json')
sections={s['section_id']:s for r in sources for s in r['own_sections']}

def ref(sid, marker=None):
    if sid.startswith('BIAN:'):
        s=sections[sid];native=sid.split(':')[1]
        p=__import__('pathlib').Path(s['source_file'])
        assert hashlib.sha256(p.read_bytes()).hexdigest()==s['source_file_sha256']
        raw=json.JSONDecoder().raw_decode(p.read_text().split('var objectData =',1)[1].strip())[0]
        docs=[(n,c) for n,c in enumerate(raw[native]['data'][0]['categories']) if c['type']=='documentation']
        index,clause=docs[int(sid.rsplit(':',1)[1])]
        text=plain(clause['content']['value']);assert text==s['text']
        quote=marker or text[:180];assert quote in text
        return dict(id='BIAN:14.0.0:portal:'+native,name=s['name'],url=s['source_url'],
                    locator=f'objectData[{json.dumps(native)}].data[0].categories[{index}].content.value',
                    source_snapshot_id='BIAN-14-public-portal-2026-10-02',source_sha256=s['source_file_sha256'],
                    exact_quote=quote,context_requires_review=False,rationale='root가 직접 결과·역할·인접 정의와 대조한 기능 근거',
                    quote_normalisation='HTML text extraction using prepare_mece_v18.plain',
                    proof_scope='specified_financial_result_not_global_right_or_provider_ui')
    meta=read(STORE/(sid+'.json'));text=(STORE/meta['text_path']).read_text()
    assert hashlib.sha256((STORE/meta['raw_path']).read_bytes()).hexdigest()==meta['sha256']
    assert hashlib.sha256((STORE/meta['text_path']).read_bytes()).hexdigest()==meta['text_sha256']
    assert marker and marker in text
    return dict(id='WGSS-PROCESS-'+sid,name=sid,url=meta['url'],locator='selected operative text: '+marker[:70],
                source_snapshot_id='WGSS-primary-process-20261006',source_sha256=meta['sha256'],exact_quote=marker,
                context_requires_review=False,rationale='공식 절차의 직접 결과를 보존합니다. 적용 법역·계약 조건은 별도입니다.',
                proof_scope=meta['source_kind']+'_not_global_right_or_ui_capture')

new=[]
def add(suffix,title,category,role,obj,outcome,definition,includes,excludes,near,sids,conditions):
    i='WGSS-MECE-'+suffix
    w=dict(id=i,title=title,layer='institution',category=category,actor_role=role,
        actor_label='금융기관 처리 담당자 · '+role.replace('_',' '),object_key=obj,outcome_key=outcome,outcome=outcome.replace('_',' '),
        discriminator=None,definition=definition,includes=includes,excludes=excludes,
        boundary=dict(related_ids=near,distinction='직접 결과와 책임 범위를 기준으로 인접 업무를 구분하며, 상품·기관·지역 차이만으로 복제하지 않습니다.'),
        refs=[ref(*s) if isinstance(s,tuple) else ref(s) for s in sids],status='edited',
        review_note='v1.8 원문 전수 대조에서 발견된 결과를 root가 별도로 판정하여 검토 목록에 등록했습니다. 전역 MECE 승인은 아닙니다.',
        source_gaps=[],input_ids=[],origin_unit_id='MECE-V18-'+suffix,definition_is_wgss_editorial=True,
        independent_human_review=False,mece_approved=False,applicability_conditions=conditions)
    new.append(w);return i

incentive=add('INCENTIVE-EXPIRY','적립 인센티브 만료·몰취 확정','accounts-deposits','incentive_program_operator','accrued_incentive_value','expire_or_forfeit_accrued_incentive_value',
    '운영기관이 약관상 만료 또는 몰취 조건에 따라 적립 인센티브 가치를 소멸시키는 결과. 고객의 자발적 사용이나 적립 오류의 반전과 구분합니다.',
    ['기한·몰취 조건에 따른 적립가치 소멸'],['인센티브 적립','고객의 사용·상환 지시','오류 적립의 반전'],
    ['WGSS-2FE759473E85','WGSS-0C1020C84419'],[('BIAN:29328:doc:3','Handling expiration and forfeiture of accrued incentives')],['만료·몰취 조건 및 통지 의무는 실제 프로그램 약관에 따릅니다.'])
cash=add('CASH-INVENTORY-ALLOCATION','기관 현금재고 배분 결정','institution-processing','cash_inventory_allocation_authority','branch_atm_cash_inventory_allocation','determine_cash_inventory_allocation',
    '현금운영 책임자가 지점·창구·ATM에 유지할 현금 플로트와 중앙 보관시설 입출 배치를 결정·지시하는 결과. 중앙·지점 관점은 하나의 배분 결과로 집계합니다.',
    ['현금 플로트 배분·재배분 결정'],['현금 수송의 물류·배차','고객 현금 입출금 실행','고객 출금가능액 산출'],
    ['WGSS-5503FC0DA616','WGSS-1D3BAC32F1A8','WGSS-65B2C8AB2A4D'],['BIAN:29445:doc:0','BIAN:34826:doc:0','BIAN:39191:doc:0'],['배분 결정과 현금의 실제 인도·수송 완료를 동일시하지 않습니다.'])
master=add('MASTER-AGREEMENT-FORMATION','고객 마스터계약 성립','identity-support','master_agreement_counterparty','customer_master_agreement','establish_customer_master_legal_terms',
    '고객과 기관이 하위 상품약정에 앞서는 마스터 법적 조건을 합의하여 기준 계약관계를 성립시키는 결과.',
    ['고객 마스터계약의 최초 성립'],['계약문서 발급·교부','하위 상품계약 체결','기존 조건 변경','개별 제안행위의 계약 포함 여부 판정'],
    ['WGSS-84A417F867F9'],['BIAN:31459:doc:1','BIAN:31459:doc:2'],['기관이 마스터계약 구조를 사용하는 경우입니다. 모든 금융상품에 별도 마스터계약을 요구하지 않습니다.'])
report=add('BOND-TRUSTEE-REPORT','채권투자자 대상 수탁 재무보고','investments-custody','corporate_trust_agent','bond_investor_trustee_reporting_obligation','fulfil_financial_reporting_to_bond_investors',
    '기업신탁 대리인이 채권투자자를 대상으로 수탁 관계에 따른 재무보고를 수행하는 결과.',
    ['채권투자자 대상 재무보고 이행'],['개별 계좌 거래명세서','규제보고 제출','기업행위 이벤트 통지','조건부 에스크로 지급'],
    ['WGSS-B9195A767122','WGSS-079F6A97FFB4','WGSS-D078BF76895D'],[('BIAN:33293:doc:3','Administer financial reporting with bond investors')],['보고 내용·주기·수탁 책임은 실제 채무증서와 수탁약정에 따릅니다.'])
correspondent=add('CORRESPONDENT-RELATIONSHIP','코레스은행 서비스 관계 성립','institution-processing','correspondent_banking_counterparty','correspondent_bank_service_relationship','establish_correspondent_bank_service_relationship',
    '은행과 상대 은행이 국제 지급·무역금융 대행을 위한 코레스은행 서비스 관계를 성립시키는 결과.',
    ['코레스은행 서비스 관계의 최초 성립'],['상호 거래실적 추적·호혜성 평가','영업기회 발굴','타행 예금계좌 개설','하위수탁자 계약관리'],
    ['WGSS-A2CC3C808559','WGSS-90894A4B1D44'],['BIAN:34643:doc:1'],['제공 서비스와 책임 조건은 실제 은행 간 약정에 따릅니다. 관계 성립을 계좌 개설과 동일시하지 않습니다.'])
network=add('CARD-NETWORK-PARTICIPATION','카드망 참가기관 이용관계 성립','payments-cards','card_network_participation_counterparty','card_network_institution_participation','establish_issuer_acquirer_network_participation',
    '카드네트워크와 발급·매입 은행 사이에 네트워크 참가 이용조건과 이용관계가 성립하는 결과.',
    ['발급·매입 은행의 카드망 참가 등록'],['가맹점 수납계약','카드 발급','개별 카드거래 승인','카드망 정산지시','기존 참가조건·상태 변경'],
    ['WGSS-77D80A20399C','WGSS-DD4FB57556AA','WGSS-9E925F512EF7'],['BIAN:36870:doc:0','BIAN:36870:doc:1'],['네트워크별 참가조건을 실제 약정에서 확인합니다. 은행 가입과 가맹점 가입은 당사자·직접 권리 대상이 다릅니다.'])
treasury=add('BANK-TREASURY-POSITION','은행 통합 트레저리 포지션 산출','institution-processing','corporate_treasury_position_manager','consolidated_bank_treasury_position','produce_consolidated_bank_treasury_position_information',
    '트레저리가 거래내역·요약을 통합하여 은행 전체 유동성·자본 포지션과 만기래더·현금흐름 전망 정보를 산출·보고하는 결과.',
    ['은행 전체 트레저리 포지션 정보 산출','관련 만기래더·현금흐름 전망 산출'],['고객 재무포지션 제공','트레이딩계좌 포지션 통합','위험평가 판정','경제적 자본 요구액 산출','헤지 주문 제출·체결'],
    ['WGSS-7219DCE0C54F','WGSS-C1405A805E6A','WGSS-859BDADDD789','WGSS-70AA5703F3A4','WGSS-B051E356227D'],['BIAN:40508:doc:0','BIAN:46157:doc:0','BIAN:46157:doc:2'],['포지션 정보 자체와 한도 준수 판정·헤지 실행 결과를 구별합니다.'])
settlement=add('PAYMENT-RAIL-SETTLEMENT','지급레일 은행간 결제 완결','payments-cards','interbank_settlement_operator','payment_rail_interbank_settlement','complete_interbank_payment_rail_settlement',
    '결제운영자가 지급레일·결제기구를 통해 은행 간 결제를 완료하여 해당 레일 규칙에서 정한 결제 결과를 확정하는 업무.',
    ['결제기구를 통한 은행간 결제 완료'],['은행간 결제용 자금의 사전 확보','계좌 대조','메시지 변환·전송','카드망 정산지시 발행'],
    ['WGSS-96C318236155','WGSS-B704DE36E9CF','WGSS-DD4FB57556AA'],[('BIAN:47741:doc:3','Handle interbank settlement through Payment Authority'),('FEDWIRE_FINAL_SETTLEMENT','Fedwire Funds Service participants benefit from the finality of payments credited to their Federal Reserve Bank master accounts.')],
    ['Fedwire의 결제 최종성은 해당 미국 서비스의 공식 설명에 근거합니다. 다른 레일의 종국성·취소 가능 여부는 해당 규칙으로 확인합니다.'])
invoice=add('INVOICE-FINANCE-PAYMENT-REQUEST','송장금융 가용액 지급요청 제출','lending-trade','invoice_finance_facility_user','invoice_finance_payment_request','submit_invoice_finance_availability_payment_request',
    '송장금융 이용자가 기존 약정의 지급가능액을 고려하여 금액·지급방법을 지정하고 자금 지급요청을 제출하는 결과. 제출 시점의 Sent 상태는 실제 자금 지급 완료를 뜻하지 않습니다.',
    ['금액·지급방법을 포함한 지급요청 제출'],['대출 신용한도 인출요청의 법적 권리 추정','매출채권 매입 완료','실제 선지급 집행 완료'],
    ['WGSS-16DACF2B667D','WGSS-610BF7A63589','WGSS-DE4E23D3BB89'],[('NATWEST_INVOICE_PAYMENT_REQUEST','Its status will stay as Sent until it’s been processed by us.')],['NatWest FacFlow Invoice Discounting 지급요청 절차를 근거로 합니다. 송장할인을 모든 시장에서 담보대출로 간주하지 않습니다.'])

actions=[]
for w in new:
    ledger['additions'].append(w)
    actions.append(dict(work_id=w['id'],decision='added_review_definition',reason=w['review_note'],automatic_adoption=False))

# Actual clauses expose a contract-viewpoint duplicate that earlier reviews missed.
i='WGSS-6CA6BDD01105';text=(STORE/'IFSB27_RETAKAFUL.txt').read_text();at=text.index('Conventional reinsurance operates');quote=text[at:text.index('Other forms',at)].strip()
fields=dict(title='재보험계약 체결(위험 이전)',actor_role='reinsurance_contract_counterparty',object_key='reinsurance_risk_transfer_contract',
    outcome_key='establish_shared_reinsurance_risk_transfer_contract',discriminator='shared_contract_not_counterparty_viewpoint_or_underwriting_decision',
    definition='출재자와 재보험자가 보험위험의 전부 또는 일부를 보험료 대가로 이전하는 재보험계약을 성립시키는 결과. 출재·인수라는 양 당사자 관점은 같은 공유 계약 결과로 집계합니다.',
    includes=['출재자와 재보험자 사이의 위험이전 계약 성립'],excludes=['원수 보험계약 인수','계약 전 위험평가·인수조건 결정','리타카풀 상호보장 풀 출재(WGSS-3DFF635AF396)','재보험 회수금 청구·정산'],
    boundary=dict(related_ids=['WGSS-3DFF635AF396','WGSS-78CEC2469827','WGSS-273782CBD0C9'],distinction='양 계약 당사자가 공유하는 하나의 위험이전 계약 결과입니다. 인수심사 판단·손실 청구·풀 기반 위험공유는 별도 결과입니다.'),
    refs=by[i]['refs']+[ref('IFSB27_RETAKAFUL',quote)],review_note='원문과 공유 계약 집계 규칙에 따라 출재·인수 계약 관점 복제를 교정했습니다.')
ledger['edits'].append(dict(id=i,fields=fields,reason=fields['review_note'],phase='v18-explicit-root-result-review',automatic_adoption=False))
ledger['merges'].append(dict(**{'from':'WGSS-B0E67CF66BA2'},into=i,reason='같은 재보험 계약의 인수·출재 관점을 병합합니다. 독립 인수심사 결과의 책임 근거는 별도 후속 검토로 보존합니다.'))
actions += [dict(work_id=i,decision='corrected_edit',reason=fields['review_note'],automatic_adoption=False),dict(work_id='WGSS-B0E67CF66BA2',decision='merged',target_ids=[i],reason=ledger['merges'][-1]['reason'],automatic_adoption=False)]

i='WGSS-F4E90272B38B';refs=copy.deepcopy(by[i]['refs'])
for r in refs:r.update(context_requires_review=True,proof_scope='repo_domain_or_role_context_not_securities_loan_terms_process')
text=(STORE/'SEC_FILED_SECURITIES_LOAN.txt').read_text();at=text.index('The parties shall agree orally');quote=text[at:text.index('\n\nSection',at)].strip()
fields=dict(title='증권대차 거래조건 합의',object_key='securities_loan_terms_agreement',outcome_key='agree_individual_securities_loan_terms',
    definition='대여자와 차입자가 개시일·종목·수량·보상·담보 등 개별 증권대차 조건에 합의하는 결과. 조건 합의와 실제 증권·담보 이전, 인도 조건 충족 후 대차의 효력 발생을 구별합니다.',
    includes=['개별 증권대차 조건 합의'],excludes=['개별 거래조건 변경','증권·담보 실제 이전','대차 효력 발생 자체','레포 삼자거래 체결','대차계약 종료','일반 금전소비대차 계약'],
    discriminator='individual_loan_terms_agreement_not_delivery_or_loan_effectiveness',refs=refs+[ref('SEC_FILED_SECURITIES_LOAN',quote)],
    boundary=dict(related_ids=['WGSS-097C29210B88','WGSS-D490EDEAC5CD','WGSS-C6CD1A422A0E'],distinction='대차 조건의 합의와 실제 인도·반환은 독립 결과입니다. 현금 매매·재매입인 레포와 같은 계약으로 취급하지 않습니다.'),
    applicability_conditions=['SEC에 제출된 역사적 계약 Schedule 3 §1.1 및 §1.3을 근거로 합니다. §1.3은 증권과 담보 이전 전 Loan이 발생하지 않는다고 정합니다. SEC의 승인 또는 전 세계 의무조건을 뜻하지 않습니다.'],
    review_note='레포 중심 BIAN와 차입자 명사만으로 책임을 입증한 부분을 교정하고 실제 제출 계약의 조건 합의·효력 요건을 보존했습니다.')
ledger['edits'].append(dict(id=i,fields=fields,reason=fields['review_note'],phase='v18-explicit-root-result-review',automatic_adoption=False))
actions.append(dict(work_id=i,decision='corrected_edit',reason=fields['review_note'],automatic_adoption=False))

for r in ledger['input_mapping_overrides']:
    if r['input_id']=='institution-processing-consolidated treasury position-determine and hedge-51':
        r.update(work_ids=[treasury,'WGSS-B051E356227D'],state='corrected_source_relationship',reason='BIAN 40508·46157의 은행 전체 포지션 정보와 실제 거래 주문 개시를 독립 결과에 연결했습니다. 고객 정보나 위험판정으로 대체하지 않습니다.')
    elif r['input_id']=='lending-trade-invoice financing advance-draw-51':
        r.update(reason='원 입력은 실제 선지급을 뜻하며, NatWest는 지급요청 제출까지만 직접 입증합니다. 요청 업무는 별도로 등록하되 송장 담보대출 집행과 채권양도형 선지급의 실제 책임·구조 대조는 미해결로 유지합니다.')
ledger['v18_source_results_applied']=True
write(ROOT/'data/operation-backbone-dispositions.json',ledger)
progress=read(ROOT/'data/mece-closure-review.json');progress['root_decisions']+=actions
progress['technical_validation']=dict(state='pending',note='v1.8 결과 추가·계약 병합 후 회귀 대기')
progress['current_stage']='source_candidates_root_disposed_delta_review_pending'
progress['v18_result_actions']=actions
write(ROOT/'data/mece-closure-review.json',progress)

admitted={'ServiceDomain:29328#0':incentive,'ServiceDomain:29445#0':cash,'ServiceDomain:31459#0':master,'ServiceDomain:33293#0':report,'ServiceDomain:34643#0':correspondent,'ServiceDomain:36870#0':network,'ServiceDomain:40508#0':treasury,'ServiceDomain:47741#0':settlement}
excluded={'ServiceDomain:29306#0','ServiceDomain:31819#0','ServiceDomain:33829#0','ServiceDomain:44135#0'}
merged={'ServiceDomain:34826#0':'ServiceDomain:29445#0','ServiceDomain:39191#0':'ServiceDomain:29445#0','BusinessCapability:60759#0':'BusinessCapability:64188#0'}
pending_notes={
 'ServiceDomain:31108#0':'정책지침과 대형거래 승인은 두 결과입니다. 신용정책 후보와의 중복 및 기존 승인 업무와의 독립 책임을 각각 판정합니다.',
 'ServiceDomain:37849#0':'사업부 목표 미달 시정 예시를 법규 위반 해소로 단정한 모델 제안을 반려합니다. 재무성과와 법규준수 책임을 구분해야 합니다.',
 'ServiceDomain:44473#0':'샤리아 적격 운용지침은 일반 펀드의 법적 설정을 입증하지 않습니다. 기존 샤리아 정의의 무조건 일반화 제안을 반려합니다.',
 'ServiceDomain:48953#0':'원문에 NAV 가격 확정이 명시되지 않았습니다. 일반 평가가치와 다른 계약상 가격 결과가 있는지 직접 근거를 보강합니다.',
 'BusinessCapability:64533#0':'가상자산·연금에만 연결해 일반 증권 보관 수임을 덮은 것으로 처리한 제안을 반려합니다. 실제 미연결 범위를 별도로 정의해야 합니다.',
 'BusinessCapability:64436#0':'현재가치에 한정된 기존 정의를 미래 기준일·포트폴리오 범위까지 확장할 근거와 중복 여부를 판정합니다.',
}
rows=[]
for r in advice:
    i=r['id'];state='registered_result' if i in admitted else 'excluded_nonfinancial_context' if i in excluded else 'merged_hypothesis' if i in merged else 'pending_result_boundary'
    rows.append(dict(id=i,model_decision=r['decision'],root_decision=state,work_ids=[admitted[i]] if i in admitted else [],
        target_candidate_id=merged.get(i),reason=pending_notes.get(i,('독립 결과·책임과 실제 원문을 대조하여 좁힌 정의로 등록했습니다.' if i in admitted else '내부 기장·참조 데이터는 금융 권리·의무·정보의 독립 결과로 집계하지 않습니다.' if i in excluded else '같은 결과의 출처·중앙/지점 관점 복제를 합칩니다.' if i in merged else r.get('remaining_action') or '명시된 직접 결과를 인접 정의 및 실제 절차와 재대조합니다.')),
        evidence_section_ids=r['evidence_section_ids'],job_id=r['job_id'],prompt_sha256=r['prompt_sha256'],automatic_adoption=False))
write(ROOT/'data/mece-v18-result-dispositions.json',dict(version='WGSS-root-results-v18-20261006',rows=rows,actions=actions,
    separate_added_result_ids=[invoice],remaining_source_results=[
      dict(id='REINSURANCE-RISK-DECISION',title='재보험 인수심사 결과',reason='계약 관점 병합과 독립 위험판정 책임은 별개입니다. 실제 인수심사 책임의 원문 범위를 검토합니다.'),
      dict(id='TREASURY-RATE-PUBLICATION',title='전행 금리·환율 결정과 공표',reason='BIAN 46157의 전행 금리·환율 결과를 예금금리 한 항목으로 전부 덮을 수 없습니다.'),
      dict(id='MASTER-AGREEMENT-LIFECYCLE',title='마스터계약 변경·개별 활동 포함 판정',reason='최초 성립 외의 명시된 결과는 추가 분해 및 권한 만다트 후보와의 비교가 필요합니다.'),
      dict(id='CORRESPONDENT-RECIPROCITY',title='코레스은행 상호주의 평가',reason='관계 성립과 이후 호혜성 평가가 다른 결과인지 검토합니다.'),
      dict(id='NETWORK-PARTICIPATION-LIFECYCLE',title='카드망 참가기관 조건·상태 변경',reason='참가 등록 외의 변경·유지 행위를 독립 결과와 실행 단계로 구분합니다.'),
      dict(id='SECURITIES-LOAN-LIFECYCLE',title='증권대차 조건변경·효력개시',reason='조건 합의 이후 변경 및 실제 인도 조건 충족 결과의 기존 업무 포함 범위를 확인합니다.'),
    ],automatic_adoption=False,independent_human_review=False,global_mece_approved=False))

nav=read(ROOT/'data/business-backbone-review.json')
nav['assignments']=[a for a in nav['assignments'] if a['id']!='WGSS-B0E67CF66BA2']
families={incentive:'accounts',cash:'controls',master:'customer',report:'custody',correspondent:'controls',network:'cards',treasury:'controls',settlement:'payments',invoice:'lending'}
for i,f in families.items():nav['assignments'].append(dict(id=i,family_id=f,ambiguous=False,reason='원문 기반 독립 결과의 직접 대상에 따라 root 분류'))
for g in nav['goals']:
    for k in ['canonical_work_ids','optional_work_ids']:g[k]=list(dict.fromkeys('WGSS-6CA6BDD01105' if i=='WGSS-B0E67CF66BA2' else i for i in g[k]))
write(ROOT/'data/business-backbone-review.json',nav)
products=read(ROOT/'data/product-profiles-review.json')
for p in products['product_profiles']:
    for step in p['steps']:
        for k in ['work_ids','review_candidate_ids']:
            if k in step:step[k]=list(dict.fromkeys('WGSS-6CA6BDD01105' if i=='WGSS-B0E67CF66BA2' else i for i in step[k]))
write(ROOT/'data/product-profiles-review.json',products)
print('9 root-authored result definitions, 1 shared-contract merge, 2 edits; no global MECE approval')
