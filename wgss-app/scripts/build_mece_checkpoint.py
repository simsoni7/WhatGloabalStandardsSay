"""Derive a finite, inspectable closure queue from retained review evidence."""
import collections,hashlib
from run_mece_closure import ROOT,RUN,read,write

progress=read(ROOT/'data/mece-closure-review.json')
data=read(ROOT/'dist/data/operations.json');by={w['id']:w for w in data['works']}
root={r['work_id']:r for r in progress['root_decisions']}
initial=[]
baseline_jobs={
    'semantic-institution-processing','semantic-identity-support','semantic-investments-custody',
    'semantic-lending-trade','semantic-islamic-virtual','semantic-insurance-pensions',
    *('semantic-accounts-split-'+str(n).zfill(2) for n in range(1,4)),
    *('semantic-payments-split-'+str(n).zfill(2) for n in range(1,5)),
}
for p in sorted((RUN/'reviews').glob('semantic-*/*/proposal.json')):
    name=p.parts[-3]
    if name not in baseline_jobs:continue
    d=read(p)
    initial.extend({**r,'job_id':d['job_id'],'prompt_sha256':d['prompt_sha256']} for r in d['result']['rows'])
assert len(initial)==368 and len({r['id'] for r in initial})==368

# These proposed defects were inspected against the actual objects/results. Null
# discriminators and contract viewpoints are not, by themselves, ME violations.
rejections={
 'WGSS-5F8FC967D676':'원문과 현재 객체는 여러 상품·채널에 공통인 권한 프로파일입니다. 단일 계좌 소유자의 거래한도와 구분됩니다.',
 'WGSS-COMPLETION-PREPAID-ENROLLMENT':'계약 당사자는 하나의 이용관계 성립을 공동 책임지는 역할입니다. 관점별로 새 결과를 만들지 않습니다.',
 'WGSS-41449688AD99':'지급인의 별칭 해석 결과는 기관의 계좌 유효성 판정·수취인 주소록 등록과 직접 대상·결과가 다릅니다.',
 'WGSS-53C0FF6152E8':'공동소유 구조의 성립은 권한 위임·계좌 연계와 다른 권리 결과입니다. 구분자 공란만으로 병합하지 않습니다.',
 'WGSS-0151053534AB':'기존 담보 구성·상태 조회는 새 평가금액 산출과 다른 정보 결과입니다. 관측 당사자의 시점 차이로 추가 집계하지 않습니다.',
 'WGSS-1AE2353F25AC':'ISO CollateralInterest 원문은 calculation and request를 직접 기술합니다. 청구 성립과 실제 지급은 다른 결과이며 구분자 공란만으로 결함으로 판정하지 않습니다.',
 'WGSS-7B8A6581BE10':'포괄 분쟁 처리 부모는 이미 집계에서 제외했습니다. 구속적 판정과 청구 접수의 독립 결과는 보존합니다.',
 'WGSS-8F752B8D2E89':'카드거래 생애주기 기록 조회는 기간 계좌명세서·통합포지션과 직접 대상·산출물이 다릅니다.',
 'WGSS-9637BC62C33D':'요청 제출과 발급사 승인 판단은 서로 다른 결과입니다. 제공 원문이 전자상거래라는 이유만으로 범용 개념의 대면 실행권을 주장하지 않습니다.',
 'WGSS-5E65EEAAD57A':'계좌 거래수권과 법적 대리 지위의 차이는 대리 지위 항목을 교정하여 보존했습니다.',
 'WGSS-BEA6E0F20512':'일시 정기예치의 성립과 적립식 예금 계약은 직접 의무·납입 구조가 다릅니다. 공란 구분자만으로 중복이라 판정하지 않습니다.',
 'WGSS-5A6BEBC2E6CB':'이슬람 윈도우의 자금 격리와 신탁관계 성립·혼입수익 정화는 직접 대상·권리 결과가 다릅니다.',
 'WGSS-7A0BD639A755':'보험계약 소유권 이전은 피보험자·수익자 변경과 직접 권리 대상이 다릅니다.',
 'WGSS-EE5A37EAB496':'참여기관의 인수지분 배분과 멤버십 성립은 독립 결과입니다. 관련 항목 목록이 짧다는 사실만으로 중복이 되지 않습니다.',
 'WGSS-15B2DC324B63':'보험료 납입의무 정지와 대출 원리금 지급유예는 같은 moratorium 용어를 쓰더라도 직접 채무가 다릅니다.',
 'WGSS-3C4A94A9E527':'신용보험 위험인수와 보증인의 지급확약은 직접 부담 의무가 다릅니다.',
 'WGSS-11940117C228':'등록명의 성립과 실질수익자 신고·증권 이동은 다른 권리·정보 결과입니다.',
 'WGSS-7944C767C173':'신탁관계 창설과 신탁계좌 생성·보관 인수는 직접 대상·책임·결과가 다릅니다.',
 'WGSS-F8C91C0AAA38':'BIAN 원문은 제3자 상품 이행의 조정을 금융중개 책임으로 명시합니다. 수수료 약정과 직접 결과가 다릅니다.',
}
actions={
 'WGSS-A876ACA7DC86':'보증·스탠바이와 화환신용장의 직접 의무를 원문으로 비교하고, 조건변경 2항목의 병합 또는 필수 구분자를 결정합니다.',
 'WGSS-F1BBF631D3AB':'보증·스탠바이와 화환신용장의 직접 의무를 원문으로 비교하고, 조건변경 2항목의 병합 또는 필수 구분자를 결정합니다.',
 'WGSS-3DFF635AF396':'리타카풀 참가자 기금과 재보험 출재자의 권리·위험이전 결과를 비교해 병합 여부를 결정합니다.',
 'WGSS-A3D3B2A84738':'담보 해지와 구별되는 증명서 발급 책임·절차의 공식 원문을 확보합니다.',
 'WGSS-AF6645904647':'투자일임 합의의 공동 책임 역할과 투자계좌·이슬람 투자계약의 결과 경계를 고정합니다.',
 'WGSS-F4E90272B38B':'증권대차 계약의 공유 성립 결과와 차입자·대여자 관점의 중복을 인접 계약 정의와 대조합니다.',
 'WGSS-3C503665EDE3':'리스 계약 종료와 담보권 해지·자산 반환의 독립 완료 조건을 분리합니다.',
 'WGSS-BB9E69AF7B7D':'연금 가입자의 신청과 관리기관의 가입 확정·자격 판정 책임을 원문으로 구분합니다.',
 'WGSS-EAB16CB1D4C4':'금융시장 분석의견과 금융기관 일반 사업분석의 입력·근거 연결을 정리합니다.',
 'WGSS-ADD-5CDA21892432':'보존된 OFAC 해제 원문의 조문·인용 앵커를 고정하고 내부정책 해제 조건의 증거 범위를 표시합니다.',
}
semantic=[];remaining=[]
for r in initial:
    i=r['id']
    if i in root:
        state=root[i]['decision'];reason=root[i]['reason']
    elif i in rejections:
        state='proposal_rejected_non_defect';reason=rejections[i]
    elif r['decision'].startswith('retain'):
        state='boundary_retained';reason=r['reason']
    else:
        state='pending_root_boundary_or_source';reason=r['reason']
        remaining.append(dict(id='SEMANTIC-'+i,kind='semantic_or_process_source',title=by.get(i,{}).get('title',i),
                              work_ids=[i] if i in by else [],reason=reason,
                              next_action=actions.get(i,'검토 제안과 현재 정의·원문을 대조해 수정 또는 반려 사유를 확정합니다.')))
    semantic.append(dict(id=i,state=state,reason=reason,job_id=r['job_id'],proposal_prompt_sha256=r['prompt_sha256'],
                         source_ce_approval=False,independent_human_review=False))
