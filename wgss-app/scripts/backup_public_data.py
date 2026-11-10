"""Back up approved public records and exact images using Python's standard library.
No credentials, intake proposals, private originals or operational logs are read.
"""
import argparse, concurrent.futures, datetime as dt, gzip, hashlib, json, os, re, time
from pathlib import Path
import urllib.parse, urllib.request

API='https://wgss-public-intake.booknfoto461.chatgpt.site/api/wgss'
ROOT=Path(__file__).resolve().parents[1]

def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def atomic(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(raw);os.replace(tmp,path)

def fetch(url):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args):raise ValueError('backup_redirect_rejected')
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'WGSS-PublicBackup/1.0','Origin':'https://3.36.58.188'})
            with urllib.request.build_opener(NoRedirect()).open(request,timeout=45) as response:
                raw=response.read(32*1024*1024+1)
                if len(raw)>32*1024*1024:raise ValueError('backup_response_too_large')
                return raw
        except Exception:
            if attempt==2:raise
            time.sleep(2**attempt)

def public_records(raw):
    data=json.loads(raw)
    if not isinstance(data.get('items'),list) or not isinstance(data.get('providers'),list):raise ValueError('backup_invalid_public_response')
    items=[]
    for row in data['items']:
        if row.get('type') not in {'screens','terms','phrases','features'} or not row.get('targetId') or not isinstance(row.get('patch'),dict):raise ValueError('backup_invalid_record')
        items.append({k:row[k] for k in ['type','targetId','revision','patch','appliedVersions','appliedAt'] if k in row})
    providers=[{k:r[k] for k in ['id','name','kind','sourceUrl','aliases','origin'] if k in r} for r in data['providers']]
    return {'items':sorted(items,key=lambda r:(r['type'],r['targetId'])),'providers':sorted(providers,key=lambda r:r['id'])}

def image_ext(raw):
    if raw.startswith(b'\x89PNG\r\n\x1a\n'):return 'png'
    if raw.startswith(b'\xff\xd8\xff'):return 'jpg'
    if raw[:4]==b'RIFF' and raw[8:12]==b'WEBP':return 'webp'
    raise ValueError('backup_invalid_image')

def backup(destination,api=API,get=fetch):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    data=public_records(get(api+'?resource=publications'))
    versions={}
    def history(row):
        url=api+'?resource=recordVersions&type=screens&id='+urllib.parse.quote(row['targetId'],safe='')
        result=json.loads(get(url))['items']
        if not isinstance(result,list):raise ValueError('backup_invalid_history')
        return row['targetId'],result
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for key,rows in pool.map(history,[r for r in data['items'] if r['type']=='screens']):versions[key]=rows
    data['versions']=versions
    digest=sha(encoded(data));old_path=destination/'manifest.json'
    if old_path.exists() and json.loads(old_path.read_text()).get('contentSha256')==digest:
        return {**verify(destination),'changed':False}
    image_ids={}
    for fields in [r['patch'] for r in data['items']]+[r['fields'] for history in versions.values() for r in history]:
        fid,expected=fields.get('imageFileId'),fields.get('originalSha')
        if not fid:continue
        if not re.fullmatch(r'[0-9a-f-]{36}',fid) or not re.fullmatch('[0-9a-f]{64}',expected or ''):raise ValueError('backup_image_identity_missing')
        if fid in image_ids and image_ids[fid]!=expected:raise ValueError('backup_image_identity_conflict')
        image_ids[fid]=expected
    def download(pair):
        fid,expected=pair
        cached=list((destination/'assets').glob(expected+'.*')) if (destination/'assets').exists() else []
        raw=cached[0].read_bytes() if cached else get(api+'?resource=file&id='+urllib.parse.quote(fid))
        if sha(raw)!=expected:raise ValueError('backup_image_hash_mismatch')
        relative='assets/'+expected+'.'+image_ext(raw);atomic(destination/relative,raw)
        return fid,{'path':relative,'sha256':expected,'bytes':len(raw)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:assets=dict(pool.map(download,image_ids.items()))
    # An approval during export invalidates the snapshot; retry next time instead of mixing versions.
    if public_records(get(api+'?resource=publications'))!={k:data[k] for k in ['items','providers']}:raise ValueError('backup_source_changed_during_export')
    snapshot={**data,'exportedAt':dt.datetime.now(dt.timezone.utc).isoformat(),'backendBase':api.rsplit('/api/',1)[0],'liveUpdates':True}
    payload=gzip.compress(encoded(snapshot),mtime=0)
    counts={kind:sum(r['type']==kind for r in data['items']) for kind in ['screens','terms','phrases','features']}
    manifest={'schema':'wgss-public-backup/v1','exportedAt':snapshot['exportedAt'],'contentSha256':digest,'snapshotSha256':sha(payload),'snapshot':'publications.json.gz','counts':counts,'assets':assets}
    atomic(destination/'publications.json.gz',payload);atomic(old_path,encoded(manifest)+b'\n')
    return {**verify(destination),'changed':True}

def verify(destination):
    destination=Path(destination);manifest=json.loads((destination/'manifest.json').read_text());raw=(destination/'publications.json.gz').read_bytes()
    if sha(raw)!=manifest['snapshotSha256']:raise ValueError('backup_snapshot_hash_mismatch')
    data=json.loads(gzip.decompress(raw))
    if sha(encoded({k:data[k] for k in ['items','providers','versions']}))!=manifest['contentSha256']:raise ValueError('backup_content_hash_mismatch')
    expected={}
    for fields in [r['patch'] for r in data['items']]+[r['fields'] for rows in data['versions'].values() for r in rows]:
        if fields.get('imageFileId'):expected[fields['imageFileId']]=fields['originalSha']
    if set(expected)!=set(manifest['assets']):raise ValueError('backup_image_coverage_missing')
    for fid,item in manifest['assets'].items():
        if not re.fullmatch(r'assets/[0-9a-f]{64}\.(png|jpg|webp)',item['path']):raise ValueError('backup_unsafe_path')
        raw=(destination/item['path']).read_bytes()
        if sha(raw)!=item['sha256'] or sha(raw)!=expected[fid] or len(raw)!=item['bytes']:raise ValueError('backup_image_hash_mismatch')
    return {'verified':True,'counts':manifest['counts'],'images':len(expected),'exportedAt':manifest['exportedAt']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--destination',type=Path,default=ROOT/'source-data/runtime-backup');parser.add_argument('--api',default=API);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if urllib.parse.urlsplit(args.api).scheme!='https':raise SystemExit('HTTPS public API required')
    print(json.dumps(verify(args.destination) if args.verify_only else backup(args.destination,args.api),ensure_ascii=False))
