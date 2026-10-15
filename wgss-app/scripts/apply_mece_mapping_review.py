"""Curated result/role corrections and explicit repair of contradictory mappings."""
import copy
from run_mece_closure import ROOT,RUN,read,write

review=read(ROOT/'data/mece-closure-review.json');assert not review.get('mapping_patch_applied')
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
by={w['id']:w for w in read(ROOT/'dist/data/operations.json')['works']}
selected={
 'semantic-current-followup-01-resume-1-source-id-retry':['WGSS-009BE91CB5A0','WGSS-05A51FD5B808','WGSS-0F76E3C2B5B5'],
 'semantic-current-followup-01-resume-2':['WGSS-19829603FDD5'],
 'semantic-current-followup-02-resume-1':['WGSS-21CFE4244D5F','WGSS-24AD8A6460EC','WGSS-2D859C09DA95'],
 'semantic-current-followup-02-resume-2-source-id-retry':['WGSS-5001E20F90A5','WGSS-587877289E94','WGSS-5C590613C2E4'],
 'semantic-current-followup-06':['WGSS-COMPLETION-SAVINGS-AGREEMENT'],
}
def patch(i,fields,reason,job=None,evidence=None):
    fields=copy.deepcopy(fields);fields['review_note']=reason
    ledger['edits'].append(dict(id=i,fields=fields,reason=reason,phase='mece-closure-v17-mapping-root-review',automatic_adoption=False))
    review['root_decisions'].append(dict(work_id=i,decision='corrected_edit',job_id=job,reason=reason,evidence=evidence or [],automatic_adoption=False))
for job_id,ids in selected.items():
    proposal=read(next((RUN/'reviews'/job_id).glob('*/proposal.json')))
    rows={r['id']:r for r in proposal['result']['rows']}
    for i in ids:
        r=rows[i];assert r['decision']=='edit'
        fields=dict(r['fields'])
        if i=='WGSS-009BE91CB5A0':fields['definition']='인수·주관기관이 확정된 발행조건에 따라 신규 증권의 투자자별 배정 수량을 확정하는 업무.'
        if i=='WGSS-0F76E3C2B5B5':
            fields.update(title='신디케이트 구성원 의무이행 판정',outcome_key='assess_syndicate_member_obligation_compliance',
                          definition='신디케이트 관리자가 합의된 운영약정에서 정한 구성원의 이행의무 준수 여부를 판정하는 업무. 분담금 실제 정산을 포함하지 않습니다.',
                          includes=['구성원 운영약정상 이행의무 준수 판정'])
        if i=='WGSS-19829603FDD5':fields['excludes']+=['SAR 제출 여부의 최종 결정', '제재목록 경보의 유효 일치 판정']
        if i=='WGSS-21CFE4244D5F':fields['layer']='institution'
        patch(i,fields,r['reason']+' 책임·직접 결과와 보존 원문을 대조한 선택 교정입니다.',job_id,r.get('evidence'))

patch('WGSS-11F17132FBF8',dict(actor_role='account_switch_service_provider',layer='institution',
      outcome_key='complete_account_and_payment_arrangements_switch',
      definition='계좌이동 서비스 제공자가 고객 계좌와 그 계좌에 연결된 지급 약정을 다른 지급기관으로 이관하는 업무. 이전 완료와 고객의 단순 신청 제출을 구별합니다.',
      includes=['계좌와 연결 지급약정의 기관 간 이관 완료'],excludes=['계좌이동 신청 제출만 완료된 상태', '개별 결제수단 재발급']),
      'ISO AccountSwitching 원문은 보장된 이관 결과를 정의합니다. 별도 신청 결과의 절차를 입증하지 않은 상태에서 신청과 이관을 두 개로 만들지 않습니다.')

# The same confirmation source supplies the required checks; no independent
# pre-validation decision is specified in the currently retained clauses.
ledger['merges'].append(dict(**{'from':'WGSS-04EE57EE330E','into':'WGSS-AFF4499574AA'},
    reason='BIAN Payment Confirmation의 사전 확인은 지급 승인 책임의 필수 점검입니다. 별도 독립 확인 책임·결과가 명시되지 않아 같은 책임을 추가 집계하지 않습니다.'))
review['root_decisions'].append(dict(work_id='WGSS-04EE57EE330E',decision='merged',target_ids=['WGSS-AFF4499574AA'],reason=ledger['merges'][-1]['reason'],automatic_adoption=False))

# Remove misleading input association without destroying the former raw input.
inputs=[
 ('insurance-pensions-pension account funds-request_early_withdrawal-37',['WGSS-647DCADA33FC'],'연금 중도인출 요청은 대출 신청이 아닙니다.'),
 ('institution-processing-holder election instruction-capture and apply-57',['WGSS-86C3A7BB3CD6','WGSS-B076A6656970'],'원 입력이 일반 선택지시와 매수인 보호지시를 함께 기술합니다. 직접 결과별 연결을 명시합니다.'),
]
for original,targets,reason in inputs:
    ledger.setdefault('input_mapping_overrides',[]).append(dict(input_id=original,work_ids=targets,state='corrected_source_relationship',reason=reason))
    if original.startswith('insurance-pensions-'):
        patch('WGSS-9EDE2FF3C6A4',dict(input_ids=[i for i in by['WGSS-9EDE2FF3C6A4']['input_ids'] if i!=original],
          refs=[r for r in by['WGSS-9EDE2FF3C6A4']['refs'] if r['name']!='Pension']),reason)

review['mapping_patch_applied']=True
write(ROOT/'data/operation-backbone-dispositions.json',ledger)
write(ROOT/'data/mece-closure-review.json',review)
nav=read(ROOT/'data/business-backbone-review.json');nav['assignments']=[a for a in nav['assignments'] if a['id']!='WGSS-04EE57EE330E']
for g in nav['goals']:
    for field in ['canonical_work_ids','optional_work_ids']:g[field]=list(dict.fromkeys('WGSS-AFF4499574AA' if i=='WGSS-04EE57EE330E' else i for i in g[field]))
write(ROOT/'data/business-backbone-review.json',nav)
products=read(ROOT/'data/product-profiles-review.json')
for p in products['product_profiles']:
    for s in p['steps']:s['work_ids']=list(dict.fromkeys('WGSS-AFF4499574AA' if i=='WGSS-04EE57EE330E' else i for i in s['work_ids']))
write(ROOT/'data/product-profiles-review.json',products)
print('12 selected role/result corrections, 1 duplicate merge, 2 input relationships repaired')
