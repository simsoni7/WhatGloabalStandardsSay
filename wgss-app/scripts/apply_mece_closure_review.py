"""Apply explicit root-reviewed v1.7 decisions, not arbitrary model output."""
import copy, json
from pathlib import Path
from run_mece_closure import ROOT, RUN, read, write

ledger = read(ROOT / 'data/operation-backbone-dispositions.json')
assert ledger['new_version'] == 'WGSS-operation-v1.6-review-20261004', 'One-time reviewed migration'
current = read(ROOT / 'dist/data/operations.json')
by = {w['id']: w for w in current['works']}
decisions = []

def proposal(job):
    files = list((RUN / 'reviews' / job).glob('*/proposal.json'))
    assert len(files) == 1
    return read(files[0])['result']

def evidence_refs(job, evidence):
    refs = []
    input_data = read(RUN / 'inputs' / (job + '.json'))
    for q in evidence:
        sid = q['section_id'].split(':')[0]
        assert q['quote'] in input_data['sections'][q['section_id']]
        if sid == 'BIAN':
            native = q['section_id'].split(':')[1]
            sections = [s for r in input_data['input']['references'] for s in r['own_sections']]
            sections += [s for r in input_data['input']['references'] for c in r['related_source_context'] for s in c['sections']]
            s = next(s for s in sections if s['section_id'] == q['section_id'])
            source_id = 'BIAN:14.0.0:portal:' + native
            ref = {'id': source_id, 'name': s['name'], 'url': s['source_url'], 'locator': s['source_locator'],
                   'source_snapshot_id': 'BIAN-14-public-portal-2026-10-02', 'source_sha256': s['source_file_sha256']}
        else:
            s = read(RUN / 'sources' / (sid + '.json'))
            source_id = 'WGSS-PROCESS-' + sid
            ref = {'id': source_id, 'name': sid.replace('_', ' '), 'url': s['url'], 'locator': q['section_id'],
                   'source_snapshot_id': 'WGSS-primary-process-20261005', 'source_sha256': s['sha256']}
        ref.update(rationale=q.get('claim', '책임·직접 결과 원문 대조'), exact_quote=q['quote'],
                   context_requires_review=False, proof_scope='specified_process_not_global_right_or_ui_capture')
        if not any(r['id'] == ref['id'] and r['locator'] == ref['locator'] for r in refs):
            refs.append(ref)
    return refs

def edit(work_id, fields, job, evidence, reason):
    previous = by[work_id]
    patch = copy.deepcopy(fields)
    patch.pop('boundary_distinction', None)
    patch['refs'] = previous['refs'] + evidence_refs(job, evidence)
    patch['source_gaps'] = []
    patch['review_note'] = reason
    patch['status'] = 'edited'
    ledger['edits'].append({'id': work_id, 'fields': patch, 'reason': reason,
                           'phase': 'mece-closure-v17-root-review', 'automatic_adoption': False})
    decisions.append({'work_id': work_id, 'decision': 'corrected_edit', 'job_id': job,
                      'reason': reason, 'evidence': evidence, 'automatic_adoption': False})

credit = {r['id']: r for r in proposal('definition-credit')['rows']}
for work_id in ['WGSS-9A4B541DD443', 'WGSS-9EAFFE368698']:
    row = credit[work_id]
    fields = row['fields']
    fields['actor_role'] = 'credit_facility_holder'
    fields['boundary'] = {'related_ids': ['WGSS-CB2F5FE40642', 'WGSS-671FA819885C', 'WGSS-779616C3F2C3'],
                          'distinction': '고객 요청 제출과 은행의 심사·약정 변경·한도 종료는 별도 결과입니다. 차입 한도와 송금 거래한도를 구별합니다.'}
    fields['applicability_conditions'] = ['HSBC UK의 약정 당좌대월 관리 절차를 직접 근거로 합니다. 다른 시장·상품의 요청 경로와 완료 조건은 별도로 확인합니다.']
    edit(work_id, fields, 'definition-credit', row['evidence'], '요청 제출이 공식 절차에 명시되어 결과를 요청으로 한정합니다. 해지·승인·잔여채무 정산 완료를 주장하지 않습니다.')

