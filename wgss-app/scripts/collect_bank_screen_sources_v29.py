# One-time v29 recorder/preparer. Already executed; frozen files must not be overwritten.
import concurrent.futures,datetime,hashlib,json,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse
from bs4 import BeautifulSoup
import pymupdf
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-screen-expansion-v29-20261012'
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def fetch(target):
 sid,pid,country,language,url,kind=target
 try:
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (WGSS official public UI research)'}),timeout=35) as resp:raw=resp.read();resolved=resp.geturl();status=resp.status
  time.sleep(.15);sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True);pdf=raw.startswith(b'%PDF');filename='source.pdf' if pdf else 'source.html';(folder/filename).write_bytes(raw);pages=[];links=[];images=[];meta=None
  if pdf:
   doc=pymupdf.open(stream=raw,filetype='pdf');meta=doc.metadata
   for i,p in enumerate(doc):pages.append({'page':i+1,'text':' '.join(p.get_text().split()),'width':p.rect.width,'height':p.rect.height,'embedded_image_count':len(p.get_images())})
   text=' '.join(x['text'] for x in pages)
  else:
   soup=BeautifulSoup(raw,'html.parser');body=soup.find('main') or soup.find('body') or soup
   for n in body.select('script,style,nav,footer,header'):n.decompose()
   text=' '.join(body.get_text(' ',strip=True).split());links=[{'label':a.get_text(' ',strip=True),'url':urljoin(resolved,a['href'])} for a in body.select('a[href]')];images=[{'url':urljoin(resolved,im.get('src') or im.get('data-src')),'alt':im.get('alt',''),'ordinal':i} for i,im in enumerate(body.select('img[src],img[data-src]'))]
  (folder/'normalized.txt').write_text(text)
  return {'id':sid,'provider_id':pid,'country':country,'language':language,'url':url,'resolved_url':resolved,'http_status':status,'state':'fetched_pending_review','source_format':'official_pdf' if pdf else 'official_html','raw_filename':filename,'raw_sha256':sha,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text,'snapshot_path':str(folder.relative_to(R)),'images':images,'links':links,'pdf_pages':pages,'pdf_metadata':meta,'research_family':kind,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'automatic_adoption':False}
 except Exception as e:return {'id':sid,'provider_id':pid,'country':country,'language':language,'url':url,'state':'fetch_failed','error_type':type(e).__name__,'automatic_adoption':False}
assert not (RUN/'FROZEN').exists()
targets=[
 ('kr-shinhan-openbank','shinhan-card','KR','ko','https://www.shinhancard.com/pconts/html/mobile/main/openbanking/openbanking.html','cards-payments'),
 ('kr-shinhan-solguide','shinhan-card','KR','ko','https://www.shinhancard.com/pconts/pLay/shPlay.html','cards-payments'),
 ('kr-shinhan-point','shinhan-card','KR','ko','https://www.shinhancard.com/pconts/html/benefit/my/point/pointExplain/CONFM50047/CONFM50047R01.html','cards'),
 ('kr-samsungfire-claims','samsung-fire','KR','ko','https://pr.samsungfire.com/v2/html/claim/05/C_050_040_008.html','insurance'),
 ('kr-samsungpop-guide-index','samsung-securities','KR','ko','https://www.samsungpop.com/customer/system/tab_guide3.pop','investment'),
 ('kr-samsungpop-pdf','samsung-securities','KR','ko','https://www.samsungpop.com/download/customer/mPOP_guide.pdf','investment'),
 ('gb-fidelity-guides','fidelity-uk','GB','en-GB','https://www.fidelity.co.uk/how-to-guide/','investment'),
 ('gb-fidelity-pension','fidelity-uk','GB','en-GB','https://www.fidelity.co.uk/retirement/access-your-pension/','pension'),
 ('gb-hl-drawdown','hl-uk','GB','en-GB','https://www.hl.co.uk/help/adding-and-withdrawing-money/accessing-pension/drawdown','pension'),
 ('gb-hl-apply-drawdown','hl-uk','GB','en-GB','https://www.hl.co.uk/retirement/drawdown/apply-for-drawdown','pension'),
 ('hk-manulife-claims-guide','manulife-hk','HK','en','https://www.manulife.com.hk/en/individual/services/manage-your-account/claims-submission-and-enquiries.html','insurance'),
 ('hk-manulife-eclaims','manulife-hk','HK','en','https://www.manulife.com.hk/en/individual/services/file-a-claim/eclaims.html','insurance'),
 ('hk-hsbclife-existing','hsbc-life-hk','HK','zh-Hant','https://www.hsbc.com.hk/zh-hk/insurance/existing-customers/','insurance'),
 ('hk-hsbclife-guide','hsbc-life-hk','HK','zh-Hant','https://www.hsbc.com.hk/content/dam/hsbc/hk/tc/docs/insurance/life/policy-ways-to-manage-guide.pdf','insurance'),
 ('hk-hsbclife-healthplus','hsbc-life-hk','HK','en','https://forms.hsbc.com.hk/content/dam/hsbc/hk/docs/insurance/healthylife/user-guide-healthplus.pdf','insurance'),
 ('my-cimb-durian','cimb-islamic-my','MY','en','https://www.cimb.com.my/en/personal/day-to-day-banking/accounts/mudarabah-ia/daily-unrestricted-investment-account-i.html','secondary-market-islamic')]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:sources=list(p.map(fetch,targets))
