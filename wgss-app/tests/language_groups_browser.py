"""Language groups include source locales without rewriting source records."""
import asyncio,functools,http.server,json,os,pathlib,threading
from urllib.parse import urlsplit,parse_qs
from playwright.async_api import async_playwright
from admin_navigation_browser import ITEM
from review_ui_browser import make_fixtures
ROOT=pathlib.Path(os.environ.get('WGSS_UI_EXPORT','/home/ubuntu/wgss-languages-20261023/export'))
OUT=pathlib.Path('/home/ubuntu/wgss-languages-20261023/qa');OUT.mkdir(parents=True,exist_ok=True)
BASE='/WhatGloabalStandardsSay/wgss/'
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def copyfile(self,source,outputfile):
  try:super().copyfile(source,outputfile)
  except (BrokenPipeError,ConnectionResetError):pass
 def translate_path(self,path):return str(ROOT/(urlsplit(path).path.removeprefix(BASE).lstrip('/') or 'index.html'))
async def main():
 make_fixtures();catalog=json.loads((ROOT/'integration-data/catalog.json').read_text());checks=[];errors=[]
 # Synthetic locale observations complement the real public dictionary chunks.
 origin=next(r for r in catalog['screens'] if r['providerId']=='citi')
 for suffix,language in [('ko','ko-KR'),('en','en-GB'),('mixed','en / zh-Hant')]:catalog['screens'].append({**origin,'id':'locale-fixture-'+suffix,'language':language})
 catalog['languages'] += [{'id':'ko_KR','label':'ko_KR'},{'id':'en-US','label':'en-US'}]
 item={**ITEM,'current':{**ITEM['current'],'language':'ko-KR'}}
 def ck(name,value):
  assert value,name
  checks.append(name);print(name,flush=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'+BASE
 try:
  async with async_playwright() as p:
   b=await p.chromium.launch();page=await b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
   async def route(route):
    req=route.request;q=parse_qs(urlsplit(req.url).query);resource=q.get('resource',[''])[0]
    if req.url.split('?',1)[0].endswith('/integration-data/catalog.json'):await route.fulfill(json=catalog);return
    if '/api/wgss' not in req.url:await route.continue_();return
    if req.method=='POST':
     assert req.post_data_json['action']=='prepareReviewDraft'
     await route.fulfill(json={'status':'completed','sourceVersion':1,'files':[{'fileId':f['id'],'sha256':f['sha256']} for f in item['files']],'draft':{'providerId':'citi','screens':[{'fileId':f['id'],'title':'Locale check','language':'en-GB','taskId':'signup','ocrPhrases':[]} for f in item['files']]}});return
    if resource=='file':await route.fulfill(path='/home/ubuntu/wgss-review-ui-check/photo-1.png',content_type='image/png');return
    await route.fulfill(json={'role':'admin','publicReview':True} if resource=='session' else {'items':[item]} if resource=='submissions' else {'items':[],'providers':[]})
   await page.route('**/*',route)
   async def go(tail):
    await page.goto(base+tail,wait_until='domcontentloaded');await page.wait_for_function('typeof state!=="undefined"&&state.catalog&&document.querySelector("#app h1")')
   await go('?language=ko-KR#screens')
   ck('Korean and English have one named option each',await page.locator('#language option').evaluate_all('els=>els.filter(e=>e.textContent==="한국어").length===1&&els.filter(e=>e.textContent==="영어").length===1'))
   ck('region and mixed-code duplicates are absent from the selector',await page.locator('#language option').evaluate_all('els=>!els.some(e=>["ko-KR","ko_KR","en-GB","en-US","pt-BR","zh-Hant-HK","en / zh-Hant"].includes(e.value))'))
   ck('old locale links resolve to the selected Korean group',await page.locator('#language').input_value()=='ko' and 'language=ko&' in page.url)
   ck('Korean filter includes the original ko-KR observation',await page.evaluate('state.catalog.screens.filter(matchesCommon).some(r=>r.id==="locale-fixture-ko")'))
   await page.locator('#language').select_option('en')
   ck('English filter includes regional and bilingual observations',await page.evaluate('["locale-fixture-en","locale-fixture-mixed"].every(id=>state.catalog.screens.filter(matchesCommon).some(r=>r.id===id))'))
   await page.locator('#language').select_option('zh-Hant')
   ck('bilingual screen is also available under its Chinese group',await page.evaluate('state.catalog.screens.filter(matchesCommon).some(r=>r.id==="locale-fixture-mixed")'))
   ck('Simplified and Traditional Chinese remain distinct',await page.locator('#language option[value="zh-Hans"]').count()==1 and await page.locator('#language option[value="zh-Hant"]').count()==1)
   ck('Tagalog retains the source code and name used by approval validation',await page.evaluate('WGSSLanguages.filter("tl")=="tl"&&labelFor("languages","tl")=="타갈로그어"&&state.catalog.languages.some(x=>x.id==="tl")&&!state.catalog.languages.some(x=>x.id==="fil")'))
   ck('country code kr is not guessed to mean Korean',await page.evaluate('WGSSLanguages.filter("kr")!=="ko"'))
   ck('source locale tags remain unchanged',await page.evaluate('state.catalog.screens.find(r=>r.id==="locale-fixture-ko").language==="ko-KR"&&state.catalog.screens.find(r=>r.id==="locale-fixture-mixed").language==="en / zh-Hant"'))
   await page.locator('#language').select_option('en');await page.locator('#provider').select_option('citi');await page.locator('[data-tab="features"]').click()
   for button in await page.locator('[data-feature-more]:visible').all():await button.click()
   ck('company grid uses the same locale matcher',await page.locator('[data-feature-screen="locale-fixture-en"]:visible').count()>0)
   await go('?tab=words&wordMode=terms&language=pt#screens');await page.wait_for_function('!state.loadingTerms',timeout=120000)
   ck('Portuguese search loads base and Brazilian language chunks',await page.evaluate('WGSSDictionary.visibleRows().length===329&&WGSSDictionary.visibleRows().some(r=>r.language==="pt")&&WGSSDictionary.visibleRows().some(r=>r.language==="pt-BR")'))
   ck('regional detail remains readable without a second filter category',await page.evaluate('labelFor("languages","pt-BR").includes("브라질")&&state.catalog.languages.filter(x=>x.id==="pt").length===1'))
   await go('?tab=words&wordMode=terms&language=tl#screens');await page.wait_for_function('!state.loadingTerms',timeout=120000)
   ck('Tagalog search loads all existing source rows',await page.evaluate('WGSSDictionary.visibleRows().length===1647&&WGSSDictionary.visibleRows().every(r=>r.language==="tl")'))
   metrics=await page.evaluate('(()=>{const m=WGSSAbout.metrics(state.catalog,state.terms);return {pairs:m.dictionaryRows,pt:m.languageCounts.get("pt"),total:[...m.languageCounts.values()].reduce((a,b)=>a+b,0),groups:m.languageCount}})()')
   ck('grouped introduction totals preserve every dictionary pair',metrics['pairs']==21188 and metrics['total']==21188 and metrics['pt']==329 and metrics['groups']==35)
   await page.set_viewport_size({'width':390,'height':844});ck('language filters fit mobile width',await page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   await page.screenshot(path=str(OUT/'language-filter-mobile.png'))
   await go('#admin');await page.locator('[data-review]').click();await page.wait_for_function('document.querySelector("#review-ai-message").textContent.includes("채웠습니다")')
   ck('regional AI language suggestions select the canonical review option',await page.locator('[data-review-field="language"]').evaluate_all('els=>els.length===3&&els.every(e=>e.value==="en")'))
   await page.locator('[data-close]').click();await page.locator('[data-admin-tab="inventory"]').click();await page.locator('[data-inventory-type="terms"]').click();await page.wait_for_function('!state.loadingTerms&&state.terms.length>=21188',timeout=120000);await page.locator('#inventory-language').select_option('pt')
   ck('management uses the same combined Portuguese group',await page.evaluate('inventoryRows().length===329'))
   ck('no uncaught JavaScript errors',not errors);await b.close()
 finally:server.shutdown();server.server_close()
 report={'passed':len(checks),'checks':checks,'metrics':metrics,'errors':errors};(OUT/'languages.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':asyncio.run(main())
