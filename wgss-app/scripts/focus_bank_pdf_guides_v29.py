"""One-time visual curation: display financial panels first, preserve original page bytes."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
rootpath=R/'data/bank-ui-collection-v29-decisions.json';root=read(rootpath);assert not root.get('visual_layout_corrections')
p=R/'data/bank-ui-benchmark-dispositions.json';bank=read(p);changes=[]
for id,box in [('BANK-BENCH-196',None),('BANK-BENCH-197',[110,900,470,1085]),('BANK-BENCH-198',None)]:
 b=next(x for x in bank['examples'] if x['id']==id);first=b['screen_evidence'];nextscreen=b['additional_screen_evidence'][0];assert first['pdf_page']==1 and nextscreen['pdf_page']==2
 if box:nextscreen['display_region']=dict(bbox_xyxy=box,original_width=953,original_height=1348,review='root_visual_checked')
 b['screen_evidence']=nextscreen;b['additional_screen_evidence']=[first]
 changes.append(dict(example_id=id,root_decision='display_financial_input_panel_first',original_page_bytes_preserved=True,first_page=2,additional_page=1,display_region=nextscreen['display_region'],automatic_adoption=False))
root['visual_layout_corrections']=changes;write(p,bank);write(rootpath,root)
print({'focused_pdf_reference_panels':3,'new_images_or_cases':0})
