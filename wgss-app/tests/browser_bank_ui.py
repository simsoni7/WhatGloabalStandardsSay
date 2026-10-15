"""Practitioner journey and management counts for the confirmed customer scope."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];d=json.loads((R/'dist/data/bank-ui.json').read_text());checks=[];errors=[]
def check(name,ok):assert ok,name;checks.append(name)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
def settled(page):page.wait_for_function("document.querySelector('h1')&&!document.querySelector('.loading')")
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'/#explore');settled(page);check('practitioner entry shows search before DB counts',page.locator('#task-query').is_visible() and page.locator('.bank-scope-summary').count()==0)
        for q in ['송금','마이너스통장','카드론']:
            page.locator('#task-query').fill(q);check('source-backed customer navigation: '+q,page.locator('.bank-search-results .bank-task').count()>0)
        page.goto(base+'/#bank-works');settled(page);check('full customer denominator and pagination',page.locator('#bank-work-results .recordrow').count()==25 and '전체 216개' in page.locator('#bank-work-count').inner_text())
        first=page.locator('#bank-work-results a').first.inner_text();page.get_by_role('button',name='다음',exact=True).click();check('actual list paginates',page.locator('#bank-work-results a').first.inner_text()!=first)
        page.locator('#bank-work-domain').select_option('cards');check('card scope filter reconciles','검색 23개' in page.locator('#bank-work-count').inner_text())
        page.locator('#bank-work-domain').select_option('');page.locator('#bank-work-query').fill('이자 지급');page.locator('#bank-work-results a').first.click();page.locator('#bank-country').wait_for();check('country selection follows customer goal',page.locator('#bank-country').input_value()=='')
        page.locator('#bank-country').select_option('KR');check('real local function wording and scope',any('지금 이자 받기' in x for x in page.locator('.bank-benchmark').all_inner_texts()) and '공식 기능 안내' in page.locator('.bank-benchmark').inner_text())
        page.locator('#bank-country').select_option('GB');check('missing country evidence not called unsupported','기능 미지원이라는 뜻은 아닙니다' in page.locator('#bank-country-results').inner_text())
        wallet=next(w for w in d['works'] if w.get('new_result_key')=='payment-wallet-bind');page.goto(base+'/#bank-work/'+wallet['id']);page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('GB');page.locator('.bank-benchmark summary').click();check('English source expression with evidence type',page.locator('.bank-benchmark h3').inner_text()=='Digital Wallet' and '앱 직접 관찰·UI 버전 미확인' in page.locator('.bank-benchmark').inner_text())
        page.goto(base+'/#bank-scope');settled(page);check('empty standards text and observed screens distinguished','공란 79개' in page.locator('#content').inner_text() and '실제 앱 캡처 0개' in page.locator('#content').inner_text())
        check('collection coverage reconciles scoped count',all(s in page.locator('#content').inner_text() for s in ['모수 216개','업무 189개','미연결 27개']))
        page.goto(base+'/#bank-works');settled(page)
        with page.expect_download() as dl:page.get_by_role('link',name='확정 목록 CSV 받기').click()
        check('actual complete CSV download',dl.value.suggested_filename=='WGSS-bank-customer-ui-v1.1.csv')
        for route in ['bank-works','bank-scope','bank-work/'+wallet['id']]:
            page.goto(base+'/#'+route);settled(page);page.set_viewport_size({'width':390,'height':844});check(route+' mobile does not overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.set_viewport_size({'width':1440,'height':1000})
        page.route('**/data/bank-ui.json',lambda r:r.fulfill(status=503,body='unavailable'));page.goto(base+'/#bank-works');page.reload();settled(page);check('scope load failure recoverable',page.get_by_role('button',name='다시 불러오기').is_visible());page.unroute('**/data/bank-ui.json');page.get_by_role('button',name='다시 불러오기').click();settled(page);check('retry restores authoritative denominator','전체 216개' in page.locator('#bank-work-count').inner_text())
        check('no uncaught browser errors',not errors);browser.close()
    print(json.dumps({'bank_browser':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:server.shutdown();server.server_close()
