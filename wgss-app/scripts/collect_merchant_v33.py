"""One-time bounded official merchant/payment source collection; no auto adoption."""
import concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/merchant-collection-v33-20261013';C.RUN=RUN
if __name__=='__main__':
 assert not(RUN/'FROZEN').exists()
 T=[
 ('merchant-stripe-uk-contract','stripe-uk','GB','en-GB','https://stripe.com/gb/legal/ssa','trade'),
 ('merchant-stripe-uk-party','stripe-uk','GB','en-GB','https://support.stripe.com/questions/your-contract-with-stripe-stripe-services-agreement-(ssa)-overview-faq?locale=en-GB','trade'),
 ('merchant-stripe-refund','stripe-uk','GB','en','https://docs.stripe.com/refunds','trade'),
 ('merchant-stripe-hold','stripe-uk','GB','en','https://docs.stripe.com/payments/place-a-hold-on-a-payment-method','trade'),
 ('merchant-stripe-dashboard-pay','stripe-uk','GB','en','https://docs.stripe.com/payments/dashboard','trade'),
 ('merchant-stripe-reconcile','stripe-uk','GB','en','https://docs.stripe.com/invoicing/bank-transfer','trade'),
 ('merchant-stripe-bank-transfer','stripe-uk','GB','en','https://docs.stripe.com/payments/bank-transfers','accounts'),
 ('merchant-stripe-bacs','stripe-uk','GB','en','https://docs.stripe.com/payments/payment-methods/bacs-debit','payments'),
 ('merchant-stripe-bacs-ui','stripe-uk','GB','en-GB','https://stripe.com/gb/resources/more/how-to-set-up-direct-debit-for-customers-a-guide-for-uk-businesses','payments'),
 ('merchant-stripe-bacs-product','stripe-uk','GB','en','https://stripe.com/payments/bacs-debit','payments'),
 ('merchant-stripe-close','stripe-uk','GB','en-GB','https://support.stripe.com/questions/close-a-stripe-account?locale=en-GB','trade'),
 ('merchant-paypal-uk-legal','paypal-uk','GB','en-GB','https://www.paypal.com/uk/legalhub/paypal/useragreement-full','trade'),
 ('merchant-paypal-refund','paypal-uk','GB','en-GB','https://www.paypal.com/uk/cshelp/article/how-do-i-issue-a-refund-help101','trade'),
 ('merchant-paypal-close','paypal-uk','GB','en-GB','https://www.paypal.com/uk/cshelp/article/how-do-i-close-my-paypal-account-help247','trade'),
 ('merchant-hsbc-uk-pool','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/corporate/solutions/investments/liquidity-liability-and-investments','trade'),
 ('merchant-hsbc-uk-virtual','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/-/media/library/business-uk/pdfs/client-factsheet.pdf','accounts'),
 ('merchant-hsbc-hk-forms','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/help-centre/business-forms/payment-making-forms','trade'),
 ('merchant-hsbc-hk-imports','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/corporate/growth/imports','trade'),
 ('merchant-hsbc-hk-notices','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/regulations/resource-centre-important-hsbc-payments-information','trade'),
 ('merchant-hsbc-uk-corporate','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/products-and-solutions/commercial-cards/corporate-card','cards'),
 ('merchant-hsbc-uk-current','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/products/small-business-bank-account','trade')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:S=list(p.map(C.fetch,T))
 # Follow linked operative forms, not guessed PDF filenames.
 extra=[]
 for s in S:
  if s['id']=='merchant-hsbc-hk-forms':
   for i,l in enumerate(s.get('links',[])):
    if '.pdf' in l['url'] and any(z in l['label'].lower() for z in ['cashier','direct debit','standing','autopay']):extra.append(('merchant-hk-form-'+str(i),s['provider_id'],s['country'],s['language'],l['url'],'trade'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:S+=list(p.map(C.fetch,extra[:6]))
 C.write(RUN/'sources.json',S);C.write(RUN/'baseline.json',C.read(R/'dist/data/bank-ui.json'));(RUN/'FROZEN').write_text('Immutable originals; docs global scope must be anchored in own UK contract and product availability.\n')
 print([(s['id'],s['state'],len(s.get('text','')))for s in S])
