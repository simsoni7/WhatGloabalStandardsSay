"""Actual catalogue search, pagination, drilldown, audit, downloads and recovery."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];data=json.loads((R/'dist/data/operations.json').read_text());checks=[];errors=[]
def check(name,ok):assert ok,name;checks.append(name)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
def settled(page):page.wait_for_function("document.querySelector('h1')&&!document.querySelector('.loading')")
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));requests=[];page.on('request',lambda r:requests.append(r.url))
  page.goto(base+'/#explore');settled(page);check('practitioner does not fetch the large review catalogue',not any('operations.json' in x for x in requests))
  page.goto(base+'/#operations');settled(page)
  check('actual count matches catalogue',page.locator('.metric strong').first.inner_text()==format(len(data['works']),','))
  check('MECE hold stays visible','아직 통과하지 않았습니다' in page.locator('.notice').inner_text())
  check('list renders 25 definitions and next page works',page.locator('#operation-results .recordrow').count()==25)
  first=page.locator('#operation-results a').first.inner_text();page.get_by_role('button',name='다음',exact=True).click();check('pagination changes actual records',page.locator('#operation-results a').first.inner_text()!=first)
  page.locator('#operation-query').fill('카드 일시 잠금');check('Korean search finds the corrected financial outcome',page.locator('#operation-results a').count()==1)
  page.locator('#operation-results a').first.click();page.get_by_role('heading',name='포함 조건',exact=True).wait_for();settled(page);check('detail exposes financial conditions and official references',all(page.get_by_role('heading',name=x,exact=True).count()==1 for x in ['포함 조건','제외 조건','유사 업무와의 경계','정의 근거']) and page.locator('a[target="_blank"]').count()>0)
  page.get_by_role('link',name='전체 목록',exact=True).click();page.locator('#operation-query').wait_for();settled(page);page.locator('#operation-query').fill('');page.locator('#operation-layer').select_option('institution');expected=sum(w['layer']=='institution' for w in data['works']);check('layer filter reconciles deterministic count',f'검색 {expected}개' in page.locator('#operation-count').inner_text())
  page.locator('#operation-layer').select_option('');page.locator('#operation-status').select_option('unresolved');check('unresolved rows are separately discoverable',f"검색 {data['audit']['counts_by_status']['unresolved']}개" in page.locator('#operation-count').inner_text())
  check('CSV is a usable complete download',page.request.get(base+'/data/operations.csv').ok and page.get_by_role('link',name='전체 목록 CSV 받기').get_attribute('download')=='WGSS-operations.csv')
  page.get_by_role('link',name='중복·누락 판정 보기').click();page.locator('#operation-audit-results').wait_for();settled(page);check('927 references are searchable without rendering all rows',page.locator('#operation-audit-results article').count()==25 and '927개' in page.locator('#operation-audit-count').inner_text())
  closure=page.locator('#mece-closure-progress');check('closure phases distinguish pending source nodes from financial work counts',closure.is_visible() and 'BIAN 원문 927개 중 최종 판정 대기 659개' in closure.inner_text() and 'root 재심 268개' in closure.inner_text() and '금융 전체의 확정 총수가 아닙니다' in closure.inner_text() and closure.locator('#mece-execution-plan > li').count()==6)
  check('complete model census remains distinct from final work count',all(x in closure.locator('#mece-census-summary').inner_text() for x in ['Opus 825개 / Sonnet 825개','NIST · 205개 절','181개','3,340개','Release 모듈 81개','잘못된 제외/경계 교정 16개','서로 다른 단계']))
  closure.locator('#mece-standard-scope > summary').click();check('standard concept inventories are not summed into financial work counts',all(x in closure.locator('#mece-standard-scope').inner_text() for x in ['791개','1,549개','208개','표준별 수를 합산해 업무 총수로 쓰지 않습니다','비수록은 금융업무 범위 제외가 아님']))
  closure.locator('#mece-pending-tickets > summary').click();pending=closure.locator('#mece-pending-tickets article');check('every pending closure task is retained with a next action and closure criteria',pending.count()==3 and all('종료 조건' in x.inner_text() and '없음' not in x.inner_text() for x in pending.all()) and all(x in ' '.join(pending.all_text_contents()) for x in ['Financial Compliance','기관 자금조달 부모','금융계정 통제']))
  closure.locator('#mece-source-followups > summary').click();check('new primary-source responsibility groups remain visible after local ticket closure',closure.locator('#mece-source-followups article').count()==5 and '전체 CE 확정의 조건' in closure.locator('#mece-source-followups').inner_text() and '신디케이트 대출' in closure.locator('#mece-source-followups').inner_text())
  closure.get_by_role('link',name='비교할 기존 정의').first.click();page.get_by_role('heading',name='포함 조건',exact=True).wait_for();settled(page);check('candidate comparisons link to existing definitions without admitting the candidate',page.get_by_role('heading',name='포함 조건',exact=True).is_visible());page.goto(base+'/#operation-audit');settled(page)
  page.locator('#operation-audit-state').select_option('검토 필요');check('CE blockers have their own filter','검토 필요' in page.locator('#operation-audit-results').inner_text())
  page.locator('#operation-audit-query').fill('Financial Statements');check('financial statement result is not hidden under enterprise exclusion',page.locator('#operation-audit-results article').count()==1 and all(x in page.locator('#operation-audit-results').inner_text() for x in ['원문 판정 기록','재무상태표','검토 필요']))
  page.locator('#operation-audit-query').fill('Employment Contract Support');check('undefined HR source remains a specification gap rather than name-based exclusion',page.locator('#operation-audit-results article').count()==1 and all(x in page.locator('#operation-audit-results').inner_text() for x in ['공란','TBD','원문 판정 기록','검토 필요']))
  page.locator('#operation-audit-query').fill('');
  page.locator('#operation-audit-kind').select_option('decisions');page.locator('#operation-audit-query').fill('bank draft');check('actual compound decision can be inspected',page.locator('#operation-audit-results article').count()>0)
  for route in ['operations','operation-audit']:
   page.goto(base+'/#'+route);settled(page);page.set_viewport_size({'width':390,'height':844});check(route+' mobile pane does not overflow document',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.set_viewport_size({'width':1440,'height':1000})
  page.route('**/data/operations.json',lambda r:r.fulfill(status=503,body='unavailable'));page.goto(base+'/#operations');page.reload();settled(page);check('load failure is recoverable',page.get_by_role('button',name='다시 불러오기').is_visible());page.unroute('**/data/operations.json');page.get_by_role('button',name='다시 불러오기').click();settled(page);check('retry recovers the same actual list',page.get_by_role('heading',name='금융업무 전체 목록',exact=True).is_visible())
  check('no uncaught browser errors',not errors);browser.close()
 print(json.dumps({'status':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:server.shutdown();server.server_close()
