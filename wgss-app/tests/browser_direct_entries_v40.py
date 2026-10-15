"""Regression: user-facing direct pages load without fragment navigation or prior tab state."""
import functools,http.server,threading,json,urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];checks=[];errors=[]
def check(n,v):
 assert v,n
 checks.append(n)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  parts=urllib.parse.urlsplit(self.path);routes=['public-screens','company-capabilities','company-dictionary']
  if parts.path in ['/'+route+'.html' for route in routes]:
   self.send_response(301);self.send_header('Location',parts.path[:-5]+('?' + parts.query if parts.query else ''));self.end_headers();return
  if parts.path.rstrip('/') in ['/'+route for route in routes]:self.path=parts.path.rstrip('/')+'.html'+('?' + parts.query if parts.query else '')
  return super().do_GET()
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'dist')));threading.Thread(target=s.serve_forever,daemon=True).start();url='http://127.0.0.1:'+str(s.server_port)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  public_count=sum(len(json.loads((R/f'dist/data/public-screen-assets-{v}.json').read_text())['assets']) for v in ['v39','v42']);word_count=sum(len(json.loads((R/f'dist/data/wording-references-{v}.json').read_text())['items']) for v in ['v38','v42','v44','v45','v46','v48']);cases=[('public-screens','회원가입·로그인·이벤트·Q&A','.public-screen-card',public_count),('company-capabilities','금융사별 기능 목록','#capability-results .recordrow',50),('company-dictionary','금융사별 언어사전','#dictionary-results .recordrow',word_count)]
  for route,title,rows,count in cases:
   res=page.goto(url+'/'+route+'.html');page.locator(rows).first.wait_for();check('direct HTML entry '+route,res.status==200 and page.url.startswith(url+'/'+route+'#') and page.locator('h1').inner_text()==title and page.locator(rows).count()==count)
   page.reload();page.locator(rows).first.wait_for();check('reload remains same view '+route,page.locator('h1').inner_text()==title)
   page.goto(url+'/#/'+route);page.locator(rows).first.wait_for();check('slash-prefixed fragment supported '+route,page.locator('h1').inner_text()==title)
   page.goto(url+'/#'+route+'/');page.locator(rows).first.wait_for();check('trailing slash supported '+route,page.locator('h1').inner_text()==title)
  page.goto(url+'/public-screens/');page.locator('.public-screen-card').first.wait_for();check('extensionless trailing-slash host entry',page.locator('.public-screen-card').count()==public_count)
  page.goto(url+'/#%2Fpublic-screens');page.locator('.public-screen-card').first.wait_for();check('encoded supported fragment reaches publicscreens',page.locator('.public-screen-card').count()==public_count)
  page.goto(url+'/public-screens.html?category=login&provider=Chase');page.locator('.public-screen-card').wait_for();check('direct entry carries filters',page.locator('.public-screen-card').count()==1 and page.locator('#public-screen-provider').input_value()=='Chase');page.get_by_role('link',name='화면·원문 보기',exact=True).click();page.locator('.capture-detail-image').wait_for();page.get_by_role('link',name='검색 결과로 돌아가기').click();page.locator('.public-screen-card').wait_for();check('direct entry detail-return keeps filters',page.locator('#public-screen-provider').input_value()=='Chase')
  page.goto(url+'/#missing-view');page.get_by_role('link',name='공개 화면 보기',exact=True).click();page.locator('.public-screen-card').first.wait_for();check('unknown route has actual page recovery',page.url.startswith(url+'/public-screens#') and page.locator('.public-screen-card').count()==public_count)
  page.set_viewport_size({'width':390,'height':844});check('direct page footer fits mobile',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));check('no JavaScript exceptions',not errors);b.close()
 print(json.dumps({'browser_direct_entries_v40':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
finally:s.shutdown();s.server_close()
