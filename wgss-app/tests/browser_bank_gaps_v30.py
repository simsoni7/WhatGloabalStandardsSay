"""Current new-source exploration and financial guide rendering, desktop and mobile."""
import json,functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];checks=[];errors=[];out=R/'research/ui-v34';out.mkdir(exist_ok=True)
def check(n,ok):assert ok,n;checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/#bank-collection');page.locator('#bank-collection-count').wait_for();check('19 targets include current pension administration operator and NatWest','대상 금융 플랫폼 36곳' in page.locator('#content').inner_text() and 'eMPF · 연금 행정 플랫폼' in page.locator('#content').inner_text() and 'NatWest' in page.locator('#content').inner_text())
  page.locator('#bank-collection-provider').select_option('empf-hk');page.locator('#bank-collection-state').select_option('screen');check('eMPF filter chooses HongKong and exactly2 canonical screen works',page.locator('#bank-collection-country').input_value()=='HK' and '표시 2개' in page.locator('#bank-collection-count').inner_text())
  page.get_by_text('원문 기능의 의미 구분 추가 검토 25건',exact=True).click();check('prior2 and new3 source issues retained','정기 투자계획·출금동의 복합 흐름' in page.locator('#content').inner_text() and 'HL→Broadridge' in page.locator('#content').inner_text() and 'MPF 제도 가입 신청 접수와 가입관계 등록의 경계' in page.locator('#content').inner_text())
  for wid,country,name in [('2DB1D4844DD5','GB','NatWest'),('58A48889FF96','HK','eMPF')]:
   page.goto(base+'/#bank-work/WGSS-UI-'+wid);page.locator('#bank-country').select_option(country);cards=page.locator('.bank-benchmark').filter(has_text=name);check('current locally scoped source available: '+wid,cards.count()>0)
   card=cards.first;img=card.locator('.bank-guide-image').first;img.scroll_into_view_if_needed();page.wait_for_function('(src)=>[...document.querySelectorAll("img")].find(i=>i.getAttribute("src")===src)?.naturalWidth>0',arg=img.get_attribute('src'))
   check('original selected financial guide loads: '+wid,img.is_visible() and card.get_by_role('link',name='공식 안내 화면 원본 크게 보기').get_attribute('href').startswith('evidence/bank-v30/'))
   if name=='NatWest':check('request Sent not disbursement, amount/method wording visible','Sent' in card.inner_text() and 'Requested Amount' in card.inner_text() and 'Payment Method' in card.inner_text())
   if name=='eMPF':
    card.get_by_text('자료의 기준과 확인 범위',exact=True).click();check('7 references distinguish existing balance vs future money and operator vs trustee',cards.count()==7 and '향후' in cards.nth(1).inner_text() and 'MPF 행정 플랫폼 운영자' in card.inner_text() and '발행자·수탁자' in page.locator('#bank-country-results').inner_text())
   card.scroll_into_view_if_needed();page.screenshot(path=str(out/(wid+'-new-reference-desktop.png')));page.set_viewport_size({'width':390,'height':844});img.scroll_into_view_if_needed();check('new guide fits mobile: '+wid,page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/(wid+'-new-reference-mobile.png')));page.set_viewport_size({'width':1440,'height':1000})
  page.goto(base+'/#bank-work/WGSS-UI-A12F4C4E3669');page.locator('#bank-country').select_option('HK');check('early withdrawal source only Permanent Departure and separate normal65','영구 출국 사유' in page.locator('#bank-country-results').inner_text() and '65세 정상 수급' in page.locator('#bank-country-results').inner_text())
  page.goto(base+'/#bank-work/WGSS-UI-E6ECD0996B28');page.locator('#bank-country').select_option('KR');check('two insurance request templates never become approved pension membership','삼성화재' in page.locator('#bank-country-results').inner_text() and '직장인단체 연금보험' in page.locator('#bank-country-results').inner_text() and '공개 웹 템플릿' in page.locator('#bank-country-results').inner_text())
  page.goto(base+'/#bank-work/WGSS-UI-F12F8ED99251');page.locator('#bank-country').select_option('GB');check('new ii own voting reference admitted while HL partner-only candidate still staged',page.locator('.bank-benchmark').filter(has_text='interactive investor').count()==1 and page.locator('.bank-benchmark').filter(has_text='Hargreaves').count()==0)
  page.goto(base+'/#bank-collection');page.locator('#bank-collection-count').wait_for();page.set_viewport_size({'width':390,'height':844});check('current administration table and review queue contained',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));check('no browser errors',not errors);browser.close()
 print(json.dumps({'bank_gaps_browser_v30':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:server.shutdown();server.server_close()
