"""Exercise the actual workspace/app.js admin route, without replacing UI functions."""
import asyncio, functools, http.server, json, pathlib, threading
from playwright.async_api import async_playwright
from review_ui_browser import make_fixtures
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path('/home/ubuntu/wgss-review-ui-check');OUT.mkdir(exist_ok=True)
ITEM={'id':'admin-navigation-fixture','kind':'screen','status':'pending','version':1,'title':'카카오뱅크 고객센터','createdAt':'2026-10-15T16:30:00Z','current':{'proposalType':'screen','text':'카카오뱅크 고객센터 쪽 화면','sourceUrl':'https://www.kakaobank.com/'},'files':[{'id':'nav-file-'+str(i),'role':'masked','sha256':'nav-sha-'+str(i),'createdAt':'2026-10-15T16:30:00Z'} for i in range(1,4)]}
APPROVED={**ITEM,'id':'approved-navigation-fixture','status':'approved','version':3,'updatedAt':'2026-10-22T16:30:00Z','files':[ITEM['files'][0],{'id':'never-show-original','role':'original'}]}
async def run():
 make_fixtures()
 checks=[];errors=[];calls=[]
 def ck(name,value):
  if not value:raise AssertionError(name)
  checks.append(name);print(name,flush=True)
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,path):
   if path.split('?',1)[0].startswith('/workspace/'):
    suffix=path.split('?',1)[0].removeprefix('/workspace/') or 'index.html'
    return str(ROOT/'integration-ui'/suffix)
   return super().translate_path(path)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 async def api_route(route):
  import urllib.parse
  request=route.request;query=urllib.parse.parse_qs(urllib.parse.urlparse(request.url).query);resource=query.get('resource',[''])[0];calls.append(resource or 'POST')
  if resource=='file':
   await route.fulfill(path=str(OUT/'photo-1.png'),content_type='image/png');return
  if request.method=='POST':
   body=request.post_data_json
   if body['action']=='prepareReviewDraft':
    response={'status':'completed','sourceVersion':1,'files':[{'fileId':f['id'],'sha256':f['sha256']} for f in ITEM['files']],'draft':{'providerId':'kakao','language':'ko','taskId':'inquiry','screens':[{'fileId':f['id'],'title':'고객센터 '+str(i),'language':'ko','taskId':'inquiry','purpose':'문의할 항목을 선택합니다.','ocrPhrases':[{'text':'고객센터','role':'heading'}]} for i,f in enumerate(ITEM['files'],1)]}}
   else:response={}
  else:
   response={'session':None}
   if resource=='session':response={'role':'admin','adminConfigured':True}
   elif resource=='submissions':response={'items':[ITEM,APPROVED]}
   elif resource=='audit':response={'items':[{'id':'audit-1','action':'자료 승인','actorId':'검토자','entityId':'fixture','createdAt':'2026-10-15T16:30:00Z','details':{'내용':'검토 완료'}}]}
   elif resource=='publications':response={'items':[]}
   else:response={'items':[]}
  await route.fulfill(json=response)
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True,args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1280,'height':950});page.on('pageerror',lambda e:errors.append(str(e)));await page.route('**/api/wgss*',api_route)
   await page.goto(f'http://127.0.0.1:{server.server_port}/workspace/#admin');await page.wait_for_selector('[data-review="admin-navigation-fixture"]')
   ck('actual app.js defaults to proposal review',await page.evaluate('state.adminTab')=='inbox' and await page.locator('[data-admin-tab="inbox"]').get_attribute('aria-selected')=='true')
   ck('only three requested admin menus',await page.locator('[data-admin-tab]').all_text_contents()==['제안 검토','자료 목록','변경 이력'])
   ck('approved item offers history instead of another review',await page.locator('[data-review="approved-navigation-fixture"]').count()==0 and await page.locator('[data-approved-review="approved-navigation-fixture"]').inner_text()=='승인 내역 보기')
   before=calls.count('POST');await page.locator('[data-approved-review="approved-navigation-fixture"]').click()
   ck('approved detail is read-only with safe attachments',await page.locator('#dialog-title').inner_text()=='승인 내역' and await page.locator('#review-form').count()==0 and await page.locator('.approved-photos img').count()==1 and 'never-show-original' not in await page.locator('#dialog-content').inner_html())
   await page.locator('[data-versions]').click();await page.wait_for_function("document.querySelector('#version-history')?.textContent.includes('저장된 버전이 없습니다')")
   ck('approved history uses read API without AI or a second decision',calls.count('POST')==before and 'versions' in calls)
   await page.evaluate("WGSSReview.open(state.adminItems.find(x=>x.status==='approved'))")
   ck('direct review entry also keeps approved items read-only',await page.locator('#review-form').count()==0 and calls.count('POST')==before)
   await page.evaluate("openReview('approved-navigation-fixture')")
   ck('stale review button cannot reopen approval form',await page.locator('#review-form').count()==0 and calls.count('POST')==before)
   await page.locator('[data-close]').click()
   await page.locator('[data-admin-tab="inventory"]').click();await page.wait_for_selector('[data-screen]')
   ck('inventory menu renders existing real catalog records',await page.locator('#admin-panel h2').inner_text()=='현재 레퍼런스 목록' and await page.locator('#admin-panel [data-screen]').count()>0)
   await page.locator('[data-admin-tab="audit"]').click();await page.wait_for_function("document.querySelector('#admin-panel h2')?.textContent==='변경 이력'")
   ck('change history loads audit API',await page.locator('#admin-panel h2').inner_text()=='변경 이력' and 'audit' in calls)
   await page.locator('[data-admin-tab="inbox"]').click();await page.wait_for_selector('[data-review="admin-navigation-fixture"]');await page.locator('[data-review="admin-navigation-fixture"]').click()
   await page.wait_for_function("document.querySelector('#review-ai-message')?.textContent.includes('채웠습니다')")
   ck('real app review button opens new dialog',await page.locator('#dialog-title').inner_text()=='자료 검토' and await page.locator('[data-photo]').count()==3)
   ck('real app connects AI recommendation to all photo inputs',await page.locator('[data-photo="nav-file-2"] [data-review-field="title"]').input_value()=='고객센터 2' and await page.locator('[data-photo="nav-file-3"] [data-review-field="providerId"]').input_value()=='kakao')
   await page.locator('[data-close]').click();await page.wait_for_timeout(100);await page.locator('[data-admin-tab="inbox"]').focus();await page.keyboard.press('End');await page.wait_for_function("state.adminTab==='audit'")
   ck('three-menu keyboard navigation still works',await page.locator('[data-admin-tab="audit"]').get_attribute('aria-selected')=='true')
   ck('no hidden legacy admin API calls',not any(call in calls for call in ['jobs','settings','governance']))
   await page.screenshot(path=str(OUT/'admin-three-menus.png'),full_page=True)
   await page.evaluate("state.adminTab='inbox';window.WGSSPublic={config:{intakeBase:'https://wgss-public-intake.booknfoto461.chatgpt.site'},fetchJSON:async(url,options={})=>{const response=await fetch(url,options);return response.json()}};renderAdmin()")
   await page.wait_for_selector('[data-review="admin-navigation-fixture"]')
   ck('public admin route keeps the three inline menus without login',await page.locator('[data-admin-tab]').all_text_contents()==['제안 검토','자료 목록','변경 이력'] and await page.locator('#app a[href*="signin"]').count()==0)
   ck('no JavaScript errors with actual sources',not errors)
   await browser.close()
 finally:server.shutdown()
 report={'passed':len(checks),'checks':checks,'errors':errors,'calls':calls};(OUT/'admin-navigation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':asyncio.run(run())
