"""Definition-audit route safeguards: lazy source report, unit distinction and failure recovery."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();BASE='http://127.0.0.1:'+str(server.server_port)
report={'version':'scope-test','global_mece_total':None,'methodology':{'unit':'역할·대상·의도·전후 상태의 업무 정의','rules':['표준별 수를 금융거래 총수로 합산하지 않습니다.','<img src=x onerror=window.injected=1>'], 'gates':[{'id':'source','label':'원문 확인','status':'passed'},{'id':'global','label':'전체 범위 검증','status':'BIAN 산출물 차이 미해결'}]},'standards':[{'name':'BIAN','unit':'공개 서비스 책임 노드','count':341,'source_url':'https://bian.org/deliverables/service-landscape/','note':'공식 정의와 현재 공개 목록'}],'discrepancies':['공식 원문 322와 공개 목록 341의 차이는 미해결입니다.'],'collection':{'summary':{'source_count':84,'fetched_sources':83,'distinct_candidate_urls':3314,'body_article_documents_fetched':0,'accepted_new_benchmarks':0,'run_at':'2026-10-02T08:54:28+00:00'},'providers':[{'id':'citi','label':'CitiManager','source_count':14,'article_count':0,'pdf_count':13,'pdf_pages':418,'discovered_urls':11,'accepted_count':0,'index_url':'https://www.citibank.com/tts/solutions/commercial-cards/','note':'공식 매뉴얼 수집 · 본문 정책 검토 전'},{'id':'unknown','label':'미확인 서비스','index_url':'javascript:alert(1)','note':'범위 미확인'}]}}
report['standards'].append({'name':'NIST','unit':'용어 + 선택 섹션','count':'189 + 19','source_url':'https://pages.nist.gov/800-63-4/sp800-63.html','note':'단위 구분'})
checks=[];errors=[]
def check(name,ok):assert ok,name;checks.append(name)
def settled(page):page.wait_for_function("document.querySelector('h1')&&!document.querySelector('.loading')")
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));requests=[];page.on('request',lambda r:requests.append(r.url));state={'fail':False}
  def respond(route):route.fulfill(status=503,body='unavailable') if state['fail'] else route.fulfill(status=200,content_type='application/json',body=json.dumps(report))
  page.route('**/data/definition-audit.json',respond)
  page.goto(BASE+'/#explore');settled(page);check('practitioner route avoids definition report download',not any('definition-audit.json' in r for r in requests))
  page.goto(BASE+'/#scope');settled(page)
  check('scope route has admin navigation active',page.locator('#nav-admin').evaluate("e=>e.classList.contains('active')"))
  check('scope tab linked and selected',page.locator('.tabs a[href="#scope"].active').count()==1)
  check('scope lazily fetches its report without full standard graph',sum('definition-audit.json' in r for r in requests)==1 and not any('standards.json' in r for r in requests))
  check('global total not invented',page.get_by_text('금융 전체의 거래 총수는 확정하지 않았습니다.',exact=True).is_visible())
  check('customer institution and support work visible',all(page.get_by_role('heading',name=n,exact=True).is_visible() for n in ['고객 업무','금융사 내부 처리','공통 지원 업무']))
  check('unresolved and passed gates separately displayed','미해결' in page.locator('.scope-gates').inner_text() and '통과' in page.locator('.scope-gates').inner_text())
  check('standard mixed source-unit count rendered verbatim','189 + 19' in page.locator('.scope-standards').inner_text())
  check('official artifact discrepancy preserved',page.get_by_text('공식 원문 322와 공개 목록 341의 차이는 미해결입니다.',exact=True).is_visible())
  check('source discovery does not masquerade as accepted benchmark',page.locator('.metric').nth(0).locator('strong').inner_text()=='83' and page.locator('.metric').nth(1).locator('strong').inner_text()=='3,314' and page.locator('.metric').nth(3).locator('strong').inner_text()=='0')
  citi=page.locator('.scope-providers tbody tr').first;check('provider acquisition units preserved',[citi.locator('td').nth(i).inner_text() for i in range(6)]==['14','0','13','418','11','0'])
  check('unknown provider fields never converted to zero',page.locator('.scope-providers tbody tr').nth(1).inner_text().count('미확인')>=6)
  check('official source links remain directly inspectable',page.locator('.scope-standards a').first.get_attribute('href')==report['standards'][0]['source_url'] and citi.locator('a').get_attribute('href')==report['collection']['providers'][0]['index_url'])
  check('untrusted report text and unsafe link stay inert',not page.evaluate('window.injected') and page.locator('#content img').count()==0 and page.locator('.scope-providers tbody tr').nth(1).locator('a').get_attribute('href')=='#')
  page.evaluate("location.hash='explore'");settled(page);page.evaluate("location.hash='scope'");settled(page);check('scope reuses one successfully loaded report',sum('definition-audit.json' in r for r in requests)==1)
  for width,font in [(390,''),(390,'32px'),(1440,'32px')]:
   page.set_viewport_size({'width':width,'height':844});page.evaluate('(font)=>document.documentElement.style.fontSize=font',font);check(f'scope table overflow belongs to table at width{width} font{font}',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  page.evaluate("document.documentElement.style.fontSize=''");state['fail']=True;page.reload();settled(page);check('report failure has retry action',page.get_by_role('button',name='다시 불러오기').is_visible());state['fail']=False;page.get_by_role('button',name='다시 불러오기').click();settled(page);check('failed report request can recover',page.get_by_role('heading',name='설계 기준과 수집 현황',exact=True).is_visible())
  page.unroute('**/data/definition-audit.json',respond);page.reload();settled(page)
  real=json.loads((ROOT/'dist/data/definition-audit.json').read_text())
  check('real report source count rendered',page.locator('.metric').nth(0).locator('strong').inner_text()==format(real['collection']['summary']['fetched_sources'],','))
  check('real acquired body count includes FAQ and product bodies',page.locator('.metric').nth(2).locator('strong').inner_text()==format(real['collection']['summary']['body_documents_total'],','))
  check('real provider rows reconcile with frozen data',page.locator('.scope-providers tbody tr').count()==len(real['collection']['providers']))
  check('real NIST glossary and selected sections stay separate',page.locator('.scope-standards tbody tr').count()==len(real['standards']) and '189 + 19' not in page.locator('.scope-standards').inner_text())
  check('real remaining FAQ cardinality gaps visible','관측 고유 54개' in page.locator('.scope-discrepancies').inner_text() and '관측 고유 185개' in page.locator('.scope-discrepancies').inner_text())
  page.set_viewport_size({'width':390,'height':844});check('real report mobile overflow belongs to tables',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
  check('no uncaught scope browser errors',not errors);browser.close()
 print(json.dumps({'status':'passed','checks':len(checks),'items':checks,'browser_errors':errors},ensure_ascii=False))
finally:server.shutdown();server.server_close()
