"""Public alternative-finance originals, before exact result extraction."""
import concurrent.futures,json
import collect_bank_gaps_v30 as c
R=c.R;c.RUN=R/'research/source-store/alternative-collection-v32-20261013'
if __name__=='__main__':
 assert not (c.RUN/'FROZEN').exists()
 targets=[('alt-revolut-crypto','revolut-crypto-uk','GB','en-GB','https://www.revolut.com/legal/cryptocurrency-terms/','alternative'),('alt-revolut-x','revolut-crypto-uk','GB','en-GB','https://www.revolut.com/legal/crypto-exchange-terms/','alternative'),('alt-alrayan-aap','al-rayan-uk','GB','en-GB','https://www.alrayanbank.co.uk/additional-acquisition-payments','alternative'),('alt-alrayan-hpp','al-rayan-uk','GB','en-GB','https://www.alrayanbank.co.uk/we-have-posted-your-home-purchase-plan-offer-letter','alternative'),('alt-uphold-staking','uphold-uk','GB','en-GB','https://uphold.com/en-gb/legal/uphold-staking-program-terms','alternative')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(c.fetch,targets))
 c.write(c.RUN/'sources.json',ss);c.write(c.RUN/'baseline.json',c.read(R/'dist/data/bank-ui.json'));print(json.dumps({'sources':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]},ensure_ascii=False))
