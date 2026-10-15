"""Check the actual curated v1.8 definitions, rather than old suggestions."""
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
by={w['id']:w for w in read(ROOT/'dist/data/operations.json')['works']}
root=read(ROOT/'data/mece-v18-boundary-dispositions.json')
ids=sorted({a['work_id'] for a in root['actions'] if a['work_id'] in by}|{'WGSS-6CA6BDD01105'})
sections=read(RUN/'root-boundary-sections.json')
used={s for a in root['actions'] for s in a['evidence_section_ids']}
selected={s:v for s,v in sections.items() if s in used}
job=dict(id='semantic-delta-v18-boundaries',model='claude-opus-5',grounded_section_ids=True,max_tokens=11000,
 instructions='''Critique the CURRENT root-corrected definitions, not the earlier proposals. Financial work = responsible role+directobject+independent intendedresult+necessarydiscriminator. All selected primary clauses supplied. Check actor, title/definition/outcome/includes/excludes consistency, overlap with nearest CURRENT results, quoted source actually proving the responsibility, and source conditions. The root has already rejected false beneficiary-acceptance differences between URDG guarantees and UCP credits and provided the actual ISDGP79-80 text; both issuer-binding and beneficiary acceptance are shared. Rule variant alone is not new financial work. Shared counterparty contract is one result, not separate borrower/lender viewpoint clones. Unproved insurer class notice removed as a rejected hypothesis, not a global absence claim. Do not call undefined discriminator a defect. Definition-source presence is not MECE proof. Exact supplied section IDs only, no quotes.
 JSONONLY {rows:[{id,decision:retain|edit|needs_source|overlap_candidate,work_ids:existingIDs,evidence_section_ids:[],reason,fields:null|{title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes},remaining_action}],limitations:[]}; every focus work ID once, short Korean reasons. No auto adoption/independent human approval/global CE claim.''',
 input=dict(focus=[by[i] for i in ids],current_universe=[{k:w.get(k) for k in ('id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes')} for w in by.values()],primary_clauses=list(selected.values()),root_dispositions=root['actions']),
 expected_ids=ids,row_key='id',work_ids=list(by),sections={k:v['text'] for k,v in selected.items()})
target=RUN/'inputs'/(job['id']+'.json')
if target.exists():assert read(target)==job
else:write(target,job)
print(job['id'],len(ids))
