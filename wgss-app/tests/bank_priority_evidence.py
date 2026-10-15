# Historical v1/v28 oracle retained; current v1.1 is independently checked in bank_expansion_v29.py.
"""Priority semantic, exact provenance, review completeness and honest quality gates."""
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v28.json');ledger=read(R/'data/bank-ui-collection-v25-decisions.json');checks=[]
def check(name,ok):assert ok,name;checks.append(name)
pids={id for g in d['collection_plan']['priority_groups'] for id in g['ui_work_ids']};a=ledger['priority_cell_dispositions']
check('scope stays 214 and all 32 priority works retained',len(d['works'])==214 and len(pids)==32 and not ledger['scope_change'])
check('all 96 reviews have distinct work-country identities',{(x['ui_work_id'],x['country']) for x in a}=={(id,c) for id in pids for c in ['KR','GB','HK']} and len(a)==96)
sources={batch['prefix']+':'+s['id']:s for batch in ledger['source_batches'] for s in read(R/batch['manifest'])}
for x in a:
 assert x['root_reviewed'] and not x['automatic_adoption'] and not x['provider_unsupported'] and x['next_action_ko']
 assert x['reviewed_source_ids'] and all(sources[id]['country']==x['country'] and sources[id].get('text') for id in x['reviewed_source_ids'])
check('a review is bounded local publisher research, never unsupported assertion',True)
rows=[b for b in d['benchmarks'] if b['source_id'].startswith(('V25:','V25S:'))]
check('all root admitted rows agree with preserved decision ledger',{b['id'] for b in rows}=={x['example_id'] for x in ledger['admitted_examples']} and len(rows)==43)
private_rows={b['id']:b for b in read(R/'data/bank-ui-benchmark-dispositions.json')['examples']}
for public_b in rows:
 b=private_rows[public_b['id']]
 s=sources[b['source_id']];text=(R/s['snapshot_path']/'normalized.txt').read_text()
 assert hashlib.sha256(text.encode()).hexdigest()==b['text_sha256'] and hashlib.sha256((R/s['snapshot_path']/'source.html').read_bytes()).hexdigest()==b['raw_sha256']
 for q in [b['proof']]+([b['function_proof']] if b.get('function_proof') else [])+b.get('flow_step_proofs',[])+[x['proof'] for x in b.get('policy_claims',[])]:
  assert text[q['start']:q['end']]==q['excerpt']
 assert len(b.get('flow_steps',[]))==len(b.get('flow_step_proofs',[]))
 assert not b['observed_app_screen'] and b['verified_ui_version'] is None
check('every label, step and qualifier has own immutable exact source range',True)
images=read(R/'research/source-store/bank-priority-v25-20261011/guide-images.json');by={x['sha256']:x for x in images}
for b in rows:
 if not b.get('screen_evidence'):continue
 e=b['screen_evidence'];i=by[e['image_sha256']];s=sources[i['source_id']]
 assert i['source_id']==b['source_id'] and any(a['url']==e['asset_url'] for a in s['images'])
 assert hashlib.sha256((R/i['private_path']).read_bytes()).hexdigest()==hashlib.sha256((R/'dist'/e['image_path']).read_bytes()).hexdigest()==e['image_sha256']
 assert e['visual_review']=='root_visual_checked'
check('new official guide assets are original and locally scoped',True)
check('device removal never admitted as withdrawing a lost notice',not any(b['source_id']=='V25:uk-mobile' and 'WGSS-UI-D4DF22E05F69' in b['ui_work_ids'] for b in rows))
check('direct debit never becomes standing order from Chinese homonym',not any(b['source_id']=='V25S:hk-zh-mobile-faq-www' and b['expression'] in ['自動轉賬','更改自動轉賬指示','刪除自動轉賬指示'] and set(b['ui_work_ids'])&{'WGSS-UI-0E34959F2794','WGSS-UI-37D8DD5B6DD8','WGSS-UI-CC40B2B0BFB3'} for b in rows))
check('scheduled single transfer not recurrent mandate',all(b['ui_work_ids']==['WGSS-UI-E7352823594F'] for b in rows if b['expression']=='예약이체'))
check('document upload not admitted as credit amendment application',not any(b['source_id']=='V25:hk-zh-limit' for b in rows))
check('priority arithmetic keeps practical evidence distinct',d['priority_collection']=={'works':32,'cells':96,'reviewed_cells':96,'works_with_examples':32,'linked_cells':78,'screen_cells':16,'flow_and_condition_cells':39})
csvrows=list(csv.DictReader((R/'dist/data/bank-ui-priority-matrix.csv').open(encoding='utf-8-sig')))
check('download includes every priority gap and next action',len(csvrows)==96 and sum(bool(x['example_ids']) for x in csvrows)==78 and all(x['next_action'] for x in csvrows))
check('no legal force invented for receipt example',all('법적' in b['conditions'] for b in rows if b['source_id']=='V25S:kakao-bills'))
print(json.dumps({'bank_priority_evidence':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
