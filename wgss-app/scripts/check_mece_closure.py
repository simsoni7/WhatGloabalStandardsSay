"""Reject stale counts, fabricated quotes and premature closure claims."""
import collections,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];S=R/'research/source-store/mece-closure-20261005'
p=json.loads((R/'data/mece-closure-review.json').read_text())
d=json.loads((R/'dist/data/operations.json').read_text());by={w['id']:w for w in d['works']}
v21path=R/'data/mece-v21-root-dispositions.json'
v21=json.loads(v21path.read_text()) if v21path.exists() else None
v21_ids=set(v21['added_work_ids']+v21['edited_work_ids']) if v21 else set()
v22path=R/'data/mece-v22-root-dispositions.json'
v22=json.loads(v22path.read_text()) if v22path.exists() else None
assert p['output_version']==d['version']
assert not any(p[k] for k in ['automatic_adoption','independent_human_review','global_mece_approved'])
assert len(p['semantic_dispositions'])==368 and len({r['id'] for r in p['semantic_dispositions']})==368
assert len(p['source_dispositions'])>=57 and len({r['reference_key'] for r in p['source_dispositions']})==len(p['source_dispositions'])
assert all(set(r['work_ids'])<=set(by) for r in p['source_dispositions']), 'retired source relationships must be explicitly rebased'
v18=R/'data/mece-v18-result-dispositions.json'
if v18.exists():
    root_results=json.loads(v18.read_text())
    previous=json.loads((R/'research/source-store/mece-closure-20261006/v17-root-progress.json').read_text())
    v19path=R/'data/mece-v19-root-dispositions.json'
    v19=json.loads(v19path.read_text()) if v19path.exists() else None
    expected_sources={r['reference_key']:r for r in previous['source_dispositions']+root_results['source_dispositions']}
    if v19:
        expected_sources.update({r['reference_key']:r for r in v19['source_dispositions']})
    v20path=R/'data/mece-v20-root-dispositions.json'
    v20=json.loads(v20path.read_text()) if v20path.exists() else None
    if v20:
        expected_sources.update({r['reference_key']:r for r in v20['source_dispositions']})
    if v21:
        expected_sources.update({r['reference_key']:r for r in v21['source_dispositions']})
    if v22:
        expected_sources.update({r['reference_key']:r for r in v22['source_dispositions']})
    assert {r['reference_key']:r for r in p['source_dispositions']}==expected_sources, 'root source ledger quorum/content mismatch'
    advisory=json.loads((R/'data/mece-source-advisory-v18.json').read_text())
    assert len(advisory['rows'])==len({r['reference_key'] for r in advisory['rows']})==927
    assert len(root_results['rows'])==len({r['id'] for r in root_results['rows']})==30
    assert not any(r['automatic_adoption'] for r in root_results['rows'])
    # Recheck the admitted BIAN clauses against the original shard, not only
    # the advisory text or an ID that happens to resolve.
    from prepare_mece_v18 import plain
    nodes=json.loads((R/'research/source-store/mece-closure-20261006/source-input.json').read_text())
    originals={r['reference_key'].split(':')[-1]:r['own_sections'] for r in nodes}
    admitted=set(root_results['separate_added_result_ids'])|{i for r in root_results['rows'] if r['root_decision']=='registered_result' for i in r['work_ids']}
    if v20:
        admitted.update(v20['added_work_ids']+['WGSS-72879CC650A0'])
        frozen=json.loads((R/'research/source-store/mece-closure-v20-20261011/tickets.json').read_text())
        assert len(v20['rows'])==len({r['id'] for r in v20['rows']})==14
        assert {r['id'] for r in v20['rows']}=={r['id'] for r in frozen}
        assert {r['id'] for r in v20['remaining_work']}=={r['id'] for r in v20['rows'] if r['state']!='closed_root_decision'}
        assert not any(v20[k] for k in ['automatic_adoption','independent_human_review','global_mece_approved'])
        assert all(r['done_conditions'] and r['next_action'] for r in v20['remaining_work'])
        assert len(v20['source_followups'])==3
        current_followups=v22['source_followups'] if v22 else v21['source_followups'] if v21 else v20['source_followups']
        assert p['source_followups']==current_followups and all(r in current_followups for r in v20['source_followups']), 'new primary responsibilities cannot silently disappear'
        fixes=R/'data/mece-v20-source-fixes.json'
        if fixes.exists():admitted.update(json.loads(fixes.read_text())['work_ids'])
        if p.get('v20_delta_review'):
            reviewed=p['v20_delta_review']['rows']
            assert len(reviewed)==len({r['id'] for r in reviewed})==21
            assert {r['id'] for r in reviewed}==set(v20['added_work_ids']+v20['edited_work_ids'])
            final_snapshot=json.loads((R/'research/source-store/mece-closure-v20-20261011/catalogue-source-fixed.json').read_text())
            frozen_by={w['id']:w for w in final_snapshot['works']}
            core=['actor_role','object_key','outcome_key','discriminator','definition','includes','excludes']
            if v21:
                v21_before=json.loads((R/'research/source-store/mece-closure-v21-20261011/catalogue-before.json').read_text())
                historical_by={w['id']:w for w in v21_before['works']}
                assert all({k:historical_by[r['id']][k] for k in core}=={k:frozen_by[r['id']][k] for k in core} for r in reviewed), 'v20 frozen review history was changed'
            assert all({k:by[r['id']][k] for k in core}=={k:frozen_by[r['id']][k] for k in core} for r in reviewed if r['id'] not in v21_ids), 'unreviewed edits drifted from historical delta'
    if v21:
        admitted.update(v21_ids)
        frozen=json.loads((R/'research/source-store/mece-closure-v21-20261011/checkpoint-before.json').read_text())['remaining_work']
        assert len(v21['rows'])==len({r['id'] for r in v21['rows']})==5
        assert {r['id'] for r in v21['rows']}=={r['id'] for r in frozen}
        assert {r['id'] for r in v21['remaining_work']}=={r['id'] for r in v21['rows'] if r['state']!='closed_root_decision'}
        assert {r['id'] for r in p['remaining_work']}=={r['id'] for r in v21['remaining_work']}, 'v21 pending source boundaries disappeared'
        assert not any(v21[k] for k in ['automatic_adoption','independent_human_review','global_mece_approved'])
        v21run=R/'research/source-store/mece-closure-v21-20261011'
        original_delta=json.loads((v21run/'catalogue-after.json').read_text())
        source_fixed=json.loads((v21run/'catalogue-source-fixed.json').read_text())
        source_fixed_by={w['id']:w for w in source_fixed['works']}
        qualified=json.loads((v21run/'catalogue-policy-qualified.json').read_text())
        qualified_by={w['id']:w for w in qualified['works']}
        snapshot=json.loads((v21run/'catalogue-final.json').read_text())
        snapshot_by={w['id']:w for w in snapshot['works']}
        original_delta_by={w['id']:w for w in original_delta['works']}
        core=['title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes','refs','applicability_conditions']
        fixes=json.loads((R/'data/mece-v21-source-fixes.json').read_text())
        assert len(fixes['work_ids'])==len(set(fixes['work_ids']))==3 and set(fixes['work_ids'])<=v21_ids
        assert all({k:source_fixed_by[i].get(k) for k in core}=={k:original_delta_by[i].get(k) for k in core} for i in v21_ids-set(fixes['work_ids'])), 'unlisted source fixes changed frozen delta'
        qualification=json.loads((R/'data/mece-v21-policy-qualification.json').read_text())
        assert qualification['work_ids']==['WGSS-MECE-FUND-POLICY-AMENDMENT']
        assert all({k:qualified_by[i].get(k) for k in core}=={k:source_fixed_by[i].get(k) for k in core} for i in v21_ids-set(qualification['work_ids'])), 'unlisted changes in final policy qualification'
        override=json.loads((R/'data/mece-v21-reference-override.json').read_text())
        assert override['work_ids']==['WGSS-CB2F5FE40642'] and override['fields']==['refs']
        assert hashlib.sha256((v21run/'catalogue-final.json').read_bytes()).hexdigest()==override['snapshot_sha256']
        assert all({k:snapshot_by[i].get(k) for k in core}=={k:qualified_by[i].get(k) for k in core} for i in v21_ids-set(override['work_ids']))
        for old_ref,new_ref in zip(qualified_by['WGSS-CB2F5FE40642']['refs'],snapshot_by['WGSS-CB2F5FE40642']['refs']):
            assert {k:v for k,v in old_ref.items() if k not in ['context_requires_review','proof_scope']}=={k:v for k,v in new_ref.items() if k not in ['context_requires_review','proof_scope']}
            if old_ref!=new_ref:assert new_ref['context_requires_review'], 'reference metadata override cannot turn a concept into operative proof'
        assert all({k:by[i].get(k) for k in core}=={k:snapshot_by[i].get(k) for k in core} for i in v21_ids), 'actual v21 edits drifted from frozen delta'
        review=p.get('v21_delta_review')
        assert review and {r['id'] for r in review['rows']}==v21_ids and review['reviewed_rows']==8, 'actual current delta has not been fully reviewed'
        assert all(r['root_state']=='retained_after_source_and_counterexample_review' and not r['automatic_adoption'] for r in review['rows'])
    if v19:
        admitted.update(v19['added_work_ids'])
        fixes_path=R/'data/mece-v19-source-fixes.json'
        if fixes_path.exists():
            admitted.update(r['id'] for r in json.loads(fixes_path.read_text())['rows'])
        assert len(v19['rows'])==len({r['id'] for r in v19['rows']})==22
        assert not any(v19[k] for k in ['automatic_adoption','independent_human_review','global_mece_approved'])
        frozen=json.loads((R/'research/source-store/mece-closure-20261011/tickets.json').read_text())
        assert {r['id'] for r in v19['rows']}=={r['id'] for r in frozen}
        open_ids={r['id'] for r in v19['rows'] if r['state']!='closed_root_decision'}
        assert {r['id'] for r in v19['remaining_work']}==open_ids
        assert all(r.get('done_conditions') and r['next_action'].strip().lower() not in ['none','없음','closed',''] for r in v19['remaining_work'])
    shards={}
    for i in admitted:
        assert i in by
        assert any(r.get('exact_quote') and not r.get('context_requires_review') for r in by[i]['refs']), 'admitted financial result needs an operative anchored proof'
        for ref in by[i]['refs']:
            if not ref['id'].startswith('BIAN:'):continue
            if ref.get('context_requires_review'):continue
            native=ref['id'].rsplit(':',1)[1];meta=originals[native][0];path=Path(meta['source_file'])
            assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['source_sha256']==meta['source_file_sha256']
            if str(path) not in shards:shards[str(path)]=json.JSONDecoder().raw_decode(path.read_text().split('var objectData =',1)[1].strip())[0]
            match=re.fullmatch(r'objectData\["([0-9]+)"\]\.data\[0\]\.categories\[([0-9]+)\]\.content\.value',ref['locator'])
            assert match and match[1]==native
            text=plain(shards[str(path)][native]['data'][0]['categories'][int(match[2])]['content']['value'])
            assert ref['exact_quote'] in text,('unverified BIAN result quote',i,native)
    if v19:
        all_sections={s['section_id']:s for r in nodes for s in r['own_sections']}
        for row in v19['source_dispositions']+(v20['source_dispositions'] if v20 else [])+(v21['source_dispositions'] if v21 else []):
            assert row['evidence'], 'own-source root review needs operative evidence'
            native=row['reference_key'].rsplit(':',1)[1]
            for evidence in row['evidence']:
                section=all_sections[evidence['section_id']]
                assert section['native_id']==native, 'ancestor proof cannot masquerade as own source'
                path=Path(section['source_file']);assert hashlib.sha256(path.read_bytes()).hexdigest()==section['source_file_sha256']
                if str(path) not in shards:shards[str(path)]=json.JSONDecoder().raw_decode(path.read_text().split('var objectData =',1)[1].strip())[0]
                doc_index=int(evidence['section_id'].rsplit(':',1)[1])
                docs=[c for c in shards[str(path)][native]['data'][0]['categories'] if c['type']=='documentation']
                assert evidence['quote'] and evidence['quote'] in plain(docs[doc_index]['content']['value']), 'unverified root own-source quote'
