import concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/merchant-operative-v33-20261013';C.RUN=RUN
assert not(RUN/'FROZEN').exists()
S0=C.read(R/'research/source-store/merchant-followup-v33-20261013/sources.json');s=next(s for s in S0 if s['id']=='merchant-hsbc-hk-payforms');T=[('merchant-stripe-manual-allocation','stripe-uk','GB','en','https://docs.stripe.com/invoicing/apply-payments','trade')]
for label,ident in [('Direct Debit Authorisation (Generic Set-up)','merchant-hk-ddamandate'),("HKD Cashier's Order Purchase Form",'merchant-hk-cashierorder')]:
 l=next(l for l in s['links']if l['label'].startswith(label));T.append((ident,'hsbc-hk','HK','en',l['url'],'trade'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as p:S=list(p.map(C.fetch,T))
C.write(RUN/'sources.json',S);(RUN/'FROZEN').write_text('Concrete linked operative pages/forms originals.\n');print([(s['id'],s['state'],len(s.get('text','')))for s in S])
