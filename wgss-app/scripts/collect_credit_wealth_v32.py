"""One-time exact originals for lending/trade/wealth/FX; no database mutation."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/credit-wealth-collection-v32-20261013';base.RUN=RUN
T=[
('cw-hk-fx','hsbc-hk','HK','en','https://www.hsbc.com.hk/investments/products/foreign-exchange/','fx'),
('cw-hk-biz-fx','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/products/foreign-exchange-spot-fx?sort=mostRecent','fx'),
('cw-hk-tradepay','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/products/hsbc-tradepay','lending'),
('cw-hk-finance-forms','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/help-centre/business-forms/financing-and-commercial-cards-forms','lending'),
('cw-hk-wpl','hsbc-hk','HK','en','https://www.hsbc.com.hk/wealth-financing/products/wealth-portfolio-lending/','lending'),
('cw-hk-loans-faq','hsbc-hk','HK','en','https://www.hsbc.com.hk/help/faq/loans/','lending'),
('cw-hk-invest-faq','hsbc-hk','HK','en','https://www.hsbc.com.hk/help/faq/investments/','wealth'),
('cw-hk-mobile-faq','hsbc-hk','HK','en','https://servicing.hsbc.com.hk/help/faq/mobile-banking/','wealth'),
('cw-hk-ipo','hsbc-hk','HK','en','https://www.hsbc.com.hk/investments/products/ipo/','wealth'),
('cw-gb-fidelity-howto','fidelity-uk','GB','en-GB','https://www.fidelity.co.uk/how-to-guide/','wealth'),
('cw-gb-fidelity-client-guide','fidelity-uk','GB','en-GB','https://www.fidelity.co.uk/media/Advised%20Client/pdfs/guides/client-guide-to-fnw.pdf','wealth'),
('cw-gb-hl-advice','hl-uk','GB','en-GB','https://www.hl.co.uk/financial-advice','wealth'),
('cw-gb-hl-limits','hl-uk','GB','en-GB','https://www.hl.co.uk/shares/share-dealing/limits','wealth'),
('cw-gb-liquidity','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/corporate/solutions/investments/liquidity-liability-and-investments','trade'),
('cw-hk-business-collect','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/products/hsbc-business-collect?DCSext.nav=tabordion','trade'),
('cw-hk-merchant-guide','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/-/media/media/hong-kong/pdfs/products/hsbc-dms-merchant-guide.pdf','trade'),
('cw-kr-creditline','kakaobank','KR','ko','https://www.kakaobank.com/products/creditLine','lending')]
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(base.fetch,T))
 extra=[]
 for s in ss:
  if s['id']=='cw-hk-finance-forms':wanted=['Loan Drawdown Instruction','Guarantee by individual']
  elif s['id']=='cw-hk-wpl':wanted=['step-by-step','Step-by-step','Terms and conditions (effective']
  elif s['id']=='cw-gb-fidelity-howto':wanted=['Tracking your performance']
  else:continue
  seen=set()
  for label in wanted:
   for a in s.get('links',[]):
    if label.lower() in a['label'].lower() and a['url'] not in seen:
     seen.add(a['url']);extra.append((s['id']+'-follow-'+str(len(seen)),s['provider_id'],s['country'],s['language'],a['url'],s['research_family']))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss+=list(p.map(base.fetch,extra))
 base.write(RUN/'sources.json',ss);base.write(RUN/'baseline.json',json.loads((R/'dist/data/bank-ui.json').read_text()));(RUN/'FROZEN').write_text('New originals frozen; followed URLs from actual own links. No admission.\n')
 print(json.dumps({'sources':len(ss),'fetched':sum(s['state']=='fetched_pending_review' for s in ss),'inventory':[(s['id'],len(s.get('text','')),len(s.get('pdf_pages',[])),s['state']) for s in ss]},ensure_ascii=False))
