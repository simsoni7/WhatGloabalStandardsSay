"""Frozen public originals for UK and explicitly labelled secondary-market research."""
import concurrent.futures
import collect_bank_gaps_v30 as c
c.RUN=c.R/'research/source-store/alternative-collection-v33-20261013'
if __name__=='__main__':
 assert not (c.RUN/'FROZEN').exists()
 targets=[
 ('alt-gatehouse-refresher','gatehouse-uk','GB','en-GB','https://gatehousebank.com/insights/your-home-purchase-plan-a-quick-refresher','alternative'),
 ('alt-gatehouse-guide','gatehouse-uk','GB','en-GB','https://assets.gatehousebank.com/production/downloads/2026-04-01-Home-Purchase-Plan-Criteria-Guide-finance-up-to-80-V1.pdf?dm=1775030272','alternative'),
 ('alt-blme-wakala','blme-uk','GB','en-GB','https://www.blme.com/products-and-services/wealth-management/wakala/','alternative'),
 ('alt-uphold-help','uphold-uk','GB','en','https://support.uphold.com/hc/en-us/articles/11967029021339-Staking','alternative'),
 ('alt-cimb-durian','cimb-islamic-my','MY','en','https://www.cimb.com.my/en/personal/day-to-day-banking/accounts/mudarabah-ia/daily-unrestricted-investment-account-i.html','alternative'),
 ('alt-cimb-smia','cimb-islamic-my','MY','ms','https://www.cimb.com.my/bm/personal/day-to-day-banking/accounts/mudarabah-ia/special-mudharabah-investment-account-i.html','alternative'),
 ('alt-dib-ijara','dib-ae','AE','en','https://www.dib.ae/business/products-services/ijara','alternative'),
 ('alt-dib-vehicle-terms','dib-ae','AE','en','https://www.dib.ae/docs/default-source/default-document-library/vehicle-finance-ijara_termsandconditions.pdf','alternative'),
 ('alt-dib-property','dib-ae','AE','en','https://dib.ae/business/corporate/real-estate','alternative'),
 ('alt-bisb-terms','bisb-bh','BH','en','https://www.bisb.com/en/general-banking-terms-and-conditions','alternative'),
 ('alt-bisb-finance','bisb-bh','BH','en','https://www.bisb.com/index.php/en/financing-solutions','alternative')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:ss=list(pool.map(c.fetch,targets))
 c.write(c.RUN/'sources.json',ss);c.write(c.RUN/'baseline.json',c.read(c.R/'dist/data/bank-ui.json'))
 (c.RUN/'FROZEN').write_text('Own sources. MY/AE/BH are secondary candidates until explicit market adjudication, not silently primary country examples.\n')
 print([(s['id'],s['state'],len(s.get('text',''))) for s in ss])
