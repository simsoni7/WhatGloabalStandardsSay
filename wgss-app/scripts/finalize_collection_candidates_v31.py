"""Root corrections plus bounded final checks; no data admission in this stage."""
import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/collection-final-v31-20261012'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();orig=read(R/'research/source-store/savings-candidates-v31-20261012/root-candidates.json');rows=copy.deepcopy(orig['examples']);critic=[c for p in (R/'research/source-store/savings-candidates-v31-20261012').glob('reviews/*/*/proposal.json') for c in read(p)['result']['rows']];assert len(critic)==19
sources={'S31:'+s['id']:s for name in ['savings-collection-v31-20261012','empf-collection-v31-20261012'] for s in read(R/'research/source-store'/name/'sources.json')};ws={w['id']:w for w in read(R/'dist/data/bank-ui.json')['works']}
def proof(sid,q):
 t=sources[sid]['text'];i=t.index(q);return dict(kind='normalized_text_character_range',start=i,end=i+len(q),excerpt=q)
corrected=[]
for b in rows:
 c=next(c for c in critic if c['id']==b['id']);assert c['status'] in ['pass','correct'],c
 if c['status']=='correct':corrected.append(b['id'])
 if b['id']=='BANK-BENCH-231':
  b['channel']='HL 공식 지정가·손절 주문 서비스 안내 · 세부 실행 채널은 별도 확인';b['meaning']='투자자가 지정한 매수 가격에 도달하면 매수 지시가 발동하도록 주문을 제출합니다. 체결은 보장되지 않습니다.';qs=[('매수하려는 금액을 충당하는 자금이 계정에 있어야 합니다.','In the case of purchases (i.e. buy limit orders only), you hold sufficient monies in your Hargreaves Lansdown account to cover the intended purchase.'),('지정가·손절 주문은 정규 시장 시간에만 집행할 수 있다고 안내합니다.','Limit orders and stop loss orders can be executed only during normal market hours and only if:')];b['policy_claims']=[dict(description_ko=d,proof=proof(b['source_id'],q)) for d,q in qs];b['conditions']=' '.join(d for d,q in qs)
 if b['id']=='BANK-BENCH-232':
  b['channel']='HL 지정가·손절 주문 서비스 안내 · 세부 실행 채널은 별도 확인';b['flow_steps']=['미집행 상태이며 체결 진행 중이 아닌 주문에 대해 취소 지시를 합니다.','고객이 취소 지시의 수락 여부를 확인해야 합니다.'];qs=['You may cancel a limit order or stop loss order providing that it has not been executed or is not in the process of being executed.','It is your responsibility to check that your instruction to cancel has been accepted.'];b['flow_step_proofs']=[proof(b['source_id'],q) for q in qs];b['wgss_mapping_note']+=' 기업행위·거래정지 시 기관 재량 취소와 만기 경과 삭제는 고객 취소 요청에서 제외합니다.'
 if b['id']=='BANK-BENCH-234':
  b['meaning']='예치 신청 시 만기 처리지시를 사전 설정합니다. HSBC HK App은 원리금·원금만, Online Banking은 추가로 증액 후 재예치·감액 후 재예치를 선택할 수 있다고 안내합니다. 실제 갱신 실행과 구분합니다.';b['flow_steps']=['선택한 자동갱신 지시가 추후 통지 전까지 반복 적용되도록 설정합니다.'];b['flow_step_proofs']=[proof(b['source_id'],'Select one of the following maturity instructions to automatically renew your deposit recurrently until further notice:')];qs=[('지시 변경은 만기일 최소 1영업일 전 HSBC HK App에서 해야 한다고 안내합니다.',"If you'd like to update a maturity instruction for your time deposit, please do it at least one business day before the maturity date through the HSBC HK App."),('자동갱신 시 갱신일의 당시 표준금리를 적용한다고 안내합니다.','If an auto-renewal instruction has been set up for the deposit, please note that the interest rate will be the prevailing standard interest rate on the date of renewal.')];b['policy_claims']=[dict(description_ko=d,proof=proof(b['source_id'],q)) for d,q in qs];b['conditions']=' '.join(d for d,q in qs)
 if b['id']=='BANK-BENCH-237':b['expression_type']='공식 자료의 절차 안내 제목';b['meaning']='HSBC Online Banking의 신규 정기예금 예치 절차를 안내합니다. 다음 항목은 안내서 서술 순서이며 현재 로그인 화면을 직접 관찰한 기록은 아닙니다.'
 if b['id']=='BANK-BENCH-241':
  qs=[('출금 후 정기예금 잔액이 100만원 이상이어야 합니다.','출금 후 예금잔액 100만원 이상'),('계약기간 중 최대 2회이며 자동연장된 계약기간마다 최대 2회라고 안내합니다.','계약기간 중 최대 2회 (만기 자동연장 시 연장된 계약기간 마다 최대 2회)')];b['policy_claims']=[dict(description_ko=d,proof=proof(b['source_id'],q)) for d,q in qs];b['conditions']=' '.join(d for d,q in qs)
 if b.get('review_note'):b['review_note']=b['review_note'].replace('官方 가이드','공식 안내서')
