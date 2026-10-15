"""Native workspace contribution flow against capability-enforcing API fixtures.
No deployed service is contacted; all create/upload/delete requests stay local.
"""
import asyncio,functools,http.server,json,pathlib,re,threading,urllib.parse
from playwright.async_api import async_playwright
from review_ui_browser import make_fixtures
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=pathlib.Path('/home/ubuntu/wgss-review-ui-check')
async def run():
 make_fixtures();checks=[];errors=[];records={};requests=[];lose_create=True;lose_upload=True
 def ck(name,value):
  if not value:raise AssertionError(name)
  checks.append(name);print(name,flush=True)
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,path):
   if path.split('?',1)[0].startswith('/workspace/'):
    suffix=path.split('?',1)[0].removeprefix('/workspace/') or 'index.html';return str(ROOT/'integration-ui'/suffix)
   return super().translate_path(path)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 async def route_api(route):
  nonlocal lose_create,lose_upload
  request=route.request;headers=await request.all_headers();token=headers.get('x-wgss-contribution-token');query=urllib.parse.parse_qs(urllib.parse.urlparse(request.url).query);resource=query.get('resource',['session'])[0]
  if request.method=='GET':
   requests.append({'action':'GET '+resource,'token':token,'cookie':headers.get('cookie','')})
   if resource=='session':response={'role':'anonymous','userId':None,'publicIntake':True}
   elif resource=='submissions':
    if not token:return await route.fulfill(status=401,json={'error':'제안 확인 정보가 필요합니다.'})
    response={'items':[record['item'] for key,record in records.items() if key==token]}
   else:response={'items':[]}
   return await route.fulfill(json=response)
  content=headers.get('content-type','')
  if content.startswith('multipart/form-data'):
   raw=request.post_data_buffer.decode('latin1');action='upload'
   def field(name):
    match=re.search('name="'+name+'"\\r\\n\\r\\n([^\\r]*)',raw);return match.group(1) if match else ''
   client_id=field('clientUploadId');sid=field('submissionId');role=field('role')
  else:
   body=request.post_data_json;action=body['action'];client_id='';sid=body.get('id') or body.get('submissionId');role=''
  requests.append({'action':action,'token':token,'clientId':client_id,'cookie':headers.get('cookie','')})
  if action in ['prepareReviewDraft','reviewSubmission']:
   return await route.fulfill(json={'adminCookiePreserved':'native_session=admin-fixture' in headers.get('cookie',''),'hasContributionToken':bool(token)})
  if not token or not re.fullmatch('[0-9a-f]{64}',token):return await route.fulfill(status=401,json={'error':'제안 확인 정보가 필요합니다. 화면을 새로 열어 다시 시도해 주세요.'})
  if action=='createSubmission':
   if token not in records:records[token]={'item':{'id':'fixture-'+str(len(records)+1),'version':1,'status':'pending'},'uploads':{}}
   if lose_create:lose_create=False;return await route.abort('failed')
   return await route.fulfill(json={'item':records[token]['item']})
  if action=='upload':
   if token not in records or records[token]['item']['id']!=sid:return await route.fulfill(status=403,json={'error':'다른 제안입니다.'})
   if role!='masked':return await route.fulfill(status=400,json={'error':'마스킹 사진만 받습니다.'})
   records[token]['uploads'][client_id]=sid
   if len(records[token]['uploads'])==2 and lose_upload:lose_upload=False;return await route.abort('failed')
   return await route.fulfill(json={'item':records[token]['item']})
  if action in ['deleteOwn','deleteSubmission']:
   if token not in records or records[token]['item']['id']!=sid:return await route.fulfill(status=403,json={'error':'다른 제안입니다.'})
   del records[token];return await route.fulfill(json={'deleted':True})
  return await route.fulfill(status=403,json={'error':'권한이 없습니다.'})
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True,args=['--no-sandbox']);context=await browser.new_context(viewport={'width':1280,'height':1000});page=await context.new_page();page.on('pageerror',lambda error:errors.append(str(error)));await page.route('**/api/wgss*',route_api)
   base=f'http://127.0.0.1:{server.server_port}';await page.goto(base+'/workspace/#contribute');await page.wait_for_selector('#contribution-form');ck('actual native app runs without Pages adapter',not await page.evaluate('Boolean(window.WGSSPublic)'))
   await page.locator('#contribution-text').fill('카카오뱅크 고객센터 쪽 화면');await page.locator('#capture-file').set_input_files([str(OUT/('photo-'+str(i)+'.png')) for i in [1,2,3]]);await page.wait_for_selector('#mask-editor:not([hidden])');await page.locator('[name=safeTextConfirmed]').check();await page.locator('#submit-contribution').click();await page.wait_for_function("document.querySelector('#contribution-status').className==='error'")
   ck('native create includes secure 256-bit proof',len(records)==1 and any(re.fullmatch('[0-9a-f]{64}',request['token'] or '') for request in requests if request['action']=='createSubmission'))
   first_token=next(iter(records));ck('lost create response retains description and three photos',await page.locator('#contribution-text').input_value()=='카카오뱅크 고객센터 쪽 화면' and await page.locator('#capture-list img').count()==3)
   await page.locator('#submit-contribution').click();await page.wait_for_function("document.querySelector('#submit-contribution').textContent==='이어서 보내기'")
   ck('retry reuses same draft instead of duplicate submission',len(records)==1 and all(request['token']==first_token for request in requests if request['action']=='createSubmission'))
   ck('lost upload response preserves stable upload identity',len(records[first_token]['uploads'])==2)
   await page.locator('#submit-contribution').click();await page.wait_for_function("document.querySelector('#contribution-status').textContent.startsWith('접수되었습니다')")
   uploads=[request for request in requests if request['action']=='upload'];ck('three photos complete with retry-safe masked uploads',len(records[first_token]['uploads'])==3 and all(request['token']==first_token for request in uploads) and len(uploads)==4)
   ck('completion tells user about human review','담당자가 검토한 뒤 게시합니다' in await page.locator('#contribution-status').inner_text())
   await page.evaluate('renderContribution()');ck('completed form rerender does not rotate proof or clear receipt',await page.locator('#submit-contribution').inner_text()=='새 자료 보내기' and await page.evaluate('nativeContributionToken')==first_token)
   own=await page.evaluate("api('submissions')");ck('own-status lookup uses the same draft proof',len(own['items'])==1 and requests[-1]['token']==first_token)
   deleted=await page.evaluate("post('deleteOwn',{id:contributionDraft.id,expectedVersion:1})");ck('pending rollback uses original proof',deleted['deleted'] and first_token not in records and requests[-1]['token']==first_token)
   await page.locator('#submit-contribution').click();ck('explicit new draft rotates proof',await page.evaluate('nativeContributionToken')!=first_token and await page.locator('#contribution-text').input_value()=='')
   second_token=await page.evaluate('nativeContributionToken');await page.locator('#contribution-text').fill('새 제안');await page.locator('[name=safeTextConfirmed]').check();await page.locator('#submit-contribution').click();await page.wait_for_function("document.querySelector('#contribution-status').textContent.startsWith('접수되었습니다')");ck('new draft uses new secure proof',second_token in records and len(records)==1)
   await context.add_cookies([{'name':'native_session','value':'admin-fixture','url':base,'httpOnly':True,'sameSite':'Lax'}]);await page.evaluate("state.session={role:'admin'}")
   admin=await page.evaluate("post('prepareReviewDraft',{submissionId:'admin-fixture'})");ck('admin AI keeps native cookie and receives no draft capability',admin['adminCookiePreserved'] and not admin['hasContributionToken'])
   await page.evaluate("post('reviewSubmission',{id:'admin-fixture',decision:'held'})");ck('admin review receives no contribution capability',requests[-1]['action']=='reviewSubmission' and not requests[-1]['token'])
   await page.evaluate("api('session')");ck('session requests never leak draft capability',requests[-1]['action']=='GET session' and not requests[-1]['token'])
   ck('no uncaught JavaScript errors',not errors);await page.screenshot(path=str(OUT/'native-contribution-success.png'),full_page=True);await browser.close()
 finally:server.shutdown()
 result={'passed':len(checks),'checks':checks,'errors':errors,'createRequests':sum(r['action']=='createSubmission' for r in requests),'uploadRequests':sum(r['action']=='upload' for r in requests),'source':'actual integration-ui/app.js, local capability-enforcing API fixtures; no live writes'};(OUT/'native-contribution-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':asyncio.run(run())
