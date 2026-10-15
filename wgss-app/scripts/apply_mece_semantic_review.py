"""One-time, explicitly curated semantic corrections after the 368-row audit."""
import copy, hashlib, json
from pathlib import Path
from run_mece_closure import ROOT, RUN, read, write

ledger = read(ROOT/'data/operation-backbone-dispositions.json')
review = read(ROOT/'data/mece-closure-review.json')
assert not review.get('semantic_patch_applied'), 'One-time reviewed migration'
by = {w['id']: w for w in read(ROOT/'dist/data/operations.json')['works']}
changes = []

def proof(sid, start, end=None):
    meta = read(RUN/'sources'/ (sid+'.json'))
    text = (RUN/'sources'/meta['text_path']).read_text()
    pos = text.index(start)
    quote = text[pos:text.index(end, pos)] if end else start
    return dict(id='WGSS-PROCESS-'+sid, name=sid.replace('_',' '), url=meta['url'],
                locator=f'{meta["text_path"]} / character {pos}', exact_quote=quote,
                source_snapshot_id='WGSS-primary-process-20261005', source_sha256=meta['sha256'],
                rationale='책임·직접 결과의 원문 대조', context_requires_review=False,
                proof_scope='specified_regional_process_not_global_right_or_ui_capture')

def edit(i, reason, evidence=None, **fields):
    if evidence:
        fields['refs'] = by[i]['refs'] + evidence
    fields['review_note'] = reason
    ledger['edits'].append(dict(id=i, fields=fields, reason=reason,
                               phase='mece-closure-v17-semantic-root-review', automatic_adoption=False))
    by[i].update(copy.deepcopy(fields))
    changes.append(dict(work_id=i, decision='corrected_edit', reason=reason,
                        changed_fields=list(fields), automatic_adoption=False))

def merge(old, dest, reason):
    ledger['merges'].append(dict(from_=old, into=dest, reason=reason))
    ledger['merges'][-1]['from'] = ledger['merges'][-1].pop('from_')
    changes.append(dict(work_id=old, decision='merged', target_ids=[dest], reason=reason, automatic_adoption=False))

def context(i, dest, reason):
    ledger['noncountable_contexts'].append(dict(id=i, targets=dest, reason=reason))
    changes.append(dict(work_id=i, decision='noncountable_context', target_ids=dest, reason=reason, automatic_adoption=False))

# Caller and verifier labels cannot manufacture two identical authentication results.
merge('WGSS-992EB3CF75F6', 'WGSS-E8145840821E', '두 항목 모두 비대면 카드거래에 대한 3DS 인증결과를 뜻합니다. 고객의 별도 응답 제출 결과를 입증하지 않은 상태에서 관점만으로 두 번 집계하지 않습니다.')
edit('WGSS-E8145840821E', '3DS 인증결과와 발급사의 금전거래 승인·서비스 로그인 세션을 구분합니다.',
     actor_role='card_transaction_authentication_provider', layer='institution',
     excludes=by['WGSS-E8145840821E']['excludes']+['발급사의 카드거래 승인·거절', '일반 서비스 로그인 세션 성립', '인증정보 입력 화면·요청 라우팅 자체'])
merge('WGSS-1B39BB0943F9', 'WGSS-DD4FB57556AA', 'BIAN Card Network Participant Facility의 직접 결과는 정산지시 발행입니다. 실행이라는 이름만으로 실제 은행 자금이전과 같은 결과를 추가 집계하지 않습니다.')
edit('WGSS-DD4FB57556AA', '망의 정산지시 발행을 은행의 자금이전·매입사의 가맹점 지급과 분리합니다.',
     definition='카드망 정산 담당자가 기간별 클리어링 결과에 따라 발급사와 매입사에 순액·총액 정산지시를 발행하는 업무.',
     excludes=by['WGSS-DD4FB57556AA']['excludes']+['발급·매입은행의 실제 자금이전', '가맹점에 대한 매입사 대금 지급'])
