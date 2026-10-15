"""Preserve new public process sources without approving UI or legal claims."""
import concurrent.futures, datetime, hashlib, io, json, urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
from run_mece_closure import ROOT,write

# Shared process-proof store: existing reference validators resolve these IDs.
DEST=ROOT/'research/source-store/mece-closure-20261005/sources'
SOURCES={
 'CHASE_MORTGAGE_SATISFACTION':'https://www.chase.com/personal/mortgage/payoff/payoff-options/receive-confirmation',
 'IFSB27_RETAKAFUL':'https://www.ifsb.org/wp-content/uploads/2023/10/IFSB-27_En.pdf',
 'ICC_UCP_AMENDMENT':'https://library.iccwbo.org/content/tfb/BOOKS/BK_0002/BK_0002_04_2017Revision.htm',
 'ICC_GUARANTEE_AMENDMENT':'https://library.iccwbo.org/content/tfb/RULES/tfb-isdgp-rules.htm',
 'FINRA_CLASS_NOTICE':'https://syndication.finra.org/content/securities-class-action-lawsuits-what-investors-should-know',
 'IBKR_CLASS_ACTION_SCOPE':'https://www.interactivebrokers.com/en/general/corporate-actions.php',
 'FRB_LEASE_RETURN':'https://www.federalreserve.gov/PUBS/leasing/resource/consider/endclosed_info1.htm',
 'NEST_ENROLMENT_PROCESS':'https://www.nestpensions.org.uk/schemeweb/helpcentre/workers/enrolling-workers/enrol-workers-online.html',
 'NEST_ENROLMENT_TYPES':'https://nestpensions.org.uk/schemeweb/helpcentre/workers/enrolling-workers/different-enrolment-types.html',
 'HSBC_CASH_CONCENTRATION':'https://www.business.hsbc.com/en-gb/products/liquidity-and-investments',
 'REVOLUT_RESTRICTION_REVIEW':'https://www.revolut.com/blog/post/how-to-close-revolut-account/',
 'ISLA_SECURITIES_LENDING':'https://www.islaemea.org/wp-content/uploads/2021/04/ISLA_Institutional_Investor_Guide_to_Securities_Lending.pdf',
 'SEC_FILED_SECURITIES_LOAN':'https://www.sec.gov/Archives/edgar/data/1081400/000108140022000619/seclending.htm',
}

def capture(item):
 sid,url=item;meta=DEST/(sid+'.json')
 if meta.exists():return sid,'cached'
 request=urllib.request.Request(url,headers={'User-Agent':'WGSS-public-definition-review/1.8'})
 with urllib.request.urlopen(request,timeout=45) as response:body=response.read();effective=response.url
 pdf=body.startswith(b'%PDF');extension='.pdf' if pdf else '.html'
 if pdf:
  pages=[p.extract_text() or '' for p in PdfReader(io.BytesIO(body)).pages]
  text='\n'.join(f'PDF_PAGE {i+1}\n'+t for i,t in enumerate(pages))
 else:
  soup=BeautifulSoup(body,'html.parser')
  for n in soup(['script','style']):n.decompose()
  text=soup.get_text(' ',strip=True)
 assert len(text)>800,'empty/challenge is not evidence'
 (DEST/(sid+extension)).write_bytes(body);(DEST/(sid+'.txt')).write_text(text)
 write(meta,dict(id=sid,url=url,effective_url=effective,raw_path=sid+extension,text_path=sid+'.txt',
  sha256=hashlib.sha256(body).hexdigest(),text_sha256=hashlib.sha256(text.encode()).hexdigest(),
  retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_kind='official_process_or_standard',
  ui_benchmark_admitted=False,admission='pending_exact_clause_review'))
 return sid,len(text)

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for future in concurrent.futures.as_completed([pool.submit(capture,x) for x in SOURCES.items()]):
   try:print(future.result(),flush=True)
   except Exception as exc:print(type(exc).__name__,flush=True)
