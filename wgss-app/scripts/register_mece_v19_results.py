"""One-time, explicit root migration. Never adopt Bedrock output automatically."""
import copy, hashlib, json
from pathlib import Path
from prepare_mece_v18 import plain
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research/source-store/mece-closure-20261011'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
assert not ledger.get('v19_results_applied'), 'Already applied; do not rerun'
before=read(RUN/'catalogue-before.json');by={w['id']:w for w in before['works']}
assert len(by)==373
sources=read(RUN/'source-input.json');source_by={r['reference_key']:r for r in sources}
sections={s['section_id']:s for r in sources for s in r['own_sections']}
advice={}
for p in sorted((RUN/'reviews').glob('closure*/*/proposal.json')):
    d=read(p)
    for r in d['result']['rows']: advice[r['id']]={**r,'job_id':d['job_id'],'prompt_sha256':d['prompt_sha256']}
assert len(advice)==22
def ref(sid,quote):
    if sid.startswith('BIAN:'):
        s=sections[sid];native=sid.split(':')[1];p=Path(s['source_file'])
        assert hashlib.sha256(p.read_bytes()).hexdigest()==s['source_file_sha256']
        raw=json.JSONDecoder().raw_decode(p.read_text().split('var objectData =',1)[1].strip())[0]
        docs=[(n,c) for n,c in enumerate(raw[native]['data'][0]['categories']) if c['type']=='documentation']
        n,c=docs[int(sid.rsplit(':',1)[1])];text=plain(c['content']['value']);assert quote in text
        return dict(id='BIAN:14.0.0:portal:'+native,name=s['name'],url=s['source_url'],
            locator=f'objectData["{native}"].data[0].categories[{n}].content.value',source_sha256=s['source_file_sha256'],
            source_snapshot_id='BIAN-14-public-portal-2026-10-02',exact_quote=quote,
            quote_normalisation='HTML text extraction using prepare_mece_v18.plain',context_requires_review=False,
            proof_scope='own_functional_clause_not_legal_duty_or_provider_ui',rationale='직접 결과와 책임을 root가 원문·현재 정의와 대조했습니다.')
    store=ROOT/'research/source-store'/('mece-closure-20261011/sources' if sid=='SEC_FILED_CUSTODY_FORM' else 'mece-closure-20261005/sources')
    meta=read(store/(sid+'.json'));text=(store/meta['text_path']).read_text();assert quote in text
    return dict(id='WGSS-PROCESS-'+sid,name=sid,url=meta['url'],locator='selected operative clause: '+quote[:65],
        source_snapshot_id='WGSS-primary-process-20261011',source_sha256=meta['sha256'],exact_quote=quote,
        source_store_relative=str(store.relative_to(ROOT)),context_requires_review=False,
        proof_scope=meta['source_kind']+'_not_global_right_or_ui_capture',rationale='제출 계약의 한정된 기능 근거입니다. 원문 추출 범위와 역사적 조건을 보존합니다.')
new=[]
def add(suffix,title,category,role,obj,outcome,definition,includes,excludes,near,evidence,conditions,family):
    i='WGSS-MECE-'+suffix
    w=dict(id=i,title=title,layer='institution',category=category,actor_role=role,
      actor_label='금융기관 처리 담당자 · '+role.replace('_',' '),object_key=obj,outcome_key=outcome,outcome=outcome.replace('_',' '),
      discriminator=None,definition=definition,includes=includes,excludes=excludes,
      boundary=dict(related_ids=near,distinction='직접 책임·대상·완료 결과로 구분합니다. 상품명·상대방 관점·상태 차이로 복제하지 않습니다.'),
      refs=[ref(*s) for s in evidence],status='edited',source_gaps=[],input_ids=[],origin_unit_id='MECE-CLOSURE-'+suffix,
      review_note='v1.9 root 원문·전체 정의 대조 후 등록했습니다. 전체 MECE 확정 또는 법적·독립 전문가 승인이 아닙니다.',
      definition_is_wgss_editorial=True,independent_human_review=False,mece_approved=False,applicability_conditions=conditions)
    new.append(w);return i,family
