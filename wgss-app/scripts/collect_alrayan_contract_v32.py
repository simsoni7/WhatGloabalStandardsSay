"""Actual linked HPP contract index, separate frozen source inventory."""
import collect_bank_gaps_v30 as c
R=c.R;c.RUN=R/'research/source-store/alrayan-contract-v32-20261013';assert not (c.RUN/'FROZEN').exists();index=next(s for s in c.read(R/'research/source-store/alternative-contracts-v32-20261013/sources.json') if s['id']=='alt-alrayan-documents');link=next(l for l in index['links'] if l['label']=='HPP Terms & Conditions');s=c.fetch(('alt-alrayan-hpp-terms','al-rayan-uk','GB','en-GB',link['url'],'alternative'));sources=[s]
if s['state']=='fetched_pending_review':
 links=[l for l in s['links'] if '.pdf' in l['url']];c.write(c.RUN/'pdf-links.json',links)
 for i,l in enumerate(links[:3]):sources.append(c.fetch(('alt-alrayan-terms-pdf-'+str(i),'al-rayan-uk','GB','en-GB',l['url'],'alternative')))
c.write(c.RUN/'sources.json',sources);(c.RUN/'FROZEN').write_text('Linked HPP documents preserved. Existing-customer terms not new product availability.\n');print([(s['id'],s['state'],len(s.get('text','')),len(s.get('pdf_pages',[]))) for s in sources])
