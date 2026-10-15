"""Own public savings sources; exact links followed, immutable v31 snapshots."""
import json,concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as c
R=c.R;c.RUN=R/'research/source-store/savings-collection-v31-20261012'
if __name__=='__main__':
 assert not (c.RUN/'FROZEN').exists()
 targets=[
 ('hk-deposit-offers','hsbc-hk','HK','en','https://www.hsbc.com.hk/accounts/offers/deposits/','savings'),
 ('hk-deposit-forms','hsbc-hk','HK','en','https://www.hsbc.com.hk/accounts/forms/','savings'),
 ('kr-term-deposit','kakaobank','KR','ko','https://www.kakaobank.com/products/deposit','savings'),
 ('kr-installment','kakaobank','KR','ko','https://www.kakaobank.com/products/savings','savings'),
 ('gb-regular-saver','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/savings/products/regular-saver/','savings'),
 ('gb-fixed-saver','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/savings/products/fixed-rate/','savings'),
 ('gb-hl-limit-orders','hl-uk','GB','en-GB','https://www.hl.co.uk/shares/share-dealing/limits','wealth')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:sources=list(p.map(c.fetch,targets))
 c.write(c.RUN/'sources.json',sources)
 print(json.dumps({'base_sources':len(sources),'states':[(s['id'],s['state'],len(s.get('text',''))) for s in sources],'follow_candidates':[(s['id'],x) for s in sources for x in s.get('links',[]) if any(k in x['label'].lower() for k in ['step-by-step','maturity instructions form','상품설명서','특약','regular saver terms','fixed rate saver terms'])]},ensure_ascii=False))