items=[]
items.append(add('SERVICING-ACTIVITY-AUTHORITY','외부 제공자 요청의 서비스 접근권한 판정','identity-support',
 'servicing_activity_authority_assessor','external_provider_requested_bank_service_access','determine_requested_service_access_within_existing_mandate',
 '은행이 외부 제공자의 실제 요청이 기존 서비싱 약정의 전체·고객별 은행 서비스 접근 허용 범위에 드는지 판정하는 결과.',
 ['요청 활동의 외부 제공자 접근권한 적합성 판정'],['외부 제공자 접근 약정 성립','신원 인증','채무자의 직접출금 추심 수권 유효성','지급지시 자금확보·집행'],
 ['WGSS-9EDEA2CB28B3','WGSS-B5B544940BAB','WGSS-AFF4499574AA'],
 [('BIAN:28808:doc:3','Check proposed activity is covered by the mandate')],
 ['서비싱 접근 약정이 존재하는 경우입니다. 채무자의 계좌 추심 허용권과 은행 서비스 접근권은 서로 다른 권한 제약입니다.'],'identity'))
items.append(add('MASTER-ACTIVITY-COVERAGE','제안 활동의 마스터계약 적용범위 판정','identity-support',
 'customer_agreement_coverage_assessor','proposed_activity_under_customer_master_terms','determine_proposed_activity_covered_by_master_agreement',
 '기관이 고객 마스터계약의 법적 조건을 기준으로 제안된 활동이 해당 계약의 적용 범위에 포함되는지 판정하는 결과.',
 ['제안된 활동과 고객 마스터계약의 적용범위 대조 판정'],['마스터계약 최초 성립·조건 변경','외부 제공자의 서비스 접근권한 판정','규제 준수 점검 자체'],
 ['WGSS-MECE-MASTER-AGREEMENT-FORMATION','WGSS-MECE-SERVICING-ACTIVITY-AUTHORITY','WGSS-19829603FDD5'],
 [('BIAN:31459:doc:3','Determine if proposed actions are covered by the agreement')],
 ['마스터계약을 사용하는 구조의 계약상 적용범위 판정입니다. 당사자 신원·접근권한·개별 지급 적격성을 동시에 승인하지 않습니다.'],'controls'))
items.append(add('ALM-POLICY-DIRECTIVE','자산·부채 관리 정책 지시 확정','institution-processing',
 'asset_liability_policy_authority','bank_asset_liability_policy_directive','issue_bank_asset_liability_policy_directive',
 '은행의 자산·부채 정책 책임자가 통합 포지션·손익·위험성향을 근거로 자산·부채 관리의 정책 지시를 확정·발행하는 결과.',
 ['자산·부채 정책 지시 발행·정비'],['통합 포지션 정보 산출','유동성·금리 위험평가 산출','개별 고객 신용한도 승인','초대형 거래 승인·거절','일반 기업 경영정책'],
 ['WGSS-MECE-BANK-TREASURY-POSITION','WGSS-859BDADDD789','WGSS-779616C3F2C3'],
 [('BIAN:31108:doc:0','defines and directs asset and liability policies'),('BIAN:31108:doc:3','Issue directives to remain in alignment with policies')],
 ['명시된 금융 자산·부채 정책을 대상으로 합니다. 법적 규제 충족 판정이나 일반 경영 전략 수립을 뜻하지 않습니다.'],'controls'))
items.append(add('LARGE-TRADE-APPROVAL','은행 자산·부채 관점의 초대형 거래 승인·거절','institution-processing',
 'asset_liability_large_transaction_authority','proposed_large_transaction_alm_impact','approve_or_reject_large_transaction_on_alm_impact',
 '자산·부채 관리 책임자가 제안된 초대형 거래의 은행 전체 포지션 영향을 검토하여 독립적인 승인·거절 결정을 확정하는 결과.',
 ['은행 전체 자산·부채 영향에 대한 초대형 거래 승인·거절'],['정책 지시 발행','고객 신용한도 승인','개별 대출 인수심사','지급지시 적격성 승인','실제 매매·지급 집행'],
 ['WGSS-779616C3F2C3','WGSS-1740AFFB2840','WGSS-AFF4499574AA','WGSS-MECE-ALM-POLICY-DIRECTIVE'],
 [('BIAN:31108:doc:3','Consider impact and approve/reject very large transactions')],
 ['BIAN의 ALM 독립 승인 기능입니다. 초대형의 금액 기준·승인 권한은 해당 기관 정책이며 보편적 법적 의무로 주장하지 않습니다.'],'controls'))
items.append(add('CREDIT-MARGIN-POLICY','신용·마진 의사결정 정책 지침 확정','institution-processing',
 'credit_margin_policy_authority','bank_credit_margin_decision_policy','determine_credit_margin_policy_directives',
 '은행의 신용·마진 정책 책임자가 기관의 위험·수익 성향을 반영하여 신용 의사결정을 규율하는 정책 지침을 결정·정비하는 결과.',
 ['기관 신용·마진 의사결정 정책 지침 확정'],['개별 고객 신용한도 승인','특정 고객 우대가격 적용','자산·부채 정책 지시','이미 정해진 정책에 따른 개별 승인'],
 ['WGSS-779616C3F2C3','WGSS-EED3EA86E4C5','WGSS-MECE-ALM-POLICY-DIRECTIVE'],
 [('BIAN:42913:doc:0','Determine and refine credit and margin directives and policies')],
 ['직접 대상은 신용 의사결정의 정책 제약입니다. ALM은 은행 자산·부채 구조의 지시이며 개별 고객 한도와도 대상이 다릅니다.'],'controls'))
