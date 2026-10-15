"""Current own linked trust deed, insurance ownership and trading instructions."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-contracts-v33-20261013';base.RUN=RUN
ss0=json.loads((R/'research/source-store/insurance-investment-final-sources-v33-20261013/sources.json').read_text());T=[]
for s in ss0:
 for a in s.get('links',[]):
  take=s['id']=='ip33-chesnara-trust' and any(q in a['url'] for q in ['a-customer-guide-to-our-flexible-trust','protection-flexible-trust-uk']) or s['id']=='ip33-aia-forms' and 'Ownership / Trustee' in a['label'] or s['id']=='ip33-hti-futures' and 'User Manual' in a['label']
  if take and a['url'] not in [t[4] for t in T]:T.append(('ip33-contract-'+str(len(T)),s['provider_id'],s['country'],s['language'],a['url'],s['research_family']))
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(base.fetch,T))
 extra=[]
 for s in ss:
  if s['provider_id']=='chesnara-life-uk':
   for a in s.get('links',[]):
    if '.pdf' in a['url']:extra.append(('ip33-deed-'+str(len(extra)),s['provider_id'],s['country'],s['language'],a['url'],s['research_family']))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss+=list(p.map(base.fetch,extra))
 base.write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('Native currentpublisher actualURLs only retained.\n');print({'records':len(ss),'inventory':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]})
