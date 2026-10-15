"""Meaningful workflow and evidence safeguards for the rebuilt WGSS UI."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/ui-v10';OUT.mkdir(exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();BASE='http://127.0.0.1:'+str(server.server_port)
checks=[]
def check(name,condition):
 assert condition,name
 checks.append(name)
def route(page,hash):
 page.goto(BASE+'/#'+hash);page.wait_for_function("document.querySelector('h1') && !document.querySelector('.loading')")
 page.wait_for_timeout(120)
def overflow(page):return page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
errors=[];requests=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
  route(page,'explore');check('popular financial paths browse without provider evidence prerequisite',page.locator('.taskcard').count()==12);check('practitioner search avoids full standard download',not any('standards.json' in u for u in requests))
  check('search and first task visible in first viewport',page.locator('.taskcard').first.bounding_box()['y']<850)
  page.screenshot(path=str(OUT/'desktop-explore.png'),full_page=False)
  page.locator('#task-query').fill('카드 잠금');check('plain Korean query returns lock and unlock separately',page.locator('.taskcard').count()==2)
  page.locator('#task-query').fill('카드 분실신고');check('loss reporting is discoverable as separate intent from temporary lock',page.locator('#task-results .taskcard').count()==1 and page.get_by_role('heading',name='카드 분실신고·재발급',exact=True).count()==1)
  page.locator('#task-query').fill('자동이체 해지');check('ambiguous debit versus standing order preserved as two choices',page.locator('.taskcard').count()==2)
  page.locator('#filter-market').select_option('KR');check('market-filtered matches use actual records',page.locator('#task-results .taskcard').count()>0 and '금융결제원' in page.locator('#task-results').inner_text())
  page.locator('#filter-product').select_option('TOSS');check('empty target has no invented evidence',page.locator('.taskcard').count()==0 and page.get_by_text('조건에 맞는 기업 자료가 없습니다').is_visible())
  page.get_by_role('button',name='필터와 검색 초기화').click();page.locator('#task-query').fill('<img src=x onerror=window.wgssInjected=1>');check('search input remains inert',page.evaluate('!window.wgssInjected') and page.locator('#task-results img').count()==0)
  route(page,'explore');page.locator('#task-query').fill('계좌 개설');check('account opening definition discoverable without fabricated bank examples',page.locator('#task-results .taskcard').count()==1 and page.get_by_role('heading',name='계좌 개설',exact=True).count()==1 and '자료 수집 전' in page.locator('#task-results').inner_text())
  route(page,'task/card-unlock');check('Monzo unlock evidence not mapped to freezing',page.locator('.examplecard',has_text='Monzo').count()==1)
  page.locator('.examplecard',has_text='Monzo').get_by_role('link',name='사례 보기').click();page.wait_for_timeout(100)
  check('actual defrost wording and source class shown',page.locator('.evidence',has_text='공식 제품 이미지').count()==1 and page.locator('.evidence .quote',has_text='Defrost card').count()>=1)
  check('screen original asset loads',page.locator('.screenshot').evaluate('(el)=>el.complete && el.naturalWidth>0'))
  page.screenshot(path=str(OUT/'desktop-example.png'),full_page=False)
  route(page,'example/card-lock__WISE__unspecified__en');check('document-only example useful scope explicit',page.get_by_text('확보된 UI 화면이 없어 배치나 버튼 위치는 확인할 수 없습니다.').is_visible() and page.locator('.policyrow').count()==3)
  route(page,'task/direct-debit-end');cards=page.locator('.examplecard');check('cross-market examples available',cards.count()==3)
  cards.filter(has_text='Payinfo').get_by_role('button',name='비교 선택').click();check('compare disabled with one explicit selection',page.get_by_role('button',name='비교하기').is_disabled())
  cards.filter(has_text='Monzo').get_by_role('button',name='비교 선택').click();page.get_by_role('button',name='비교하기').click();page.wait_for_timeout(100)
  check('cross-market comparison allowed and qualified',page.get_by_text('시장별 정책을 구분해 적용하세요.').is_visible())
  check('conflict and unknown preserved in comparison',page.get_by_text('화면의 처리 기한과 현재 문서가 다름',exact=True).count()==1 and page.locator('td',has_text='미확인').count()>0)
  page.screenshot(path=str(OUT/'desktop-compare.png'),full_page=False)
  page.get_by_role('button',name='비우기').click();route(page,'example/direct-debit-end__PAYINFO__KR__ko')
  check('conflicting screen warnings appear twice before asset',page.get_by_text('이 화면의 처리 기한은 현재 도움말과 다릅니다',exact=True).count()==2)
  check('record locator source remains explicit',page.get_by_role('link',name='원문 확인').count()>=4)
  route(page,'admin');check('separate counts render',page.locator('#content > .metrics .metric').count()==4 and page.locator('#content > .metrics .metric').nth(0).inner_text().find('21')>=0)
  page.locator('#coverage-axis').select_option('concept');check('many-to-many count caveat explicit',page.get_by_text('같은 기능이나 기록이 여러 표준 참조에 연결될 수 있습니다.',exact=False).is_visible())
  page.screenshot(path=str(OUT/'desktop-admin.png'),full_page=False)
  route(page,'records?status=conflict');check('conflict drilldown reconciles',page.locator('.recordrow').count()==2 and '2개 기록' in page.locator('#record-count').inner_text())
  route(page,'records?status=quarantined');check('quarantined sources retained for admin only',page.locator('.recordrow').count()==5 and 'O04' in page.locator('#record-results').inner_text())
  route(page,'record/UI004');check('corporate card conditions and unverified version retained','미확인' in page.locator('.facts').inner_text() and '법인' in page.locator('.evidence').inner_text())
  route(page,'concepts');check('entire object index browsable','791개 참조 항목' in page.locator('#concept-count').inner_text());page.locator('#concept-query').fill('PaymentCard');check('object search exact available',page.locator('.recordrow').count()==1)
  page.locator('.recordrow a').click();page.wait_for_timeout(100);check('provisional links and real relationships shown',page.get_by_text('공식 원문의 참조와 연결 해석은 별개입니다.',exact=False).is_visible() and page.locator('.recordrow').count()>0)
  route(page,'concepts?standard=BIAN');check('BIAN official service resources browsable','258개 참조 항목' in page.locator('#concept-count').inner_text());page.locator('#concept-query').fill('Party Authentication');page.locator('.recordrow a').click();page.wait_for_timeout(100);check('BIAN scoped definition rendered','support access to the banks products and services' in page.locator('#content').inner_text().lower() and page.get_by_text('표준 간 동치',exact=False).count()>0)
  route(page,'concepts?standard=FIBO');check('released FIBO schema terms browsable','1549개 참조 항목' in page.locator('#concept-count').inner_text());page.locator('#concept-query').fill('payment card');page.locator('.recordrow a').first.click();page.wait_for_timeout(100);check('FIBO URI navigation preserves complete identifier',page.locator('h1').inner_text()=='payment card')
  route(page,'concepts?standard=NIST');page.locator('#concept-query').fill('identity proofing');page.locator('.recordrow a').first.click();page.wait_for_timeout(100);check('NIST glossary native ID not invented',page.get_by_text('용어별 원문 식별자 없음',exact=False).is_visible())
  route(page,'example/identity-proofing__WISE__unspecified__en');check('new identity feature is document-grounded',page.locator('.policyrow').count()==3 and page.get_by_text('Update information',exact=True).is_visible())
  route(page,'example/login-authentication__WISE__unspecified__en');check('authentication is distinct from identity proofing',page.locator('h1').inner_text().find('Wise')>=0 and page.get_by_text('2-step verification',exact=True).count()>0)
  route(page,'targets');check('zero-evidence targets and intended platforms explicit',page.locator('article',has_text='토스 · 토스뱅크').get_by_text('수집 전',exact=True).is_visible() and page.get_by_text('수집 목표 플랫폼:',exact=False).count()==9)
  page.set_viewport_size({'width':390,'height':844});route(page,'explore');page.get_by_role('button',name='초기화',exact=True).click()
  for name in ['explore','task/direct-debit-end','example/direct-debit-end__PAYINFO__KR__ko','admin','records','concepts','targets']:
   route(page,name);check('mobile no page-wide horizontal overflow: '+name,overflow(page))
   if name=='explore':page.screenshot(path=str(OUT/'mobile-explore.png'),full_page=False)
  route(page,'task/direct-debit-end');page.locator('[data-compare]').nth(0).click();page.locator('[data-compare]').nth(1).click();page.get_by_role('button',name='비교하기').click();page.wait_for_timeout(100);check('mobile comparison scroll belongs to table',overflow(page) and page.locator('.tablewrap').evaluate('el=>el.scrollWidth>el.clientWidth'))
  page.screenshot(path=str(OUT/'mobile-compare.png'),full_page=False)
  page.get_by_role('button',name='비우기').click()
  for name in ['explore','admin','record/UI004','concepts']:
   route(page,name);page.evaluate("document.documentElement.style.fontSize='32px'");
   check('200 percent text fits page: '+name,overflow(page))
   page.evaluate("document.documentElement.style.fontSize=''")
  check('no uncaught browser errors',not errors)
  check('primary accent is green',page.locator('.tabs a.active').evaluate('el=>getComputedStyle(el).backgroundColor')=='rgb(0, 134, 83)')
  browser.close()
 report={'status':'passed','checks':len(checks),'items':checks,'screenshots':'research/ui-v10','browser_errors':errors};(OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
finally:server.shutdown();server.server_close()