items.append(add('TRADER-MANDATE','트레이딩 북 내 거래 책임·한도 배정','investments-custody',
 'trading_book_authority_administrator','individual_trader_trading_responsibility_and_constraints','assign_trader_trading_responsibility_and_limits',
 '트레이딩 북 책임자가 소속 트레이더에게 거래할 증권 포지션과 거래 책임·지침·한도를 배정하여 허용된 거래 책임 범위를 확정하는 결과.',
 ['트레이더별 거래 책임·포지션·제약 배정'],['고객 채널·상품 접근 권한 설정','거래상대방 신용한도 감시','일반 직원 직위 배정','블로터 기록·도구 제공 자체'],
 ['WGSS-5F8FC967D676','WGSS-5001E20F90A5','WGSS-779616C3F2C3'],
 [('BIAN:38568:doc:0','allocation of trading responsibilities and limits/constraints to individual traders')],
 ['기관 자체 거래 책임 배정입니다. 고객 권한·상대방 신용한도와 다른 직접 대상이며 실제 거래 집행은 별도입니다.'],'securities'))
items.append(add('FINANCIAL-PLAN','고객 재무계획 산출물 수립','identity-support',
 'financial_planning_provider','customer_financial_plan','produce_customer_financial_plan',
 '재무계획 제공자가 고객의 재무목표를 달성하기 위한 계획 산출물을 작성하여 고객 재무계획이 성립하는 정보 결과.',
 ['고객 재무계획 산출물 작성'],['재무목표 정의만 확정','특정 투자·세무 권고만 제공','기존 계획 효과성 판정','일임 운용지침 합의','실제 투자·지급 실행'],
 ['WGSS-MECE-FINANCIAL-GOAL','WGSS-1EF9D68BA7E7','WGSS-CLOSE-B834C8689F3C','WGSS-AF6645904647'],
 [('BIAN:64188:doc:0','Ability to create, monitor etc... a financial plan for a customer.')],
 ['BIAN이 명시한 계획 생성 기능에 한정합니다. 고객의 동의·계약상 구속력·계획 변경·종료 절차까지 입증하지 않습니다.'],'customer'))
items.append(add('SECURITIES-SAFEKEEPING-RECEIPT','증권 보관 인수','investments-custody',
 'securities_safekeeping_custodian','accepted_client_securities_for_safekeeping','assume_safekeeping_of_accepted_client_securities',
 '수탁자가 보관을 위해 인도·입고된 고객 증권을 수락하고 해당 증권에 대한 보관 책임을 인수하는 결과. 계좌 개설·장부 이동만으로 보관 수락을 추정하지 않습니다.',
 ['수락된 고객 증권의 보관 책임 인수'],['보관계좌 개설 자체','증권 입출고 기장만','신탁 자산의 법적 소유권 인수','가상자산 개인키 통제 수임','하위수탁자 계약 체결'],
 ['WGSS-D490EDEAC5CD','WGSS-C749D4C3757F','WGSS-A52E1501821C','WGSS-5F4112E4CDE1','WGSS-A2CC3C808559'],
 [('BIAN:64533:doc:0','Ability to receive financial instrument(s) for safekeeping'),('SEC_FILED_CUSTODY_FORM','The Custodian will hold Securities delivered or credited to its account under this Agreement directly or through accounts at Subcustodians or CSDs.'),('SEC_FILED_CUSTODY_FORM','the Custodian will only accept custody of Securities and other assets that it is operationally equipped and licensed to hold')],
 ['SEC 수록 State Street 2025 계약 양식 §3.1·§3.4의 역사적·한정된 기능 근거입니다. 효력일 공란이며 체결 사실·SEC 승인·전 세계 법적 의무·모든 금융상품 수탁을 입증하지 않습니다.','기관이 거절한 증권이나 수탁하지 않는 자산에 보관 책임 성립을 표시하지 않습니다.'],'custody'))
