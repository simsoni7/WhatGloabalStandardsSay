"""Regression: every selectable language has records; offline assets and missing-file fallback."""
import tempfile,zipfile,json,threading,http.server
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
def serve(directory):
 class Handler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**k):super().__init__(*a,directory=directory,**k)
  def log_message(self,*a):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();return f'http://127.0.0.1:{server.server_port}/financial-dictionary.html'

with tempfile.TemporaryDirectory() as directory:
 with zipfile.ZipFile(root/'dist/financial-dictionary.zip') as z:z.extractall(directory)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://**',lambda r:r.abort())
  page.goto(serve(directory));page.wait_for_function('DATA.rows.length===25146',timeout=30000)
  codes=page.locator('#language option').evaluate_all('(options)=>options.map(o=>o.value).filter(Boolean)');assert len(codes)==45,codes
  counts={}
  for code in codes:
   page.select_option('#language',code);n=page.evaluate('filtered.length');assert n>0,(code,n);counts[code]=n
  page.click('#clear');page.click('button[data-view="statistics"]');page.locator('#languageList button').filter(has_text='벵골어').click();assert page.locator('#language').input_value()=='bn';assert page.evaluate('filtered.length')==52
  assert not errors,errors
  print(json.dumps({'scenario':'extracted offline ZIP served locally; external network blocked','language_counts':counts,'zero_languages':0,'errors':errors},ensure_ascii=False))
  browser.close()
 # HTML alone: every listed language must still have rows, unavailable ones must not be offered.
 with tempfile.TemporaryDirectory() as alone:
  import shutil
  shutil.copy2(Path(directory,'financial-dictionary.html'),Path(alone,'financial-dictionary.html'))
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page();page.goto(serve(alone));page.wait_for_function('loadingCommunity===null',timeout=15000)
   codes=page.locator('#language option').evaluate_all('(options)=>options.map(o=>o.value).filter(Boolean)');assert len(codes)==36,len(codes)
   for c in codes:page.select_option('#language',c);assert page.evaluate('filtered.length')>0,c
   assert '현재 읽은 자료의 언어만 표시' in page.locator('#layerStatus').inner_text()
   print(json.dumps({'scenario':'HTML without companion files','visible_languages':len(codes),'zero_languages':0,'explicit_failure_notice':True}));browser.close()
