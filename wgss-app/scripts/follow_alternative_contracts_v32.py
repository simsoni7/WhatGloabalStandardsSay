"""Follow own hyperlinked UK contracts under a new immutable source batch."""
import concurrent.futures
import collect_bank_gaps_v30 as c
R=c.R;c.RUN=R/'research/source-store/alternative-contracts-v32-20261013';assert not (c.RUN/'FROZEN').exists();old=c.read(R/'research/source-store/alternative-collection-v32-20261013/sources.json');targets=[]
for sid,label,nid in [('alt-uphold-staking','on our website','alt-uphold-uk-agreement'),('alt-alrayan-aap','Settling your finance','alt-alrayan-settle'),('alt-alrayan-aap','Important documents','alt-alrayan-documents')]:
 s=next(s for s in old if s['id']==sid);link=next(l for l in s['links'] if label in l['label']);targets.append((nid,s['provider_id'],s['country'],s['language'],link['url'],'alternative'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(c.fetch,targets))
c.write(c.RUN/'sources.json',ss);c.write(c.RUN/'baseline.json',c.read(R/'dist/data/bank-ui.json'));(c.RUN/'FROZEN').write_text('Own actual links followed, no inferred market.\n');print([(s['id'],s['state'],len(s.get('text',''))) for s in ss])
