"""Stage root-selected official PDF pages; a render is not an observed app screen."""
import argparse,datetime,hashlib,json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
import pymupdf as fitz
R=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);a=p.parse_args();run=a.run_dir.resolve();assert not (run/'FROZEN').exists();rows=[]
 for target in json.loads((run/'targets.json').read_text()):
  assert target['root_source_reviewed'] and urlparse(target['url']).scheme=='https'
  with urlopen(Request(target['url'],headers={'User-Agent':'Mozilla/5.0 (WGSS official guide research)'}),timeout=35) as response:
   assert urlparse(response.url).hostname in target['allowed_hosts'];raw=response.read();url=response.url
  assert raw.startswith(b'%PDF-');sha=hashlib.sha256(raw).hexdigest();folder=run/'sources'/target['id']/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.pdf').write_bytes(raw);doc=fitz.open(stream=raw,filetype='pdf');assert not doc.needs_pass
  pages=[];texts=[]
  for i,page in enumerate(doc):
   text=' '.join(page.get_text().split());texts.append(text)
   if i+1 not in target['page_numbers']:continue
   output=folder/('page-'+str(i+1)+'.png');page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False).save(output);pages.append({'page_number':i+1,'image_path':str(output.relative_to(R)),'image_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'derivation':'official_pdf_page_render','render_scale':2,'observed_app_screen':False,'root_visual_review':'pending'})
  assert len(pages)==len(target['page_numbers']);text=' '.join(texts);(folder/'normalized.txt').write_text(text);rows.append(dict(target,resolved_url=url,source_sha256=sha,text_sha256=hashlib.sha256(text.encode()).hexdigest(),pages=pages,pdf_page_count=len(doc),snapshot_path=str(folder.relative_to(R)),collected_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),automatic_adoption=False));doc.close()
 (run/'pdf-captures.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(run/'FROZEN').write_text('Source PDF and render bytes frozen; no automatic work mapping.\n')
 print(json.dumps({'official_pdfs_staged':len(rows),'page_renders':sum(len(x['pages']) for x in rows),'observed_app_screens':0}))
if __name__=='__main__':main()