boundary = proposal('boundary-criterion-review')
rows = {r['id']: r for r in boundary['rows']}
for work_id in ['WGSS-16DACF2B667D', 'WGSS-77BA8EDACD11', 'WGSS-ECD7907DE4BA', 'WGSS-4E2F205250BC', 'WGSS-72879CC650A0', 'WGSS-B41573DD9A49']:
    row = rows[work_id]
    fields = copy.deepcopy(row['fields'])
    fields['boundary'] = copy.deepcopy(by[work_id]['boundary'])
    fields['boundary']['distinction'] = row['reason']
    if work_id == 'WGSS-16DACF2B667D':
        fields['outcome_key'] = 'request_fund_drawdown'
        fields['applicability_conditions'] = ['既存 약정 신용한도에서 차입자의 별도 이용 요청이 존재하는 경우입니다.'.replace('既存', '기존'), 'HSBC의 취소불능·신청 기한은 해당 계약 조건이며 전 세계 공통 요건이 아닙니다.']
        invoice = 'lending-trade-invoice financing advance-draw-51'
        fields['input_ids'] = [i for i in by[work_id]['input_ids'] if i != invoice]
        ledger.setdefault('input_mapping_overrides', []).append({'input_id': invoice, 'work_ids': [],
             'state': 'unresolved_source_relationship', 'reason': '매출채권 매각 선지급과 차입자 한도 이용 요청은 직접 대상·책임이 다릅니다. 옛 병합을 해제하고 금융 구조별 원문 판정을 보존합니다.'})
    if work_id == 'WGSS-77BA8EDACD11':
        fields['applicability_conditions'] = ['보험계약 관리 권한 범위에서 수행하는 이력정보 조회입니다. 고객의 보편적 법정 열람권을 주장하지 않습니다.']
    if work_id == 'WGSS-B41573DD9A49':
        fields['layer'] = 'customer'
        fields['outcome_key'] = 'establish_self_custody_wallet_key_control'
        fields['definition'] = '지갑 이용자가 비밀복구구문 등 개인키 통제수단을 초기 확보하여 자가보관 책임과 해당 지갑의 서명 통제 능력을 갖추는 업무. 자산 잔액의 존재·법적 소유권·거래 완료를 뜻하지 않습니다.'
        fields['excludes'] += ['토큰 취득·자산 이전 완료', '앱 설치·계정 레코드 생성·주소 계산 자체', '키 분실 후 접근 복구 및 기존 키 교체']
        fields['refs'] = []
        # VASP glossary is unsuitable process evidence for a holder's self-custody setup.
        by[work_id] = {**by[work_id], 'refs': [r for r in by[work_id]['refs'] if r['id'].startswith('ISO20022:')]}
        fields['applicability_conditions'] = ['자가보관 키 통제 설정에 한정합니다. 소셜 로그인·제3자 수탁·임계서명은 통제 주체를 별도로 확인합니다.']
    edit(work_id, fields, 'boundary-criterion-review', row['evidence'], row['reason'])

def add(work_id, category, layer, fields, job, evidence, related, reason):
    w = {'id': work_id, 'category': category, 'layer': layer, 'actor_label': fields['actor_role'],
         **fields, 'outcome': fields['outcome_key'].replace('_', ' '),
         'boundary': {'related_ids': related, 'distinction': reason}, 'refs': evidence_refs(job, evidence),
         'status': 'edited', 'review_note': reason, 'source_gaps': [], 'input_ids': [],
         'origin_unit_id': 'MECE-CLOSURE-' + work_id, 'definition_is_wgss_editorial': True,
         'independent_human_review': False, 'mece_approved': False}
    ledger['additions'].append(w)
    decisions.append({'work_id': work_id, 'decision': 'source_checked_addition', 'job_id': job,
                      'reason': reason, 'evidence': evidence, 'automatic_adoption': False})

