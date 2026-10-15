"""Derive scope and benchmark coverage from reviewed records; no LLM counting."""
import datetime
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'dist/data'
def read(path): return json.loads(path.read_text())
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def selector_overlap(a, b):
    """Missing constraints are wildcards, not disjoint values."""
    return all(set(x if isinstance(x,list) else [x]) & set(b[k] if isinstance(b[k],list) else [b[k]])
               for k,x in a.items() if k in b)

def family_coverage(taxonomy, case_rows, entries, products):
    """Aggregate narrow UI observations without declaring every family branch covered."""
    mappings={m['case_id']:m for m in taxonomy['legacy_mappings']}
    assert set(mappings)=={c['id'] for c in case_rows}
    family_ids={f['id'] for f in taxonomy['families']}
    assert len(family_ids)==len(taxonomy['families'])
    assert all(m['family_id'] in family_ids for m in mappings.values())
    domains={d['id']:d['name_ko'] for d in taxonomy['domains']}
    refs=[dict(e,scenario_id=e['case_id'],case_id=mappings[e['case_id']]['family_id'],
               stage=mappings[e['case_id']]['stage']) for e in entries]
    rows=[]
    for f in taxonomy['families']:
        es=[e for e in refs if e['case_id']==f['id']];bench=[e for e in es if e['benchmark_eligible']]
        images=[e for e in bench if e['kind'] in ('live_web','guide_screen','product_image')]
        rows.append(dict(f,name=f['name_ko'],domain=domains[f['domain_id']],
            scenario_ids=[m['case_id'] for m in mappings.values() if m['family_id']==f['id']],
            has_reference=bool(es),has_benchmark=bool(bench),has_screen=bool(images),
            has_live_capture=any(e['kind']=='live_web' for e in images),
            company_count=len({e['company_id'] for e in bench}),
            product_ids=sorted({e['product_id'] for e in bench}),
            screen_refs=sorted({e['ref_id'] for e in images}),reference_ids=sorted({e['ref_id'] for e in es}),
            policy_conflict=any(e['policy_conflict'] for e in es),
            conditional_screen=any(e['relation']!='exact_flow' for e in images),flow_completeness='not_established'))
    metrics={'registered_cases':len(rows),'domains':len(domains)}
    metrics['iso_object_linked']=sum(bool(f['iso_concept_names']) for f in taxonomy['families'])
    metrics['wgss_extensions']=len(rows)-metrics['iso_object_linked']
    for field in ('reference','benchmark','screen','live_capture'):
        metrics['cases_with_'+field]=sum(r['has_'+field] for r in rows)
    metrics.update(cases_with_multiple_companies=sum(r['company_count']>=2 for r in rows),
        cases_without_reference=sum(not r['has_reference'] for r in rows),
        cases_without_benchmark=sum(not r['has_benchmark'] for r in rows))
    ds=[]
    for domain_id,name in domains.items():
        rs=[r for r in rows if r['domain_id']==domain_id]
        ds.append({'id':domain_id,'name':name,'total':len(rs),'benchmark':sum(r['has_benchmark'] for r in rs),
                   'screen':sum(r['has_screen'] for r in rs),'missing':sum(not r['has_benchmark'] for r in rs)})
    for p in products:
        es=[e for e in refs if e['product_id']==p['id']]
        p['benchmark_families']=len({e['case_id'] for e in es if e['benchmark_eligible']})
        p['screen_families']=len({e['case_id'] for e in es if e['kind'] in ('live_web','guide_screen','product_image')})
    return {'version':taxonomy['version'],'scope':taxonomy['scope'],'cases':rows,'entries':refs,
            'metrics':metrics,'domains':ds,'gap_closure':taxonomy['gap_closure'],
            'facets':taxonomy['facets'],'sources':taxonomy['sources'],'audit':taxonomy.get('audit',{}),
            'foundation':taxonomy['foundation'],
            'counting_rules':[
                f"분모는 WGSS v1의 고정된 {len(rows)}개 업무 케이스. 주요 업무대상 × 고객의 직접 목적을 고유 조합으로 집계.",
                '기존 42개 UI 상황은 상태·조건별 세부 사례이며 업무 케이스 총수와 별도로 보존.',
                '한 업무에 문구·화면 근거가 하나 이상 있으면 근거 있음으로 집계. 모든 상태·상품·시장 수집 완료를 의미하지 않음.',
                '정책만 있는 도움말은 참고 근거에 포함하되 문구·화면 벤치마크 분자에서 제외.',
                '같은 업무의 여러 자료·뷰포트는 업무 수를 늘리지 않음. 기업 수는 브랜드 그룹의 고유 개수.',
                'Citi 개인·CitiManager 법인은 별도 서비스, 같은 브랜드 그룹. Pay.UK는 UI 벤치마크 대상과 별도.',
                '국가·언어·채널·상품·조건이 다른 자료의 적용 적합성을 별도로 검토. 미공개 OS·UI 버전은 추정하지 않음.',
                '미수집 셀은 기능 미지원이나 해당 없음이라는 뜻이 아님.',
                'ISO 개념 연결과 고객 업무 정의는 구분. 제품 확장은 WGSS 정의로 표시하고 사전 버전으로 관리.'
            ]}