loanquote='which terms may be amended during the Loan upon mutual agreement of the parties.'
items.append(add('SECURITIES-LOAN-AMENDMENT','증권대차 개별 거래조건 변경 합의','investments-custody',
 'securities_loan_counterparty','in_force_individual_securities_loan_terms','amend_individual_securities_loan_terms_by_mutual_agreement',
 '대여자와 차입자가 대차 존속 중 개별 거래의 대여증권·보상·담보 등 조건 변경을 상호 합의하여 기존 거래조건을 변경하는 결과.',
 ['대차 존속 중 개별 거래조건의 상호 변경 합의'],['최초 거래조건 합의','담보 수량 조정 집행','증권·담보 실제 이전','대차 효력 발생 조건 충족 상태','대차 종료'],
 ['WGSS-F4E90272B38B','WGSS-C6CD1A422A0E','WGSS-62992A5182F5','WGSS-D490EDEAC5CD'],
 [('SEC_FILED_SECURITIES_LOAN',loanquote)],
 ['SEC에 제출된 역사적 증권대차 계약 Schedule 3 §1.1의 상호 합의 조건입니다. 현재 보편적 약관·법적 의무를 뜻하지 않습니다.','§1.3의 증권·담보 이전 요건은 계약 효력 조건입니다. 같은 이전 이행의 상태를 별도 업무로 세지 않습니다.'],'securities'))
new_ids=[w['id'] for w in new]
ledger['additions']+=new
patches={
 'WGSS-9EDEA2CB28B3':('요청 시점의 서비스 접근권한 판정(WGSS-MECE-SERVICING-ACTIVITY-AUTHORITY)',['WGSS-MECE-SERVICING-ACTIVITY-AUTHORITY']),
 'WGSS-MECE-MASTER-AGREEMENT-FORMATION':('제안 활동의 마스터계약 적용범위 판정(WGSS-MECE-MASTER-ACTIVITY-COVERAGE)',['WGSS-MECE-MASTER-ACTIVITY-COVERAGE']),
 'WGSS-5F8FC967D676':('기관 트레이더의 거래 책임·한도 배정(WGSS-MECE-TRADER-MANDATE)',['WGSS-MECE-TRADER-MANDATE']),
 'WGSS-MECE-FINANCIAL-GOAL':('고객 재무계획 산출물 작성(WGSS-MECE-FINANCIAL-PLAN)',['WGSS-MECE-FINANCIAL-PLAN']),
 'WGSS-DF3339F2234C':('미래 포트폴리오 예측을 현재가치 평가로 자동 동일시하지 않음(별도 경계 검토 중)',[]),
 'WGSS-D490EDEAC5CD':('수락된 증권의 보관 책임 인수(WGSS-MECE-SECURITIES-SAFEKEEPING-RECEIPT)',['WGSS-MECE-SECURITIES-SAFEKEEPING-RECEIPT']),
 'WGSS-F4E90272B38B':('존속 중 거래조건 변경 합의(WGSS-MECE-SECURITIES-LOAN-AMENDMENT)',['WGSS-MECE-SECURITIES-LOAN-AMENDMENT']),
 'WGSS-779616C3F2C3':('기관 신용·마진 정책 확정 및 ALM 초대형 거래 승인',['WGSS-MECE-CREDIT-MARGIN-POLICY','WGSS-MECE-LARGE-TRADE-APPROVAL']),
}
actions=[]
for w in new: actions.append(dict(work_id=w['id'],decision='added_review_definition',reason=w['review_note'],automatic_adoption=False))
for i,(exclude,near) in patches.items():
    w=by[i];boundary=copy.deepcopy(w['boundary']);boundary['related_ids']=list(dict.fromkeys(boundary['related_ids']+near))
    fields={'excludes':w['excludes']+[exclude],'boundary':boundary}
    reason='v1.9 독립 결과·책임 범위를 보완했습니다. 기존 결과를 새 표준 객체·상품·상태로 복제하지 않습니다.'
    ledger['edits'].append(dict(id=i,fields=fields,reason=reason,phase='v19-root-boundary',automatic_adoption=False))
    actions.append(dict(work_id=i,decision='corrected_boundary',reason=reason,automatic_adoption=False))
ledger['new_version']='WGSS-operation-v1.9-review-20261011';ledger['v19_results_applied']=True
write(ROOT/'data/operation-backbone-dispositions.json',ledger)
nav=read(ROOT/'data/business-backbone-review.json');nav['operation_version']=ledger['new_version']
nav['assignments'] += [dict(id=i,family_id=f,ambiguous=False,reason='원문 직접 대상·결과에 따른 v1.9 탐색 배정') for i,f in items]
write(ROOT/'data/business-backbone-review.json',nav)