for i,w in by.items():
    if w['status']=='unresolved':
        remaining.append(dict(id='SOURCE-'+i,kind='unproven_responsibility',title=w['title'],work_ids=[i],
                              reason=w['review_note'],next_action='보험자 통지의무의 원문 근거를 찾거나, 입증되는 금융 분쟁 고지 책임으로 재정의합니다.'))
for gap in data['audit']['input_mapping_gaps']:
    remaining.append(dict(id='INPUT-'+gap['input_id'],kind='input_mapping',title=gap['input_id'],work_ids=gap['work_ids'],
                          reason=gap['reason'],next_action=('송장금융의 약정 원문에서 채권 매입·담보대출 구조와 요청·실제 선지급 결과를 구분하고, 한도 이용 요청·자금 지급·채권 매입 중 입증되는 결과로 연결합니다.' if gap['input_id'].startswith('lending-trade-') else 'BIAN 40508·46157에서 기관 통합 포지션 산출과 헤지 거래 개시를 분리하고, 고객 통합정보를 제외한 기존 기관 결과에 각각 대응시키거나 누락 결과를 추가합니다.')))

delta=[]
for p in sorted((RUN/'reviews').glob('semantic-delta-v17-*/*/proposal.json')):
    d=read(p);delta.extend({**r,'job_id':d['job_id']} for r in d['result']['rows'])
