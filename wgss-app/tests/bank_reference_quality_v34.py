"""Check source-specific controls and PIDM facts without promoting them to UI observations."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
d=read('data/bank-ui-baseline-v34.json') if (R/'data/bank-ui-baseline-v34.json').exists() else read('dist/data/bank-ui.json');base=read('data/bank-ui-baseline-v33.json')
ledger=read('data/bank-ui-reference-quality-v34-decisions.json')
private={b['id']:b for b in read('data/bank-ui-benchmark-dispositions.json')['examples']}
if (R/'data/bank-ui-supporting-task-flow-v35-decisions.json').exists():
 for r in read('data/bank-ui-supporting-task-flow-v35-decisions.json')['metadata_changes']:private[r['id']]=r['before']
public={b['id']:b for b in d['benchmarks']};old={b['id']:b for b in base['benchmarks']}
checks=[]
def check(n,v):assert v,n;checks.append(n)
check('216 work identities, coverage and country-study scope unchanged',d['works']==base['works'] and d['benchmark_counts']==base['benchmark_counts'] and d['collection_matrix']==base['collection_matrix'] and not ledger['scope_change'])
changed={r['id'] for r in ledger['metadata_changes']}
check('only four explicitly rooted metadata changes',changed=={'BANK-BENCH-303','BANK-BENCH-338','BANK-BENCH-339','BANK-BENCH-340'} and all(public[k]==old[k] for k in public if k not in changed))
sources={batch['prefix']+':'+s['id']:s for batch in ledger['source_batches'] for s in read(batch['manifest'])}
for row in ledger['metadata_changes']:
 b=private[row['id']];source=sources[b['source_id']]
 check('root after and original SHA binding '+b['id'],b==row['after'] and hashlib.sha256(source['text'].encode()).hexdigest()==b['text_sha256'] and hashlib.sha256((R/source['snapshot_path']/source['raw_filename']).read_bytes()).hexdigest()==b['raw_sha256'])
 for p in [x['proof'] for x in b['policy_claims']]+[x['proof'] for x in b.get('documented_ui_controls',[])]:assert source['text'][p['start']:p['end']]==p['excerpt']
 check('exact facts not new app/version observations '+b['id'],not b['observed_app_screen'] and not b['current_ui_verified'] and not b['verified_ui_version'])
controls=private['BANK-BENCH-303']['documented_ui_controls']
check('actions, option and input data distinct',[(x['label'],x['role']) for x in controls]==[('Refund payment','document_described_action'),('Refund','document_described_action'),('Other','document_described_option'),('refund amount','document_described_input_data')] and all(not x['observed_current_ui'] for x in controls))
check('partial amount and reason requirement source-bound',all(x['source_id']=='M33:merchant-stripe-refund' for x in controls) and 'must add a note' in controls[2]['proof']['excerpt'] and 'partial refund' in controls[3]['proof']['excerpt'])
for bid in ['BANK-BENCH-338','BANK-BENCH-339','BANK-BENCH-340']:
 b=private[bid];claim=b['policy_claims'][-1]
 check('PIDM exclusion distinct from capital guarantee '+bid,'PIDM' in claim['proof']['excerpt'] and ('NOT PROTECTED' in claim['proof']['excerpt'] or 'TIDAK DILINDUNGI' in claim['proof']['excerpt']) and '원금 미보장과 구분' in claim['description_ko'] and b['reference_document_version']==old[bid]['reference_document_version'])
check('private proof excerpts redacted from public nested controls and claims',all('excerpt' not in p for bid in changed for p in [x['proof'] for x in public[bid]['policy_claims']]+[x['proof'] for x in public[bid].get('documented_ui_controls',[])]))
q=d['practitioner_review'];check('three concrete work-country tasks retained',len(q['tasks'])==3 and {(t['work_id'],t['country']) for t in q['tasks']}=={(private['BANK-BENCH-303']['ui_work_ids'][0],'GB'),(private['BANK-BENCH-325']['ui_work_ids'][0],'KR'),(private['BANK-BENCH-338']['ui_work_ids'][0],'MY')})
check('no utility or independent human approval',not q['practitioner_utility_measured'] and not q['independent_human_review'] and q['actual_time_error_measurements']==0 and not ledger['automatic_adoption'])
check('four actual successful model outputs retained',len(ledger['practitioner_model_reviews'])==3 and all(read(p)['automatic_adoption'] is False for p in ledger['practitioner_model_reviews']+[ledger['source_review']]) and ledger['successful_bedrock_jobs']==4)
print(json.dumps({'bank_reference_quality_v34':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
