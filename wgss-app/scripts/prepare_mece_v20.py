"""Freeze the remaining fourteen tickets and verified primary extracts once."""
import hashlib,json,re,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research/source-store/mece-closure-v20-20261011'
def read(p):return json.loads(p.read_text())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'catalogue-before.json').exists(),'Frozen inputs already exist; use a new phase'
store=RUN/'sources'
# An HTTP 200 challenge page is not the regulation. Preserve it as rejected.
bad=store/'ECFR_FUND_NAV.json'
if bad.exists():
    meta=read(bad);meta.update(functional_evidence_rejected=True,rejection_reason='Downloaded text lacks the requested operative regulation; use separately captured official web extract')
    write(bad,meta)
selected={
 'ECFR_FUND_NAV_SELECTED':('https://www.ecfr.gov/current/title-17/chapter-II/part-270/section-270.2a-4','us_electronic_regulation_selected_web_text_not_global_rule',103,118),
 'SEC_SYNDICATED_ASSIGNMENT_EFFECTIVE':('https://www.sec.gov/Archives/edgar/data/849399/000084939916000025/a7116exhibit403.htm','historical_sec_filed_contract_selected_web_text',1640,1692),
 'SEC_FUND_DECLARATION_SELECTED':('https://www.sec.gov/Archives/edgar/data/763852/000119312526277772/d139095dex99a2.htm','historical_sec_filed_fund_declaration_selected_web_text',177,450),
}
for sid,(url,kind,lo,hi) in selected.items():
    raw=(store/(sid+'.web.txt')).read_bytes();text='\n'.join(line for line in raw.decode().splitlines() if (m:=re.match(r'L(\d+):',line)) and lo<=int(m[1])<=hi)
    assert len(text)>500
    (store/(sid+'.txt')).write_text(text+'\n')
    write(store/(sid+'.json'),dict(id=sid,url=url,source_kind=kind,raw_path=sid+'.web.txt',text_path=sid+'.txt',sha256=hashlib.sha256(raw).hexdigest(),text_sha256=hashlib.sha256((text+'\n').encode()).hexdigest(),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),capture_scope='selected_official_web_tool_text_only_not_complete_HTML',ui_benchmark_admitted=False))
catalogue=read(ROOT/'dist/data/operations.json');progress=read(ROOT/'data/mece-closure-review.json')
assert len(catalogue['works'])==382 and len(progress['remaining_work'])==14
write(RUN/'catalogue-before.json',catalogue);write(RUN/'checkpoint-before.json',progress)
old={t['id']:t for t in read(ROOT/'research/source-store/mece-closure-20261011/tickets.json')}
keys=['id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes']
compact=[{k:w[k] for k in keys} for w in catalogue['works']]
primary={}
for p in store.glob('*.json'):
    m=read(p)
    if m.get('functional_evidence_rejected'):continue
    text=(store/m['text_path']).read_text()
    if m['id']=='VISA_CORE_RULES':
        chunks=[]
        for term in ['represent a binding contract','Voluntary termination of membership']:
            at=text.find(term)
            if at>=0:chunks.append(text[max(0,at-450):at+1500])
        text='\n'.join(chunks)
    elif m['id']=='SWISS_RE_UNDERWRITING':
        match=re.search(r'Underwriting.{0,15}is the process',text,re.S);at=match.start() if match else -1
        assert at>=0,'Underwriting operative section not found'
        text=text[max(0,at-400):at+11000]
    elif m['id']=='FINRA_ANALYSIS_TOOLS':
        at=text.find('(a) General Considerations');text=text[at:at+8000] if at>=0 else text[3000:10000]
    elif m['id']=='ISDA_AMICUS_MASTER_AMENDMENT':
        at=text.find('No amendment');text=text[max(0,at-800):at+3500] if at>=0 else ''
    if text:primary['PRIMARY:'+m['id']]={'section_id':'PRIMARY:'+m['id'],'text':text,'source_metadata':m}
