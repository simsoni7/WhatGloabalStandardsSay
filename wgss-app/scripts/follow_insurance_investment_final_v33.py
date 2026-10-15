"""New source-family followups, actual publisherlinks only."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-final-sources-v33-20261013';base.RUN=RUN
T=[
('ip33-chesnara-trust','chesnara-life-uk','GB','en-GB','https://www.chesnaralife.co.uk/customers/trusts-protection/','wealth'),
('ip33-hti-securities','htisec-hk','HK','en','https://www.htisec.com/en-us/securities','wealth'),
('ip33-hti-futures','htisec-hk','HK','en','https://www.htisec.com/en-us/futures-and-options','wealth'),
('ip33-aia-advice','aia-hk','HK','en','https://www.aia.com.hk/en/help-and-support/information-and-faq/useful-information/about-aia-e-services/list-of-aia-e-advice-correspondences','protection'),
('ip33-aia-forms','aia-hk','HK','en','https://www.aia.com.hk/en/help-and-support/forms-individuals','protection')]
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(base.fetch,T))
 extra=[]
 for s in ss:
  if s['id']=='ip33-chesnara-trust':
   for a in s.get('links',[]):
    if ('Flexible Trust' in a['label'] or 'using our Trust' in a['label']) and '.pdf' in a['url']:extra.append(('ip33-chesnara-trust-follow-'+str(len(extra)),s['provider_id'],s['country'],s['language'],a['url'],'wealth'))
  if s['id']=='ip33-hti-futures':
   for a in s.get('links',[]):
    if 'User Guide' in a['label']:extra.append(('ip33-hti-guide-follow-'+str(len(extra)),s['provider_id'],s['country'],s['language'],a['url'],'wealth'))
  if s['id']=='ip33-aia-forms':
   for a in s.get('links',[]):
    if 'Change of Insured under Newborn' in a['label'] or 'Request for Change Form of Basic' in a['label']:extra.append(('ip33-aia-change-'+str(len(extra)),s['provider_id'],s['country'],s['language'],a['url'],'protection'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss+=list(p.map(base.fetch,extra))
 base.write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('Ownsource links frozen; currentproviders/stages explicit.\n');print(json.dumps({'records':len(ss),'inventory':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]}))