merge('WGSS-1A4E02C9F8A5', 'WGSS-CCF615A45814', '현재 정의는 모두 가입자가 연금 투자배분 지시를 확정하는 결과입니다. 신규 부담금·기존 적립금이라는 적용 대상을 보존하고 같은 지시를 중복 집계하지 않습니다. 실제 매매 실행은 별도입니다.')
edit('WGSS-CCF615A45814', '신규 부담금과 기존 적립금 배분은 같은 결과의 적용 조건으로 보존합니다. ISO 개념 연결을 개별 업체의 실행 절차 증거로 승격하지 않습니다.',
     title='연금 투자배분 지시 확정', object_key='pension_investment_allocation_instruction',
     outcome_key='confirm_pension_investment_allocation_instruction',
     definition='연금 가입자가 신규 부담금 또는 기존 적립금에 대해 투자대상과 배분 비율을 선택하여 지시를 확정하는 업무.',
     includes=['신규 부담금의 투자대상·비율 지시', '기존 적립금의 투자배분 변경 지시'],
     excludes=['부담금 납부', '운용기관의 실제 펀드 매매·결제', '계약·법령상 선택권이 없는 가입자의 지시'])

# A broad dispute workflow and a mandatory account identifier are navigation context.
context('WGSS-0C78B43732B6', ['WGSS-B3C21A43D010','WGSS-7B8A6581BE10'],
        '접수부터 판정까지를 포괄하는 분쟁 처리 부모입니다. 접수와 판정은 각각 집계하고 그 전 과정을 세 번째 결과로 더하지 않습니다.')
context('WGSS-3E112BE4FCB7', ['WGSS-90894A4B1D44','WGSS-FBFE37ED9D15'],
        '공급된 AccountIdentification은 식별 속성입니다. 계좌와 무관한 독립 식별자 발급 책임·결과가 입증되지 않아 계좌 개설·가상계좌 생성의 문맥으로 보존합니다.')

# Privacy consent has its own normative object; payment acceptance is not its source.
consent = proof('EC_CONSENT', 'When is consent valid?', 'For consent to be informed')
for i, title, result, direction in [
    ('WGSS-CE6010277573','개인정보 처리 동의 부여','grant_personal_data_processing_consent','부여'),
    ('WGSS-9798312430EF','개인정보 처리 동의 철회','withdraw_personal_data_processing_consent','철회')]:
    refs = [r for r in by[i]['refs'] if not r['id'].endswith(':41780')]+[consent]
    edit(i, '유럽위원회의 정보주체 동의·철회 안내로 교체합니다. 지급 동의와 다른 직접 대상이며 기록 담당자가 이용자를 대신해 동의하는 업무가 아닙니다.',
         title=title, actor_role='data_subject', layer='support', object_key='personal_data_processing_consent',
         outcome_key=result, discriminator='personal_data_processing_not_payment_authority', refs=refs,
         definition=f'정보주체가 특정 목적의 개인정보 처리에 대한 동의를 {direction}하는 업무. 동의를 법적 근거로 사용하는 처리와 해당 시장의 법적 요건에 한정합니다.',
         includes=[f'특정 목적의 개인정보 처리 동의 {direction}'],
         excludes=['지급·출금·계좌 접근 수권', '동의 외의 근거에 따른 개인정보 처리', '모든 개인정보의 자동 삭제', '관리자의 단순 기록 수정'],
         applicability_conditions=['GDPR가 적용되는 처리의 동의 요건을 직접 근거로 합니다. 다른 시장과 다른 적법 처리 근거는 별도 확인합니다.'])

