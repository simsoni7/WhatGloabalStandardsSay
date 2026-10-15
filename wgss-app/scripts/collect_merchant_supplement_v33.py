import concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/merchant-bank-supplement-v33-20261013';C.RUN=RUN
assert not(RUN/'FROZEN').exists()
T=[('merchant-barclay-resource','barclaycard-uk','GB','en-GB','https://www.barclaycard.co.uk/business/help-and-support/accepting-payments/taking-payments/resources','trade'),('merchant-barclay-close','barclaycard-uk','GB','en-GB','https://www.barclaycard.co.uk/business/help/accepting-payments/how-do-i-close-my-pdq-agreement','trade'),('merchant-barclay-statement','barclaycard-uk','GB','en-GB','https://www.barclaycard.co.uk/business/help-and-support/accepting-payments/taking-payments/understand-account-statement','trade')]
s=C.read(R/'research/source-store/merchant-dib-supplement-v33-20261013/sources.json')[0]
for label,sid in [('Export LC Document Presentation Cover','merchant-dib-lcpresentation'),('Export Collection Documents Covering Letter','merchant-dib-exportcollection'),('Fund Transfer Request Under Wakala Murabaha Open Account','merchant-dib-fundtransfer')]:
 l=next(l for l in s.get('links',[])if l['label']==label);T.append((sid,'dib-ae','AE','en',l['url'],'trade'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as p:S=list(p.map(C.fetch,T))
extra=[]
s=next(s for s in S if s['id']=='merchant-barclay-resource')
# Only PDFs concretely linked from current own resource index. Preserve2025/2026 contract cohorts.
for i,l in enumerate(s.get('links',[])):
 if '.pdf' in l['url']and any(k in l['url'].lower()for k in ['merchant','procedure']):extra.append(('merchant-barclay-pdf-'+str(i),'barclaycard-uk','GB','en-GB',l['url'],'trade'))
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as p:S+=list(p.map(C.fetch,extra[:4]))
C.write(RUN/'sources.json',S);(RUN/'FROZEN').write_text('Own legalbank acquirer andDIBAE operative forms; AE requires explicitrootmarketstudyupdate.\n');print([(s['id'],s['state'],len(s.get('text','')))for s in S])
