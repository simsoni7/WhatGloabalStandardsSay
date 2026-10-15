"""Independent binding, semantic-boundary, and original-byte checks for v44."""
import json,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist';checks=[]
def check(n,v):assert v,n;checks.append(n)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
x=read(D/'data/public-flow-cases-v44.json');words=read(D/'data/wording-references-v44.json')['items'];cat=read(D/'data/user-work-catalog-v44.json');bank=read(D/'data/bank-ui.json');tasks={t['id']:t for t in cat['tasks']};places={p['work_id']:p for p in cat['work_placements']};cases={c['id']:c for c in x['cases']}
check('canonical216 byte-bound and unchanged',len(bank['works'])==216 and sha(D/'data/bank-ui.json')==cat['source_catalog']['sha256'])
check('216 complete unique placements, no new global MECE claim',set(places)=={w['id'] for w in bank['works']} and not cat['global_mece_approved'] and all(p['primary_task_id'] in tasks for p in places.values()))
check('task membership follows explicit placement, not facet counts',all(set(t['work_ids'])=={p['work_id'] for p in places.values() if p['primary_task_id']==t['id'] or t['id'] in p['additional_task_ids']} for t in cat['tasks']))
check('accountopening excludes virtual and group service',tasks['account-opening']['work_ids']==['WGSS-UI-014E9CA936CF'] and places['WGSS-UI-0DFD4428014D']['primary_task_id']=='virtual-account' and places['WGSS-UI-E99864B2D351']['primary_task_id']=='group-account-service')
check('prepaid use separate from card issuance',places['WGSS-UI-1126AA49A830']['primary_task_id']=='prepaid-service' and tasks['card-application']['work_ids']==['WGSS-UI-3826A2FD05F2'])
check('longterm card loan excludes cashadvance alias',all('현금서비스' not in f['aliases'] for tid in ['loan-application','loan-contract'] for f in tasks[tid]['product_facets'] if f['id']=='card-loan'))
check('overdraft and transfer facets contextonly not multiplying results',all(f.get('context_only') and not f['work_ids'] for tid in ['transfer','credit-line-contract','credit-line-use'] for f in tasks[tid]['product_facets']))
check('registration/login/recovery independent work purposes',len({tasks[t]['work_ids'][0] for t in ['signup','login','password-recovery','password-change','kyc']})==5)
check('22 cases distinct from 8bounded complete8partial6failed',len(cases)==22 and x['counts']['case_states']=={'public-segment-complete':8,'partial':8,'access-failed':6} and len(x['attempts'])==73)
check('3failed cases have no false reference image',all(not cases[c]['steps'] for c in ['citi-us-card-application','monzo-gb-account-opening','toss-kr-account-opening']))
check('no canonical or installed-app financial admissions',x['canonical_financial_work_admissions']==0 and x['public_segment_not_completed_financial_transaction'] and all(not c['authenticated'] and not c['input_or_submit_executed'] for c in cases.values()))
steps=[s for c in cases.values() for s in c['steps']];by={(c['id'],s['id']):s for c in cases.values() for s in c['steps']}
check('29 stage records 25 intact originals sourcebound dates',len(steps)==29 and len({s['image_sha256'] for s in steps})==25 and all(sha(D/s['image_path'])==s['image_sha256'] and s['root_visual_reviewed'] and s['source_url']==s['final_url'] and s['source_url'].startswith('https://') and datetime.datetime.fromisoformat(s['collected_at']).tzinfo for s in steps))
check('local flow chain continuity from explicit public URL entry',all(s['navigation_from']==(None if i==0 else c['steps'][i-1]['id']) for c in cases.values() for i,s in enumerate(c['steps'])))
check('ZIP input separate from normal account application',cases['citi-us-account-opening']['steps'][0]['stage_code']=='eligibility' and cases['citi-us-account-opening']['terminal']['observed_text']=='Where Do You Live?')
check('OCBC modal not installed-app boundary',cases['ocbc-sg-account-opening']['steps'][1]['stage_code']=='eligibility' and cases['ocbc-sg-account-opening']['case_state']=='partial')
check('47 literal records own source/image/date/label',len(words)==47 and all(w['label'] in by[(w['case_id'],w['step_id'])]['observed_labels'] and w['source_url']==by[(w['case_id'],w['step_id'])]['source_url'] and w['image_sha256']==by[(w['case_id'],w['step_id'])]['image_sha256'] and w['collected_at']==by[(w['case_id'],w['step_id'])]['collected_at'] and w['view_href'].startswith('#reference-flow/'+w['case_id']+'?page=') for w in words))
for version,n,count in [('v39',20,0),('v42',13,46)]:
 old=read(D/f'data/public-screen-assets-{version}.json');check(version+' historical original cohort unchanged and bound',len(old['assets'])==n and all(sha(D/a['image_path'])==a['image_sha256'] for a in old['assets']))
 if count:check(version+' historical literal records retained',len(read(D/f'data/wording-references-{version}.json')['items'])==count)
check('dictionary original172 plus46 plus47 contextual records',len(read(D/'data/wording-references-v38.json')['items'])+46+47==265)
print(json.dumps({'public_flow_evidence_v44':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
