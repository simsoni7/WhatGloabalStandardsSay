"""Build the rooted bank-customer scope; never admit model proposals."""
import csv,io,json,collections,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def build():
    root=read(ROOT/'data/bank-ui-root-decisions.json')
    assert root['root_approved'] and not root['automatic_adoption']
    d=root['catalogue'];works=d['works'];valid={w['id'] for w in works}
    assert len(valid)==len(works) and all(w['scope_approved'] for w in works)
    assert len({tuple(w['semantic_key']) for w in works})==len(works)
    if root.get('scope_revision_ledger'):
        revision=read(ROOT/root['scope_revision_ledger'])
        d['scope_revision']={k:revision[k] for k in ['scope_version','baseline_scope_version','baseline_works','current_works','source_work_ids_preserved','root_reviewed','global_financial_mece_approved','automatic_adoption']}
        public_revision=d['scope_revision']|{'metadata_corrections':revision['metadata_corrections'],'new_works':[{'work_id':r['work_id'],'own_source':{k:r['own_source'][k] for k in ['id','provider_id','country','url','raw_sha256']},'root_decision':r['root_decision']} for r in revision['new_works']]}
        write(ROOT/'dist/data/bank-ui-scope-revision.json',public_revision)
    d['counts']={'total':len(works),**dict(collections.Counter(w['module'] for w in works)),
        'by_domain':dict(collections.Counter(w['domain_id'] for w in works))}
    benchmarks=read(ROOT/'data/bank-ui-benchmark-dispositions.json')
    assert benchmarks['scope_version']==d['version']
    assert all(set(b['ui_work_ids'])<=valid and b['root_function_admitted'] for b in benchmarks['examples'])
    # Public data carries immutable hashes/ranges and UI labels. Full publisher
    # prose excerpts remain in the private root proof ledger, not the website.
    d['benchmarks']=json.loads(json.dumps(benchmarks['examples']))
    def redact_quotes(value):
        if isinstance(value,dict):
            if value.get('kind')=='normalized_text_character_range':value.pop('excerpt',None)
            for child in value.values():redact_quotes(child)
        elif isinstance(value,list):
            for child in value:redact_quotes(child)
    redact_quotes(d['benchmarks'])
    quality_path=ROOT/'data/bank-ui-practitioner-review-v34.json'
    if quality_path.exists():
        quality=read(quality_path)
        assert quality['root_reviewed'] and not quality['practitioner_utility_measured']
        assert all(t['work_id'] in valid for t in quality['tasks'])
        d['practitioner_review']=quality
        write(ROOT/'dist/data/bank-ui-practitioner-review-v34.json',quality)
    covered={id for b in d['benchmarks'] for id in b['ui_work_ids']}
    screens=[b for b in d['benchmarks'] if b.get('screen_evidence')]
    assert all(not b.get('additional_screen_evidence') or b.get('screen_evidence') for b in d['benchmarks'])
    for b in screens:
        for screen in [b['screen_evidence']]+b.get('additional_screen_evidence',[]):
            assert re.fullmatch(r'evidence/[A-Za-z0-9_/-]+\.(jpg|png|webp|avif)',screen['image_path'])
            assert hashlib.sha256((ROOT/'dist'/screen['image_path']).read_bytes()).hexdigest()==screen['image_sha256']
            assert screen['visual_review']=='root_visual_checked'
            if screen.get('display_region'):
                region=screen['display_region'];x0,y0,x1,y1=region['bbox_xyxy']
                assert region['review']=='root_visual_checked'
                assert 0<=x0<x1<=region['original_width'] and 0<=y0<y1<=region['original_height']
        assert b['evidence_type'] in ['official_guide_screen','official_product_image','live_public_web','observed_app_screen']
        assert bool(b['observed_app_screen'])==(b['evidence_type']=='observed_app_screen')
        if b['observed_app_screen']:assert b['app_os'] in ['ios','android']
    actual_app=[b for b in screens if b.get('observed_app_screen') and b['evidence_type']=='observed_app_screen']
    d['benchmark_counts']={'works_with_function_documents':len(covered),'examples':len(d['benchmarks']),
        'providers':len({b['provider_id'] for b in d['benchmarks']}),'countries':len({b['country'] for b in d['benchmarks']}),
        'official_guide_screens':len({s['image_sha256'] for b in screens if b['evidence_type']=='official_guide_screen' for s in [b['screen_evidence']]+b.get('additional_screen_evidence',[])}),
        'public_web_captures':len({s['image_sha256'] for b in screens if b['evidence_type']=='live_public_web' for s in [b['screen_evidence']]+b.get('additional_screen_evidence',[])}),
        'works_with_screen_references':len({id for b in screens for id in b['ui_work_ids']}),
        'observed_app_captures':len({b['screen_evidence']['image_sha256'] for b in actual_app}),
        'verified_app_ui_versions':len({(b['provider_id'],b['country'],b['app_os'],b['verified_ui_version']) for b in actual_app if b.get('verified_ui_version')}),
        'unlinked_works':len(works)-len(covered)}
    plan=read(ROOT/'data/bank-ui-collection-plan.json')
    redact_quotes(plan)
    d['collection_plan']=plan
    audit_path=plan.get('public_collection_audit_ledger','data/bank-ui-public-collection-v32.json')
    if (ROOT/audit_path).exists():
        d['public_collection_audit']=read(ROOT/audit_path)
        write(ROOT/'dist/data'/Path(audit_path).name,d['public_collection_audit'])
    if plan.get('market_study_revision'):
        market=read(ROOT/plan['market_study_revision'])
        redact_quotes(market)
        d['market_study_revision']=market
        write(ROOT/'dist/data'/Path(plan['market_study_revision']).name,market)
    if (ROOT/'data/authenticated-collection-v31.json').exists():
        d['authenticated_collection']=read(ROOT/'data/authenticated-collection-v31.json')
        write(ROOT/'dist/data/authenticated-collection-v31.json',d['authenticated_collection'])
    if plan.get('strategy_review_ledger'):
        d['collection_review_queue']=read(ROOT/plan['strategy_review_ledger']).get('staged_semantic_routes',[])
    priority_audits=[]
    if plan.get('priority_audit_ledger'):
        priority_root=read(ROOT/plan['priority_audit_ledger'])
        assert priority_root['scope_version']==d['version']
        if priority_root['scope_change']:
            revision=read(ROOT/priority_root['scope_revision_ledger'])
            assert revision['scope_version']==d['version'] and set(revision['source_work_ids_preserved'])<=valid
            assert priority_root['priority_audit_compatible_work_ids_preserved']
        assert all(a['ui_work_id'] in valid for a in priority_root['priority_cell_dispositions'])
        priority_audits=priority_root['priority_cell_dispositions']
        assert len(priority_audits)==96 and all(a['root_reviewed'] and not a['automatic_adoption'] for a in priority_audits)
    priority_by={(a['ui_work_id'],a['country']):a for a in priority_audits}
    cells=[]
    for w in works:
        for country in plan['countries']:
            code=country['country'];rows=[b for b in d['benchmarks'] if b['country']==code and w['id'] in b['ui_work_ids']]
            reviewed=code=='GB' and any(w['id'] in row['ui_work_ids'] for row in root['official_inventory'])
            latest=next((r for r in d.get('public_collection_audit',{}).get('rows',[]) if r['work_id']==w['id']),None)
            latest_sources=[s for s in latest.get('reviewed_sources',[]) if s.get('country')==code] if latest else []
            priority_audit=priority_by.get((w['id'],code))
            cells.append({'ui_work_id':w['id'],'country':code,'example_ids':[b['id'] for b in rows],
                          'provider_ids':sorted({b['provider_id'] for b in rows}),
                          'assessment_state':'linked' if rows else 'reviewed_no_admissible_evidence' if priority_audit or latest_sources else 'reviewed_evidence_not_admitted' if reviewed else 'not_started',
                          'reviewed_provider_ids':sorted({s['provider_id'] for s in latest_sources}|({'hsbc-uk'} if reviewed else set())),
                          'latest_reviewed_source_ids':[s['source_id'] for s in latest_sources],
                          'screen_example_ids':[b['id'] for b in rows if b.get('screen_evidence')],
                          'priority_audit':priority_audit})
    d['collection_matrix']=cells
    d['collection_counts']={'planned_countries':len(plan['countries']), 'candidate_platforms':len(plan.get('provider_targets',[])),
        'country_work_cells':len(cells),'linked_country_work_cells':sum(bool(c['example_ids']) for c in cells),
        'empty_country_work_cells':sum(not c['example_ids'] for c in cells),
        'screen_country_work_cells':sum(bool(c['screen_example_ids']) for c in cells),
        'reviewed_unlinked_cells':sum(c['assessment_state'].startswith('reviewed_') for c in cells),
        'not_started_cells':sum(c['assessment_state']=='not_started' for c in cells),
        'definition_review_gaps':len(plan.get('definition_review_gaps',[]))}
    priority_ids={id for g in plan['priority_groups'] for id in g['ui_work_ids']}
    # Country expansion changes the whole collection denominator, not the
    # original 32-work pilot. Its 96 reviewed work-country identities persist.
    priority_countries=set(plan.get('priority_countries',[c['country'] for c in plan['countries']]))
    priority_cells=[c for c in cells if c['ui_work_id'] in priority_ids and c['country'] in priority_countries]
    d['priority_collection']={'works':len(priority_ids),'cells':len(priority_cells),'reviewed_cells':len(priority_audits),
        'works_with_examples':len(covered&priority_ids),'linked_cells':sum(bool(c['example_ids']) for c in priority_cells),
        'screen_cells':sum(bool(c['screen_example_ids']) for c in priority_cells),
        'flow_and_condition_cells':sum(any(b.get('flow_steps') and b.get('policy_claims') for b in d['benchmarks'] if b['id'] in c['example_ids']) for c in priority_cells)}
    # Whole-scope progress is independent of the 32-work pilot. Document linkage
    # and an illustrated reference never imply an observed complete UI journey.
    d['breadth_progress']={'scope_version':d['version'],'works':len(works),'country_work_cells':len(cells),
        'work_linkage_percent':round(100*len(covered)/len(works),1),
        'country_work_linkage_percent':round(100*d['collection_counts']['linked_country_work_cells']/len(cells),1),
        'domains':[],'work_queue':[],
        'practitioner_utility_measured':False,'independent_ready_for_use_reviews':0,
        'readiness_ko':'문서 연결과 화면 참고 확보는 실무 적용 가능성의 검증과 별개입니다. 판단 시간·오류 감소는 아직 측정하지 않았습니다.'}
    if plan.get('strategy_review_ledger'):
        strategy=read(ROOT/plan['strategy_review_ledger'])
        d['breadth_progress']['semantic_field_review_queue']=strategy.get('semantic_field_review_queue',[])
        d['breadth_progress']['parallel_tracks']=plan.get('parallel_tracks',[])
    followup=read(ROOT/'data/bank-ui-collection-v28-followup.json') if (ROOT/'data/bank-ui-collection-v28-followup.json').exists() else {}
    for domain in d['domains']:
        ws=[w for w in works if w['domain_id']==domain['id']];wid={w['id'] for w in ws};ds=[c for c in cells if c['ui_work_id'] in wid]
        paired={id for b in d['benchmarks'] if b.get('flow_steps') and b.get('policy_claims') for id in b['ui_work_ids']}
        screen_ids={id for b in screens for id in b['ui_work_ids']}
        d['breadth_progress']['domains'].append({'id':domain['id'],'label':domain['label'],'works':len(ws),
            'linked_works':len(wid&covered),'unlinked_works':len(wid-covered),'screen_reference_works':len(wid&screen_ids),
            'paired_path_condition_works':len(wid&paired),'country_work_cells':len(ds),
            'linked_country_work_cells':sum(bool(c['example_ids']) for c in ds)})
    for w in works:
        rows=[b for b in d['benchmarks'] if w['id'] in b['ui_work_ids']]
        has_screen=any(b.get('screen_evidence') for b in rows)
        d['breadth_progress']['work_queue'].append({'work_id':w['id'],'domain_id':w['domain_id'],'module':w['module'],
            'linked_countries':sorted({b['country'] for b in rows}),'example_ids':[b['id'] for b in rows],
            'evidence_stage':'illustrated_reference' if has_screen else 'function_document' if rows else 'unlinked',
            'market_applicability':'not_assessed','ready_for_use_review':'not_assessed',
            'source_family_ko':followup.get('source_families_by_domain',{}).get(w['domain_id'],'업무를 직접 설명하는 현지 공식 자료'),
            'next_action_ko':'업무 결과를 직접 설명하는 현지 공식 자료 조사' if not rows else '공식 안내·공개 금융 폼 화면과 실제 표기 확보' if not has_screen else '상품·시장·채널을 맞춘 비교와 실무 적용성 검토'})
    write(ROOT/'dist/data/bank-ui-breadth-progress.json',d['breadth_progress'])
    if (ROOT/'data/bank-ui-capture-plan.json').exists():
        capture_plan=read(ROOT/'data/bank-ui-capture-plan.json')
        assert capture_plan['root_reviewed'] and not capture_plan['automatic_adoption']
        capture_cells=cells if capture_plan.get('collection_scope')=='all_scoped_works' else priority_cells
        assert capture_plan['scope_version']==d['version'] and capture_plan['country_work_cells']==len(capture_cells)
        capture_plan['counts']={'planned_country_work_cells':len(capture_cells),'planned_works':len({c['ui_work_id'] for c in capture_cells}),'function_linked_cells':sum(bool(c['example_ids']) for c in capture_cells),
            'cells_with_screen_references':sum(bool(c['screen_example_ids']) for c in capture_cells),'cells_without_screen':sum(not c['screen_example_ids'] for c in capture_cells),
            'official_guide_images':d['benchmark_counts']['official_guide_screens'],'public_web_captures':d['benchmark_counts']['public_web_captures'],
            'observed_app_captures':d['benchmark_counts']['observed_app_captures']}
        capture_plan['cells']=[]
        for c in capture_cells:
            paired=any(b.get('flow_steps') and b.get('policy_claims') for b in d['benchmarks'] if b['id'] in c['example_ids'])
            capture_plan['cells'].append({'work_id':c['ui_work_id'],'country':c['country'],'function_example_ids':c['example_ids'],
                'screen_example_ids':c['screen_example_ids'],'paired_path_and_conditions':bool(paired),
                'priority':1 if not c['example_ids'] else 2 if paired and not c['screen_example_ids'] else 3 if not c['screen_example_ids'] else 4,
                'next_action_ko':c['priority_audit']['next_action_ko'] if c['priority_audit'] else '현지 공식 기능 결과 근거 조사' if not c['example_ids'] else '공식 안내·공개 금융 폼 화면 확보' if not c['screen_example_ids'] else '상품·시장·채널을 맞춘 비교·조건 검토','provider_ids':c['provider_ids'],
                'market_applicability':'not_assessed','ready_for_use_review':'not_assessed'})
        d['capture_plan']=capture_plan
        write(ROOT/'dist/data/bank-ui-capture-plan.json',capture_plan)
    dest=ROOT/'dist/data';write(dest/'bank-ui.json',d)
    write(dest/'bank-ui-dispositions.json',{k:v for k,v in root.items() if k!='catalogue'})
    write(dest/'bank-ui-collection-plan.json',read(ROOT/'data/bank-ui-collection-plan.json'))
    out=io.StringIO();writer=csv.writer(out);writer.writerow(['scope_version','id','domain','module','title','actor_role','object_key','outcome_key','definition','completion','conditions','concept_sources','function_document_examples'])
    domains={x['id']:x['label'] for x in d['domains']}
    for w in works:
        writer.writerow([d['version'],w['id'],domains[w['domain_id']],w['module'],w['title'],w['actor_role'],w['object_key'],w['outcome_key'],w['definition'],w['completion'],' | '.join(w['condition_facets']),' | '.join(r['url'] for r in w['refs']),sum(w['id'] in b['ui_work_ids'] for b in d['benchmarks'])])
    (dest/'bank-ui-works.csv').write_text('\ufeff'+out.getvalue())
    out=io.StringIO();writer=csv.writer(out)
    writer.writerow(['scope_version','work_id','work_title','country','evidence_state','assessment_state','provider_ids','example_ids','screen_example_ids'])
    titles={w['id']:w['title'] for w in works}
    for c in cells:
        writer.writerow([d['version'],c['ui_work_id'],titles[c['ui_work_id']],c['country'],
            'screen_reference' if c['screen_example_ids'] else 'function_document' if c['example_ids'] else 'not_collected',
            c['assessment_state'],'|'.join(c['provider_ids']),'|'.join(c['example_ids']),'|'.join(c['screen_example_ids'])])
    (dest/'bank-ui-collection-matrix.csv').write_text('\ufeff'+out.getvalue())
    out=io.StringIO();writer=csv.writer(out)
    writer.writerow(['scope_version','work_id','work_title','country','example_ids','screen_example_ids','same_example_flow_and_condition','reviewed_source_ids','next_action'])
    for c in priority_cells:
        a=c['priority_audit'] or {}
        paired=any(b.get('flow_steps') and b.get('policy_claims') for b in d['benchmarks'] if b['id'] in c['example_ids'])
        writer.writerow([d['version'],c['ui_work_id'],titles[c['ui_work_id']],c['country'],'|'.join(c['example_ids']),
            '|'.join(c['screen_example_ids']),bool(paired),'|'.join(a.get('reviewed_source_ids',[])),a.get('next_action_ko','조사 예정')])
    (dest/'bank-ui-priority-matrix.csv').write_text('\ufeff'+out.getvalue())
    print(json.dumps({'bank_scope':d['version'],'counts':d['counts'],'benchmarks':d['benchmark_counts']},ensure_ascii=False))
    return d
if __name__=='__main__':build()
