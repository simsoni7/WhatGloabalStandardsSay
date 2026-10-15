import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];checks=[];errors=[]
def check(label,ok):assert ok,label;checks.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(s.server_port)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/#explore');page.locator('#task-query').wait_for();check('core initiation in home popular goals',page.get_by_role('heading',name='송금하기',exact=True).count()==1)
  page.locator('#task-query').fill('송금');check('user regression shows initiate domestic and overseas',all(page.get_by_role('heading',name=x,exact=True).count()==1 for x in ['송금하기','국내송금','해외송금']))
  out=R/'research/source-store/backbone-20261004';page.screenshot(path=str(out/'after-remittance-search.png'),full_page=False)
  page.get_by_role('heading',name='해외송금',exact=True).click();page.locator('#transfer-geography').wait_for();check('overseas route preselects contextual geography',page.locator('#transfer-geography').input_value()=='cross_border')
  check('FX need remains unknown for overseas',page.locator('#transfer-fx').input_value()=='' and page.locator('#optional-fx a').count()==0)
  check('initiation does not invent Wise Citi or Toss benchmarks',page.get_by_text('이 결과에 직접 대응하는 기업 자료는 아직 연결하지 않았습니다.',exact=True).count()==1)
  page.locator('#transfer-fx').select_option('no');check('same-currency overseas use stays possible','환전 없이 송금' in page.locator('#transfer-context-summary').inner_text())
  page.locator('#transfer-fx').select_option('yes');check('FX information and actual exchange exposed separately',page.locator('#optional-fx a').count()==2)
  check('settlement funding cannot masquerade as final settlement',page.get_by_text('결제자금 확보를 최종 은행간 결제로 표시하지 않습니다.',exact=True).count()==1)
  page.set_viewport_size({'width':390,'height':844});check('goal mobile layout no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'mobile-overseas.png'),full_page=False)
  page.set_viewport_size({'width':1440,'height':1000});page.goto(base+'/#explore');page.locator('#task-query').fill('카드 신청');check('card application available without provider observations',page.get_by_role('heading',name='카드 발급 신청',exact=True).count()==1)
  page.locator('#task-query').fill('환율');page.get_by_role('heading',name='환율·환전 예상금액 조회',exact=True).click();page.get_by_role('heading',name='이 화면이 만드는 결과',exact=True).wait_for();check('FX information uses its new canonical result',page.get_by_role('heading',name='환율·환전 예상금액 조회',exact=True).count()==2 and '실제 교환' in page.locator('#content').inner_text())
  check('preserved official calculator evidence reachable',page.get_by_role('link',name='기업 문구·정책·화면 보기',exact=True).count()==1)
  page.goto(base+'/#family/payments');page.locator('#task-query').wait_for();check('all financial definitions reachable through family browse',page.locator('#operation-results').count()==0 and page.locator('#task-results').inner_text().find('수취인')>=0)
  page.locator('#task-query').fill('<img src=x onerror=window.injected=1>');check('query inert and escaped',page.evaluate('!window.injected') and page.locator('#content img[src="x"]').count()==0)
  page.locator('#task-query').fill('');page.locator('#filter-category').select_option('');page.locator('#filter-product').select_option('TOSS');check('empty provider target does not fabricate observations',page.locator('#task-results .taskcard').count()==0 and page.get_by_text('조건에 맞는 기업 자료가 없습니다',exact=True).is_visible())
  check('no browser errors',not errors);b.close()
 print(json.dumps({'status':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
