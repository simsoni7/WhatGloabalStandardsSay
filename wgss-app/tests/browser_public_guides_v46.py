import json,hashlib,threading,http.server,functools
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'research/ui-v46';O.mkdir(parents=True,exist_ok=True);checks=[];errors=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();u=f'http://127.0.0.1:{s.server_port}'
try:
 f=json.loads((R/'dist/data/public-flow-cases-v46.json').read_text());w=json.loads((R/'dist/data/wording-references-v46.json').read_text())['items'];steps=[x for c in f['cases'] for x in c['steps']]
 check('six original images intact',len(steps)==6 and all(hashlib.sha256((R/'dist'/x['image_path']).read_bytes()).hexdigest()==x['image_sha256'] for x in steps))
 check('words keep exact image source and dates',len(w)==9 and all(any(z['id']==x['step_id'] and z['image_sha256']==x['image_sha256'] and z['source_url']==x['source_url'] and z['collected_at']==x['collected_at'] and x['label'] in z['observed_labels'] for z in steps) for x in w))
 check('no live input admissions or hidden-cookie reference',f['canonical_financial_work_admissions']==0 and f['counts']['blank_application_forms']==0 and not any('natwest' in c['id'] for c in f['cases']))
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1440,'height':1000});p.set_default_timeout(10000);p.on('pageerror',lambda e:errors.append(str(e)))
  def go(path):p.goto(u+'/'+path);p.locator('.wgss-v44').wait_for()
  def body():return p.locator('#content').inner_text()
  go('references.html#reference-search?task=account-opening&q=계좌개설&provider=ally');p.locator('[data-pick][value="case:v45-ally-account"]').wait_for();check('prior live reference kept in first gallery',p.locator('[data-pick][value="case:v45-ally-account"]').count()==1)
  for cid in ['v46-ally-guide-app','v46-ally-guide-web']:check('official guide searchable '+cid,p.locator(f'[data-pick][value="case:{cid}"]').count()==1)
  check('publisher date visible before opening details','2026-06-16 발행' in body());p.screenshot(path=str(O/'ally-gallery.png'))
  for c in f['cases']:
   go('#reference-flow/'+c['id']);p.locator('.wg-large img').wait_for();im=p.locator('.wg-large img');im.scroll_into_view_if_needed();p.wait_for_function('(e)=>e.complete&&e.naturalWidth>0',arg=im.element_handle());check('actual original served '+c['id'],im.get_attribute('src')==c['steps'][0]['image_path']);check('source and non-input context '+c['id'],c['steps'][0]['source_url'] in body() and '실제 신청 입력 아님' in body())
   if c['platform']=='app':check('authenticated publisher illustration qualified','Log Out' in body() and '수집자가 앱에 로그인한 관찰은 아닙니다' in body())
   if len(c['steps'])>1:
    check('published sequence not claimed observed journey',p.get_by_role('link',name='다음 예시',exact=True).count()==1 and '예시 1 / 2' in body());p.get_by_role('link',name='다음 예시',exact=True).click();p.locator('.wg-large img').wait_for();check('second publisher original and issue date',p.locator('.wg-large img').get_attribute('src')==c['steps'][1]['image_path'] and '안내 발행일' in body() and '2026-06-16' in body());p.reload();p.locator('.wg-large img').wait_for();check('publisher page reload preserves2','예시 2 / 2' in body())
  go('#reference-search?task=card-application&q=카드신청&provider=amex');check('company id shared by screen and words',p.locator('[data-pick][value="case:v46-amex-application-faq"]').count()==1)
  p.goto(u+'/company-dictionary.html');p.locator('#dictionary-results .recordrow').first.wait_for();check('standalone dictionary includes new native rows',p.locator('#dictionary-results .recordrow').count()==sum(len(json.loads((R/'dist/data'/name).read_text()).get('items',[])) for name in ['wording-references-v38.json','wording-references-v42.json','wording-references-v44.json','wording-references-v45.json','wording-references-v46.json','wording-references-v48.json']) and 'Open Savings Account' in body())
  go('#reference-search?view=wording&q=Open%20Savings%20Account&provider=ally');p.locator('.rw-copy').first.wait_for();check('native button usable with correct publisher provenance','Open Savings Account' in body() and '공식 발행 UI 예시' in body() and '2026-06-16 발행' in body())
  go('manage.html');p.locator('.wg-table').wait_for();check('admin correct explicit source and action units','v46 공식 안내·설명: 4사례 · 원본 6장 · 원문 9개 · 공식 페이지 조회 4회 · 이미지 확보 4회 · 공개 설명 화면 수집 3회.' in body());check('admin keeps zero actual input comparison pairs','v46 실제 신청 입력 0건 · 카드 신청 비교쌍 0 · 계좌 개설 비교쌍 0' in body());p.screenshot(path=str(O/'admin.png'))
  p.set_viewport_size({'width':390,'height':844});go('#reference-flow/v46-ally-guide-app?page=2');p.locator('.wg-large img').wait_for();check('mobile guide fits',p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));check('no browser exceptions',not errors);b.close()
 print(json.dumps({'browser_public_guides_v46':'passed','checks':len(checks)},ensure_ascii=False));(O/'browser-results.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2)+'\n')
finally:s.shutdown();s.server_close()
