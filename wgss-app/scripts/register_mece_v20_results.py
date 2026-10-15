"""One-time root-authored migration; Bedrock proposals are never auto-adopted."""
import copy,json,hashlib
from pathlib import Path
from prepare_mece_v18 import plain
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research/source-store/mece-closure-v20-20261011';STORE=RUN/'sources'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
assert not ledger.get('v20_results_applied'),'Already applied; do not rerun'
before=read(RUN/'catalogue-before.json');by={w['id']:w for w in before['works']};assert len(by)==382
sections={s['section_id']:s for row in read(ROOT/'research/source-store/mece-closure-20261006/source-input.json') for s in row['own_sections']}
def ref(sid,quote):
    if sid.startswith('BIAN:'):
        s=sections[sid];native=sid.split(':')[1];p=Path(s['source_file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==s['source_file_sha256']
        shard=json.JSONDecoder().raw_decode(p.read_text().split('var objectData =',1)[1].strip())[0]
        docs=[(n,c) for n,c in enumerate(shard[native]['data'][0]['categories']) if c['type']=='documentation']
        n,c=docs[int(sid.rsplit(':',1)[1])];assert quote in plain(c['content']['value'])
        return dict(id='BIAN:14.0.0:portal:'+native,name=s['name'],url=s['source_url'],locator=f'objectData["{native}"].data[0].categories[{n}].content.value',source_sha256=s['source_file_sha256'],exact_quote=quote,context_requires_review=False,source_snapshot_id='BIAN-14-public-portal-2026-10-02',proof_scope='own_functional_clause_not_legal_duty_or_provider_ui',rationale='v2.0 root 원문·전체 정의 대조입니다.')
    m=read(STORE/(sid+'.json'));assert not m.get('functional_evidence_rejected');assert quote in (STORE/m['text_path']).read_text()
    return dict(id='WGSS-PROCESS-'+sid,name=sid,url=m['url'],locator='operative clause: '+quote[:70],source_snapshot_id='WGSS-primary-functional-20261011',source_sha256=m['sha256'],source_store_relative=str(STORE.relative_to(ROOT)),exact_quote=quote,context_requires_review=False,proof_scope=m['source_kind']+'_conditional_function_not_global_law_or_ui',rationale='공식 원문의 한정된 기능 근거입니다. 현재 서비스·계약 실행·화면 관측을 주장하지 않습니다.')
def line(sid,number):
    import re
    text=(STORE/(sid+'.txt')).read_text()
    match=re.search(r'^L'+str(number)+r'(?:@P[^:]+)?: (.*)$',text,re.M);assert match,(sid,number)
    return match[1]
def paragraph(sid,needle,length=450):
    text=(STORE/(sid+'.txt')).read_text();at=text.find(needle);assert at>=0,(sid,needle)
    return text[at:at+length]
new=[];families={}
def add(suffix,title,category,role,obj,outcome,definition,includes,excludes,near,evidence,conditions,family):
    i='WGSS-MECE-'+suffix
    w=dict(id=i,title=title,layer='institution',category=category,actor_role=role,actor_label='금융 업무 책임자 · '+role.replace('_',' '),object_key=obj,outcome_key=outcome,outcome=outcome.replace('_',' '),discriminator=None,definition=definition,includes=includes,excludes=excludes,boundary=dict(related_ids=near,distinction='책임·직접 대상·독립 완료 결과로 구분하며 상품·관점·방법·상태로 복제하지 않습니다.'),refs=[ref(*e) for e in evidence],status='edited',source_gaps=[],input_ids=[],origin_unit_id='MECE-CLOSURE-'+suffix,review_note='v2.0 root 편집 판정입니다. 전체 MECE·세계 금융 총수·현재 업체 서비스·UI 관측 승인이 아닙니다.',definition_is_wgss_editorial=True,independent_human_review=False,mece_approved=False,applicability_conditions=conditions)
    new.append(w);families[i]=family;return i
fund='SEC_FUND_DECLARATION_SELECTED';loan='SEC_SYNDICATED_ASSIGNMENT_EFFECTIVE';scheme='MASTERCARD_PARTICIPATION_SELECTED'
transfer=add('REGISTERED-HOLDER-TRANSFER','등록 증권 보유자 이전 확정','investments-custody','securities_register_administrator','registered_security_holder_transfer','make_transfer_of_registered_security_holder_effective',
 '등록 담당자가 유효한 이전 지시·양도증서와 필요한 권한 근거를 수리하고 등록부에 반영하여 기존 증권의 등록 보유자가 변경되는 결과.',
 ['기존 펀드 지분 등 등록 증권의 보유자 이전 효력 확정'],['신규 지분 생성·환매 소멸','명의대리 보유관계 자체','매매 합의','수탁 계좌의 증권 포지션 입출고만 기록'],
 ['WGSS-11940117C228','WGSS-D490EDEAC5CD','WGSS-ADD-D0A1ACA9428E'],[(fund,line(fund,229)),(fund,line(fund,230))],
 ['해당 선언서에서는 등록 전 기존 보유자가 계속 보유자로 간주됩니다. 다른 관할·등록 방식에 이 효력 조건을 자동 적용하지 않습니다. 비등록 증권의 모든 소유권 이전을 포함한다고 주장하지 않습니다.'],'securities')
assignment=add('LENDER-POSITION-ASSIGNMENT','대출 대주 지위·권리·의무 이전','lending-trade','lender_assignment_counterparty','lender_contractual_position_assignment','transfer_lender_contractual_rights_and_obligations',
 '기존 대주와 양수인이 약정상 양도·수리·등록 조건을 충족하여 양수인이 대출계약 당사자가 되고 양도인이 이전 범위의 의무에서 벗어나는 결과.',
 ['대출·약정상 대주 지위의 전부 또는 일부 이전'],['기존 대주가 남는 경제적 참여분 매각','신디케이트 분담금 정산','대출자산 풀 유동화 매각','등록부 입력만을 별도 업무로 복제'],
 ['WGSS-1A0EF50D7D0F','WGSS-D151DD97CD2C','WGSS-94E86B863786'],[(loan,line(loan,1678))],
 ['2016년 제출 약정의 Assignment and Assumption 효력 조건을 기능 근거로 사용합니다. 동의·수리·등록 조건은 약정별로 확인합니다. 원채무의 소멸을 의미하지 않습니다.'],'lending')
participation=add('LOAN-PARTICIPATION-SALE','대출의 경제적 참여분 매각','lending-trade','loan_participation_counterparty','loan_economic_participation_agreement','establish_economic_participation_with_original_lender_retained',
 '대주와 참여자가 대출의 경제적 참여분 매각을 성립시키되, 원 대주가 원 대출계약의 당사자·의무 이행 책임자로 계속 남는 결과.',
 ['원 대주 지위를 유지하는 대출 참여분 매각 성립'],['원 대출계약의 대주 지위·의무 양도','신디케이트 자금 정산','대출자산 풀 유동화 매각'],
 [assignment,'WGSS-1A0EF50D7D0F','WGSS-D151DD97CD2C'],[(loan,line(loan,1684))],
 ['해당 약정의 participation 구조입니다. 차주 통지·동의 면제와 참여자의 권한 조건을 다른 약정에 일반화하지 않습니다.'],'lending')
series=add('FUND-SERIES-ESTABLISHMENT','집합투자 시리즈의 분리 책임재산 설정','investments-custody','fund_series_establishment_authority','segregated_collective_investment_series','establish_segregated_collective_investment_series',
 '펀드 설정 책임자가 결의 등 필요한 조건에 따라 집합투자 시리즈를 설정·지정하여 해당 시리즈의 자산·부채 귀속과 다른 시리즈와 구별되는 책임재산 범위를 성립시키는 결과.',
 ['분리 책임재산을 갖는 집합투자 시리즈 설정'],['모체 신탁 최초 창설·출연','단순 투자상품 이름 등록','청약 지분 생성','투자정책·샤리아 기준 확정','종류주 구분만으로 분리 책임재산 성립을 추정'],
 ['WGSS-7944C767C173','WGSS-D04C78B35E3E','WGSS-ADD-D0A1ACA9428E'],[(fund,line(fund,242)),(fund,line(fund,251)),(fund,line(fund,263))],
 ['해당 선언서의 시리즈별 계약상 책임 제한입니다. Class별 비용 배분을 Series별 책임재산 격리와 동일시하지 않습니다. §3804의 법정 효과에는 증서상 공지 등 별도 조건이 있습니다. 설정만으로 투자금 납입·상시 운용·규제인가가 끝나지 않습니다.'],'securities')
nav=add('FUND-NAV','펀드 지분당 순자산가치 확정','investments-custody','fund_nav_determination_authority','fund_net_asset_value_per_share','determine_fund_net_asset_value_per_share',
 '펀드 또는 위임받은 산정 책임자가 보유자산 가치·귀속 비용과 부채·발행 지분을 반영하여 시리즈·클래스의 지분당 순자산가치를 정해진 기준에 따라 확정하는 정보 결과. 청약·환매 가격 산정에 사용하는 기준값이다.',
 ['시리즈·클래스의 지분당 순자산가치 확정'],['개별 보유 금융상품의 평가가치만 산출','청약 주문 실행·지분 생성','환매 주문 실행·지분 소멸','산정 권한 위임·기준시점만으로 별도 업무 생성'],
 ['WGSS-DF3339F2234C','WGSS-ADD-D0A1ACA9428E','WGSS-ADD-555BDFC74CD7'],[(fund,line(fund,446)),(fund,line(fund,233)),('ECFR_FUND_NAV_SELECTED',line('ECFR_FUND_NAV_SELECTED',104))],
 ['미국 규정 및 해당 선언서에 근거한 기능입니다. NAV와 실제 청약·환매 가격의 관계에는 판매 수수료·환매 비용 등 적용 조건이 있으며 항상 최종 거래가격과 같다는 뜻이 아닙니다.'],'securities')
projection=add('INVESTMENT-OUTCOME-PROJECTION','투자 가정에 따른 미래 결과 전망 산출','investments-custody','investment_projection_provider','prospective_investment_outcome_analysis','produce_prospective_investment_outcome_analysis',
 '분석 제공자가 투자·전략·시장 등 가정을 적용하여 미래 투자금전 결과의 전망을 산출하는 정보 결과. 예상 가치 또는 결과 가능성 등 분석 형태는 적용 방법과 산출물의 변형이다.',
 ['가정에 따른 미래 포트폴리오 금전가치 전망','시뮬레이션·통계 분석에 따른 미래 투자결과 가능성 산출'],['평가 목적의 현재 금융상품 가치 확정','실현된 투자 성과 보고','개인 연금 계정의 예상급여 조회','투자 권고 확정·재무계획 전체 수립','전망대로 투자·지급이 실제 이행되었다는 주장'],
 ['WGSS-DF3339F2234C','WGSS-B091487E4AA0','WGSS-517968C749F0','WGSS-MECE-FINANCIAL-PLAN'],
 [('BIAN:64436:doc:0','Ability to project (using various methods) the monetary worth of an investment portfolio for any future time.'),('FINRA_ANALYSIS_TOOLS',paragraph('FINRA_ANALYSIS_TOOLS','criteria and methodology used',260))],
 ['가치평가의 날짜만 바뀌었다는 이유로 분리하지 않습니다. 직접 산출 목적은 가정하 미래 투자결과 전망이며 현재 가치평가와 구분합니다. FINRA 규칙 적용 시 방법·주요 가정·한계·비보장 고지가 필요합니다. 예상값과 확률분포를 방법 차이로 복제하지 않습니다.'],'securities')
rates=add('BANK-REFERENCE-RATES','은행 기준 금리·환율 결정·공표','institution-processing','treasury_rate_authority','bank_reference_interest_and_exchange_rate_schedule','determine_and_publish_bank_reference_rates',
 '은행 금리 책임자가 상품·서비스에 적용할 기관 기준 금리·환율을 결정하고 공표하여 적용 기준 가격표를 확정하는 결과.',
 ['기관 기준 금리·환율 결정 및 공표'],['개별 예금계약 적용금리 설정','고객의 참고 환율 조회','개별 거래 견적 수락','기관 포지션 산출','일반 ALM 정책 지시'],
 ['WGSS-8080B7031AAB','WGSS-BACKBONE-FX-QUOTE','WGSS-MECE-ALM-POLICY-DIRECTIVE'],[('BIAN:46157:doc:3','Determine and publish bank interest and exchange rates')],
 ['BIAN의 은행 기준 가격 결정 책임입니다. 고객별 최종 제시금리·약정금리·수수료가 같은 값이라는 뜻이 아닙니다. 공표 대상·적용 조건은 기관 절차에 따릅니다.'],'controls')
master=add('MASTER-AGREEMENT-AMENDMENT','고객 마스터계약 조건변경 합의','identity-support','master_agreement_counterparty','customer_master_agreement_amendment','effect_agreed_amendment_of_customer_master_terms',
 '고객과 기관이 기존 마스터계약의 법적 조건 변경을 합의하고 약정상 효력 조건을 충족하여 변경 합의가 성립하는 공유 결과.',
 ['기존 마스터계약 조건변경 합의의 효력 확정'],['마스터계약 최초 성립','제안 활동의 계약 적용범위 판정','하위 개별 상품약정 변경','운영기관의 일방적 규칙 개정','마스터계약 전체 종료'],
 ['WGSS-MECE-MASTER-AGREEMENT-FORMATION','WGSS-MECE-MASTER-ACTIVITY-COVERAGE','WGSS-671FA819885C'],[('ISDA_AMICUS_MASTER_AMENDMENT',paragraph('ISDA_AMICUS_MASTER_AMENDMENT','No amendment, modification or waiver',373))],
 ['ISDA 원문의 §9(b)는 서면·양 당사자 실행 또는 규정된 메시지 교환 확인 조건을 명시합니다. 법원서면에 수록된 역사적 원문이며 모든 금융사의 현행 변경 절차로 일반화하지 않습니다.'],'controls')
advance=add('RECEIVABLE-ADVANCE-DISBURSEMENT','매입채권에 대한 선지급금 집행','lending-trade','receivable_finance_advance_provider','purchased_receivable_advance_obligation','fulfil_advance_payment_on_purchased_receivable',
 '채권매입 금융제공자가 매입채권을 근거로 약정한 선지급금을 고객에게 실제 지급하여 선지급 의무를 이행하는 결과.',
 ['채권매입 기반 선지급금 실제 지급'],['채권 소유권의 매입 자체','송장금융 지급요청 제출','대출계약 기반 대출금 지급','채무자로부터 팩토링 채권 회수','이용가능액 조회·산정만 수행'],
 ['WGSS-610BF7A63589','WGSS-MECE-INVOICE-FINANCE-PAYMENT-REQUEST','WGSS-DE4E23D3BB89','WGSS-F566EFC5B5E6'],
 [('HSBC_INVOICE_DISCOUNTING',paragraph('HSBC_INVOICE_DISCOUNTING','Invoice Discounting provides funding',470))],
 ['HSBC 안내가 명시한 채권매입·선지급 구조에 한정한 기능 근거입니다. 실제 약정·지급 관측이 아니며 NatWest 지급요청 Sent로 지급 완료를 추정하지 않습니다. 지급 비율·한도·수수료는 약정별 조건입니다.'],'lending')
schemechange=add('CARD-NETWORK-TERMS-CHANGE','카드망 참가조건 변경·제한 확정','institution-processing','card_network_participation_authority','existing_network_participant_rights_and_obligations','modify_existing_network_participant_rights_and_obligations',
 '카드망 운영기관이 기존 참가자의 허용 활동·권리·의무를 변경하여 참가조건 또는 권한 제한이 확정되는 결과. 참가관계의 영구 종료는 포함하지 않는다.',
 ['기존 참가권의 조건 부과·일시 정지','기존 참가자의 권리·의무 변경'],['카드망 참가관계 최초 성립','참가관계 영구 종료','개별 고객 계좌·카드 거래 제한','양자 계약 변경 합의를 규칙상 일방 권한에서 추정'],
 ['WGSS-MECE-CARD-NETWORK-PARTICIPATION','WGSS-C071E3977CBE'],[(scheme,line(scheme,1734)+'\n'+next(l for l in (STORE/(scheme+'.txt')).read_text().splitlines() if l.startswith('L1735'))),(scheme,line(scheme,1736))],
 ['2022-06-07 Mastercard 규칙 §1.12의 조건부 일방 권한을 기능 근거로 사용합니다. 조건 부과와 일시정지는 동일 기존 참가권 제약 변경의 변형입니다. 현재 권한·양자 합의 절차로 일반화하지 않습니다.'],'controls')
schemeend=add('CARD-NETWORK-PARTICIPATION-END','카드망 참가관계 종료 확정','institution-processing','card_network_relationship_termination_responsible','card_network_institution_participation_relationship','end_card_network_institution_participation_relationship',
 '약정·규칙에 따른 종료 책임자가 카드망 참가기관의 참가관계를 종료시켜 그 기관의 계속 참가 권리가 끝나는 결과. 자발적 탈퇴와 운영기관의 종료는 종료 원인·효력 조건의 변형으로 보존한다.',
 ['참가기관 자발적 탈퇴에 의한 참가관계 종료','운영기관의 규칙상 종료에 의한 참가관계 종료'],['참가권 일시 정지·제한','미처리 정산·분쟁·수수료 등 잔존 의무가 모두 소멸했다는 주장','개별 고객 카드 해지'],
 ['WGSS-MECE-CARD-NETWORK-PARTICIPATION',schemechange,'WGSS-EA7B479E14C4'],[(scheme,line(scheme,1751)+'\n'+next(l for l in (STORE/(scheme+'.txt')).read_text().splitlines() if l.startswith('L1752'))+'\n'+next(l for l in (STORE/(scheme+'.txt')).read_text().splitlines() if l.startswith('L1753')))],
 ['Mastercard의 자발적·운영기관 종료 조건과 Visa의 식별자 반납 조건은 각 규칙에 따라 적용하며 합쳐서 보편 조건으로 만들지 않습니다. 종료 후 남는 지급·통지·카드 취소 의무는 해당 독립 결과로 처리합니다.'],'controls')
dividend=add('DISTRIBUTION-DECLARATION','배당·분배 선언 결정','investments-custody','distribution_declaration_authority','dividend_or_distribution_event_terms','declare_dividend_or_distribution_event',
 '발행인 또는 펀드의 권한 있는 운영주체가 배당·분배의 실시와 조건을 선언하여 후속 권리배정·지급의 기준이 되는 이벤트를 확정하는 결과.',
 ['배당·분배 실시 및 조건 선언'],['보유자별 배정액 산출','실제 대금·증권 분배','이미 정해진 기업행위 정보 통지','기준일이라는 파라미터만 별도 업무로 복제'],
 ['WGSS-C69BC3C2667A','WGSS-CA96597CD253','WGSS-D078BF76895D'],[('DELAWARE_DIVIDEND_DECLARATION','The directors of every corporation, subject to any restrictions contained in its certificate of incorporation, may declare and pay dividends upon the shares of its capital stock either:')],
 ['Delaware 회사법 §170과 해당 펀드 선언서의 한정된 기능 근거입니다. 감독규제·정관·재원 요건은 관할·발행인별로 확인하며 선언만으로 지급 완료 또는 전 세계 동일 채무 효력을 주장하지 않습니다.'],'securities')
assert len(new)==12
edits=[]
def edit(i,**changes):
    value=copy.deepcopy(by[i]);value.update(changes);value['review_note']='v2.0 원문·근접 의미 경계를 편집했습니다. 전체 MECE 확정은 아닙니다.'
    edits.append(dict(id=i,fields={k:value[k] for k in changes}|{'review_note':value['review_note']},reason='직접 결과 경계와 새 기능 근거를 반영했습니다.'))
edit('WGSS-11940117C228',definition='명의대리인이 실질 수익자를 대신하여 증권 등 자산의 등록명의를 보유하는 명의대리 관계를 성립·관리하는 업무. 등록 담당자의 일반 증권 보유자 이전 효력 확정과 구분한다.',includes=['실질수익자를 위한 명의대리 보유관계 등록·관리'],excludes=['실제 매매체결·결제처리','등록 담당자의 증권 보유자 이전 효력 확정'])
edit('WGSS-1A0EF50D7D0F',definition='에이전트은행이 기존 신디케이트 참여기관의 분담금 이전 등 의무이행을 관리·정산하는 서비싱 결과. 계약상 대주 지위 이전과 경제적 참여분 매각은 별도 결과이다.',includes=['기존 참여지분·의무에 따른 자금이전·정산'],excludes=['최초 멤버십 가입 승인','대주 지위·권리·의무 양도','원 대주를 유지하는 경제적 참여분 매각','대출자산 풀 유동화 매각'])
edit('WGSS-DF3339F2234C',excludes=[x for x in by['WGSS-DF3339F2234C']['excludes'] if '미래 포트폴리오' not in x]+['펀드 지분당 순자산가치 확정','투자 가정에 따른 미래 결과 전망 산출'])
for i,excluded in [('WGSS-8080B7031AAB','은행 기준 금리·환율표의 결정·공표'),('WGSS-BACKBONE-FX-QUOTE','은행 기준 금리·환율표의 결정·공표'),('WGSS-MECE-MASTER-AGREEMENT-FORMATION','기존 마스터계약 조건변경 합의'),('WGSS-MECE-CARD-NETWORK-PARTICIPATION','기존 참가조건 변경·제한과 참가관계 종료'),('WGSS-610BF7A63589','매입채권에 대한 선지급금 실제 지급')]:edit(i,excludes=list(dict.fromkeys(by[i]['excludes']+[excluded])))
edit('WGSS-72879CC650A0',definition='보험자 또는 재보험자 내부에서 제출된 개별 위험·위험 포트폴리오를 평가하여 인수 여부·조건을 결정하는 업무. 대외 승낙에 따른 보험·재보험계약 성립 및 증권 발행과 구별된다.',includes=['원수보험 및 재보험 제시 위험에 대한 내부 위험평가·인수조건 결정'],excludes=['청약 제출','대외 승낙 통지·보험계약 성립','재보험계약 성립','보험증권 발행'],refs=by['WGSS-72879CC650A0']['refs']+[ref('SWISS_RE_UNDERWRITING',paragraph('SWISS_RE_UNDERWRITING','Underwriting 3 is the process',500))])
ledger['additions']+=new
# Existing edits are overlay order, not new IDs or retired work copies.
existing={e['id']:e for e in ledger['edits']}
for e in edits:
    if e['id'] in existing:existing[e['id']]['fields'].update(e['fields']);existing[e['id']]['reason']=e['reason']
    else:ledger['edits'].append(e)
invoice=next(x for x in ledger['input_mapping_overrides'] if x['input_id']=='lending-trade-invoice financing advance-draw-51')
invoice.update(work_ids=[advance,'WGSS-DE4E23D3BB89'],state='corrected_source_relationship',reason='실제 선지급 입력을 계약 구조별 이행 결과로 분해했습니다. 채권매입 기반은 매입채권 선지급금 집행, 대출계약 기반은 대출금 지급입니다. 요청 Sent를 지급 근거로 쓰지 않고 구조 미지정 시 자동 선택하지 않습니다.',selection_conditions={advance:'채권매입 약정에 따른 선지급 의무의 실제 지급','WGSS-DE4E23D3BB89':'대출계약과 승인된 인출요청에 따른 실제 지급'})
version='WGSS-operation-v1.10-review-20261011';ledger.update(new_version=version,v20_results_applied=True)
write(ROOT/'data/operation-backbone-dispositions.json',ledger)
navdata=read(ROOT/'data/business-backbone-review.json');navdata['operation_version']=version
assert set(families.values()) <= {f['id'] for f in navdata['families']}
for i,f in families.items():navdata['assignments'].append(dict(id=i,family_id=f,ambiguous=False,reason='v2.0 직접 결과에 따른 탐색 경로이며 금융 전체 MECE 승인이 아닙니다.'))
write(ROOT/'data/business-backbone-review.json',navdata)
progress=read(ROOT/'data/mece-closure-review.json');progress.update(output_version=version,version='WGSS-mece-closure-v20-20261011',current_stage='v20_current_delta_and_source_boundary_review',technical_validation={'state':'pending','automatic_adoption':False})
open_reasons={
 'CANDIDATE-ServiceDomain:37849#0':'원문 실적 미달 시정은 X01로 제외합니다. non compliance 의미 충돌은 남아 있어, 규제 시정 종결의 책임·완료 조건을 감독기관 절차 원문으로 확인합니다.',
 'CANDIDATE-ServiceDomain:44473#0':'시리즈 분리 책임재산 설정을 등록했습니다. 일반 펀드 투자정책 헌장의 확정 책임·절차를 확보해 기존 샤리아 정책·투자자 운용지침과 비교합니다. 샤리아 행의 상품명만 바꿔 복제하지 않습니다.',
 'CANDIDATE-ServiceDomain:46157#0':'포지션·기준 금리 결과는 분리했습니다. 전술·전략 조달과 유동화 착수의 실제 결과를 차입·발행·매각·지급 및 기존 거래 개시와 대조합니다. 관리 부모를 실행 업무로 등록하지 않습니다.',
 'CANDIDATE-ServiceDomain:38742#0':'대주 지위 양도와 경제적 참여분 매각은 등록했습니다. §2.9의 회전 신용약정 종료는 전체 대출채무 소멸·신디케이트 가입과 다릅니다. 약정 종료 책임과 기존 신용한도 계약의 미포함 결과를 판정하고 만기 상환·기관 수납을 각각 연결합니다.',
 'CANDIDATE-BusinessCapability:64574#0':'금융계정 승인·감시·정확성 검증의 책임·독립 완료 조건을 실제 금융계정 통제 절차로 분해하고 지급지시 승인·계좌 대조에 미포함된 결과를 판정합니다.',
}
closed_links={
 'INPUT-lending-trade-invoice financing advance-draw-51':[advance,'WGSS-DE4E23D3BB89'],
 'CANDIDATE-ServiceDomain:37104#0':[transfer],
 'CANDIDATE-ServiceDomain:48953#0':[nav],
 'CANDIDATE-BusinessCapability:64039#0':[dividend,'WGSS-C69BC3C2667A','WGSS-CA96597CD253'],
 'CANDIDATE-BusinessCapability:64436#0':[projection],
 'SOURCE-RESULT-REINSURANCE-RISK-DECISION':['WGSS-72879CC650A0','WGSS-6CA6BDD01105'],
 'SOURCE-RESULT-TREASURY-RATE-PUBLICATION':[rates,'WGSS-8080B7031AAB','WGSS-BACKBONE-FX-QUOTE'],
 'SOURCE-RESULT-MASTER-AGREEMENT-LIFECYCLE':[master],
 'SOURCE-RESULT-NETWORK-PARTICIPATION-LIFECYCLE':[schemechange,schemeend],
}
advice={}
for p in sorted((RUN/'reviews').glob('closure-tickets-*/*/proposal.json')):
    d=read(p)
    for row in d['result']['rows']:advice[row['id']]={'job_id':d['job_id'],'prompt_sha256':d['prompt_sha256'],'decision':row['decision']}
assert len(advice)==14
rows=[];remaining=[]
for ticket in read(RUN/'tickets.json'):
    i=ticket['id'];closed=i in closed_links
    reason=open_reasons.get(i,'공식 기능 조항과 현재 전체 정의를 대조하여 독립 결과를 등록하거나 기존 기능의 범위를 명확히 했습니다. 원문 부모의 CE 판정은 별도입니다.')
    if i.endswith('38742#0'):reason+=' 대주 등록부 반영은 양도의 효력 조건으로 보존하며 별도 복제하지 않습니다. §2.9·§2.10의 약정 종료·차주 만기 상환·대주별 수납 기록은 기존 결과의 조건·서비싱 범위로 연결합니다.'
    if i.endswith('64436#0'):reason+=' 미래 금액과 확률분포는 방법·산출 형태로 합칩니다. 전망 목적과 현재 평가 목적의 차이를 유지합니다.'
    if i.endswith('NETWORK-PARTICIPATION-LIFECYCLE'):reason+=' 자발적·강제 종료를 같은 관계 종료의 원인 변형으로 보존합니다. 잔존 의무 이행이라는 복합 부모를 추가하지 않습니다. 양자 변경 합의·정지 해제·공적 인허가는 이 원문에서 입증된 결과로 주장하지 않습니다.'
    rows.append(dict(id=i,state='closed_root_decision' if closed else 'pending_source_boundary',work_ids=closed_links.get(i,[]),reason=reason,model_advice=advice[i],automatic_adoption=False,independent_human_review=False))
    if not closed:remaining.append({k:v for k,v in ticket.items() if k!='sections'}|dict(reason=reason,next_action=reason))
# Extra responsibilities encountered in complete primary sources are visible
# source-coverage followups, never silently counted as solved local tickets.
followups=[
 dict(id='V20-CE-INVOICE-FACILITY',title='송장금융 추가 책임',next_action='HSBC 안내의 가용액·리텐션 산정, 추심대리 관계, 채권 환매, 대조 보고·담보·보증·약정 변경을 기존 직접 결과와 대조해 포함·누락·명시 제외를 판정합니다.',source_ids=['HSBC_INVOICE_DISCOUNTING']),
 dict(id='V20-CE-CONTRACT-LIFECYCLE',title='마스터·카드망 약정 추가 책임',next_action='마스터 전체 종료·개별 거래 확인, 카드망 참가권 정지 해제·양자 변경·공적 인허가와 종료 후 카드 취소·통지·미지급 의무를 원문 및 기존 결과와 대조합니다. 부재한 조항을 기능으로 추정하지 않습니다.',source_ids=['ISDA_AMICUS_MASTER_AMENDMENT','MASTERCARD_PARTICIPATION_SELECTED']),
 dict(id='V20-CE-FUND-INSURANCE',title='펀드·재보험 추가 책임',next_action='일반 펀드 정책·시리즈 종료와 재보험 용량 배분 등 추가 책임의 독립성·직접 근거를 대조합니다. Class 비용 배분을 Series 책임재산 격리로 확대하지 않습니다.',source_ids=['SEC_FUND_DECLARATION_SELECTED','SWISS_RE_UNDERWRITING']),
]
v20=dict(version='WGSS-root-dispositions-v20-20261011',input_version=before['version'],output_version=version,rows=rows,remaining_work=remaining,added_work_ids=[w['id'] for w in new],edited_work_ids=[e['id'] for e in edits],source_dispositions=[],source_followups=followups,automatic_adoption=False,independent_human_review=False,global_mece_approved=False,
 root_corrections=['역사적·조건부 공식 기능 원문을 편집 정의 근거로 인정하되 현재 계약·법적 보편성·UI 증거로 승격하지 않습니다.','시리즈별 자산·채무 격리를 Class별 비용 배분까지 확대하지 않습니다.','미래 예상가치와 확률분포를 방법·양 차이로 별도 집계하지 않습니다.','자발적·강제 종료 관점 복제 및 잔존 의무라는 복합 결과 부모를 거절합니다.','최종 승인·독립 인적 검토·특정 금융사 실서비스를 주장하는 모델 제안을 수락하지 않습니다.'])
write(ROOT/'data/mece-v20-root-dispositions.json',v20)
write(ROOT/'data/mece-closure-review.json',progress)
print(json.dumps(dict(added=len(new),edited=len(edits),closed=len(closed_links),pending=len(remaining),current=382+len(new))))