initial_pending={i for r in remaining for i in r['work_ids']}
for r in progress.get('delta_root_dispositions',[]):
    if r['state']=='pending_source_boundary' and r['id'] not in initial_pending:
        i=r['id']
        remaining.append(dict(id='DELTA-'+i,kind='semantic_or_process_source',title=by[i]['title'],work_ids=[i],
                              reason=r['reason'],next_action='집중이동과 장부이체의 금융 결과·원 약정을 원문으로 비교합니다.'))
v18_path=ROOT/'data/mece-v18-result-dispositions.json'
if v18_path.exists():
    v18=read(v18_path)
    candidates={r['id']:r for r in read(ROOT/'research/source-store/mece-closure-20261006/candidate-input.json')}
    former_ids={old:i for i,w in by.items() for old in w.get('former_work_ids',[])}
    for r in v18['rows']:
        if r['root_decision']!='pending_result_boundary':continue
        remaining.append(dict(id='CANDIDATE-'+r['id'],kind='candidate_result_boundary',
            title=candidates[r['id']]['proposal']['title'],work_ids=r['work_ids'],
            related_work_ids=list(dict.fromkeys(former_ids.get(i,i) for i in candidates[r['id']]['proposal'].get('nearest_work_ids',[]) if former_ids.get(i,i) in by)),
            reason=r['reason'],next_action=r['reason']))
    for r in v18['remaining_source_results']:
        remaining.append(dict(id='SOURCE-RESULT-'+r['id'],kind='candidate_result_boundary',title=r['title'],
                              work_ids=[],reason=r['reason'],next_action=r['reason']))
v19_path=ROOT/'data/mece-v19-root-dispositions.json'
if v19_path.exists():
    v19=read(v19_path)
    disposed={r['id'] for r in v19['rows']}
    # Replace only explicitly reviewed tickets; retain unrelated/new defects.
    remaining=[r for r in remaining if r['id'] not in disposed]+v19['remaining_work']
    assert all(r['next_action'].strip().lower() not in ['없음','none','closed',''] for r in remaining)
v20_path=ROOT/'data/mece-v20-root-dispositions.json'
if v20_path.exists():
    v20=read(v20_path)
    disposed={r['id'] for r in v20['rows']}
    remaining=[r for r in remaining if r['id'] not in disposed]+v20['remaining_work']
    progress['source_followups']=v20['source_followups']
    source_overlay={r['reference_key']:r for r in progress['source_dispositions']}
    source_overlay.update({r['reference_key']:r for r in v20['source_dispositions']})
    progress['source_dispositions']=list(source_overlay.values())
v21_path=ROOT/'data/mece-v21-root-dispositions.json'
if v21_path.exists():
    v21=read(v21_path)
    disposed={r['id'] for r in v21['rows']}
    remaining=[r for r in remaining if r['id'] not in disposed]+v21['remaining_work']
    progress['source_followups']=v21['source_followups']
    source_overlay={r['reference_key']:r for r in progress['source_dispositions']}
    source_overlay.update({r['reference_key']:r for r in v21['source_dispositions']})
    progress['source_dispositions']=list(source_overlay.values())
v22_path=ROOT/'data/mece-v22-root-dispositions.json'
if v22_path.exists():
    v22=read(v22_path)
    source_overlay={r['reference_key']:r for r in progress['source_dispositions']}
    source_overlay.update({r['reference_key']:r for r in v22['source_dispositions']})
    progress['source_dispositions']=list(source_overlay.values())
    progress['source_followups']=v22['source_followups']
    progress['v22_source_review']=v22['review']
    progress['standard_material_census']=v22['standard_material_census']
