import unittest,threading,http.server,json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import document_transport_v46 as dt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from playwright.sync_api import sync_playwright
class TransportTests(unittest.TestCase):
 def setUp(self):
  self.hits=[];hits=self.hits
  class H(http.server.BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    hits.append(('GET',self.path))
    if self.path.startswith('/r/'):
     self.send_response(int(self.path.split('/')[-1]));self.send_header('Location',self.server.trap_url);self.end_headers();return
    body=b'<html><body><h1>Reviewed document</h1></body></html>';self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body)
   def do_POST(self):hits.append(('POST',self.path));self.send_response(200);self.end_headers()
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),H);self.trap=http.server.ThreadingHTTPServer(('127.0.0.1',0),H)
  self.url=f'http://127.0.0.1:{self.server.server_port}/doc';self.trapurl=f'http://127.0.0.1:{self.trap.server_port}/trap';self.server.trap_url=self.trapurl
  self.threads=[]
  for s in [self.server,self.trap]:
   t=threading.Thread(target=s.serve_forever,daemon=True);t.start();self.threads.append(t)
  self.key=Ed25519PrivateKey.generate();self.public=self.key.public_key().public_bytes_raw()
 def tearDown(self):
  for s in [self.server,self.trap]:s.shutdown();s.server_close()
  for t in self.threads:t.join(timeout=2)
 def signed(self,doc):
  r={'sha256':dt.sha256_hex(doc['bytes']),'url':doc['url'],'reviewer':'synthetic-independent-reviewer','reason':'Exact synthetic document reviewed','expires_at':time.time()+60};r['signature']=self.key.sign(dt.build_signed_record_payload(doc['bytes'],r['url'],r['reviewer'],r['reason'],r['expires_at'])).hex();return r
 def test_five_redirect_codes_never_reach_live_trap(self):
  for code in [301,302,303,307,308]:
   self.hits.clear();u=self.url.replace('/doc',f'/r/{code}')
   with self.assertRaisesRegex(dt.DocumentTransportError,'redirect_refused_'+str(code)):dt.read_document(u,u,test_mode=True)
   self.assertEqual(self.hits,[('GET',f'/r/{code}')])
 def test_exact_url_get_and_no_production_http(self):
  with self.assertRaises(dt.DocumentTransportError):dt.read_document(self.url,self.trapurl,test_mode=True)
  with self.assertRaises(dt.DocumentTransportError):dt.read_document(self.url,self.url)
  self.assertEqual(self.hits,[]);d=dt.read_document(self.url,self.url,test_mode=True);self.assertEqual(d['status'],200);self.assertEqual(self.hits,[('GET','/doc')])
 def test_unsigned_or_changed_document_not_rendered(self):
  d=dt.read_document(self.url,self.url,test_mode=True);r=self.signed(d)
  with self.assertRaises(dt.DocumentTransportError):dt.render_verified(d,{},self.public)
  d['bytes']+=b'changed'
  with self.assertRaisesRegex(dt.DocumentTransportError,'hash_mismatch'):dt.render_verified(d,r,self.public)
 def test_expired_or_wrong_url_or_signature_rejected(self):
  d=dt.read_document(self.url,self.url,test_mode=True)
  for mutation in ['expired','url','signature']:
   r=self.signed(d)
   if mutation=='expired':r['expires_at']=time.time()-1
   if mutation=='url':r['url']=self.trapurl
   if mutation=='signature':r['signature']='00'*64
   with self.assertRaises(dt.DocumentTransportError):dt.render_verified(d,r,self.public)
 def test_browser_owns_blocking_and_two_fresh_renders(self):
  d=dt.read_document(self.url,self.url,test_mode=True)
  d['bytes']=f'''<html><head><meta http-equiv="refresh" content="0;url={self.trapurl}"></head><body><h1>Reviewed document</h1><script>window.executed=true;fetch('{self.trapurl}')</script><img src="{self.trapurl}"><form action="{self.trapurl}" method="POST"><button>Submit</button></form><a href="{self.trapurl}">Leave</a></body></html>'''.encode()
  with sync_playwright() as p:
   b=p.chromium.launch(headless=True,args=['--no-sandbox'])
   for i in range(2):
    view=dt.render_verified_to_browser(b,d,self.signed(d),self.public)
    try:
     self.assertEqual(view.page.locator('h1').inner_text(),'Reviewed document');self.assertFalse(view.page.evaluate('Boolean(window.executed)'));view.page.locator('button').click(no_wait_after=True);view.page.wait_for_timeout(100);self.assertEqual(self.hits,[('GET','/doc')]);self.assertFalse(view.page.locator('meta[http-equiv=refresh]').count());self.assertEqual(view.ledger['sha256'],dt.sha256_hex(d['bytes']))
     try:view.page.locator('a').click(no_wait_after=True);view.page.wait_for_timeout(100)
     except Exception:pass
     self.assertEqual(self.hits,[('GET','/doc')]);self.assertTrue(any(x['resource_type']=='document' for x in view.blocked_requests))
    finally:view.close()
   b.close()
if __name__=='__main__':unittest.main(verbosity=2)
