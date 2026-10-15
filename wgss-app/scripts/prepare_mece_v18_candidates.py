"""Consolidate source-grounded hypotheses globally before any admission."""
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
rows=read(RUN/'source-issues-advisory.json')['rows']
refs={r['reference_key']:r for r in read(RUN/'source-input.json')}
by={w['id']:w for w in read(ROOT/'dist/data/operations.json')['works']}
candidates=[]
for r in rows:
 for n,c in enumerate(r.get('new_results',[])):
  candidates.append(dict(id=r['reference_key']+'#'+str(n),reference_key=r['reference_key'],proposal=c))
assert len(candidates)==30
write(RUN/'candidate-input.json',candidates)
universe=[{k:w.get(k) for k in ('id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes')} for w in by.values()]
instructions='''Globally consolidate 30 source-derived hypotheses, do NOT add each independently. Compare all CURRENT work definitions and ALL hypotheses. Atomic unit responsible financial role + direct object/right/obligation/info + independently intended result + only NECESSARY discriminator. Parent/child both counting is prohibited. Product type/name, source name, institution as customer vs natural person as customer, dates, calculation algorithms and implementation steps alone do not create another work. A bank opening an account at another bank is still account-owner enrollment; self-owned internal accounting mirror ledger is X03, not a financial relationship with itself. Mere securities bookkeeping/log/positions maintenance is X03; actual delivery altering asset control/holding reuses asset-transfer result if same. Root excludes software/model development, reference-data plumbing and bank customer-profitability marketing. Generic treasury funding/hedging is a parent intent over actual borrowing, asset sale, derivative contracts and market order submission: do not add generic funding parent alongside those executions. Distinguish the institution's consolidated cash-flow/capital position INFORMATION from trading-account positions/risk JUDGMENT; add only if source directly specifies the independent information result and none exists. Financial contract counterparty viewpoints cannot clone same contract result. Fund setup cannot be generic new parent plus shariah/hedge product-specific child; if same fund-formation rights result use a corrected generic retained definition with product conditions, unless actual obligations require a discriminator. Generic safekeeping mandate vs crypto/plan custody: do not add a broad parent overlapping existing children; propose reuse/narrowing/generalisation with explicit preserved scope. A future valuation date may be an input to an existing monetary valuation, not automatically a distinct result. NAV is separate only if necessary contractual price/rights result differs, not just calculation method. Customer advice may already produce a financial plan; verify original source responsibility, not word differences. Dividend payer/issuer and custodian obligations may differ but counterpart views of SAME distribution cannot be double counted. Monetary obligation settlement finality can differ from funds-provision preparation and needs its own direct source process. Master contract formation/amendment/ongoing admin must not be ONE compound. Each retained candidate must have one clear independently completable result, explicit nearest non-overlap, original proof. A genuine missing result remains a candidate; no LLM approval.
JSON ONLY {rows:[{id,decision:create_candidate|reuse_existing|merge_hypotheses|edit_existing|noncountable_context|needs_source,work_ids:existingIDs,target_candidate_ids:[],fields:null|{title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes,layer},evidence_section_ids:[suppliedIDs],reason,nonoverlap_reason,remaining_action}],limitations:[]} each assigned candidateID exactly once. Target candidate IDs must come from supplied list; explain target coverage fully. No invented ID, auto adoption, human review or worldwide MECE. Source IDs only, no quotes. Short Korean reasons.'''
jobs=[]
for start in range(0,len(candidates),6):
 batch=candidates[start:start+6]
 keys={r['reference_key'] for r in batch}
 originals=[refs[k] for k in keys]
 # Every hypothesis is visible; include all clauses actually selected by the
 # hypotheses so that proposed merges can compare the real alternative proof.
 all_selected={sid for c in candidates for sid in c['proposal']['evidence_section_ids']}
 all_sections={s['section_id']:s for r in refs.values() for s in r['own_sections']}
 allowed={sid:all_sections[sid]['text'] for sid in all_selected}
 job=dict(id=f'candidate-consolidation-v18-{start//6+1:02}',model='claude-opus-5',grounded_section_ids=True,max_tokens=11000,instructions=instructions,
  input=dict(focus=batch,all_hypotheses=candidates,current_universe=universe,original_sources=originals,selected_original_clauses=[all_sections[sid] for sid in all_selected]),
  expected_ids=[c['id'] for c in batch],row_key='id',work_ids=list(by),sections=allowed)
 path=RUN/'inputs'/(job['id']+'.json')
 if path.exists():assert read(path)==job
 else:write(path,job)
 jobs.append(job['id'])
write(RUN/'candidate-manifest.json',dict(candidates=len(candidates),jobs=jobs,automatic_adoption=False))
print(' '.join(jobs))
