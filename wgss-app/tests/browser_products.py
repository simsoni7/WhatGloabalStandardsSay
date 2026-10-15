"""Practitioner product/action regressions, all current profile and explicit gap routes."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];K=json.loads((R/'dist/data/business-backbone.json').read_text());checks=[];errors=[]
def check(label,ok):assert ok,label;checks.append(label)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(s.server_port);out=R/'research/ui-v36';out.mkdir(parents=True,exist_ok=True)
try:
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/#legacy-explore');page.locator('#task-query').wait_for()
  for query,id,step in [('마이너스통장','overdraft',None),('카드론 신청','card-loan','apply'),('카드론 중도상환','card-loan','early-repay'),('마이너스 통장 한도조회','overdraft','eligibility'),('리볼빙 최소결제비율 변경','payment-revolving','min-ratio'),('리볼빙 약정결제비율 변경','payment-revolving','ratio'),('카드론 해지','card-loan','close')]:
   page.goto(base+'/#legacy-explore');page.locator('#task-query').fill(query);card=page.locator('.product-work-card').filter(has=page.get_by_role('heading',name=next(p['title'] for p in K['product_profiles'] if p['id']==id),exact=True));check(query+' resolves to its product',card.count()==1);card.click();page.locator('#product-step-result').wait_for()
   check(query+' selects the specific result only',page.locator('[data-product-step][aria-pressed="true"]').get_attribute('data-product-step')==step if step else page.locator('[data-product-step][aria-pressed="true"]').count()==0)
   if id=='overdraft' and step=='eligibility':check('borrowing ceiling does not show account transfer limit',page.locator('#product-step-result .card').count()==1 and page.get_by_role('heading',name='개인 대출한도·금리 조건 조회',exact=True).count()==1 and '거래한도 설정' not in page.locator('#product-step-result').inner_text())
  for query,pid,selected_step in [('26주적금 신청','installment-savings','open'),('부가세박스 해지','cash-pocket','close'),('mini카드 신청','prepaid-mini-card','apply'),('mini 26일저금','prepaid-saving-pocket',None),('내 신용정보 조회','credit-information','information')]:
   page.goto(base+'/#legacy-explore');page.locator('#task-query').fill(query);card=page.locator('.product-work-card').filter(has=page.get_by_role('heading',name=next(p['title'] for p in K['product_profiles'] if p['id']==pid),exact=True));check(query+' source-derived route',card.count()==1);card.click();page.locator('#product-step-result').wait_for()
   check(query+' keeps official variant conditions',page.locator('.source-variants .source-variant').count()==1 and page.get_by_role('heading',name='검색한 상품의 적용 조건',exact=True).count()==1)
   check(query+' correct screen result',page.locator('[data-product-step][aria-pressed="true"]').get_attribute('data-product-step')==selected_step if selected_step else page.locator('[data-product-step][aria-pressed="true"]').count()==0)
   page.locator('[data-product-step]').first.click();check(query+' retains source context when changing screen','q=' in page.url and page.locator('.source-variants .source-variant').count()==1)
  for query in ['카드론 우주여행','카드론 조회','카드론 vs 현금서비스 차이']:
   page.goto(base+'/#legacy-explore');page.locator('#task-query').fill(query);page.locator('.product-work-card').first.click();page.locator('#product-step-result').wait_for();check(query+' does not assume a step',page.locator('[data-product-step][aria-pressed="true"]').count()==0 and page.locator('#product-step-result .card').count()==0)
  page.goto(base+'/#legacy-explore');page.locator('#task-query').fill('카드론');page.screenshot(path=str(out/'desktop-cardloan-search.png'))
  page.goto(base+'/#product-work/card-loan?step=early-repay');page.locator('#product-step-result .card').wait_for();page.screenshot(path=str(out/'desktop-cardloan-early-repay.png'))
  page.set_viewport_size({'width':390,'height':844})
  for p in K['product_profiles']:
   page.goto(base+'/#product-work/'+p['id']);page.locator('#product-step-result').wait_for();check(p['id']+' does not assume an intended screen',page.locator('[data-product-step][aria-pressed="true"]').count()==0);check(p['id']+' mobile layout',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  for item in K['product_inventory']:
   if item['disposition']!='gap':continue
   page.goto(base+'/#product-gap/'+item['id']);page.get_by_role('heading',name=item['term'],exact=True).wait_for();check(item['id']+' is an explicit sourced gap',page.get_by_text(item['gap_reason'],exact=True).count()==1 and page.locator('[data-product-step]').count()==0);check(item['id']+' mobile layout',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  page.goto(base+'/#product-work/overdraft?step=eligibility');page.locator('#product-step-result').wait_for();page.screenshot(path=str(out/'mobile-overdraft-limit-gap.png'))
  page.goto(base+'/#product-coverage');page.get_by_role('heading',name='상품별 업무 연결 현황',exact=True).wait_for();check('admin current denominator and all profile rows',page.locator('.product-coverage-table tbody tr').count()==len(K['product_profiles']));check('admin includes independent source inventory gap counts',str(len(K['product_inventory']))+'개 표제' in page.locator('#content').inner_text());check('coverage mobile layout',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
  check('no browser errors',not errors);browser.close()
finally:s.shutdown()
report={'status':'passed','checks':len(checks),'profiles_verified':len(K['product_profiles']),'inventory_gap_routes_verified':sum(i['disposition']=='gap' for i in K['product_inventory']),'items':checks};(out/'browser-products-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='items'},ensure_ascii=False))