progress['semantic_dispositions']=semantic
progress['delta_model_reviews']=delta
progress['remaining_work']=remaining
progress['review_counts']=dict(initial_model_rows=len(initial),initial_unique_ids=len(semantic),
    root_change_count=len(root),root_action_count=len(progress['root_decisions']),semantic_pending_count=sum(r['kind']=='semantic_or_process_source' for r in remaining),
    root_source_rows=len(progress['source_dispositions']),source_reference_denominator=927,
    source_rows_not_root_adjudicated=927-len(progress['source_dispositions']),
    source_specification_gaps=sum(r['decision']=='source_specification_gap' for r in progress['source_dispositions']),
    source_partial_links=sum(r['decision']=='linked_partial' for r in progress['source_dispositions']),
    input_mapping_gap_count=len(data['audit']['input_mapping_gaps']),delta_model_rows=len(delta))
if v18_path.exists():
    progress['review_counts'].update(source_model_rows=progress['v18_source_model_review']['reviewed_rows'],
        source_issue_model_rows=progress['v18_source_model_review']['source_issue_rows'],
        candidate_hypotheses=len(v18['rows']),candidate_root_dispositions=len(v18['rows']),
        candidate_pending_count=sum(r['kind']=='candidate_result_boundary' for r in remaining),
        current_delta_model_rows=progress.get('v18_current_delta_root_dispositions',{}).get('reviewed_rows',0),
        v18_added_definitions=len(v18['separate_added_result_ids'])+sum(r['root_decision']=='registered_result' for r in v18['rows']))
if v19_path.exists():
    progress['review_counts'].update(v19_ticket_model_rows=len(v19['rows']),
        v19_closed_tickets=sum(r['state']=='closed_root_decision' for r in v19['rows']),
        v19_added_definitions=len(v19['added_work_ids']),
        v19_current_delta_rows=progress.get('v19_delta_review',{}).get('reviewed_rows',0))
    progress['execution_plan']=[
      dict(id='tickets',label='쟁점·종료 조건 고정',state='passed',done_when='각 쟁점에 원문·인접 정의·구체 작업·종료 조건을 기록',note=f'이번 쟁점 {len(v19["rows"])}개를 개별 판정했습니다.'),
      dict(id='atomic_results',label='독립 결과·중복 판정',state='pending',done_when='열린 의미 경계·입력 쟁점 0개',note=f'이번 쟁점 {progress["review_counts"]["v19_closed_tickets"]}개 종료 · 현재 열린 작업 {len(remaining)}개'),
      dict(id='source_disposition',label='BIAN 원문 전수 포함·제외 판정',state='pending',done_when='927개 노드의 원문 전체에 대한 판정·부분 결과 후속 처리 완료',note=f'root 판정 {len(progress["source_dispositions"])} / 927개. 노드 수는 업무 수가 아닙니다.'),
      dict(id='standards_scope',label='ISO·FIBO·NIST 보완 범위 판정',state='pending',done_when='현재 수록 범위와 비수록·선택 원문의 금융 결과 영향 판정 완료',note='수록 원문 ID·스냅샷 목록을 고정했습니다. ISO 프로세스·FIBO 비수록 관계·NIST 규범 결과의 영향 판정은 남았습니다.'),
      dict(id='meaning_and_coverage',label='전체 목록 ME·CE 재심',state='pending',done_when='변경 정의·인접 의미·누락 범위의 미해결 갭 0개',note='검색 성공이나 모델 재검토만으로 승인하지 않습니다.'),
      dict(id='version_freeze',label='업무 분모 버전 고정',state='pending',done_when='목록·총수·근거·범위가 일치하고 전체 회귀 통과',note='그 뒤 업무 → 배포 국가 → 현지 플랫폼 화면 수집으로 진행합니다.')]
    advisory=read(ROOT/'data/mece-source-advisory-v18.json')['rows']
    if v22_path.exists():
        overlay={r['reference_key']:r for r in advisory}
        overlay.update({r['reference_key']:r for r in read(ROOT/'data/quality-steward-v22-source-dispositions.json')['rows']})
        advisory=list(overlay.values())
    root_keys={r['reference_key'] for r in progress['source_dispositions']}
    progress['unadjudicated_source_buckets']=dict(collections.Counter(r['decision'] for r in advisory if r['reference_key'] not in root_keys))
    scope_file=ROOT/'data/mece-standards-scope-v19.json'
    if scope_file.exists():
        standards=read(scope_file)
        progress['standards_scope']=[{k:v for k,v in r.items() if k!='units'} for r in standards['standards']]
        progress['standards_scope_open_tasks']=standards['open_scope_tasks']
