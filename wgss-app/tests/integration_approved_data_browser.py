import json,pathlib,os,io
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw
O=pathlib.Path(os.environ.get('WGSS_QA_OUTPUT','/home/ubuntu/wgss-approval-integration'));O.mkdir(exist_ok=True)
BASE=os.environ.get('WGSS_QA_BASE','http://127.0.0.1:3011');checks=[];errors=[]
def ck(label,ok):
 if not ok:raise AssertionError(label)
 checks.append(label);print(label,flush=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1440,'height':1000});p.on('pageerror',lambda e:errors.append(str(e)))
 p.goto(BASE+'/signin-with-chatgpt?return_to=/workspace/',wait_until='networkidle');p.goto(BASE+'/workspace/?tab=published#screens',wait_until='networkidle');p.locator('[data-tab="screens"]').wait_for()
 ck('obsolete approval tab removed and legacy URL resolves to normal screens',p.locator('[data-tab="published"]').count()==0 and 'tab=screens' in p.url)
 ck('real signed-in admin',p.evaluate('state.session.role')=='admin')
 p.evaluate('openScreen("toss-v6:TOSS-019")');ck('Toss shows all 101 accepted captures as a shared collection','101장' in p.locator('#flow-section').inner_text() and p.locator('#flow-section [data-screen]').count()==12 and '실제 이동 순서는 확인되지' in p.locator('#flow-section').inner_text());p.locator('[data-related-page]').last.click();ck('shared collection pagination works',p.locator('#flow-section [data-screen]').count()==12);p.keyboard.press('Escape')
 def post(payload):
  r=p.request.post(BASE+'/api/wgss',data=payload);assert r.ok,r.text();return r.json()
 def create(ref='',kind='text'):
  return post({'action':'createSubmission','kind':kind,'title':'Synthetic approval integration QA','text':'Proposal description must not become a label','referenceId':ref})['item']
 def review(item):
  p.goto(BASE+'/workspace/#admin',wait_until='networkidle');p.locator('[data-review="'+item['id']+'"]').click();p.locator('#apply-fields').wait_for();p.locator('[name=privacyReviewed]').check();p.locator('[name=readabilityReviewed]').check();p.locator('#review-reason').fill('Synthetic local QA')
 def approve():
  p.get_by_role('button',name='이 버전 승인',exact=True).click();p.wait_for_function('!document.querySelector("#detail-dialog").open')
 def refresh(url):
  p.goto(BASE+'/workspace/'+url,wait_until='networkidle');p.wait_for_function('state.catalog!==null')
 made=[]
 try:
  phrase=p.evaluate('state.catalog.phrases.find(r=>r.providerId==="paypal"&&r.language==="en")');old=phrase['text'];item=create(phrase['id']);made.append(item['id']);review(item);p.wait_for_function('state.applySelection!==null');ck('existing phrase target selected automatically',p.locator('#apply-type').input_value()=='phrases');p.locator('#apply-text').fill('Synthetic Save WGSS QA');approve()
  refresh('?tab=words&wordMode=phrases&query=Synthetic%20Save&provider=paypal&language=en#screens');ck('approved wording appears directly in normal company phrase search',p.locator('[data-phrase-detail="'+phrase['id']+'"]').count()>=1 and '수정 반영' in p.locator('#results').inner_text());ck('update preserves record ID, original observation and no duplicate',p.evaluate('(id)=>state.catalog.phrases.filter(r=>r.id===id).length===1&&state.catalog.phrases.find(r=>r.id===id).sourceObservation.text!=="Synthetic Save WGSS QA"',phrase['id']))
  p.locator('[data-phrase-detail="'+phrase['id']+'"]').first.click();ck('normal phrase detail shows approved label','Synthetic Save WGSS QA' in p.locator('#dialog-content').inner_text());p.keyboard.press('Escape')
  # Correct a real chunk-backed term without preloading the dictionary in this page.
  term=p.request.get(BASE+'/api/wgss?resource=targets&type=terms&q=interest').json()['items'][0];item=create(term['id'],'translation_issue');made.append(item['id']);review(item);p.locator('#apply-target').wait_for();p.wait_for_function('state.applySelection!==null');p.locator('#apply-target').fill('Synthetic Existing Term WGSS');approve()
  refresh('?tab=words&wordMode=terms&query=Synthetic%20Existing%20Term#screens');p.wait_for_function('!state.loadingTerms',timeout=90000);ck('existing dictionary correction survives fresh chunk loading',p.evaluate('(id)=>state.terms.find(r=>r.id===id).target==="Synthetic Existing Term WGSS"',term['id']))
  item=create(kind='translation_issue');made.append(item['id']);review(item);p.locator('#apply-type').select_option('terms');p.locator('#apply-operation').select_option('add');p.locator('#apply-english').fill('Synthetic Term WGSS');p.locator('#apply-target').fill('Synthetic Definition WGSS');p.locator('#apply-language').select_option('en');approve()
  refresh('?tab=words&wordMode=terms&query=Synthetic%20Definition&language=en#screens');p.wait_for_function('!state.loadingTerms',timeout=90000);ck('approved term appears in normal dictionary search','Synthetic Definition WGSS' in p.locator('#dictionary-results').inner_text());ck('new term does not claim expert translation approval',p.evaluate('state.terms.find(r=>r.target==="Synthetic Definition WGSS").approvedTranslation===null'))
  feature=p.evaluate('state.catalog.features.find(r=>r.providerId==="paypal")');item=create(feature['id']);made.append(item['id']);review(item);p.locator('#apply-expression').fill('Synthetic Feature WGSS');p.locator('#apply-meaning').fill('Synthetic feature explanation');approve()
  refresh('?tab=features&provider=paypal#screens');ck('approved company feature enters actual matrix data',p.evaluate('(id)=>state.catalog.features.find(r=>r.id===id).expression==="Synthetic Feature WGSS"',feature['id']))
  # Narrow by its canonical definition label so the changed cell is visible.
  label=p.evaluate('(id)=>state.catalog.canonicalWorks.find(w=>w.id===state.catalog.features.find(f=>f.id===id).workId).label',feature['id']);p.locator('#query').fill(label);p.wait_for_timeout(350);ck('company matrix displays the revised function name','Synthetic Feature WGSS' in p.locator('#results').inner_text())
  # Replace an actual original screen and ensure the old image becomes history.
  original=p.evaluate('state.catalog.screens.find(r=>r.cohort!=="contribution")');item=create(original['id'],'screen');made.append(item['id']);img=Image.new('RGB',(160,100),'#eeeeee');out=io.BytesIO();img.save(out,format='PNG');res=p.request.post(BASE+'/api/wgss',multipart={'action':'upload','submissionId':item['id'],'role':'masked','file':{'name':'synthetic.png','mimeType':'image/png','buffer':out.getvalue()}});assert res.ok,res.text();item=res.json()['item'];review(item);p.locator('#review-file').select_option([f['id'] for f in item['files']]);p.locator('#apply-title').fill('Synthetic Replacement WGSS');approve()
  refresh('?tab=screens&reference='+original['id']+'#screens');p.locator('[data-previous-versions]').click();p.wait_for_function('document.querySelector("#previous-versions .screen-card")!==null');ck('new approved screenshot is primary and original image is an earlier version',p.locator('#dialog-title').inner_text().endswith('Synthetic Replacement WGSS') and p.locator('#previous-versions img').first.get_attribute('src')==original['imagePath'] and p.locator('#dialog-content > .dialog-layout img').get_attribute('src')!=original['imagePath']);p.keyboard.press('Escape')
  item=create(kind='screen');made.append(item['id'])
  for n in [1,2]:
   img=Image.new('RGB',(200,150),'white');ImageDraw.Draw(img).text((10,10),'SYNTHETIC '+str(n),fill='black');out=io.BytesIO();img.save(out,format='PNG')
   r=p.request.post(BASE+'/api/wgss',multipart={'action':'upload','submissionId':item['id'],'role':'masked','file':{'name':'synthetic.png','mimeType':'image/png','buffer':out.getvalue()}});assert r.ok,r.text();item=r.json()['item']
  review(item);p.locator('#review-file').select_option([f['id'] for f in item['files']]);p.locator('#apply-operation').select_option('add');p.locator('#apply-title').fill('Synthetic Screens WGSS');p.locator('#apply-providerId').select_option('citi');p.locator('#apply-language').select_option('en');p.locator('#apply-taskId').select_option('signup');p.screenshot(path=str(O/'approval-admin.png'),full_page=True);approve()
  refresh('?tab=screens&query=Synthetic%20Screens&provider=citi&language=en&task=signup#screens');ck('two approved captures appear in normal filtered screen library',p.locator('.screen-card').count()==2);p.wait_for_function('[...document.querySelectorAll(".screen-card img")].every(i=>i.naturalWidth>0)');ck('real stored masked files render',p.locator('.screen-card img').count()==2)
  ck('screen selection and saved-comparison workflow removed',p.locator('[data-compare]').count()==0 and p.locator('[data-nav="saved"]').count()==0 and p.locator('#compare-tray').count()==0)
  refresh('?tab=screens&query=Synthetic%20Screens&language=en#saved');ck('old saved link returns to search and preserves filters',p.url.endswith('#screens') and p.locator('#query').input_value()=='Synthetic Screens' and p.locator('#language').input_value()=='en')
  refresh('?tab=screens&query=Synthetic%20Screens#screens');p.set_viewport_size({'width':390,'height':844});ck('normal screen results fit mobile390',p.evaluate('document.documentElement.scrollWidth<=390'));p.screenshot(path=str(O/'approved-screens-mobile.png'),full_page=True)
 finally:
  current=p.request.get(BASE+'/api/wgss?resource=submissions').json().get('items',[])
  for item in current:
   if item['id'] in made:post({'action':'deleteSubmission','id':item['id'],'expectedVersion':item['version']})
  for item in p.request.get(BASE+'/api/wgss?resource=comparisons').json().get('items',[]):
   if item['name']=='Synthetic comparison WGSS':post({'action':'deleteComparison','id':item['id']})
  b.close()
ck('no unhandled browser errors',not errors)
(O/'browser-results.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'errors':errors,'realBackend':True},ensure_ascii=False,indent=2))
