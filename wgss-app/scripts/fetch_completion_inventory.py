"""Capture official target bodies for frozen vocabulary review; never adopt claims."""
import concurrent.futures,hashlib,json,re,urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1]
P=R/'research/source-store/definition-completion-20261004'
OUT=P/'inventory-sources';OUT.mkdir(parents=True,exist_ok=True)
def fetch(item):
 sid=item['id'];dest=OUT/sid;dest.mkdir(exist_ok=True)
 if (dest/'manifest.json').exists():return json.loads((dest/'manifest.json').read_text())
 url=re.sub(r'^http:', 'https:',item['source_url'])
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WGSS-public-definition-research/1.0'}),timeout=40) as response:
   raw=response.read();final=response.url
  (dest/'source.html').write_bytes(raw)
  soup=BeautifulSoup(raw,'html.parser');title=soup.title.get_text(' ',strip=True) if soup.title else ''
  for el in soup.select('script,style,header,footer,nav,#kakaoHead,#kakaoFoot'):el.decompose()
  main=soup.select_one('#kakaoContent') or soup.select_one('main') or soup.body or soup
  text='\n'.join(x.strip() for x in main.get_text('\n').splitlines() if x.strip())
  (dest/'source.txt').write_text(text)
  # Retain exact body excerpts, not inferred product properties or full-page prompts.
  snippets=[{'char_start':0,'char_end':min(len(text),2100),'text':text[:2100]}]
  for term in ['예금종류','상품 개요','가입대상','신청대상','대출대상','상환방법','가입제한','서비스 이용','이용방법','입금','해지','자동','신청절차','발급대상','계약기간']:
   positions=[m.start() for m in re.finditer(re.escape(term),text)]
   if not positions:continue
   at=positions[-1];a=max(0,at-80);b=min(len(text),at+520)
   if not any(a>=s['char_start'] and b<=s['char_end'] for s in snippets):snippets.append({'char_start':a,'char_end':b,'text':text[a:b]})
   if len(snippets)>=7:break
  result={'inventory_id':sid,'source_id':'completion-'+sid,'url':url,'final_url':final,'title':title,'sha256':hashlib.sha256(raw).hexdigest(),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'body_chars':len(text),'checked_at':'2026-10-04','source_kind':'official_public_target_body','benchmark_admitted':False,'automatic_adoption':False,'selected_public_clauses':snippets,'requires_root_semantic_review':True}
 except Exception as e:result={'inventory_id':sid,'url':url,'error':type(e).__name__,'automatic_adoption':False}
 (dest/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':
 inventory=json.loads((R/'data/product-vocabulary-inventory.json').read_text())['items'];items=[i for i in inventory if i['disposition']=='gap']
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,items))
 (OUT/'manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 for job in sorted((P/'inputs').glob('inventory-*.json')):
  ids={x['id'] for x in json.loads(job.read_text())['scope']['inventory']};sources=[x for x in results if x['inventory_id'] in ids]
  dest=P/'supplements'/job.name;dest.parent.mkdir(exist_ok=True)
  if dest.exists():assert json.loads(dest.read_text())=={'target_documents':sources}
  else:dest.write_text(json.dumps({'target_documents':sources},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'target_count':len(results),'errors':[x for x in results if x.get('error')],'body_chars':{x['inventory_id']:x.get('body_chars') for x in results}},ensure_ascii=False))
