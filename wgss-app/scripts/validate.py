import json,copy
from pathlib import Path
from jsonschema import Draft202012Validator
R=Path(__file__).resolve().parents[1];D=R/'dist/data'
load=lambda n:json.loads((D/n).read_text())
cases,obs,sources=load('cases.json'),load('observations.json'),load('sources.json')
checks=[]
def check(name,cond):
 if not cond:raise AssertionError(name)
 checks.append(name)
for name,file in [('case','cases'),('observation','observations')]:
 schema=load(name+'.schema.json');Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(load(file+'.json'));checks.append(name+' JSON Schema')
cs={c['id'] for c in cases};ss={s['id'] for s in sources}
check('unique IDs',len(cs)==len(cases) and len(ss)==len(sources) and len({r['id'] for r in obs})==len(obs))
check('case relations resolve',all(x in cs for c in cases for x in c['related']))
check('source and case foreign keys',all(r['source_id'] in ss and (r['case_id'] in cs or r['case_id'] is None) for r in obs))
check('known conditions have evidence',all(c['source_id'] in ss and c['locator'] for r in obs for c in r['claims'] if c['state']=='known'))
check('unknown is not false',all(c['value'] is None for r in obs for c in r['claims'] if c['state']=='unknown'))
check('all critical fields present',all(set(next(c for c in cases if c['id']==r['case_id'])['critical_fields'])<=set(x['field'] for x in r['claims']) for r in obs if r['case_id']))
check('no duplicate fields in a record',all(len(r['claims'])==len({c['field'] for c in r['claims']}) for r in obs))
check('no fabricated screenshot or human verification',all(not r['observed_in_app'] and not r['independent_review'] for r in obs))
check('undefined market retained',all(r['market']=='unspecified' for r in obs if r['provider']=='Wise'))
check('out of scope explicitly retained',any(r['mapping_status']=='out_of_scope' and r['facts']['object']=='money_request' for r in obs))
check('UI role separated from missing UI',all((r['expression'] is None)==(r['expression_role']=='no_ui_label') for r in obs))
mut=copy.deepcopy(obs);mut[0]['claims'][0]['source_id']=None
check('schema rejects known condition without source',bool(list(Draft202012Validator(load('observation.schema.json')).iter_errors(mut))))
mut=copy.deepcopy(obs);mut[0]['claims'][0]['state']='unknown';mut[0]['claims'][0]['value']='blocked'
check('schema rejects unknown with asserted value',bool(list(Draft202012Validator(load('observation.schema.json')).iter_errors(mut))))
tasks=load('design-tasks.json')
check('task IDs are unique',len({t['id'] for t in tasks})==len(tasks))
check('task route definitions are version pinned',all(r['selector']==next(c for c in cases if c['id']==r['case_id'])['selector'] and r['selector_ref']['version']==next(c for c in cases if c['id']==r['case_id'])['version'] for t in tasks for r in t['routes']))
check('route scopes and default screen roles resolve',all(t['default_role'] in {'confirmation','result','detail'} and all(r['target_scope'] in {s['id'] for s in t['scopes']} and r['templates'] for r in t['routes']) for t in tasks))
check('result templates require a runtime signal',all('status_signal' in r.get('role_fields',{}).get('result',[]) for t in tasks for r in t['routes'] if 'result' in r['templates']))
check('recommendation not strengthened to obligation',all(next(c for c in r['claims'] if c['field']=='creditor_notification')['value']=='recommended' for r in obs if r['id'] in {'O39','O40'}))
check('feature expression and policy provenance may differ',all(r['source_id']=='S17' and all(c['source_id']=='S16' for c in r['claims'] if c['state']=='known') for r in obs if r['id'] in {'O37','O38'}))
summary=dict(schema_checks=len(checks),schema_passed=len(checks),schema_items=checks)
(D/'structural-report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
