"""Freeze reviewed public targets; HTTP success never admits a benchmark claim."""
import argparse, concurrent.futures, datetime, hashlib, json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
def digest(raw): return hashlib.sha256(raw).hexdigest()
def collect(target, directory):
    directory=directory.resolve()
    result = {**target, 'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'automatic_adoption': False, 'semantic_review': 'pending'}
    try:
        assert urlparse(target['url']).scheme == 'https'
        request = Request(target['url'], headers={'User-Agent': 'Mozilla/5.0 (compatible; WGSS public-source research)'})
        with urlopen(request, timeout=45) as response:
            raw = response.read(); final = response.url
            allowed_hosts={urlparse(target['url']).hostname, *target.get('reviewed_redirect_hosts',[])}
            assert urlparse(final).hostname in allowed_hosts
            result.update(http_status=response.status, resolved_url=final, content_type=response.headers.get('Content-Type'))
        soup = BeautifulSoup(raw, 'html.parser')
        links=[{'url':urljoin(final,a['href']),'label':' '.join(a.stripped_strings)} for a in soup.select('a[href]')]
        images = [{'url':urljoin(final, el.get('src', '')), 'alt':el.get('alt', ''), 'ordinal':i}
                  for i, el in enumerate(soup.select('img[src]'))]
        # Retain native table cells, not flattened responsive duplicates or inferred ticks.
        tables = [[[' '.join(cell.stripped_strings) for cell in row.find_all(['th','td'])]
                   for row in table.select('tr')] for table in soup.select('table')]
        for el in soup(['script','style']): el.decompose()
        text = ' '.join(soup.get_text(' ',strip=True).split())
        folder = directory/'sources'/target['id']/digest(raw); folder.mkdir(parents=True, exist_ok=True)
        (folder/'source.html').write_bytes(raw); (folder/'normalized.txt').write_text(text)
        result.update(raw_sha256=digest(raw), text_sha256=digest(text.encode()), text=text,
                      images=images, links=links, tables=tables, snapshot_path=str(folder.relative_to(ROOT)), state='fetched_pending_review')
    except Exception as exc:
        result.update(state='fetch_failed', error_type=type(exc).__name__, http_status=getattr(exc,'code',None))
    return result
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,required=True);args=parser.parse_args()
    args.run_dir=args.run_dir.resolve()
    if (args.run_dir/'FROZEN').exists():
        parser.error('This source batch is frozen. Use a new run directory for revisions.')
    targets=json.loads((args.run_dir/'targets.json').read_text());args.run_dir.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda t:collect(t,args.run_dir),targets))
    output=args.run_dir/'sources.json'
    if output.exists():
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        output.rename(args.run_dir/('sources-prior-'+stamp+'.json'))
    output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([{'id':r['id'],'state':r['state'],'http_status':r.get('http_status'), 'characters':len(r.get('text',''))} for r in rows],ensure_ascii=False))
if __name__=='__main__': main()
