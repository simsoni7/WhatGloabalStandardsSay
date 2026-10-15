"""One-time root-authored priority evidence dispositions; no automatic model admission."""
import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-priority-v25-20261011';SUP=R/'research/source-store/bank-priority-v25-supplement-20261011'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 dest=R/'data/bank-ui-collection-v25-decisions.json';assert not dest.exists(), 'Never rerun a recorded root batch'
 bank=read(R/'data/bank-ui-benchmark-dispositions.json');assert len(bank['examples'])==49
 sources={};proposals={};runs=[]
 for prefix,directory in [('V25',RUN),('V25S',SUP)]:
  sources.update({prefix+':'+x['id']:x for x in read(directory/'sources.json')})
  for p in sorted((directory/'reviews').glob('*/*/proposal.json')):
   d=read(p);runs.append({k:d[k] for k in ['job_id','model','prompt_sha256','usage']}|{'source_batch':prefix})
   for row in d['result']['rows']:
    for feature in row.get('features',[]):
     for id in feature['work_ids']:
      proposals[(prefix+':'+row['source_id'],feature['native_expression'],id)]=(feature,d['job_id'])
 plan=read(R/'data/bank-ui-collection-plan.json');work_ids={i for g in plan['priority_groups'] for i in g['ui_work_ids']}
 decisions=[];image_rows=read(RUN/'guide-images.json');images={i['id']:i for i in image_rows}
 def wid(short):
  full='WGSS-UI-'+short;assert full in work_ids;return full
 def proof(s,q):
  start=s['text'].index(q);return {'kind':'normalized_text_character_range','start':start,'end':start+len(q),'excerpt':q}
 def add(source,short,label,meaning,steps=(),qualifiers=(),channel='공식 앱 이용 안내',job=None):
  s=sources[source];id=wid(short);assert label in s['text']
  b={'id':f'BANK-BENCH-{len(bank["examples"])+1:03d}','source_id':source,'ui_work_ids':[id],
     'provider_id':s['provider_id'],'provider_name':{'hsbc-uk':'HSBC UK','hsbc-hk':'HSBC Hong Kong','kakao':'카카오뱅크','toss':'토스뱅크'}[s['provider_id']],
     'country':s['country'],'language':s['language'],'channel':channel,'expression':label,
     'expression_type':'공식 자료의 기능 표제 또는 문서에서 설명한 UI 문구','meaning':meaning,
     'conditions':' '.join(x['description_ko'] for x in qualifiers) or '이 자료에서 이 기능의 상세 적용 조건을 확인하지 못했습니다. 추가 확인이 필요합니다.',
     'source_url':s['resolved_url'],'raw_sha256':s['raw_sha256'],'text_sha256':s['text_sha256'],'proof':proof(s,label),
     'function_proof':None,'collected_at':'2026-10-11','root_function_admitted':True,
     'policy_admission':'only_explicit_qualifications_no_global_policy','policy_status':'source_specific_qualifications_only',
     'policy_claims':[{'description_ko':x['description_ko'],'proof':proof(s,x['proof_quote'])} for x in qualifiers],
     'flow_steps':[x['description_ko'] for x in steps],'flow_step_proofs':[proof(s,x['proof_quote']) for x in steps],
     'evidence_type':'official_public_function_document','observed_app_screen':False,'verified_ui_version':None,'app_os':None}
  bank['examples'].append(b);decisions.append({'example_id':b['id'],'source_id':source,'work_id':id,'root_decision':'admit','review_basis':'own customer outcome, native expression and scoped qualifiers checked','model_job':job,'automatic_adoption':False});return b
 def use(source,label,short,meaning,steps=None,qualifiers=None,channel='공식 앱 이용 안내'):
  feature,job=proposals[(source,label,wid(short))]
  b=add(source,short,label,meaning,feature.get('flow_steps',[]) if steps is None else steps,
        feature.get('conditions',[]) if qualifiers is None else qualifiers,channel,job)
  b['function_proof']=proof(sources[source],feature['proof_quote']);return b
 def step(desc,q):return {'description_ko':desc,'proof_quote':q}
 def attach(b,image_id,labels,description):
  im=images[image_id];assert im['source_id']==b['source_id'];s=sources[b['source_id']]
  assert any(i['url']==im['asset_url'] for i in s['images'])
  path='evidence/bank-v25/'+image_id+im['public_extension'];out=R/'dist'/path;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/im['private_path'],out)
  b.update(evidence_type='official_guide_screen',screen_evidence={'image_path':path,'image_sha256':im['sha256'],'asset_url':im['asset_url'],'source_locator':im['image_locator'],'description_ko':description,'labels':labels,'image_derivation':'unmodified_original_official_asset','visual_review':'root_visual_checked','independent_human_review':False,'source_version':None,'screen_role':'illustrative_action_entry_or_form','limitation_ko':'공식 설명용 화면. 표시 인물·계좌·금액·기기 정보는 예시이며 설치 앱·UI 버전·실제 거래를 관찰한 결과가 아닙니다.'})
 # Reviewed English guides: keep app/online paths separate and reject history-document confusion.
 for label,short,meaning in [('Set up a standing order','0E34959F2794','고객이 고정 주기 지급지시를 등록'),('Cancel a standing order','CC40B2B0BFB3','고객이 기존 정기지급 지시를 중지'),('Amend a standing order','37D8DD5B6DD8','정기지급 금액 변경; 그 외 상세 변경은 취소 후 재등록')]:
  use('V25:uk-standing',label,short,meaning)
 use('V25:uk-payments','Add a new payee','BE3E28DEF349','수취인 정보 등록과 수취인 정보 확인; 실제 송금 실행과 구분')
 use('V25:uk-payments','Transfer money between your HSBC accounts','E7352823594F','본인 HSBC 계좌 간 이체 지시 제출')
 b=use('V25:uk-close','Close account','4012B26180F6','잔여 잔액과 미결 거래를 정리한 뒤 계좌를 종료')
 for q,desc in [('We can\'t complete account closure through your app between 21:45 and 03:00.','앱 계좌 종료는 현지 21:45~03:00 점검 중 제한됩니다.'),('If you do have pending transactions, they need to be cleared before your account can be shut down.','미결 거래 정리 후 종료할 수 있습니다.')]:
  b['policy_claims'].append({'description_ko':desc,'proof':proof(sources[b['source_id']],q)});b['conditions']+=' '+desc
 use('V25:uk-statements','certificate of interest','F695E90DA8E7','이자 증명서 PDF 확인·수령')
 for label,short,meaning in [('Freeze card','F4EC0C60B176','카드의 임시 사용 잠금'),('Unfreeze card','C45F080F8F9A','임시 사용 잠금 해제; 분실신고 철회와 구분')]:use('V25:uk-block',label,short,meaning)
 for label,short,meaning in [('Report a lost or stolen card','B840FB22717E','카드 분실·도난 신고 후 교체 발급 절차'),('Replace a damaged card','FEB82BBD0285','손상된 카드의 교체 발급 신청')]:use('V25:uk-lost',label,short,meaning)
 use('V25:uk-register','Setting up a Mobile Banking PIN','8D6F981E0EF8','디지털뱅킹 등록 중 모바일 인증 PIN 설정',channel='공식 디지털뱅킹 등록 안내')
 use('V25:uk-international','Track global payments','44B3F0605C30','국제 송금의 처리 진행상태 조회',channel='공식 온라인뱅킹 이용 안내')
 f=proposals[('V25S:uk-activate','Activate your card',wid('9BA0A71D5DA5'))][0]
 use('V25S:uk-activate','Activate your card','9BA0A71D5DA5','신규 카드 사용 활성화',steps=f['flow_steps'][:1],qualifiers=[],channel='공식 모바일 앱 카드 활성화 안내')
 use('V25S:uk-pin','view your card PIN on screen','4C651EE831D1','앱에서 카드 PIN 조회; 채널 로그인 PIN과 구분')
 use('V25S:uk-creditlimit','Credit limit increase','86F2DD937522','신용카드 한도 증액 심사 신청; 즉시 승인·효력 발생을 주장하지 않음')
 # Korean credit and card application outcomes with their own source context.
 use('V25:kakao-card','[간편결제 등록하기] 버튼','ACC94DC0E603','체크카드 신청 완료 화면에서 카카오페이·ISP/페이북·삼성페이에 카드 등록')
 for label,short,meaning in [('한도/금리 조회','56DCD16215A9','개인별 마이너스통장 대출 한도·금리 조회'),('모바일 대출 계약서 작성','698D2CE7A1AA','확인한 대출조건에 대한 신청서 작성 단계; 계약 성립과 실행 결과는 구분'),('금리인하 요구권','86F2DD937522','신용상태 변화에 따른 금리변경 심사 신청'),('휴일에도 앱에서 직접 상환','314E135C277E','앱을 통한 대출 상환금 납입')]:
  use('V25:kakao-overdraft',label,short,meaning)
 use('V25:kakao-remittance','"송금하기" 버튼','E7352823594F','해외 송금 정보·환율·금액 확인 후 송금 지시 제출')
 use('V25:toss-card','카드 만들기','3826A2FD05F2','토스뱅크 체크카드 신청 진입점',channel='공식 상품 웹의 앱 연결 버튼')
 b=use('V25:kakao-customer','분실 신고는 1599-3333','B840FB22717E','카드·OTP·휴대폰 분실 사실 신고',channel='공식 전화 ARS 이용 안내');b['described_channels']=['telephone_ivr']
 b=use('V25:kakao-customer','새 카드 사용 등록','9BA0A71D5DA5','전화 ARS에서 새 카드 사용 등록',channel='공식 전화 ARS 이용 안내');b['described_channels']=['telephone_ivr']
 for label,image_id,short_label,meaning in [('AI 이체','kr-transfer-1','AI로 이체하기','최근·자주 쓰는 수취 계좌를 선택하는 송금'),('사진이체','kr-transfer-2','카메라 버튼','사진으로 계좌번호 인식 후 고객이 확인하여 송금'),('예약이체','kr-transfer-3','예약이체','단일 송금의 미래 실행일 지정; 반복 정기이체 등록을 입증하지 않음')]:
  b=use('V25S:kakao-transfer-how',label,'E7352823594F',meaning);attach(b,image_id,[short_label],'송금 선택·정보 입력 단계의 공식 안내 이미지')
 b=use('V25S:kakao-bills','납부 확인증','F695E90DA8E7','세금·공과금 납부 확인증 발급·수령; 독립적인 법적 증명 효력은 보장하지 않음')
 attach(b,'kr-bills-5',['납부확인증'],'세금 납부 확인증의 공식 설명용 예시')
 b['conditions']='이미지의 하단 안내는 거래 참고용이며 법적 효력이 없다고 설명합니다. 계좌·납부자·금액은 예시입니다.'
 # Native Chinese guides. Root manual selections supplement advisory extraction.
 sec='V25:hk-zh-security'
 b=add(sec,'F94E9EA98403','驗證您的身分','신분증 촬영과 셀카로 고객 신원확인',
  [step('홍콩 신분증 원본 촬영','將您的香港身份證正本置於簡潔的背景上拍攝。'),step('밝은 곳에서 셀카 촬영','以素色背景拍攝自拍照。')],
  [step('2018년식 홍콩 스마트 신분증을 가진 만 11세 이상 고객 경로','如果您年滿11歲並持有新版香港智能身份證（2018年版本）')]);attach(b,'hk-id',['拍攝身份證'],'신분증 원본 촬영 전의 공식 안내 화면')
 b=add(sec,'8D6F981E0EF8','流動理財PIN','6자리 모바일 인증 PIN 설정',
  [step('디지털뱅킹 등록 후 6자리 PIN 설정','最後請設定您的6位數字「 流動理財PIN 」')],
  [step('지원 기기에서 생체인증도 선택적으로 활성화 가능','您亦可於支援的裝置上選擇啟動生物認證')]);attach(b,'hk-bind-pin',['設定6位數字流動理財PIN'],'6자리 PIN 설정 입력 화면의 공식 예시')
 b=add(sec,'4C73650B5797','更改流動理財PIN','기존 인증 PIN을 입력하고 새 모바일 PIN으로 변경; 분실 복구와 구분',
  [step('메뉴 → 프로필 → 保障您的戶口安全 → 管理裝置','開啟HSBC HK App，點擊選單圖示，然後點選頭像圖示。在「保障您的戶口安全」下選擇「管理裝置」。'),step('更改流動理財PIN 선택 후 현재 PIN 입력','選擇「更改流動理財PIN」並輸入您的流動理財PIN。')]);attach(b,'hk-change-pin-menu',['更改流動理財PIN'],'PIN 변경 메뉴의 공식 안내 예시')
 b=add(sec,'57106ED8458D','獲取保安編碼','인터넷뱅킹 접속 인증용 보안 코드 생성과 입력',
  [step('로그인 전 앱에서 보안코드 가져오기 선택','停留在登入頁面並不要登入，在畫面下方選擇「獲取保安編碼」。')],
  [step('잘못된 PIN·수동 기기 시간·보안수단 제거 시 무효 코드 위험','您手機的時間並沒有設為「自動」')]);attach(b,'hk-get-code',['獲取保安編碼'],'로그인 전 보안코드 생성 진입점 공식 예시')
 faq='V25S:hk-zh-mobile-faq-www'
 for old,label,short,meaning in [('啟動新卡','啟動新卡','9BA0A71D5DA5','카드 최초 활성화'),('暫時封鎖我的信用卡','封鎖卡','F4EC0C60B176','카드의 임시 사용 잠금'),('解鎖信用卡','解鎖卡','C45F080F8F9A','임시 사용 잠금 해제'),('報失並申請補發新卡','報失並申請補發新卡','B840FB22717E','카드 분실 신고와 교체 신청으로 연결되는 진입점'),('申請補發新卡','申請補發新卡','FEB82BBD0285','거래 이의제기 후 카드 재발급 신청 진입점'),('繳付款項','繳付款項','314E135C277E','카드 청구대금 납부 진입점'),('查閱過往多久的交易紀錄','查閱交易紀錄','591B10169113','계좌별 최근 거래내역 조회; 유형별 기간 제한')]:
  feature,job=proposals[(faq,old,wid(short))];b=add(faq,short,label,meaning,feature.get('flow_steps',[]),feature.get('conditions',[]),job=job);b['function_proof']=proof(sources[faq],feature['proof_quote'])
 use(faq,'申請循環「萬應錢」','698D2CE7A1AA','현지 한도대출 신청; 홍콩 거주자·성인·소득 요건')
 b=bank['examples'][-1];q='必須為香港居民。 必須年滿十八歲或以上。';b['policy_claims']=[{'description_ko':'홍콩 거주 만 18세 이상이며 등록 연락처·주소와 월 HKD 5,000 이상 소득 등 요건이 있습니다.','proof':proof(sources[faq],q)}];b['conditions']=b['policy_claims'][0]['description_ko']
 internet='V25S:hk-zh-internet-faq-www'
 add(internet,'BE3E28DEF349','新增受款人','인터넷뱅킹에서 수취인 주소록 등록',
  [step('轉賬及繳費 → 管理受款人／轉賬 → 新增受款人','在頂部選單下的「轉賬及繳費」 > 「管理受款人／轉賬」 >「新增受款人」')],
  [step('등록 시 보안코드 필요; 현지 접수 시간에 따라 다음 또는 둘째 영업일 효력','您可使用保安編碼器或流動保安編碼')],channel='공식 인터넷뱅킹 이용 안내')
 add(faq,'87A044308A2E','刪除自動轉賬指示','직접출금 동의 철회; 고정 금액 정기지급 중지와 구분',
  [step('관리 중인 출금동의에서 삭제 선택','如需要取消現行自動轉賬指示，您可點選「刪除自動轉賬指示」。')])
 # Scope is fixed: all 96 priority cells get a bounded public-source assessment,
 # not a claim that all nine providers or all possible sources were exhausted.
 root={'scope_version':'bank-customer-ui-v1','denominator':214,'scope_change':False,'reviewed_at':'2026-10-11',
       'model_runs':runs,'admitted_examples':decisions,'source_batches':[{'prefix':'V25','manifest':str((RUN/'sources.json').relative_to(R))},{'prefix':'V25S','manifest':str((SUP/'sources.json').relative_to(R))}],
       'rejected_findings':[
        {'source_id':'V25:uk-mobile','label':'remove your lost or stolen device','reason_ko':'분실한 기기의 접근 제거는 분실신고 철회가 아님'},
        {'source_id':'V25:uk-statements','label':'View statements','reason_ko':'발급 명세서 조회를 대화형 거래내역 조회로 연결하지 않음'},
        {'source_id':faq,'label':'自動轉賬','reason_ko':'홍콩 직접출금 동의를 고정 금액 정기지급 등록·변경·중지로 연결하지 않음'},
        {'source_id':'V25:hk-zh-limit','label':'提高信用卡限額申請','reason_ko':'기존 심사 신청의 증빙 업로드 페이지를 신규 심사 신청 제출로 입증하지 않음'},
        {'source_id':'V25S:uk-pin','label':"'Unlock' the card",'reason_ko':'PIN 오입력 복구 경로를 임시 잠금의 해제 경로로 일반화하지 않음'},
        {'source_id':'V25S:kakao-bills','label':'세금/공과금 납부','reason_ko':'세금·공과금 지급을 수취인 송금으로 단정하지 않음; 우선 수집 32개 밖의 업무는 이번 연결에서 제외'},
        {'source_id':'V25:kakao-loan-comparison','label':'바로 대출 신청을 할 수 있어요','reason_ko':'타 금융사로 이동하는 설명을 카카오뱅크 직접 대출 신청의 근거로 삼지 않음'}],
       'source_failures_retained':[{'source_id':prefix+':'+x['id'],'error_type':x.get('error_type'),'retry_batch':'V25S' if x.get('error_type')=='ValueError' else None} for prefix,directory in [('V25',RUN)] for x in read(directory/'sources.json') if x['state']=='fetch_failed'],
       'automatic_adoption':False,'independent_human_review':False}
 audits=[]
 for id in sorted(work_ids):
  for country in ['KR','GB','HK']:
   reviewed=[sid for sid,s in sources.items() if s['country']==country and s.get('text')]
   examples=[b for b in bank['examples'] if b['country']==country and id in b['ui_work_ids']]
   paired=[b for b in examples if b.get('flow_steps') and b.get('policy_claims')]
   next_action='현지 금융사의 기능·정책 근거 추가 수집' if not examples else '공식 화면 예시 추가 수집' if not any(b.get('screen_evidence') for b in examples) else '상세 적용 조건·처리 결과 추가 확인' if not paired else '다른 현지 플랫폼과 비교·화면 버전 확인'
   audits.append({'id':id+':'+country,'ui_work_id':id,'country':country,'state':'reviewed_public_batch','reviewed_source_ids':reviewed,'reviewed_provider_ids':sorted({sources[x]['provider_id'] for x in reviewed}),
     'method_ko':'등록한 국가별 공식 안내 문서를 우선 업무 정의와 대조. 대상 금융사 전체·기능 전체의 완전 탐색은 아님.','next_action_ko':next_action,'provider_unsupported':False,'root_reviewed':True,'automatic_adoption':False})
 root['priority_cell_dispositions']=audits;write(dest,root)
 bank['collection_batches'].append({'batch':'collection-v25','root_ledger':'data/bank-ui-collection-v25-decisions.json','scope_change':False});write(R/'data/bank-ui-benchmark-dispositions.json',bank)
 plan['plan_version']='collection-v25';plan['priority_audit_ledger']='data/bank-ui-collection-v25-decisions.json';plan['latest_execution']={'batch':'collection-v25','source_targets':44,'source_retries':7,'admitted_new_examples':len(decisions),'bedrock_successful_jobs':len(runs),'actual_app_captures':0,'priority_work_country_cells':96,'root_reviewed_cells':96};write(R/'data/bank-ui-collection-plan.json',plan)
 print(json.dumps({'new_examples':len(decisions),'total_examples':len(bank['examples']),'model_jobs':len(runs),'priority_cells':len(audits)},ensure_ascii=False))
if __name__=='__main__':main()
