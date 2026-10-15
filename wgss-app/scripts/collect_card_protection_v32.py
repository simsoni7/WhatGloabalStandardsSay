"""One-time bounded official-source collection for unlinked bank UI results."""
import concurrent.futures,datetime,hashlib,json,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import pymupdf
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/card-protection-sources-v32-20261013'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def fetch(target):
 sid,pid,country,language,url,family=target
 try:
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (WGSS public official financial research)'}),timeout=30) as res:raw=res.read();resolved=res.geturl();status=res.status
  sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True);pdf=raw.startswith(b'%PDF');filename='source.pdf' if pdf else 'source.html';(folder/filename).write_bytes(raw);pages=[];links=[];images=[];metadata=None
  if pdf:
   doc=pymupdf.open(stream=raw,filetype='pdf');metadata=doc.metadata
   pages=[dict(page=i+1,text=' '.join(p.get_text().split()),width=p.rect.width,height=p.rect.height) for i,p in enumerate(doc)];text=' '.join(p['text'] for p in pages)
  else:
   soup=BeautifulSoup(raw,'html.parser');body=soup.find('main') or soup.find('body') or soup
   for x in body.select('script,style,nav,header,footer'):x.decompose()
   text=' '.join(body.get_text(' ',strip=True).split());links=[dict(label=a.get_text(' ',strip=True),url=urljoin(resolved,a['href'])) for a in body.select('a[href]')];images=[dict(url=urljoin(resolved,a.get('src') or a.get('data-src')),alt=a.get('alt',''),ordinal=i) for i,a in enumerate(body.select('img[src],img[data-src]'))]
  (folder/'normalized.txt').write_text(text)
  return dict(id=sid,provider_id=pid,country=country,language=language,url=url,resolved_url=resolved,http_status=status,state='fetched_pending_review',source_format='official_pdf' if pdf else 'official_html',raw_filename=filename,raw_sha256=sha,text_sha256=hashlib.sha256(text.encode()).hexdigest(),text=text,snapshot_path=str(folder.relative_to(R)),pdf_pages=pages,pdf_metadata=metadata,links=links,images=images,research_family=family,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),automatic_adoption=False)
 except Exception as e:return dict(id=sid,provider_id=pid,country=country,language=language,url=url,state='fetch_failed',error_type=type(e).__name__,automatic_adoption=False)
