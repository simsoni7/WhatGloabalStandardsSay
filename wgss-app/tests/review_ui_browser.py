"""Independent reviewer dialog: image-by-image edits, delayed AI, responsive layout."""
import asyncio, functools, http.server, json, pathlib, threading
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=pathlib.Path('/home/ubuntu/wgss-review-ui-check'); OUT.mkdir(exist_ok=True)
HTML='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/integration-ui/styles.css"><link rel="stylesheet" href="/integration-ui/review.css"><body><dialog id="detail-dialog"><div class="dialog-head"><h2 id="dialog-title"></h2><button onclick="document.querySelector('dialog').close()">닫기</button></div><div id="dialog-content"></div></dialog><script>
window.$=(s,r=document)=>r.querySelector(s);window.$$=(s,r=document)=>[...r.querySelectorAll(s)];window.esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));window.arr=v=>Array.isArray(v)?v:[];window.safeUrl=v=>v||'';window.link=(v,l)=>`<a href="${esc(v)}">${l}</a>`;window.notify=()=>{};window.optionList=(rows,value,label,key='label')=>`<option value="">${esc(label)}</option>`+rows.map(row=>`<option value="${esc(row.id)}" ${row.id===value?'selected':''}>${esc(row[key]||row.id)}</option>`).join('');window.state={catalog:{providers:[{id:'kakao',name:'카카오뱅크'}],languages:[{id:'ko',label:'한국어'},{id:'en',label:'영어'}],tasks:[{id:'support',label:'고객센터',workIds:['support-case']}],canonicalWorks:[],screens:[],features:[],phrases:[]},terms:[],adminItems:[]};window.openDialog=(title,html)=>{$('#dialog-title').textContent=title;$('#dialog-content').innerHTML=html;if(!$('dialog').open)$('dialog').showModal()};window.labelFor=(type,id)=>state.catalog[type].find(r=>r.id===id)?.label||id;window.fetchJSON=async()=>({items:[]});window.post=async()=>new Promise(resolve=>window.resolveAI=resolve);window.screenById=()=>null;
</script><script src="/integration-ui/publications.js"></script><script src="/integration-ui/review.js"></script><script>window.testItem={id:'sample',kind:'screen',status:'pending',version:1,title:'고객센터 쪽 화면',createdAt:'2026-10-15T16:30:00Z',current:{text:'카카오뱅크 고객센터 쪽 화면',sourceUrl:'https://www.kakaobank.com/'},files:[1,2,3].map(i=>({id:'f'+i,role:'masked',sha256:'sha'+i,createdAt:'2026-10-15T16:30:00Z'}))};WGSSReview.open(testItem);</script></body></html>'''
def make_fixtures():
 font=ImageFont.load_default(size=26)
 small=ImageFont.load_default(size=18)
 for i,title in enumerate(['Customer support','Frequently asked questions','Contact us'],1):
  image=Image.new('RGB',(390,690),'white');draw=ImageDraw.Draw(image)
  draw.rectangle((0,0,390,80),fill='#ffdf00');draw.text((22,28),'kakaobank',font=font,fill='#111')
  draw.text((22,118),title,font=small,fill='#111')
  for j,label in enumerate(['Help topics','Online support','Send a message']):
   y=200+j*95;draw.rounded_rectangle((20,y,370,y+70),radius=8,fill='#f4f4f4');draw.text((38,y+25),label,font=small,fill='#111')
  draw.text((22,625),'Synthetic UI for review testing',font=small,fill='#666');image.save(OUT/('photo-'+str(i)+'.png'))
async def run():
 make_fixtures()
 checks=[];errors=[]
 def ck(label,value):
  if not value:raise AssertionError(label)
  checks.append(label);print(label,flush=True)
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  async with async_playwright() as p:
   browser=await p.chromium.launch(headless=True,args=['--no-sandbox']);page=await browser.new_page(viewport={'width':1280,'height':950});page.on('pageerror',lambda error:errors.append(str(error)))
   await page.route('**/review-check',lambda route:route.fulfill(body=HTML,content_type='text/html'))
   await page.route('**/api/wgss?resource=file&**',lambda route:route.fulfill(path=str(OUT/('photo-'+route.request.url.rsplit('f',1)[-1]+'.png')),content_type='image/png'))
   await page.goto(f'http://127.0.0.1:{server.server_port}/review-check');await page.wait_for_selector('[data-photo="f1"]')
   dialog_text=await page.locator('#dialog-content').inner_text()
   ck('plain title and no raw record jargon',await page.locator('#dialog-title').inner_text()=='자료 검토' and not any(s in dialog_text for s in ['미확인','SHA256','masked','찾아보기 업무','기여 개별']))
   ck('three independently selected photographs',await page.locator('[name="maskedFileIds"]:checked').count()==3 and await page.locator('[data-photo]').count()==3)
   ck('upload date uses Korea date at UTC boundary',await page.locator('[data-photo="f1"] [data-review-field="capturedAt"]').input_value()=='2026-10-16')
   await page.locator('[data-photo="f1"] [data-review-field="title"]').fill('직접 고친 제목')
   await page.evaluate('''()=>resolveAI({status:'completed',sourceVersion:1,files:testItem.files.map(f=>({fileId:f.id,sha256:f.sha256})),draft:{providerId:'kakao',language:'ko',taskId:'support',screens:[1,2,3].map(i=>({fileId:'f'+i,title:'고객센터 '+i,language:'ko',taskId:'support',purpose:'도움받을 항목을 선택합니다.',ocrPhrases:[{text:'고객센터',role:'heading'},{text:'문의하기',role:'button'}]}))}})''')
   await page.wait_for_function("document.querySelector('#review-ai-message').textContent.includes('채웠습니다')")
   ck('AI preserves manual edit and fills untouched photographs',await page.locator('[data-photo="f1"] [data-review-field="title"]').input_value()=='직접 고친 제목' and await page.locator('[data-photo="f2"] [data-review-field="title"]').input_value()=='고객센터 2')
   ck('company language task and OCR automatically filled',await page.locator('[data-photo="f1"] [data-review-field="providerId"]').input_value()=='kakao' and await page.locator('[data-photo="f1"] [data-review-field="language"]').input_value()=='ko' and await page.locator('[data-photo="f1"] [data-review-field="taskId"]').input_value()=='support' and '문의하기' in await page.locator('[data-photo="f1"] [data-review-field="ocr"]').input_value())
   await page.locator('[data-review-photo="f3"]').click()
   ck('thumbnail changes editor without discarding other edits',await page.locator('[data-photo="f3"]').is_visible() and not await page.locator('[data-photo="f1"]').is_visible())
   application=await page.evaluate("WGSSApplied.application(document.querySelector('#review-form'))")
   ck('approval maps all photos to their own titles and OCR',len(application['photos'])==3 and application['photos'][0]['fields']['title']=='직접 고친 제목' and application['photos'][2]['fields']['title']=='고객센터 3' and application['photos'][0]['phrases'][1]['text']=='문의하기' and application['photos'][0]['phrases'][1]['role']=='button')
   ck('company function is derived from the selected task',application['photos'][0]['feature']['workId']=='support-case' and application['photos'][0]['feature']['expression']=='고객센터')
   await page.evaluate("document.querySelector('[name=privacyReviewed]').checked=true;document.querySelector('[name=readabilityReviewed]').checked=true;WGSSReview.validateDecision(document.querySelector('#review-form'),'approved')")
   ck('approve defaults reason without extra entry',await page.locator('[name="reason"]').input_value()=='내용 확인 후 승인')
   await page.locator('[name="reason"]').fill('')
   ck('holding requires actual explanation',await page.evaluate("(()=>{try{WGSSReview.validateDecision(document.querySelector('#review-form'),'held');return false}catch(e){return e.message.includes('사유')}})()"))
   await page.evaluate("document.activeElement.blur();document.querySelector('dialog').scrollTop=0")
   await page.wait_for_function("[...document.querySelectorAll('[data-photo] img')].every(image=>image.complete&&image.naturalWidth===390)")
   ck('each photo preview loads actual PNG bytes',await page.locator('[data-photo] img').evaluate_all('(images)=>images.every(image=>image.naturalWidth===390)'))
   await page.screenshot(path=str(OUT/'review-1280-top.png'),full_page=True)
   await page.locator('[data-photo=\"f3\"]').scroll_into_view_if_needed()
   await page.screenshot(path=str(OUT/'review-1280-editor.png'),full_page=True)
   await page.set_viewport_size({'width':390,'height':844})
   ck('mobile dialog fits viewport and fields do not overlap',await page.evaluate("(()=>{const d=document.querySelector('dialog');return d.getBoundingClientRect().left>=0&&d.getBoundingClientRect().right<=innerWidth+1&&d.scrollWidth<=d.clientWidth+1})()"))
   await page.locator('[name="decision"][value="approved"]').scroll_into_view_if_needed()
   ck('mobile publish controls remain distinct',await page.evaluate("(()=>{const a=document.querySelector('[value=approved]').getBoundingClientRect(),b=document.querySelector('[value=held]').getBoundingClientRect();return a.bottom<=b.top+1||a.right<=b.left+1})()"))
   await page.evaluate("document.activeElement.blur();document.querySelector('dialog').scrollTop=0")
   await page.screenshot(path=str(OUT/'review-390-top.png'),full_page=True)
   await page.locator('[name=\"reason\"]').scroll_into_view_if_needed()
   ck('memo textarea does not intersect sticky footer',await page.evaluate("(()=>{const field=document.querySelector('[name=reason]').getBoundingClientRect(),footer=document.querySelector('.review-actions').getBoundingClientRect();return field.bottom<=footer.top+1||field.top>=footer.bottom-1})()"))
   await page.screenshot(path=str(OUT/'review-390-footer.png'),full_page=True)
   await page.locator('dialog').evaluate('(d)=>d.close()')
   await page.evaluate("WGSSReview.open(testItem)")
   await page.evaluate("resolveAI({status:'completed',sourceVersion:2,files:[],draft:{screens:[{fileId:'f1',title:'오래된 추천'}]}})")
   await page.wait_for_function("document.querySelector('#review-ai-message').textContent.includes('변경')")
   ck('changed version rejects stale recommendation',await page.locator('[data-photo="f1"] [data-review-field="title"]').input_value()!='오래된 추천')
   await page.locator('dialog').evaluate('(d)=>d.close()')
   await page.evaluate("WGSSReview.open(testItem)")
   await page.evaluate("resolveAI({status:'completed',sourceVersion:1,files:[{fileId:'f1',sha256:'modified'}],draft:{screens:[{fileId:'f1',title:'다른 사진 추천'}]}})")
   await page.wait_for_function("document.querySelector('#review-ai-message').textContent.includes('사진이 변경')")
   ck('changed file fingerprint rejects AI metadata',await page.locator('[data-photo=\"f1\"] [data-review-field=\"title\"]').input_value()!='다른 사진 추천')
   await page.locator('dialog').evaluate('(d)=>d.close()')
   await page.evaluate("post=async()=>{throw Error('개인정보를 가린 자료인지 먼저 확인해 주세요. 확인 후 AI 추천을 만들 수 있습니다.')} ; WGSSReview.open(testItem)")
   await page.wait_for_selector('#review-ai-privacy',state='visible')
   ck('legacy images need explicit privacy confirmation before model call',await page.locator('#review-ai-privacy-confirmed').is_checked()==False and 'Bedrock' in await page.locator('#review-ai-privacy').inner_text())
   await page.locator('#review-ai-confirm').click()
   ck('unchecked privacy cannot send analysis', '먼저 확인' in await page.locator('#review-ai-message').inner_text())
   await page.locator('dialog').evaluate('(d)=>d.close()')
   await page.evaluate("post=async()=>({status:'completed',sourceVersion:1,files:[],draft:{kind:'term',screens:[],term:{korean:'계좌',english:'Account',target:'계좌',language:'ko',explanation:'금융 거래를 기록하는 계좌'}}});WGSSReview.open({...testItem,kind:'translation_issue',files:[],current:{proposalType:'term',termEnglish:'Account',termTarget:'계좌',language:'ko'}})")
   await page.wait_for_function("document.querySelector('#apply-korean')?.value==='계좌'")
   ck('terms keep clear two-type contract and commercial rights review',await page.locator('#apply-type').input_value()=='terms' and await page.locator('#apply-rights-confirmed').count()==1 and await page.locator('#apply-type option').count()==2)
   ck('no JavaScript errors',not errors)
   await browser.close()
 finally:server.shutdown()
 (OUT/'report.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2));print(json.dumps({'passed':len(checks),'report':str(OUT/'report.json')},ensure_ascii=False))
if __name__=='__main__':asyncio.run(run())
