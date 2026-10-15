"""Freeze outstanding boundary questions with exact primary source clauses."""
import hashlib
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
STORE=ROOT/'research/source-store/mece-closure-20261005/sources'
data=read(RUN/'catalogue-input.json');by={w['id']:w for w in data['works']}
refs=read(RUN/'source-input.json')
std={s['id']:s for s in read(ROOT/'dist/data/standards.json')['nodes']}
sections={s['section_id']:s for r in refs for s in r['own_sections']}
for s in std.values():
 if s['definition']:
  sections[s['id']]=dict(section_id=s['id'],text=s['definition'],name=s['name'],source_url=s['source_url'],
                        source_locator=s['source_locator'],source_snapshot_id=s['source_snapshot_id'])

def select(sid,terms,width=2200):
 meta=read(STORE/(sid+'.json'));text=(STORE/meta['text_path']).read_text()
 assert hashlib.sha256((STORE/meta['text_path']).read_bytes()).hexdigest()==meta['text_sha256']
 for term in terms:
  at=text.find(term);assert at>=0,(sid,term)
  key=sid+':'+str(at);sections[key]=dict(section_id=key,text=text[at:at+width],name=sid,source_url=meta['url'],
   source_locator=dict(char_start=at,char_end=min(len(text),at+width)),source_file_sha256=meta['sha256'],source_snapshot_id='WGSS-primary-process-20261006')

select('IFSB27_RETAKAFUL',['13.0.1','13.0.5'],4000)
select('ICC_UCP_AMENDMENT',['amended nor cancelled'],3500)
select('ICC_GUARANTEE_AMENDMENT',['Amendments that have been rejected'],900)
select('CHASE_MORTGAGE_SATISFACTION',['We’ll let the county know'],1500)
select('FINRA_CLASS_NOTICE',['Notice is normally'],1800)
select('IBKR_CLASS_ACTION_SCOPE',['For those clients'],1600)
select('FRB_LEASE_RETURN',['Returning the Vehicle'],2500)
old=ROOT/'research/source-store/operation-v12/closure-20261004/definitions/sources/OFAC_UNBLOCKING_RULE.txt'
text=old.read_text();at=text.find('unblocked')
key='OFAC_UNBLOCKING_RULE:'+str(at)
sections[key]=dict(section_id=key,text=text[max(0,at-900):at+3700],name='OFAC unblocking rule',
 source_url='https://ofac.treasury.gov/media/933481/download?inline=',source_locator='31 CFR 501.603(b)(3), retained Federal Register text',
 source_file=str(old),source_file_sha256=hashlib.sha256(old.read_bytes()).hexdigest())
icc=ROOT/'research/source-store/operation-v12/basis/actual-audit/gap-primary-sources/ICC_SCF2016.txt'
text=icc.read_text()
for term in ['Receivables Discounting','Factoring','Loan or Advance against Receivables']:
 starts=[];start=0
 while True:
  at=text.find(term,start)
  if at<0:break
  starts.append(at);start=at+len(term)
 # Later occurrences include the actual definition beyond the contents page.
 for at in starts[-3:]:
  key='ICC_SCF2016:'+str(at);sections[key]=dict(section_id=key,text=text[max(0,at-80):at+3800],name=term,
    source_url='https://iccwbo.org/wp-content/uploads/sites/3/2017/01/ICC-Standard-Definitions-for-Techniques-of-Supply-Chain-Finance.pdf',
    source_locator=dict(char_start=max(0,at-80),char_end=at+3800),source_file=str(icc),source_file_sha256=hashlib.sha256(icc.read_bytes()).hexdigest())
write(RUN/'boundary-sections.json',sections)
universe=[{k:w.get(k) for k in ('id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes')} for w in by.values()]
pending=read(ROOT/'data/mece-closure-review.json')['remaining_work']
groups=[pending[:5],pending[5:10],pending[10:]]
jobs=[]
instructions='''WGSS source-grounded boundary completion. Only atomic role + direct object + independently completed financial result + necessary discriminator. Joint counterparties may jointly form ONE contract; do not clone viewpoints. Definition noun alone cannot establish a duty. Do not narrow unrelated valid variants merely because supplied clauses are regional. Product labels do not split cases UNLESS they change direct rights/obligations/results (IFSB risk pooling vs conventional reinsurer assumption must be compared explicitly). Request, decision, contract effective, asset transfer and document issuance are different results. Certificate proof must show what it proves: Chase prepares mortgage satisfaction BEFORE recorder legally releases lien, not a bank certifying a pre-existing recorded release. The FINRA notice is typically court-appointed law firm, not a universal insurer duty; propose transparent noncountable external legal context if not in financial-provider scope, rather than mislabelling as proven financial institution duty. BIAN cash concentration physical transfer should be compared fully with book-entry-transfer execution and separate instructions. BIAN Employee Benefits is bank HR; it is context not necessarily customer pension membership proof. Existing definitions must be reused if actually identical.
Return JSON ONLY {rows:[{id,decision:retain|edit|merge|noncountable_context|needs_source|input_relink,work_ids:existingIDs,fields:null|{title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes,layer,applicability_conditions},evidence_section_ids:[suppliedIDs],reason,negative_counterexample,remaining_action}],new_candidates:[]} for each focus task id ONCE (task IDs, not work IDs). For input_relink map every source-defined atomic result; a source compound need not become a compound work. new_candidates require actual independently complete source-defined result and closest existing neighbours. No quotes: select original section IDs only; source text remains unchanged. A missing mandatory procedural proof must remain needs_source. No worldwide MECE or auto approval. Korean concise explanation. Don't automatically approve any proposal.'''
for n,focus in enumerate(groups,1):
 ids={i for r in focus for i in r['work_ids']};sidset={r['id'] for i in ids for r in by[i]['refs']}
 selected={k:v for k,v in sections.items() if k in sidset or (k.startswith('BIAN:') and any(k.startswith('BIAN:'+sid.split(':')[-1]+':') for sid in sidset)) or not k.startswith(('BIAN:','ISO20022:','https:'))}
 # Institution treasury mapping needs both complete original role definitions.
 for k,v in sections.items():
  if k.startswith(('BIAN:40508:','BIAN:46157:','BIAN:30731:')):selected[k]=v
 job=dict(id=f'boundary-v18-{n:02}',model='claude-opus-5',grounded_section_ids=True,max_tokens=14000,instructions=instructions,
   input=dict(focus=focus,current_definitions=[by[i] for i in ids],current_universe=universe,primary_clauses=list(selected.values()),
              explicit_scope=read(ROOT/'research/source-store/operation-v12/basis/scope.json')['explicit_exclusions']),
   expected_ids=[r['id'] for r in focus],row_key='id',work_ids=list(by),sections={k:v['text'] for k,v in selected.items()})
 target=RUN/'inputs'/(job['id']+'.json')
 if target.exists():assert read(target)==job
 else:write(target,job)
 jobs.append(job['id'])
print(' '.join(jobs))
