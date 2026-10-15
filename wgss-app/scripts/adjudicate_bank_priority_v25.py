"""Root correction of the completed Opus critique, preserving before/after evidence."""
import copy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-priority-v25-20261011'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 output=R/'data/bank-ui-collection-v25-steward-dispositions.json';assert not output.exists()
 bank=read(R/'data/bank-ui-benchmark-dispositions.json');before=copy.deepcopy(bank['examples']);by={b['id'][-3:]:b for b in bank['examples']}
 src={p+':'+s['id']:s for p,n in [('V25','bank-priority-v25-20261011'),('V25S','bank-priority-v25-supplement-20261011')] for s in read(R/'research/source-store'/n/'sources.json')}
 def pf(b,q,after=0):
  t=src[b['source_id']]['text'];start=t.index(q,after);return {'kind':'normalized_text_character_range','start':start,'end':start+len(q),'excerpt':q}
 def claim(b,desc,q):return {'description_ko':desc,'proof':pf(b,q)}
 def conditions(b,items):b['policy_claims']=items;b['conditions']=' '.join(x['description_ko'] for x in items)
 def flow(b,items):b['flow_steps']=[x[0] for x in items];b['flow_step_proofs']=[pf(b,x[1]) for x in items]
 # Native proof for each condition, with the correct path or channel scope.
 b=by['052'];conditions(b,[claim(b,'증액은 지급 예정일 2일 전 23:45까지 가능','You can increase the payment amount up to 2 days before the scheduled payment date, until 23:45.'),claim(b,'감액은 지급일 전날 23:45까지 가능','You can decrease the amount until 23:45 the day before.'),claim(b,'금액 외 정보 변경은 기존 지시 취소 후 새로 등록','If you want to change any other details, you\'ll need to cancel the existing standing order and set up a new one.')])
 by['053']['meaning']='수취인 계좌·정보를 입력하여 주소록 항목 등록; 정보 확인은 등록 절차의 단계'
 b=by['056'];conditions(b,[claim(b,'종이본·특정 기간 증명서는 채팅으로 별도 요청','If you\'d like a paper copy or a certificate for a specific time frame, chat with us in the mobile banking app to request one.'),claim(b,'별도 요청한 증명서는 10영업일 내 수령, 앱에는 2영업일 내 반영','Once we\'ve got your request, you should receive the certificate within 10 working days and it will be available on the app within 2 working days.')])
 b=by['059'];b['meaning']='카드 분실·도난 사실 신고 접수; 후속 교체 발급은 별 업무';b['flow_steps']=b['flow_steps'][:1];b['flow_step_proofs']=b['flow_step_proofs'][:1];b['policy_claims']=[];b['conditions']='이 단계는 분실·도난 사실 신고 접수입니다. 교체 카드 발급·배송은 별도 업무와 후속 조건으로 확인하세요.'
 b=by['060'];t=src[b['source_id']]['text'];context=t.index('Replace a damaged card',11000)
 for field in ['function_proof']:
  q=b[field]['excerpt'];b[field]=pf(b,q,context)
 b['flow_step_proofs']=[pf(b,q['excerpt'],context) for q in b['flow_step_proofs']]
 b=by['061'];conditions(b,[claim(b,'등록 시 모바일 PIN 설정이 필요하며 최대 3개 기기에 앱 설정 가능','During registration you\'ll be asked to set up a Mobile Banking PIN.'),claim(b,'처음 설정한 기기 외 2개 기기에 추가 설정 가능','Once you\'ve set up your new PIN to access the app, you\'ll be able to set up the app on 2 other devices.')]);b['policy_claims'][0]['description_ko']='등록 시 모바일 PIN 설정 필요';b['conditions']='등록 시 모바일 PIN 설정 필요. 처음 설정한 기기 외 2개 기기에 추가 설정 가능.';b['meaning']='디지털뱅킹 등록 과정에서 앱 접속용 PIN 설정; 단순 PIN 변경이나 로그인 인증과 구분'
 b=by['063'];conditions(b,[claim(b,'만료일이 2027년 12월 이상인 직불카드, 활성화 스티커 없는 신용카드는 별도 활성화 불필요','Debit cards with an expiry date of December 2027 or later, and credit cards without an activation sticker, are ready to be used, so you won\'t need to activate them.')])
 by['068']['meaning']='표제는 대출 계약서 작성이나 자체 설명은 신청서 작성 단계입니다. 신청서 제출과 별도의 계약 성립·실행은 구분합니다.'
 b=by['070'];b['meaning']='이자납입일 지급가능 금액 부족 시 앱에서 약정 상환금 납입; 임의 원금 선상환과 구분';conditions(b,[claim(b,'이자납입일 지급가능 금액 부족 시 연체 위험이 있어 해당일 자금 입금 또는 앱 직접 상환 안내','지급가능금액이 부족한 경우, 연체이자가 발생할 수 있으므로 상환자금을 해당일 중 입금하시거나 휴일에도 앱에서 직접 상환할 수 있습니다.')])
 # Replace unsupported card-entry attribution with an own application-completion guide.
 b=by['072'];s=src['V25:toss-card-how'];b.update(source_id='V25:toss-card-how',source_url=s['resolved_url'],raw_sha256=s['raw_sha256'],text_sha256=s['text_sha256'],channel='공식 앱 카드 신청 이용 안내',expression='카드 만들기',meaning='앱에서 카드 디자인·영문 이름을 선택한 뒤 카드 발급 신청 완료')
 b['proof']=pf(b,'카드 만들기');b['function_proof']=pf(b,'카드 디자인과 영문 이름을 선택한 뒤 신청을 완료해요.')
 flow(b,[('전체 탭 → 토스뱅크','토스 앱에서 [전체 탭] → [토스뱅크]를 선택해요.'),('토스뱅크 체크카드 → 카드 만들기','[토스뱅크 체크카드]에서 [카드 만들기]를 눌러요.'),('디자인·영문 이름 선택 후 신청 완료','카드 디자인과 영문 이름을 선택한 뒤 신청을 완료해요.')])
 conditions(b,[claim(b,'토스뱅크 계좌 보유 고객을 위한 신청 안내 경로','이미 토스뱅크 계좌가 있다면 몇 단계만 거쳐 카드를 만들 수 있고')])
 by['074']['meaning']='전화 ARS 처리 가능 업무 목록의 새 카드 사용 등록. 구체 조작 경로·카드 범위는 미확인'
 b=by['078'];b['conditions']='공식 예시 이미지 하단에 법적 효력이 없으며 거래 참고용이라는 안내가 있습니다. 원문 본문의 별도 효력 설명은 미확인입니다. 인물·계좌·금액은 예시입니다.'
 b=by['079'];b['function_proof']=pf(b,'選擇「繼續」以開始使用香港身份證來驗證您的身分。')
 b=by['080'];b['function_proof']=pf(b,'最後請設定您的6位數字「 流動理財PIN 」；您亦可於支援的裝置上選擇啟動生物認證');b['meaning']='신분 확인·디지털뱅킹 등록 후 해당 앱 기기에 접속용 PIN과 선택적 생체인증 설정. 자발적 PIN 변경과 구분'
 b=by['081'];b['function_proof']=pf(b,'選擇「更改流動理財PIN」並輸入您的流動理財PIN。')
 # Reframe token generation as an intermediate step of the actually documented login flow.
 b=by['082'];b.update(expression='登入滙豐網上理財',meaning='사용자명과 앱에서 생성한 보안코드를 입력하여 인터넷뱅킹 접속 인증. 코드 생성만으로 인증 완료를 주장하지 않음',channel='공식 인터넷뱅킹 로그인 안내 · 모바일 앱 보안코드 사용')
 b['proof']=pf(b,b['expression']);b['function_proof']=pf(b,'您可以經手機上的HSBC HK App獲取保安編碼，以登入滙豐網上理財')
 flow(b,[('인터넷뱅킹 로그인 페이지에서 사용자명 입력','前往滙豐網上理財 （「登入」 >「滙豐網上理財」）。輸入您的用戶名稱'),('앱에서 보안코드 생성 후 유효시간 안에 인터넷뱅킹에 입력','使用您手機上的HSBC HK App即可 獲取保安編碼 ，並於時效內輸入保安編碼')])
 conditions(b,[claim(b,'신뢰한 브라우저에서 비밀번호로 코드를 대체하면 로그인 접근이 제한될 수 있음','您也可以經「信任的瀏覽器」以個人網上理財的密碼來取代保安編碼，但為保安理由，您的登入將受到限制。')]);b['screen_evidence']['description_ko']='인터넷뱅킹 접속 인증 중 보안코드 생성 진입점의 공식 예시';b['screen_evidence']['screen_role']='intermediate_authentication_step_not_login_completion'
 by['086']['meaning']='카드 분실 신고 진입점. 원어 메뉴에는 후속 재발급도 함께 표시되지만 이 연결의 결과는 분실 신고에 한정'
 b=by['087'];b['proof']=pf(b,b['expression'],b['function_proof']['start']);conditions(b,[claim(b,'미승인 거래 이의제기 제출 확인 화면에서 재발급 신청하는 경로','在確認提交爭議的頁面，選擇「申請補發新卡」。')])
 b=by['089'];t=src[b['source_id']]['text'];p=t.index('查阅') if '查阅' in t else t.index('查閱交易紀錄');b['function_proof']=copy.deepcopy(b['policy_claims'][0]['proof']);b['review_note']='계좌 유형별 거래내역 조회 FAQ 답변으로 기능과 기간을 명시. 조작 경로는 이 자료에서 미확인.'
 b=by['090'];b['function_proof']=pf(b,'可以，如果想透過HSBC HK App申請滙豐循環「萬應錢」，您必須符合以下所有條件：');conditions(b,[claim(b,'홍콩 거주 만 18세 이상','必須為香港居民。 必須年滿十八歲或以上。'),claim(b,'등록한 유효 휴대전화·이메일·주소 필요','必須在我們的紀錄中留有有效的手提電話號碼、電郵地址及住址。'),claim(b,'월 소득 HKD 5,000 이상','每月收入必須達港幣5,000元或以上。')])
 b=by['091'];b['function_proof']=pf(b,'有兩種方法為第三者戶口登記至「我的受款人」：')
 conditions(b,[claim(b,'수취인 등록 시 보안코드 필요','您可使用保安編碼器或流動保安編碼'),claim(b,'평일 21:00 또는 토요일 18:00 전 접수는 다음 영업일, 이후·공휴일은 둘째 영업일 효력','在星期一至五晚上9:00前或星期六下午6:00前遞交，新受款人指示將於下一個工作天生效，若在星期一至五晚上9:00後或星期六下午6:00後或於公眾假期遞交，新受款人指示將於第二個工作天生效。'),claim(b,'새 수취인의 HSBC 계좌로 보내는 글로벌 송금은 신규 등록 6시간 대기 규칙이 별도로 설명됨; 위 일반 등록 시간과 적용 맥락을 구분','為保障客戶在付款轉賬過程中的安全，新增受款人的指示需要6個小時才會生效。')])
 b=by['092'];b['function_proof']=pf(b,'如需要取消現行自動轉賬指示，您可點選「刪除自動轉賬指示」。');conditions(b,[claim(b,'변경·삭제 지시는 토·일·공휴일을 제외한 2영업일 내 수납기관에 전달; 효력은 수납기관 처리에 따름','更改或刪除現有的自動轉賬指示會在兩個營業日內（不包括星期六、日及公眾假期）提交給商戶／機構。生效時間視乎商戶／機構處理指示的時間而定。')])
 # Explicit function proof even where a plain feature heading was the valid proof.
 for b in bank['examples'][49:]:
  if b.get('function_proof') is None:b['function_proof']=copy.deepcopy(b['proof'])
 proposal=read(next((RUN/'reviews/priority-final-boundaries').glob('*/proposal.json')))
 old_by={b['id']:b for b in before};changed=[]
 for b in bank['examples']:
  if b!=old_by[b['id']]:changed.append({'id':b['id'],'before':old_by[b['id']],'after':b,'automatic_adoption':False})
 dispositions=[]
 for row in proposal['result']['rows']:
  decision='retained_after_own_source_correction' if any(x['id']==row['id'] for x in changed) else 'retain_verified_case'
  if row['id']=='BANK-BENCH-089':decision='retain_explicit_read_result_and_period_faq; reject_invented_navigation'
  dispositions.append({'model_finding':row,'root_decision':decision,'automatic_adoption':False})
 write(R/'data/bank-ui-benchmark-dispositions.json',bank)
 ledger=read(R/'data/bank-ui-collection-v25-decisions.json')
 for row in ledger['admitted_examples']:
  b=next(b for b in bank['examples'] if b['id']==row['example_id']);row['source_id']=b['source_id']
 for a in ledger['priority_cell_dispositions']:
  rows=[b for b in bank['examples'] if a['country']==b['country'] and a['ui_work_id'] in b['ui_work_ids']]
  paired=any(b.get('flow_steps') and b.get('policy_claims') for b in rows)
  a['next_action_ko']='현지 금융사의 기능·정책 근거 추가 수집' if not rows else '공식 화면 예시 추가 수집' if not any(b.get('screen_evidence') for b in rows) else '상세 적용 조건·처리 결과 추가 확인' if not paired else '다른 현지 플랫폼과 비교·화면 버전 확인'
 ledger['model_runs'] += [{k:proposal[k] for k in ['job_id','model','prompt_sha256','usage']}|{'source_batch':'V25'}]
 hk=read(next((RUN/'reviews/hk-boundary-review').glob('*/proposal.json')));ledger['model_runs'].append({k:hk[k] for k in ['job_id','model','prompt_sha256','usage']}|{'source_batch':'V25'})
 write(R/'data/bank-ui-collection-v25-decisions.json',ledger)
 write(output,{'model_run':{k:proposal[k] for k in ['job_id','model','prompt_sha256','usage']},'row_dispositions':dispositions,'global_findings':proposal['result']['global_findings'],'root_global_disposition':'Correct explicit condition scopes and ranges, separate outcomes, replace unsupported entry-only application with own completion guide, anchor channel authentication in documented login flow. Images remain guide-only.','changed_rows':changed,'hk_boundary_advisory':hk['result'],'automatic_adoption':False})
 plan=read(R/'data/bank-ui-collection-plan.json');plan['latest_execution']['bedrock_successful_jobs']=len(ledger['model_runs']);plan['release_quality_review']={'batch':'collection-v25','reviewer':'claude-opus-5','rows_reviewed':43,'root_corrected_rows':len(changed),'steward_ledger':str(output.relative_to(R)),'independent_human_review':False};write(R/'data/bank-ui-collection-plan.json',plan)
 print(json.dumps({'reviewed':43,'corrected':len(changed),'bedrock_successful_jobs':len(ledger['model_runs'])}))
if __name__=='__main__':main()
