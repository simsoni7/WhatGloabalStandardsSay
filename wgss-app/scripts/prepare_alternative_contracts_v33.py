"""Retain failed large bilingual jobs and cover them with bounded replacements."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/alternative-contract-extraction-v33-20261013';OLD=R/'research/source-store/alternative-extraction-v33-20261013'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists();template=read(next((OLD/'inputs').glob('*.json')));jobs=[];replacements=[]
 def create(s,t,name,old=None):
  j=copy.deepcopy(template);j.update(id=name,model='claude-sonnet-5',max_tokens=8000,expected_ids=[s['id']],sections={s['id']:t});j['input']['sources']=[dict(id=s['id'],provider_id=s['provider_id'],country=s['country'],language=s['language'],url=s['url'],publisher_text=t)];j['instructions']+=' IMPORTANT exact evidence must be short contiguous substrings under180characters copied from suppliednormalisedtext, not a full bilingualparagraph. Maximum2features. No reconstructed linebreaks; Arabic/Englishinterleaving is real and cannot be silentlyrepaired. native_expression short exact operativeheading/label under90characters. Partial segment boundaries are not wholecontract; distinguishpartyroles and tiedclauses. Salamcard includes contractual customerSeller vs bankBuyer, upfront PurchasePrice andspecifiedcommoditydelivery, notcardnameglossary alone. Ijara saleundertaking ejercised aftercompletepayments vs purchaseobligation default/earlyterminationdistinct. JSON only.';write(RUN/'inputs'/f'{name}.json',j);jobs.append(name)
  if old:replacements.append(dict(old_job=old,new_job=name))
 for p in OLD.glob('inputs/*.json'):
  old=read(p)
  if list((OLD/'reviews'/old['id']).glob('*/proposal.json')):continue
  s=old['input']['sources'][0];t=s['publisher_text']
  for i in range(0,len(t),4500):create(s,t[i:i+4500],old['id']+'-bounded-'+str(i//4500+1),old['id'])
 for s in read(R/'research/source-store/alternative-contracts-v33-20261013/sources.json'):
  if s['state']!='fetched_pending_review' or s['id']=='alt-dib-card-index':continue
  for i in range(0,len(s['text']),6500):create(s,s['text'][i:i+6500],'v33-contract-'+s['id']+'-'+str(i//6500+1))
 write(RUN/'assigned.json',jobs);write(RUN/'replacement-jobs.json',replacements);(RUN/'FROZEN').write_text('Original failures preserved, all assigned input segments covered by bounded replacements.\n');print({'jobs':len(jobs),'replacement_jobs':len(replacements)})
