"""Practitioner-facing document/control distinctions and mobile readability."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];out=R/'research/ui-v36';out.mkdir(exist_ok=True)
data=json.loads((R/'dist/data/bank-ui.json').read_text());checks=[];errors=[]
def check(n,v):assert v,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')))
threading.Thread(target=s.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(s.server_port)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+'/#bank-work/WGSS-UI-798ED0DAB916');page.locator('#bank-country').select_option('GB');card=page.locator('.bank-benchmark').filter(has=page.get_by_role('heading',name='Issue refunds',exact=True))
  check('document heading explicitly distinguished before the heading',card.locator('.bank-expression-purpose').inner_text()=='문서의 표제·용어 · 실제 UI 표기 미확인' and card.locator('.bank-expression-purpose').evaluate('(e)=>e.nextElementSibling.tagName==="H3"'))
  controls=card.locator('.bank-documented-controls');check('document-described control actions native English',controls.locator('li').count()==4 and 'Refund payment · 조작 문구' in controls.inner_text() and 'Other · 선택 항목' in controls.inner_text() and '환불 사유를 설명하는 메모가 필수' in controls.inner_text())
  check('refund amount not presented as an observed field label','refund amount · 입력 데이터 · 필드 라벨 미확인' in controls.inner_text() and '실제 화면·배치·현재 UI 버전 미확인' in controls.inner_text())
  check('card funding pending not cardholder receipt','pending' in card.inner_text() and '고객 수령 완료' in card.inner_text());card.screenshot(path=str(out/'refund-document-controls-desktop.png'))
  page.set_viewport_size({'width':390,'height':844});check('refund controls fit mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'refund-document-controls-mobile.png'))
  page.goto(url+'/#bank-work/WGSS-UI-020499E81104');page.locator('#bank-country').select_option('MY');page.locator('#bank-reference-language').select_option('ms');card=page.locator('.bank-benchmark')
  check('Malay product term not promoted to an app button',card.locator('.bank-expression-purpose').count()==1 and card.locator('.bank-documented-controls').count()==0 and card.locator('h3').get_attribute('lang')=='ms')
  check('PIDM exclusion and dated source visible','PIDM' in card.inner_text() and '원금 미보장과 구분' in card.inner_text() and '2026-01-01' in card.inner_text());page.screenshot(path=str(out/'mudarabah-risk-mobile.png'))
  wid=next(b for b in data['benchmarks'] if b['id']=='BANK-BENCH-325')['ui_work_ids'][0];page.goto(url+'/#bank-work/'+wid);page.locator('#bank-country').select_option('KR');card=page.locator('.bank-benchmark').filter(has=page.get_by_role('heading',name='제21조 (청약의 철회)',exact=True));check('2024 insurance clause identified as document expression',card.locator('.bank-expression-purpose').count()==1 and card.locator('.bank-documented-controls').count()==0 and '2024.5' in card.inner_text())
  page.goto(url+'/#bank-collection');review=page.locator('#bank-practitioner-review');review.wait_for();check('quality findings collapsed outside practitioner detail',not review.evaluate('(e)=>e.open'));review.locator('summary').click();check('three concrete task assessments and no measured benefit claim',review.locator('.recordrow').count()==3 and '아직 측정하지 않았습니다' in review.inner_text());check('quality review fit mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'quality-audit-mobile.png'))
  check('no browser errors',not errors);browser.close()
 print(json.dumps({'browser_reference_quality_v34':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
