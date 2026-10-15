"""Apply an explicit root-selected subset; retain conflicting proposals separately."""
import copy
from run_mece_closure import ROOT, RUN, read, write

review=read(ROOT/'data/mece-closure-review.json')
assert not review.get('followup_patch_applied')
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
by={w['id']:w for w in read(ROOT/'dist/data/operations.json')['works']}
selection={
 'semantic-current-followup-03': ['WGSS-5E53DA466A34','WGSS-5FEE8E418F00','WGSS-671FA819885C','WGSS-7219DCE0C54F','WGSS-77D80A20399C','WGSS-79C6FBAB7915','WGSS-7FB42975FA0E'],
 'semantic-current-followup-04': ['WGSS-86C3A7BB3CD6','WGSS-94E86B863786','WGSS-A4D3333EA17A','WGSS-A52E1501821C','WGSS-A6B44E3A0561','WGSS-A93CA2216CB9','WGSS-AA21448779BC'],
 'semantic-current-followup-05': ['WGSS-B0DA64D7BCB4','WGSS-B5B544940BAB','WGSS-B6D7A72FE1F6','WGSS-B6E0D79F2BA6','WGSS-B704DE36E9CF','WGSS-BCE322BA2F5A','WGSS-C1405A805E6A'],
 'semantic-current-followup-06': ['WGSS-CCF5FB649297','WGSS-D151DD97CD2C','WGSS-D69F9183EC85','WGSS-EC7E0C4D2BED'],
 'semantic-current-followup-07': ['WGSS-F802F38E3CF6','WGSS-FBFE37ED9D15'],
}
overrides={
 'WGSS-5E53DA466A34':{'layer':'institution'},
 'WGSS-AA21448779BC':{'layer':'institution','actor_role':'acquirer'},
 'WGSS-FBFE37ED9D15':{'layer':'institution'},
 'WGSS-F802F38E3CF6':{'actor_role':'insurance_contract_counterparty','layer':'customer'},
}
for job_id, ids in selection.items():
    proposal=read(next((RUN/'reviews'/job_id).glob('*/proposal.json')))
    job=read(RUN/'inputs'/(job_id+'.json'))
    rows={r['id']:r for r in proposal['result']['rows']}
    for i in ids:
        row=rows[i]
        assert row['decision']=='edit'
        patch={**copy.deepcopy(row['fields']),**overrides.get(i,{})}
        # Proposed lifecycle narrowing needs actual missing results, not exclusion
        # of known amend/cancel duties. They are added explicitly below.
        if i=='WGSS-7219DCE0C54F':
            mixed=[v for v in by[i]['input_ids'] if v.startswith('institution-processing-')]
            patch['input_ids']=[v for v in by[i]['input_ids'] if v not in mixed]
            for v in mixed:
                ledger.setdefault('input_mapping_overrides',[]).append(dict(input_id=v,work_ids=[],state='unresolved_source_relationship',
                    reason='기관 자기 포지션·헤지와 고객 통합정보는 같은 결과가 아닙니다. 복합 원 입력을 결과별로 재판정합니다.'))
        if i=='WGSS-671FA819885C':
            # Modification is not automatically permanent or unilateral.
            patch['actor_role']='credit_agreement_counterparty'
            patch['discriminator']='binding_terms_amendment_not_payment_execution_or_write_down'
            patch['definition']='여신계약 당사자가 기존 금리·만기 등의 변경 조건을 구속력 있게 합의하는 업무. 정상·부실 상태의 재약정을 포함하되 감액 집행과 구별합니다.'
        if i=='WGSS-7FB42975FA0E':
            patch['definition']='금융서비스 지원 담당자가 본인을 대신할 법적 대리·관리 지위를 해당 서비스에서 확인·등록하고 권한 범위를 확정하는 업무. 등록만으로 법정 대리권을 새로 창설한다고 주장하지 않습니다.'
        patch['review_note']=row['reason']+' 원문 책임·대상·결과 대조 후 선택 반영; MECE 전체 승인 아님.'
        refs=[]
        sources={d['id']:d for d in job['input']['original_clauses']}
        for q in row.get('evidence',[]):
            assert q['quote'] in job['sections'][q['section_id']]
            source=sources[q['section_id']]
            refs.append(dict(id=source['id'],name=source['name'],url=source['source_url'],locator=source['source_locator'],
                             exact_quote=q['quote'],source_snapshot_id=source['source_snapshot_id'],
                             context_requires_review=False,rationale=row['reason'],proof_scope='source_functional_responsibility_not_provider_ui'))
        patch['refs']=by[i]['refs']+refs
        ledger['edits'].append(dict(id=i,fields=patch,reason=patch['review_note'],phase='mece-closure-v17-followup-root-review',automatic_adoption=False))
        review['root_decisions'].append(dict(work_id=i,decision='corrected_edit',job_id=job_id,reason=patch['review_note'],
                                            evidence=row.get('evidence',[]),proposal_prompt_sha256=proposal['prompt_sha256'],automatic_adoption=False))

