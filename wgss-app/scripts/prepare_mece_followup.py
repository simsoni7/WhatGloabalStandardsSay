"""Freeze current definitions and source clauses for bounded independent criticism."""
from run_mece_closure import ROOT, RUN, read, write

current = read(ROOT/'dist/data/operations.json')
by = {w['id']:w for w in current['works']}
initial = []
definitions = {}
for p in sorted((RUN/'inputs').glob('semantic-*.json')):
    j = read(p)
    for d in j['input'].get('selected_original_definitions',j['input'].get('original_source_definitions',[])):
        definitions[d['id']] = d
for p in sorted((RUN/'reviews').glob('semantic-*/*/proposal.json')):
    if p.parts[-3] == 'semantic-counterexample-review':
        continue
    j = read(p)
    for r in j['result']['rows']:
        if not r['decision'].startswith('retain') and r['id'] in by:
            initial.append(r)
changes = {r['work_id'] for r in read(ROOT/'data/mece-closure-review.json')['root_decisions']}
ids = sorted({r['id'] for r in initial}-changes)
instructions = '''Critique the remaining WGSS semantic findings against CURRENT source-grounded fields, not the old audit blindly. Unit: functional responsible role + direct object + independently completable intended result + ONLY NECESSARY discriminator. A null discriminator is NOT by itself a fault when object/result distinguish cases. Unicode keys are valid. Joint contract counterparties can describe ONE shared contract-formation result; do not split by viewpoint alone. Selected source omission is NOT worldwide absence. Prior broad merged source reference can be context only. Need original procedural evidence for newly asserted process, normative evidence only for legal rights/duties; law need not explicitly say WGSS financial work. Reuse exact existing results before additions. No LLM/worldwide MECE approval. Every focusID once. JSONONLY {rows:[{id,decision:retain|edit|merge|noncountable_context|needs_source,work_ids:existingIDs,evidence:[{section_id,quote}],fields:null|{title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes,layer},reason,remaining_action,negative_counterexample}]}. Short answers; retain rows fieldsnull. Exact quote from allowed clauses only. For edit explain independent financial result preserved; do NOT narrow broad retained functional coverage to only one supplied source and lose other variants. For a merge show full target coverage, no cycles. Prior root decisions override speculation unless explicit new source contradiction supplied.'''
universe = [{k:w[k] for k in ['id','title','actor_role','object_key','outcome_key','discriminator']} for w in by.values()]
jobs = []
for n in range(0,len(ids),12):
    batch = ids[n:n+12]
    refs = {r['id'] for i in batch for r in by[i]['refs']}
    sources = [definitions[i] for i in refs if i in definitions]
    sections = {d['id']:d['definition'] for d in sources}
    job = dict(id='semantic-current-followup-'+str(n//12+1).zfill(2),model='claude-opus-5',instructions=instructions,
               input=dict(focus=[by[i] for i in batch],previous_findings=[r for r in initial if r['id'] in batch],
                          current_universe=universe,original_clauses=sources,
                          prior_root_rejection='A replacement terminal is not merged into first activation merely because both activate a terminal. Existing rights/termination matter.'),
               expected_ids=batch,row_key='id',work_ids=list(by),sections=sections)
    target = RUN/'inputs'/(job['id']+'.json')
    if target.exists(): assert read(target)==job
    else:write(target,job)
    jobs.append(job['id'])
write(RUN/'followup-manifest.json',dict(input_version=current['version'],current_work_count=len(by),
                                     expected_unique_rows=len(ids),jobs=jobs,automatic_adoption=False))
print(' '.join(jobs))
