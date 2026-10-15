"""Recheck actual changed definitions, not a stale earlier model input."""
from run_mece_closure import ROOT,RUN,read,write
review=read(ROOT/'data/mece-closure-review.json')
data=read(ROOT/'dist/data/operations.json');by={w['id']:w for w in data['works']}
ids=sorted({r['work_id'] for r in review['root_decisions']} & set(by))
definitions={}
for p in (RUN/'inputs').glob('semantic-*.json'):
    j=read(p)
    for key in ['selected_original_definitions','original_source_definitions','original_clauses']:
        for d in j['input'].get(key,[]):definitions[d['id']]=d
universe=[{k:w[k] for k in ['id','title','actor_role','object_key','outcome_key','discriminator']} for w in by.values()]
jobs=[]
for n in range(0,len(ids),12):
    batch=ids[n:n+12]
    focused=[]
    for i in batch:
        w=by[i]
        evidence=[{'id':r['id'],'text':r.get('exact_quote') or definitions.get(r['id'],{}).get('definition',''),
                   'proof_scope':r.get('proof_scope','context_or_source_function_definition')} for r in w['refs']]
        focused.append({**w,'retained_source_clauses':evidence})
    job=dict(id='semantic-delta-v17-'+str(n//12+1).zfill(2),model='claude-opus-5',
      instructions='Audit CURRENT root-corrected definitions and new additions against the FULL current compact universe. NOT old 368-input states. Unit functional responsibility+directobject+one independently completable result+ONLY necessary discriminator. Joint contract parties can express one shared agreement result. Null discriminator alone NOT a defect. Generic consent/auth/claim processes can be scoped to financial services without a source literally naming WGSS; legal duties must follow actual conditions. Primary evidence does not imply actual captured UI. Report only REAL remaining collision, compound result, unsupported responsibility/legal claim or dropped existing variant. No new ID/model/human/global approval. JSONONLY {rows:[{id,decision:boundary_consistent|needs_boundary|needs_source,work_ids:existing related IDs,reason:one short Korean sentence,remaining_action:shortstring}]}. Every assignedID once. Maximum 1400 output tokens total; no fields or quotes. boundary_consistent is model advice, not source/MECE approval.',
      input=dict(focus=focused,current_universe=universe),expected_ids=batch,row_key='id',work_ids=list(by))
    target=RUN/'inputs'/(job['id']+'.json')
    if target.exists():assert read(target)==job
    else:write(target,job)
    jobs.append(job['id'])
write(RUN/'delta-manifest.json',dict(input_version=data['version'],current_work_count=len(by),expected_unique_rows=len(ids),jobs=jobs,automatic_adoption=False))
print(' '.join(jobs))
