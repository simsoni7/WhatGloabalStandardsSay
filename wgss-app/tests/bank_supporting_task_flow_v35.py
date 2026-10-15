"""Source/branch/role checks for process supplements, without new UI observations."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
d=read('dist/data/bank-ui.json');base=read('data/bank-ui-baseline-v34.json');ledger=read('data/bank-ui-supporting-task-flow-v35-decisions.json')
private={b['id']:b for b in read('data/bank-ui-benchmark-dispositions.json')['examples']};public={b['id']:b for b in d['benchmarks']};old={b['id']:b for b in base['benchmarks']};checks=[];proof_count=0
def check(n,v):assert v,n;checks.append(n)
check('work definitions, counts, geography and actual-capture counts unchanged',d['works']==base['works'] and d['benchmark_counts']==base['benchmark_counts'] and d['collection_counts']==base['collection_counts'] and not ledger['scope_change'] and ledger['observed_screens_added']==ledger['admitted_examples_added']==0)
check('only two existing references gain explicit process-source supplements',{x['id'] for x in ledger['metadata_changes']}=={'BANK-BENCH-303','BANK-BENCH-338'} and all(public[k]==old[k] for k in public if k not in {'BANK-BENCH-303','BANK-BENCH-338'}))
for row in ledger['metadata_changes']:
 b=private[row['id']];check('root after is actual admitted metadata '+b['id'],b==row['after'] and row['before']['source_id']==b['source_id'] and b['ui_work_ids']==row['before']['ui_work_ids'])
 for s in b['supporting_process_sources']:
  source=next(v for v in read(s['source_manifest']) if v['id']==s['native_source_id']);assert hashlib.sha256(source['text'].encode()).hexdigest()==s['text_sha256'];assert hashlib.sha256((R/source['snapshot_path']/source['raw_filename']).read_bytes()).hexdigest()==s['raw_sha256']
  assert (s['country'],s['provider_id'])==(b['country'],b['provider_id']) and not s['observed_app_screen'] and not s['current_ui_verified']
  ps=[x['proof'] for k in ['steps','eligibility','state_conditions','role_permissions'] for x in s.get(k,[])]+([s['applicability_proof']] if s.get('applicability_proof') else [])
  for p in ps:assert source['text'][p['start']:p['end']]==p['excerpt'];proof_count+=1
  public_s=public[b['id']]['supporting_process_sources'][0];assert '"excerpt"' not in json.dumps(public_s)
check('all15 exact supplemental ranges bound to own source bytes',proof_count==15)
c=private['BANK-BENCH-338']['supporting_process_sources'][0]
check('DURIAN expressly included, not only conventional savings','Daily Unrestricted Investment Account-i with CIMB Islamic Bank' in c['applicability_proof']['excerpt'])
check('four official process headings not observed field labels',[x['label'] for x in c['steps']]==['Step 1: Contact Details','Step 2: Verify your Identity','Step 3: Application Form','Step 4: Fund Your Account'] and c['expression_role']=='document_described_process' and 'SEP2026' in c['document_version'])
check('OTP, face and other-bank funding not invented','OTP via SMS' in c['steps'][0]['proof']['excerpt'] and 'front and back' in c['steps'][1]['proof']['excerpt'] and 'facial recognition' in c['steps'][1]['proof']['excerpt'] and 'another financial institution in Malaysia' in c['steps'][3]['proof']['excerpt'])
check('opened not usable; and/or maintained; seven days not promised approval','and/or your debit card activation' in c['state_conditions'][0]['proof']['excerpt'] and 'inoperable' in c['state_conditions'][0]['proof']['excerpt'] and 'initial deposit amount' in c['state_conditions'][0]['proof']['excerpt'] and 'reserves the right' in c['state_conditions'][1]['proof']['excerpt'] and 'automatically close' in c['state_conditions'][2]['proof']['excerpt'])
roles=private['BANK-BENCH-303']['supporting_process_sources'][0]['role_permissions'];check('ViewOnly explicit refund denial versus Analyst refund allowed',{x['role_label']:x['refund_permission'] for x in roles}=={'Administrator':'documented_allowed','Analyst':'documented_allowed','View Only':'documented_denied','Support Associate':'documented_allowed'} and all(x['role_label'] in x['proof']['excerpt'] for x in roles) and "Some of what this role can't do" in roles[2]['proof']['excerpt'])
check('independent model critique advisory, no human benefit claim',all(read(p)['result']['rows'][0]['status']=='pass' for p in ledger['source_reviews']) and ledger['root_reviewed'] and not ledger['automatic_adoption'] and not ledger['actual_user_utility_measured'] and not ledger['independent_human_review'])
print(json.dumps({'bank_supporting_task_flow_v35':'passed','checks':len(checks),'exact_proofs':proof_count,'items':checks},ensure_ascii=False))
