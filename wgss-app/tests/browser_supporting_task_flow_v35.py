"""Supplemental process and permission sources stay usable and truthful."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];out=R/'research/ui-v36';out.mkdir(exist_ok=True);checks=[];errors=[]
def check(n,v):assert v,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(s.server_port)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+'/#bank-work/WGSS-UI-020499E81104');page.locator('#bank-country').select_option('MY');page.locator('#bank-reference-language').select_option('en');card=page.locator('.bank-benchmark').filter(has=page.get_by_role('heading',name='Daily Unrestricted Investment Account-i (DURIAN-i)',exact=True));flow=card.locator('.bank-supporting-process')
  check('process hidden until asked, attached only to exact DURIAN reference',flow.count()==1 and not flow.evaluate('(e)=>e.open') and page.locator('.bank-supporting-process').count()==1);flow.locator('summary').click()
  check('four documented steps and source edition visible',flow.locator('ol > li').count()==4 and 'Step 1: Contact Details' in flow.inner_text() and 'Step 4: Fund Your Account' in flow.inner_text() and 'SEP2026' in flow.inner_text())
  check('input data not observed controls','실제 버튼·필드 라벨은 확인하지 않았습니다' in flow.inner_text() and 'SMS OTP' in flow.inner_text() and '앞뒤 사진·안면인식' in flow.inner_text())
  check('opened versus inoperable and adverse verification visible','이용 불가(inoperable)' in flow.inner_text() and '및/또는 카드 활성화' in flow.inner_text() and '최대 7영업일' in flow.inner_text() and '자동 폐쇄' in flow.inner_text())
  check('supplement has its own eKYC source not original PDS URL',flow.get_by_role('link',name='이 절차·조건의 공식 원문').get_attribute('href').endswith('/web-ekyc-terms-and-conditions.pdf'));page.screenshot(path=str(out/'durian-process-desktop.png'));page.set_viewport_size({'width':390,'height':844});flow.scroll_into_view_if_needed();check('full process fits mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'durian-process-mobile.png'))
  page.goto(url+'/#bank-work/WGSS-UI-798ED0DAB916');page.locator('#bank-country').select_option('GB');card=page.locator('.bank-benchmark').filter(has=page.get_by_role('heading',name='Issue refunds',exact=True));roles=card.locator('.bank-supporting-process');roles.locator('summary').click()
  check('four documented roles shown; ViewOnly denied not silent absence',roles.locator('li').count()==4 and 'View Only' in roles.inner_text() and '환불이 불가능' in roles.inner_text() and 'Analyst' in roles.inner_text())
  check('global documentation does not claim actual account access','실제 계정에 부여된 권한·현재 영국 UI를 확인한 자료는 아닙니다' in roles.inner_text() and roles.get_by_role('link',name='이 절차·조건의 공식 원문').get_attribute('href').endswith('/teams/roles'));check('role text fits mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'refund-role-permissions-mobile.png'))
  check('no uncaught errors',not errors);browser.close()
 print(json.dumps({'browser_supporting_task_flow_v35':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
