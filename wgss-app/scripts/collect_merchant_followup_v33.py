import concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/merchant-followup-v33-20261013';C.RUN=RUN
assert not(RUN/'FROZEN').exists()
T=[('merchant-hsbc-uk-mivision','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/solutions/mivision','cards'),('merchant-hsbc-uk-cardpdf','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/-/media/library/business-uk/pdfs/corporate-card.pdf','cards'),('merchant-hsbc-hk-formindex','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/help-centre/business-forms','trade'),('merchant-natwest-amend','natwest-uk','GB','en-GB','https://www.natwest.com/support-centre/help-with-your-product/current-accounts/how-can-i-amend-a-standing-order.html','payments')]
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as p:S=list(p.map(C.fetch,T))
extra=[]
for s in S:
 if s['id']=='merchant-hsbc-hk-formindex':
  for l in s.get('links',[]):
   if l['label']=='See forms' and 'payment' in l['url']:extra.append(('merchant-hsbc-hk-payforms','hsbc-hk','HK','en',l['url'],'trade'))
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as p:S+=list(p.map(C.fetch,extra))
extra=[]
for s in S:
 if s['id']=='merchant-hsbc-hk-payforms':
  for i,l in enumerate(s.get('links',[])):
   if '.pdf' in l['url'] and any(z in l['label'].lower()for z in ['cashier','direct debit','standing','autopay']):extra.append(('merchant-hk-payform-'+str(i),'hsbc-hk','HK','en',l['url'],'trade'))
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as p:S+=list(p.map(C.fetch,extra[:6]))
C.write(RUN/'sources.json',S);(RUN/'FROZEN').write_text('Immutable original followups.\n');print([(s['id'],s['state'],len(s.get('text','')))for s in S])
