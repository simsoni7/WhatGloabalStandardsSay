# One-time v29 recorder/preparer. Already executed; frozen files must not be overwritten.
import datetime,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-screen-browser-v29-20261012';assert not (RUN/'FROZEN').exists();RUN.mkdir(exist_ok=True)
targets=[('hk-manulife-claims-guide','manulife-hk','HK','en','https://www.manulife.com.hk/en/individual/services/manage-your-account/claims-submission-and-enquiries.html'),('hk-manulife-eclaims','manulife-hk','HK','en','https://www.manulife.com.hk/en/individual/services/file-a-claim/eclaims.html'),('kr-samsungfire-claims','samsung-fire','KR','ko','https://pr.samsungfire.com/v2/html/claim/05/C_050_040_008.html')];rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,args=['--no-sandbox']);ctx=b.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page()
 for sid,pid,country,lang,url in targets:
  try:
   response=page.goto(url,wait_until='domcontentloaded',timeout=40000);page.wait_for_timeout(1800);raw=page.content().encode();resolved=page.url;sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'rendered.html').write_bytes(raw);s=BeautifulSoup(raw,'html.parser');body=s.find('main') or s.find('body') or s
   for x in body.select('script,style,nav,header,footer'):x.decompose()
   text=' '.join(body.get_text(' ',strip=True).split());(folder/'normalized.txt').write_text(text);images=[{'url':im.get('src') or im.get('data-src'),'alt':im.get('alt',''),'ordinal':i} for i,im in enumerate(body.select('img[src],img[data-src]'))]
   from urllib.parse import urljoin
   for im in images:im['url']=urljoin(resolved,im['url'])
   rows.append({'id':sid,'provider_id':pid,'country':country,'language':lang,'url':url,'resolved_url':resolved,'http_status':response.status if response else None,'state':'rendered_pending_review','source_format':'official_browser_html','raw_filename':'rendered.html','raw_sha256':sha,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text,'snapshot_path':str(folder.relative_to(R)),'images':images,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browser_version':b.version,'automatic_adoption':False});print(sid,response.status if response else None,len(text),len(images),flush=True)
  except Exception as e:rows.append({'id':sid,'provider_id':pid,'country':country,'url':url,'state':'browser_failed','error_type':type(e).__name__,'automatic_adoption':False});print(sid,type(e).__name__,flush=True)
 ctx.close();b.close()
(RUN/'sources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(RUN/'FROZEN').write_text('Normal public browser read, no credentials or transactions; document screen not financialUI capture.\n')
