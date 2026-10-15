"""Recheck every claimed missing/partial source result, rather than add aliases."""
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
advisory=read(RUN/'source-review-advisory.json')['rows'];refs={r['reference_key']:r for r in read(RUN/'source-input.json')}
data=read(RUN/'catalogue-input.json');by={w['id']:w for w in data['works']}
root=read(ROOT/'data/mece-v18-boundary-dispositions.json')
for a in root['actions']:
 if a['decision']=='corrected_edit':by[a['work_id']].update(a['fields'])
aliases={a['work_id']:a.get('target_ids',[]) for a in root['actions'] if a['decision'] in ['merged','rejected_unproven_candidate']}
for i in aliases:by.pop(i)
universe=[{k:w.get(k) for k in ('id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes')} for w in by.values()]
issues=[r for r in advisory if r['decision'] in ['missing_work','linked_partial']]
instructions='''Re-adjudicate claimed missing/partial financial results using the ORIGINAL source and corrected CURRENT definitions. Atomic financial-work result role+direct financial object/right/obligation/info+independently complete result+necessary discriminator. Do NOT add every financial-sounding infrastructure capability. A mathematical credit/pricing/trading model specification, algorithm development, software configuration, reference-data plumbing, business strategy/marketing/customer profitability for BANK sales purposes is an enabling artifact/general enterprise operation, NOT by itself an applied financial judgment or financial service result. Explicit risk-policy decision or validation authority that actually changes permitted financial obligations may be financial; prove the direct result, don't infer it from model development. ATM cash inventory is a financial asset but logistics/forecasting routines do not each create independent financial outcomes; distinguish actual asset allocation, availability judgment and physical cash movement, reuse existing results. Generic servicing order/processing/management is a parent over actual ordered results and NEVER one new atomic case. Do not mistake financial content for an independently intended financial-service result. A bill reminder is a communication step of receivable collection unless source explicitly defines separate notice responsibility/result. A stakeholder/source attribute is not a new work. Broad parent source must decompose exactly supported known results and explicitly excluded implementation components; child definitions may supply detailed process proof. Don't invent a process from a label/TBD.
 Correct apparent gaps by reuse/exclusion when supported; otherwise propose a genuinely independent result with full fields and original supporting sectionIDs. Source missing own definition is a specification gap, not approval or evidence of a globally absent case. Variant and actor perspective of same shared contract outcome are not new cases. Global proposals can overlap other batches: new_results are staging candidates, not final count.
JSON ONLY {rows:[{reference_key,decision:linked_specific|linked_composed|linked_partial|excluded_scope|noncountable_context|source_specification_gap|missing_work,work_ids:existingIDs,evidence_section_ids:[suppliedIDs],reason,coverage_components:[{result,work_ids,exclusion_id:null|X01|X02|X03|X05|X06,source_section_id}],uncovered_results:[],new_results:[{title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes,layer:customer|institution|support,evidence_section_ids:[],nearest_work_ids:[],nonoverlap_reason}],exclusion_id:null|X01|X02|X03|X05|X06,remaining_action}]} all assigned sourceIDs exactly once. Keep answers concise. No quotes; exact original sections retained. No automatic adoption, worldwide CE or human review claim.'''
jobs=[]
for start in range(0,len(issues),10):
 batch=issues[start:start+10];original=[refs[r['reference_key']] for r in batch]
 allowed={s['section_id']:s['text'] for r in original for s in r['own_sections']}
 allowed.update({s['section_id']:s['text'] for r in original for c in r['related_source_context'] for s in c['sections']})
 job=dict(id=f'source-issues-v18-{start//10+1:02}',model='claude-opus-5',grounded_section_ids=True,max_tokens=14000,instructions=instructions,
  input=dict(focus=original,previous_proposals=batch,current_universe=universe,retired_aliases=aliases,
    all_other_gap_hypotheses=[dict(reference_key=r['reference_key'],uncovered_results=r['uncovered_results']) for r in issues]),
  row_key='reference_key',expected_ids=[r['reference_key'] for r in batch],work_ids=list(by),sections=allowed)
 path=RUN/'inputs'/(job['id']+'.json')
 if path.exists():assert read(path)==job
 else:write(path,job)
 jobs.append(job['id'])
write(RUN/'source-issues-manifest.json',dict(source_issue_rows=len(issues),jobs=jobs,automatic_adoption=False))
print(' '.join(jobs))
