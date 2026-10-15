"""Follow three operative guide/form links found on official index pages."""
import concurrent.futures
import collect_bank_gaps_v30 as c
R=c.R;c.RUN=R/'research/source-store/savings-collection-v31-20261012'
assert not (c.RUN/'FROZEN').exists();sources=c.read(c.RUN/'sources.json');extra=[]
for sid,label,nid in [('hk-deposit-offers','HSBC HK App step-by-step guide','hk-placement-app'),('hk-deposit-offers','Online Banking step-by-step guide','hk-placement-web'),('hk-deposit-forms','Time Deposit / Deposit Plus Maturity Instructions Form','hk-maturity-form')]:
 s=next(s for s in sources if s['id']==sid);link=next(x for x in s['links'] if label in x['label']);extra.append((nid,s['provider_id'],s['country'],s['language'],link['url'],'savings'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:sources+=list(p.map(c.fetch,extra))
c.write(c.RUN/'sources.json',sources);c.write(c.RUN/'baseline.json',c.read(R/'dist/data/bank-ui.json'));(c.RUN/'FROZEN').write_text('10 exact own-source snapshots frozen. No automatic approval.\n')
print([(s['id'],s['state'],len(s.get('text','')),len(s.get('pdf_pages',[]))) for s in sources])