assert p['review_counts']['root_source_rows']==len(p['source_dispositions'])
assert p['review_counts']['source_rows_not_root_adjudicated']==927-len(p['source_dispositions'])
assert p['review_counts']['semantic_pending_count']==sum(r['kind']=='semantic_or_process_source' for r in p['remaining_work'])
assert set(p['current_definition_signatures'])==set(by)
for i,w in by.items():
    signature=hashlib.sha256(json.dumps({k:w[k] for k in ['actor_role','object_key','outcome_key','discriminator','definition','includes','excludes']},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    assert signature==p['current_definition_signatures'][i],('stale definition checkpoint',i)
    for ref in w['refs']:
        if not ref['id'].startswith('WGSS-PROCESS-'):continue
        sid=ref['id'].removeprefix('WGSS-PROCESS-');store=(R/ref['source_store_relative']).resolve() if ref.get('source_store_relative') else S/'sources'
        assert store.is_relative_to((R/'research/source-store').resolve()), 'primary store must stay within private source snapshots'
        meta=json.loads((store/(sid+'.json')).read_text())
        assert hashlib.sha256((store/meta['raw_path']).read_bytes()).hexdigest()==meta['sha256']
        assert hashlib.sha256((store/meta['text_path']).read_bytes()).hexdigest()==meta['text_sha256']
        assert ref.get('exact_quote') and ref['exact_quote'] in (store/meta['text_path']).read_text(),('unverified primary quote',i,sid)
        assert not meta['ui_benchmark_admitted']
for r in p['remaining_work']:assert set(r['work_ids'])<=set(by)
gates={g['id']:g for g in p['gates']}
assert gates['semantic_me']['state']=='pending' and gates['source_ce']['state']=='pending', 'open definitions/sources cannot approve ME/CE'
assert not d['audit']['new_provider_collection_allowed'] and d['audit']['mece_approved_count']==0
assert p['review_counts']['input_mapping_gap_count']==len(d['audit']['input_mapping_gaps'])
if (R/'data/mece-standards-scope-v19.json').exists():
    standards=json.loads((R/'data/mece-standards-scope-v19.json').read_text())
    assert not standards['global_mece_approved'] and not standards['automatic_adoption']
    assert {r['id'] for r in standards['standards']}=={'ISO20022','BIAN','FIBO','NIST'}
    for row in standards['standards']:
        assert len(row['units'])==len(set(row['units']))==row['source_count']
        assert hashlib.sha256((R/row['scope_input']).read_bytes()).hexdigest()==row['source_input_sha256']
        assert not row['work_mapping_review_complete'], 'import completeness cannot approve financial work coverage'
assert all(r['root_adjudicated'] and not r['coverage_is_complete'] for r in p['source_dispositions'])
if v22:
    assert len(v22['source_dispositions'])==166 and len(p['source_dispositions'])==268
    assert p['source_followups']==v22['source_followups'] and len(p['source_followups'])==5
    assert v21['source_followups']==v22['source_followups'][:4], 'historical responsibility groups cannot disappear'
    assert v22['remaining_work']==p['remaining_work']
    assert not v22['added_work_ids'] and not v22['edited_work_ids']
    assert p['v22_source_review']==v22['review']
    assert p['v22_source_review']['opus_own_source_rows']==p['v22_source_review']['sonnet_own_source_rows']==825
    assert p['v22_source_review']['nist_opus_sections']==p['v22_source_review']['nist_sonnet_sections']==205
    for name,sha in v22['source_hashes'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==sha
print(json.dumps({'closure_checkpoint':'passed','baseline_rows':368,'current_definitions':len(by),
                  'semantic_pending':p['review_counts']['semantic_pending_count'],'root_source_rows':len(p['source_dispositions']),
                  'global_mece_approved':False}))