def candidate(k):return 'CANDIDATE-'+k+'#0'
closed={candidate('ServiceDomain:28808'):'권한 성립·채무자 추심 수권과 다른 서비스 접근권한 판정 결과를 원문으로 등록했습니다.',
 candidate('ServiceDomain:31108'):'정책 지시와 초대형 거래 승인·거절을 독립 결과 두 개로 분리·등록했습니다.',
 candidate('ServiceDomain:38568'):'기관 트레이더의 거래 책임 배정을 고객 접근 프로파일과 구분해 등록했습니다.',
 candidate('ServiceDomain:42913'):'기관 정책 지침을 개별 고객 한도 승인과 구분하여 등록했습니다.',
 candidate('BusinessCapability:64188'):'목표·권고·효과성 판정과 별개인 계획 산출물 작성만 등록했습니다. 미명시 생애주기를 추가하지 않습니다.',
 candidate('BusinessCapability:64533'):'공식 제출 계약 양식으로 증권 보관 인수 책임을 입증해 등록했습니다. 모든 금융상품·법적 소유권 이전으로 일반화하지 않습니다.',
 'SOURCE-RESULT-CORRESPONDENT-RECIPROCITY':'명시된 이후 활동은 호혜적 거래실적·영업 관계 관리입니다. X01 경영 범위로 제외하고 최초 금융 서비스 관계 성립은 기존 정의에 유지합니다.',
 'SOURCE-RESULT-SECURITIES-LOAN-LIFECYCLE':'상호 거래조건 변경을 등록했습니다. 실제 증권·담보 이전에 따른 효력 조건은 계약 조건으로 보존하고 독립 상태 업무로 추가하지 않습니다.'}
nexts={
 'INPUT-lending-trade-invoice financing advance-draw-51':('송장금융 실제 선지급 책임·계약 구조','송장금융 약정의 채권양도·담보 설정과 실제 지급 조항을 확보해 지급요청, 채권매입 이행, 담보대출 집행과 대조합니다.'),
 candidate('ServiceDomain:37104'):('투자자 간 지분 이전의 직접 결과','유닛트러스트의 투자자 간 교환 절차에서 소유권 이전·매매 성립·증권 입출고 중 독립 결과를 특정하고, 일반 증권 이전과 중복 여부를 판정합니다.'),
 candidate('ServiceDomain:37849'):('Financial Compliance 원문 의미 불명확','BIAN 역할 정의의 non compliance와 실적 미달 예시의 의미 충돌을 확인합니다. 내부 실적 시정은 X01로 제외하고 규제 시정 의무는 별도 공식 절차로 입증합니다.'),
 candidate('ServiceDomain:38742'):('대주 참여지분 이전과 분담금 정산의 경계','대출 참여지분 이전 약정에서 이전되는 권리·의무를 확인하고 WGSS-1A0EF50D7D0F의 분담금 정산·지분 조정과 분리 또는 포함 경계를 판정합니다. 만기처리의 실제 상환·종료 결과도 원문에서 분해합니다.'),
 candidate('ServiceDomain:44473'):('일반 펀드 설정 결과의 기능·법적 근거','펀드 정관·설립 계약 또는 공식 설정 절차에서 당사자·성립 결과를 확보합니다. 샤리아 운용지침, 투자자 청약·환매, 펀드 운영 부모와 구분합니다.'),
 candidate('ServiceDomain:46157'):('기관 자금조달 부모의 원자 결과 분해','전술·전략 조달 관리와 유동화 착수의 실제 기능 원문을 수집해 차입·증권 발행·매각·지급 등 기존 직접 결과와 연결합니다. manage funding만으로 자금조달 집행을 등록하지 않습니다.'),
 candidate('ServiceDomain:48953'):('펀드 NAV 확정 결과의 근거','공식 펀드 약관·규칙에서 NAV 산정 책임과 단위당 가격 확정 조건을 확보하여 현재 금융상품 평가가치와 비교합니다. BIAN의 회계 관리 문구는 NAV 근거로 쓰지 않습니다.'),
 candidate('BusinessCapability:64039'):('발행인 배당 배분과 기존 기업행위 처리의 경계','은행 배당 지급·배분의 실제 절차를 확보하고 C69BC3C2667A·CA96597CD253의 권리배정·분배와 비교합니다. 발행인이라는 관점만으로 지급 업무를 복제하지 않습니다.'),
 candidate('BusinessCapability:64436'):('포트폴리오 예상가치와 평가가치의 의미 경계','공식 예측 기능의 기준가치·가정·사용 목적을 확인해 현재 가치평가의 방법·기준시점 변형인지 독립 전망 정보인지 판정합니다. 미래 시점만으로 새 업무를 만들지 않습니다.'),
 candidate('BusinessCapability:64574'):('금융계정 통제 복합 역량의 책임·범위','승인·상시 감시·정확성 판정을 실제 금융계정 통제 절차에서 분해합니다. 지급지시 승인·계좌 대조에 포함되는 범위와 그 밖의 직접 결과를 각각 판정합니다.'),
 'SOURCE-RESULT-REINSURANCE-RISK-DECISION':('재보험 인수심사 책임의 직접 근거','재보험사의 공식 인수 절차 또는 규정에서 위험 선택·조건 결정 책임을 확보해 원수 보험 심사와 공유 재보험계약 성립에 대한 경계를 판정합니다.'),
 'SOURCE-RESULT-TREASURY-RATE-PUBLICATION':('전행 기준 금리·환율과 계약별 적용 금리','BIAN 46157의 금리·환율 결정·공표가 기관 기준 가격표인지 개별 계약 적용금리인지 확인하여 예금 금리 설정·환율 정보 제공의 범위를 교정하거나 독립 결과를 등록합니다.'),
 'SOURCE-RESULT-MASTER-AGREEMENT-LIFECYCLE':('마스터계약 변경 결과의 직접 근거','활동 적용범위 판정은 등록했습니다. 별도 계약 변경 절차·합의 결과를 확보하여 maintain 표현만으로 변경·종료를 추정하지 않고 잔여 변경 후보를 판정합니다.'),
 'SOURCE-RESULT-NETWORK-PARTICIPATION-LIFECYCLE':('카드망 참가조건·상태 변경의 직접 근거','카드망 참가 약정 또는 공식 운영 절차에서 변경 합의와 참가 자격 중지·회수 결과를 확보합니다. terms administration·status maintenance만으로 전 생애주기를 등록하지 않습니다.')}
