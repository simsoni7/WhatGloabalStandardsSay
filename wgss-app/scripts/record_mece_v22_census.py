"""Record only the explicit root-authored scope selections; never adopt all proposals."""
import collections,hashlib,json
from pathlib import Path
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-v22-20261011'

def proposals(prefix,expected):
    result=[];jobs=[]
    for p in sorted((RUN/'reviews').glob(prefix+'*/*/proposal.json')):
        d=read(p);job=read(RUN/'inputs'/(d['job_id']+'.json'))
        assert len(job['expected_ids'])==len(set(job['expected_ids']))
        assert {r[job['row_key']] for r in d['result']['rows']}==set(job['expected_ids'])
        jobs.append(dict(id=d['job_id'],model=d['model'],prompt_sha256=d['prompt_sha256'],automatic_adoption=False))
        for r in d['result']['rows']:result.append({**r,'job_id':d['job_id'],'prompt_sha256':d['prompt_sha256']})
    key='reference_key' if prefix in ['census-','steward-'] else 'section_id'
    assert len(result)==len({r[key] for r in result})==expected,(prefix,len(result),expected)
    return result,jobs

def record():
    path=ROOT/'data/mece-v22-root-dispositions.json';assert not path.exists(), 'One-time final record already exists'
    before=read(RUN/'checkpoint-before.json');catalogue=read(RUN/'catalogue-before.json')
    assert read(ROOT/'dist/data/operations.json')==catalogue, 'Actual catalogue changed; prepare fresh audits'
    sources=read(RUN/'own-source-census.json');source_by={s['reference_key']:s for s in sources}
    allowed={w['id'] for w in catalogue['works']}
    opus,ojobs=proposals('census-',825);sonnet,sjobs=proposals('steward-',825)
    for row in opus+sonnet:
        assert set(row['work_ids'])<=allowed
        assert set(row.get('evidence_section_ids',[]))<={s['section_id'] for s in source_by[row['reference_key']]['own_sections']}
    op={r['reference_key']:r for r in opus};so={r['reference_key']:r for r in sonnet}
    old_keys={s['reference_key'] for s in before['source_dispositions']}
    assert not old_keys & set(source_by) and len(old_keys|set(source_by))==927
    selection=read(ROOT/'data/mece-v22-root-selection.json');corrections=read(ROOT/'data/mece-v22-financial-exclusion-corrections.json')
    authored=[]
    for group in selection['groups']:
        for native in group['native_ids']:
            authored.append(dict(reference_key='BusinessCapability:'+native,decision=group['decision'],work_ids=[],
                exclusion_id=group['exclusion_id'],reason=group['reason'],uncovered_results=['자체 명세·직접 금융 대상·완료 책임 확인'] if group['decision']=='source_specification_gap' else []))
    authored+=corrections['rows']
    assert len(authored)==len({r['reference_key'] for r in authored})==166
    roots=[]
    for row in authored:
        key=row['reference_key'];src=source_by[key];evidence=[]
        if row['decision']!='source_specification_gap':
            evidence=[dict(section_id=s['section_id'],quote=s['text'][:180]) for s in src['own_sections'] if s['text']]
        else:
            evidence=[dict(section_id=s['section_id'],quote=s['text'][:180]) for s in src['own_sections'] if s['text']]
        roots.append({**row,'source_name':src['name'],'evidence':evidence,
            'own_source_sections':[dict(section_id=s['section_id'],locator=s['source_locator'],source_sha256=s['source_file_sha256']) for s in src['own_sections']],
            'opus_proposal_prompt_sha256':op[key]['prompt_sha256'],'sonnet_proposal_prompt_sha256':so[key]['prompt_sha256'],
            'model_disagreement':op[key]['decision']!=so[key]['decision'],
            'root_correction_of_sonnet':row['decision']!=so[key]['decision'],
            'mapping_is_comparison_only':row['decision']=='linked_partial',
            'root_adjudicated':True,'coverage_is_complete':False,'automatic_adoption':False})
    ni,njobs=proposals('nist-unique-',205);nv,vjobs=proposals('nist-validator-',205)
    unique=read(RUN/'nist-full-section-scope-v3.json');assert {x['section_id'] for x in ni}=={b['section_id'] for b in unique['blocks']}
    nvalidation={x['section_id']:x for x in nv}
    scope=read(RUN/'standard-scope-census.json')
    scope.update(nist_heading_blocks=len(unique['blocks']),nist_unique_section_ids=len({b['section_id'] for b in unique['blocks']}),
                 nist_requirement_containing_blocks=sum(b['contains_requirement_words'] for b in unique['blocks']))
    source_review=dict(version='WGSS-v22-two-model-own-source-census',input_operation_version=catalogue['version'],
        reviewed_source_count=825,rows=opus,automatic_adoption=False,root_adjudicated=False,global_mece_approved=False)
    write(ROOT/'data/mece-source-advisory-v22.json',source_review)
    write(ROOT/'data/quality-steward-v22-source-dispositions.json',dict(version='WGSS-v22-source-steward',rows=sonnet,
        automatic_adoption=False,global_mece_approved=False,logical_exception_root_overrides=['ServiceDomain:32833']))
    write(RUN/'nist-valid-two-model-reviews.json',dict(rows=[dict(opus=x,sonnet=nvalidation[x['section_id']]) for x in ni],
        authoritative_scope='nist-full-section-scope-v3.json',automatic_adoption=False,mapping_review_complete=False))
    followup=dict(id='V22-CENSUS-FINANCIAL-BOUNDARIES',title='BIAN 재검토에서 확인한 금융정보·보수·규제통제 경계',
        source_reference_keys=[r['reference_key'] for r in corrections['rows']],
        next_action='재무제표·금융시장 정보·세무 판단·규제 감사/시정·보수/급부 지급·투자자 공시·위험 통제를 기존 정의와 개별 대조합니다. 비교 링크는 기능 포함 승인과 다르며 원문 전체 제외·완전 연결을 주장하지 않습니다.')
    report=dict(version='WGSS-mece-census-v22-20261011',input_version=catalogue['version'],output_version=catalogue['version'],
        source_dispositions=roots,remaining_work=before['remaining_work'],source_followups=before['source_followups']+[followup],
        added_work_ids=[],edited_work_ids=[],automatic_adoption=False,independent_human_review=False,global_mece_approved=False,
        review=dict(opus_own_source_rows=825,sonnet_own_source_rows=825,nist_opus_sections=205,nist_sonnet_sections=205,
            root_new_source_rows=len(roots),root_scope_exclusions=133,root_empty_or_placeholder_source_gaps=17,
            root_financial_exclusion_corrections=len(corrections['rows']),
            changed_model_decisions=sum(op[k]['decision']!=so[k]['decision'] for k in op),
            opus_decision_counts=dict(collections.Counter(r['decision'] for r in opus)),
            sonnet_decision_counts=dict(collections.Counter(r['decision'] for r in sonnet)),
            nist_opus_decision_counts=dict(collections.Counter(r['decision'] for r in ni)),
            nist_sonnet_decision_counts=dict(collections.Counter(r['decision'] for r in nv))),
        standard_material_census=scope,bedrock_jobs=ojobs+sjobs+njobs+vjobs,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [RUN/'catalogue-before.json',RUN/'checkpoint-before.json',RUN/'own-source-census.json',RUN/'nist-full-section-scope-v3.json',
             RUN/'iso-catalogue-scope.json',RUN/'fibo-omitted-scope.json',ROOT/'data/mece-v22-root-selection.json',ROOT/'data/mece-v22-financial-exclusion-corrections.json']},
        next_actions=['미판정 원문 659개를 현재 정의에 개별 연결·분해하고 잔여 결과를 판정합니다.',
          'ISO 181개 메시지 묶음과 관련 메시지의 기능/보고/흐름에서 객체만으로 빠진 직접 결과를 대조합니다.',
          'FIBO 비수록 Release 모듈 81개를 우선 대조하고 나머지 성숙도·외부 관계의 영향을 구분합니다.',
          'NIST 205개 절의 두 모델 제안을 실제 정의와 비교하여 생애주기 누락과 기술/정책 구성요소를 판정합니다.',
          '잔여 3개 경계 쟁점·5개 원문 책임 그룹을 정리한 뒤 전체 ME/CE 재검증·업무 분모를 고정합니다.'])
    write(path,report)
    p=read(ROOT/'data/mece-closure-review.json');p.update(version=report['version'],current_stage='v22_full_own_source_two_model_review_complete_financial_mapping_and_standard_impact_pending')
    write(ROOT/'data/mece-closure-review.json',p)
    print(json.dumps(report['review'],ensure_ascii=False))

if __name__=='__main__':record()
