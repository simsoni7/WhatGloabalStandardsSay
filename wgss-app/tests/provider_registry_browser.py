"""A reviewer can register a missing service without losing their photo edits."""
import asyncio,functools,http.server,json,pathlib,threading
from playwright.async_api import async_playwright
from review_ui_browser import make_fixtures
from admin_navigation_browser import ITEM
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path('/home/ubuntu/wgss-providers-20261023/qa');OUT.mkdir(parents=True,exist_ok=True)
async def main():
 make_fixtures();checks=[];errors=[];created=[];registered=[];recommendations=0
 item={**ITEM,'status':'held','current':{'proposalType':'screen','text':'Example Wallet 화면입니다.'}}
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
  def translate_path(self,path):
   if path.split('?',1)[0].startswith('/workspace/'):
    return str(ROOT/'integration-ui'/(path.split('?',1)[0].removeprefix('/workspace/') or 'index.html'))
   return super().translate_path(path)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 def ck(name,value):
  assert value,name
  checks.append(name);print(name,flush=True)
 async def route_api(route):
  nonlocal recommendations
  from urllib.parse import urlsplit,parse_qs
  q=parse_qs(urlsplit(route.request.url).query);resource=q.get('resource',[''])[0]
  if route.request.method=='POST':
   data=route.request.post_data_json
   if data['action']=='createProvider':
    created.append(data);row={'id':'registered-example-wallet','name':data['name'],'kind':data['kind'],'aliases':data['aliases'],'sourceUrl':data['sourceUrl'],'origin':'registered'};registered[:]=[row];response={'item':row,'reused':False}
   elif data['action']=='prepareReviewDraft':
    recommendations+=1
    response={'status':'completed','sourceVersion':item['version'],'files':[{'fileId':f['id'],'sha256':f['sha256']} for f in item['files']],'draft':{'providerName':'Example Wallet','providerId':'citi' if recommendations>1 else '', 'screens':[{'fileId':f['id'],'title':'Wallet photo '+str(n),'language':'en','taskId':'signup','purpose':'지갑 화면을 확인합니다.','ocrPhrases':[{'text':'Wallet','role':'heading'}]} for n,f in enumerate(item['files'],1)]}}
   else:raise AssertionError('Unexpected write '+data['action'])
  elif resource=='file':await route.fulfill(path='/home/ubuntu/wgss-review-ui-check/photo-1.png',content_type='image/png');return
  elif resource=='session':response={'role':'admin','publicReview':True}
  elif resource=='submissions':response={'items':[item]}
  elif resource=='publications':response={'items':[],'providers':registered}
  else:response={'items':[]}
  await route.fulfill(json=response)
 try:
  async with async_playwright() as p:
   b=await p.chromium.launch();page=await b.new_page(viewport={'width':1280,'height':950});page.on('pageerror',lambda e:errors.append(str(e)));await page.route('**/api/wgss*',route_api)
   url=f'http://127.0.0.1:{server.server_port}/workspace/#admin'
   await page.goto(url);await page.locator('[data-review]').click();await page.wait_for_function('document.querySelector("#review-ai-message").textContent.includes("채웠습니다")')
   first=page.locator('[data-photo]').first
   ck('unknown model provider is shown as a registration suggestion', 'Example Wallet' in await first.locator('[data-provider-suggestion]').inner_text() and await first.locator('[data-review-field="providerId"]').input_value()=='')
   await first.locator('[data-review-field="title"]').fill('직접 확인한 제목')
   await first.locator('summary').click();await first.locator('[data-new-provider="kind"]').select_option('wallet');await first.locator('[data-new-provider="aliases"]').fill('예시지갑');await first.locator('[data-new-provider="sourceUrl"]').fill('https://example.test/')
   await first.locator('[data-register-provider]').click();await page.wait_for_function('document.querySelector("[data-review-field=providerId]").value==="registered-example-wallet"')
   ck('registration is a separate action rather than approval',len(created)==1 and created[0]['name']=='Example Wallet' and created[0]['kind']=='wallet')
   ck('registration selects the new service without discarding title edits',await first.locator('[data-review-field="title"]').input_value()=='직접 확인한 제목')
   ck('other photo selectors gain the new option',await page.locator('[data-review-field="providerId"] option[value="registered-example-wallet"]').count()==3)
   await page.locator('#review-ai-retry').click();await page.wait_for_timeout(200)
   ck('later AI advice cannot replace the manually selected service',await first.locator('[data-review-field="providerId"]').input_value()=='registered-example-wallet' and await first.locator('[data-review-field="title"]').input_value()=='직접 확인한 제목')
   plan=await page.evaluate('WGSSReview.application(document.querySelector("#review-form"))')
   ck('the approval payload carries the new ID for the correct photo',plan['photos'][0]['fields']['providerId']=='registered-example-wallet' and all(x['fields']['providerId']=='citi' for x in plan['photos'][1:]))
   await page.set_viewport_size({'width':390,'height':844});ck('provider registration fits the mobile review dialog',await page.evaluate('document.documentElement.scrollWidth<=innerWidth&&document.querySelector("#detail-dialog").scrollWidth<=document.querySelector("#detail-dialog").clientWidth+1'))
   await page.screenshot(path=str(OUT/'mobile-new-provider.png'))
   await page.reload();await page.locator('[data-review]').wait_for();await page.locator('[data-review]').click();await page.wait_for_function('document.querySelector("#review-ai-message").textContent.includes("채웠습니다")')
   ck('registered service survives page reload through the shared catalogue',await page.evaluate('state.catalog.providers.some(p=>p.id==="registered-example-wallet")'))
   await page.locator('[data-close]').click();await page.locator('[data-nav="screens"]').click();await page.locator('#provider').wait_for()
   ck('new service is also selectable in public reference search',await page.locator('#provider option[value="registered-example-wallet"]').count()==1)
   ck('no browser exceptions',not errors);await b.close()
 finally:server.shutdown();server.server_close()
 report={'passed':len(checks),'checks':checks,'errors':errors};(OUT/'providers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