ticket_rows=[];remaining=[]
for t in read(RUN/'tickets.json'):
    i=t['id'];r=advice[i];done=i in closed
    reason=closed[i] if done else nexts[i][1]
    ticket_rows.append(dict(id=i,state='closed_root_decision' if done else 'pending_atomic_proof_or_boundary',
       reason=reason,proposal_decision=r['decision'],proposal_prompt_sha256=r['prompt_sha256'],
       automatic_adoption=False,independent_human_review=False,
       root_qualification=('채권·계약·날짜·관점 차이만으로 확대하지 않습니다. 원문이 입증하는 기능 범위만 적용합니다.')))
    if not done:
        remaining.append({**{k:v for k,v in t.items() if k not in ['sections','source_keys','decision_options']},
          'title':nexts[i][0],'reason':reason,'next_action':reason,'work_ids':t.get('work_ids',[]),
          'done_conditions':t['done_conditions'],'related_work_ids':t.get('related_work_ids',[])})

# Root-authored qualifications: these disagree with several model expansions.
qualifications=[
 {'finding':'기관 자금조달 실행 신규 권고','decision':'rejected_unproven_parent_execution','reason':'manage tactical/strategic funding은 완료된 조달거래의 구조·책임을 특정하지 않습니다.'},
 {'finding':'카드망 조건변경 신규 권고','decision':'deferred_missing_direct_change_result','reason':'terms administration만으로 합의된 조건변경 결과를 입증하지 않습니다.'},
 {'finding':'미래 포트폴리오 평가 신규 권고','decision':'deferred_semantic_discriminator','reason':'시점·평가방법·수량 차이만으로 독립 금융업무를 추가하지 않습니다.'},
 {'finding':'발행인 배당 지급 신규 권고','decision':'deferred_counterparty_clone_risk','reason':'동일 분배의 발행인·수탁자 관점을 별도 지급 결과로 복제할 수 없습니다.'},
 {'finding':'보관 수임 근거 부족','decision':'corrected_with_new_primary_form','reason':'새 SEC 제출 계약 양식 §3.1·§3.4로 증권 보관 인수만 한정해 입증했습니다.'},
 {'finding':'만다트·마스터계약 적용범위 통합 권고','decision':'split_distinct_constraint_objects','reason':'외부 제공자의 은행 서비스 접근권과 고객 마스터 법적 조건은 독립적인 권한·계약 제약입니다. 채무자의 추심 허용권도 구분합니다.'},
 {'finding':'재무계획 변경·종료 갭 신규 권고','decision':'rejected_speculative_lifecycle_enumeration','reason':'create, monitor etc...는 변경·종료가 필수 업무임을 특정하지 않습니다. 명시된 생성 기능을 등록하고 원문 CE는 부분으로 유지합니다.'}]
