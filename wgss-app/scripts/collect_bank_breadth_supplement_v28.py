import json,hashlib,datetime,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pymupdf
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-breadth-supplement-v28-20261012'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();sources=[]
url='https://www.business.hsbc.uk/en-gb/solutions/import-and-export-smartforms';raw=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read();sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/'uk-business-smartforms'/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.html').write_bytes(raw);soup=BeautifulSoup(raw,'html.parser');body=soup.find('main') or soup
for x in body.select('script,style,nav,header,footer'):x.decompose()
text=' '.join(body.get_text(' ',strip=True).split());(folder/'normalized.txt').write_text(text);s={'id':'uk-business-smartforms','provider_id':'hsbc-uk','country':'GB','language':'en-GB','url':url,'resolved_url':url,'http_status':200,'state':'fetched_pending_review','source_format':'official_html','raw_filename':'source.html','raw_sha256':sha,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text,'snapshot_path':str(folder.relative_to(R)),'images':[],'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'automatic_adoption':False};sources.append(s)
write(RUN/'form-links.json',[{'label':a.get_text(' ',strip=True),'url':urljoin(url,a['href'])} for a in body.select('a[href]') if any(q in a['href'].lower() for q in ['.pdf','form','application'])])
write(RUN/'sources.json',sources)
ws=read(R/'dist/data/bank-ui.json')['works'];base=read(R/'research/source-store/bank-breadth-additional-v28-20261012/inputs/v28-exact-uk-business-trade.json');jid='v28-exact-smartforms';write(RUN/'inputs'/(jid+'.json'),dict(base,id=jid,expected_ids=[s['id']],sections={s['id']:text},input={'works':[{k:w[k] for k in ['id','title','definition','completion']} for w in ws],'sources':[{'id':s['id'],'provider_id':s['provider_id'],'country':s['country'],'language':s['language'],'url':url,'publisher_text':text}]}))
# Original official guide assets, staged for root visual review only.
fx=next(x for x in read(R/'research/source-store/bank-breadth-additional-v28-20261012/sources.json') if x['id']=='hk-fx-tools');images=[];seen=set()
for im in fx['images']:
 if im['ordinal'] not in [1,2,3,4,6,8] or im['url'] in seen:continue
 seen.add(im['url']);raw=urlopen(Request(im['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=35).read();sha=hashlib.sha256(raw).hexdigest();out=RUN/'guide-images'/(sha+'.jpg');out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);images.append({'source_id':'A28:hk-fx-tools','url':im['url'],'ordinal':im['ordinal'],'alt':im['alt'],'sha256':sha,'private_path':str(out.relative_to(R)),'automatic_adoption':False});time.sleep(.15)
write(RUN/'guide-images.json',images);(RUN/'FROZEN').write_text('Frozen own smartforms instructions and6 officialFX guide assets; not admitted or app observation.\n');print({'sources':len(sources),'guide_assets':len(images),'smartform_chars':len(text)},flush=True)