acceptance = boundary['new_candidates'][0]
fields = {k: acceptance[k] for k in ['title', 'actor_role', 'object_key', 'outcome_key', 'discriminator', 'definition', 'includes', 'excludes']}
fields['title'] = '보험 청약 승낙에 의한 계약 성립'
fields['outcome_key'] = 'form_insurance_contract_by_acceptance'
fields['includes'] = ['보험자의 승낙 의사표시에 따른 보험계약 성립']
fields['definition'] = '보험자가 청약자의 가입 의사표시를 승낙하여 보험계약의 합의가 성립하는 업무. 내부 위험평가 결과와 계약을 증명하는 문서 발행을 구별합니다.'
fields['applicability_conditions'] = ['한국 상법의 간주승낙·기간 계산·사고 책임은 해당 요건을 별도로 확인합니다. 기간 경과 자체를 새 업무로 집계하지 않습니다.']
add('WGSS-MECE-INSURANCE-ACCEPTANCE', 'insurance-pensions', 'institution', fields,
    'boundary-criterion-review', acceptance['evidence'], acceptance['nearest_work_ids'], acceptance['boundary'])

scope_rows = {r['reference_key']: r for r in proposal('scope-gap-boundary-review')['rows']}
tax = scope_rows['ServiceDomain:42252']
fields = {'title': '고객 금융자문 권고안 제공', 'object_key': 'customer_financial_advisory_recommendation',
          'definition': '금융자문 담당자가 고객의 투자·자금조달·세무 등 금융 과제에 관한 구체적 권고안을 작성하여 제공하는 업무. 개인·기업과 자문 주제는 적용 조건이며 같은 권고 제공 결과를 중복 집계하지 않습니다.',
          'includes': ['고객 대상 금융 권고안 산출·전달', '개인·법인의 상품 선택·투자·재무구조·세무 최적화 권고'],
          'excludes': ['전문가 배정·일정 관리', '세금 신고·원천징수 집행', '고객 재무목표 자체 수립', '기존 계획의 성과 판정'],
          'boundary': {'related_ids': ['WGSS-CLOSE-B834C8689F3C', 'WGSS-D5AB29B67DCA'],
                       'distinction': '권고안 제공과 목표 정의·성과 평가·사실 증명서 발급은 직접 결과가 다릅니다.'}}
edit('WGSS-1EF9D68BA7E7', fields, 'scope-gap-boundary-review', tax['evidence'],
     '이미 병합한 개인·법인·세무 자문을 제목·정의에도 반영합니다. 자문 주제별 복제 항목을 만들지 않습니다.')

specs = [
 ('ServiceDomain:32532', 'WGSS-MECE-PRODUCT-CONDITIONS', 'accounts-deposits', 'customer', 'customer',
  ['공개 금융상품 기능·가격·자격 요건 안내정보 획득'], ['고객별 가입자격 판정', '개인별 여신 제안조건', '보유 상품 목록', '금융기관 내부 운영 요건 관리']),
 ('ServiceDomain:32825', 'WGSS-MECE-CUSTOMER-INVOICE', 'institution-processing', 'institution', 'financial_service_billing_operator',
  ['확정 수수료·요금에 대한 고객 청구서 발행'], ['수수료 금액 확정', '수납 대조', '과거 거래명세 제공', '연체채권 추심·독촉', '자사 물품 조달 비용 처리']),
 ('BusinessCapability:63944', 'WGSS-MECE-FINANCIAL-GOAL', 'investments-custody', 'institution', 'financial_planning_provider',
  ['고객 재무목표 결정·정의'], ['투자·세무 등 구체적 권고안 제공', '실행 계획 수립', '기존 계획의 성과 판정', '포트폴리오 운용지침 합의']),
]
for refkey, work_id, category, layer, actor, includes, excludes in specs:
    row = scope_rows[refkey]
    fields = {k: row['fields'][k] for k in ['title', 'object_key', 'outcome_key', 'discriminator', 'definition']}
    fields.update(actor_role=actor, includes=includes, excludes=excludes)
    if work_id == 'WGSS-MECE-CUSTOMER-INVOICE':
        fields['definition'] = '금융서비스 요금 청구 담당자가 이미 확정된 수수료·요금에 대한 지급청구 문서를 고객에게 발행하는 업무. 독촉·추심과 실제 지급·수납을 포함하지 않습니다.'
    evidence = [q for q in row['evidence'] if q['quote'] != 'TBD']
    add(work_id, category, layer, fields, 'scope-gap-boundary-review', evidence, [], row['reason'])