# Resolve guide PDFs only from the publisher's own guide-index links.
fid=next(s for s in sources if s['id']=='gb-fidelity-guides');labels=['Buy a fund (OEIC & Unit trust)','Sell a fund (OEIC & Unit trust)','Buy an exchange-traded instrument','Set up a regular savings plan','Cancel your regular savings plan','Change your password','Withdraw cash from your account','Shareholder rights & voting guide']
extra=[]
for i,label in enumerate(labels):
 found=[x for x in fid.get('links',[]) if x['label']==label and '.pdf' in x['url']]
 if found:extra.append(('gb-fidelity-pdf-'+str(i),'fidelity-uk','GB','en-GB',found[0]['url'],'investment'))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:sources+=list(p.map(fetch,extra))
write(RUN/'sources.json',sources);(RUN/'FROZEN').write_text('Own provider pages/PDFs frozen; no capability or screen admission from HTTP success.\n')
# General exact-extract jobs use ALL214 existing+2 proposed IDs; additions are
# admitted separately through the scope gate before any benchmark is linked.
root=json.loads((R/'data/bank-ui-root-decisions.json').read_text());ws=root['catalogue']['works'];scope=json.loads((R/'research/source-store/bank-scope-v29-20261012/root-proposals.json').read_text());ws=ws+[x['proposal'] for x in scope['rows'] if x['kind']=='source_counterexample_new_result'];ids=[w['id'] for w in ws];compact=[{k:w[k] for k in ['id','title','definition','completion','includes','excludes']} for w in ws]
base=json.loads((R/'research/source-store/bank-priority-v27-20261012/inputs/priority-kr-1.json').read_text());base['instructions']=base['instructions'].replace('Use only 32 given work IDs.','Use only the216 frozen existing+proposed work IDs.').replace('Maximum 8 features per source','Maximum6 features per source')+' Official guides and PDF screenshots support described workflows, NOT observed installedapp or currentversion. Preserve investment vs ordinary deposit, retirement benefit vs early pension withdrawal, cancellation of regular investment mandate vs selling existingholding, beneficiary election vs shareholdervote proxy. HSBC Life is insurer; HSBC Bank may be distribution channel, not samelegalservice provider. General imageindex/nav alone notaffirmative capability. Malaysia is separate stagedmarket, notGB/HK/KR. Keep dates, languages, product, device, role unknowns unknown. Corporate/statements mainfooters excluded. For old mPOPguide explicitly mention source-version age fromprovidedmetadata; do not claim currentapp. Quote exact contiguous short labels/body, no smartquote normalisation.'
for s in sources:
 if s['state']!='fetched_pending_review':continue
 text=s['text']
 if len(text)>18000:
  # Page bounded sections, immutable original remains whole. Distinct fragments
  # never blend own qualifications from unrelated product headings.
  chunks=[text[i:i+14000] for i in range(0,len(text),14000)]
 else:chunks=[text]
 for i,t in enumerate(chunks):
  jid='v29-exact-'+s['id']+'-'+str(i+1);job=dict(base,id=jid,max_tokens=17000,input={'works':compact,'sources':[{'id':s['id'],'provider_id':s['provider_id'],'country':s['country'],'language':s['language'],'url':s['url'],'publisher_text':t,'pdf_metadata':s['pdf_metadata']}]},expected_ids=[s['id']],work_ids=ids,sections={s['id']:t});write(RUN/'inputs'/f'{jid}.json',job)
print(json.dumps({'targets':len(targets),'own_pdfs_from_index':len(extra),'fetched':sum(s['state']=='fetched_pending_review' for s in sources),'failed':[s['id'] for s in sources if s['state']=='fetch_failed'],'jobs':len(list((RUN/'inputs').glob('*.json'))),'image_links':sum(len(s.get('images',[])) for s in sources)}),flush=True)
