"""Frozen own-publisher v33 protection and investment gap collection."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-collection-v33-20261013';base.RUN=RUN
T=[
('ip33-empf-payment','empf-hk','HK','en','https://www.empf.org.hk/page/paymentMethods?language_id=1','protection'),
('ip33-empf-member','empf-hk','HK','en','https://www.empf.org.hk/FAQ/member/?search=how+to+register+EMPF','protection'),
('ip33-empf-employer','empf-hk','HK','en','https://www.empf.org.hk/faq/employer/?language_id=1','protection'),
('ip33-samsung-terms','samsung-fire','KR','ko','https://www.samsungfire.com/publication/pdf/ZPB316050_0_20240401_file1.pdf','protection'),
('ip33-samsung-coolingoff','samsung-fire','KR','ko','https://direct.samsungfire.com/mydirect/PP020405_001.html','protection'),
('ip33-aviva-contact','aviva-uk','GB','en-GB','https://www.aviva.co.uk/help-and-support/life-cover-and-protection/life-insurance/','protection'),
('ip33-aviva-home-cancel','aviva-uk','GB','en-GB','https://www.aviva.co.uk/insurance/home-products/home-insurance/knowledge-centre/cancelling-your-home-insurance/','protection'),
('ip33-aviva-leaving','aviva-uk','GB','en-GB','https://www.aviva.co.uk/insurance/life-products/life-insurance/thinking-of-leaving-us/','protection'),
('ip33-aviva-car-change','aviva-uk','GB','en-GB','https://www.aviva.co.uk/insurance/motor/car-insurance/knowledge-centre/transferring-car-insurance-to-another-car/','protection'),
('ip33-aviva-business','aviva-uk','GB','en-GB','https://businessdirect.aviva.co.uk/MComm/htmlfiles/faq_AVIVA.html','protection'),
('ip33-aviva-life-terms','aviva-uk','GB','en-GB','https://www.aviva.co.uk/adviser/documents/view/sd08001c.pdf','protection'),
('ip33-ii-voting','ii-uk','GB','en-GB','https://www.ii.co.uk/investing-with-ii/shareholder-voting-information','wealth'),
('ip33-ii-appvote','ii-uk','GB','en-GB','https://www.ii.co.uk/analysis-commentary/interactive-investor-launches-major-voting-innovation-app-ii528574','wealth'),
('ip33-hl-report','hl-uk','GB','en-GB','https://www.hl.co.uk/financial-advice/insights/what-to-expect-from-your-first-meeting-with-an-hl-adviser','wealth'),
('ip33-schwab-options','schwab-uk','GB','en-GB','https://www.schwab.co.uk/investment-products/options-trading','wealth'),
('ip33-hsbc-fxexecution','hsbc-uk','GB','en-GB','https://www.business.hsbc.com/-/media/media/gbm-global/gbm-refresh/financial-regulations/attachments/best-execution-globalfx-annex-client-disclosure-statement.pdf','wealth'),
('ip33-hsbc-life-trust','hsbc-life-uk','GB','en-GB','https://www.life.hsbc.co.uk/customers/trusts/','wealth'),
('ip33-hk-order','htisec-hk','HK','en','https://www.htisec.com/power_sec/help_eng/change.htm','wealth'),
('ip33-hsbc-legacy','hsbc-life-hk','HK','en','https://forms.hsbc.com.hk/content/dam/hsbc/hk/docs/insurance/booklets/2024-sep-legacy.pdf','wealth')]
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(base.fetch,T))
 base.write(RUN/'sources.json',ss);base.write(RUN/'baseline.json',json.loads((R/'dist/data/bank-ui.json').read_text()));(RUN/'FROZEN').write_text('Exact own public bytes frozen. Document titles and HTTPsuccess are not admissions.\n')
 print(json.dumps({'records':len(ss),'fetched':sum(s['state']=='fetched_pending_review' for s in ss),'inventory':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]},ensure_ascii=False))
