import asyncio,json,pathlib,io,os
from PIL import Image,ImageDraw
from playwright.async_api import async_playwright
O=pathlib.Path(os.environ.get('WGSS_QA_OUTPUT','/tmp/wgss-search-contribution-qa'));O.mkdir(parents=True,exist_ok=True);BASE=os.environ.get('WGSS_QA_BASE','http://127.0.0.1:5173');checks=[];errors=[]
def ck(label,value):
 if not value:raise AssertionError(label)
 checks.append(label);print(label,flush=True)
async def main():
 for n in [1,2]:
  img=Image.new('RGB',(160,120),'white' if n==1 else '#eeeeee');ImageDraw.Draw(img).text((5,5),'SYNTHETIC TEST',fill='red');img.save(O/f'photo{n}.png')
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True,args=['--no-sandbox']);p=await b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
  await p.goto(BASE+'/workspace/?tab=words&query=탈퇴&task=card-application#screens',wait_until='networkidle');await p.wait_for_function('state.catalog&&state.loadingTerms===false')
  ck('both phrase and dictionary sections visible by default',await p.locator('#company-phrases').count()==1 and await p.locator('#dictionary-results').count()==1)
  ck('stale task conflict explains eight hidden phrase contexts','8건' in await p.locator('.filter-conflict').inner_text())
  await p.locator('.filter-conflict [data-remove-filter="task"]').click();await p.wait_for_function('state.loadingTerms===false');ck('targeted task reset preserves search and reveals eight',await p.locator('[data-phrase-propose]').count()==6 and '8건' in await p.locator('#company-phrases').inner_text() and await p.locator('#query').input_value()=='탈퇴')
  ck('company phrases include actual thumbnail links',await p.locator('.phrase-thumbnail img').count()==6)
  await p.locator('#task').select_option('card-application');await p.locator('#query').fill('회원가입');await p.wait_for_timeout(400)
  ck('new query clears previous task visibly and in URL',await p.evaluate('state.task===""') and 'task=' not in p.url and await p.locator('#task').input_value()=='')
  ck('task dropdown excludes editorial affinity groups',await p.locator('#task option[value^="toss-v6:"]').count()==0)
  await p.locator('#task').select_option('card-close');await p.locator('#query').fill('');await p.wait_for_timeout(400);await p.locator('#task').select_option('card-close');await p.get_by_role('tab',name='화면과 흐름',exact=True).click()
  ck('common card closure task finds three real Toss screens',await p.locator('.screen-card').count()==3 and 'Toss' in await p.locator('#results').inner_text())
  await p.locator('.screen-card .screen-button').first.click();ck('navigation mapping not asserted as verified flow','검색용 연결' in await p.locator('#dialog-content').inner_text() and '실제 이동 순서는 확인되지' in await p.locator('#dialog-content').inner_text());await p.keyboard.press('Escape')
  await p.goto(BASE+'/workspace/?tab=words&query=interest#screens',wait_until='networkidle');await p.wait_for_function('state.loadingTerms===false');total=await p.evaluate('state.terms.filter(termMatches).length');ck('real matching dictionary rows loaded',total>0)
  await p.locator('#provider').select_option('citi');ck('company filter does not falsely filter dictionary',await p.evaluate('state.terms.filter(termMatches).length')==total)
  ck('dictionary filter scope stated in ordinary language','검색어와 언어 조건만 적용' in await p.locator('#dictionary-results').inner_text())
  if await p.locator('[data-term-page="2"]').count():
   await p.locator('[data-term-page="2"]').click();ck('dictionary pagination independent of phrase page',await p.evaluate('state.termPage===2&&state.page===1'))
  await p.goto(BASE+'/signin-with-chatgpt?return_to=/workspace/',wait_until='networkidle');await p.goto(BASE+'/workspace/#contribute',wait_until='networkidle')
  ck('contribution has only description source photo and one confirmation',await p.locator('#contribution-fields textarea').count()==1 and await p.locator('#contribution-fields input[type="url"]').count()==1 and await p.locator('#contribution-fields input[type="checkbox"]').count()==1 and await p.locator('#contribution-fields select').count()==0)
  ck('photos allow multiple selection',await p.locator('#capture-file').get_attribute('multiple') is not None)
  await p.locator('#contribution-text').fill('Browser batch capture acceptance check');await p.locator('#contribution-source').fill('https://example.com/reference')
  await p.locator('#capture-file').set_input_files([str(O/'photo1.png'),str(O/'photo2.png')]);await p.wait_for_function('captureFiles.length===2&&maskState?.item?.id===captureFiles[0].id')
  await p.get_by_text('키보드로 가림 영역 지정',exact=True).click()
  for k,v in {'x':0,'y':0,'w':40,'h':30}.items():await p.locator('#mask-'+k).fill(str(v))
  await p.get_by_role('button',name='영역 가리기',exact=True).click();await p.locator('[data-capture-edit]').nth(1).click();await p.wait_for_function('maskState?.item?.id===captureFiles[1].id');await p.locator('[data-capture-edit]').nth(0).click();await p.wait_for_function('maskState?.item?.id===captureFiles[0].id');ck('switching photos preserves each mask',await p.evaluate('captureFiles[0].rects.length===1&&captureFiles[1].rects.length===0'))
  await p.locator('[name="safeTextConfirmed"]').check();await p.screenshot(path=str(O/'contribute-desktop.png'),full_page=True)
  uploads=[];lost=False
  async def fault(route):
   nonlocal lost
   req=route.request
   if req.method=='POST' and 'multipart/form-data' in req.headers.get('content-type',''):
    uploads.append(req.post_data_buffer)
    if len(uploads)==2 and not lost:
     response=await route.fetch();ck('injected lost acknowledgement follows successful real second upload',response.status==200);lost=True;await route.abort('failed');return
   await route.continue_()
  await p.route('**/api/wgss',fault);await p.get_by_role('button',name='자료 보내기',exact=True).click();await p.get_by_role('button',name='이어서 보내기',exact=True).wait_for(timeout=30000);ck('partial upload offers resumable submission not duplicate form','1/2장' in await p.locator('#contribution-status').inner_text())
  ck('partial failure locks masks and source fields',await p.locator('#contribution-fields').evaluate('(el)=>el.disabled') and await p.evaluate('getComputedStyle(document.querySelector("#mask-canvas")).pointerEvents==="none"'));await p.get_by_role('button',name='이어서 보내기',exact=True).click();await p.wait_for_function('document.querySelector("#contribution-status").textContent.includes("접수되었습니다")',timeout=30000);await p.unroute('**/api/wgss',fault)
  item=await p.evaluate('contributionDraft.item');ck('lost acknowledgement retry stores one submission and exactly two files',len(item['files'])==2 and len(uploads)==3)
  ck('raw names never used in uploaded multipart',all(b'photo1.png' not in raw and b'photo2.png' not in raw for raw in uploads))
  for i,f in enumerate(item['files']):
   res=await p.request.get(BASE+'/api/wgss?resource=file&id='+f['id']);img=Image.open(io.BytesIO(await res.body())).convert('RGB');ck('stored image mask verified '+str(i+1),img.getpixel((2,2))==((0,0,0) if i==0 else (238,238,238)))
  ck('submission keeps description/source and leaves classification empty',item['current']['text']=='Browser batch capture acceptance check' and item['current']['sourceUrl']=='https://example.com/reference' and not item['current']['country'])
  await p.get_by_role('link',name='관리',exact=True).click();await p.get_by_role('button',name='개별 검토').first.click();await p.locator('#review-file').select_option([f['id'] for f in item['files']]);await p.locator('[name="privacyReviewed"]').check();await p.locator('[name="readabilityReviewed"]').check();await p.locator('#review-reason').fill('Two synthetic images checked independently');await p.locator('#apply-operation').select_option('add');await p.locator('#apply-providerId').select_option('citi');await p.locator('#apply-language').select_option('en');await p.locator('#apply-taskId').select_option('signup');await p.get_by_role('button',name='이 버전 승인',exact=True).click();await p.wait_for_function('!document.querySelector("#detail-dialog").open')
  current=await p.evaluate('async id=>(await (await fetch("/api/wgss?resource=submissions")).json()).items.find(r=>r.id===id)',item['id']);applied=await p.evaluate('async id=>(await (await fetch("/api/wgss?resource=publications")).json()).items.filter(r=>r.type==="screens"&&r.targetId.includes(id))',item['id']);ck('both exact reviewed images enter ordinary screen records',len(applied)==2 and all(r['patch']['imageFileId'] in [f['id'] for f in current['files']] for r in applied))
  await p.evaluate('async x=>{const r=await fetch("/api/wgss",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"deleteSubmission",id:x.id,expectedVersion:x.version})});if(!r.ok)throw Error(await r.text())}',current)
  await p.set_viewport_size({'width':390,'height':844});await p.goto(BASE+'/workspace/?tab=words&query=탈퇴#screens',wait_until='networkidle');await p.wait_for_function('state.loadingTerms===false');ck('combined word search fits mobile390',await p.evaluate('document.documentElement.scrollWidth<=390'));await p.locator('.phrase-thumbnail').first.scroll_into_view_if_needed();await p.wait_for_function('document.querySelector(".phrase-thumbnail img")?.naturalWidth>0');await p.screenshot(path=str(O/'words-mobile.png'),full_page=True)
  await p.get_by_role('link',name='자료 제안',exact=True).click();ck('simple contribution fits mobile390',await p.evaluate('document.documentElement.scrollWidth<=390'));await p.screenshot(path=str(O/'contribute-mobile.png'),full_page=True)
  ck('no unhandled browser errors',not errors);await b.close()
 (O/'browser-results.json').write_text(json.dumps({'checks':checks,'passed':len(checks),'errors':errors,'realBackend':True,'injectedFault':'lost acknowledgement after successful second storage write'},ensure_ascii=False,indent=2));print(json.dumps({'passed':len(checks),'checks':checks},ensure_ascii=False))
asyncio.run(main())