progress['current_definition_signatures']={i:hashlib.sha256(__import__('json').dumps({k:w[k] for k in ['actor_role','object_key','outcome_key','discriminator','definition','includes','excludes']},sort_keys=True,ensure_ascii=False).encode()).hexdigest() for i,w in by.items()}
progress['gates']=[
 dict(id='scope_contract',state='passed',label='대조 범위·업무 집계 단위 고정',note='범위·제외 규칙·버전과 세계 전체 총수 주장을 분리했습니다.'),
 dict(id='initial_model_review',state='passed',label='기존 368개 항목 전수 반례 검토 완료',note='368개 고유 ID의 유효 응답을 보존했습니다. 모델 검토 완료이며 MECE 승인이 아닙니다.'),
 dict(id='semantic_me',state='pending',label=f'의미 경계 확정 보류 · 구체 쟁점 {progress["review_counts"]["semantic_pending_count"]}개',note='역할·직접 결과·복합 입력의 잔여 판정 및 변경 정의 재검토가 필요합니다.'),
 dict(id='source_ce',state='pending',label='기준 원문 전수 포함·제외·부분 연결 확정 보류',note=f'BIAN 927개 원문 노드 중 root 재심 {len(progress["source_dispositions"])}개. 나머지 {927-len(progress["source_dispositions"])}개 제안의 판정과 이미 발견된 명세 공백·부분 연결 처리가 필요합니다.'),
 dict(id='final_regression',state='pending',label='확정 목록의 전체 검색·연결 회귀 대기',note='기술적 회귀 통과와 최종 업무 분모 승인을 따로 검증합니다.'),
]
if v18_path.exists():
    c=progress['review_counts']
    progress['gates'][2].update(label=f'의미 경계 확정 보류 · 경계·절차 {c["semantic_pending_count"]}개 / 후보·후속 결과 {c["candidate_pending_count"]}개',
        note='기존 쟁점 교정과 새 결과 등록을 마쳤습니다. 신규 후보의 복합 결과·포함 범위와 원문 미정의 결과는 별도 판정 대상으로 보존합니다.')
    progress['gates'][3]['note']+=f' 모델 원문 전수 검토 {c["source_model_rows"]}개, 누락·부분 연결 재검토 {c["source_issue_model_rows"]}개, 후보 {c["candidate_hypotheses"]}개 대조를 완료했으며 자동 승인하지 않았습니다.'
if progress.get('technical_validation',{}).get('state')=='passed':
    progress['gates'][-1].update(state='passed',label='현재 목록의 검색·연결·브라우저 회귀 통과',
                               note='기술적 회귀 검증 통과입니다. 의미 경계·포함 범위의 미확정을 해소하지 않습니다.')
if v19_path.exists():
    progress['gates'][2]['note']='명시된 독립 결과 등록·경계 교정을 마쳤습니다. 잔여 작업에는 실제 수행할 원문 수집·의미 비교와 종료 조건을 기록했습니다.'
    progress['gates'][3]['note']+=' ISO·FIBO·NIST의 선택 대조 범위 판정도 완료되어야 합니다.'
if v20_path.exists():
    progress['review_counts'].update(v20_ticket_model_rows=len(v20['rows']),
        v20_closed_tickets=sum(r['state']=='closed_root_decision' for r in v20['rows']),
        v20_added_definitions=len(v20['added_work_ids']),
        v20_current_delta_rows=progress.get('v20_delta_review',{}).get('reviewed_rows',0),
        latest_closed_tickets=sum(r['state']=='closed_root_decision' for r in v20['rows']),
        latest_added_definitions=len(v20['added_work_ids']),
        latest_current_delta_rows=progress.get('v20_delta_review',{}).get('reviewed_rows',0))
    progress['execution_plan'][0]['note']=f'이전 단계의 열린 쟁점 {len(v20["rows"])}개를 추가 공식 원문으로 대조했습니다.'
    progress['execution_plan'][1]['note']=f'이번 쟁점 {progress["review_counts"]["v20_closed_tickets"]}개 종료 · 현재 열린 작업 {len(remaining)}개 · 추가 원문 검토 {len(v20["source_followups"])}그룹'
