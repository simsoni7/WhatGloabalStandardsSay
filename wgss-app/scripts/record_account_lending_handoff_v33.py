"""Preserve all bounded v33 account/lending reviews and source-bound handoff."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'research/source-store';OUT=B/'account-lending-handoff-v33-20261013'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
SOURCE_RUNS=['account-lending-collection-v33-20261013','account-lending-followup-v33-20261013','account-lending-final-sources-v33-20261013','account-lending-rate-sources-v33-20261013','account-lending-market-v33-20261013','account-lending-dispute-v33-20261013']
MODEL_RUNS=['account-lending-extraction-v33-20261013','account-lending-followup-extraction-v33-20261013','account-lending-final-extraction-v33-20261013','account-lending-rate-extraction-v33-20261013','account-lending-candidates-v33-20261013','account-lending-corrections-v33-20261013','account-lending-dispute-extraction-v33-20261013','account-lending-dispute-review-v33-20261013','account-lending-owner-final-v33-20261013','account-lending-branch-final-v33-20261013']
if __name__=='__main__':
 assert not(OUT/'FROZEN').exists();ss=[s for n in SOURCE_RUNS for s in read(B/n/'sources.json')];S={'S33:'+s['id']:s for s in ss};baseline=read(B/SOURCE_RUNS[0]/'baseline.json');linked={i for b in baseline['benchmarks']for i in b['ui_work_ids']};W={w['id']:w for w in baseline['works']};assigned=[w for w in baseline['works']if w['id']not in linked and w['domain_id']in ['accounts','savings','lending','identity','servicing']];c=read(B/'account-lending-candidates-v33-20261013/root-candidates.json');examples={b['id']:b for b in c['examples']};critics={};reports=[]
 for n in MODEL_RUNS:
  jobs=list((B/n/'inputs').glob('*.json'));proposals=list((B/n).glob('reviews/*/*/proposal.json'));assert len(jobs)==len(proposals),(n,len(jobs),len(proposals));reports.append(dict(run_dir=str((B/n).relative_to(R)),assigned_jobs=len(jobs),successful_jobs=len(proposals),api_attempt_records=len(list((B/n).glob('reviews/*/*/attempt-*.json'))),all_assigned_complete=True))
  if 'candidates' in n or 'corrections'in n or 'review'in n or 'final'in n and 'extraction' not in n:
   for p in proposals:
    for row in read(p)['result']['rows']:
     if 'status'in row:critics[row['id']]=row|dict(review_run=n)
 for n in ['account-lending-corrections-v33-20261013','account-lending-dispute-review-v33-20261013','account-lending-owner-final-v33-20261013','account-lending-branch-final-v33-20261013']:
  for b in read(B/n/'root-candidates.json')['examples']:examples[b['id']]=b
 recommended=[i for i,r in critics.items()if r['status']=='pass'];staged=[i for i,r in critics.items()if r['status']!='pass'];finalrows=[examples[i]for i in sorted(examples)];source_batches=[dict(prefix='S33',manifest='research/source-store/'+n+'/sources.json')for n in SOURCE_RUNS]
 for b in finalrows:
  s=S[b['source_id']];assert b['raw_sha256']==s['raw_sha256']and b['text_sha256']==s['text_sha256'];p=R/s['snapshot_path'];assert hashlib.sha256((p/s['raw_filename']).read_bytes()).hexdigest()==s['raw_sha256'];assert hashlib.sha256((p/'normalized.txt').read_bytes()).hexdigest()==s['text_sha256']
  for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof']for x in b['policy_claims']]:assert s['text'][q['start']:q['end']]==q['excerpt']
 write(OUT/'root-candidates.json',dict(examples=finalrows,source_batches=source_batches,provider_id_aliases={},recommended_candidate_ids=recommended,staged_candidate_ids=staged,automatic_adoption=False));write(OUT/'critic-results.json',dict(rows=list(critics.values()),original_and_correction_runs_preserved=True,automatic_adoption=False));write(OUT/'job-report.json',dict(runs=reports,successful_jobs=sum(x['successful_jobs']for x in reports),api_attempt_records=sum(x['api_attempt_records']for x in reports),source_records=len(ss),retrieved_records=sum(s['state']=='fetched_pending_review'for s in ss),automatic_adoption=False))
 fs=[]
 for n in MODEL_RUNS:
  if 'extraction'not in n:continue
  for p in(B/n).glob('reviews/*/*/proposal.json'):
   for row in read(p)['result']['rows']:
    for f in row.get('features',[]):fs.append(dict(source_id='S33:'+row['source_id'],work_ids=f['work_ids']))
 audits=[]
 for w in assigned:
  bs=[b for b in finalrows if w['id']in b['ui_work_ids']];positives=[b for b in bs if b['id']in recommended];related={f['source_id']for f in fs if w['id']in f['work_ids']}|{b['source_id']for b in bs}
  sources=[s for s in ss if s.get('research_family')==w['domain_id']or s['id']in [i.removeprefix('S33:')for i in related]]
  disposition='positive_candidate'if positives else'insufficient_direct_result'if related else'no_relevant_source_found'
  reasons=[item for b in bs for item in critics[b['id']].get('findings_ko',[])]
  audits.append(dict(work_id=w['id'],title=w['title'],domain_id=w['domain_id'],disposition=disposition,candidate_ids=[b['id']for b in bs],recommended_candidate_ids=[b['id']for b in positives],reviewed_source_ids=['S33:'+s['id']for s in sources],reason_ko='자체 원문의 직접 고객 결과를 출처에 묶어 검증했습니다. 후보는 루트 최종 승인 전이며 실제 거래·현행 앱 관찰이 아닙니다.'if positives else' '.join(reasons)if reasons else'이번 제한된 원문 집합에서 해당 직접 결과를 입증하는 기능 구간을 찾지 못했습니다. 금융사의 미지원 판정이나 전체 웹 조사 완료가 아닙니다.',next_search_ko=w['title']+'의 고객 요청 경로와 제공기관의 처리 후 효력을 함께 설명하는 공식 도움말·현행 약관·상태 안내를 추가 조사합니다.',provider_support_inferred=False,scope_change=False,review_scope='bounded_39_own_source_records_not_exhaustive_web_census'))
 write(OUT/'gap-audit.json',dict(scope_version='bank-customer-ui-v1.1',denominator=216,assigned_domains=['accounts','savings','lending','identity','servicing'],assigned_unlinked_work_count=len(assigned),rows=audits,source_batches=source_batches,automatic_adoption=False))
 def proof(s,q):i=s['text'].index(q);return dict(kind='normalized_text_character_range',start=i,end=i+len(q),excerpt=q)
 market=[]
 for pid,sid,q,name,country,home,kind,platform in [('ncb-hk','al-ncb-profile','Nanyang Commercial Bank, Limited (referred to as "NCB") began operations in Hong Kong on 14 December 1949.','Nanyang Commercial Bank','HK','https://www.ncb.com.hk/','bank','Personal Mobile Banking / Internet Banking'),('starling-uk','al-starling-sitelegal','a company registered in England and Wales','Starling Bank','GB','https://www.starlingbank.com/','bank','Starling app / Online Banking'),('lombard-uk','al-lombard-market','Available to UK customers for business purposes only.','Lombard','GB','https://www.lombard.co.uk/','asset_finance_provider_brand','Lombard business asset finance')]:
  s=S['S33:'+sid];market.append(dict(id=pid,name=name,country=country,languages=['en-GB'if country=='GB'else'en'],official_url=home,provider_kind=kind,platforms_ko=[platform],research_status_ko='공식 기능 자료와 국가 근거 수집·검토. 실제 앱 관찰 없음.',channels_ko='공식 고객 도움말·모바일 서비스 안내·조건 문서',selection_basis_ko='미연결 고객 결과의 직접 기능 근거 보완용. 시장 대표성 미검증.',representativeness_proven=False,country_proof=dict(source_id='S33:'+sid,url=s['url'],raw_sha256=s['raw_sha256'],text_sha256=s['text_sha256'],proof=proof(s,q)),recommended_primary_target=pid!='lombard-uk',legal_entity_note_ko='Lombard 브랜드의 실제 계약 법인은 개별 계약에서 확인해야 합니다.'if pid=='lombard-uk'else'자체 법인·국가 표기 확인. 금융당국 독립 등록 재검증은 이 조사 범위 밖입니다.'))
 write(OUT/'new-provider-targets.json',dict(providers=market,source_batches=source_batches,automatic_adoption=False));write(OUT/'source-exclusions.json',dict(rows=[dict(source_id='S33:al-hk-bizterms',reason_ko='HTTP 200이나 원문은404 오류 본문'),dict(source_id='S33:al-ncb-faq',reason_ko='HTTP 200이나 본문 정규화 결과0자, 검색 스니펫을 원문 증거로 전용하지 않음'),dict(source_id='S33:al-starling-disputefaq',reason_ko='HTTP 본문46자 앱 셸이며 금융 기능 본문 없음')],automatic_adoption=False))
 write(OUT/'definition-boundary-review.json',dict(rows=[dict(work_id='WGSS-UI-A3E0811BB53C',source_id='S33:al-lombard-lease',reason_ko='정의가 리스 고객의 담보권 취득을 요구하지만 공식 금융리스는 제공자에게 소유권을 유보하고 고객은 사용권을 취득합니다. 은행 서비스 고객 결과로서의 리스계약 정의 역할을 재검토해야 합니다.',scope_change=False),dict(work_id='WGSS-UI-80799C0A539F',source_id='S33:al-nw-poaremove',reason_ko='은행 등록 POA 제거는 가능한 고객 결과지만 OPG에 등록된 법적 권한은 유효하게 남습니다. 현재 정의의 법적 권한 소멸과 은행 서비스 등록 종료를 구분할 루트 판단이 필요합니다.',scope_change=False)],automatic_adoption=False))
 (OUT/'FROZEN').write_text('Completed bounded-source handoff. No source admission, scope edit, observed UI or independent human approval.\n');print({'sources':len(ss),'jobs':sum(x['successful_jobs']for x in reports),'examples':len(finalrows),'recommended':len(recommended),'works':len(assigned),'positive_work_ids':len({i for b in finalrows if b['id']in recommended for i in b['ui_work_ids']})})
