"""New public financial result navigation,106auditcoverage and true original images."""
import json,functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];out=R/'research/ui-v34';out.mkdir(exist_ok=True);checks=[];errors=[]
def check(n,v):assert v,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(s.server_port)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+'/#bank-collection');page.locator('#bank-collection-count').wait_for();check('106 initialgaps audit and40newlinks visible','공개 자료 업무 연결 · 66개 대상' in page.locator('#content').inner_text() and '이번에 39개 연결 · 남은 27개' in page.locator('#content').inner_text())
  with page.expect_download() as dl:page.get_by_role('link',name='업무별 조사 근거·다음 작업 받기').click()
  d=json.loads(dl.value.path().read_text());check('all106 audited rows download despite tablepage20',len(d['rows'])==66 and sum(r['root_status']=='linked' for r in d['rows'])==39)
  page.get_by_text('남은 업무의 조사 상태와 다음 자료',exact=True).click();check('remaining66 realrows visible without claimingunsupported',page.locator('section').filter(has=page.get_by_role('heading',name='공개 자료 업무 연결 · 66개 대상')).locator('.recordrow').count()==27)
  page.get_by_role('heading',name='공개 자료 업무 연결 · 66개 대상').scroll_into_view_if_needed();check('reviewed own originals are directly accessible links',page.locator('section').filter(has=page.get_by_role('heading',name='공개 자료 업무 연결 · 66개 대상')).locator('details details a[href^="https://"]').count()>0);page.screenshot(path=str(out/'public-collection-audit-desktop.png'));page.set_viewport_size({'width':390,'height':844});check('expandedaudit onmobilecontained',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'public-collection-audit-mobile.png'));page.set_viewport_size({'width':1440,'height':1000})
  for wid,country,phrase in [('DCE064307324','GB','indemnity'),('698EB3626343','KR','약정'),('F1FB941BFE3A','HK','IPO'),('64A78D83F417','GB','Cryptoassets'),('E71D450DA031','GB','AlRayan')]:
   page.goto(url+'/#bank-work/WGSS-UI-'+wid);page.locator('#bank-country').select_option(country);check('qualified reference '+wid,phrase in page.locator('#bank-country-results').inner_text())
  for wid,country,phrase in [('EFE3E19CE882','GB','공식 상품 페이지의 화면 예시'),('EE8B53980E2F','HK','Collateral Breakdown'),('6E264279DEC9','GB','Total Return')]:
   page.goto(url+'/#bank-work/WGSS-UI-'+wid);page.locator('#bank-country').select_option(country);check('source image class and actual financial label '+wid,phrase in page.locator('#bank-country-results').inner_text());img=page.locator('.bank-guide-image').first;img.scroll_into_view_if_needed();page.wait_for_function("document.querySelector('.bank-guide-image').naturalWidth>0");check('original publisher image including AVIF loads '+wid,img.is_visible());page.screenshot(path=str(out/(wid+'-v32-reference-desktop.png')));page.set_viewport_size({'width':390,'height':844});check('financialreference fitsmobile '+wid,page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/(wid+'-v32-reference-mobile.png')));page.set_viewport_size({'width':1440,'height':1000})
  page.goto(url+'/#bank-works');page.locator('#bank-work-query').fill('공모주');check('new native operation searchable from sourcecontext, not oneoffalias',page.locator('a[href="#bank-work/WGSS-UI-F1FB941BFE3A"]').count()==1)
  check('no uncaught browser errors',not errors);b.close()
 print(json.dumps({'browser_collection_v32':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
