"""Freeze original guide assets and unmodified PDF page renders for visual review."""
import json,hashlib,concurrent.futures
from pathlib import Path
from urllib.request import urlopen,Request
from PIL import Image
import pymupdf
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/bank-gap-collection-v30-20261012';RUN=R/'research/source-store/bank-gap-assets-v30-20261012'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();sources=read(SRC/'sources.json');assets=[]
s=next(x for x in sources if x['id']=='gb-natwest-facflow')
for a in s['images']:
 if a['ordinal'] not in [7,9,13,14,15,16,17,18,20]:continue
 raw=urlopen(Request(a['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read();sha=hashlib.sha256(raw).hexdigest();p=RUN/'original-images'/(sha+'.png');p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);im=Image.open(p);assets.append(dict(id='natwest-img-'+str(a['ordinal']),source_id='S30:'+s['id'],source_url=s['url'],asset_url=a['url'],native_ordinal=a['ordinal'],image_sha256=sha,width=im.width,height=im.height,private_path=str(p.relative_to(R)),image_derivation='original_official_guide_asset',financial_ui_visual_review='pending',observed_app=False))
for id in ['hk-empf-invest-web','hk-empf-invest-app','hk-empf-contribution-web','hk-empf-withdrawal-web','hk-hsbc-tradepay']:
 s=next(x for x in sources if x['id']==id);doc=pymupdf.open(R/s['snapshot_path']/'source.pdf')
 for i,page in enumerate(doc):
  if i<2:continue # cover/preface/contents not financial screenshots
  pix=page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6));p=RUN/'pdf-pages'/id/(str(i+1)+'.png');p.parent.mkdir(parents=True,exist_ok=True);pix.save(p);raw=p.read_bytes();assets.append(dict(id=id+'-page-'+str(i+1),source_id='S30:'+s['id'],source_url=s['url'],page=i+1,raw_pdf_sha256=s['raw_sha256'],image_sha256=hashlib.sha256(raw).hexdigest(),width=pix.width,height=pix.height,render_scale=1.6,private_path=str(p.relative_to(R)),image_derivation='original_official_pdf_page_render',financial_ui_visual_review='pending',observed_app=False))
write(RUN/'assets.json',assets);(RUN/'FROZEN').write_text('Raw inventory only. Each financial function and UI reference requires root visual admission.\n');print({'asset_inventory':len(assets)})
