# One-time v29 recorder/preparer. Already executed; frozen files must not be overwritten.
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/bank-screen-expansion-v29-20261012';RUN=R/'research/source-store/bank-screen-jobs-v29-20261012'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();ws=read(R/'data/bank-ui-root-decisions.json')['catalogue']['works']+[x['proposal'] for x in read(R/'research/source-store/bank-scope-v29-20261012/root-proposals.json')['rows'] if x['kind']=='source_counterexample_new_result'];families={'investment':['wealth','payments','identity','servicing'],'pension':['protection','wealth','identity','servicing'],'insurance':['protection','identity','servicing'],'cards-payments':['cards','payments','identity','servicing'],'cards':['cards','payments','identity','servicing'],'secondary-market-islamic':['alternative','accounts','payments','identity','servicing']}
for p in (SRC/'inputs').glob('*.json'):
 j=read(p);s=next(s for s in read(SRC/'sources.json') if s['id']==j['input']['sources'][0]['id']);allowed=[w for w in ws if w['domain_id'] in families[s['research_family']]];compact=[{k:w[k] for k in ['id','title','definition','completion']} for w in allowed];jid=j['id']+'-bounded';job=dict(j,id=jid,input=dict(j['input'],works=compact),work_ids=[w['id'] for w in allowed]);job['instructions']=j['instructions'].replace('Use only the216 frozen existing+proposed work IDs.','Use only the assigned frozen work IDs. Other work families are separately reviewed, do not infer exclusions.');write(RUN/'inputs'/f'{jid}.json',job)
write(RUN/'sources.json',read(SRC/'sources.json'));(RUN/'FROZEN').write_text('Bounded family inputs; original collector inputs retained, not executed.\n');print({'jobs':len(list((RUN/'inputs').glob('*.json')))})
