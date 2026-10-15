"""Use the actual generated Pages bundle with public curation API fixtures.
Pass the generated build directory as argv[1]. All mutations are local fixtures.
"""
import asyncio,functools,http.server,json,pathlib,re,sys,threading,urllib.parse
from playwright.async_api import async_playwright
from review_ui_browser import make_fixtures
OUT=pathlib.Path('/home/ubuntu/wgss-review-ui-check');ROOT=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/home/ubuntu/wgss-public-review-browser-fixture');BASE='/WhatGloabalStandardsSay/wgss/';CENTRAL='https://wgss-public-intake.booknfoto461.chatgpt.site'
ITEM={'id':'public-review-fixture','kind':'screen','status':'pending','version':4,'title':'카카오뱅크 고객센터','createdAt':'2026-10-15T16:30:00Z','current':{'proposalType':'screen','text':'카카오뱅크 고객센터 쪽 화면','sourceUrl':'https://www.kakaobank.com/'},'files':[{'id':'public-photo-'+str(i),'role':'masked','sha256':'sha-'+str(i),'createdAt':'2026-10-15T16:30:00Z'} for i in [1,2,3]]}
async def run():
 make_fixtures();checks=[];errors=[];calls=[];contributions={};reviews=[];public_enabled=True;fail_upload=True
 def ck(name,value):
  if not value:raise AssertionError(name)
  checks.append(name);print(name,flush=True)
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,path):
   p=urllib.parse.urlparse(path).path
   if p.startswith(BASE):return str(ROOT/(p.removeprefix(BASE) or 'index.html'))
   return str(ROOT/'missing')
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 async def api_route(route):
  nonlocal fail_upload
  request=route.request;headers=await request.all_headers();token=headers.get('x-wgss-contribution-token');query=urllib.parse.parse_qs(urllib.parse.urlparse(request.url).query);resource=query.get('resource',['session'])[0];cors={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type,X-WGSS-Contribution-Token'}
  async def reply(value,status=200):return await route.fulfill(json=value,status=status,headers=cors)
  if request.method=='OPTIONS':return await route.fulfill(status=204,headers=cors)
  if request.method=='GET':
   calls.append({'method':'GET','resource':resource,'url':request.url,'token':token})
   if resource=='file':return await route.fulfill(path=str(OUT/'photo-1.png'),content_type='image/png',headers=cors)
   if resource=='session':return await reply({'role':'admin' if public_enabled else 'anonymous','publicReview':public_enabled,'userId':'public-reviewer:fixture' if public_enabled else None})
   if resource=='submissions':return await reply({'items':[ITEM]+[value['item'] for value in contributions.values()]})
   if resource=='audit':return await reply({'items':[]})
   return await reply({'items':[]})
  if headers.get('content-type','').startswith('multipart/form-data'):
   raw=request.post_data_buffer.decode('latin1');action='upload'
   def field(name):
    match=re.search('name="'+name+'"\\r\\n\\r\\n([^\\r]*)',raw);return match.group(1) if match else ''
   body={'action':action,'submissionId':field('submissionId'),'role':field('role'),'clientUploadId':field('clientUploadId')}
  else:body=request.post_data_json;action=body['action']
  calls.append({'method':'POST','action':action,'token':token,'url':request.url})
  if action in ['createSubmission','upload','deleteOwn']:
   if not token or not re.fullmatch('[0-9a-f]{64}',token):return await reply({'error':'제안 확인 정보가 필요합니다.'},401)
   if action=='createSubmission':
    if token not in contributions:contributions[token]={'item':{'id':'public-contribution','version':1,'status':'pending','title':body['title']},'files':set()}
    return await reply({'item':contributions[token]['item']})
   if action=='upload':
    if token not in contributions:return await reply({'error':'다른 제안입니다.'},403)
    contributions[token]['files'].add(body['clientUploadId'])
    if fail_upload:fail_upload=False;return await route.abort('failed')
    return await reply({'item':contributions[token]['item']})
   if action=='deleteOwn':
    if token not in contributions:return await reply({'error':'다른 제안입니다.'},403)
    del contributions[token];return await reply({'deleted':True})
  if action=='prepareReviewDraft':return await reply({'status':'completed','sourceVersion':4,'files':[{'fileId':f['id'],'sha256':f['sha256']} for f in ITEM['files']],'draft':{'providerId':'kakao','language':'ko','taskId':'inquiry','screens':[{'fileId':f['id'],'title':'고객센터 '+str(i),'language':'ko','taskId':'inquiry','purpose':'문의 방법을 고릅니다.','ocrPhrases':[{'text':'문의하기','role':'button'}]} for i,f in enumerate(ITEM['files'],1)]}})
  if action=='reviewSubmission':reviews.append(body);return await reply({'item':{**ITEM,'status':body['decision'],'version':5}})
  return await reply({'error':'허용되지 않은 작업입니다.'},403)
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True,args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1280,'height':1000});page.on('pageerror',lambda error:errors.append(str(error)));await page.route(CENTRAL+'/api/wgss*',api_route)
   await page.goto(f'http://127.0.0.1:{server.server_port}'+BASE+'#admin');await page.wait_for_selector('[data-review="public-review-fixture"]')
   ck('generated public frontend fetches actual session and opens inline management',await page.evaluate('state.session.publicReview') and any(call.get('resource')=='session' for call in calls))
   ck('public management has exactly three tabs and no login',await page.locator('[data-admin-tab]').all_text_contents()==['제안 검토','자료 목록','변경 이력'] and await page.locator('#app a[href*="signin"]').count()==0)
   await page.locator('[data-nav="contribute"]').click();await page.locator('#contribution-text').fill('합성 제안 테스트');await page.locator('#capture-file').set_input_files([str(OUT/('photo-'+str(i)+'.png')) for i in [1,2,3]]);await page.wait_for_selector('#mask-editor:not([hidden])');await page.locator('[name=safeTextConfirmed]').check();await page.locator('#submit-contribution').click();await page.wait_for_function("document.querySelector('#submit-contribution').textContent==='이어서 보내기'");await page.locator('#submit-contribution').click();await page.wait_for_function("document.querySelector('#contribution-status').textContent.startsWith('접수되었습니다')")
   proof=next(iter(contributions));ck('public contribution retains per-draft proof across upload retry',len(contributions)==1 and len(contributions[proof]['files'])==3 and all(call['token']==proof for call in calls if call.get('action') in ['createSubmission','upload']))
   await page.locator('[data-nav="admin"]').click();await page.wait_for_selector('[data-review="public-review-fixture"]');await page.locator('[data-review="public-review-fixture"]').click();await page.wait_for_function("document.querySelector('#review-ai-message')?.textContent.includes('채웠습니다')")
   ck('pending masked photos resolve to central service in public review',await page.locator('[data-photo] img').evaluate_all('(images)=>images.every(image=>image.src.startsWith("https://wgss-public-intake.booknfoto461.chatgpt.site/api/wgss?"))'))
   await page.wait_for_function("[...document.querySelectorAll('[data-photo] img')].every(image=>image.complete&&image.naturalWidth>0)");ck('cross-origin pending photo previews load',await page.locator('[data-photo] img').evaluate_all('(images)=>images.every(image=>image.naturalWidth===390)'))
   ck('AI review request carries no contribution capability',all(not call['token'] for call in calls if call.get('action')=='prepareReviewDraft'))
   await page.locator('[name=privacyReviewed]').check();await page.locator('[name=readabilityReviewed]').check();await page.locator('[name=decision][value=approved]').click();await page.wait_for_function('!document.querySelector("dialog").open');ck('public review posts all three independently titled photos',len(reviews)==1 and len(reviews[0]['application']['photos'])==3 and reviews[0]['application']['photos'][1]['fields']['title']=='고객센터 2')
   ck('approval request carries no contribution capability',all(not call['token'] for call in calls if call.get('action')=='reviewSubmission'))
   deleted=await page.evaluate("post('deleteOwn',{id:'public-contribution',expectedVersion:1})");ck('own contribution rollback still uses original proof',deleted['deleted'] and not contributions and calls[-1]['token']==proof)
   await page.locator('[data-admin-tab="inventory"]').click();await page.wait_for_function("document.querySelector('#admin-panel h2')?.textContent==='현재 레퍼런스 목록'");await page.locator('[data-admin-tab="audit"]').click();await page.wait_for_function("document.querySelector('#admin-panel h2')?.textContent==='변경 이력'");ck('public catalog and change-history tabs work',await page.locator('[data-admin-tab]').count()==3)
   ck('public browser never requests private settings or jobs',not any(call.get('resource') in ['settings','jobs','governance'] or call.get('action') in ['runAiJob','runMarketScan'] for call in calls))
   await page.screenshot(path=str(OUT/'public-review-three-tabs.png'),full_page=True);public_enabled=False;await page.evaluate('renderAdmin()');await page.wait_for_function("document.querySelector('#admin-content')?.textContent.includes('연결하지 못했습니다')");blocked_text=await page.locator('#app').inner_text();ck('disabled backend gives connection message without login prompt',not any(word in blocked_text for word in ['로그인','관리자 권한']))
   ck('no uncaught JavaScript errors',not errors);await browser.close()
 finally:server.shutdown()
 result={'passed':len(checks),'checks':checks,'errors':errors,'apiSessionRequests':sum(call.get('resource')=='session' for call in calls),'source':'actual generated Pages runtime and app, local API fixtures only'};(OUT/'public-review-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':asyncio.run(run())
