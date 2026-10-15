"""Live practitioner examples, local collector handoff and chat fallback."""
import json,functools,http.server,threading,zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];out=R/'research/ui-v34';out.mkdir(exist_ok=True);checks=[];errors=[]
def check(n,ok):assert ok,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(s.server_port)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+'/#bank-capture-plan');section=page.locator('#bank-authenticated-collection');section.wait_for();check('zero actual login connections shown separately','실제 로그인 서비스 연결 0개' in section.inner_text())
  section.get_by_text('연결 방법과 준비 상태',exact=True).click();check('chat image fallback real option without claimed automatic ingestion','대화창 이미지 첨부' in section.inner_text() and '이미지 미제공' in section.inner_text() and '현재 첨부된 실제 금융 이미지는 없습니다' in section.inner_text())
  section.get_by_text('접근이 막혔거나 추가 확인이 필요한 서비스 5곳',exact=True).click();check('403, old source and partner boundary distinct','403' in section.inner_text() and '2013' in section.inner_text() and 'Broadridge' in section.inner_text())
  with page.expect_download() as dl:section.get_by_role('link',name='로컬 수집 도구·연결 안내 받기').click()
  with zipfile.ZipFile(dl.value.path()) as z:check('collector bundle downloads actual tool and complete216 ID catalogue','local_session_capture.py' in z.namelist() and len(json.loads(z.read('bank-ui.json'))['works'])==216)
  section.scroll_into_view_if_needed();page.screenshot(path=str(out/'authenticated-plan-desktop.png'));page.set_viewport_size({'width':390,'height':844});check('connection plan contained on mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'authenticated-plan-mobile.png'));page.set_viewport_size({'width':1440,'height':1000})
  for wid,country,word in [('B85A9A562018','KR','긴급출금'),('06FC495733F0','HK','만기'),('58A48889FF96','HK','基金轉換／重組投資組合')]:
   page.goto(url+'/#bank-work/WGSS-UI-'+wid);page.locator('#bank-country').select_option(country);check('native financial example available '+wid,word in page.locator('#bank-country-results').inner_text())
   if country=='KR':check('termdeposit100만원 and installment10만원 both productscoped','100만원' in page.locator('#bank-country-results').inner_text() and '10만원' in page.locator('#bank-country-results').inner_text() and '자유적금' in page.locator('#bank-country-results').inner_text())
   if wid=='58A48889FF96':
    check('four genuine Chinese references distinct existing/future and documentedversion',page.locator('.bank-benchmark:has(h3[lang="zh-Hant-HK"])').count()==4 and '향후 부담금' in page.locator('#bank-country-results').inner_text())
    page.locator('#bank-reference-language').select_option('zh-Hant-HK');check('HongKong practitioner can isolate4 local native references',page.locator('.bank-benchmark').count()==4 and page.locator('.bank-benchmark h3').first.get_attribute('lang')=='zh-Hant-HK')
    page.locator('#bank-reference-language').select_option('en');check('English comparison remains separate3 examples',page.locator('.bank-benchmark').count()==3);page.locator('#bank-reference-language').select_option('zh-Hant-HK')
   imgs=page.locator('.bank-guide-image');
   if imgs.count():
    imgs.first.scroll_into_view_if_needed();page.wait_for_function("document.querySelector('.bank-guide-image').naturalWidth>0");check('official original guide loaded '+wid,imgs.first.is_visible());page.screenshot(path=str(out/(wid+'-v31-reference-desktop.png')))
   page.set_viewport_size({'width':390,'height':844});check('new local references fit mobile '+wid,page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/(wid+'-v31-reference-mobile.png')));page.set_viewport_size({'width':1440,'height':1000})
  check('no uncaught browser errors',not errors);b.close()
 print(json.dumps({'browser_collection_v31':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
