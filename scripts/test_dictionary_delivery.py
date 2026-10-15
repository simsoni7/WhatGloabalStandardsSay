"""Regression: every selectable language has records; offline assets and missing-file fallback."""
import tempfile,zipfile,json,threading,http.server
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
core=[json.loads(line) for line in (root/'dist/data/glossary_entries.jsonl').read_text().splitlines()]
catalog=json.loads((root/'dist/community/catalog.json').read_text())
base_codes=set(r['target_language'] for r in core);all_codes=base_codes|set(catalog['counts_by_language']);expected_total=len(core)+catalog['entry_count']
expected_counts={code:sum(r['target_language']==code for r in core)+catalog['counts_by_language'].get(code,0) for code in all_codes}
def serve(directory):
 class Handler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**k):super().__init__(*a,directory=directory,**k)
  def log_message(self,*a):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();return f'http://127.0.0.1:{server.server_port}/financial-dictionary.html'

with tempfile.TemporaryDirectory() as directory:
 with zipfile.ZipFile(root/'dist/financial-dictionary.zip') as z:z.extractall(directory)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://**',lambda r:r.abort())
  page.goto(serve(directory));page.wait_for_function('(n)=>DATA.rows.length===n',arg=expected_total,timeout=30000)
  codes=page.locator('#language option').evaluate_all('(options)=>options.map(o=>o.value).filter(Boolean)');assert set(codes)==all_codes,codes
  counts={}
  for code in codes:
   page.select_option('#language',code);n=page.evaluate('filtered.length');assert n>0,(code,n);counts[code]=n
  page.click('#clear');page.click('button[data-view="statistics"]');page.locator('#languageList button').filter(has_text='벵골어').click();assert page.locator('#language').input_value()=='bn';assert page.evaluate('filtered.length')==expected_counts['bn']
  page.click('#clear');page.fill('#q','예금');page.wait_for_timeout(300)
  assert page.evaluate('filtered.length')>0,'Korean search returned no results'
  assert page.evaluate("filtered.every(r=>[r.source_english_korean,r.source_english,r.source_target,r.evidence_id,r.source_concept_id].some(v=>String(v||'').includes('예금')))")
  assert page.locator('thead').first.inner_text().find('영어 원문의 한국어 표현')>=0
  for query,language in [('경상계정','ms'),('당좌예금계좌','ne')]:
   page.click('#clear');page.select_option('#language',language);page.fill('#q',query);page.wait_for_timeout(300);assert page.evaluate('filtered.length')>0,(query,language)
  assert not errors,errors
  print(json.dumps({'scenario':'extracted offline ZIP served locally; external network blocked','language_counts':counts,'zero_languages':0,'errors':errors},ensure_ascii=False))
  browser.close()
 # HTML alone: every listed language must still have rows, unavailable ones must not be offered.
 with tempfile.TemporaryDirectory() as alone:
  import shutil
  shutil.copy2(Path(directory,'financial-dictionary.html'),Path(alone,'financial-dictionary.html'))
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page();page.goto(serve(alone));page.wait_for_function('loadingCommunity===null',timeout=15000)
   codes=page.locator('#language option').evaluate_all('(options)=>options.map(o=>o.value).filter(Boolean)');assert set(codes)==base_codes,codes
   for c in codes:page.select_option('#language',c);assert page.evaluate('filtered.length')>0,c
   assert '현재 읽은 자료의 언어만 표시' in page.locator('#layerStatus').inner_text()
   print(json.dumps({'scenario':'HTML without companion files','visible_languages':len(codes),'zero_languages':0,'explicit_failure_notice':True}));browser.close()

# Email bundle keeps external code absent and can load Korean search aids from source JSON.
with tempfile.TemporaryDirectory() as directory:
 with zipfile.ZipFile(root/'dist/financial-dictionary-email.zip') as z:
  assert not any(Path(name).suffix.lower() in {'.js','.mjs','.jse'} for name in z.namelist())
  z.extractall(directory)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://**',lambda r:r.abort())
  page.goto(serve(directory));page.wait_for_function('(n)=>DATA.rows.length===n',arg=len(core))
  page.locator('#importSource').set_input_files([str(Path(directory,'data',c['file'])) for c in catalog['components']])
  page.wait_for_function('(n)=>DATA.rows.length===n',arg=expected_total)
  page.fill('#q','예금');page.wait_for_timeout(300);assert page.evaluate('filtered.length')>0
  assert page.evaluate("filtered.some(r=>SOURCES.get(r.dataset_id).community&&String(r.source_english_korean||'').includes('예금'))"),'Imported community Korean search missing'
  assert not errors,errors
  print(json.dumps({'scenario':'email ZIP, source JSON imported, external network blocked','rows':expected_total,'languages':len(all_codes),'korean_search':True,'errors':errors},ensure_ascii=False));browser.close()
