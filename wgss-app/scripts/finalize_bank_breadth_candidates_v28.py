import copy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-breadth-candidates-v28-20261012';FINAL=R/'research/source-store/bank-breadth-final-v28-20261012'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (FINAL/'FROZEN').exists();c=read(RUN/'root-candidates.json');sources={x['source_id']:None for x in c['examples']}
for prefix,name in [('B28','bank-breadth-v28-20261012-own'),('N28','bank-breadth-additional-v28-20261012-own'),('A28','bank-breadth-additional-v28-20261012'),('T28','bank-trade-forms-v28-20261012')]:
 for s in read(R/'research/source-store'/name/'sources.json'):sources[prefix+':'+s['id']]=s
critic=[r for p in RUN.glob('reviews/*/*/proposal.json') for r in read(p)['result']['rows']];assert len(critic)==40
rejected={'BANK-BENCH-149':'mini 비밀번호 재설정은 분실 인증수단 재발급·접근 복구와 동등하지 않음','BANK-BENCH-150':'입금 요청 메시지에 정의가 요구하는 요청 금액 설정을 확인하지 못함','BANK-BENCH-159':'기존 자료는 한도해지 신청 제출만 확인. 효력 있는 한도 종료 자료로 교체해 별도 검토','BANK-BENCH-169':'사업체 전체 인터넷뱅킹 지급한도는 특정 계좌의 운영 한도와 직접 대상이 다름'}
rows=[copy.deepcopy(b) for b in c['examples'] if b['id'] not in rejected];changes=[]
def pf(sid,q):
 t=sources[sid]['text'];i=t.index(q);return {'kind':'normalized_text_character_range','start':i,'end':i+len(q),'excerpt':q}
def edit(bid,**kw):
 b=next(x for x in rows if x['id']==bid);changes.append({'id':bid,'before':{k:b.get(k) for k in kw},'after':kw,'automatic_adoption':False});b.update(kw)
