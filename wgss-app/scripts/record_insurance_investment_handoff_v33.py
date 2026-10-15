"""Correct reviewer findings and handoff exactsourceadvisory nominations."""
import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-handoff-v33-20261013'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();cr=R/'research/source-store/insurance-investment-candidates-v33-20261013';d=read(cr/'root-candidates.json');sources={'S33:'+s['id']:s for s in read(cr/'sources.json')};critics={r['id']:r for p in cr.glob('reviews/*/*/proposal.json') for r in read(p)['result']['rows']};assert len(critics)==18
for s in read(R/'research/source-store/insurance-investment-last-sources-v33-20261013/sources.json'):sources['S33:'+s['id']]=s
def proof(b,q):
 t=sources[b['source_id']]['text'];i=t.index(q);return dict(kind='normalized_text_character_range',start=i,end=i+len(q),excerpt=q)
for b in d['examples']:
 cid=b['id'];b['critic_status']=critics[cid]['status'];b['critic_findings_ko']=critics[cid]['findings_ko'];b['root_function_admitted']=False
 if cid=='IP-V33-2':
  b['meaning']='계약자가 회사의 승낙을 얻어 보험기간·납입조건·보험가입금액 등 변경된 보장조건을 확정하는 계약상 기능입니다(2024.5 약관 판본).';b['flow_steps'][0]='계약자가 보험가입금액·적립보험료 등 보장조건 변경사항을 제시합니다.';b['flow_step_proofs'][0]=proof(b,'5. 보험가입금액, 적립보험료 등 기타 계약의 내용')
 if cid=='IP-V33-3':
  b['meaning']='계약자가 회사의 승낙을 얻어 기존 계약의 피보험자(사람 계약관계자)를 변경하고 통지·증권 기재로 변경 내용을 확정하는 계약상 기능입니다(2024.5 판본).';b['flow_steps']=b['flow_steps'][:2];b['flow_step_proofs']=b['flow_step_proofs'][:2];b['wgss_mapping_note']+=' 이 조문은 최초 피보험자 신규등록 절차를 설명하지 않습니다.'
 if cid=='IP-V33-4':b['policy_claims'][1]['description_ko']='해지 시 회사는 제36조 제1항에 따른 해약환급금을 계약자에게 지급한다고 설명합니다.'
 if cid=='IP-V33-5':b['meaning']=b['meaning'].replace('2024.4','2024.5');b['expression_type']='공식 약관의 기능 조항 표기'
 if cid=='IP-V33-6':
  b['policy_document_version']='AIA OPPOSF29.0926';b['review_note']='공식 현재 양식 페이지에서 연결한 2026.09 양식 판본의 계약상 기능입니다. 개인 실행 및 현재 앱 화면은 확인하지 않았습니다.'
  for key in ['meaning','conditions']:b[key]=b[key].replace('批註','배서(Endorsement)')
  b['flow_steps']=[x.replace('批註','배서(Endorsement)') for x in b['flow_steps']]
 if cid=='IP-V33-15':
  q='Investment restrictions are only permitted in exceptional cases. In these situations we will manage your Portfolio in line with your Model, subject to such investment restrictions or other instructions agreed with you.';b['function_proof']=proof(b,q);b['meaning']='고객과 합의한 투자제한·지시를 반영하여 모델에 따라 포트폴리오를 운용하기로 하는 계약상 운용지침 합의입니다.';b['flow_steps']=b['flow_steps'][1:];b['flow_step_proofs']=b['flow_step_proofs'][1:]
 if cid in ['IP-V33-16','IP-V33-17']:
  b['policy_claims']=[];b['conditions']='원문에서 계약 유형별 거래시간·증거금 조건을 구분합니다. 다른 시장·계약 유형에 공통 조건으로 적용하지 않도록 해당 분기를 확인해야 합니다.';b['review_note']='공개 서비스 안내에 기술된 체결 가능 기능입니다. 미국 해외선물 시간표를 홍콩 옵션 등 전체 계약의 공통 정책으로 사용하지 않습니다.'
  if cid=='IP-V33-16':b['flow_steps'][0]='Power Futures를 통해 해외선물을 전자거래합니다.'
  else:b['flow_steps']=['인터넷에 연결한 컴퓨터를 이용하여 옵션 거래를 할 수 있다고 안내합니다.'];b['flow_step_proofs']=[b['function_proof']];b['channel']='인터넷 연결 컴퓨터 · 원문에 기술된 옵션 거래 서비스'
 # Align rewrittendescriptioncondition to retained explicitclaim set
 if b['policy_claims']:b['conditions']=' '.join(x['description_ko'] for x in b['policy_claims'])
