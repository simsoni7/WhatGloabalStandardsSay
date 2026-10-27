import asyncio,json,urllib.request,urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
import os
root=Path(os.environ.get('WGSS_TEST_EXPORT','/tmp/wgss-public'));base='https://wgss-public-intake.booknfoto461.chatgpt.site/api/wgss'
async def main():
 async with async_playwright() as pw:
  browser=await pw.chromium.launch(headless=True,args=['--no-sandbox']);p=await browser.new_page(viewport={'width':773,'height':704});writes=[];errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  async def assets(route):
   path=urllib.parse.urlsplit(route.request.url).path.split('/WhatGloabalStandardsSay/wgss/',1)[-1]
   await route.fulfill(path=str(root/path))
  await p.route('http://127.0.0.1:8778/WhatGloabalStandardsSay/wgss/**',assets)
  async def api(route):
   req=route.request
   if req.method=='OPTIONS':return await route.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'Content-Type','Access-Control-Allow-Methods':'GET,POST'})
   if req.method=='POST':
    data=req.post_data_json
    if data.get('action')=='prepareReviewDraft':return await route.fulfill(json={'status':'failed','error':'테스트 중 모델 요청 생략'},headers={'Access-Control-Allow-Origin':'*'})
    writes.append(data);return await route.fulfill(status=400,json={'error':'테스트: 서버 검증 실패도 이 창에 표시됩니다.'},headers={'Access-Control-Allow-Origin':'*'})
   url=base+'?'+urllib.parse.urlsplit(req.url).query
   raw=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Origin':'https://3.36.58.188'})).read()
   await route.fulfill(body=raw,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'})
  await p.route('**/api/wgss*',api)
  await p.goto(__import__('os').environ.get('WGSS_TEST_URL','http://127.0.0.1:8778/#admin'));await p.wait_for_function('state.adminItems.length>0')
  await p.evaluate("WGSSReview.open(state.adminItems.find(x=>['pending','held'].includes(x.status)&&x.current.proposalType==='term'))")
  await p.locator('#apply-english').wait_for();await p.locator('button[value=approved]').click()
  await p.locator('#review-submit-error').wait_for(state='visible');msg=await p.locator('#review-submit-error').inner_text();assert '2개' in msg;assert not writes
  await p.check('[name=privacyReviewed]');await p.check('[name=readabilityReviewed]');await p.locator('button[value=approved]').click();assert '상업 이용' in await p.locator('#review-submit-error').inner_text();assert not writes
  await p.select_option('#apply-rights-license','Unicode-3.0');await p.fill('#apply-rights-url','https://www.unicode.org/license.txt');await p.fill('#apply-rights-basis','공식 언어팩의 원문과 이용 조건을 확인했습니다.');await p.check('#apply-rights-confirmed');await p.locator('button[value=approved]').click();await p.wait_for_function("document.querySelector('#review-submit-error').textContent.includes('서버 검증')")
  assert len(writes)==1;assert not await p.locator('button[value=approved]').is_disabled()
  assert not errors,errors
  print(json.dumps({'visibleValidation':True,'rightsValidation':True,'serverErrorVisible':True,'buttonReenabled':True,'interceptedApprovalRequests':len(writes),'realWrites':0,'errors':errors},ensure_ascii=False));await browser.close()
asyncio.run(main())
