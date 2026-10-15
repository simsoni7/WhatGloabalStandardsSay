"""Resolve advisory FAQ candidates to their own public publisher records; no admission."""
import concurrent.futures,datetime,hashlib,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-kakao-faq-v27-20261012'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 assert not (RUN/'EVIDENCE_FROZEN').exists();index={x['source_id']:x for x in json.loads((RUN/'index-questions.json').read_text())};reviews=[json.loads(f.read_text()) for f in RUN.glob('reviews/faq-discovery-*/*/proposal.json')];assert len(reviews)==6
 candidates={x['source_id'] for d in reviews for x in d['result']['rows'] if x.get('work_ids')}
 def fetch(id):
  native=index[id]['native_post_id'];url='https://www.kakaobank.com/api/v1/boards/FAQ/posts/'+str(native);raw=urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read();d=json.loads(raw)['result'];sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/id/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.json').write_bytes(raw)
  title=d['title'];content=d['content'];soup=BeautifulSoup(content,'html.parser');text=' '.join((title+' '+soup.get_text(' ',strip=True)).split());assert title==index[id]['title'];(folder/'normalized.txt').write_text(text)
  return {'id':id,'native_post_id':native,'provider_id':'kakao','country':'KR','language':'ko','url':url,'resolved_url':url,'reader_url':'https://www.kakaobank.com/Help/Guide/Faq','http_status':200,'state':'fetched_pending_review','source_format':'official_faq_json','raw_filename':'source.json','raw_sha256':sha,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text,'title':title,'snapshot_path':str(folder.relative_to(R)),'images':[{'url':urljoin('https://www.kakaobank.com',im['src']),'alt':im.get('alt',''),'ordinal':i} for i,im in enumerate(soup.select('img[src]'))],'index_provenance':index[id]['index_provenance'],'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'automatic_adoption':False}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:rows=list(p.map(fetch,sorted(candidates)))
 write(RUN/'sources.json',rows);defs=json.loads((R/'data/bank-ui-root-decisions.json').read_text())['catalogue']['works'];plan=json.loads((R/'data/bank-ui-collection-plan.json').read_text());ids={id for g in plan['priority_groups'] for id in g['ui_work_ids']};works=[{k:w[k] for k in ['id','title','definition','completion','includes','excludes']} for w in defs if w['id'] in ids]
 original=json.loads((R/'research/source-store/bank-priority-v27-20261012/inputs/priority-kr-1.json').read_text());sections={s['id']:s['text'] for s in rows}
 for i in range(0,len(rows),8):
  shard=rows[i:i+8];id='faq-exact-'+str(i//8+1);job=dict(original,id=id,max_tokens=18000,input={'works':works,'sources':[{'id':s['id'],'provider_id':'kakao','country':'KR','language':'ko','url':s['url'],'publisher_text':s['text']} for s in shard]},expected_ids=[s['id'] for s in shard],work_ids=sorted(ids),sections={s['id']:s['text'] for s in shard});job['instructions'] += '\nThese are individual own official FAQ answers, not a help index. The question alone is never affirmative evidence. If answer redirects to a third-party credit card issuer, mark referral, not a direct KakaoBank capability. Lost-report cancellation is NOT temporary card unlock. Domestic-only usage restriction is card use scope, not necessarily whole-card freeze. Scheduled group membership dues are not bank standing orders. Extract only affirmative customer operations from the answer body and preserve all stated product/channel qualifications. Short proof quotes only, copy whitespace exactly.';write(RUN/'inputs'/(id+'.json'),job)
 (RUN/'EVIDENCE_FROZEN').write_text('Own FAQ records frozen; candidate admission still root reviewed.\n');print(json.dumps({'own_faq_records':len(rows),'exact_jobs':(len(rows)+7)//8}))
if __name__=='__main__':main()
