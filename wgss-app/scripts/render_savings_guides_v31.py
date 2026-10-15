"""Render full original public PDF pages; no visual admission by page inventory."""
import json,hashlib
from pathlib import Path
import pymupdf
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/savings-assets-v31-20261012'
assert not (RUN/'FROZEN').exists();ss=json.loads((R/'research/source-store/savings-collection-v31-20261012/sources.json').read_text());out=[]
for s in ss:
 if s['id'] not in ['hk-placement-app','hk-placement-web']:continue
 doc=pymupdf.open(R/s['snapshot_path']/s['raw_filename'])
 for i,page in enumerate(doc):
  aid=s['id']+'-page-'+str(i+1);f=RUN/'renders'/f'{aid}.png';f.parent.mkdir(parents=True,exist_ok=True);pix=page.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6));pix.save(f)
  out.append(dict(id=aid,source_id='S31:'+s['id'],source_url=s['url'],private_path=str(f.relative_to(R)),image_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),raw_pdf_sha256=s['raw_sha256'],page=i+1,render_scale=1.6,width=pix.width,height=pix.height,image_derivation='original_official_pdf_page_render'))
(RUN/'assets.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(RUN/'FROZEN').write_text('9 original whole PDF pages staged; no automatic visual admission.\n');print([(s['id'],[(p['page'],p['text'][:130]) for p in s['pdf_pages']]) for s in ss if s['id'].startswith('hk-placement')])
