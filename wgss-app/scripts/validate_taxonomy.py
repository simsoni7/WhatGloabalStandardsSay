"""Validate the released catalogue and its provenance; never count with an LLM."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def validate():
    t=read('dist/data/case-taxonomy.json');index=read('dist/data/iso-concept-index.json')
    families=t['families'];ids={f['id'] for f in families};domains={d['id'] for d in t['domains']}
    concepts={c['name']:c for c in index['concepts']};checks=[]
    assert t['version']=='1.0.0' and t['scope']['status']=='frozen'
    assert t['scope']['global_certification'] is False
    checks.append('versioned operational scope is frozen without ISO or universal certification')
    assert len(ids)==len(families) and len(domains)==len(t['domains'])
    assert len({(f['object'],f['intent']) for f in families})==len(families)
    assert all(f['domain_id'] in domains for f in families)
    checks.append('unique family IDs and object-intent pairs resolve to declared domains')
    assert all(any(f['domain_id']==d for f in families) for d in domains)
    for f in families:
        assert all(f[k] for k in ('object','intent','name_ko','definition_ko','includes','excludes','source_basis'))
        assert isinstance(f['variant_axes'],list)
    checks.append('each family has a definition, inclusion, exclusion and counting boundary')
    for f in families:
        assert all(n in concepts for n in f['iso_concept_names']),f['id']
        assert [concepts[n]['id'] for n in f['iso_concept_names']]==f['iso_concept_ids']
        assert f['mapping_basis'] in ('ISO_object_WGSS_intent','WGSS_extension')
        assert bool(f['iso_concept_names'])==(f['mapping_basis']=='ISO_object_WGSS_intent')
    checks.append('ISO anchors match actual identifiers in the pinned complete component index')
    scenarios=read('dist/data/cases.json');mappings=t['legacy_mappings']
    assert {m['case_id'] for m in mappings}=={c['id'] for c in scenarios}
    assert len(mappings)==len(scenarios)==42
    assert all(m['family_id'] in ids and m['stage'] in t['facets']['lifecycle_stage'] for m in mappings)
    checks.append('all original 42 UI scenarios map once to a valid family and lifecycle stage')
    assert {g['id'] for g in t['gap_closure']}=={f'G{i:02}' for i in range(1,13)}
    assert all(g['family_ids'] and set(g['family_ids'])<=ids and g['explanation_ko'] for g in t['gap_closure'])
    checks.append('all 12 prior gaps resolve to defined families without claiming benchmark collection')
    fixtures=read('research/taxonomy-boundary-fixtures.json')
    by_key={(f['object'],f['intent']):f['id'] for f in families}
    for fixture in fixtures['items']:
        actual=[by_key.get((purpose['object'],purpose['intent'])) for purpose in fixture['purposes']]
        assert actual==fixture['expected_family_ids'],fixture['id']
        assert all(x in ids for x in actual)
    assert set(f['domain_id'] for f in families)<=set(fixtures['covered_domains'])
    checks.append(f"{len(fixtures['items'])} reviewed boundary and compound-purpose fixtures resolve")
    cv=read('dist/data/coverage.json');fc=cv['taxonomy']
    assert len(fc['cases'])==fc['metrics']['registered_cases']==len(families)
    assert sum(d['total'] for d in fc['domains'])==len(families)
    assert len(fc['entries'])==len(cv['entries'])
    old={(e['ref_id'],e['product_id'],e['case_id']) for e in cv['entries']}
    assert {(e['ref_id'],e['product_id'],e['scenario_id']) for e in fc['entries']}==old
    checks.append('coverage retains every original observation and deduplicates by family')
    for f in fc['cases']:
        es=[e for e in fc['entries'] if e['case_id']==f['id'] and e['benchmark_eligible']]
        assert f['company_count']==len({e['company_id'] for e in es})
        assert f['has_benchmark']==bool(es) and f['flow_completeness']=='not_established'
    checks.append('partial family references never imply all stages or conditions are collected')
    report={'status':'passed','checks':len(checks),'items':checks,'version':t['version'],
        'fixed_case_total':len(families),'domain_total':len(domains),
        'iso_object_linked':sum(bool(f['iso_concept_names']) for f in families),
        'wgss_extensions':sum(not f['iso_concept_names'] for f in families),
        'fixture_count':len(fixtures['items']),
        'catalogue_sha256':hashlib.sha256((ROOT/'dist/data/case-taxonomy.json').read_bytes()).hexdigest(),
        'independent_human_review':False,'universal_mece_proof':False}
    (ROOT/'research/taxonomy-validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False));return report
if __name__=='__main__':validate()
