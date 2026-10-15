import json,hashlib,datetime
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path('/home/ubuntu/wgss-prototype');m=json.loads((ROOT/'dist/data/wording-metadata-v45.json').read_text());reviews=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def n(s):return ' '.join(s.split()).replace('’',"'").lower()
for version,prefix,source,provider in [('v38','ON-CITI-ONLINE-ENROLLMENT-',Path('/home/ubuntu/wgss-v38-onboarding-collection/citi-register-stable.html'),'citi'),('v42','PUB42-dbs-account-entry-',Path('/home/ubuntu/wgss-v42-public-expansion/followup/raw/dbs-account-entry.html'),'dbs')]:
 assert source.exists(),source
 s=BeautifulSoup(source.read_text(),'html.parser')
 for w in json.loads((ROOT/f'dist/data/wording-references-{version}.json').read_text())['items']:
  if not w['id'].startswith(prefix):continue
  matches=[e for e in s.find_all(['label','span','div','h1','h2','h3','button','a','p']) if n(e.get_text(' ',strip=True))==n(w['label'])];matches.sort(key=lambda e:len(str(e)))
  assert matches,w['id'];e=matches[0]
  ev={'word_id':w['id'],'image_sha256':sha(ROOT/'dist'/w['image_path']),'source_html_sha256':sha(source),'source_file':str(source),'literal_label':w['label'],'dom_proof':str(e)[:900],'visual_reviewed':True,'visual_judgment':'Original directly inspected. Citi says enter the account or card number provided when your account was opened; DBS says open an account first on digibank app if none. Therefore existing customer registration, not new bank account application. Step labels Verification/Confirmation describe later steps and are not evidence of executed verification/completion.','reviewer':'worker B / data_rework_v45','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_view_href':w['view_href'],'model_images_provided':False}
  o={'provider_id':provider,'task_id':'signup','purpose_code':'existing-customer-registration','stage_code':'registration-input','evidence':ev};m['overrides'][w['id']]=o;reviews.append({'id':w['id'],'overlay':o})
allold=[w for v in ['v38','v42'] for w in json.loads((ROOT/f'dist/data/wording-references-{v}.json').read_text())['items']];m['unclassified_word_ids']=[w['id'] for w in allold if w['id'] not in m['overrides'] and not w.get('purpose_code')];m['legacy_purpose_reviewed_records']=len(reviews)
(ROOT/'dist/data/wording-metadata-v45.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));(ROOT/'research/public-flow-v45/legacy-purpose-review-v45.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2));print('legacy reviewed',len(reviews),'unclassified',len(m['unclassified_word_ids']))