root_sources=[]
scope_jobs=list((RUN/'reviews').glob('scope-own*/*/proposal.json'));assert len(scope_jobs)==1
scope_job=read(scope_jobs[0]);scope_by={r['reference_key']:r for r in scope_job['result']['rows']}
exclusion_reasons={
 '29101':'전사 조직·시스템 아키텍처 청사진과 도입 지원', '29475':'PBX 음성채널의 용량·설정·유지보수·장애 운영',
 '30604':'잠재고객 획득 캠페인·대상 목록·반응 분석','30904':'고용주가 임직원 업무경비를 승인·급여로 정산하는 내부 경비 운영',
 '30911':'고객 유지 캠페인의 범위·성과·자원 관리','31008':'은행 자체 지식재산 등록·보호·라이선스 관리',
 '31034':'고용주와 인력의 고용계약 협상·유지','32097':'생산 플랫폼·인프라의 운영·백업·복구',
 '33231':'잠재고객 대상 캠페인의 범위·성과 관리','33514':'전사 HR 정책·인력 계획',
 '33924':'사업장 열·수도·전력 등 시설 유틸리티 조달·운영','34170':'생산시스템 장애 접수·진단·엔지니어 지원',
 '34291':'직원 대상 금융상품 교육·일정·효과 측정','35210':'직원 성과 평가·다면 피드백',
 '36108':'직원 업무·직위 배정·가동률 관리','36250':'기관 사업장의 공간·부서 배분·활용도 관리',
 '37168':'내부 통신망·임직원 생산시스템 접근 관리','37174':'전사 브랜드·마케팅 활용 관리',
 '37520':'광고 캠페인 예산·자원·효과 관리','38385':'생산시스템 신규 버전 배포·검수·교육·전환 지원'}
for native,reason in exclusion_reasons.items():
    k='ServiceDomain:'+native;s=source_by[k];m=scope_by[k]
    assert m['decision']=='excluded_scope' and m['exclusion_id']=='X01'
    root_sources.append(dict(reference_key=k,decision='excluded_scope',work_ids=[],reason=reason+'입니다. 자체 기능 전체를 대조했으며 고객 금융 결과·공통 이용자 지원 결과가 아닌 X01 공급기관 운영 범위로 판정합니다.',
      exclusion_id='X01',evidence=[{'section_id':q['section_id'],'quote':q['text']} for q in s['own_sections']],
      proposal_prompt_sha256=scope_job['prompt_sha256'],source_name=s['name'],root_adjudicated=True,coverage_is_complete=False,automatic_adoption=False))
