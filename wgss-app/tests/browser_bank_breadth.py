"""Whole-scope navigation and native financial terms from admitted local sources."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];checks=[];errors=[]
def check(n,ok):assert ok,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(s.server_port)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/#bank-collection');page.locator('#bank-collection-count').wait_for()
  check('entire216 is default, 32pilot detail folded',page.locator('#bank-collection-scope').input_value()=='all' and not page.get_by_text('32개 시범 업무의 상세 진척',exact=True).evaluate('(e)=>e.parentElement.open'))
  check('all12 domains report189 linked out of216',page.locator('.bank-domain-progress tbody tr').count()==12 and '업무 연결률 87.5%' in page.locator('#content').inner_text() and '국가·업무 조합 연결률 23.2%' in page.locator('#content').inner_text())
  page.locator('[data-bank-progress-domain=alternative]').click();check('alternative domain keeps all12works despite9linked','표시 12개' in page.locator('#bank-collection-count').inner_text() and '조사 미착수' in page.locator('#bank-collection-results').inner_text())
  page.locator('[data-bank-progress-domain=trade]').click();check('enterprise domain uses correct frozen21 work denominator','표시 21개' in page.locator('#bank-collection-count').inner_text())
  with page.expect_download() as dl:page.get_by_role('link',name='216개 업무의 상태·다음 작업 받기').click()
  d=json.loads(dl.value.path().read_text());check('filtered view still downloads all216 tasks, not only connected189',len(d['work_queue'])==216 and sum(x['evidence_stage']=='unlinked' for x in d['work_queue'])==27 and not d['practitioner_utility_measured'])
  page.goto(base+'/#bank-scope');page.get_by_role('heading',name='범위 v1.1 정정',exact=True).wait_for();check('three metadata conflicts now resolved under explicit scope revision','독립된 직접 결과 2개' in page.locator('#content').inner_text());page.goto(base+'/#bank-collection');page.locator('#bank-collection-count').wait_for()
  out=R/'research/ui-v34';out.mkdir(exist_ok=True);page.goto(base+'/#bank-collection');page.locator('#bank-collection-count').wait_for();page.evaluate('scrollTo(0,0)');page.screenshot(path=str(out/'breadth-desktop.png'),full_page=False);page.set_viewport_size({'width':390,'height':844});check('domain progress table contained on mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'breadth-mobile.png'));page.set_viewport_size({'width':1440,'height':1000})
  page.goto(base+'/#bank-works');page.locator('#bank-work-query').wait_for()
  for query,expected in [('부가세박스','WGSS-UI-D73DBA2F52C6'),('티머니','WGSS-UI-7AC4A6C80B48'),('전자서명으로 계약','WGSS-UI-0DD0B76C851C')]:
   page.locator('#bank-work-query').fill(query);check('source-backed native navigation: '+query,page.locator(f'a[href="#bank-work/{expected}"]').count()==1)
  page.locator('#bank-work-query').fill('모임통장');check('shared service does not silently become legal joint ownership',page.locator('a[href="#bank-work/WGSS-UI-E99864B2D351"]').count()==1 and page.locator('a[href="#bank-work/WGSS-UI-EFE3E19CE882"]').count()==0)
  page.goto(base+'/#bank-capture-plan');page.locator('#bank-capture-count').wait_for();first=page.locator('#bank-capture-queue tbody tr').first.inner_text();page.locator('#bank-capture-next').click();check('648 plan truly paginates and changes tasks','2/54페이지' in page.locator('#bank-capture-count').inner_text() and page.locator('#bank-capture-queue tbody tr').first.inner_text()!=first)
  page.locator('#bank-capture-country').select_option('HK');check('country filtering resets page and retains216','총 216개 조합 · 1/11페이지' in page.locator('#bank-capture-count').inner_text())
  page.goto(base+'/#bank-work/WGSS-UI-A2A53B62BD1A');page.locator('#bank-country').select_option('HK');card=page.locator('.bank-benchmark').filter(has_text='공식 안내서 화면 예시');card.locator('.bank-guide-gallery summary').click();card.locator('.bank-guide-image').last.scroll_into_view_if_needed();page.wait_for_function("[...document.querySelectorAll('.bank-guide-image')].every(i=>i.complete&&i.naturalWidth>0)")
  card.get_by_text('자료의 기준과 확인 범위',exact=True).click()
  check('two rates lookup modes remain guide references, not sequential currency transaction',card.locator('.bank-guide-image').count()==2 and '추가 환율 조회 안내' in card.inner_text() and '환전 체결 화면으로 사용하지 않습니다' in card.inner_text())
  page.screenshot(path=str(out/'fx-guide-reference.png'));page.set_viewport_size({'width':390,'height':844});check('new original FX guide gallery contained on mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  check('no browser errors',not errors);b.close()
 print(json.dumps({'bank_breadth_browser':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
