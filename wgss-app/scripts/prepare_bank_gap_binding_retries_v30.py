import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/bank-gap-candidates-v30-20261012';RUN=R/'research/source-store/bank-gap-critic-retries-v30-20261012'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();orig=read(SRC/'inputs/v30-critic-1.json')
for i in range(0,6,2):
 rows=orig['input']['rows'][i:i+2];ids=[r['candidate']['id'] for r in rows];j=dict(orig,id='v30-binding-pair-'+str(i//2+1),input=dict(rows=rows),expected_ids=ids,candidate_bindings={k:orig['candidate_bindings'][k] for k in ids});j['instructions']+=' Prior output swapped hk-trade-form-0 with hk-trade-form-1. Copy each input candidate source_id/work_id/native_expression exactly. Never infer another source with similar name. This two-row group is complete.';write(RUN/'inputs'/f"{j['id']}.json",j)
write(RUN/'sources.json',read(SRC/'sources.json'));(RUN/'FROZEN').write_text('Three bound pairs replace failed source-assignment whole group.\n')
