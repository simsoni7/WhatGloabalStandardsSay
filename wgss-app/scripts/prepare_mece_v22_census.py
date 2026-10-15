"""Freeze every still-unadjudicated BIAN own clause against the actual catalogue.

Preparation only: no model proposal changes the accepted ledger.
"""
import hashlib,json
from pathlib import Path
from prepare_mece_v18 import plain
from run_mece_closure import ROOT,read,write

RUN=ROOT/'research/source-store/mece-closure-v22-20261011'

def prepare():
    assert not (RUN/'manifest.json').exists(), 'Use a new identity instead of changing frozen inputs'
    catalogue=read(ROOT/'dist/data/operations.json')
    checkpoint=read(ROOT/'data/mece-closure-review.json')
    scope=read(ROOT/'research/source-store/operation-v12/basis/scope.json')
    sources=read(ROOT/'research/source-store/mece-closure-20261006/source-input.json')
    advisory={r['reference_key']:r for r in read(ROOT/'data/mece-source-advisory-v18.json')['rows']}
    rooted={r['reference_key'] for r in checkpoint['source_dispositions']}
    shards={};refs=[]
    for src in sources:
        if src['reference_key'] in rooted: continue
        sections=[]
        for old in src['own_sections']:
            path=Path(old['source_file'])
            if str(path) not in shards:
                assert hashlib.sha256(path.read_bytes()).hexdigest()==old['source_file_sha256']
                shards[str(path)]=json.JSONDecoder().raw_decode(path.read_text().split('var objectData =',1)[1].strip())[0]
            native=old['native_id']; cats=shards[str(path)][native]['data'][0]['categories']
            docs=[(n,c) for n,c in enumerate(cats) if c['type']=='documentation']
            index=int(old['section_id'].rsplit(':',1)[1]); n,c=docs[index]
            assert old['text']==plain(c['content']['value']), 'Frozen clause drift'
            sections.append({**old,'source_locator':f'objectData["{native}"].data[0].categories[{n}].content.value'})
        refs.append(dict(reference_key=src['reference_key'],name=src['name'],kind=src['kind'],own_sections=sections,
                         previous_advisory=advisory[src['reference_key']]))
    assert len(refs)==825
    write(RUN/'catalogue-before.json',catalogue);write(RUN/'checkpoint-before.json',checkpoint)
    write(RUN/'own-source-census.json',refs);write(RUN/'scope-contract.json',scope)
    universe=[{k:w.get(k) for k in ['id','title','layer','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes']} for w in catalogue['works']]
    instructions='''You are the WGSS finite-source coverage auditor. Review EVERY assigned BIAN node's OWN clauses against the actual current financial-work catalogue. Past advisory is fallible, stale, NOT authority. Use full own role and example together; ancestors/children cannot supply missing own duties. Unit: responsible role + direct object + independently completed intended result + necessary discriminator. No product/country/method/CRUD/status/API or counterparty viewpoint clones. A workflow parent is not an additional result. Existing title similarity is not sufficient: compare definition, actor responsibility, direct object, completion and exclusions. X01 excludes ordinary enterprise HR/buildings/IT/marketing/product strategy, NOT financial customer service, risk judgments, financial information, fees, funding or obligations. X03 excludes machine plumbing/bookkeeping implementation, NOT independently completed financial control decisions or information results. Mere underspecification is a SOURCE GAP, not exclusion. Never invent approve/execute/terminate from generic 'manage', 'initiate', or 'track'. Distinguish request submission, provider judgment, actual legal/economic result. Source-specific practices/conditions cannot be universalized.
Return ONLY JSON {rows:[{reference_key,decision:linked_specific|linked_composed|linked_partial|excluded_scope|noncountable_context|source_specification_gap|missing_work,work_ids:[],evidence_section_ids:[],reason,coverage_components:[{result,work_ids:[],exclusion_id:null|X01|X02|X03|X05|X06,source_section_id}],uncovered_results:[short concrete result or source ambiguity],exclusion_id:null|X01|X02|X03|X05|X06,remaining_action}]}. Exactly every assigned ID once. Use only supplied IDs and own evidence_section_ids, never evidence quotes. Evidence section IDs alone do not prove complete coverage. For composed/partial sources enumerate ALL express own responsibilities, each mapped/excluded/uncovered. Where one clause itself lacks independently completed outcome state the ambiguity precisely. Decision linked_specific/composed requires zero uncovered results; excluded requires real scope evidence. Concise Korean reasons and short components. MAX 180 words per row. No final worldwide MECE/human approval/automatic adoption claims.'''
    jobs=[]
    for start in range(0,len(refs),55):
        batch=refs[start:start+55]; sections={s['section_id']:s['text'] for r in batch for s in r['own_sections']}
        jid=f'census-v22-{start//55+1:02}'
        job=dict(id=jid,model='claude-opus-5',max_tokens=24000,instructions=instructions,
                 input=dict(references=batch,current_universe=universe,scope_exclusions=scope['explicit_exclusions']),
                 expected_ids=[r['reference_key'] for r in batch],row_key='reference_key',
                 work_ids=[w['id'] for w in catalogue['works']],sections=sections,grounded_section_ids=True)
        write(RUN/'inputs'/(jid+'.json'),job);jobs.append(jid)
    write(RUN/'manifest.json',dict(input_version=catalogue['version'],baseline_work_count=len(universe),
          baseline_root_source_count=len(rooted),pending_source_count=len(refs),source_denominator=len(sources),jobs=jobs,
          catalogue_sha256=hashlib.sha256((RUN/'catalogue-before.json').read_bytes()).hexdigest(),
          automatic_adoption=False,global_mece_approved=False))
    print(json.dumps({'frozen_works':len(universe),'pending_own_nodes':len(refs),'opus_jobs':len(jobs)}))

if __name__=='__main__':prepare()