ledger['new_version'] = 'WGSS-operation-v1.7-review-20261005'
ledger['audit_summary']['mece_closure_v17'] = {'six_pending_definitions_source_adjudicated': True, 'semantic_me_approved': False,
                                             'scope_ce_approved': False, 'root_decision_count': len(decisions)}
write(ROOT / 'data/operation-backbone-dispositions.json', ledger)
nav = read(ROOT / 'data/business-backbone-review.json')
nav['version'] = 'WGSS-backbone-v1.7-20261005'
nav['operation_version'] = ledger['new_version']
for work_id, family in [('WGSS-MECE-INSURANCE-ACCEPTANCE', 'insurance'), ('WGSS-MECE-PRODUCT-CONDITIONS', 'customer'),
                        ('WGSS-MECE-CUSTOMER-INVOICE', 'customer'), ('WGSS-MECE-FINANCIAL-GOAL', 'securities')]:
    nav['assignments'].append({'id': work_id, 'family_id': family, 'ambiguous': False, 'reason': '직접 대상·결과의 주 분류'})
write(ROOT / 'data/business-backbone-review.json', nav)
profiles = read(ROOT / 'data/product-profiles-review.json')
profiles['version'] = 'WGSS-products-v1.7-20261005'
for p in profiles['product_profiles']:
    for s in p['steps']:
        candidates = s.get('review_candidate_ids', [])
        if 'WGSS-16DACF2B667D' in candidates:
            s['review_candidate_ids'] = [i for i in candidates if i != 'WGSS-16DACF2B667D']
            # An already-proven facility request does not prove that a Korean
            # lump-sum loan has a separate request step. Keep the product gap.
            s['gap'] = '별도 약정 한도 이용 요청이 있는 상품에만 적용됩니다. 해당 국내 상품이 신청·약정과 별도의 인출 요청을 받는지는 업체 원문을 확인해야 합니다.'
            s['mapping_note'] = '약정 신용한도 이용 요청과 실제 자금 지급을 구분합니다. 일시대출·매출채권 매각을 요청 단위로 자동 연결하지 않습니다.'
        if 'WGSS-9EAFFE368698' in candidates:
            s['review_candidate_ids'] = [i for i in candidates if i != 'WGSS-9EAFFE368698']
            s['work_ids'] = ['WGSS-9EAFFE368698']
            s['gap'] = '고객의 차입 한도 변경 요청이라는 결과로 연결합니다. 해당 한국 상품의 요청 경로·조건은 별도 업체 원문 확인이 필요합니다.'
            s['mapping_note'] = 'HSBC UK 공식 관리 절차로 요청·승인·약정 변경의 결과를 구분했습니다. 국내 업체 기능 증거로 표시하지 않습니다.'
        if not s.get('review_candidate_ids'):
            s.pop('review_candidate_ids', None)
write(ROOT / 'data/product-profiles-review.json', profiles)
write(ROOT / 'data/mece-closure-review.json', {'version': 'WGSS-mece-closure-v17-20261005',
      'input_version': current['version'], 'output_version': ledger['new_version'], 'root_decisions': decisions,
      'automatic_adoption': False, 'independent_human_review': False, 'global_mece_approved': False,
      'completed_gates': [], 'source_dispositions': [], 'semantic_dispositions': [], 'remaining_work': []})
print(json.dumps({'root_decisions': len(decisions), 'additions': 4, 'automatic_adoption': False}))
