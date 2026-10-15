"""Followed contract clauses assigned to bounded exact extraction jobs."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/alternative-contracts-v32-20261013';RUN=R/'research/source-store/alternative-contract-extraction-v32-20261013'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();ss=read(SRC/'sources.json');base=read(R/'research/source-store/alternative-extraction-v32-20261013/inputs/v32-alt-alt-uphold-staking-1.json');assigned=[]
for s in ss:
 if s['state']!='fetched_pending_review' or s['id']=='alt-alrayan-documents':continue
 t=s['text'];segments=[t[i:i+14000] for i in range(0,len(t),13500)]
 for i,seg in enumerate(segments):
  j=json.loads(json.dumps(base));jid='v32-alt-contract-'+s['id']+'-'+str(i+1);j.update(id=jid,sections={s['id']:seg},expected_ids=[s['id']]);j['input']['sources']=[dict(id=s['id'],provider_id=s['provider_id'],country=s['country'],language=s['language'],url=s['url'],publisher_text=seg)];j['instructions']+=' Explicit financial result procedure or own contractual capability is a useful source-described function reference even without observing a real account transaction; do NOT reject only because no actual UI execution observed. However purely abstract definitions, offers awaiting acceptance, and ambiguous request vs contract establishment are insufficient. Preserve result and actor; useragreement for UK users supports market here, operatorcrypto≠depositbank. AlRayan final settlement customerpurchase of remaining share requires operative transfer/right evidence, settling conventionalloan shorthand or setting rentalrate alone is not acquiredownership. No invented currentUIlabels.';write(RUN/'inputs'/f'{jid}.json',j);assigned.append(jid)
write(RUN/'sources.json',ss);write(RUN/'assigned.json',assigned);(RUN/'FROZEN').write_text('Followed official contract body assigned with overlap. No automatic admission.\n');print({'jobs':len(assigned)})
