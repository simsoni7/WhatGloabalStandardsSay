"""Changed and unavailable sources cannot silently replace accepted revisions."""
import functools,hashlib,http.server,importlib.util,json,os,subprocess,sys,tempfile,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('collector',ROOT/'scripts/collect_provider_snapshots.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
checks=[]
def check(name,condition):
 assert condition,name
 checks.append(name)
class Handler(http.server.BaseHTTPRequestHandler):
 content=b'<html><header>Menu</header><main>Cancel is available before processing.</main></html>'
 blocked=False
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(403 if self.blocked else 200);self.end_headers();self.wfile.write(self.content)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with tempfile.TemporaryDirectory() as tmp:
  work=Path(tmp);source={'id':'TEST','url':'http://127.0.0.1:'+str(server.server_port),'sha256':hashlib.sha256(Handler.content).hexdigest()}
  active_source=dict(source);first=module.collect(source,work)
  check('same source bytes classified unchanged',first['revision_state']=='unchanged')
  original=(Path(first['snapshot_path'])/'source.html').read_bytes();Handler.content=b'<html><main>Cancel is unavailable after processing.</main></html>';changed=module.collect(source,work)
  check('changed source requires reassessment',changed['revision_state']=='needs_reassessment' and changed['semantic_review']=='not_assessed')
  check('old revision retained',Path(first['snapshot_path'])!=Path(changed['snapshot_path']) and (Path(first['snapshot_path'])/'source.html').read_bytes()==original)
  check('active source pointer unmodified',source==active_source)
  Handler.blocked=True;failed=module.collect(source,work)
  check('inaccessible source not promoted',failed['http_status']==403 and failed['revision_state']=='unreachable' and 'sha256' not in failed)
  cache=work/'standard';cache.mkdir();(cache/'raw').mkdir();raw=cache/'raw/pinned';raw.write_bytes(b'changed')
  (cache/'source-manifest.json').write_text(json.dumps({'sources':[{'id':'TEST','url':source['url'],'raw_path':'raw/pinned','sha256':hashlib.sha256(b'original').hexdigest()}]}))
  r=subprocess.run([sys.executable,str(ROOT/'research/data-v10/reproduce/standards/fetch_pinned_sources.py')],env=os.environ|{'WGSS_STANDARD_WORKDIR':str(cache)},capture_output=True,text=True)
  check('pinned standard drift stops parsing',r.returncode!=0 and 'Source changed' in r.stderr and raw.read_bytes()==b'changed')
 report={'status':'passed','checks':len(checks),'items':checks};(ROOT/'research/ui-v10/collector-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report))
finally:server.shutdown();server.server_close()
