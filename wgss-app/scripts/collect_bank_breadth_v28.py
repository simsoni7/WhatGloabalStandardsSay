import concurrent.futures,datetime,hashlib,json,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode,urljoin,urlparse
from bs4 import BeautifulSoup
import pymupdf
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-breadth-additional-v28-20261012'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def get(url):
 raw=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (WGSS public financial source research)'}),timeout=40).read();time.sleep(.15);return raw
assert not (RUN/'FROZEN').exists()
def faq(tag,page):
 url='https://www.kakaobank.com/api/v1/search/FAQ?'+urlencode({'tag':tag,'page':page});raw=get(url);d=json.loads(raw);sha=hashlib.sha256(raw).hexdigest();folder=RUN/'indexes'/tag.replace('/','-')/str(page)/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.json').write_bytes(raw)
 return {'url':url,'category':tag,'page':page,'raw_sha256':sha,'snapshot_path':str(folder.relative_to(R)),'result':d['result'],'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
tags=['대출','외환','투자','mini','사업자','ATM','알림','앱 이용','기타'];first=[faq(t,0) for t in tags];todo=[(s['category'],i) for s in first for i in range(1,s['result']['total_pages'])]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:rows=first+list(p.map(lambda x:faq(*x),todo))
indexed={}
for row in rows:
 for x in row['result']['content']:
  text=' '.join(BeautifulSoup(x['content'],'html.parser').get_text(' ',strip=True).split());item={'source_id':'kr-faq-'+str(x['post_id']),'native_post_id':x['post_id'],'title':x['title'],'answer':text,'categories':[],'index_provenance':[]};current=indexed.setdefault(item['source_id'],item);assert current['answer']==text and current['title']==x['title'];current['categories'].append(row['category']);current['index_provenance'].append({'url':row['url'],'raw_sha256':row['raw_sha256'],'snapshot_path':row['snapshot_path']})
write(RUN/'indexes.json',rows);write(RUN/'index-questions.json',list(indexed.values()))
original=R/'research/source-store/bank-breadth-v28-20261012';works=json.loads((R/'dist/data/bank-ui.json').read_text())['works'];ids=[w['id'] for w in works];compact=[{k:w[k] for k in ['id','title','domain_id','definition','completion']} for w in works]
oldids={x['source_id'] for x in json.loads((R/'research/source-store/bank-kakao-faq-v27-20261012/index-questions.json').read_text())};items=[x for x in indexed.values() if x['source_id'] not in oldids];basejob=json.loads((original/'inputs/v28-breadth-discovery-1.json').read_text())
for i in range(0,len(items),90):
 shard=items[i:i+90];jid='v28-added-discovery-'+str(i//90+1);job=dict(basejob,id=jid,input={'works':compact,'sources':[{'source_id':x['source_id'],'title':x['title'],'answer':x['answer']} for x in shard]},expected_ids=[x['source_id'] for x in shard]);write(RUN/'inputs'/(jid+'.json'),job)
# Explicit own sources selected from official search results, not invented URLs.
targets=[('hk-fx-tools','hsbc-hk','HK','zh-Hant','https://www.hsbc.com.hk/zh-hk/investments/products/foreign-exchange/fx-tools-on-mobile/'),('hk-fx-faq','hsbc-hk','HK','zh-Hant','https://www.hsbc.com.hk/zh-hk/help/faq/investments/'),('uk-business-help','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/campaigns/bib-help-centre/using-bib'),('uk-business-trade','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/solutions/ways-to-bank'),('uk-business-manage-guide','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/-/media/media/uk/pdfs/campaigns/managing-service-guide.pdf')]
sources=[]
for sid,pid,country,lang,url in targets:
 try:
  raw=get(url);sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True);pdf=raw.startswith(b'%PDF');filename='source.pdf' if pdf else 'source.html';(folder/filename).write_bytes(raw)
  if pdf:
   doc=pymupdf.open(stream=raw,filetype='pdf');text=' '.join(' '.join(p.get_text() for p in doc).split());images=[]
  else:
   soup=BeautifulSoup(raw,'html.parser');body=soup.find('main') or soup.find('body') or soup
   for x in body.select('script,style,nav,footer,header'):x.decompose()
   text=' '.join(body.get_text(' ',strip=True).split());images=[{'url':urljoin(url,x.get('src','')),'alt':x.get('alt',''),'ordinal':i} for i,x in enumerate(body.select('img[src]'))]
  (folder/'normalized.txt').write_text(text);sources.append({'id':sid,'provider_id':pid,'country':country,'language':lang,'url':url,'resolved_url':url,'http_status':200,'state':'fetched_pending_review','source_format':'official_pdf' if pdf else 'official_html','raw_filename':filename,'raw_sha256':sha,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text,'snapshot_path':str(folder.relative_to(R)),'images':images,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'automatic_adoption':False})
  print(sid,len(text),flush=True)
 except Exception as e:sources.append({'id':sid,'url':url,'state':'fetch_failed','error_type':type(e).__name__});print(sid,type(e).__name__,flush=True)
write(RUN/'sources.json',sources)
base=json.loads((R/'research/source-store/bank-priority-v27-20261012/inputs/priority-kr-1.json').read_text());base['instructions']=base['instructions'].replace('Use only 32 given work IDs.','Use only the 214 given work IDs.').replace('Maximum 8 features per source','Maximum 18 features per source')+' Whole-scope breadth discovery. Corporate UI is not retail UI: preserve corporate role and business platform; trade online forms are not an observed app. FX coupons alone do not prove execution unless own instructions explicitly describe currency conversion. Main page links/headings are not affirmative child operation proof.'
for s in sources:
 if s['state']!='fetched_pending_review':continue
 jid='v28-exact-'+s['id'];write(RUN/'inputs'/(jid+'.json'),dict(base,id=jid,max_tokens=22000,input={'works':compact,'sources':[{'id':s['id'],'provider_id':s['provider_id'],'country':s['country'],'language':s['language'],'url':s['url'],'publisher_text':s['text']}]},expected_ids=[s['id']],work_ids=ids,sections={s['id']:s['text']}))
(RUN/'FROZEN').write_text('Immutable public category census and publisher sources; discovery not admission.\n');print(json.dumps({'index_pages':len(rows),'unique_questions':len(indexed),'additional_questions':len(items),'jobs':len(list((RUN/'inputs').glob('*.json'))),'sources':len(sources)}),flush=True)