if v21_path.exists():
    progress['review_counts'].update(v21_ticket_model_rows=len(v21['rows']),
        v21_closed_tickets=sum(r['state']=='closed_root_decision' for r in v21['rows']),
        v21_added_definitions=len(v21['added_work_ids']),
        v21_current_delta_rows=progress.get('v21_delta_review',{}).get('reviewed_rows',0),
        latest_closed_tickets=sum(r['state']=='closed_root_decision' for r in v21['rows']),
        latest_added_definitions=len(v21['added_work_ids']),
        latest_current_delta_rows=progress.get('v21_delta_review',{}).get('reviewed_rows',0))
    progress['execution_plan'][0]['note']=f'직전 열린 쟁점 {len(v21["rows"])}개를 현행 전체 정의·추가 공식 원문으로 대조했습니다.'
    progress['execution_plan'][1]['note']=f'이번 쟁점 {progress["review_counts"]["v21_closed_tickets"]}개 종료 · 현재 열린 작업 {len(remaining)}개 · 추가 원문 검토 {len(v21["source_followups"])}그룹'
if v22_path.exists():
    progress['review_counts'].update(v22_new_root_source_rows=len(v22['source_dispositions']),
        v22_opus_source_rows=v22['review']['opus_own_source_rows'],v22_sonnet_source_rows=v22['review']['sonnet_own_source_rows'],
        latest_closed_tickets=0,latest_added_definitions=0,latest_current_delta_rows=0)
    progress['execution_plan'][0]['note']='직전 미판정 원문 825개와 NIST 205개 절의 두 모델 검토를 완료했습니다. 실제 업무 목록 자동 변경은 없습니다.'
    progress['execution_plan'][1]['note']=f'열린 경계 쟁점 {len(remaining)}개 · 별도 원문 책임 그룹 {len(progress["source_followups"])}개. 검토안 완료는 의미 확정과 다릅니다.'
    progress['execution_plan'][2]['note']=f'현재 397개 정의에 대하여 미판정 원문 825개를 Opus·Sonnet이 각각 검토했습니다. 최종 판정 {len(progress["source_dispositions"])} / 927개, 나머지는 개별 금융 결과 연결 검토가 남습니다.'
    progress['execution_plan'][3]['note']='ISO 실제 파일: 업무영역 36개·메시지 묶음 181개·메시지 정의 3,340개. FIBO 비수록 모듈 219개와 NIST 205개 절을 열거하고 NIST 두 모델 검토를 완료했습니다. 업무 영향 판정은 미완료입니다.'
progress['completed_gates']=[g['id'] for g in progress['gates'] if g['state']=='passed']
progress['bedrock_jobs']=[dict(id=read(p)['job_id'],model=read(p)['model'],prompt_sha256=read(p)['prompt_sha256'],automatic_adoption=False) for p in sorted((RUN/'reviews').glob('*/*/proposal.json'))]
if v18_path.exists():
    progress['bedrock_jobs'] += [dict(id=read(p)['job_id'],model=read(p)['model'],prompt_sha256=read(p)['prompt_sha256'],automatic_adoption=False)
        for p in sorted((ROOT/'research/source-store/mece-closure-20261006/reviews').glob('*/*/proposal.json'))]
if v19_path.exists():
    progress['bedrock_jobs'] += [dict(id=read(p)['job_id'],model=read(p)['model'],prompt_sha256=read(p)['prompt_sha256'],automatic_adoption=False)
        for p in sorted((ROOT/'research/source-store/mece-closure-20261011/reviews').glob('*/*/proposal.json'))]
if v20_path.exists():
    progress['bedrock_jobs'] += [dict(id=read(p)['job_id'],model=read(p)['model'],prompt_sha256=read(p)['prompt_sha256'],automatic_adoption=False)
        for p in sorted((ROOT/'research/source-store/mece-closure-v20-20261011/reviews').glob('*/*/proposal.json'))]
if v21_path.exists():
    progress['bedrock_jobs'] += [dict(id=read(p)['job_id'],model=read(p)['model'],prompt_sha256=read(p)['prompt_sha256'],automatic_adoption=False)
        for p in sorted((ROOT/'research/source-store/mece-closure-v21-20261011/reviews').glob('*/*/proposal.json'))]
if v22_path.exists():
    progress['bedrock_jobs']+=v22['bedrock_jobs']
proof_ids={r['id'].removeprefix('WGSS-PROCESS-') for w in by.values() for r in w['refs'] if r['id'].startswith('WGSS-PROCESS-')}
progress['definition_source_count']=len(proof_ids)
write(ROOT/'data/mece-closure-review.json',progress)
print(__import__('json').dumps(progress['review_counts'],ensure_ascii=False))
