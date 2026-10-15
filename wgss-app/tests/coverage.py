"""Coverage must preserve provenance and count situations instead of screenshots."""
from pathlib import Path
import hashlib
import importlib.util
import itertools
import json

ROOT=Path(__file__).resolve().parents[1]
load=lambda p:json.loads((ROOT/p).read_text())
cv=load('dist/data/coverage.json');m=cv['metrics'];checks=[]
def ok(s):checks.append(s)
cases=load('dist/data/cases.json');obs=load('dist/data/observations.json')
screens=load('dist/data/screen-evidence.json')['records']
assert m['registered_cases']==len(cases)==42 and len(cv['cases'])==42
assert sum(d['total'] for d in cv['domains'])==42 and m['domains']==9
assert cv['scope']['global_total'] is None
assert cv['taxonomy']['scope']['status']=='frozen'
assert not cv['me_check']['ce_verified'] and not cv['me_check']['natural_language_me_verified']
ok('registered denominator and domain totals do not claim universal MECE')
assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected for path,expected in cv['input_sha256'].items())
ok('coverage is derived from the current source input snapshot')
assert {r['id'] for r in cv['cases'] if r['has_reference']}=={o['case_id'] for o in obs if o['case_id']}|{x['case_id'] for s in screens for x in s['case_mappings']}
assert m['cases_with_reference']==17 and m['cases_without_reference']==25
assert m['cases_with_benchmark']==15 and m['cases_without_benchmark']==27
ok('reference coverage and wording-screen benchmark coverage use different numerators')
assert m['screen_records']==7 and m['cases_with_screen']==4 and m['cases_with_live_capture']==1
assert {e['case_id'] for e in cv['entries'] if e['product_id']=='WISE' and e['kind']=='live_web'}=={'F01'}
ok('two live Wise viewports remain one covered situation')
assert all(not e['benchmark_eligible'] for e in cv['entries'] if e['kind']=='policy' or e['product_id']=='PAYUK')
assert m['benchmark_product_targets']==8 and m['benchmark_company_targets']==7 and m['policy_reference_providers']==1
ok('policy-only references and scheme provider do not inflate UI benchmark diversity')
assert {e['case_id'] for e in cv['entries'] if e['product_id']=='CITI_RETAIL'}=={'C01','C02'}
assert {e['case_id'] for e in cv['entries'] if e['product_id']=='CITI_MANAGER'}=={'C03'}
assert {p['company_id'] for p in cv['products'] if p['id'].startswith('CITI_')}=={'CITI'}
assert next(e for e in cv['entries'] if e['ref_id']=='UI004')['relation']=='conditional_branch'
ok('Citi products stay separate while company diversity deduplicates the brand')
assert next(p for p in cv['products'] if p['id']=='TOSS')['status']=='not_collected'
assert not any(e['product_id']=='TOSS' for e in cv['entries'])
assert len(cv['excluded'])==1 and cv['excluded'][0]['id']=='O36'
ok('unmapped sources and target-only Toss do not become invented benchmarks')
assert all(e['platform']=='unknown' for e in cv['entries'] if e['ref_id'].startswith('O'))
assert {e['platform'] for e in cv['entries'] if e['ref_id'] in ('UI004','UI005')}=={'app_os_unspecified'}
assert not any(e['platform'] in ('ios','android') for e in cv['entries'])
assert m['verified_ui_versions']==m['authenticated_app_captures']==0
ok('planned platforms and unknown OS are never promoted to observed native apps')
assert {e['ref_id'] for e in cv['entries'] if e['policy_conflict']}=={'UI001','UI003'}
assert all(e['case_id']=='D03' for e in cv['entries'] if e['ref_id'].startswith('UI00') and e['product_id']=='PAYINFO')
ok('stale policy and debit-vs-standing-order boundaries survive aggregation')
assert all(e['case_id'] in {c['id'] for c in cases} and e['product_id'] in {p['id'] for p in cv['products']} for e in cv['entries'])
assert len(cv['entries'])==len({(e['case_id'],e['product_id'],e['ref_id']) for e in cv['entries']})
assert m['cases_with_multiple_companies']==7
ok('matrix references are unique and resolve to real cases and declared products')
spec=importlib.util.spec_from_file_location('coverage_builder',ROOT/'scripts/build_coverage.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
fixtures=[{}, {'object':'card'}, {'object':'transfer'}, {'object':['card','transfer'],'action':'status'}, {'object':'card','action':['status','restore']}, {'object':'card','action':'restore'}]
world=[dict(zip(('object','action'),vs)) for vs in itertools.product(('card','transfer'),('status','restore'))]
matches=lambda s,w:all(w[k] in (v if isinstance(v,list) else [v]) for k,v in s.items())
for a,b in itertools.product(fixtures,repeat=2):
    oracle=any(matches(a,w) and matches(b,w) for w in world)
    assert module.selector_overlap(a,b)==oracle
assert cv['me_check']['pair_count']==861 and cv['me_check']['overlap_count']==0
ok('finite-world oracle verifies omitted constraints are wildcards, without proving completeness')
assert len(cv['taxonomy']['gap_closure'])==12 and all(g['family_ids'] for g in cv['taxonomy']['gap_closure'])
ok('previous scope gaps are closed by defined families in the frozen denominator')
steward=cv['quality_steward']
assert steward['total_tokens']==sum((r['input_tokens'] or 0)+(r['output_tokens'] or 0) for r in steward['runs'])
assert not steward['independent_human_review'] and not steward['always_running']
ok('quality-agent token totals and execution limits are explicit')
report={'status':'passed','checks':len(checks),'items':checks,'registered_cases':42,'global_mece_verified':False}
(ROOT/'research/coverage-validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