assign={
 'INPUT-lending-trade-invoice financing advance-draw-51':['HSBC_INVOICE_DISCOUNTING'],
 'CANDIDATE-ServiceDomain:37104#0':['SEC_FUND_DECLARATION_SELECTED'],
 'CANDIDATE-ServiceDomain:38742#0':['SEC_SYNDICATED_ASSIGNMENT_EFFECTIVE'],
 'CANDIDATE-ServiceDomain:44473#0':['SEC_FUND_DECLARATION_SELECTED'],
 'CANDIDATE-ServiceDomain:48953#0':['SEC_FUND_DECLARATION_SELECTED','ECFR_FUND_NAV_SELECTED'],
 'CANDIDATE-BusinessCapability:64039#0':['SEC_FUND_DECLARATION_SELECTED'],
 'CANDIDATE-BusinessCapability:64436#0':['FINRA_ANALYSIS_TOOLS'],
 'SOURCE-RESULT-REINSURANCE-RISK-DECISION':['SWISS_RE_UNDERWRITING'],
 'SOURCE-RESULT-MASTER-AGREEMENT-LIFECYCLE':['ISDA_AMICUS_MASTER_AMENDMENT'],
 'SOURCE-RESULT-NETWORK-PARTICIPATION-LIFECYCLE':['VISA_CORE_RULES'],
}
tickets=[]
for row in progress['remaining_work']:
    sections=old[row['id']]['sections']+[primary['PRIMARY:'+sid] for sid in assign.get(row['id'],[]) if 'PRIMARY:'+sid in primary]
    tickets.append({**row,'sections':sections})
write(RUN/'tickets.json',tickets)
instructions='''Return JSON only {"rows":[{"id":exact assigned id,"decision":"register_independent_result|covered_existing_result|boundary_edit_existing|split_to_atomic_followups|proof_gap|excluded_explicit_scope","work_ids":existing IDs only,"evidence_section_ids":supplied IDs only,"reason":Korean,"atomic_results":[{"title":Korean,"actor_role":snake_case,"object_key":snake_case,"outcome_key":snake_case,"discriminator":string or null,"definition":Korean,"nearest_work_ids":existing IDs only,"evidence_section_ids":supplied IDs only,"recommendation":"add|covered|gap|excluded","reason":Korean}],"boundary_edits":[{"id":existing ID,"definition":Korean,"includes":[Korean],"excludes":[Korean],"reason":Korean}],"remaining_results":[Korean],"next_action":Korean}]}. Review all current 382 definitions and all own clauses. Inputs include new operative primary extracts, with scope limitations; compare function and legal completion conditions rather than names. No product, bank, viewpoint, method/date/quantity clones. A source parent is not a work. A request is not payment. A fund unit price aggregate with fee/liability/unit denominator might differ from instrument valuation, but justify its independent object/use. A fund trust's legal formation may be covered by existing trust creation; do not clone it merely for fund name; segregated collective-investment series establishment may require an independent rights object. Fund charter policy differs from legal entity formation and investor mandate. Registered ownership change is not automatically nominee title holding or mere securities account position movement. Loan assignment transferring lender obligations differs from selling a participation leaving originating lender as lender of record; never conflate them. Explain relevant differences and retain any uncovered atomic results. A hypothetical future portfolio outcome distribution is not merely a future date on a valuation; compare its actual purpose/assumptions. Reinsurance contract formation is shared; risk acceptance determination can be a distinct result but compare primary underwriting directly and do not create counterpart view clones. Dividend issuer perspective alone does not clone entitlement calculation or actual distribution; declaration is a separate hypothesis requiring own clause. Generic account activity control cannot mean every unproven approval. Rules self-modification is not bilateral agreement amendment. Voluntary membership exit is not involuntary suspension or termination; absence of public licensing clauses must remain an explicit source gap. Historical sources are conditional functional evidence, not current universally applicable law, executed agreement, independent human approval or UI capture. Even a rejected hypothesis does not close the financial source coverage gap. Cite section IDs only, no fabricated quotes. Return exactly all assigned IDs and no global approval.'''
scope=read(ROOT/'research/source-store/operation-v12/basis/scope.json')
for n,start in enumerate(range(0,len(tickets),4),1):
    batch=tickets[start:start+4];sections={s['section_id']:s['text'] for t in batch for s in t['sections']}
    job=dict(id=f'closure-tickets-v20-{n:02}',model='claude-opus-5',max_tokens=24000,instructions=instructions,input={'scope':scope,'catalogue':compact,'tickets':batch},expected_ids=[t['id'] for t in batch],row_key='id',work_ids=[w['id'] for w in compact],sections=sections,grounded_section_ids=True)
    write(RUN/'inputs'/(job['id']+'.json'),job)
print(json.dumps({'frozen_definitions':len(compact),'tickets':len(tickets),'primary_sections':list(primary),'jobs':4}))