if __name__=='__main__':
 import sys
 if not any(x in sys.argv for x in ['--supplement','--insurance','--last','--current-terms']):assert not (RUN/'FROZEN').exists()
 if '--current-terms' in sys.argv:
  RUN=R/'research/source-store/card-protection-current-terms-v32-20261013';assert not (RUN/'FROZEN').exists()
  old=read(R/'research/source-store/card-protection-last-sources-v32-20261013/sources.json')[1];raw=(R/old['snapshot_path']/old['raw_filename']).read_bytes();soup=BeautifulSoup(raw,'html.parser');option=soup.select_one('#dateSelect option');url=urljoin(old['resolved_url'],option['data-url']);s=fetch(('cp-kr-shinhan-current-terms','shinhan-card','KR','ko',url,'cards'));s['followed_from_source_id']=old['id'];s['selection_label']=option.get_text(' ',strip=True);write(RUN/'sources.json',[s]);(RUN/'FROZEN').write_text('Latest own dateSelect data-url followed; old historical page does not become latest through navigationlabels.\n');print({'id':s['id'],'state':s['state'],'length':len(s.get('text','')),'selected_date':s['selection_label']});sys.exit(0)
 if '--last' in sys.argv:
  RUN=R/'research/source-store/card-protection-last-sources-v32-20261013';assert not (RUN/'FROZEN').exists()
  targets=[('cp-kr-kakao-month-savings','kakao','KR','ko','https://www.kakaobank.com/products/m1savings','savings'),('cp-kr-shinhan-revolving-agreement','shinhan-card','KR','ko','https://www.shinhancard.com/pconts/html/helpdesk/terms/terms56/1186792_1133.html','cards')]
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:sources=list(pool.map(fetch,targets))
  write(RUN/'sources.json',sources);(RUN/'FROZEN').write_text('Own full current sources retained, selected financial clauses assigned separately.\n');print(json.dumps({'attempts':len(sources),'lengths':[(s['id'],s['state'],len(s.get('text',''))) for s in sources]},ensure_ascii=False));sys.exit(0)
 if '--insurance' in sys.argv:
  RUN=R/'research/source-store/card-protection-insurance-v32-20261013';assert not (RUN/'FROZEN').exists()
  targets=[('cp-hk-hsbc-life-index','hsbc-life-hk','HK','en','https://www.hsbc.com.hk/insurance/forms/','protection'),('cp-hk-hsbc-life-reinstatement','hsbc-life-hk','HK','en/zh-Hant-HK','https://www.hsbc.com.hk/content/dam/hsbc/hk/docs/insurance/life/policy-reinstatement.pdf','protection'),('cp-kr-samsung-appeal','samsung-fire','KR','ko','https://direct.samsungfire.com/claim/healthreward/health_caution02.html','protection')]
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:sources=list(pool.map(fetch,targets))
  index=sources[0];extra=[]
  # Match concrete policy row text to its own PDF, not repeated generic Download labels.
  raw=(R/index['snapshot_path']/index['raw_filename']).read_bytes();soup=BeautifulSoup(raw,'html.parser')
  for key in ['Transfer of policy ownership','Change of policy benefit','Change of Life Insured','Appeal form']:
   matched=[]
   for row in soup.select('tr'):
    if key in row.get_text(' ',strip=True):
     matched += [urljoin(index['resolved_url'],a['href']) for a in row.select('a[href]') if '.pdf' in a['href'].lower()]
   if matched:extra.append(('cp-hk-hsbc-life-form-'+str(len(extra)),'hsbc-life-hk','HK','en/zh-Hant-HK',matched[0],'protection'))
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:sources+=list(pool.map(fetch,extra))
  write(RUN/'sources.json',sources);(RUN/'FROZEN').write_text('Own insurance forms frozen; request is distinct from approved contract change.\n');print(json.dumps({'attempts':len(sources),'lengths':[(s['id'],s['state'],len(s.get('text',''))) for s in sources]},ensure_ascii=False));sys.exit(0)
 if '--supplement' in sys.argv:
  RUN=R/'research/source-store/card-protection-supplement-v32-20261013'
  assert not (RUN/'FROZEN').exists()
  prior=read(R/'research/source-store/card-protection-sources-v32-20261013/sources.json')
  targets=[
   ('cp-kr-samsung-coolingoff','samsung-fire','KR','ko','https://m.samsungfire.com/consumer/P_U06_08_02_002.html','protection'),
   ('cp-kr-samsung-coolingoff-ui','samsung-fire','KR','ko','https://direct.samsungfire.com/m/mydirect/MP020403_005.html','protection'),
   ('cp-kr-samsung-public-services','samsung-fire','KR','ko','https://www.samsungfire.com/da/main/M_P00_00_00_00.html','protection'),
  ]
  gift=next(x for x in prior if x['id']=='cp-kr-woori-gift')
  a=next(x for x in gift['links'] if x['label']=='충전/환불')
  targets.append(('cp-kr-woori-gift-refund','woori-card','KR','ko',a['url'],'cards'))
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:sources=list(pool.map(fetch,targets))
  # Main selector omitted Shinhan's own sibling popup financial guide; normalize same frozen bytes full-body and preserve separate provenance.
  s=next(x for x in prior if x['id']=='cp-kr-shinhan-revolving');raw=(R/s['snapshot_path']/s['raw_filename']).read_bytes();body=BeautifulSoup(raw,'html.parser').find('body')
  for node in body.select('script,style,nav,header,footer'):node.decompose()
  t=' '.join(body.get_text(' ',strip=True).split());folder=RUN/'sources'/'cp-kr-shinhan-revolving-fullbody'/s['raw_sha256'];folder.mkdir(parents=True,exist_ok=True);(folder/'source.html').write_bytes(raw);(folder/'normalized.txt').write_text(t)
  import copy
  n=copy.deepcopy(s);n.update(id='cp-kr-shinhan-revolving-fullbody',text=t,text_sha256=hashlib.sha256(t.encode()).hexdigest(),snapshot_path=str(folder.relative_to(R)),normalization_note='Full publisher body retains sibling popup financial guide omitted by earlier main selector. Same raw source hash, no new HTTP source.');sources.append(n)
  # Normal headed-free browser navigation can render official public shell; no challenges/session/private steps are bypassed.
  from playwright.sync_api import sync_playwright
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True)
   for sid in ['cp-kr-samsung-quote','cp-hk-manulife-policy','cp-hk-manulife-digital']:
    old=next(x for x in prior if x['id']==sid);page=browser.new_page()
    try:
     response=page.goto(old['url'],wait_until='domcontentloaded',timeout=45000);page.wait_for_timeout(2000);status=response.status if response else None
     if status and status>=400:raise RuntimeError('http_blocked_'+str(status))
     raw=page.content().encode();sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/(sid+'-browser')/sha;folder.mkdir(parents=True,exist_ok=True);(folder/'source.html').write_bytes(raw)
     soup=BeautifulSoup(raw,'html.parser');body=soup.find('body') or soup
     for node in body.select('script,style,nav,header,footer'):node.decompose()
     t=' '.join(body.get_text(' ',strip=True).split());(folder/'normalized.txt').write_text(t)
     sources.append(dict(id=sid+'-browser',provider_id=old['provider_id'],country=old['country'],language=old['language'],url=old['url'],resolved_url=page.url,http_status=status,state='fetched_pending_review',source_format='official_html',raw_filename='source.html',raw_sha256=sha,text_sha256=hashlib.sha256(t.encode()).hexdigest(),text=t,snapshot_path=str(folder.relative_to(R)),pdf_pages=[],pdf_metadata=None,links=[dict(label=a.get_text(' ',strip=True),url=urljoin(page.url,a['href'])) for a in body.select('a[href]')],images=[],research_family=old['research_family'],checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),automatic_adoption=False,fetch_method='normal_browser_public_navigation'))
    except Exception as e:sources.append(dict(id=sid+'-browser',provider_id=old['provider_id'],country=old['country'],language=old['language'],url=old['url'],state='fetch_failed',error_type=type(e).__name__,automatic_adoption=False))
    finally:page.close()
   browser.close()
  write(RUN/'sources.json',sources);(RUN/'FROZEN').write_text('Supplemental source snapshots frozen. No blocked-site bypass.\n');print(json.dumps({'attempts':len(sources),'lengths':[(s['id'],s['state'],len(s.get('text',''))) for s in sources]},ensure_ascii=False));sys.exit(0)
 targets=[
 ('cp-kr-shinhan-revolving','shinhan-card','KR','ko','https://www.shinhancard.com/pconts/html/finance/revolving/CONFM60032/CONFM60032R02.html','cards'),
 ('cp-kr-woori-revolving','woori-card','KR','ko','https://pc.wooricard.com/dcpc/yh1/lon/lon04/useadvexpr/H1LON204S00.do','cards'),
 ('cp-kr-woori-gift','woori-card','KR','ko','https://m.wooricard.com/dcmw/yh1/crd/crd10/giftcard/M1CRD210S06.do','cards'),
 ('cp-gb-hsbc-disputes','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/card-support/dispute-transaction/','cards'),
 ('cp-gb-hsbc-disputes-tool','hsbc-uk','GB','en-GB','https://servicing.hsbc.co.uk/help/disputes-tool/','cards'),
 ('cp-gb-hsbc-corporate','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/en-gb/products/corporate-card','cards'),
 ('cp-gb-hsbc-rewards','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/credit-cards/rewards-offer/','cards'),
 ('cp-gb-hsbc-rewards-faq','hsbc-uk','GB','en-GB','https://servicing.hsbc.co.uk/credit-cards/products/rewards/faq/','cards'),
 ('cp-kr-samsung-quote','samsung-fire','KR','ko','https://www.samsungfire.com/page/VH.RPPD0301.do?pCode=20','protection'),
 ('cp-hk-manulife-policy','manulife-hk','HK','zh-Hant-HK','https://www.manulife.com.hk/zh-hk/individual/services/manage-your-account/policy-management.html','protection'),
 ('cp-hk-manulife-digital','manulife-hk','HK','en','https://www.manulife.com.hk/en/individual/services/digital-services.html','protection'),
 ]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:sources=list(pool.map(fetch,targets))
 extra=[]
 for s in sources:
  if s['state']!='fetched_pending_review':continue
  for a in s['links']:
   if '.pdf' in a['url'].lower() and any(k in a['label'].lower() for k in ['corporate card','programme rules','미비전','reinstatement','退保','保單','user guide']):
    if len(extra)>=12:break
    extra.append((s['id']+'-linked-'+str(len(extra)),s['provider_id'],s['country'],s['language'],a['url'],s['research_family']))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:sources+=list(pool.map(fetch,extra))
 write(RUN/'sources.json',sources);write(RUN/'baseline.json',read(R/'dist/data/bank-ui.json'));(RUN/'FROZEN').write_text('Own originals frozen; no function admitted.\n')
 print(json.dumps({'attempts':len(sources),'fetched':sum(s['state']=='fetched_pending_review' for s in sources),'lengths':[(s['id'],s['state'],len(s.get('text',''))) for s in sources]},ensure_ascii=False))
