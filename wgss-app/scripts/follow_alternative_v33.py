"""Follow concrete own links; no inferred filenames or model-invented evidence."""
import concurrent.futures
import collect_bank_gaps_v30 as c
c.RUN=c.R/'research/source-store/alternative-followup-v33-20261013'
if __name__=='__main__':
 assert not (c.RUN/'FROZEN').exists();ss=c.read(c.R/'research/source-store/alternative-collection-v33-20261013/sources.json');targets=[];seen=set()
 for s in ss:
  for link in s.get('links',[]):
   u=link['url'];label=link['label'].lower()
   keep=(s['id']=='alt-cimb-durian' and 'Product Disclosure Sheet' in link['label']) or (s['id']=='alt-cimb-smia' and 'pds/' in u) or (s['id']=='alt-dib-ijara' and 'sharia-certificates/' in u) or (s['id']=='alt-dib-property' and any(x in u for x in ['/istisna','/murabaha-on-lands','/murabaha-on-buildings']))
   if keep and u not in seen:
    seen.add(u);targets.append(('alt-follow-'+str(len(targets)+1),s['provider_id'],s['country'], 'ms' if '-bm.pdf' in u else s['language'],u,'alternative'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:out=list(pool.map(c.fetch,targets))
 c.write(c.RUN/'sources.json',out);(c.RUN/'FROZEN').write_text('Source-owned document links and immutable originals. No admission implied.\n');print([(s['id'],s['state'],len(s.get('text',''))) for s in out])
