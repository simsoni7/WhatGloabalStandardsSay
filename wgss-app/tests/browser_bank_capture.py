"""Capture planning, original public entry states and evidence-type presentation."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];errors=[];checks=[]
def check(n,ok):assert ok,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda x:errors.append(str(x)))
  page.goto(base+'/#bank-collection');page.get_by_role('link',name='화면 수집 계획',exact=True).click();page.wait_for_function("document.querySelector('h1')?.textContent==='앱·웹 화면 수집 계획'")
  check('capture programme available from collection page','로그인 후 앱 직접 확인' in page.locator('#content').inner_text())
  check('all1080 capture tasks are paginated, not arbitrary screenshots',page.locator('#bank-capture-queue tbody tr').count()==20 and '총 1080개 조합' in page.locator('#bank-capture-count').inner_text())
  page.locator('#bank-capture-country').select_option('KR');check('country filter preserves all216 works',page.locator('#bank-capture-queue tbody tr').count()==20 and '총 216개 조합' in page.locator('#bank-capture-count').inner_text())
  check('article captures excluded from financial UI','금융 거래 UI 캡처 수와 화면 커버리지에 포함하지 않음' in page.locator('#content').inner_text())
  with page.expect_download() as dl:page.get_by_role('link',name='전체 화면 수집 계획 JSON 받기').click()
  plan=json.loads(dl.value.path().read_text());check('download includes all1080 tasks despite filter',len(plan['cells'])==1080 and plan['counts']['public_web_captures']==2 and plan['environment']['connected_android_devices']==0 and not plan['automatic_collection_scheduled'])
  page.set_viewport_size({'width':390,'height':844});check('capture plan fits mobile with contained table',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.set_viewport_size({'width':1440,'height':1000})
  page.get_by_role('link',name='영국 로그인 업무에서 캡처 보기').click();page.locator('#bank-country').select_option('GB');card=page.locator('.bank-benchmark').filter(has_text='직접 캡처한 공개 웹')
  check('actual web capture has its own label, not app guide',card.count()==1 and '금융사 설명용 화면' not in card.inner_text())
  check('entry does not imply successful authentication','인증 성공을 관찰한 사례가 아님' in card.inner_text() and '로그인 전 상태' in card.inner_text())
  check('both entry states with empty identifiers present',card.locator('.bank-guide-image').count()==2)
  card.locator('.bank-guide-gallery summary').click();card.locator('.bank-guide-image').last.scroll_into_view_if_needed();page.wait_for_function("[...document.querySelectorAll('.bank-guide-image')].every(i=>i.complete&&i.naturalWidth>0)")
  check('original two capture files load',card.locator('.bank-guide-image').last.is_visible() and card.get_by_role('link',name='추가 공식 안내 화면 원본 크게 보기').get_attribute('href').startswith('evidence/bank-v27/'))
  page.set_viewport_size({'width':390,'height':844});check('expanded web gallery fits mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  out=R/'research/ui-v34';out.mkdir(exist_ok=True);page.set_viewport_size({'width':1440,'height':1000});card.scroll_into_view_if_needed();page.screenshot(path=str(out/'public-web-reference.png'));page.goto(base+'/#bank-capture-plan');page.get_by_role('heading',name='앱·웹 화면 수집 계획',exact=True).wait_for();page.screenshot(path=str(out/'capture-plan-desktop.png'));page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(out/'capture-plan-mobile.png'))
  check('no browser errors',not errors);b.close()
 print(json.dumps({'bank_capture_browser':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:server.shutdown();server.server_close()