# These source decisions remain partial unless the whole own source scope is
# resolved. A newly proven result does not upgrade unrelated functions.
links={
 'ServiceDomain:28808':(['WGSS-9EDEA2CB28B3',items[0][0]],'접근 약정 성립·요청 접근권한 판정은 입증했습니다. 활동 보고의 수신자·독립 산출물은 미명시입니다.'),
 'ServiceDomain:31108':([items[2][0],items[3][0],'WGSS-MECE-BANK-TREASURY-POSITION','WGSS-859BDADDD789'],'정책 지시·독립 거래 승인·포지션·위험평가를 연결했습니다. 정책 정렬 평가의 전 범위는 별도 대조가 필요합니다.'),
 'ServiceDomain:37104':(['WGSS-ADD-D0A1ACA9428E','WGSS-D490EDEAC5CD'],'투자자 간 지분 교환을 청약·입출고만으로 전부 포함했다고 주장하지 않습니다.'),
 'ServiceDomain:37849':(['WGSS-19829603FDD5'],'내부 실적 시정 예시와 non compliance 역할 표현의 의미가 불명확합니다. 규제 시정 의무는 입증되지 않았습니다.'),
 'ServiceDomain:38568':([items[5][0]],'트레이더 거래 책임·한도 배정은 입증했습니다. 시장 정보·호가·P&L 등 다른 기능의 포함 범위는 남았습니다.'),
 'ServiceDomain:38742':(['WGSS-1A0EF50D7D0F','WGSS-2F243A6298A1'],'지분 이전과 분담금 정산의 권리 결과, 만기 처리의 최종 결과는 미확정입니다.'),
 'ServiceDomain:42913':([items[4][0]],'자체 두 조항의 신용·마진 정책 결정·정비 책임을 직접 결과로 등록했습니다.'),
 'ServiceDomain:44473':(['WGSS-ADD-D0A1ACA9428E','WGSS-ADD-555BDFC74CD7'],'투자자 유입·유출과 펀드의 법적 설정을 분리했습니다. 회계·보고·설정 전체를 포함했다고 주장하지 않습니다.'),
 'ServiceDomain:46157':(['WGSS-MECE-BANK-TREASURY-POSITION','WGSS-D151DD97CD2C'],'통합 포지션 외 조달·유동화 착수·기관 적용금리 결과의 경계가 남아 있습니다.'),
 'ServiceDomain:48953':(['WGSS-ADD-D0A1ACA9428E','WGSS-ADD-555BDFC74CD7','WGSS-587877289E94'],'청약·환매·보수 일부를 연결했습니다. 자체 원문에 NAV 확정은 없으며 회계·보고의 전 범위도 미확정입니다. 원문 상품 설명을 실제 시장의 법적 규칙으로 사용하지 않습니다.'),
 'BusinessCapability:64188':([items[6][0],'WGSS-CLOSE-B834C8689F3C'],'계획 생성과 효과성 판정을 구분했습니다. 일반 monitor 등 세부 내용 전체의 포함을 주장하지 않습니다.'),
 'BusinessCapability:64039':(['WGSS-C69BC3C2667A','WGSS-CA96597CD253'],'배당 배분·지급은 인접 결과로 연결하되 발행인 관점만으로 새 지급 업무를 만들지 않습니다. allocation의 의사결정 범위는 남았습니다.'),
 'BusinessCapability:64436':(['WGSS-DF3339F2234C','WGSS-B091487E4AA0'],'미래 포트폴리오 전망과 현재 금융상품 평가의 책임·산출물 의미 경계는 미확정입니다.'),
 'BusinessCapability:64533':([items[7][0],'WGSS-D490EDEAC5CD'],'보관 수락과 장부 이동을 분리했습니다. 제출 계약 양식은 증권 수탁의 한정된 근거이며 모든 금융상품 보관을 입증하지 않습니다.'),
 'BusinessCapability:64574':(['WGSS-B704DE36E9CF','WGSS-AFF4499574AA'],'승인·감시·정확성 판정의 직접 대상·책임이 불명확하여 복합 역량을 전부 포함으로 표시하지 않습니다.'),
 'ServiceDomain:31459':(['WGSS-MECE-MASTER-AGREEMENT-FORMATION',items[1][0]],'최초 계약과 활동 적용범위 판정을 등록했습니다. maintain 문구로 모든 변경·종료를 입증하지 않습니다.'),
 'ServiceDomain:34643':(['WGSS-MECE-CORRESPONDENT-RELATIONSHIP'],'최초 금융 서비스 관계 성립은 포함하고 이후 영업·호혜 실적 관리·운영 이슈는 X01 공급기관 경영 범위로 한정 제외했습니다.'),
 'ServiceDomain:36870':(['WGSS-MECE-CARD-NETWORK-PARTICIPATION'],'최초 참가 이용관계를 연결했습니다. terms administration·status maintenance의 실제 변경·중지·해지 결과는 미명시입니다.')}
for k,(ids,reason) in links.items():
    s=source_by[k]
    root_sources.append(dict(reference_key=k,decision='source_specification_gap' if k in ['ServiceDomain:37849','BusinessCapability:64436','BusinessCapability:64574'] else 'linked_specific' if k=='ServiceDomain:42913' else 'linked_composed' if k=='ServiceDomain:34643' else 'linked_partial',
      work_ids=ids,reason=reason,evidence=[{'section_id':q['section_id'],'quote':q['text']} for q in s['own_sections']],
      source_name=s['name'],root_adjudicated=True,coverage_is_complete=False,automatic_adoption=False,
      review_phase='v19-own-source-root-review'))
record=dict(version='WGSS-mece-root-v19-20261011',output_version=ledger['new_version'],
    rows=ticket_rows,remaining_work=remaining,root_qualifications=qualifications,actions=actions,
    added_work_ids=new_ids,source_dispositions=root_sources,
    automatic_adoption=False,independent_human_review=False,global_mece_approved=False)
write(ROOT/'data/mece-v19-root-dispositions.json',record)
progress=read(ROOT/'data/mece-closure-review.json');progress['output_version']=ledger['new_version']
progress['version']='WGSS-mece-closure-v19-20261011';progress['root_decisions']+=actions
sr={r['reference_key']:r for r in progress['source_dispositions']}
sr.update({r['reference_key']:r for r in root_sources});progress['source_dispositions']=list(sr.values())
progress['current_stage']='v19_root_results_registered_delta_review_pending'
progress['technical_validation']={'state':'pending','note':'v1.9 결과·경계·UI 변경 후 전체 회귀 대기'}
write(ROOT/'data/mece-closure-review.json',progress)
print(json.dumps({'registered_additions':len(new),'closed_tickets':len(closed),'remaining_tickets':len(remaining),'root_source_rows':len(sr),'global_mece_approved':False}))
