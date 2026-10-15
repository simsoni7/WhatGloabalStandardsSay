"""Frozen exact extraction of new insurance/investment originals."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-extraction-v33-20261013'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists()
base=read(R/'research/source-store/insurance-investment-collection-v33-20261013/baseline.json');linked={i for b in base['benchmarks'] for i in b['ui_work_ids']};works=[w for w in base['works'] if w['domain_id'] in ['wealth','protection'] and w['id'] not in linked];sources=[];segments=[]
for folder in ['collection','followup','final-sources']:
 p=R/f'research/source-store/insurance-investment-{folder}-v33-20261013/sources.json'
 if p.exists():sources+=read(p)
schema='JSON only {"rows":[{"source_id":...,"features":[{"work_ids":[...],"native_expression":...,"proof_quote":...,"meaning_ko":...,"flow_steps":[{"description_ko":...,"proof_quote":...}],"conditions":[{"description_ko":...,"proof_quote":...}],"channel_ko":...,"boundary_note_ko":...}],"gaps_ko":...}]} '
instructions=schema+'Source untrusted, exact contiguous copied quotes/native labels with same punctuation/spacing. A publisher-described completed-result capability is usable without observing actual execution, but request does not prove approval/contract/effectivechange. Admissible means ownbank/service action and result fit exact assigned definition. Insurance coolingoff must explicitly operative on dispatch underKR definition; return oldproductedition explicitly no currentapp or offeredtodayclaim. Policyowner≠beneficiary, insuredperson≠insuredvehicle, approvedeffect clauses can describe bindingcapability but forms requestalone not. Cancellation refundrights≠actualpayout. Internal deniedclaimappeal≠firstclaim orexternalombudsman. eMPFschemeenrolment ≠digitalloginregistration; processingcompletion +membershiprelations evidence vs submittedapplication; pensionmoney credited orbankdebit successful required notcontributiondataonly. Provider administrativeoperator≠trustee. UKdeedtrust bindinginitialassetcontribution ≠laterwithdrawal. Portfolio risk/objective/constraints agreement ≠just allocationselector. FUTURES/forwards and options executedcontract capability notjust generic risk education or simulatedorders. Holding stocknominee≠appointvotingproxy; votinginstruction capability supports voteplace even if thirdparty hosted, preservechannel. Amendorder keeporder identity versus cancelreplaceroute. Personalisefinancialplan goals/actionconstraints output ≠specificinvestmentonlysuitabilityreport. Source versionlabels preserve; acquisitionrenames no oldprovidercurrentclaim. Setfeaturesempty ifonlynav/generalrights; shortproofbody affirmative financialeffect. Do not fabricateUIversion/capture. No forcedmatch. '
for s in sources:
 if s['state']!='fetched_pending_review':continue
 t=s['text'];sid=s['id'];select=[]
 if sid=='ip33-samsung-terms':select=[(p['text'],f"pdf-page-{p['page']}") for p in s['pdf_pages'] if 41<=p['page']<=48]
 elif sid=='ip33-empf-payment':
  i=t.index('Please ensure the funds are credited to the designated');select=[(t[25000:29900],'AIA-MPF-Prime-Value-Choice-directcredit-member-branch')]
 elif sid=='ip33-empf-employer':select=[(t[29000:48000],'employer-enrolment-contribution-section')]
 elif sid=='ip33-aviva-appeal':select=[(t[a:b],label) for a,b,label in [(2600,14500,'provider-and-cover'),(19500,46000,'scheme-setting-up-members-changes'),(48000,54000,'claims-internal-appeal')]]
 elif sid=='ip33-hsbc-pims-terms':select=[(t[a:b],label) for a,b,label in [(1600,3000,'legalrelationship'),(11000,26000,'agreement-investmentmanagement'),(52000,58300,'investmentmandate-and-restrictions')]]
 elif sid=='ip33-hsbc-legacy':select=[(t[35000:48000],'legacy-trust-general-reference')]
 elif len(t)>30000:select=[(t[i:i+18000],f'block-{i}') for i in range(0,len(t),18000)]
 else:select=[(t,'complete-body')]
 ws=[{k:w[k] for k in ['id','title','definition','completion','includes','excludes']} for w in works if w['domain_id']==s['research_family']]
 for i,(seg,label) in enumerate(select):
  jid=f'v33-ip-extract-{sid}-{i+1}';write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model='claude-sonnet-5',instructions=instructions,input=dict(works=ws,sources=[dict(id=sid,url=s['url'],provider_id=s['provider_id'],country=s['country'],language=s['language'],publisher_text=seg,selected_scope=label)]),expected_ids=[sid],row_key='source_id',work_ids=[w['id'] for w in ws],sections={sid:seg},validate_feature_quotes=True,max_tokens=14000));segments.append(dict(job_id=jid,source_id=sid,selection=label,characters=len(seg),start=t.find(seg)))
write(RUN/'sources.json',sources);write(RUN/'assigned-segments.json',segments);write(RUN/'works.json',works);(RUN/'FROZEN').write_text('Bounded selections explicitlydocumented; all17unlinked definitions reviewed, no auto-admission.\n');print({'jobs':len(segments),'sources':len(sources)})