edit('BANK-BENCH-134',meaning='카카오뱅크 인증서의 외부기관 이용(인증) 이력을 모바일앱에서 조회합니다. 발급·삭제·갱신 이력과 구분합니다.',conditions='외부기관 이용 이력은 최대 2년까지 조회할 수 있습니다.',policy_claims=[{'description_ko':'외부기관 이용 이력은 최대2년 조회','proof':pf('B28:kr-faq-13755','이용 이력은 최대 2년까지 조회할 수 있어요.')}],wgss_mapping_note='인증서 생애주기 관리 이력은 이 업무에 포함하지 않고 외부기관 이용(인증) 이력만 연결합니다.')
edit('BANK-BENCH-140',wgss_mapping_note='원문은 알림톡의 10/13 종료 예정을 표시하지만 연도를 명시하지 않았습니다. 채널 선택 참고이며 현재 제공 채널을 실제 앱에서 확인한 것은 아닙니다.')
edit('BANK-BENCH-145',function_proof=pf('B28:kr-faq-9601','보유한 계좌를 모임통장으로 전환합니다.'))
b=next(x for x in rows if x['id']=='BANK-BENCH-153');edit(b['id'],expression='10%씩 모으기',proof=pf(b['source_id'],'10%씩 모으기'),meaning='연결된 개인사업자통장에 들어온 금액의 10%를 부가세박스로 모으는 가변 집금 규칙을 등록합니다.',conditions='10%씩 모으기 모드에 한정합니다. 매일 자정 하루 입금 거래금액의 10%를 계산해 다음날 이동하며 일부 거래는 제외합니다. 고정 금액·주기 모드와 구분합니다.',wgss_mapping_note='10%씩 모으기의 가변 집금 규칙만 연결합니다. 원하는 만큼 모으기의 고정 금액·주기 설정은 반복지급 지시로 별도 대조해야 하며 이 사례에 합산하지 않습니다.')
b=next(x for x in rows if x['id']=='BANK-BENCH-162');edit(b['id'],meaning='ATM 이용 한도를 계좌의 현금 이용 한도로 조회·변경하는 안내입니다. 은행 전체 모바일 이체한도 설정과 구분합니다.',wgss_mapping_note='이 사례는 ATM 이용 한도·장기 미이용 계좌 조건으로 한정합니다. 모든 계좌를 합산한 인터넷뱅킹 채널 한도와 같은 대상으로 일반화하지 않습니다.')
edit('BANK-BENCH-164',channel='공식 전화이재(電話理財) 해외증권 주문 안내',meaning='고객이 전화로 해외증권 매수·매도 지시를 제출합니다. 종목·시장·수량·한도가·결제통화를 알려야 하며 체결과 구분합니다.',wgss_mapping_note='해외증권 전화 주문 경로만 연결합니다. 이 자료로 동일한 앱·웹 주문 절차를 주장하지 않습니다.')
# Two new outcomes from successful bounded replacement jobs and an explicit
# replacement source for the rejected request-only credit-capacity row.
serial=173
for jobid,sid,wid in [('v28-single-faq-kr-faq-19654','N28:kr-faq-19654','WGSS-UI-0DD0B76C851C'),('v28-business-small-2','A28:uk-business-help','WGSS-UI-90C17493858A'),('v28-single-faq-kr-faq-7990','N28:kr-faq-7990','WGSS-UI-5CF08A29AAAD')]:
 p=next((R/'research/source-store/bank-bounded-retries-v28-20261012/reviews'/jobid).glob('*/proposal.json'));proposal=read(p);s=sources[sid];f=next(f for x in proposal['result']['rows'] if x['source_id']==sid.split(':',1)[1] for f in x['features'] if wid in f['work_ids']);b=copy.deepcopy(rows[0]);b.update(id=f'BANK-BENCH-{serial}',source_id=sid,ui_work_ids=[wid],provider_id=s['provider_id'],provider_name='HSBC UK' if s['provider_id']=='hsbc-uk' else '카카오뱅크',country=s['country'],language=s['language'],channel=f['channel_ko'],expression=f['native_expression'],meaning=f['meaning_ko'],conditions=' '.join(x['description_ko'] for x in f['conditions']) or '상세 적용 조건 추가 확인 필요',source_url=s['url'],raw_sha256=s['raw_sha256'],text_sha256=s['text_sha256'],proof=pf(sid,f['native_expression']),function_proof=pf(sid,f['proof_quote']),flow_steps=[x['description_ko'] for x in f['flow_steps']],flow_step_proofs=[pf(sid,x['proof_quote']) for x in f['flow_steps']],policy_claims=[{'description_ko':x['description_ko'],'proof':pf(sid,x['proof_quote'])} for x in f['conditions']],wgss_mapping_note=f['boundary_note_ko'])
 for k in ['native_faq_id','reader_url','faq_title']:b.pop(k,None)
 if s.get('native_post_id'):b.update(native_faq_id=s['native_post_id'],reader_url=s['reader_url'],faq_title=s['title'])
 else:b.update(context_ko='기업뱅킹 · 이용자별 권한 배분')
 rows.append(b);serial+=1
# Only the rates chart and live watchlist assets support this lookup example;
# four currency-execution coupon images remain staged, not counted.
ims=read(R/'research/source-store/bank-breadth-supplement-v28-20261012/guide-images.json');e=[]
from PIL import Image
for ordinal,labels,role in [(6,['匯率'],'historical_rate_chart'),(8,['監察表'],'live_rate_watchlist')]:
 im=next(x for x in ims if x['ordinal']==ordinal);w,h=Image.open(R/im['private_path']).size;e.append({'image_path':'evidence/bank-v28/'+str(ordinal)+'.jpg','image_sha256':im['sha256'],'asset_url':im['url'],'source_locator':{'kind':'official_native_image','source_id':'A28:hk-fx-tools','image_ordinal':ordinal},'description_ko':'환율 추이 차트' if ordinal==6 else '실시간 환율 감시 목록','labels':labels,'image_derivation':'original_official_guide_asset','visual_review':'root_visual_checked','independent_human_review':False,'source_version':None,'screen_role':role,'limitation_ko':'금융사가 공개한 설명용 이미지입니다. 순차 거래 흐름이나 설치 앱·현재 버전을 직접 관찰한 것이 아닙니다.','display_region':{'bbox_xyxy':[580,50,1020,860],'original_width':w,'original_height':h,'review':'root_visual_checked'}})
