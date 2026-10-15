"""Freeze source and catalogue inputs for the next explicit closure gates."""
import hashlib, json
from pathlib import Path
from run_mece_closure import ROOT, RUN, read, write

data = read(ROOT / 'dist/data/operations.json')
works = data['works']
universe = [{k: w.get(k) for k in ('id', 'title', 'category', 'actor_role', 'object_key', 'outcome_key', 'discriminator')} for w in works]
work_ids = [w['id'] for w in works]
sources = []
keywords = {
    'HSBC_OVERDRAFT': ['You can ask', 'An arranged overdraft'],
    'HSBC_UTILISATION': ['2.  Utilisation Request', '3.'],
    'KR_INSURANCE_FORMATION': ['청약서 •', '보험증권 •', '보험자가 보험계약자로부터'],
    'ORACLE_POLICY_HISTORY': ['View Policy History This action', 'policy status history'],
    'CT_WALLET_CUSTODY': ['The\xa0difference', 'With a non-custodian'],
    'METAMASK_WALLET_CREATION': ['To create a new wallet', 'A Secret Recovery Phrase', 'Creating a new SRP'],
}
for sid, terms in keywords.items():
    metadata = read(RUN / 'sources' / (sid + '.json'))
    text = (RUN / 'sources' / (sid + '.txt')).read_bytes().decode('utf-8')
    assert hashlib.sha256(text.encode()).hexdigest() == metadata['text_sha256']
    quotes = []
    for term in terms:
        at = text.find(term)
        if at >= 0:
            quotes.append({'section_id': sid + ':' + str(at), 'locator': {'char_start': at, 'char_end': min(len(text), at + 750)}, 'text': text[at:at + 750]})
    assert quotes, sid
    sources.append({**metadata, 'selected_clauses': quotes})
sections = {q['section_id']: q['text'] for s in sources for q in s['selected_clauses']}
instructions = '''WGSS source-grounded definition closure specialist. Atomic unit = responsible contractual role + direct financial object/right/obligation/info + independently completable intended result + necessary semantic discriminator. Product names/channel/country/API CRUD are not newwork units. Parent and specialised child cannot both count same result. Request != institutional decision/execution != contract legally formed != document issued != effective cover. Existing full catalogue supplied; prefer reuse/narrow/edit/merge when actually same intended result. Do not invent absent global-work claim based on batch. Fix the supplied six unresolved definitions from new public primary process clauses; source noun alone cannot prove responsibility. Oracle process documentation supports insurer-side policy history retrieval; not a captured bank UI and not a global legal right. Wallet generation/self-custody != login account enrollment != custody assumption != provider VASP status. Loan drawdown request supports a facility utilisation; factoring invoice sale advance may have different contract and must not blindly merge. Limit change request != provider approved capacity != contract amendment. Close precisely supported results; never mark unresolved as edited just to reach zero. Each focus gets a row with id, decision(edit|merge_candidate|split_candidate|retain_unresolved|noncountable_context), work_ids(existing matching ID only), fields(title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes,boundary_distinction,status), evidence[{section_id,quote,claim}], counting_reason, negative_counterexample, missing_proof; optional new_candidates with canonical fields/proofs. Quotes exact from supplied sections. All source conditions must be explicit. JSON only {rows:[],new_candidates:[],limitations:[]}; short Korean explanations; no worldwide MECE, independent human approval or automatic adoption.'''
groups = {
    'credit': ['WGSS-9A4B541DD443', 'WGSS-9EAFFE368698', 'WGSS-16DACF2B667D'],
    'insurance': ['WGSS-77BA8EDACD11', 'WGSS-ECD7907DE4BA'],
    'wallet': ['WGSS-B41573DD9A49'],
}
jobs = []
for name, ids in groups.items():
    job = {'id': 'definition-' + name, 'model': 'claude-opus-5', 'instructions': instructions,
           'input': {'focus': [w for w in works if w['id'] in ids], 'existing_universe': universe, 'primary_process_sources': sources},
           'row_key': 'id', 'expected_ids': ids, 'work_ids': work_ids, 'sections': sections}
    jobs.append(job)

# Rebase previously unresolved source references on the current definitions, using
# the preserved original clauses rather than repeating name-only assignments.
base = ROOT / 'research/source-store/operation-v12'
prior = read(base / 'basis/actual-audit/reference-coverage-after-critical-review.json')['records']
source_input = {x['reference_key']: x for x in read(base / 'closure-20261004/scope/source-input.json')}
targets = [source_input[r['reference_key']] for r in prior if r['disposition'] == 'unresolved']
scope = read(base / 'basis/scope.json')
scope_instructions = '''WGSS critical source scope adjudication, NOT automatic approval. Actual original source sections and ALL current canonical definitions are provided. Old unmapped source status may be stale: closure additions may now cover results. Atomic work role+directobject+independentresult+necessarydiscriminator. Source reference can be broader than one atomic work; partial coverage is not full CE. An undefined/TBD source is a SOURCE SPECIFICATION GAP, not evidence that a financial work is missing; contextualize with explicit ancestor only. Never exclude because no work matches, no own definition, no UI or no manual execution. Genuine corporate HR/IT/marketing/enterpriseplanning excluded under explicit policy; customer financial tax advice, obligations, pricing, risk judgment, information results included. Financial source broad parent needs explicit constituent results, not vague new manage-product work. For each assigned reference one row {reference_key,decision:linked_specific|linked_partial|excluded_scope|source_specification_gap|missing_work,work_ids:[],evidence:[{section_id,quote}],reason,required_result:null|{title,actor_role,object_key,outcome_key,discriminator,definition,includes,excludes,nearest_work_ids},remaining_action,own_definition_present}. source_specification_gap must specify whether related known financial results exist. Customerrequest vs institutiondecision differs; API verbs/names alone don't prove it. All quoted clauses must exactly match supplied sections. Same contract result generic+product variant reuse. JSON only {rows:[],limitations:[]}, all assigned exact IDs once. No MECE or human approval claim.'''
for start in range(0, len(targets), 19):
    batch = targets[start:start + 19]
    allowed = {s['section_id']: s['text'] for r in batch for s in r['own_sections']}
    allowed.update({s['section_id']: s['text'] for r in batch for x in r['related_source_context'] for s in x['sections']})
    jobs.append({'id': 'scope-critical-' + str(start // 19 + 1).zfill(2), 'model': 'claude-opus-5', 'instructions': scope_instructions,
                 'input': {'references': batch, 'universe': universe, 'exclusions': scope['explicit_exclusions']},
                 'row_key': 'reference_key', 'expected_ids': [r['reference_key'] for r in batch], 'work_ids': work_ids, 'sections': allowed})

for job in jobs:
    target = RUN / 'inputs' / (job['id'] + '.json')
    if target.exists():
        assert read(target) == job, 'Frozen input changed; use a new stage/version'
    else:
        write(target, job)
write(RUN / 'manifest.json', {'input_version': data['version'], 'catalogue_sha256': hashlib.sha256((ROOT / 'dist/data/operations.json').read_bytes()).hexdigest(),
      'work_count': len(works), 'unresolved_definitions': sum(w['status'] == 'unresolved' for w in works),
      'source_reference_denominator': len(prior), 'critical_source_references': len(targets), 'primary_process_sources': len(sources),
      'jobs': [{'id': j['id'], 'model': j['model'], 'expected_rows': len(j['expected_ids'])} for j in jobs],
      'automatic_adoption': False, 'global_mece_approved': False})
print(json.dumps({'jobs': len(jobs), 'primary_sources': len(sources), 'critical_source_rows': len(targets)}))
