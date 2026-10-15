"""Normal public browser fetch for rejected HTTP originals, not access bypass."""
import datetime,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import collect_bank_gaps_v30 as c
R=c.R;RUN=R/'research/source-store/alternative-collection-v32-20261013';assert not (RUN/'FROZEN').exists();ss=c.read(RUN/'sources.json')
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000})
 for old in ss[:2]:
  sid=old['id']+'-browser'
  try:
   res=page.goto(old['url'],wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(1000);assert res and res.status==200,'HTTP status '+str(res.status if res else None);raw=page.content().encode();soup=BeautifulSoup(raw,'html.parser');body=soup.find('main') or soup.find('body') or soup
   for n in body.select('script,style,nav,header,footer'):n.decompose()
   text=' '.join(body.get_text(' ',strip=True).split());assert len(text)>3000,'public terms not loaded';sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.html').write_bytes(raw);(folder/'normalized.txt').write_text(text)
   ss.append(dict(id=sid,provider_id=old['provider_id'],country=old['country'],language=old['language'],url=old['url'],resolved_url=page.url,http_status=res.status,state='fetched_pending_review',source_format='official_rendered_html',raw_filename='source.html',raw_sha256=sha,text_sha256=hashlib.sha256(text.encode()).hexdigest(),text=text,snapshot_path=str(folder.relative_to(R)),pdf_pages=[],pdf_metadata=None,links=[],images=[],research_family='alternative',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),automatic_adoption=False,financial_ui_capture=False))
  except Exception as e:ss.append(dict(id=sid,provider_id=old['provider_id'],country=old['country'],language=old['language'],url=old['url'],state='fetch_failed',error_type=type(e).__name__,reason=str(e)[:100],automatic_adoption=False))
 b.close()
c.RUN=RUN;ss.append(c.fetch(('alt-uphold-instructions','uphold-uk','GB','en-GB','https://support.uphold.com/hc/en-us/articles/11967029021339-Staking','alternative')))
c.write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('Public original snapshots frozen; browser access not assumed if HTTP rejects.\n');print([(s['id'],s['state'],len(s.get('text',''))) for s in ss])
