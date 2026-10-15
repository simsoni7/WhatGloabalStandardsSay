"""Retain bounded public primary sources; HTTP success is not evidence admission."""
import concurrent.futures, datetime, hashlib, json, urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

DEST = Path(__file__).resolve().parents[1] / 'research/source-store/mece-closure-20261005/sources'
SOURCES = {
    'FFIEC_SAR_DECISION': 'https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/04',
    'OFAC_VALID_MATCH': 'https://ofac.treasury.gov/faqs/5',
    'KR_CONSUMER_WITHDRAWAL': 'https://easylaw.go.kr/CSP/CnpClsMainBtr.laf?ccfNo=1&cciNo=2&cnpClsNo=3&csmSeq=1771&popMenu=ov',
    'US_RULE23': 'https://www.govinfo.gov/content/pkg/USCODE-2024-title28/html/USCODE-2024-title28-app-federalru-dup1.htm',
}

def capture(item):
    sid, url = item
    meta = DEST / (sid + '.json')
    if meta.exists():
        return sid, 'cached'
    req = urllib.request.Request(url, headers={'User-Agent': 'WGSS-public-source-review/1.7'})
    with urllib.request.urlopen(req, timeout=45) as response:
        body, effective = response.read(), response.url
    soup = BeautifulSoup(body, 'html.parser')
    for node in soup(['script', 'style']):
        node.decompose()
    text = soup.get_text(' ', strip=True)
    assert len(text) > 1000, 'Empty/challenge response cannot be admitted'
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / (sid + '.html')).write_bytes(body)
    (DEST / (sid + '.txt')).write_text(text)
    data = dict(id=sid, url=url, effective_url=effective, raw_path=sid+'.html', text_path=sid+'.txt',
                sha256=hashlib.sha256(body).hexdigest(), text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                source_kind='official_regional_rule_or_guidance', ui_benchmark_admitted=False,
                admission='pending_exact_clause_review')
    meta.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    return sid, len(text)

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for future in concurrent.futures.as_completed([pool.submit(capture, x) for x in SOURCES.items()]):
            try:
                print(future.result(), flush=True)
            except Exception as exc:
                print(type(exc).__name__, flush=True)