zh=copy.deepcopy(read(R/'research/source-store/empf-candidates-v31-20261012/candidates.json')['examples']);assets={a['id']:a for a in read(R/'research/source-store/empf-collection-v31-20261012/assets.json')}
for i,b in enumerate(zh):
 b['id']='BANK-BENCH-'+str(246+i)
 if b['ui_work_ids']==['WGSS-UI-58A48889FF96']:
  b['flow_steps'][0]='현 계정 잔액의 투자 분기를 선택합니다.' if i%2==0 else '향후 부담금의 투자 분기를 선택합니다.'
  b['flow_steps'][3]='자료를 확인해 제출을 선택합니다.'
  b['policy_claims']=[dict(x,description_ko=x['description_ko'].replace('오후 4시 이후','오후 4시 또는 그 이후')) for x in b['policy_claims']];b['conditions']=' '.join(x['description_ko'] for x in b['policy_claims'])
 for e in [b['screen_evidence']]+b.get('additional_screen_evidence',[]):
  e['visual_review']='root_visual_checked';e['image_derivation']='original_official_pdf_page_render';a=assets[e['source_asset_id']]
  # Full original image is retained. Crop/focus only in CSS using reviewed coordinates.
  name=e['source_asset_id'];regions={'empf-zh-invest-app-page-6':[490,238,665,620],'empf-zh-invest-app-page-11':[290,84,473,734],'empf-zh-invest-web-page-6':[78,235,550,1195],'empf-zh-invest-web-page-13':[87,107,700,1050],'empf-zh-withdrawal-web-page-9':[90,270,478,850]}
  if name in regions:e['display_region']=dict(bbox_xyxy=regions[name],original_width=a['width'],original_height=a['height'],review='root_visual_checked')
  e.pop('private_image_path',None)
rows+=zh;write(RUN/'root-final-candidates.json',dict(examples=rows,initial_savings_critic=critic,corrected_ids=corrected,root_zh_corrections_ko='투자 첫 단계는 정확 인용에 맞춰 현 잔액/향후 부담금으로 한정. cutoff는16:00포함. 이미지 직접 확인, 전체 원본 유지.',automatic_adoption=False))
# Opus for first independent critique of native examples; Sonnet for corrected savings.
for group,model,chosen in [('native','claude-opus-5',zh),('corrected','claude-sonnet-5',[b for b in rows if b['id'] in corrected])]:
 for i in range(0,len(chosen),3):
  shard=chosen[i:i+3];compact=[]
  for b in shard:
   w=ws[b['ui_work_ids'][0]];t=sources[b['source_id']]['text'];qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']];assert all(t[q['start']:q['end']]==q['excerpt'] for q in qs);compact.append(dict(candidate=b,actual_definition={k:w[k] for k in ['id','title','definition','completion','includes','excludes']},own_source_contexts=[t[max(0,q['start']-180):q['end']+240] for q in qs]))
  jid=f'v31-final-{group}-{i//3+1}';write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model=model,instructions='JSON only {"rows":[{"id":...,"source_id":...,"work_id":...,"native_expression":...,"status":"pass"|"correct"|"reject","findings_ko":[...],"correction_ko":...}]}. Preserve bindings. Source-described qualified financial capabilities allowed, not observed execution/currentapp/approval. Corrected savings must keep channel/product branch exact; HK app2renewaloptionsvsweb4distinct; cancellationcustomerbeforeexecutionnotbrokerexpiry. Partialwithdrawal100만원 term vs10만원instalment notmix. eMPF platformoperator≠trustee/issuer. 現有累算權益 = existing MPF assets NOT wages;futurecontributionsonlyleavesexistingassetsunchanged. Allocation100%/integers only relevantbranch. 16:00orafter/nonworkday recordednextday. Quote steps must be samebranch; short genericUIlabel may evidence choice only, no invented menu hierarchy. Permanentdeparture earlyclaim distinct ordinary65 age, requestsubmission notpayout. MPF applicationnotconfirmedmembership. Root has directly viewed guide images, model cannot approve pixels independently. PDFs languagequerydirectlycheckedactualChinese, no assumption fromURL. Preserve scope216, no automaticadmission/human approval/globalMECE.',input=dict(rows=compact),expected_ids=[b['id'] for b in shard],row_key='id',work_ids=list(ws),candidate_bindings={b['id']:dict(source_id=b['source_id'],work_id=b['ui_work_ids'][0],native_expression=b['expression']) for b in shard},max_tokens=12000))
(RUN/'FROZEN').write_text('24 nominated references.5 savings corrections and5 native rows undergo4 final jobs.\n');print({'nominees':len(rows),'corrections':corrected,'final_jobs':4})
