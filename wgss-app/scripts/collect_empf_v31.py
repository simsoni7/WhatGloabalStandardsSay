"""One-time eMPF own-source native-language and enrolment collection.

Normal public HTML/JS determines language URLs and linked assets. No private
session, authentication, captcha bypass, or admission is performed.
"""
import concurrent.futures, datetime, hashlib, json, re
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlsplit, urlunsplit, quote
from bs4 import BeautifulSoup
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'research/source-store/empf-collection-v31-20261012'
BASE = 'https://www.empf.org.hk'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def fetch(target):
    sid, url, language, via = target
    parts=urlsplit(url);url=urlunsplit((parts.scheme,parts.netloc,quote(parts.path,safe='/%'),parts.query,parts.fragment))
    try:
        with urlopen(Request(url, headers={'User-Agent':'Mozilla/5.0 (WGSS official public research)'}),timeout=40) as res:
            raw=res.read(); resolved=res.geturl(); status=res.status
        sha=hashlib.sha256(raw).hexdigest();folder=RUN/'sources'/sid/sha;folder.mkdir(parents=True,exist_ok=True)
        pdf=raw.startswith(b'%PDF');filename='source.pdf' if pdf else 'source.html';(folder/filename).write_bytes(raw)
        pages=[]; links=[];metadata=None
        if pdf:
            doc=pymupdf.open(stream=raw,filetype='pdf');metadata=doc.metadata
            pages=[dict(page=i+1,text=' '.join(p.get_text().split()),width=p.rect.width,height=p.rect.height) for i,p in enumerate(doc)]
            text=' '.join(p['text'] for p in pages)
        else:
            soup=BeautifulSoup(raw,'html.parser');body=soup.find('main') or soup.find('body') or soup
            links=[dict(label=a.get_text(' ',strip=True),url=urljoin(resolved,a['href']),context=a.parent.parent.get_text(' ',strip=True)[:250]) for a in body.select('a[href]')]
            for x in body.select('script,style,nav,header,footer'):x.decompose()
            text=' '.join(body.get_text(' ',strip=True).split())
        (folder/'normalized.txt').write_text(text)
        return dict(id=sid,provider_id='empf-hk',country='HK',language=language,url=url,resolved_url=resolved,http_status=status,state='fetched_pending_review',source_format='official_pdf' if pdf else 'official_html',raw_filename=filename,raw_sha256=sha,text_sha256=hashlib.sha256(text.encode()).hexdigest(),text=text,snapshot_path=str(folder.relative_to(ROOT)),pdf_pages=pages,pdf_metadata=metadata,links=links,images=[],research_family='protection',discovery=via,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),automatic_adoption=False)
    except Exception as e:
        return dict(id=sid,provider_id='empf-hk',country='HK',language=language,url=url,state='fetch_failed',error_type=type(e).__name__,http_status=getattr(e,'code',None),automatic_adoption=False)

if __name__ == '__main__':
    assert not (RUN/'FROZEN').exists(), 'frozen one-time run must not be overwritten'
    en=fetch(('empf-en-index',BASE+'/tutorial/tutorials/mpf-account-enrolment?parent=/tutorial/member&language_id=1','en','v30 own tutorial hyperlink'))
    raw=(ROOT/en['snapshot_path']/'source.html').read_text()
    assert 'const changeLanguage = (languageId)' in raw
    assert 'newUrl.searchParams.set("language_id", languageId ?? 1)' in raw
    assert 'onclick="changeLanguage(5377681);return false;"' in raw
    m=re.search(r'const changeLanguage = .*?\n        }',raw,re.S);assert m
    write(RUN/'discovery.json',dict(language_switch_public_js=m.group(),native_traditional_link='繁體 / changeLanguage(5377681)',language_id=5377681,english_tutorial_resolved_url=en['resolved_url'],method='own_public_html_inline_javascript_inspection',browser_probe=dict(state='failed_to_load_function',error_type='ReferenceError',admitted_browser_observation=False),automatic_adoption=False))
    initial=[('empf-zh-index',BASE+'/useful-tools/member-and-self-employed-person/?language_id=5377681','zh-Hant-HK','public JS verified language_id'),('empf-zh-member-faq',BASE+'/faq/member/?language_id=5377681','zh-Hant-HK','public JS verified language_id'),('empf-zh-employer-faq',BASE+'/faq/employer/?language_id=5377681','zh-Hant-HK','public JS verified language_id')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:sources=[en]+list(p.map(fetch,initial))
    index=next(s for s in sources if s['id']=='empf-zh-index');assert '強積金' in index['text'] and '註冊' in index['text']
    targets=[]
    wanted=[('empf-zh-invest-app','1177ed4215','zh-Hant-HK',index),('empf-zh-invest-web','91a520cb8d','zh-Hant-HK',index),('empf-zh-withdrawal-web','09c14bba3c','zh-Hant-HK',index),('empf-zh-enrolment-web','f65dbe89f4','zh-Hant-HK',index),('empf-en-enrolment-app','89a3565bc6','en',en),('empf-en-enrolment-web','f65dbe89f4','en',en),('empf-en-sep-web','0822971879','en',en)]
    for sid,asset,language,idx in wanted:
        links=[l for l in idx['links'] if '/dA/'+asset+'/' in l['url'] and '.pdf' in l['url']];assert links,(sid,asset)
        targets.append((sid,links[0]['url'],language,dict(index_source_id=idx['id'],link=links[0])))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:sources+=list(p.map(fetch,targets))
    assets=[]
    for s in sources:
        if s['state']!='fetched_pending_review' or not s['pdf_pages']:continue
        doc=pymupdf.open(ROOT/s['snapshot_path']/s['raw_filename'])
        for i,p in enumerate(doc):
            if i<2:continue
            pix=p.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5));aid=s['id']+'-page-'+str(i+1);path=RUN/'assets'/(aid+'.png');path.parent.mkdir(parents=True,exist_ok=True);pix.save(path)
            assets.append(dict(id=aid,source_id=s['id'],source_url=s['url'],page=i+1,raw_pdf_sha256=s['raw_sha256'],image_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),image_path=str(path.relative_to(ROOT)),width=pix.width,height=pix.height,render_scale=1.5,image_derivation='unmodified_full_official_pdf_page_render',automatic_adoption=False))
    write(RUN/'sources.json',sources);write(RUN/'assets.json',assets);write(RUN/'baseline.json',json.loads((ROOT/'dist/data/bank-ui.json').read_text()))
    (RUN/'FROZEN').write_text('Own originals, language discovery and PDF renders frozen; all advisory, no UI/admission assertion.\n')
    print(json.dumps(dict(sources=len(sources),fetched=sum(s['state']=='fetched_pending_review' for s in sources),failures=[s['id'] for s in sources if s['state']=='fetch_failed'],staged_page_renders=len(assets),pages=[(s['id'],len(s.get('pdf_pages',[]))) for s in sources]),ensure_ascii=False))
