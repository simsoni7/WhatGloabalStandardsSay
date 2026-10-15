"""New bounded reviews after detecting actual source/proposal contradictions."""
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
STORE=ROOT/'research/source-store/mece-closure-20261005/sources'
sections=read(RUN/'boundary-sections.json')
def add(sid,term,width):
 meta=read(STORE/(sid+'.json'));t=(STORE/meta['text_path']).read_text();at=t.find(term);assert at>=0,(sid,term)
 k=sid+':'+str(at);sections[k]=dict(section_id=k,text=t[at:at+width],name=sid,source_url=meta['url'],
  source_locator=dict(char_start=at,char_end=min(len(t),at+width)),source_snapshot_id='WGSS-primary-process-20261006',source_file_sha256=meta['sha256'])
add('ICC_GUARANTEE_AMENDMENT','F. Amendments',2100)
add('NEST_ENROLMENT_PROCESS','You have to enrol workers',1100)
add('NEST_ENROLMENT_PROCESS','A message will then pop up',500)
add('NEST_ENROLMENT_TYPES','What are the different enrolment types',2500)
add('HSBC_CASH_CONCENTRATION','Cash Concentration, also referred',1800)
write(RUN/'targeted-sections.json',sections)
data=read(RUN/'catalogue-input.json');by={w['id']:w for w in data['works']}
groups={
 'undertaking-amendment':['WGSS-A876ACA7DC86','WGSS-F1BBF631D3AB'],
 'process-proof':['WGSS-BB9E69AF7B7D','WGSS-A3D3B2A84738','WGSS-B947CF3FC565'],
}
for name,ids in groups.items():
 refids={r['id'] for i in ids+['WGSS-F92805EAE41E'] for r in by[i]['refs']}
 selected={k:v for k,v in sections.items() if k in refids or (k.startswith('BIAN:') and any(k.startswith('BIAN:'+sid.split(':')[-1]+':') for sid in refids)) or k.startswith(('ICC_UCP_AMENDMENT:','ICC_GUARANTEE_AMENDMENT:','NEST_ENROLMENT_PROCESS:','NEST_ENROLMENT_TYPES:','CHASE_MORTGAGE_SATISFACTION:','HSBC_CASH_CONCENTRATION:'))}
 job=dict(id='targeted-v18-'+name+'-bounded',model='claude-opus-5',grounded_section_ids=True,max_tokens=9000,
 instructions='''Source-grounded WGSS review, original short clauses supplied. Root found a factual mistake in earlier Opus review: BOTH guarantee amendment (ISDGP 79) and documentary-credit amendment (UCP10) bind issuer when issued and require beneficiary acceptance for changed terms. Do NOT invent a distinction from that shared condition. Explain whether there is any actual different direct financial obligation/result that makes guarantee/LC amendment nonoverlapping, otherwise propose ONE generic issued-undertaking amendment with rule-specific applicability branches. Automatic variation does not create a second case merely for timing/automation. Never count generic parent plus specialised child. NEST source proves employer/authorised administrator registers a worker and confirmation creates membership, not that worker unilaterally registers. Correct responsibilities; qualification is a prerequisite distinct from maintenance of product eligibility list. One shared membership result need not be cloned by viewpoint. Original bank-HR source is context not direct pension-procedure proof. Chase proves preparing/sending mortgage satisfaction BEFORE recorder releases lien; correct the result/title to issue the source-proven document for release instead of claiming a certificate of already recorded release. Existing collateral release is NOT a document issuance result. HSBC proves cash concentration is an actual transfer of funds between accounts; compare to existing book-entry-transfer execution (which has no same-bank restriction) and reuse if identical result. Automatic/zero-balance objectives are service traits; a different contract instruction can still exist separately. Evidence section IDs only, no quotes. No worldwide MECE/auto adoption.
 JSON ONLY {rows:[{id,decision:retain|edit|merge|needs_source,work_ids:existingIDs,fields:null|{title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes,layer,applicability_conditions:[]},evidence_section_ids:[],reason,negative_counterexample,remaining_action}],limitations:[]}; every focus WORK ID once. Referenced existing IDs only. Short Korean explanations.''',
 input=dict(focus=[by[i] for i in ids],current_universe=[{k:w.get(k) for k in ('id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes')} for w in by.values()],primary_clauses=list(selected.values())),
 expected_ids=ids,row_key='id',work_ids=list(by),sections={k:v['text'] for k,v in selected.items()})
 path=RUN/'inputs'/(job['id']+'.json')
 if path.exists():assert read(path)==job
 else:write(path,job)
print('targeted-v18-undertaking-amendment-bounded targeted-v18-process-proof-bounded')
