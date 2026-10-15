"""Financial labels route to correct results; reference versions and issuer roles visible."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];checks=[];errors=[]
def check(n,ok):assert ok,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(s.server_port);out=R/'research/ui-v34';out.mkdir(exist_ok=True)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/#bank-works');page.locator('#bank-work-query').wait_for()
  for query,expected,forbidden in [('Daily payment limits','05004E3900EF','DFEB572279B8'),('Forgotten your password?','0A65B1936347','4C73650B5797'),('Move or withdraw cash','E7352823594F','80F4B517097C')]:
   page.locator('#bank-work-query').fill(query);check('source-native financial phrase routed without false equivalent: '+query,page.locator('a[href="#bank-work/WGSS-UI-'+expected+'"]').count()==1 and page.locator('a[href="#bank-work/WGSS-UI-'+forbidden+'"]').count()==0)
  page.goto(base+'/#bank-collection');page.locator('#bank-collection-count').wait_for();check('explicit five-country study includes Malaysian provider without changing financial units','대상 금융 플랫폼 36곳' in page.locator('#content').inner_text() and 'CIMB Islamic' in page.locator('#content').inner_text() and page.locator('#bank-collection-country option').count()==6)
  for provider,country,text in [('shinhan-card','KR','신한카드'),('fidelity-uk','GB','Fidelity UK'),('hsbc-life-hk','HK','HSBC Life Hong Kong')]:
   page.locator('#bank-collection-provider').select_option(provider);page.locator('#bank-collection-state').select_option('screen');check('provider filter uses correct market and admits screens: '+provider,page.locator('#bank-collection-country').input_value()==country and text in page.locator('#bank-collection-results').inner_text())
  check('blocked and historical providers visible without invented UI','403 접근 실패' in page.locator('#content').inner_text() and '2013년 구버전' in page.locator('#content').inner_text())
  for wid,country,provider,version in [('E7352823594F','GB','Fidelity UK','2024-10'),('FC18DDD43155','HK','HSBC Life Hong Kong','2025-01')]:
   page.goto(base+'/#bank-work/WGSS-UI-'+wid);page.locator('#bank-country').select_option(country);card=page.locator('.bank-benchmark').filter(has_text=provider).filter(has_text=version);check('correct dated reference displayed: '+wid,card.count()==1 and '현재 화면과 다를 수 있습니다' in card.inner_text())
   img=card.locator('.bank-guide-image').first;img.scroll_into_view_if_needed();page.wait_for_function("(src)=>[...document.querySelectorAll('img')].find(i=>i.getAttribute('src')===src)?.naturalWidth>0",arg=img.get_attribute("src"))
   check('original PDF financial panel loads: '+wid,img.evaluate('(i)=>i.complete&&i.naturalWidth>0') and card.get_by_role('link',name='공식 안내 화면 원본 크게 보기').get_attribute('href').startswith('evidence/bank-v29/'))
   if card.locator('.bank-guide-gallery summary').count():card.locator('.bank-guide-gallery summary').click();card.locator('.bank-guide-image').last.scroll_into_view_if_needed();page.wait_for_function("[...document.querySelectorAll('img[src*=\"bank-v29\"]')].every(i=>i.complete&&i.naturalWidth>0)")
   if country=='HK':check('insurer and bank publisher roles, actual app name visible','보험자' in card.inner_text() and '공식 PDF 호스팅' in card.inner_text() and 'HealthyLife App' in card.inner_text())
   page.set_viewport_size({'width':1440,'height':1000});card.scroll_into_view_if_needed();page.screenshot(path=str(out/(wid+'-reference-desktop.png')))
   page.set_viewport_size({'width':390,'height':844});img.scroll_into_view_if_needed();check('new PDF reference contained on mobile: '+wid,page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/(wid+'-reference-mobile.png')));page.set_viewport_size({'width':1440,'height':1000})
  page.goto(base+'/#bank-work/WGSS-UI-591B10169113');page.locator('#bank-country').select_option('KR');card=page.locator('.bank-benchmark').filter(has_text='신한카드');check('partial guide focuses transaction history and retains original',card.locator('.bank-guide-focus').count()==1 and '최근 입출금' in card.locator('h3').inner_text());card.locator('img').scroll_into_view_if_needed();page.screenshot(path=str(out/'shinhan-history-reference.png'))
  page.goto(base+'/#bank-scope');page.get_by_role('heading',name='범위 v1.1 정정',exact=True).wait_for()
  with page.expect_download() as dl:page.get_by_role('link',name='정정 전후와 근거 받기').click()
  rev=json.loads(dl.value.path().read_text());check('revision download provides3 actual before/after records and2 source URLs',rev['current_works']==216 and len(rev['metadata_corrections'])==3 and all('before' in x and 'after' in x for x in rev['metadata_corrections']) and len(rev['new_works'])==2 and all(x['own_source']['url'].startswith('https://') for x in rev['new_works']))
  check('no browser errors',not errors);browser.close()
 print(json.dumps({'bank_expansion_browser_v29':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
