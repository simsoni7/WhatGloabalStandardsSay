"""Reconcile all retained Bedrock jobs against separate root dispositions."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/definition-completion-20261004'
q=json.loads((R/'data/definition-completion-dispositions.json').read_text());w=json.loads((R/'dist/data/operations.json').read_text());k=json.loads((R/'dist/data/business-backbone.json').read_text());ids={x['id'] for x in w['works']}
historical=w['version']!=q['output_version']
if historical:
 # Historical completion totals describe that release, not all later releases.
 snapshots=q['validation_snapshots']
 for name,path in [('operations','output-operations.json'),('backbone','output-backbone.json')]:
  assert hashlib.sha256((P/path).read_bytes()).hexdigest()==snapshots[name]['sha256']
 w=json.loads((P/'output-operations.json').read_text());k=json.loads((P/'output-backbone.json').read_text())
 assert w['version']==q['output_version'];ids={x['id'] for x in w['works']}
assert q['root_adjudicated'] and not q['automatic_adoption'] and not q['global_mece_approved']
jobs=[json.loads(f.read_text()) for f in (P/'reviews').glob('*/*/proposal.json')]
assert len(jobs)==12 and len({x['job_id'] for x in jobs})==12
covered={(x['job_id'],x['proposal_id']) for x in q['decisions']+q['inventory_definition_decisions']}
for job in jobs:
 for d in job['proposal']['definition_proposals']:assert (job['job_id'],d['local_id']) in covered,('unadjudicated proposal',job['job_id'],d['local_id'])
 assigned={x['id'] for x in json.loads((P/'inputs'/(job['job_id']+'.json')).read_text())['scope'].get('inventory',[])}
 for s in job['proposal']['inventory_dispositions']:
  if s['inventory_id'] in assigned:assert s['inventory_id'] in {x['inventory_id'] for x in q['inventory_decisions']}
for d in q['decisions']+q['inventory_definition_decisions']:assert set(d['work_ids'])<=ids,(d['job_id'],d['proposal_id'])
assert len(q['inventory_decisions'])==37 and q['progress']['newly_mapped_navigation_terms']==34
assert q['progress']['registered_definitions']==len(ids) and q['progress']['unresolved_definitions']==sum(x['status']=='unresolved' for x in w['works'])
assert q['progress']['current_gap_steps']==k['product_quality']['gap_step_count'] and q['progress']['official_product_sources']==len(k['product_sources'])
assert len([x for x in w['works'] if x['id'].startswith('WGSS-COMPLETION-')])==q['progress']['source_checked_new_definitions']==16
print(json.dumps({'status':'passed','bedrock_jobs':len(jobs),'definition_proposals_disposed':len(covered),'official_target_bodies_reviewed':len(q['inventory_decisions']),'source_checked_additions':16,'whole_mece_approved':False}))
