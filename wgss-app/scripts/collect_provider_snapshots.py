"""Append immutable public document revisions; never auto-promote policy claims."""
import argparse,concurrent.futures,datetime,hashlib,json,urllib.request,urllib.error
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def collect(source,storage):
 now=datetime.datetime.now(datetime.timezone.utc).isoformat();sid=source['id']
 result={'source_id':sid,'requested_url':source['url'],'checked_at':now,'active_sha256':source.get('sha256'),'semantic_review':'not_assessed'}
 try:
  request=urllib.request.Request(source['url'],headers={'User-Agent':'Mozilla/5.0 (compatible; WGSS public-source collector)'})
  with urllib.request.urlopen(request,timeout=45) as response:
   content=response.read();result.update(http_status=response.status,resolved_url=response.url,content_type=response.headers.get('Content-Type'))
  sha=hashlib.sha256(content).hexdigest();directory=storage/sid/sha;directory.mkdir(parents=True,exist_ok=True)
  (directory/'source.html').write_bytes(content);soup=BeautifulSoup(content,'html.parser')
  for el in soup(['script','style','nav','footer','header']):el.decompose()
  text=' '.join(soup.get_text(' ',strip=True).split());(directory/'normalized.txt').write_text(text)
  normalized_sha=hashlib.sha256(text.encode()).hexdigest();previous=ROOT/'research/data-v10/source-texts'/(sid+'.normalized.txt')
  previous_text=previous.read_text().strip() if previous.exists() else None
  result.update(sha256=sha,normalized_text_sha256=normalized_sha,revision_state='unchanged' if source.get('sha256')==sha else 'needs_reassessment',text_revision_state='unchanged' if previous_text==text else 'changed' if previous_text is not None else 'no_prior_text',snapshot_path=str(directory))
  # A fresh check is a separate event; previous revision and check metadata survive.
  (directory/('check-'+now.replace(':','-')+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 except (OSError,urllib.error.URLError) as exc:result.update(revision_state='unreachable',error=str(exc),http_status=getattr(exc,'code',None))
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',action='append',default=[]);p.add_argument('--storage',type=Path,default=ROOT/'research/source-store/provider-revisions');args=p.parse_args()
 sources=json.loads((ROOT/'dist/data/library.json').read_text())['sources'];known={s['id'] for s in sources}
 if set(args.source)-known:p.error('Unknown source ID: '+','.join(sorted(set(args.source)-known)))
 selected=[s for s in sources if not args.source or s['id'] in args.source];args.storage.mkdir(parents=True,exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(lambda s:collect(s,args.storage),selected))
 report={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'automatic_promotion':False,'results':results}
 stamp=report['checked_at'].replace(':','-');(args.storage/('run-'+stamp+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps([{'source_id':r['source_id'],'revision_state':r['revision_state'],'http_status':r.get('http_status')} for r in results],ensure_ascii=False))
if __name__=='__main__':main()