# ISO's own process definition explicitly grants the CSD participant two further
# independent lifecycle results. Do not erase them when narrowing registration.
standing=by['WGSS-5FEE8E418F00']
job=read(RUN/'inputs/semantic-current-followup-03.json')
source=next(s for s in job['input']['original_clauses'] if s['name']=='AgentCorporateActionStandingInstruction')
quote='a CSD participant can amend or cancel a standing instruction.'
assert quote in source['definition']
nav=read(ROOT/'data/business-backbone-review.json')
for suffix,title,outcome,includes,excludes in [
 ('AMEND','기업행위 상시지시 변경','amend_existing_corporate_action_standing_instruction',['기존 기업행위 상시지시 내용 변경'],['신규 상시지시 등록','상시지시 취소','개별 기업행위 선택지시']),
 ('CANCEL','기업행위 상시지시 취소','cancel_existing_corporate_action_standing_instruction',['기존 기업행위 상시지시 효력 종료'],['신규 상시지시 등록','내용 변경','이미 실행된 기업행위의 반전'])]:
    i='WGSS-MECE-CORPORATE-STANDING-'+suffix
    w=copy.deepcopy(standing)
    w.update(id=i,title=title,actor_role='csd_participant',layer='institution',outcome_key=outcome,outcome=outcome.replace('_',' '),
             definition=f'예탁결제기관 참가자가 기존 기업행위 상시지시를 {"변경" if suffix=="AMEND" else "취소"}하는 업무. 원 지시의 등록과 개별 이벤트 지시를 구별합니다.',
             includes=includes,excludes=excludes,status='edited',input_ids=[],origin_unit_id='MECE-CLOSURE-'+i,
             review_note='ISO 자체 정의의 명시적 변경·취소 책임을 결과별로 보존합니다.',source_gaps=[],
             boundary=dict(related_ids=['WGSS-5FEE8E418F00'],distinction='신규 등록·기존 내용 변경·기존 지시 효력 종료는 각각 독립적으로 완료·실패합니다.'))
    w['refs']=[dict(id=source['id'],name=source['name'],url=source['source_url'],locator=source['source_locator'],
                   exact_quote=quote,source_snapshot_id=source['source_snapshot_id'],context_requires_review=False,
                   rationale='원문이 참가자의 변경·취소를 명시합니다.',proof_scope='standard_functional_process_not_provider_ui')]
    ledger['additions'].append(w)
    nav['assignments'].append(dict(id=i,family_id='securities',ambiguous=False,reason='직접 대상과 결과의 주 분류'))
    review['root_decisions'].append(dict(work_id=i,decision='source_checked_addition',job_id='semantic-current-followup-03',
                                        reason=w['review_note'],evidence=[dict(section_id=source['id'],quote=quote)],automatic_adoption=False))
review['followup_patch_applied']=True
write(ROOT/'data/operation-backbone-dispositions.json',ledger)
write(ROOT/'data/business-backbone-review.json',nav)
write(ROOT/'data/mece-closure-review.json',review)
print('27 explicitly selected boundary corrections + 2 source-defined lifecycle results')
