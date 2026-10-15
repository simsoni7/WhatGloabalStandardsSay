"""Collect public, official screen evidence. Never logs in or submits a financial action.

Original source files, hashes and OCR live in a local SQLite store. Publishing
requires annotations tied to the exact screenshot hash; changed captures stay
pending. This is a manual collection batch, not a background scheduler.
"""
import argparse
import datetime
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen

import pymupdf
from bs4 import BeautifulSoup
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT/'research/capture-store'
PUBLIC = ROOT/'dist/evidence'
ALLOWED = {'payinfo.or.kr','www.citi.com','monzo.com','images.ctfassets.net','wise.com'}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read_json(path): return json.loads(path.read_text())
def fetch(url):
    if urlparse(url).scheme!='https' or urlparse(url).hostname not in ALLOWED:
        raise ValueError('URL is outside the reviewed official source allowlist')
    with urlopen(Request(url,headers={'User-Agent':'WGSS public UI research/0.1'}),timeout=45) as r:
        if urlparse(r.url).hostname not in ALLOWED: raise ValueError('Unreviewed redirect')
        return r.read(),r.url
def connect():
    STORE.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(STORE/'captures.sqlite3')
    db.row_factory=sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS captures (
        target_id TEXT NOT NULL, image_sha256 TEXT NOT NULL, source_sha256 TEXT NOT NULL,
        first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, metadata TEXT NOT NULL,
        annotation TEXT, PRIMARY KEY(target_id,image_sha256))''')
    db.execute('''CREATE TABLE IF NOT EXISTS attempts (
        target_id TEXT NOT NULL, attempted_at TEXT NOT NULL, status TEXT NOT NULL, reason TEXT)''')
    return db
def capture(target,page):
    raw,final_url=fetch(target['source_url'])
    source_hash=sha(raw)
    original=STORE/(source_hash+('.pdf' if target['method']=='pdf_image' else '.html'))
    original.write_bytes(raw)
    metadata={'target_id':target['id'],'source_url':target['source_url'],'resolved_source_url':final_url,
              'source_sha256':source_hash,'source_original_path':str(original.relative_to(ROOT)),
              'capture_method':target['method'],'source_locator':target['locator']}
    if target['method']=='image':
        asset=target['asset_url']
        linked_images={urljoin(final_url,i.get('src','')) for i in BeautifulSoup(raw,'html.parser').select('img[src]')}
        if asset not in linked_images: raise ValueError('Asset URL is not present in the official source page')
        image_bytes,asset_final=fetch(asset)
        metadata.update(original_asset_sha256=sha(image_bytes),asset_url=asset_final)
        ext=Path(urlparse(asset).path).suffix.lstrip('.')
        asset_path=STORE/(sha(image_bytes)+'.'+ext);asset_path.write_bytes(image_bytes)
        metadata['original_asset_path']=str(asset_path.relative_to(ROOT))
        if ext=='avif':
            # Rasterize the unmodified official image through Chromium for PNG support.
            page.set_content('<img style="display:block" src="'+asset+'">')
            page.wait_for_function('document.querySelector("img").complete && document.querySelector("img").naturalWidth>0')
            image_bytes=page.locator('img').screenshot()
            ext='png';metadata['image_derivation']='Chromium rendering of the original image; no content edits'
        else: metadata['image_derivation']='original published image bytes'
    elif target['method']=='pdf_image':
        doc=pymupdf.open(stream=raw,filetype='pdf');pdf_page=doc[target['page_index']]
        images=pdf_page.get_images()
        selected=[x for x in images if x[2]==target['image_width'] and x[3]==target['image_height']]
        if len(selected)!=1: raise ValueError('PDF screenshot selector changed; review the page again')
        img=doc.extract_image(selected[0][0]);image_bytes=img['image'];ext=img['ext']
        metadata.update(pdf_page=target['page_index']+1,pdf_xref=selected[0][0],pdf_metadata=doc.metadata,
                        image_derivation='unmodified embedded screenshot extracted from official PDF')
    elif target['method']=='live_web':
        page.set_viewport_size(target['viewport'])
        response=page.goto(target['source_url'],wait_until='domcontentloaded',timeout=45000)
        if not response or response.status!=200 or urlparse(page.url).hostname not in ALLOWED:
            raise ValueError('Public page did not load normally; no bypass attempted')
        page.locator('#source-input').wait_for()
        element=page.locator(target['selector'])
        if element.count()!=1: raise ValueError('Live UI selector no longer identifies one component')
        # Re-read the actual rendered source used for this capture.
        dom=page.content().encode();source_hash=sha(dom);original=STORE/(source_hash+'.html');original.write_bytes(dom)
        image_bytes=element.screenshot();ext='png'
        metadata.update(source_sha256=source_hash,source_original_path=str(original.relative_to(ROOT)),
                        resolved_source_url=page.url,viewport=target['viewport'],browser=page.context.browser.version,
                        locale='en-US',dom_labels=element.inner_text()[:1800],
                        input_values=element.locator('input').evaluate_all('(els)=>els.map(e=>({id:e.id,value:e.value}))'),
                        image_derivation='direct capture of the public live calculator; no form submitted')
    else: raise ValueError('Unsupported capture method')
    image_hash=sha(image_bytes);path=STORE/'images'/(image_hash+'.'+ext);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(image_bytes)
    image=Image.open(path);metadata.update(image_path='evidence/'+path.name,image_local_path=str(path.relative_to(ROOT)),image_sha256=image_hash,
                                           width=image.width,height=image.height)
    ocr=subprocess.run(['tesseract',str(path),'stdout','-l',target['ocr_languages'],'--psm','11'],capture_output=True,text=True,timeout=35)
    if ocr.returncode!=0: raise ValueError('OCR failed; no labels approved')
    metadata['ocr_text']=ocr.stdout
    return metadata
def collect(ids=None):
    targets=read_json(ROOT/'research/screen-targets.json');db=connect()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1400,'height':1000},locale='en-US')
        page=context.new_page()
        for target in targets:
            if ids and target['id'] not in ids: continue
            try:
                m=capture(target,page);timestamp=now()
                db.execute('''INSERT INTO captures VALUES (?,?,?,?,?,?,NULL)
                    ON CONFLICT(target_id,image_sha256) DO UPDATE SET last_seen_at=excluded.last_seen_at,
                    source_sha256=excluded.source_sha256,metadata=excluded.metadata''',
                    (target['id'],m['image_sha256'],m['source_sha256'],timestamp,timestamp,json.dumps(m,ensure_ascii=False)))
                db.execute('INSERT INTO attempts VALUES (?,?,?,?)',(target['id'],timestamp,'captured',None));db.commit()
                print(json.dumps({'id':target['id'],'status':'captured_pending_review','image_sha256':m['image_sha256'],'image_path':m['image_path']},ensure_ascii=False),flush=True)
            except Exception as e:
                # No tokens, cookies, authenticated storage or response bodies in logs.
                db.execute('INSERT INTO attempts VALUES (?,?,?,?)',(target['id'],now(),'failed',type(e).__name__));db.commit()
                print(json.dumps({'id':target['id'],'status':'failed','error_type':type(e).__name__}),flush=True)
        browser.close()
def export():
    db=connect();annotations=read_json(ROOT/'research/screen-annotations.json');records=[];pending=[]
    for t in read_json(ROOT/'research/screen-targets.json'):
        row=db.execute('SELECT * FROM captures WHERE target_id=? ORDER BY last_seen_at DESC LIMIT 1',(t['id'],)).fetchone()
        if not row: pending.append({'target_id':t['id'],'reason':'not_captured'});continue
        a=annotations.get(t['id']);m=json.loads(row['metadata'])
        if not a or a.get('reviewed_image_sha256')!=row['image_sha256']:
            pending.append({'target_id':t['id'],'reason':'exact_image_review_required'});continue
        local_path=ROOT/m.get('image_local_path','dist/'+m['image_path'])
        raw=local_path.read_bytes()
        if sha(raw)!=row['image_sha256']: raise ValueError('Screenshot hash mismatch')
        PUBLIC.mkdir(parents=True,exist_ok=True);(ROOT/'dist'/m['image_path']).write_bytes(raw)
        public={k:v for k,v in m.items() if k in {'target_id','source_url','resolved_source_url','source_sha256','asset_url','original_asset_sha256','source_locator','capture_method','image_derivation','image_path','image_sha256','width','height','pdf_page','viewport','browser','locale'}}
        public.update(a,observed_at=row['first_seen_at'],last_checked_at=row['last_seen_at'])
        public.pop('reviewed_image_sha256');public['reviewed_image_sha256']=row['image_sha256']
        db.execute('UPDATE captures SET annotation=? WHERE target_id=? AND image_sha256=?',(json.dumps(a,ensure_ascii=False),t['id'],row['image_sha256']))
        records.append(public)
    db.commit();db.close()
    out={'version':'0.1.0','collected_at':now(),'records':records,'pending':pending,
         'independent_human_review':False,'authenticated_app_captures':0}
    (ROOT/'dist/data/screen-evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'published':len(records),'pending':len(pending)}))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['collect','export']);parser.add_argument('--targets',nargs='*');args=parser.parse_args()
    collect(args.targets) if args.action=='collect' else export()
