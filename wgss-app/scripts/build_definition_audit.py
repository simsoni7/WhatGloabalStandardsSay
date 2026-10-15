"""Build a discovery staging database; never promote candidates into benchmarks."""
import hashlib,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'research/definition-v11/collection'
def read(name): return json.loads((INPUT/name).read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(value): return json.dumps(value,ensure_ascii=False)
def build():
 ledger=read('source-manifest.json'); inventory=read('discovered-inventory.json'); procedures=read('citimanager-procedure-candidates.json'); summary=read('summary.json')
 assert summary['global_mece_total'] is None and summary['accepted_new_benchmarks']==0
 assert all(not x.get('accepted_benchmark') for x in ledger+procedures)
 ids={x['id'] for x in ledger}; assert len(ids)==len(ledger),'duplicate source IDs'
 assert all(x['source_id'] in ids for x in inventory+procedures),'orphan source'
 path=ROOT/'data/collection.building.sqlite';path.unlink(missing_ok=True)
 con=sqlite3.connect(path);con.execute('PRAGMA foreign_keys=ON')
 con.executescript('''
 CREATE TABLE source_snapshot(id TEXT PRIMARY KEY, provider_id TEXT NOT NULL, url TEXT NOT NULL, data TEXT NOT NULL, admission_status TEXT NOT NULL DEFAULT 'inventory_only' CHECK(admission_status='inventory_only'));
 CREATE TABLE discovered_candidate(id INTEGER PRIMARY KEY, provider_id TEXT NOT NULL, url TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES source_snapshot(id), data TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unassessed' CHECK(status='unassessed'));
 CREATE TABLE procedure_candidate(id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES source_snapshot(id), data TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unassessed' CHECK(status='unassessed'));
 CREATE TABLE faq_source(id TEXT PRIMARY KEY, url TEXT NOT NULL, data TEXT NOT NULL);
 CREATE TABLE faq_document_candidate(id TEXT PRIMARY KEY, data TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unassessed' CHECK(status='unassessed'));
 CREATE TABLE faq_observation(id INTEGER PRIMARY KEY, document_id TEXT NOT NULL REFERENCES faq_document_candidate(id), source_id TEXT NOT NULL REFERENCES faq_source(id), data TEXT NOT NULL);
 CREATE TABLE rendered_source(id TEXT PRIMARY KEY,url TEXT NOT NULL,data TEXT NOT NULL);
 CREATE TABLE rendered_candidate(id INTEGER PRIMARY KEY,source_id TEXT NOT NULL REFERENCES rendered_source(id),data TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'unassessed' CHECK(status='unassessed'));
 CREATE TABLE run_metadata(key TEXT PRIMARY KEY,data TEXT NOT NULL);
 ''')
 for x in ledger: con.execute('INSERT INTO source_snapshot(id,provider_id,url,data) VALUES(?,?,?,?)',(x['id'],x['provider_id'],x['url'],dump(x)))
 for x in inventory: con.execute('INSERT INTO discovered_candidate(provider_id,url,source_id,data) VALUES(?,?,?,?)',(x['provider_id'],x['url'],x['source_id'],dump(x)))
 for x in procedures: con.execute('INSERT INTO procedure_candidate(id,source_id,data) VALUES(?,?,?)',(x['candidate_id'],x['source_id'],dump(x)))
 rendered=read('rendered-source-manifest.json');rendered_links=read('rendered-discovered-inventory.json')
 for x in rendered: con.execute('INSERT INTO rendered_source VALUES(?,?,?)',(x['id'],x['url'],dump(x)))
 for x in rendered_links: con.execute('INSERT INTO rendered_candidate(source_id,data) VALUES(?,?)',(x['source_id'],dump(x)))
 faq_sources=read('toss-faq-api-source-manifest.json') if (INPUT/'toss-faq-api-source-manifest.json').exists() else []
 faq_docs=read('toss-faq-document-candidates.json') if (INPUT/'toss-faq-document-candidates.json').exists() else []
 faq_categories=read('toss-faq-category-completeness.json')
 faq_gaps=[x for x in faq_categories if not x['cardinality_and_pagination_complete']]
 faq_lookup={}
 for i,x in enumerate(faq_sources):
  fid=x.get('id',x.get('source_id',str(i)));url=x.get('url',x.get('source_url'));digest=x.get('raw_sha256',x.get('source_raw_sha256'))
  assert url and digest,'FAQ source provenance missing'
  con.execute('INSERT INTO faq_source VALUES(?,?,?)',(fid,url,dump(x)));faq_lookup[url,digest]=fid
 assert not faq_docs or faq_sources,'FAQ docs require original API source manifest'
 for i,x in enumerate(faq_docs):
  assert not x.get('accepted_benchmark')
  did=x.get('id',x.get('candidate_id'));assert did,'stable FAQ document ID missing'
  con.execute('INSERT INTO faq_document_candidate(id,data) VALUES(?,?)',(did,dump(x)))
  assert x.get('observations'),'FAQ document proof missing'
  for obs in x['observations']:
   fid=faq_lookup.get((obs['source_url'],obs['source_raw_sha256']));assert fid,'FAQ source/hash mismatch'
   assert obs.get('json_pointer'),'FAQ JSON locator missing'
   con.execute('INSERT INTO faq_observation(document_id,source_id,data) VALUES(?,?,?)',(did,fid,dump(obs)))
 labels={'wise':('Wise','https://wise.com/help/'),'monzo':('Monzo','https://monzo.com/help'),'paypal-us':('PayPal US','https://www.paypal.com/us/cshelp/personal'),'toss-bank':('토스뱅크','https://www.tossbank.com/'),'toss-platform':('토스','https://support.toss.im/faq'),'citimanager':('CitiManager','https://www.citibank.com/tts/sa/commercial_cards/training/')}
 providers=[]
 for pid,count in con.execute('SELECT provider_id,count(*) FROM source_snapshot GROUP BY provider_id'):
  rows=[x for x in ledger if x['provider_id']==pid];p=summary.get('per_provider',{}).get(pid,{})
  providers.append({'id':pid,'label':labels.get(pid,(pid,''))[0],'index_url':labels.get(pid,(pid,''))[1],'source_count':count,'article_count':p.get('body_article_documents',0)+p.get('product_body_documents',0)+(len(faq_docs) if pid=='toss-platform' else 0),'pdf_count':p.get('pdf_documents',0),'pdf_pages':p.get('pdf_pages',0),'discovered_urls':con.execute('SELECT count(DISTINCT url) FROM discovered_candidate WHERE provider_id=?',(pid,)).fetchone()[0],'accepted_count':0,'note':'토스 FAQ 공개 응답 본문 1,020건. API 출처는 별도 집계. 업체·시장·역할·앱 버전은 개별 검토 필요.' if pid=='toss-platform' else '공개 자료 발견·원문 보존 단계. 개별 시장·역할·현재 앱 화면은 별도 검증 필요.'})
 counts={'source_count':len(ledger),'candidate_inventory_rows':len(inventory),'distinct_candidate_urls':con.execute('SELECT count(DISTINCT url) FROM discovered_candidate').fetchone()[0],'procedure_candidate_count':len(procedures),'faq_document_candidates':len(faq_docs),'faq_api_sources':len(faq_sources),'rendered_index_snapshots':len(rendered),'rendered_candidate_rows':len(rendered_links)}
 for key in ['source_count','candidate_inventory_rows','distinct_candidate_urls']:
  if key in summary: assert summary[key]==counts[key],f'run summary mismatch: {key}'
 assert summary['unadjudicated_canonical_reference_inventory_rows']==len(inventory)
 summary={**summary,**counts,'body_documents_total':sum(p['article_count'] for p in providers)};inputs={f.name:sha(f) for f in sorted(INPUT.glob('*.json'))}
 con.execute('INSERT INTO run_metadata VALUES(?,?)',('summary',dump(summary)));con.execute('INSERT INTO run_metadata VALUES(?,?)',('input_hashes',dump(inputs)))
 assert not con.execute('PRAGMA foreign_key_check').fetchall();con.commit();con.close();path.replace(ROOT/'data/collection.sqlite')
 report={'version':'WGSS definition contract 1.1 / discovery snapshot 2026-10-02','global_mece_total':None,'methodology':{'unit':'한 행위자가 직접 달성하려는 하나의 업무 결과','rules':['행위자 역할 + 직접 대상 타입 + 의도된 결과 + 필요한 의미 구분자로 업무를 정의합니다.','고객 업무·금융사 처리·공통 지원 업무를 구분합니다. 인증은 여러 여정에서 재사용합니다.','업체·시장·언어·채널·정책은 사례의 조건입니다. 처리중·성공·실패는 업무 상태입니다.','포함·제외 조건과 가장 가까운 유사 업무의 구분 근거를 반드시 기록합니다.','은행·결제·대출·투자·보험·연금·무역금융·이슬람금융·가상자산을 누락 감사 대상으로 둡니다.'],'gates':[{'id':'G1','label':'표준별 역할·단위 분리','status':'방법 채택'},{'id':'G2','label':'원본 집합과 버전 대조','status':'BIAN 산출물 차이 미해결'},{'id':'G3–G4','label':'업무별 정의와 의미 중복 검토','status':'신규 후보 검토 전'},{'id':'G5','label':'명시한 자료 목록의 모든 후보 판정','status':'미완료'},{'id':'G6','label':'은행 밖 범위 누락 감사','status':'미완료'},{'id':'G7','label':'경계·정책·화면 각각의 근거 검증','status':'신규 후보 검토 전'},{'id':'G8','label':'업무·자료·표준 수 별도 집계','status':'적용'}]},'standards':[{'name':'ISO 20022','unit':'현재 수록 BusinessComponent 객체','count':791,'source_url':'https://www.iso20022.org/iso20022-repository/business-model','note':'객체·관계 근거. 고객 업무 총수가 아닙니다.'},{'name':'BIAN Matrix 14 snapshot','unit':'ServiceDomain 속성 노드','count':341,'source_url':'https://bian.org/servicelandscape-14-0-0/views/view_54081.html','note':'339 stereotype + 2 속성 식별. 공식 PDF 총수 322와 미해결 차이.'},{'name':'BIAN BCM 14 snapshot','unit':'업무 역량 계층 노드','count':586,'source_url':'https://bian.org/servicelandscape-14-0-0/views/view_53866.html','note':'범위 점검용. 내부 운영도 포함하며 거래 총수가 아닙니다.'},{'name':'FIBO','unit':'현재 4개 영역에서 수록한 named schema term','count':1549,'source_url':'https://spec.edmcouncil.org/fibo/','note':'금융 개념·관계 근거. 전체 FIBO 수록을 뜻하지 않습니다.'},{'name':'NIST SP 800-63-4','unit':'현재 수록 informative glossary 용어','count':189,'source_url':'https://pages.nist.gov/800-63-4/sp800-63.html','note':'신원 확인·인증·연합 근거. 금융거래 분류가 아닙니다.'},{'name':'NIST SP 800-63-4 선택절','unit':'선택한 원문 섹션','count':19,'source_url':'https://pages.nist.gov/800-63-4/sp800-63.html','note':'전체 절 수가 아닙니다. glossary 용어와 별도로 집계합니다.'}],'discrepancies':['BIAN 공식 Release Notes: 도메인 322·API 242. 공개 Matrix snapshot: 노드 341·고정 API 저장소 파일 258. 차이 원인 미해결.','표준 노드 수, 발견 URL, 문서 목차, 승인 업무는 다른 단위입니다. 합산하거나 전체 금융 완성률로 표시하지 않습니다.'],'collection':{'summary':summary,'providers':providers},'input_hashes':inputs,'database_sha256':sha(ROOT/'data/collection.sqlite'),'active_corpus_unchanged':True}
 report['collection']['category_gaps']=[{'label':x['label'],'declared_counts':x['declared_counts_observed'],'observed_unique':x['unique_native_documents_seen']} for x in faq_gaps]
 report['collection']['separate_source_units']={'static_snapshots':len(ledger),'rendered_index_snapshots':len(rendered),'faq_api_snapshots':len(faq_sources)}
 report['discrepancies'] += [f"토스 FAQ {x['label']}: 원문 표시 {x['declared_counts_observed']}개 / 관측 고유 {x['unique_native_documents_seen']}개. 페이지 탐색 종료와 항목 수 일치는 별개이며 해당 범위 완전성은 미승인." for x in faq_gaps]
 (ROOT/'dist/data/definition-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(dump({'status':'built','counts':counts,'global_mece_total':None,'accepted_new_benchmarks':0}))
if __name__=='__main__':build()
