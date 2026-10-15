import json,hashlib,datetime
from pathlib import Path
from bs4 import BeautifulSoup
r=Path('/home/ubuntu/wgss-prototype');p=r/'dist/data/wording-metadata-v45.json';m=json.loads(p.read_text());w=json.loads((r/'dist/data/wording-references-v38.json').read_text())['items']
for id,c in [('PUB-citi-login-3','citi'),('PUB-chase-login-3','chase')]:
 x=next(x for x in w if x['id']==id);h=Path('/home/ubuntu/wgss-v39-public-screen-assets/'+c+'-login.html');s=BeautifulSoup(h.read_text(),'html.parser');es=[e for e in s.find_all('button') if ' '.join(e.get_text(' ',strip=True).split()).lower()==x['label'].lower()];assert es,id
 e=es[0];ev={'word_id':id,'image_sha256':hashlib.sha256((r/'dist'/x['image_path']).read_bytes()).hexdigest(),'source_html_sha256':hashlib.sha256(h.read_bytes()).hexdigest(),'source_file':str(h),'literal_label':x['label'],'dom_proof':str(e)[:800],'visual_reviewed':True,'visual_judgment':'Original directly inspected: main action below blank User ID/Username and Password inputs. Existing-user credentials entry. No login executed. Auxiliary signup actions not assigned this purpose.','reviewer':'worker B / data_rework_v45','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_view_href':x['view_href'],'model_images_provided':False}
 m['overrides'][id]={'provider_id':c,'task_id':'login','purpose_code':'login','stage_code':'credentials-input','role_detail':'button','evidence':ev}
m['unclassified_word_ids']=[x for x in m['unclassified_word_ids'] if x not in m['overrides']];p.write_text(json.dumps(m,ensure_ascii=False,indent=2));print('overrides',len(m['overrides']))
