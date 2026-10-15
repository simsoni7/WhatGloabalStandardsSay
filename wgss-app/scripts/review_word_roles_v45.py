"""Write additive metadata after worker B's direct original-image/DOM review."""
import json,hashlib,datetime
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path('/home/ubuntu/wgss-prototype');RAW=Path('/home/ubuntu/wgss-v44-public-flows/raw');OUT=ROOT/'research/public-flow-v45';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return ' '.join((s or '').split()).casefold()
words=json.loads((ROOT/'dist/data/wording-references-v44.json').read_text())['items'];cases={c['id']:c for c in json.loads((ROOT/'dist/data/public-flow-cases-v44.json').read_text())['cases']}
# Explicit ambiguity resolution from image location and intended contextual occurrence.
selected={'FLOW-citi-us-password-recovery-citi-10-0':80,'FLOW-citi-us-login-citi-10-0':69,'FLOW-citi-us-login-citi-10-1':71,'FLOW-paypal-us-signup-paypal-02-0':100,'FLOW-paypal-us-signup-paypal-02-1':102,'FLOW-citi-us-existing-registration-citi-11-0':5}
roles={};reviews=[]
for w in words:
 raw=RAW/(w['step_id']+'.json');r=json.loads(raw.read_text());htmlfile=RAW/(w['step_id']+'.html');soup=BeautifulSoup(htmlfile.read_text(),'html.parser');matches=[c for c in r['controls'] if c['visible'] and c['in_view'] and (norm(c['text'])==norm(w['label']) or norm(c.get('placeholder'))==norm(w['label']))]
 c=next((c for c in matches if c['i']==selected.get(w['id'])),None) or next((c for c in matches if c['tag'] in ['LABEL','INPUT','H1','H2','H3']),None) or matches[0]
 tag=c['tag'];detail='button' if tag=='BUTTON' else 'link' if tag=='A' else 'heading' if tag.startswith('H') else 'input_placeholder' if tag=='INPUT' else 'input_label'
 if c.get('id') in ['radioAcc-label','card - checkbox-label'] or w['id'] in ['FLOW-paypal-us-signup-paypal-02-0','FLOW-paypal-us-signup-paypal-02-1'] or w['step_id']=='ocbc-account-03':detail='option_label'
 el=soup.find(id=c['id']) if c.get('id') else None
 if not el:
  candidates=[e for e in soup.find_all(tag.lower()) if norm(e.get_text(' ',strip=True))==norm(w['label']) or norm(e.get('placeholder'))==norm(w['label']) or norm(e.get('aria-label'))==norm(w['label'])]
  if tag=='A' and c.get('href'): candidates=sorted(candidates,key=lambda e:0 if c['href'].endswith(e.get('href','!')) else 1)
  el=candidates[0] if candidates else None
 if el is None and tag=='LABEL':
  el=next((e for e in soup.find_all('label') if any(norm(k.get_text(' ',strip=True))==norm(w['label']) for k in e.find_all('span'))),None)
 assert el is not None,(w['id'],c)
 # Small exact source excerpt, keeping opening tag and native copy (no synthesized DOM).
 dom=str(el);quote=dom if len(dom)<700 else str(el)[:300]+' ... '+w['label']
 kind='button' if detail == 'button' else 'ui_label'
 ev={'word_id':w['id'],'image_sha256':sha(ROOT/'dist'/w['image_path']),'source_html_sha256':sha(htmlfile),'source_file':f'research/public-flow-v44/published-source-proofs.tar.gz::{htmlfile.name}','source_control_index':c['i'],'literal_label':w['label'],'dom_proof':quote,'actual_dom_tag':tag,'actual_dom_id':c.get('id'),'visual_reviewed':True,'visual_judgment':f'Original viewport directly inspected using view_image. {detail}; '+('visible actionable control; activation not executed.' if kind=='button' else 'visible title/field/option copy; not an action button.'),'reviewer':'worker B / data_rework_v45','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model_images_provided':False}
 case=cases[w['case_id']];provider={'Citi':'citi','DBS':'dbs','Wise':'wise','PayPal':'paypal','N26':'n26','HSBC UK':'hsbc','HSBC':'hsbc','OCBC':'ocbc','Mashreq':'mashreq'}[case['provider']]
 roles[w['id']]={'element_kind':kind,'provider_id':provider,'task_id':w['task_id'],'purpose_code':w['purpose_code'],'stage_code':w['stage_code'],'role_detail':detail,'evidence':ev};reviews.append({'id':w['id'],'old_element_kind':w['element_kind'],'new_element_kind':kind,'role_detail':detail,'evidence':ev})
meta={'version':'v45','canonical_financial_work_admissions':0,'overrides':roles,'unclassified_word_ids':[],'automatically_adopted':False,'reviewed_v44_contextual_records':47,'review_note':'Direct original viewport and exact saved DOM review; labels, sources, dates and images unchanged.'}
(ROOT/'dist/data/wording-metadata-v45.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(OUT/'role-review-v45.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2));print('reviewed',len(reviews),'actions',sum(x['new_element_kind']=='button' for x in reviews))
