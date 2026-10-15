"""Normal unauthenticated own-page render for publisher documentviewer."""
import asyncio,hashlib,json,datetime
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-browser-v33-20261013'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
async def main():
 assert not (RUN/'FROZEN').exists();ss=[]
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True)
  for i,url in enumerate(['https://www.chesnaralife.co.uk/documents/a-customer-guide-to-our-flexible-trust/','https://www.chesnaralife.co.uk/documents/protection-flexible-trust-uk']):
   page=await browser.new_page();sid='ip33-chesnara-browser-'+str(i);responses=[]
   page.on('response',lambda r:responses.append(r))
   try:
    response=await page.goto(url,wait_until='networkidle',timeout=60000);await page.wait_for_timeout(1500);raw=(await page.content()).encode();t=' '.join((await page.locator('body').inner_text()).split());sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.html').write_bytes(raw);(folder/'normalized.txt').write_text(t);links=await page.locator('a[href]').evaluate_all('(xs)=>xs.map(a=>({label:a.innerText,url:a.href}))');rec=dict(id=sid,provider_id='chesnara-life-uk',country='GB',language='en-GB',url=url,resolved_url=page.url,http_status=response.status,state='fetched_pending_review',source_format='official_public_rendered_html',raw_filename='source.html',raw_sha256=sha,text_sha256=hashlib.sha256(t.encode()).hexdigest(),text=t,snapshot_path=str(folder.relative_to(R)),pdf_pages=[],pdf_metadata=None,links=links,images=[],research_family='wealth',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),automatic_adoption=False,render_network_urls=[r.url for r in responses]);ss.append(rec)
   except Exception as e:ss.append(dict(id=sid,provider_id='chesnara-life-uk',country='GB',language='en-GB',url=url,state='fetch_failed',error_type=type(e).__name__,automatic_adoption=False))
   await page.close()
  await browser.close()
 write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('Normalbrowser no login/cookies reuse/bypass. Renderedownsource only, notcapturebenchmark.\n');print({'records':len(ss),'inventory':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]})
asyncio.run(main())