eligible = proof('ECB_COLLATERAL_ELIGIBILITY', 'national central banks (NCBs) proactively assess', 'If a marketable asset does not appear')
edit('WGSS-D8EDFDFBAFAC', '원문은 담보 수용 적격성 평가를 독립 책임으로 정의합니다. 기존 가치평가·권리문서 확인과 겹치던 범위를 제거합니다.', [eligible],
     title='담보자산 수용 적격성 판정', actor_role='collateral_eligibility_assessor', object_key='proposed_collateral_asset',
     outcome_key='determine_collateral_asset_eligibility',
     definition='담보 적격성 심사자가 제시된 자산이 해당 담보 수용 기준을 충족하는지 판정하는 업무.',
     includes=['담보 수용 기준 충족 여부 판정'],
     excludes=['자산의 평가금액 산출', '소유권·담보권 문서 확인', '헤어컷 적용 후 인정금액 산출', '담보권 설정·배분'],
     applicability_conditions=['ECB/유로시스템 시장성 자산 적격성 절차를 직접 근거로 합니다. 구체적 기준은 해당 제도 조건입니다.'])

edit('WGSS-4F358B4315C3', '사기 책임귀속 판정과 환불·정정 집행은 각각 실패할 수 있습니다. 이 항목은 판정만 남기고 금전 집행은 기존 지급·반전 결과로 연결합니다.',
     title='사기 사건 책임귀속 판정', object_key='financial_fraud_case', outcome_key='adjudicate_fraud_liability',
     definition='사기 사건 해결 담당자가 조사 결과를 바탕으로 금전 손실에 대한 책임귀속을 판정하는 업무.',
     includes=['사기 손실 책임귀속 판정'], excludes=['사기 의심 신호 탐지', '고객 진위확인 응답 수령', '환불·지급·기장 반전 집행'])
edit('WGSS-69483AED45F1', '고객에게 확인하고 응답을 받는 결과와 최종 사기 판정은 같지 않습니다.',
     outcome_key='receive_customer_fraud_confirmation_response',
     includes=['의심 거래에 대한 고객 확인 응답 수령'],
     excludes=by['WGSS-69483AED45F1']['excludes']+['최종 사기 여부 판정', '책임귀속 판정', '환불 집행'])

# Correct responsibility where the retained process explicitly names the provider.
for i, actor in [('WGSS-B947CF3FC565','account_servicer'),('WGSS-BA69A55FB47D','cheque_collection_processor'),
                 ('WGSS-C28BA1C1D0B3','card_issuer'),('WGSS-EFEFBF6B2926','card_issuer'),
                 ('WGSS-28DC9D33B898','insurance_quote_provider'),('WGSS-816438C402A9','insurer')]:
    edit(i, '최종 실행·판정 결과를 담당하는 제공자 역할로 교정합니다. 고객의 요청 제출과 최종 결과를 혼동하지 않습니다.',
         actor_role=actor, layer='institution', excludes=by[i]['excludes']+['고객의 요청 제출만 완료된 상태'])
edit('WGSS-647DCADA33FC', '신청 제목·가입자 역할과 결과를 요청 제출로 일치시킵니다. 신청은 기관의 인출 승인이나 실제 지급이 아닙니다.',
     outcome_key='submit_pension_early_withdrawal_request',
     definition='연금 가입자가 제도·계약에서 허용하는 중도인출을 요청하는 업무. 접수된 요청에 대한 제공자의 승인이나 실제 지급을 뜻하지 않습니다.',
     includes=['연금 중도인출 요청 제출'], excludes=['기관의 중도인출 승인', '실제 자금 지급', '허용요건 없는 인출권 부여'])
edit('WGSS-89CB90A2150D', '해지에 따른 반환권 확정과 보험자의 실제 환급금 지급을 한 결과로 세지 않습니다.',
     outcome_key='terminate_policy_and_determine_surrender_entitlement',
     definition='보험계약 당사자가 보험계약을 해지하여 계약의 종료 및 약정상 해약환급 권리를 확정하는 업무.',
     includes=['보험계약 해지 성립', '해지에 따른 약정상 환급권 확정'],
     excludes=['환급금의 실제 지급', '청약철회', '단순 해지 요청 접수'])
