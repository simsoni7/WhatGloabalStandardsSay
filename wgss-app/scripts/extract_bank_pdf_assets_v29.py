# One-time v29 recorder/preparer. Already executed; frozen files must not be overwritten.
import json,hashlib
from pathlib import Path
import pymupdf
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/bank-screen-expansion-v29-20261012';RUN=R/'research/source-store/bank-pdf-ui-v29-20261012';assert not (RUN/'FROZEN').exists();RUN.mkdir(exist_ok=True);assets=[]
for s in json.loads((SRC/'sources.json').read_text()):
 if not s['id'].startswith('gb-fidelity-pdf'):continue
 doc=pymupdf.open(R/s['snapshot_path']/'source.pdf')
 for i,p in enumerate(doc):
  for j,entry in enumerate(p.get_images(full=True)):
   xref=entry[0];im=doc.extract_image(xref)
   if im['width']<200 or im['height']<65:continue
   raw=im['image'];sha=hashlib.sha256(raw).hexdigest();out=RUN/'images'/s['id']/(sha+'.'+im['ext']);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);assets.append({'id':s['id']+'-p'+str(i+1)+'-x'+str(xref),'source_id':'S29:'+s['id'],'page':i+1,'xref':xref,'pdf_image_rectangles':[[r.x0,r.y0,r.x1,r.y1] for r in p.get_image_rects(xref)],'width':im['width'],'height':im['height'],'image_sha256':sha,'private_path':str(out.relative_to(R)),'extension':im['ext'],'image_derivation':'original_official_pdf_embedded_image','observed_app':False,'visual_review':'pending'})
(RUN/'assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n');(RUN/'FROZEN').write_text('Unmodified embedded PDF imagebytes, xref and original page mapping; pending financialUI visualreview.\n')
cols=4;cw=350;ch=300;canvas=Image.new('RGB',(cols*cw,((len(assets)+cols-1)//cols)*ch),'white');draw=ImageDraw.Draw(canvas)
for i,x in enumerate(assets):
 im=Image.open(R/x['private_path']);im.thumbnail((cw-10,ch-35));xx=(i%cols)*cw;yy=(i//cols)*ch;canvas.paste(im,(xx,yy+30));draw.text((xx+2,yy+2),x['id'],fill='black')
canvas.save('/tmp/wgss-v29-pdf-embedded-sheet.png');print({'embedded_images':len(assets)})