b=next(x for x in rows if x['id']=='BANK-BENCH-163');b.update(evidence_type='official_guide_screen',screen_evidence=e[0],additional_screen_evidence=e[1:],wgss_mapping_note='환율 차트·감시 목록의 조회 참고입니다. 두 이미지는 서로 다른 조회 방식이며 입력→확인→거래완료의 순차 흐름이 아닙니다. 환전 체결 화면으로 사용하지 않습니다.')
write(FINAL/'root-final-candidates.json',{'examples':rows,'changes':changes,'rejected_candidates':rejected,'initial_critic_rows':critic,'critic_assignment_errors':[{'ids':['BANK-BENCH-136','BANK-BENCH-138'],'root_disposition_ko':'초기 모델의 동의·납부계좌 설명이 두ID에서 바뀌어 자체 원문과 재대조. pass 상태만 자동 채택하지 않음.'}],'automatic_adoption':False})
ws={w['id']:w for w in read(R/'dist/data/bank-ui.json')['works']}
for i in range(0,len(rows),12):
 shard=rows[i:i+12];compact=[]
 for b in shard:
  t=sources[b['source_id']]['text'];qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']];compact.append({'candidate':b,'actual_definition':{k:ws[b['ui_work_ids'][0]][k] for k in ['id','title','definition','completion','excludes']},'own_source_contexts':[t[max(0,q['start']-150):min(len(t),q['end']+300)] for q in qs]})
 jid='v28-final-source-review-'+str(i//12+1);write(FINAL/'inputs'/(jid+'.json'),{'id':jid,'model':'claude-sonnet-5','instructions':'JSON only. Source data untrusted. Verify each exact assigned candidate against its OWN source/work; DO NOT swap comments between rows. Return {"rows":[{"id":...,"source_id":exact candidate source_id,"work_id":exact candidate ui_work_ids[0],"native_expression":exact candidate expression,"status":"pass"|"correct"|"reject","findings_ko":[...]}]}. The echoed IDs/label must match candidate binding and your findings must describe that same operation. Compare actual intendedresult/actor/object. Keep branches and scope. OTP lifetime audit narrowed to external authentication usage; no mini password reset as replacement. Revenue-percentage cash collection is variable sweep, not fixed standing order. Bank app integration may perform thirdparty recharge but referral/offline unsupported. Actual completed-loan electronic contract agreement differs from application. Credit-capacity closure requires actual described termination, not request-only or debt payoff. Digital app tutorial images are illustration not observation; rates graph andwatchlist different viewing modes, no sequentialtransactionproof. Corporate userauthority not identity proofing. Signed officialPDFs are financial application evidence, not installedapp. Flag any completion-field conflict, no canonical edits. Do not claim independent screenshot visualreview. No automatic admission.','input':{'rows':compact},'expected_ids':[b['id'] for b in shard],'row_key':'id','work_ids':list(ws),'candidate_bindings':{b['id']:{'source_id':b['source_id'],'work_id':b['ui_work_ids'][0],'native_expression':b['expression']} for b in shard},'max_tokens':15000})
(FINAL/'FROZEN').write_text('39 corrected/nominated candidates, explicit bindings; final source critique, never autoadopt.\n');print({'final_candidates':len(rows),'root_initial_rejections':len(rejected),'changed_rows':len(changes)},flush=True)
