"""Curated application of checked regional clauses; no worldwide legal claims."""
from run_mece_closure import ROOT, RUN, read, write

review=read(ROOT/'data/mece-closure-review.json')
assert not review.get('legal_patch_applied')
ledger=read(ROOT/'data/operation-backbone-dispositions.json')
by={w['id']:w for w in read(ROOT/'dist/data/operations.json')['works']}
proposal=read(next((RUN/'reviews/legal-source-boundary-v17').glob('*/proposal.json')))
job=read(RUN/'inputs/legal-source-boundary-v17.json')
for row in proposal['result']['rows']:
    i=row['id']
    if i=='WGSS-B33218BC1C8A':
        # Do not invent an insurer duty or drop a currently registered gap silently.
        patch={'status':'unresolved','source_gaps':[{'input_id':i,'reason':'ISO ClassAction 정의는 보험자의 통지의무를 입증하지 않습니다. 법원 지시 고지와 금융기관 책임의 구분이 필요합니다.'}],
               'review_note':'보험자의 집단소송 통지의무 근거를 확보하지 못했습니다. 금융 분쟁 고지로 역할·범위를 재정의하거나 해당 책임을 입증하기 전 집계 승인에 사용할 수 없습니다.'}
        decision='retained_unresolved'
    else:
        assert row['decision']=='edit'
        patch=dict(row['fields'])
        refs=[]
        for q in row['evidence']:
            assert q['quote'] in job['sections'][q['section_id']]
            meta=read(RUN/'sources'/(q['section_id']+'.json'))
            text=(RUN/'sources'/meta['text_path']).read_text()
            assert q['quote'] in text
            refs.append(dict(id='WGSS-PROCESS-'+q['section_id'],name=q['section_id'].replace('_',' '),url=meta['url'],
                             locator=meta['text_path']+' / exact regional clause',exact_quote=q['quote'],
                             source_sha256=meta['sha256'],source_snapshot_id='WGSS-primary-process-20261005',
                             context_requires_review=False,rationale=row['reason'],
                             proof_scope='specified_regional_rule_not_global_right_or_ui_capture'))
        patch['refs']=by[i]['refs']+refs
        patch['source_gaps']=[]
        patch['status']='edited'
        if i=='WGSS-1F829AAE72A8':
            patch['title']='금융 집단소송 제외 요청'
            patch['definition']='금융상품·금융거래 손해에 관한 미국 Rule 23(b)(3) 집단 구성원이 법원이 고지한 기간·방법에 따라 제외 요청을 제출하는 업무. 일반 민사소송이나 보편적 참여·탈퇴권을 뜻하지 않습니다.'
            patch['excludes']+=['일반 비금융 민사소송', '보편적 opt-in 참여권', '제외 요청의 자동 승인·모든 배상청구권 포기']
            patch['applicability_conditions']+=['2024년 편찬 Rule 23(c)(2)(B)·(3)(B) 원문에 한정합니다. 적용 법원·명령과 변경 법령은 별도 확인합니다.']
        if i=='WGSS-10ABD5DF40D8':
            patch['applicability_conditions']+=['대통령령이 정한 적용 상품·철회 제외 요건·더 긴 약정 기간을 확인합니다. 법정 기간을 모든 보험·모든 시장에 적용하지 않습니다.']
        patch['review_note']=row['reason']
        decision='corrected_edit'
    ledger['edits'].append(dict(id=i,fields=patch,reason=patch['review_note'],phase='mece-closure-v17-legal-root-review',automatic_adoption=False))
    review['root_decisions'].append(dict(work_id=i,decision=decision,job_id=job['id'],reason=patch['review_note'],
                                        evidence=row['evidence'],proposal_prompt_sha256=proposal['prompt_sha256'],automatic_adoption=False))
review['legal_patch_applied']=True
write(ROOT/'data/operation-backbone-dispositions.json',ledger)
write(ROOT/'data/mece-closure-review.json',review)
print('4 regional source corrections; 1 unproven insurer duty preserved as unresolved')
