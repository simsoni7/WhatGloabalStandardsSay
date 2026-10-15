"""Verify accepted vocabulary against preserved public sources; stage live changes.

New labels, changed snapshots and HTTP responses never edit accepted profiles.
"""
import argparse,concurrent.futures,hashlib,json,re,time,urllib.request
from html.parser import HTMLParser
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/products-20261004'
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.hidden=0;self.anchor=None;self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.hidden+=1
  if tag=='a':self.anchor=[dict(attrs).get('href',''),[]]
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.hidden=max(0,self.hidden-1)
  if tag=='a' and self.anchor:self.links.append((self.anchor[0],''.join(self.anchor[1]).strip()));self.anchor=None
 def handle_data(self,data):
  if not self.hidden:self.parts.append(data)
  if self.anchor and not self.hidden:self.anchor[1].append(data)
def text(raw):
 p=Text();p.feed(raw.decode('utf-8'));return p
def norm(t):return re.sub(r'\s+','',t)
def discover_kakao(raw):
 headers={'상품안내','통장/저축','투자/외환','대출','카드','사업자','mini'}
 return {label for href,label in text(raw).links if '/products/' in href and label and label not in headers}
def check(refresh=False):
 review=json.loads((R/'data/product-profiles-review.json').read_text());inventory=json.loads((R/'data/product-vocabulary-inventory.json').read_text());issues=[];verified=[]
 for source in review['product_sources']:
  f=P/(source['id']+('.rdf' if source['id']=='fibo-credit-facility' else '.html'))
  if not f.exists():issues.append({'source':source['id'],'error':'snapshot absent'});continue
  raw=f.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=source['sha256']:issues.append({'source':source['id'],'error':'accepted snapshot hash mismatch'});continue
  content=norm(' '.join(text(raw).parts))
  if len(content)<200:issues.append({'source':source['id'],'error':'empty or shell-only document is not definition evidence'});continue
  for item in inventory['items']:
   if item['source_id']==source['id'] and norm(item['term']) not in content:issues.append({'item':item['id'],'error':'observed label not located in accepted source'})
  verified.append(source['id'])
 accepted={i['term'] for i in inventory['items'] if i['source_id']=='kakao-creditline'}
 discovered=discover_kakao((P/'kakao-creditline.html').read_bytes())
 for term in sorted(discovered-accepted):issues.append({'term':term,'error':'new source menu label has no root disposition'})
 for term in sorted(accepted-discovered):issues.append({'term':term,'error':'source menu label was removed without reassessment'})
 # Detailed target captures are separate from the parent menu label. Verify the
 # retained bytes and root mapping even for targets still explicitly unlinked.
 targets=R/'research/source-store/definition-completion-20261004/inventory-sources'
 for item in inventory['items']:
  if not item.get('target_source_id'):continue
  folder=targets/item['id'];f=folder/'source.html';manifest=folder/'manifest.json'
  if not f.exists() or not manifest.exists():issues.append({'item':item['id'],'error':'target body snapshot absent'});continue
  evidence=json.loads(manifest.read_text())
  if hashlib.sha256(f.read_bytes()).hexdigest()!=item['target_source_sha256'] or evidence['sha256']!=item['target_source_sha256']:issues.append({'item':item['id'],'error':'accepted target hash mismatch'})
  if evidence.get('body_chars',0)<200:issues.append({'item':item['id'],'error':'target is not substantive product definition'})
  if item['disposition']=='mapped':
   if item['target_source_id'] not in verified:issues.append({'item':item['id'],'error':'mapped target source is not admitted'})
   for pid in item['profile_ids']:
    profile=next(p for p in review['product_profiles'] if p['id']==pid)
    if not any(v['inventory_id']==item['id'] and v['source_id']==item['target_source_id'] for v in profile.get('source_variants',[])):issues.append({'item':item['id'],'error':'missing root variant condition'})
 live=[]
 if refresh:
  staged=P/'staged'/str(time.time_ns());staged.mkdir(parents=True)
  def fetch(source):
   try:
    raw=urllib.request.urlopen(urllib.request.Request(source['url'],headers={'User-Agent':'WGSS-definition-review/1.0'}),timeout=35).read();file=staged/(source['id']+'.bin');file.write_bytes(raw);item={'id':source['id'],'url':source['url'],'sha256':hashlib.sha256(raw).hexdigest(),'changed_snapshot':hashlib.sha256(raw).hexdigest()!=source['sha256'],'automatic_adoption':False}
    if len(norm(' '.join(text(raw).parts)))<200:item['error']='empty or shell-only response'
    if source['id']=='kakao-creditline':
     current=discover_kakao(raw);item['new_labels']=sorted(current-accepted);item['removed_labels']=sorted(accepted-current)
    return item
   except Exception as e:return {'id':source['id'],'error':type(e).__name__,'automatic_adoption':False}
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:live=list(pool.map(fetch,review['product_sources']))
  (staged/'manifest.json').write_text(json.dumps(live,ensure_ascii=False,indent=2)+'\n')
  for source in live:
   if source.get('error') or source.get('new_labels') or source.get('removed_labels'):issues.append({'source':source['id'],'error':'live vocabulary requires root reassessment','detail':source})
 result={'status':'failed' if issues else 'passed','source_count':len(verified),'inventory_count':len(inventory['items']),'known_source_names_located':len(inventory['items']) if not issues else None,'new_names_silently_adopted':False,'issues':issues,'live_staged':len(live),'policy_changes_not_inferred_from_hash':True}
 print(json.dumps(result,ensure_ascii=False));return not issues
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--refresh',action='store_true');args=parser.parse_args();raise SystemExit(0 if check(args.refresh) else 1)
