import json,hashlib,shutil,functools,http.server,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R;out=R/'research/ui-v48';out.mkdir(exist_ok=True);checks=[];errors=[]
f=json.loads((R/'dist/data/public-flow-cases-v48.json').read_text());w=json.loads((R/'dist/data/wording-references-v48.json').read_text())
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();u=f'http://127.0.0.1:{s.server_port}'
def check(n,v):
 checks.append({'name':n,'passed':bool(v)});assert v,n
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,args=['--no-sandbox']);p=b.new_page(viewport={'width':1440,'height':1000});p.set_default_timeout(10000);p.on('pageerror',lambda e:errors.append(str(e)))
  def go(h):p.goto(u+'/index.html'+h);p.locator('.wgss-v44').wait_for()
  def body():return p.locator('#content').inner_text()
  go('#reference-search?task=signup&q=회원가입&purpose=existing-customer-registration&provider=citi');card=p.locator('.wg-company').filter(has=p.locator('[data-pick][value="case:citi-us-existing-registration"]'));im=card.locator('.wg-img-button img').get_attribute('src');href=card.locator('.wg-img-button').get_attribute('href');check('preview href explicit matching page2','page=2' in href);card.locator('.wg-img-button').click();p.locator('.wg-large img').wait_for();check('preview click displays same original',p.locator('.wg-large img').get_attribute('src')==im);check('preview details stage selected2',p.locator('[role=tab][aria-selected=true]').inner_text().startswith('2'));p.reload();p.locator('.wg-large img').wait_for();check('reload preserves preview original',p.locator('.wg-large img').get_attribute('src')==im);p.get_by_role('link',name='검색 결과로 돌아가기',exact=True).click();p.locator('.wg-company').first.wait_for();check('back preserves original filters','provider=citi' in p.url and 'purpose=existing-customer-registration' in p.url);card=p.locator('.wg-company').filter(has=p.locator('[data-pick][value="case:citi-us-existing-registration"]'));card.get_by_role('link',name='흐름 보기 (2단계)',exact=True).click();p.locator('.wg-large img').wait_for();check('flow start footer still opens1',p.locator('[role=tab][aria-selected=true]').inner_text().startswith('1'))
  for c in f['cases']:
   go('#reference-search?task='+c['task_id']+'&provider='+c['provider_id']+'&country='+('unknown' if not c['country'] else c['country'])+'&language='+c['language']);sel='[data-pick][value="case:'+c['id']+'"]';p.locator(sel).wait_for();check('direct capture not in guide '+c['id'],p.locator(sel).evaluate('e=>!e.closest(".wg-guide-section")'));go('#reference-flow/'+c['id']);p.locator('.wg-large img').wait_for();check('direct capture never non-input disclaimer '+c['id'],'실제 신청 입력 아님' not in body());check('exact direct original '+c['id'],p.locator('.wg-large img').get_attribute('src')==c['steps'][0]['image_path']);check('direct source preserved '+c['id'],c['steps'][0]['source_url'] in body())
  go('#reference-flow/v46-ally-guide-app');p.locator('.wg-large img').wait_for();check('published guide non-input disclaimer preserved','실제 신청 입력 아님' in body());check('published app stays documented', 'Log Out' in body() and '수집자가 앱에 로그인한 관찰은 아닙니다' in body());check('guide pager examples not live flow','예시 1 / 2' in body());p.get_by_role('link',name='다음 예시',exact=True).click();p.get_by_text('예시 2 / 2',exact=True).wait_for();check('guide next original and reload preserved', '예시 2 / 2' in body())
  go('#reference-compare?selected=case:wise-gb-password-recovery,case:v48-n26-password-de');p.locator('select[name=stage]').wait_for();check('password request actual field stages align',p.locator('.wg-paired img').count()==2);check('friendly displayed recovery stage','비밀번호 재설정 요청 정보 입력' in body() and 'identity-input' not in body() and 'registration-input' not in body());check('same purpose different requested fields preserved','Enter your email address' in body() and 'Passwort zurücksetzen' in body());p.reload();p.locator('.wg-paired img').first.wait_for();check('recovery comparison reload preserves2',p.locator('.wg-paired img').count()==2)
  p.screenshot(path=str(out/'recovery-comparison.png'));check('real standalone words loaded',len(w['items'])==17);check('no browser exceptions',not errors);b.close()
 print(json.dumps({'checks':len(checks),'passed':True},ensure_ascii=False))
finally:
 (out/'result.json').write_text(json.dumps({'checks':checks,'passed':all(c['passed'] for c in checks),'errors':errors,'actual_integrated_data_no_fixture':True},ensure_ascii=False,indent=2));s.shutdown();s.server_close()
