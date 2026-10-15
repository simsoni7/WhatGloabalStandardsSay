import concurrent.futures,datetime,hashlib,json,time,sys
from pathlib import Path
from urllib.request import Request,urlopen
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];name=sys.argv[1];BASE=R/'research/source-store'/name;RUN=R/'research/source-store'/(name+'-own')
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();d=read(R/'dist/data/bank-ui.json');defs={w['id']:w for w in d['works']};covered={id for b in d['benchmarks'] for id in b['ui_work_ids']};idx={x['source_id']:x for x in read(BASE/'index-questions.json')}
if not idx:raise ValueError()
ps=list(BASE.glob('reviews/*discovery-*/*/proposal.json'));expected=len(list(BASE.glob('inputs/*discovery-*.json')));assert len(ps)==expected,(len(ps),expected)
bywork={};routing={}
for p in sorted(ps):
 for row in read(p)['result']['rows']:
  routing[row['source_id']]=row['work_ids']
  for wid in row['work_ids']:
   if wid not in covered:bywork.setdefault(wid,[]).append(row['source_id'])
# Sampling is for bounded candidate adjudication only, not a claim of source exhaustion.
selected=set()
for wid,ids in bywork.items():selected.update(ids[:3])
def fetch(sid):
 x=idx[sid];url='https://www.kakaobank.com/api/v1/boards/FAQ/posts/'+str(x['native_post_id']);raw=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (WGSS official public FAQ research)'}),timeout=35).read();time.sleep(.15);obj=json.loads(raw)['result'];sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.json').write_bytes(raw);text=' '.join((obj['title']+' '+BeautifulSoup(obj['content'],'html.parser').get_text(' ',strip=True)).split());assert obj['title']==x['title'];(folder/'normalized.txt').write_text(text)
 return {'id':sid,'native_post_id':x['native_post_id'],'provider_id':'kakao','country':'KR','language':'ko','url':url,'resolved_url':url,'reader_url':'https://www.kakaobank.com/Help/Guide/Faq','http_status':200,'state':'fetched_pending_review','source_format':'official_faq_json','raw_filename':'source.json','raw_sha256':sha,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text,'title':obj['title'],'snapshot_path':str(folder.relative_to(R)),'index_provenance':x['index_provenance'],'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'automatic_adoption':False}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:rows=list(p.map(fetch,sorted(selected)))
write(RUN/'sources.json',rows);write(RUN/'routing-selection.json',{'selected_source_ids':sorted(selected),'candidate_unlinked_work_ids':sorted(bywork),'candidate_only':True,'all_routed_source_work_ids':routing,'selection_rule':'up to first3 assigned source candidates per globally-unlinked work, bounded sampling; not exhaustive assurance','automatic_adoption':False})
base=read(R/'research/source-store/bank-priority-v27-20261012/inputs/priority-kr-1.json');base['instructions']=base['instructions'].replace('Use only 32 given work IDs.','Use only assigned whole-scope work IDs.')+' Whole214 discovery, now own exact answer verification. Merchant refund execution is not customer merchant-refund receipt. Referral to Shinhan/Tmoney is not Kakao directly performing operation. mini stored value is not a deposit. Card shipping is not financial application approval. Usage disclosures are not necessarily personaldata copy. Quote requested outcome fully; no invention from question heading. Do not merge shared participation and legal joint ownership. Source can support several assigned works if body explicitly describes independent outcomes.'
for i in range(0,len(rows),7):
 shard=rows[i:i+7];assigned={wid for s in shard for wid in routing[s['id']]};ws=[{k:defs[wid][k] for k in ['id','title','definition','completion','includes','excludes']} for wid in sorted(assigned)];jid='v28-own-exact-'+str(i//7+1);write(RUN/'inputs'/(jid+'.json'),dict(base,id=jid,max_tokens=20000,input={'works':ws,'sources':[{'id':s['id'],'provider_id':'kakao','country':'KR','language':'ko','url':s['url'],'publisher_text':s['text']} for s in shard]},expected_ids=[s['id'] for s in shard],work_ids=sorted(assigned),sections={s['id']:s['text'] for s in shard}))
(RUN/'FROZEN').write_text('Individual own public FAQ snapshots; exact extract and root admission still separate.\n');print({'own_records':len(rows),'potential_new_works':len(bywork),'exact_jobs':(len(rows)+6)//7},flush=True)
