"""Exact candidateproof ledger and independently bound Opus critiques."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-candidates-v33-20261013'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();sources={};batches=[]
for n in ['collection','followup','final-sources','contracts','browser','trust-pdfs']:
 p=R/f'research/source-store/insurance-investment-{n}-v33-20261013/sources.json'
 if p.exists():
  batches.append(dict(prefix='S33:',manifest=str(p.relative_to(R))))
  for s in read(p):sources['S33:'+s['id']]=s
works={w['id']:w for w in read(R/'research/source-store/insurance-investment-extraction-v33-20261013/works.json')};rows=[];seen=set();names={'empf-hk':'eMPF Platform','samsung-fire':'삼성화재','aviva-uk':'Aviva','ii-uk':'interactive investor','hl-uk':'Hargreaves Lansdown','hsbc-uk':'HSBC UK','htisec-hk':'Haitong International','aia-hk':'AIA Hong Kong','chesnara-life-uk':'Chesnara Life'}
def proof(sid,q):
 t=sources[sid]['text'];i=t.index(q);return dict(kind='normalized_text_character_range',start=i,end=i+len(q),excerpt=q)
allowed={'ip33-aviva-appeal','ip33-aviva-life-terms','ip33-empf-pledge','ip33-empf-payment','ip33-hsbc-pims-terms','ip33-hti-futures','ip33-ii-voting','ip33-trust-pdf-1','ip33-samsung-terms','ip33-aia-change-1','ip33-contract-3','ip33-hk-order','ip33-hl-report'}
for n in ['exact-retries','supplement-extraction','extraction']:
 for p in sorted((R/f'research/source-store/insurance-investment-{n}-v33-20261013/reviews').glob('*/*/proposal.json')):
  j=read(p)
  for row in j['result']['rows']:
   if row['source_id'] not in allowed:continue
   # Samsungperpage failures replaced by wholeclause exactjobs, notmix duplicate evidence
   if row['source_id']=='ip33-samsung-terms' and n!='exact-retries':continue
   for f in row.get('features',[]):
    sid='S33:'+row['source_id'];s=sources[sid]
    for wid in f['work_ids']:
     if wid not in works or (sid,wid) in seen:continue
     if row['source_id']=='ip33-contract-3' and wid=='WGSS-UI-7CC4E2DB94BF':continue # model confusedcontingentowner with insured
     seen.add((sid,wid));cid='IP-V33-'+str(len(rows)+1)
     b=dict(id=cid,source_id=sid,ui_work_ids=[wid],provider_id=s['provider_id'],provider_name=names[s['provider_id']],country=s['country'],language=s['language'],channel=f['channel_ko'],expression=f['native_expression'],expression_type='공식 자료의 기능·UI 표기',meaning=f['meaning_ko'],conditions=' '.join(x['description_ko'] for x in f['conditions']) or '원문에서 구체적인 적용 조건을 확인하지 못했습니다.',source_url=s['url'],raw_sha256=s['raw_sha256'],text_sha256=s['text_sha256'],proof=proof(sid,f['native_expression']),function_proof=proof(sid,f['proof_quote']),flow_steps=[x['description_ko'] for x in f['flow_steps']],flow_step_proofs=[proof(sid,x['proof_quote']) for x in f['flow_steps']],policy_claims=[dict(description_ko=x['description_ko'],proof=proof(sid,x['proof_quote'])) for x in f['conditions']],collected_at='2026-10-13',root_function_admitted=False,policy_admission='only_explicit_qualifications_no_global_policy',policy_status='source_specific_qualifications_only',evidence_type='official_public_function_document',observed_app_screen=False,verified_ui_version=None,app_os=None,ready_for_use_review='not_assessed',function_observation='publisher_described_function',current_ui_verified=False,wgss_mapping_note=f['boundary_note_ko'],source_model_job=j['job_id'])
     if s['provider_id']=='empf-hk':b.update(provider_kind='pension_administration_platform',financial_provider_name='해당 MPF 제도 수탁자 · 제도별로 상이',source_publisher_name='eMPF Platform Company Limited · 운영자')
     if row['source_id']=='ip33-empf-payment':b.update(review_note='AIA MPF - Prime Value Choice의 Direct Credit 납입 분기입니다. eMPF는 관리 플랫폼이며 수탁자는 AIA Company (Trustee) Limited입니다.',financial_provider_name='AIA Company (Trustee) Limited · AIA MPF - Prime Value Choice')
     if row['source_id']=='ip33-samsung-terms':b.update(policy_document_version='무배당 삼성화재 펫보험 위풍댕댕 2024.5',review_note='공식 약관의 2024.5 판본에 한정한 계약상 기능 사례입니다. 현재 판매 판본·현재 앱 화면은 확인하지 않았습니다.')
     if s['provider_id']=='aviva-uk':b.update(financial_provider_name='Aviva Life & Pensions UK Limited',provider_kind='life_insurer',source_publisher_name='Aviva')
     if s['provider_id']=='chesnara-life-uk':b.update(financial_provider_name='Chesnara Life (UK) Limited',provider_kind='life_insurer',source_publisher_name='Chesnara Life · formerly HSBC Life (UK) Limited',review_note='2026년 현재 Chesnara Life가 배포한 신탁 양식입니다. 문서의 실제 서명·고객 계약은 관찰하지 않았습니다.')
     if row['source_id']=='ip33-hk-order':b.update(review_note='공개 도움말의 현재 UI 적용·판본은 확인하지 못했습니다. 현재 제공자의 서비스 문서와 별도 비교 검토가 필요합니다.')
     rows.append(b)
write(RUN/'root-candidates.json',dict(examples=rows,automatic_adoption=False,source_batches=batches));write(RUN/'sources.json',list(sources.values()));write(RUN/'source_batches.json',batches)
for i in range(0,len(rows),3):
 shard=rows[i:i+3];compact=[]
 for b in shard:
  t=sources[b['source_id']]['text'];qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']];compact.append(dict(candidate=b,actual_definition={k:works[b['ui_work_ids'][0]][k] for k in ['id','title','definition','completion','includes','excludes']},own_source_contexts=[t[max(0,q['start']-400):q['end']+600] for q in qs]))
 jid='v33-ip-critic-'+str(i//3+1);write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model='claude-opus-5',instructions='JSON only {"rows":[{"id":...,"source_id":...,"work_id":...,"native_expression":...,"status":"pass"|"correct"|"reject","findings_ko":[...],"correction_ko":...}]}. Preserveexactcandidatebindings. Critique actor/object/intendedresult and everyclaim/flow/policy for SAMEproductbranch. A source-described financialcapability may be admitted without actualtransaction observation; not reject merelynoexecution. But application/approvalconditions alone nofundedcontract effectunlesssource actuallydescribes acceptance andresult, legalabilityclause qualifiesascontractualdescribedresult notactualUI. eMPF servicepledge completedMPFmembership +result record distinct submittedregistration; ifpledgeline onlytarget notresultinterface qualifydescribed capability, noactualindividualenrolment. Contribution directcredit fundscredited qualifies, datainstruction not. AvivaUKcoolingoff currentcanonicaldefinition requiresdispatch-timeeffect; reject ifonlyUK14daycancellationright, propose semanticfieldreview butdontchange scope. Samsung2024.5policyversion evidence accurate; currentlaw/productUI notverified, historicaleffectjustversion notfalsecurrent. Companyacceptance+endorsedchangedcontract distinguish submittedform; benefit/insured/owner different. OPPOSF88 newborninsured application mayonlychange afteracceptanceandmustnotassertappaccepted. Trustasset initiallyexistingpolicyassignment+immediatecreation bindingdescribedcapability, futurepolicyissuance-only not. Futures/optiontrade service trueexecution notsimulator; US-specifictimehours notgenericHKallcontracts, quotationanalytics notsubmitorder. Orderamendment sameorder vs cancellationreplacement. Portfolio agreement contractconditions ratherthan onlysuitability/genericapplication. UKii votingnotproxyappointment; HLreport recommendationsonly notbroadercash/actionplan. NeverinfercurrentUIversion/screens orlegaladvice fromfooterdate. If correction needed stateexactrequired amendment, not silentlyaccept falseclaims. Eachwork mayadmitownsource contractualfunction reference with transparenteditioncondition.',input=dict(rows=compact),expected_ids=[b['id'] for b in shard],row_key='id',work_ids=list(works),candidate_bindings={b['id']:dict(source_id=b['source_id'],work_id=b['ui_work_ids'][0],native_expression=b['expression']) for b in shard},max_tokens=14000))
(RUN/'FROZEN').write_text('Candidatebindings exactandfinancialreviewadvisory. Noauto-admission.\n');print({'candidates':len(rows),'critic_jobs':len(list((RUN/'inputs').glob('*.json')))})
