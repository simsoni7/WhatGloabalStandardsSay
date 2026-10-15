"""One-time bounded official-source collection for unlinked bank UI results."""
import concurrent.futures,datetime,hashlib,json,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import pymupdf
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-gap-collection-v30-20261012'
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
 assert not (RUN/'FROZEN').exists()
 targets=[
 ('gb-natwest-facflow','natwest-uk','GB','en-GB','https://www.natwest.com/business/support-centre/invoice-finance/facflow-training/invoice-discounting.html','trade'),
 ('gb-hsbc-invoice-guide','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/-/media/media/uk/pdfs/products/product-guide-invoice-discounting.pdf','trade'),
 ('gb-hsbc-export-cover','hsbc-uk','GB','en-GB','https://www.business.hsbc.uk/-/media/media/uk/pdfs/solutions/presentation-export-doc-cover.pdf','trade'),
 ('hk-hsbc-trade-forms','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/help-centre/business-forms/import-and-export-forms','trade'),
 ('hk-hsbc-tradepay','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/-/media/media/hong-kong/pdfs/products/gts-tradepay-onboarding-guide-en.pdf','trade'),
 ('gb-hl-vote','hl-uk','GB','en-GB','https://www.hl.co.uk/shares/corporate-actions/agms-and-shareholder-voting','wealth'),
 ('gb-hl-paper-transfer','hl-uk','GB','en-GB','https://www.hl.co.uk/help/transfers/transferring-to-hl/paper-share-certificates','wealth'),
 ('gb-hl-custody-transfer-form','hl-uk','GB','en-GB','https://www.hl.co.uk/__data/assets/pdf_file/0009/227619/share-account-transfer.pdf','wealth'),
 ('gb-hl-share-exchange','hl-uk','GB','en-GB','https://www.hl.co.uk/help/transfers/transferring-between-accounts/share-exchange','wealth'),
 ('gb-hl-account','hl-uk','GB','en-GB','https://www.hl.co.uk/investment-services/fund-and-share-account','wealth'),
 ('gb-hl-advice','hl-uk','GB','en-GB','https://www.hl.co.uk/financial-advice','wealth'),
 ('hk-hsbc-mpf-transition','hsbc-hk','HK','en','https://www.hsbc.com.hk/mpf/empf/','protection'),
 ('hk-empf-member-faq','empf-hk','HK','en','https://www.empf.org.hk/faq/member/?language_id=1','protection'),
 ('hk-empf-employer-faq','empf-hk','HK','en','https://www.empf.org.hk/faq/employer/?language_id=1','protection'),
 ('hk-empf-invest-web','empf-hk','HK','en','https://www.empf.org.hk/dA/91a520cb8d/MPF%20Investment%20%28Web%20Portal%20Version%29.pdf','protection'),
 ('hk-empf-invest-app','empf-hk','HK','en','https://www.empf.org.hk/dA/1177ed4215/MPF%20Investment%20-%20Mobile%20App%20User%20Guide%20%28Scheme%20Members%29.pdf?language_id=1','protection'),
 ('hk-empf-contribution-web','empf-hk','HK','en','https://www.empf.org.hk/dA/fa170f0c9a/MPF%20Contributions%20%28Web%20Portal%20Version%29.pdf','protection'),
 ('hk-empf-withdrawal-web','empf-hk','HK','en','https://www.empf.org.hk/dA/09c14bba3c/MPF%20Withdrawal%20%28Web%20Portal%20Version%29.pdf?language_id=1','protection'),
 ('kr-samsung-restoration','samsung-fire','KR','ko','https://www.samsungfire.com/sfmi/ui/m/home/mysamsung/restoration/MO_MY_RestorationPremInfo.html?_v=1730419200232','protection'),
 ('kr-samsung-application','samsung-fire','KR','ko','https://www.samsungfire.com/vh/page/VH.HPPD0001.do','protection'),
 ('kr-samsung-employer-insurance','samsung-fire','KR','ko','https://www.samsungfire.com/vh/page/VH.RSFR0200.do','protection')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:sources=list(p.map(fetch,targets))
 # Follow concrete PDF form links from the own official index, not guessed filenames.
 index=next(s for s in sources if s['id']=='hk-hsbc-trade-forms');extra=[]
 for i,label in enumerate(['Export Documentary Credit','Application for a Bank Guarantee','Application for Irrevocable Documentary Credit','Application to Transfer a Documentary Credit']):
  found=[x for x in index.get('links',[]) if label in x['label'] and '.pdf' in x['url']]
  if found:extra.append(('hk-trade-form-'+str(i),'hsbc-hk','HK','en',found[0]['url'],'trade'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:sources+=list(p.map(fetch,extra))
 write(RUN/'sources.json',sources);write(RUN/'baseline.json',read(R/'dist/data/bank-ui.json'));(RUN/'FROZEN').write_text('Source snapshots and baseline frozen. HTTP success and form titles do not admit functional evidence.\n');print(json.dumps({'attempts':len(sources),'fetched':sum(s['state']=='fetched_pending_review' for s in sources),'failures':[s['id'] for s in sources if s['state']=='fetch_failed'],'source_lengths':[(s['id'],len(s.get('text','')),len(s.get('pdf_pages',[]))) for s in sources]},ensure_ascii=False))
