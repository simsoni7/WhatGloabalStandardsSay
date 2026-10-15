# One-time v29 recorder/preparer. Already executed; frozen files must not be overwritten.
import json,hashlib,time
from pathlib import Path
from urllib.request import urlopen,Request
from PIL import Image
import pymupdf
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/bank-screen-expansion-v29-20261012';RUN=R/'research/source-store/bank-screen-assets-v29-20261012';assert not (RUN/'FROZEN').exists();RUN.mkdir(exist_ok=True);ss=json.loads((SRC/'sources.json').read_text());assets=[]
for s in ss:
 if s['state']!='fetched_pending_review':continue
 # New insurer PDF pages and current available investment web-flow PDFs.
 if s['id'].startswith('gb-fidelity-pdf') or s['id']=='hk-hsbclife-healthplus':
  doc=pymupdf.open(R/s['snapshot_path']/'source.pdf')
  for i,p in enumerate(doc):
   pix=p.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6));raw=pix.tobytes('png');sha=hashlib.sha256(raw).hexdigest();out=RUN/'pdf-pages'/s['id']/f'{i+1}.png';out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);assets.append({'id':s['id']+'-page-'+str(i+1),'source_id':'S29:'+s['id'],'source_url':s['url'],'page':i+1,'raw_pdf_sha256':s['raw_sha256'],'image_sha256':sha,'width':pix.width,'height':pix.height,'render_scale':1.6,'image_derivation':'original_official_pdf_page_render','private_path':str(out.relative_to(R)),'financial_ui_visual_review':'pending','observed_app':False})
 if s['id']=='kr-shinhan-openbank':
  seen=set()
  for im in s['images']:
   # Full tutorial bodies have imgXX names. Exclude header/footer/button/QR
   # assets. Every selected original still needs explicit visual adjudication.
   if '_opbk_img' not in im['url'] or im['url'] in seen:continue
   seen.add(im['url'])
   try:
    raw=urlopen(Request(im['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read();sha=hashlib.sha256(raw).hexdigest();out=RUN/'guide-images'/(sha+'.png');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);w,h=Image.open(out).size;assets.append({'id':'shinhan-img-'+str(im['ordinal']),'source_id':'S29:'+s['id'],'source_url':s['url'],'asset_url':im['url'],'native_ordinal':im['ordinal'],'native_alt':im['alt'],'image_sha256':sha,'width':w,'height':h,'image_derivation':'original_official_guide_asset','private_path':str(out.relative_to(R)),'financial_ui_visual_review':'pending','observed_app':False});time.sleep(.12)
   except Exception as e:print('image',im['ordinal'],type(e).__name__,flush=True)
(RUN/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n');(RUN/'FROZEN').write_text('Original guideline image/PDF page assets; no automatic admission or installedapp observations.\n');print({'assets':len(assets),'guide_images':sum('native_ordinal' in x for x in assets),'pdf_pages':sum('page' in x for x in assets)},flush=True)
# Contact sheets are private visual QA, never publication evidence.
from PIL import ImageDraw
for family in ['shinhan','fidelity','healthplus']:
 rows=[x for x in assets if (family=='shinhan' and 'native_ordinal' in x) or (family=='fidelity' and 'fidelity' in x['id']) or (family=='healthplus' and 'healthplus' in x['id'])];cols=4;cellw=350;cellh=500;canvas=Image.new('RGB',(cols*cellw,((len(rows)+cols-1)//cols)*cellh),'white');draw=ImageDraw.Draw(canvas)
 for i,x in enumerate(rows):
  im=Image.open(R/x['private_path']);im.thumbnail((cellw-15,cellh-40));xx=(i%cols)*cellw;yy=(i//cols)*cellh;canvas.paste(im,(xx,yy+30));draw.text((xx+4,yy+3),x['id'],fill='black')
 canvas.save('/tmp/wgss-v29-'+family+'-sheet.png')
