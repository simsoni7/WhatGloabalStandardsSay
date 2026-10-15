"""Exercise cached old assets against a real HTTP cache and a new release."""
import asyncio,hashlib,json,pathlib,threading,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs
from playwright.async_api import async_playwright
ROOT=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/home/ubuntu/wgss-cache-preview')
BASE='/WhatGloabalStandardsSay/wgss/';seen=[];checks=[]
class HTTP(BaseHTTPRequestHandler):
 override=None
 def log_message(self,*args):pass
 def do_GET(self):
  u=urlsplit(self.path);seen.append(self.path);name=u.path.removeprefix(BASE)
  if name=='warm.html':data=b'<!doctype html><script src="app.js"></script>';typ='text/html'
  elif name=='app.js' and not u.query:data=b'window.CACHED_OLD_SCRIPT=true;';typ='application/javascript'
  elif name=='release.json' and HTTP.override:data=json.dumps({'release':HTTP.override}).encode();typ='application/json'
  else:
   f=ROOT/(name or 'index.html')
   if not f.is_file():self.send_response(404);self.end_headers();return
   data=f.read_bytes();typ='text/html' if not name else 'application/javascript' if f.suffix=='.js' else 'text/css' if f.suffix=='.css' else 'application/json' if f.suffix=='.json' else 'image/svg+xml' if f.suffix=='.svg' else 'image/png'
  self.send_response(200);self.send_header('Content-Type',typ);self.send_header('Cache-Control','max-age=600');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
def ck(label,ok):
 if not ok:raise AssertionError(label)
 checks.append(label);print(label,flush=True)
async def main():
 server=ThreadingHTTPServer(('127.0.0.1',0),HTTP);threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'+BASE
 try:
  async with async_playwright() as pw:
   browser=await pw.chromium.launch(headless=True,args=['--no-sandbox']);p=await browser.new_page(viewport={'width':1280,'height':900});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
   await p.goto(url+'warm.html',wait_until='networkidle');ck('old unversioned app is cached',await p.evaluate('window.CACHED_OLD_SCRIPT===true'))
   before=seen.count(BASE+'app.js');old=await p.evaluate('fetch("app.js").then(r=>r.text())');ck('actual browser cache reuses the old app without HTTP request','CACHED_OLD_SCRIPT' in old and seen.count(BASE+'app.js')==before)
   await p.goto(url,wait_until='networkidle');await p.wait_for_function('state.catalog!==null')
   ck('new version bypasses the cached old app',await p.evaluate('typeof window.CACHED_OLD_SCRIPT==="undefined"') and await p.locator('[data-nav="about"]').count()==1)
   hashes=await p.locator('script[src],link[rel="stylesheet"]').evaluate_all('(nodes)=>nodes.map(n=>n.src||n.href)')
   ck('every JS/CSS URL carries its content hash',all(len(parse_qs(urlsplit(u).query).get('v',[''])[0])==16 for u in hashes))
   for path in hashes:
    u=urlsplit(path);f=ROOT/u.path.split('/')[-1];ck('asset hash matches '+f.name,parse_qs(u.query)['v'][0]==hashlib.sha256(f.read_bytes()).hexdigest()[:16])
   ck('catalogue data URL is versioned',any(x.startswith(BASE+'integration-data/catalog.json?v=') for x in seen))
   await p.goto(url+'?tab=screens&reference=toss-v6%3ATOSS-019#screens',wait_until='networkidle');await p.locator('[data-add-collection-screen]').click()
   ck('collection addition retains context under versioned assets',await p.evaluate('state.contributionPrefill.collectionReferenceId==="toss-v6:TOSS-019"&&!state.contributionPrefill.referenceId'))
   await p.locator('#contribution-text').fill('Do not discard this draft');HTTP.override='ffffffffffffffff';await p.evaluate('WGSSPublic.checkRelease()')
   ck('new release is visible without automatically discarding a draft',await p.locator('#release-update').count()==1 and await p.locator('#contribution-text').input_value()=='Do not discard this draft')
   await p.set_viewport_size({'width':390,'height':844});ck('update notice fits mobile',await p.evaluate('document.documentElement.scrollWidth<=390'))
   await p.locator('#release-update button').click();await p.wait_for_url('**release=ffffffffffffffff#contribute');ck('explicit update preserves route and requests a fresh document',p.url.endswith('#contribute') and 'release=ffffffffffffffff' in p.url)
   ck('no uncaught browser errors',not errors);await browser.close()
 finally:server.shutdown();server.server_close()
 print(json.dumps({'passed':len(checks),'checks':checks},ensure_ascii=False))
asyncio.run(main())
