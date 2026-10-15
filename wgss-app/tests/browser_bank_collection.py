"""Country/provider filtering, native guide rendering and full-gap matrix download."""
import csv,functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];d=json.loads((R/'dist/data/bank-ui.json').read_text());checks=[];errors=[]
def check(name,ok):assert ok,name;checks.append(name)
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
def settled(page):page.wait_for_function("document.querySelector('h1')&&!document.querySelector('.loading')")
try:
 with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'/#bank-collection');settled(page)
    check('whole216 opens by default, pilot remains separate','전체 기준 216개 · 표시 216개' in page.locator('#bank-collection-count').inner_text() and page.locator('.bank-collection-table tbody tr').count()==20)
    page.get_by_text('32개 시범 업무의 상세 진척',exact=True).click()
    with page.expect_download() as priority_dl:page.get_by_role('link',name='32개 우선 업무 연결표 CSV 받기').click()
    priority_rows=list(csv.DictReader(priority_dl.value.path().open(encoding='utf-8-sig')))
    check('priority download preserves all 96 gaps and practical grades',len(priority_rows)==96 and sum(r['same_example_flow_and_condition']=='True' for r in priority_rows)==40)
    check('five study countries and reviewed empty states visible',page.locator('.bank-collection-table thead th').count()==6 and '검토 후 연결 보류' in page.locator('#bank-collection-results').inner_text())
    check('scope, providers and gallery counts are separate',all(x in page.locator('#content').inner_text() for x in ['189','27','대상 금융 플랫폼 36곳','조합 1080개','화면 예시가 있는 조합 36개']))
    page.locator('#bank-collection-scope').select_option('all');check('full 216 works remain accessible','표시 216개' in page.locator('#bank-collection-count').inner_text());page.locator('#bank-collection-query').fill('송금 요청');check('one transfer work, no country duplicate denominator','표시 1개' in page.locator('#bank-collection-count').inner_text())
    check('local UK and HK references on same work row',all(x in page.locator('#bank-collection-results').inner_text() for x in ['HSBC UK','HSBC Hong Kong','화면 예시 있음']))
    page.locator('#bank-collection-provider').select_option('wise');check('global Wise guide not invented as local proof',page.locator('#bank-collection-country').input_value()=='GB' and '조사 미착수' in page.locator('#bank-collection-results').inner_text())
    page.locator('#bank-collection-country').select_option('HK');check('incompatible provider resets on new country',page.locator('#bank-collection-provider').input_value()=='' and page.locator('.bank-collection-table thead th').count()==2)
    page.locator('#bank-collection-query').fill('');page.locator('#bank-collection-state').select_option('screen');check('HK guide-backed works filter correctly','표시 20개' in page.locator('#bank-collection-count').inner_text())
    with page.expect_download() as download:page.get_by_role('link',name='전체 연결표 CSV 받기').click()
    downloaded=download.value.path();rows=list(csv.DictReader(downloaded.open(encoding='utf-8-sig')))
    check('download preserves1080 full denominator cells despite view filters',len(rows)==1080 and sum(r['evidence_state']=='not_collected' for r in rows)==829)
    for short,label in [('E7352823594F','您的滙豐戶口之間'),('8C8F9954FAF2','賬面結餘'),('314E135C277E','繳付款項')]:
        page.goto(base+'/#bank-work/WGSS-UI-'+short);page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('HK');img=page.locator('.bank-guide-image').first
        img.scroll_into_view_if_needed();page.wait_for_function("document.querySelector('.bank-guide-image')?.complete&&document.querySelector('.bank-guide-image').naturalWidth>0")
        check('original guide image loads: '+short,img.is_visible() and label in page.locator('.bank-benchmark h3').first.inner_text())
        check('guide reference not mislabeled as direct app capture: '+short,'공식 안내서 화면 예시' in page.locator('.bank-benchmark').first.inner_text() and '앱 버전 미확인' in page.locator('.bank-benchmark').first.inner_text())
    page.goto(base+'/#bank-work/WGSS-UI-D4DF22E05F69');page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('KR');ars=page.locator('.bank-benchmark').filter(has_text='전화 ARS 기능 안내');check('ARS proof visibly not a visual app example',ars.count()==1 and '우리카드' in ars.inner_text() and ars.locator('.bank-guide-image').count()==0)
    for route in ['bank-collection','bank-work/WGSS-UI-314E135C277E']:
        page.goto(base+'/#'+route);settled(page);page.set_viewport_size({'width':390,'height':844})
        if route.startswith('bank-work'):page.locator('#bank-country').select_option('HK')
        check('mobile page contains its table/gallery: '+route,page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.set_viewport_size({'width':1440,'height':1000})
    page.goto(base+'/#admin');settled(page);check('DB home shows current collection scope before older source graph',page.locator('#content h2').first.inner_text()=='216개 업무 중 189개에 자료를 연결했습니다')
    page.goto(base+'/#bank-work/WGSS-UI-3826A2FD05F2');page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('KR');check('card application supported beyond entry-only button','디자인·영문 이름 선택 후 신청 완료' in page.locator('#bank-country-results').inner_text())
    page.goto(base+'/#bank-work/WGSS-UI-57106ED8458D');page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('HK');check('token generation is an intermediate login step','인터넷뱅킹 접속 인증' in page.locator('#bank-country-results').inner_text() and '유효시간 안에 인터넷뱅킹에 입력' in page.locator('#bank-country-results').inner_text())
    check('original image is explicitly openable',page.get_by_role('link',name='공식 안내 화면 원본 크게 보기').get_attribute('href').startswith('evidence/bank-v25/'))
    out=R/'research/ui-v34';out.mkdir(exist_ok=True);page.goto(base+'/#bank-collection');settled(page);page.locator('#bank-collection-scope').select_option('priority');page.locator('#bank-collection-country').select_option('');page.locator('#bank-collection-state').select_option('');page.locator('#bank-collection-query').fill('');page.screenshot(path=str(out/'priority-desktop.png'));page.set_viewport_size({'width':390,'height':844});page.locator('.bank-priority-summary').scroll_into_view_if_needed();page.screenshot(path=str(out/'priority-mobile.png'))
    page.set_viewport_size({'width':1440,'height':1000});page.goto(base+'/#bank-work/WGSS-UI-F94E9EA98403');page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('GB')
    check('UK identity comparison preserves both providers',all(x in page.locator('#bank-country-results').inner_text() for x in ['Monzo','HSBC UK']))
    page.locator('.bank-guide-gallery summary').click();check('native guide padding folded without replacing original image',page.locator('.bank-guide-focus').count()==4 and '내용 확대' in page.locator('#bank-country-results').inner_text())
    check('all four native UK identity steps are available',page.locator('.bank-guide-image').count()==4 and page.get_by_role('link',name='추가 공식 안내 화면 원본 크게 보기').count()==3)
    page.locator('.bank-guide-strip img').last.scroll_into_view_if_needed();page.wait_for_function("[...document.querySelectorAll('.bank-guide-strip img')].every(i=>i.complete&&i.naturalWidth>0)");check('additional guide images load original assets',True)
    page.set_viewport_size({'width':390,'height':844});check('expanded gallery does not overflow mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    page.goto(base+'/#bank-work/WGSS-UI-014E9CA936CF');page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('KR');check('provider age contradiction visible before using the example',page.locator('.bank-source-conflict').is_visible() and '만 17세 미만' in page.locator('#bank-country-results').inner_text())
    page.locator('#bank-country').select_option('HK');check('HK opening gallery not duplicated into new work IDs',page.locator('.bank-guide-image').count()==5 and '홍콩에 거주하는 18~75세' in page.locator('#bank-country-results').inner_text())
    page.goto(base+'/#bank-work/WGSS-UI-8C8F9954FAF2');page.locator('#bank-country').wait_for();page.locator('#bank-country').select_option('KR');check('available balance distinct from remaining deposit capacity','출금가능금액' in page.locator('.bank-benchmark h3').first.inner_text() and '남은 월 입금 한도는 현재 잔액과 다릅니다' in page.locator('#bank-country-results').inner_text())
    check('no uncaught JavaScript errors',not errors);browser.close()
 print(json.dumps({'bank_collection_browser':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:server.shutdown();server.server_close()
