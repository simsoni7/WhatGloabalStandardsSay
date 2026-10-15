"""Resolve concrete delta regressions and reject case/instance confusion."""
from run_mece_closure import ROOT,RUN,read,write
progress=read(ROOT/'data/mece-closure-review.json');assert not progress.get('delta_patch_applied')
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
data=read(ROOT/'dist/data/operations.json');by={w['id']:w for w in data['works']}
fixes={
 'WGSS-4F358B4315C3':dict(discriminator='fraud_loss_liability_judgment_not_detection_or_remedy_execution'),
 'WGSS-69483AED45F1':dict(title='의심 거래에 대한 고객 확인 응답 수령',definition='사기 확인 담당자가 의심 거래에 대해 고객에게 사실 확인을 요청하고 응답을 받는 업무. 응답만으로 최종 사기 여부나 손실 책임을 확정하지 않습니다.'),
 'WGSS-89CB90A2150D':dict(title='보험계약 해지 및 환급권 확정'),
 'WGSS-9EDE2FF3C6A4':dict(excludes=by['WGSS-9EDE2FF3C6A4']['excludes']+['기존 대출의 기간연장 요청','기존 약정 신용한도의 이용 요청','연금 중도인출 요청']),
 'WGSS-EFF17F1D2D6F':dict(title='수쿠크 청약 지시 제출',definition='투자자가 수쿠크 취득을 위한 청약 지시를 제출하는 업무. 발행기관의 배정, 실제 결제 또는 보유기록 생성·관리를 완료한 결과가 아닙니다.'),
 'WGSS-F802F38E3CF6':dict(definition='보험계약 당사자가 기존 계약의 보장 범위·보험료 등 변경 조건을 합의하여 변경된 계약 조건을 확정하는 업무. 고객의 단순 요청과 보험자의 내부 위험평가를 구별합니다.'),
}
for i,fields in fixes.items():
    reason='변경 후 전수 대조에서 남아 있던 제목·정의·구분자 모순을 직접 결과와 일치시켰습니다.'
    fields['review_note']=reason
    ledger['edits'].append(dict(id=i,fields=fields,reason=reason,phase='mece-closure-v17-delta-root-review',automatic_adoption=False))
    progress['root_decisions'].append(dict(work_id=i,decision='corrected_edit',reason=reason,automatic_adoption=False))
    progress.setdefault('delta_root_dispositions',[]).append(dict(id=i,state='corrected',reason=reason))
progress.setdefault('delta_root_dispositions',[]).append(dict(id='WGSS-BD3D94D4FCF9',state='proposal_rejected_non_defect',
    reason='병행 계약은 별도 당사자와 독립적으로 체결하는 동일 계약 업무의 여러 실행 건입니다. 거래 건수가 둘이라는 이유로 업무 유형을 두 개로 복제하지 않습니다. 각 계약의 독립성·권리구조는 조건으로 보존합니다.'))
progress['delta_root_dispositions'].append(dict(id='WGSS-B947CF3FC565',state='pending_source_boundary',
    reason='자동 집중이동 실행과 장부이체의 직접 결과가 동일한지, 집중이동 약정·실제 자금이전의 경계를 추가 검증해야 합니다.'))
progress['delta_root_dispositions'].append(dict(id='WGSS-B33218BC1C8A',state='pending_source_boundary',
    reason='보험자 통지의무라는 기존 책임은 현재 원문으로 입증되지 않았습니다.'))

# The bank's own customer-position rendering is not its treasury hedging. An
# institutional batch label alone cannot justify removing a correct mapping.
original='institution-processing-consolidated customer position-derive and present-79'
for r in ledger['input_mapping_overrides']:
    if r['input_id']==original:
        r.update(work_ids=['WGSS-7219DCE0C54F'],state='corrected_source_relationship',reason='원문은 고객 통합 포지션 제공입니다. 기관 처리 배치에 있다는 이유만으로 기관 자기 트레저리 업무로 분류하지 않습니다.')
fields={'input_ids':by['WGSS-7219DCE0C54F']['input_ids']+[original]}
ledger['edits'].append(dict(id='WGSS-7219DCE0C54F',fields=fields,reason='고객 통합뷰 원 입력 연결을 복원합니다.',phase='mece-closure-v17-delta-root-review',automatic_adoption=False))
progress['delta_patch_applied']=True
write(ROOT/'data/operation-backbone-dispositions.json',ledger)
write(ROOT/'data/mece-closure-review.json',progress)
print('6 remaining field contradictions corrected; customer input restored; parallel-case clone rejected')