# Exactsourceproviderplatformmarketproof (not representative/leaderclaims)
providers=[]
for pid,sid,q,kind in [
 ('aviva-uk','S33:ip33-aviva-appeal','We’re Aviva Life & Pensions UK Limited (Aviva for short). We specialise in insurance in the UK','life_insurer'),
 ('ii-uk','S33:ip33-ii-voting','Here you will receive notifications for all the UK-listed companies you own shares in.','investment_platform'),
 ('htisec-hk','S33:ip33-hti-futures','Open Account (Hong Kong)','brokerage_brand'),
 ('aia-hk','S33:ip33-aia-forms','HK: AIA Wealth Select Centre','life_insurer'),
 ('chesnara-life-uk','S33:ip33-trust-pdf-1','United Kingdom. Registered in England number 88695. Issued by Chesnara Life (UK) Ltd','life_insurer')]:
 s=sources[sid]
 if q not in s['text']:
  # Sourceowncurrentforms language variant; neverinventmarketproof
  if pid=='aia-hk':q='Hong Kong'
  assert q in s['text'],(pid,q)
 i=s['text'].index(q);providers.append(dict(provider_id=pid,provider_name=next(b['provider_name'] for b in d['examples'] if b['provider_id']==pid),country=s['country'],provider_kind=kind,source_id=sid,source_url=s['url'],raw_sha256=s['raw_sha256'],text_sha256=s['text_sha256'],market_proof=dict(kind='normalized_text_character_range',start=i,end=i+len(q),excerpt=q),automatic_adoption=False,representative_rank_verified=False,notes_ko='공식 국가별 서비스·문서 배포 사실만 제안합니다. 은행·보험자·플랫폼/브랜드 역할은 구분해야 합니다.'))
write(RUN/'root-candidates.json',d);write(RUN/'critic-results.json',list(critics.values()));write(RUN/'new-provider-targets.json',providers);write(RUN/'sources.json',list(sources.values()));batches=d['source_batches']+[dict(prefix='S33:',manifest='research/source-store/insurance-investment-last-sources-v33-20261013/sources.json')];write(RUN/'source_batches.json',batches)
write(RUN/'semantic-review-tickets.json',[dict(id='coolingoff-country-effect-overfit-v33',work_id='WGSS-UI-C32657DB79D5',field='definition/completion',existing_value='일반금융소비자가 보장성 상품 청약철회 기간 내에 서면등으로 철회 의사표시를 발송하여 그 발송 시점에 청약철회의 효력이 발생하는 결과.',issue_ko='고객의 청약철회 결과에 한국의 발송 시점 효력 정책이 결합되어 UK 공식 냉각기간 취소 사례를 같은 금융업무에 연결하지 못합니다.',source_id='S33:ip33-aviva-life-terms',source_url=sources['S33:ip33-aviva-life-terms']['url'],proposed_fix_ko='업무 정의를 일반금융소비자의 보장성 상품 청약철회 의사표시로 인한 계약 취소 효력 성립으로 검토하고, 발송·수신·기한·반환 등 시장별 효력 요건은 출처를 갖춘 적용조건 필드로 분리합니다. 현행 ID/모수 변경은 별도 정의 심의가 필요합니다.',automatic_adoption=False)])
# Correctionverification jobs; root stillowns finaladmission
ws={w['id']:w for w in read(R/'research/source-store/insurance-investment-extraction-v33-20261013/works.json')};positive=[b for b in d['examples'] if b['critic_status']!='reject']
for i in range(0,len(positive),4):
 shard=positive[i:i+4];compact=[]
 for b in shard:
  t=sources[b['source_id']]['text'];ps=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']];compact.append(dict(candidate=b,definition=ws[b['ui_work_ids'][0]],previous_critic=critics[b['id']],own_source_contexts=[t[max(0,p['start']-200):p['end']+350] for p in ps]))
 jid='v33-ip-corrected-verification-'+str(i//4+1);write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model='claude-sonnet-5',instructions='JSON only {"rows":[{"id":...,"source_id":...,"work_id":...,"native_expression":...,"status":"pass"|"correct"|"reject","findings_ko":[...],"correction_ko":...}]}. Exactbindings. Verify corrections resolved everyfinancialfalseclaim. Source-describedcompleted result capability allowed without actualpersonaltransaction. Legaledition andformbindingeffect onlynotUIversion. Requestonlynotapproval, explicitapproved+endorsement descriptionusable. No scopechanges. Samsung2024.5 historicaledition explicitlylimited, notcurrentlaw/marketedproduct. Pensionpayment credited/resultunits allocated notdatainstruction. Trustinitialexistingpolicyassignment actualdeedcapability noexecutedclientclaim. USoverseasfutures conditionsremoved notalloptions policy. Portfoliomandateagreement notsuitabilityalone; nominee-vote notappointproxy. Do not add/new claims.',input=dict(rows=compact),expected_ids=[b['id'] for b in shard],row_key='id',work_ids=list(ws),candidate_bindings={b['id']:dict(source_id=b['source_id'],work_id=b['ui_work_ids'][0],native_expression=b['expression']) for b in shard},max_tokens=14000))
(RUN/'FROZEN').write_text('Corrected financialnominations andreviewbindings, no automaticrootadmission.\n');print({'positive_candidates':len(positive),'rejected':len(d['examples'])-len(positive),'corrected_review_jobs':len(list((RUN/'inputs').glob('*.json')))})
