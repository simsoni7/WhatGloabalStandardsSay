"""Capture privacy provenance and canonical case comparison regressions."""
import functools,http.server,json,threading,hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];out=R/'research/ui-v37';out.mkdir(exist_ok=True);checks=[];errors=[]
def check(n,v):assert v,n;checks.append(n)
d=json.loads((R/'dist/data/bank-ui.json').read_text());c=json.loads((R/'dist/data/user-capture-intake-v37.json').read_text());src=json.loads((R/'dist/data/capture-source-review-v37.json').read_text())
check('43 files,42 unique originals,10 selected with original byte hashes',len(c['records'])==43 and len({r['sha256'] for r in c['records']})==42 and sum(r['image_published'] for r in c['records'])==10 and all(hashlib.sha256((R/'dist'/r['image_path']).read_bytes()).hexdigest()==r['sha256'] for r in c['records'] if r['image_published']))
check('unknown-country intake never admitted as country/app/complete evidence',all(r['country'] is None and not r['canonical_admitted'] and not r['financial_submission_observed'] and r['ui_version'] is None for r in c['records']) and c['country_work_matrix_admissions']==0 and c['app_observation_admissions']==0)
check('private files excluded from distribution including hidden duplicates',all(not r['image_published'] and 'image_path' not in r for r in c['records'] if r['category']=='private') and len(list((R/'dist/assets/user-captures-v37').glob('*.jpg')))==10 and next(r for r in c['records'] if r['id']=='D16')['duplicate_of']=='D15')
check('original canonical dataset stays216/323',len(d['works'])==216 and len(d['benchmarks'])==323)
check('public evidence verification distinguished from HTTP retrieval and failures',src['counts']=={'attempts':13,'retrieved':10,'failed':3,'root_verified_articles':5,'canonical_admissions':0})
for r in src['sources']:
 if r['root_review_status']=='verified_article_section':
  p=Path('/home/ubuntu/wgss-v37-public-research/sources')/(r['id']+'.txt')
  if p.exists():
   t=p.read_text();l=r['proof_locator'];check('exact frozen source proof '+r['id'],t[l['start']:l['end']]==r['proof_quote'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['text_sha256'])
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(s.server_port)
wid='WGSS-UI-E7352823594F'
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url+'/#bank-work/'+wid+'?country=GB');page.locator('[data-bank-compare]').first.wait_for()
  check('four GB submission cases, capture separate link',page.locator('[data-bank-compare]').count()==4 and page.get_by_role('link',name='입력 화면·원문 표기 보기').count()==1)
  page.locator('[data-bank-compare]').nth(0).click();page.locator('[data-bank-compare]').nth(1).click();selected=page.locator('[data-bank-compare][aria-pressed="true"]').count();saved=page.url
  check('selection serialized and reload retained',selected==2 and 'compare=' in saved);page.reload();page.locator('[data-bank-compare]').first.wait_for();check('reload restores two selected cases',page.locator('[data-bank-compare][aria-pressed="true"]').count()==2)
  page.locator('[data-bank-open-compare]').click();page.locator('.bank-comparison').wait_for();comparisonURL=page.url
  check('comparison contains only two same-work GB references',page.locator('.bank-comparison thead th').count()==3 and page.locator('#nav-explore').get_attribute('aria-current') is not None)
  check('document instructions and observed labels separated',page.get_by_role('rowheader',name='확인한 화면 표기',exact=True).count()==1 and page.get_by_role('rowheader',name='문서에 설명된 경로',exact=True).count()==1 and page.get_by_role('rowheader',name='입력 데이터 · 필드 라벨 미확인',exact=True).count()==1)
  page.screenshot(path=str(out/'comparison-desktop.png'));page.reload();page.locator('.bank-comparison').wait_for();check('comparison bookmark reload works',page.url==comparisonURL and page.locator('.bank-comparison thead th').count()==3)
  page.get_by_role('link',name='사례 선택으로 돌아가기').click();page.locator('[data-bank-compare]').first.wait_for();check('return restores selection and country',page.locator('[data-bank-compare][aria-pressed="true"]').count()==2 and page.locator('#bank-country').input_value()=='GB')
  page.locator('[data-bank-compare]').nth(2).click();page.locator('[data-bank-compare]').nth(3).click();check('fourth selection prevented with message',page.locator('[data-bank-compare][aria-pressed="true"]').count()==3 and '최대 3개' in page.locator('#bank-compare-message').inner_text())
  page.locator('#bank-country').select_option('KR');check('country change clears incompatible selection',page.locator('[data-bank-compare][aria-pressed="true"]').count()==0 and page.locator('[data-bank-open-compare]').count()==0)
  refs=[b for b in d['benchmarks'] if b['root_function_admitted'] and b['country']=='GB' and wid in b['ui_work_ids']];wrong=next(b['id'] for b in d['benchmarks'] if b['country']!='GB' or wid not in b['ui_work_ids']);ids=refs[0]['id']+','+wrong+','+refs[1]['id']
  page.goto(url+'/#bank-compare/'+wid+'?country=GB&examples='+ids);page.locator('.bank-comparison').wait_for();check('forged cross-work/country id excluded',page.locator('.bank-comparison thead th').count()==3 and wrong not in page.locator('.bank-comparison thead').inner_text())
  page.goto(url+'/#bank-compare/'+wid+'?country=US&examples='+ids);page.get_by_role('link',name='사례 선택으로 돌아가기').wait_for();check('unsupported country cannot create comparison',page.locator('.bank-comparison').count()==0)
  page.goto(url+'/#capture-intake');page.locator('.capture-card').first.wait_for();check('reviewed gallery shows10safeoriginals and country limit',page.locator('.capture-card').count()==10 and '계정 국가와 UI 버전은 미확인' in page.locator('#content').inner_text())
  page.locator('#capture-query').fill('송금');check('capture searchable by intent with observed empty state limits',page.locator('.capture-card').count()==1 and 'Next는 비활성' in page.locator('.capture-card').inner_text());galleryURL=page.url;page.reload();page.locator('.capture-card').wait_for();check('gallery query restores after reload',page.url==galleryURL and page.locator('#capture-query').input_value()=='송금')
  page.goto(url+'/#capture-intake?capture=D08');page.locator('.capture-card').wait_for();check('work-specific captured reference stays separated',page.locator('.capture-card').count()==1 and '국가 미확인' in page.locator('.capture-card').inner_text())
  page.set_viewport_size({'width':390,'height':844});check('capture gallery fits mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));page.screenshot(path=str(out/'capture-recipient-mobile.png'))
  page.goto(url+'/#bank-compare/'+wid+'?country=GB&examples='+refs[0]['id']+','+refs[1]['id']);page.locator('.bank-comparison').wait_for();check('comparison scrolls within container on mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1') and page.locator('.bank-compare-wrap').evaluate('(e)=>e.scrollWidth>e.clientWidth'));page.screenshot(path=str(out/'comparison-mobile.png'))
  page.goto(url+'/#bank-work/'+wid+'?country=GB');page.get_by_role('link',name='입력 화면·원문 표기 보기').wait_for();page.get_by_role('link',name='입력 화면·원문 표기 보기').click();page.locator('.capture-detail-image').wait_for();check('practitioner capture view shows image directly without admin metrics',page.locator('.metric,.tabs').count()==0 and page.locator('#nav-explore').get_attribute('aria-current') is not None);page.screenshot(path=str(out/'captured-screen-mobile.png'));page.get_by_role('link',name='관련 업무로 돌아가기').click();page.locator('#bank-country').wait_for();check('captured reference returns to same country context',page.locator('#bank-country').input_value()=='GB')
  page.goto(url+'/#capture-intake?capture=D19');page.locator('#capture-results .empty').wait_for();check('private capture cannot be revealed by URL id',page.locator('.capture-card').count()==0 and page.get_by_role('link',name='전체 선별 화면 보기').count()>0)
  check('no browser JS errors',not errors);browser.close()
 print(json.dumps({'browser_capture_comparison_v37':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