edit('WGSS-70AA5703F3A4', 'Economic Capital 원문의 기관 통합 위험자본 산출로 한정하고 개별 ALM·트레이딩 위험 판정을 제외합니다.',
     object_key='institution_aggregate_economic_capital_requirement', outcome_key='calculate_institution_economic_capital',
     definition='기관 위험 담당자가 복수 위험을 결합하여 금융기관의 경제적 자본 요구량을 산출하는 업무.',
     includes=['기관 통합 위험에 대한 경제적 자본 요구량 산출'],
     excludes=['개별 유동성·금리 위험 산출', '트레이딩 포지션 위험 산출', '고객 통합 재무포지션 조회'])
edit('WGSS-C69BC3C2667A', '권리배정 산출과 별도 수수료 결정 결과를 분리합니다.',
     outcome_key='calculate_corporate_action_entitlement',
     includes=['기업행위에 따른 배정 수량·지급금액 산출'],
     excludes=by['WGSS-C69BC3C2667A']['excludes']+['별도의 금융서비스 수수료 확정'])
edit('WGSS-D078BF76895D', '마감일은 통지의 적용 조건이며 독립 금융 결과로 추가 집계하지 않습니다.',
     outcome_key='deliver_corporate_action_notification',
     includes=['기업행위 정보 및 적용 마감일 통지'], excludes=by['WGSS-D078BF76895D']['excludes']+['선택권 행사지시 확정', '실제 권리배정·지급'])
edit('WGSS-F03A4C08E46B', '담보권 소멸과 기관의 계좌거래 제한 해제는 직접 대상이 다릅니다.',
     includes=['예금계좌 질권 소멸 확정'], excludes=by['WGSS-F03A4C08E46B']['excludes']+['별도 계좌거래 제한 해제'])
for i, parent in [('WGSS-BD3D94D4FCF9','살람'),('WGSS-3E98F2AAAA13','이스티스나')]:
    edit(i, '병합 입력의 병행 계약을 excludes에서 다시 누락시키던 모순을 제거합니다. 별도 상대방과의 계약별 독립성은 적용 조건으로 보존합니다.',
         includes=by[i]['includes']+[f'별도 상대방과 독립 체결하는 병행 {parent} 계약'],
         excludes=[e for e in by[i]['excludes'] if 'parallel' not in e.lower() and '병행' not in e])
edit('WGSS-EFF17F1D2D6F', '투자자의 청약 제출과 기관의 배정·보유기록 생성은 다른 책임과 결과입니다.',
     outcome_key='submit_sukuk_subscription_order',
     includes=['수쿠크 투자 청약 지시 제출'], excludes=['발행기관의 배정 확정', '실제 취득·결제', '보유기록 생성·관리'])

review['semantic_patch_applied'] = True
review['root_decisions'].extend(changes)
write(ROOT/'data/operation-backbone-dispositions.json', ledger)
write(ROOT/'data/mece-closure-review.json', review)

# Rebase explicit navigation and product links; merges never create new source proof.
aliases = {r['from']: [r['into']] for r in ledger['merges']}
aliases.update({r['id']: r['targets'] for r in ledger['noncountable_contexts']})
def resolve(i):
    return list(dict.fromkeys(t for j in aliases[i] for t in resolve(j))) if i in aliases else [i]
nav = read(ROOT/'data/business-backbone-review.json')
nav['assignments'] = [a for a in nav['assignments'] if a['id'] not in aliases]
for g in nav['goals']:
    for field in ['canonical_work_ids','optional_work_ids']:
        g[field] = list(dict.fromkeys(t for i in g[field] for t in resolve(i)))
write(ROOT/'data/business-backbone-review.json', nav)
products = read(ROOT/'data/product-profiles-review.json')
for p in products['product_profiles']:
    for s in p['steps']:
        s['work_ids'] = list(dict.fromkeys(t for i in s['work_ids'] for t in resolve(i)))
write(ROOT/'data/product-profiles-review.json', products)
print(json.dumps({'root_changes':len(changes),'merges':3,'noncountable_contexts':2,'automatic_adoption':False}))