def build():
    cases=read(DATA/'cases.json');observations=read(DATA/'observations.json')
    source_data=read(DATA/'sources.json');sources={s['id']:s for s in source_data}
    screens=read(DATA/'screen-evidence.json')['records']
    registry=read(ROOT/'research/benchmark-targets.json');scope=read(ROOT/'research/coverage-scope.json')
    products=registry['products'];by_alias={a:p for p in products for a in p['aliases']}
    entries=[];excluded=[]
    for o in observations:
        product=by_alias[o['provider']]
        if not o['case_id']:
            excluded.append({'id':o['id'],'product_id':product['id'],'reason':o['mapping_status']});continue
        s=sources[o['source_id']]
        entries.append({'ref_id':o['id'],'case_id':o['case_id'],'product_id':product['id'],
            'company_id':product['company_id'],'benchmark_eligible':product['role']=='benchmark' and bool(o['expression']),
            'kind':'wording' if o['expression'] else 'policy','platform':'unknown','market':o['market'],'language':o['language'],
            'expression':o['expression'],'expression_role':o['expression_role'],'role':o['scene'],
            'relation':'mapped','scope':o['product_scope'],'source_id':o['source_id'],'source_url':s['url'],
            'checked_at':s['retrieved_at'],'ui_version':None,'policy_conflict':False})
    for s in screens:
        product=by_alias[s['provider']]
        for m in s['case_mappings']:
            platform='app_os_unspecified' if s['channel']=='app' else ('mobile_web' if s.get('viewport',{}).get('width',1000)<760 else 'web')
            entries.append({'ref_id':s['id'],'case_id':m['case_id'],'product_id':product['id'],
                'company_id':product['company_id'],'benchmark_eligible':product['role']=='benchmark',
                'kind':{'live_public_web':'live_web','official_guide_screen':'guide_screen','official_product_image':'product_image'}[s['evidence_kind']],
                'platform':platform,'market':s['market'],'language':s['language'],
                'expression':' / '.join(x['text'] for x in s['expressions']),'expression_role':'screen_labels',
                'role':s['screen_role'],'relation':m['relation'],'scope':s['product_scope'],
                'condition':m['condition'],'source_url':s['source_url'],'checked_at':s['last_checked_at'],
                'ui_version':s['ui_version'],'policy_conflict':s['policy_match']=='conflicts_current_help'})
    overlaps=[{'left':a['id'],'right':b['id']} for a,b in itertools.combinations(cases,2) if selector_overlap(a['selector'],b['selector'])]
    case_rows=[]
    for c in cases:
        refs=[e for e in entries if e['case_id']==c['id']]
        bench=[e for e in refs if e['benchmark_eligible']]
        images=[e for e in bench if e['kind'] in ('live_web','guide_screen','product_image')]
        groups={e['company_id'] for e in bench}
        case_rows.append({'id':c['id'],'name':c['name'],'domain':c['domain'],'selector':c['selector'],
            'has_reference':bool(refs),'has_benchmark':bool(bench),'has_screen':bool(images),
            'has_live_capture':any(e['kind']=='live_web' for e in images),
            'company_count':len(groups),'product_ids':sorted({e['product_id'] for e in bench}),
            'screen_refs':sorted({e['ref_id'] for e in images}),'reference_ids':sorted({e['ref_id'] for e in refs}),
            'policy_conflict':any(e['policy_conflict'] for e in refs),
            'conditional_screen':any(e['relation']!='exact_flow' for e in images),
            'flow_completeness':'not_established'})
    target_products=[p for p in products if p['role']=='benchmark']
    target_groups={p['company_id'] for p in target_products}
    metrics={'registered_cases':len(cases),'domains':len({c['domain'] for c in cases}),
        'cases_with_reference':sum(c['has_reference'] for c in case_rows),
        'cases_with_benchmark':sum(c['has_benchmark'] for c in case_rows),
        'cases_with_screen':sum(c['has_screen'] for c in case_rows),
        'cases_with_live_capture':sum(c['has_live_capture'] for c in case_rows),
        'cases_with_multiple_companies':sum(c['company_count']>=2 for c in case_rows),
        'cases_without_reference':sum(not c['has_reference'] for c in case_rows),
        'cases_without_benchmark':sum(not c['has_benchmark'] for c in case_rows),
        'screen_records':len(screens),'direct_web_records':sum(s['evidence_kind']=='live_public_web' for s in screens),
        'guide_records':sum(s['evidence_kind']=='official_guide_screen' for s in screens),
        'product_image_records':sum(s['evidence_kind']=='official_product_image' for s in screens),
        'authenticated_app_captures':0,'verified_ui_versions':sum(s['ui_version'] is not None for s in screens),
        'benchmark_company_targets':len(target_groups),'benchmark_product_targets':len(target_products),
        'companies_with_benchmark':len({e['company_id'] for e in entries if e['benchmark_eligible']}),
        'products_with_benchmark':len({e['product_id'] for e in entries if e['benchmark_eligible']}),
        'policy_reference_providers':sum(p['role']=='policy_reference' for p in products),
        'document_observations':len(observations),'mapped_document_observations':len(observations)-len(excluded),
        'document_sources':len(source_data),'excluded_observations':len(excluded)}
    domains=[]
    for name in dict.fromkeys(c['domain'] for c in cases):
        rows=[c for c in case_rows if c['domain']==name]
        domains.append({'name':name,'total':len(rows),'benchmark':sum(c['has_benchmark'] for c in rows),
            'screen':sum(c['has_screen'] for c in rows),'missing':sum(not c['has_benchmark'] for c in rows)})
    for p in products:
        refs=[e for e in entries if e['product_id']==p['id']]
        p['observed_markets']=sorted({e['market'] for e in refs})
        p['observed_languages']=sorted({e['language'] for e in refs})
        p['evidence_platforms']=sorted({e['platform'] for e in refs})
        p['benchmark_cases']=len({e['case_id'] for e in refs if e['benchmark_eligible']})
        p['screen_cases']=len({e['case_id'] for e in refs if e['kind'] in ('live_web','guide_screen','product_image')})
        p['reference_cases']=len({e['case_id'] for e in refs})
        p['status']='policy_only' if p['role']=='policy_reference' else ('collected' if p['benchmark_cases'] else 'not_collected')
        p['source_urls']=sorted(set(p['source_candidates'])|{e['source_url'] for e in refs})
    fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [DATA/'cases.json',DATA/'observations.json',DATA/'sources.json',DATA/'screen-evidence.json',
         ROOT/'research/benchmark-targets.json',ROOT/'research/coverage-scope.json']}
    result={'version':'0.1.0','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'input_sha256':fingerprints,'scope':scope,'metrics':metrics,'domains':domains,'cases':case_rows,
        'products':products,'entries':entries,'excluded':excluded,'selection_note':registry['selection_note'],
        'me_check':{'algorithm':'shared-key string/array constraint intersection; omitted keys are wildcards',
            'pair_count':len(cases)*(len(cases)-1)//2,'overlap_count':len(overlaps),'overlaps':overlaps,
            'ce_verified':False,'natural_language_me_verified':False},
        'counting_rules':[
            f'분모는 등록한 {len(cases)}개 상황. 전체 금융의 총수나 미등록 후보의 개수가 아님.',
            '문구·화면 근거가 있는 상황은 적격 expression 또는 검토된 화면이 하나 이상 있는 case_id의 합집합.',
            '정책만 있는 도움말은 전체 참고 근거에는 포함하되 문구·화면 벤치마크 분자에서 제외.',
            'Pay.UK는 제도 정책 출처로 기업 UI 벤치마크 수에 포함하지 않음.',
            'Citi 개인·CitiManager 법인은 두 서비스, 같은 Citi 브랜드 그룹. 2곳 기준은 브랜드 그룹으로 계산.',
            '같은 상황의 여러 이미지·뷰포트는 한 상황으로 중복 제거. 요청·접수·완료의 전체 흐름 확보를 뜻하지 않음.',
            '도움말 채널은 미확인. 앱 화면의 OS가 미공개이면 iOS/Android로 배분하지 않음.',
            '대상 미수집은 기능 미지원이나 해당 없음이라는 뜻이 아님. 시장·언어·상품이 다른 자료의 비교 적합성은 별도 검토.'
        ]}
    reviews=[('화면 문구 검토 · 이전 수집분',ROOT/'research/screen-sonnet-review.json'),
             ('범위·정의 검토',ROOT/'research/quality-steward-scope.json'),
             ('커버리지 규칙 검토 · 초기',ROOT/'research/quality-steward-coverage.json')]
    latest=ROOT/'research/quality-steward/quality-steward-coverage.json'
    if latest.exists() and read(latest).get('status')=='succeeded':
        reviews.append(('현재 대상·커버리지 검토',latest))
    if all(path.exists() for _,path in reviews):
        runs=[]
        for role,path in reviews:
            review=read(path);usage=review['usage']
            runs.append({'role':role,'model':review.get('model_returned',review.get('model')),
                'run_at':review.get('run_at',review.get('reviewed_at')),'input_tokens':usage['prompt_tokens'],
                'output_tokens':usage['completion_tokens'],'total_tokens':usage['total_tokens'],
                'status':'성공 · AI 보조 검토','input_sha256':review['input_sha256'],
                'report':str(path.relative_to(ROOT))})
        result['quality_steward']={'status':'reviewed','name':'Scope & Coverage Steward',
            'role':'사용자를 대신해 전체 범위·상황별 비교 근거·기업과 플랫폼 목록의 빈칸과 오해를 점검합니다.',
            'independent_human_review':False,'always_running':False,'runs':runs,
            'total_tokens':sum(r['total_tokens'] for r in runs),'findings':[
                {'title':'42개를 금융 전체의 총수로 표시하지 않기','disposition':'반영: 등록 정의를 분모로 쓰고 전체 MECE 미검증, 빠진 영역을 함께 공개했습니다.'},
                {'title':'요청·접수·효력 발생과 완료의 균형','disposition':'추가 정의 필요: D03/S03/F02 등의 결과 단계와 C04의 복합 의도를 점검 대상으로 남겼습니다. 현황을 완성으로 표시하지 않습니다.'},
                {'title':'상품·채널·화면 종류를 합치지 않기','disposition':'반영: Citi 개인·법인, 공개 웹·가이드·제품 예시, 채널·OS 미공개를 구분했습니다.'},
                {'title':'모델의 숫자와 해석을 원본으로 검산하기','disposition':'정정: 근거 없는 상황 25개와 문구·화면 없는 상황 27개를 구분했습니다. D03를 효력확정으로 해석한 모델 제안도 채택하지 않았습니다.'}
            ]}
    taxonomy_path=DATA/'case-taxonomy.json'
    if taxonomy_path.exists():
        taxonomy=read(taxonomy_path)
        result['taxonomy']=family_coverage(taxonomy,case_rows,entries,products)
        result['input_sha256'][str(taxonomy_path.relative_to(ROOT))]=hashlib.sha256(taxonomy_path.read_bytes()).hexdigest()
        for p in (DATA/'iso-concept-index.json',ROOT/'research/iso-domain-model-inventory.json'):
            result['input_sha256'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
        result['default_unit']='family'
        result['version']='0.2.0'
        if result.get('quality_steward'):
            result['quality_steward']['findings']=[
                {'title':'범위와 업무 단위를 확정','disposition':f"반영: WGSS v1 {len(taxonomy['families'])}개 업무 케이스를 고정했습니다. 기존 42개 UI 상황은 상태·조건별 연결 사례로 보존했습니다."},
                {'title':'누락 영역을 실제 정의로 편입','disposition':'반영: 이전 12개 누락 영역을 업무 케이스와 공통 상태·조건에 연결했습니다. 정의 완료와 벤치마크 확보는 별도로 집계합니다.'},
                {'title':'상품·채널·화면 종류를 합치지 않기','disposition':'반영: Citi 개인·법인, 공개 웹·가이드·제품 예시, 채널·OS 미공개를 구분했습니다.'},
                {'title':'ISO 개념과 WGSS 해석을 구분','disposition':'반영: 저장소의 실제 업무 객체 식별자를 검산합니다. 고객 목적·업무 분류는 WGSS 설계이며 ISO가 정한 UX 케이스 총수가 아닙니다.'}]
            for run in taxonomy['audit']['model_runs']:
                usage=run.get('usage') or {}
                status=run['status']
                label=('HTTP 실패 · 사용량 미확인' if run['http_status']!=200 else
                       'JSON 검토 완료' if status=='succeeded' else
                       '부분 출력 · 편집 검토' if run['finish_reason']=='length' else 'JSON 정규화 · 편집 검토')
                result['quality_steward']['runs'].append({'role':run['mode'],'model':run.get('model_returned') or run['model_requested'],
                    'run_at':run['run_at'],'input_tokens':usage.get('prompt_tokens'),
                    'output_tokens':usage.get('completion_tokens'),'total_tokens':usage.get('total_tokens'),
                    'status':label,'input_sha256':run['prompt_sha256'],
                    'report':f"research/taxonomy-v1/{run['mode']}.json"})
            result['quality_steward']['total_tokens']=sum(r['total_tokens'] or 0 for r in result['quality_steward']['runs'])
            result['quality_steward']['unknown_usage_runs']=sum(r['total_tokens'] is None for r in result['quality_steward']['runs'])
            result['quality_steward']['taxonomy_focused_review_valid']=taxonomy['audit']['focused_review_valid']
    bank=ROOT/'dist/data/bank-ui.json'
    if bank.exists():
        scoped=read(bank)
        result['bank_customer_ui']={'scope_version':scoped['version'],'status':scoped['status'],'denominator':len(scoped['works']),'counts':scoped['counts'],'benchmarks':scoped['benchmark_counts'],'global_financial_industry_mece_approved':False}
    write(DATA/'coverage.json',result)
    print(json.dumps({'status':'coverage_built','legacy_ui_metrics':metrics,
        'fixed_v1_metrics':result.get('taxonomy',{}).get('metrics'),'selector_overlaps':overlaps},ensure_ascii=False))
    return result
if __name__=='__main__': build()
