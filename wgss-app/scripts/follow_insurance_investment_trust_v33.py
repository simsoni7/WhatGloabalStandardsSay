"""PDF URLs discovered in normal publisher browser documentredirects."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-trust-pdfs-v33-20261013';base.RUN=RUN
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists();T=[];origins={}
 for s in json.loads((R/'research/source-store/insurance-investment-browser-v33-20261013/sources.json').read_text()):
  for u in s.get('render_network_urls',[]):
   if '.pdf' in u:
    sid='ip33-trust-pdf-'+str(len(T));T.append((sid,'chesnara-life-uk','GB','en-GB',u,'wealth'));origins[sid]=dict(discovery_source_id=s['id'],discovery_publisher_url=s['url'],discovery_mechanism='normal_public_publisher_document_redirect_network_response')
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:ss=list(p.map(base.fetch,T))
 for s in ss:s.update(origins[s['id']])
 base.write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('CurrentChesnara2026PDFs from actual ownpub redirects. Not thirdpartysearch discoveries.\n');print({'sources':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]})
