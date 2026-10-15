"""Bounded fresh followups; preserve originalcollection immutable."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-followup-v33-20261013';base.RUN=RUN
T=[
('ip33-empf-pledge','empf-hk','HK','en','https://www.empf.org.hk/servicepledge?language_id=1','protection'),
('ip33-aviva-appeal','aviva-uk','GB','en-GB','https://protection.aviva.com/globalassets/life/documents/2817_gci_techguide.pdf','protection'),
('ip33-hsbc-pims','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/investments/advice/premier-investment-management-service/','wealth'),
('ip33-hsbc-life-trs','hsbc-life-uk','GB','en-GB','https://www.life.hsbc.co.uk/customers/trs','wealth'),
('ip33-htisec-home','htisec-hk','HK','en','https://www.htisec.com/en','wealth')]
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(base.fetch,T))
 extra=[]
 for s in ss:
  if s['id']=='ip33-hsbc-pims':
   for a in s.get('links',[]):
    if 'Terms and Conditions' in a['label'] and '.pdf' in a['url']:extra.append(('ip33-hsbc-pims-terms',s['provider_id'],s['country'],s['language'],a['url'],'wealth'));break
  if s['id']=='ip33-hsbc-life-trs':
   for a in s.get('links',[]):
    if 'Gift' in a['label'] and '.pdf' in a['url']:extra.append(('ip33-life-gift-'+str(len(extra)),s['provider_id'],s['country'],s['language'],a['url'],'wealth'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss+=list(p.map(base.fetch,extra))
 base.write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('Followup actualownlinks and frozen sourceoriginals, no automaticadmission.\n');print(json.dumps({'records':len(ss),'inventory':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]}))
