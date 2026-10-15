"""Check source coverage, real locators and duplicate-heading grounding."""
import collections,hashlib,json,re,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from prepare_mece_v18 import plain
from nist_scope_blocks import blocks
import run_mece_closure as runner
S=R/'research/source-store/mece-closure-v22-20261011'
def read(p):return json.loads(p.read_text())
report=read(R/'data/mece-v22-root-dispositions.json');before=read(S/'checkpoint-before.json');sources=read(S/'own-source-census.json')
assert len(sources)==len({s['reference_key'] for s in sources})==825
assert len({s['reference_key'] for s in sources}|{s['reference_key'] for s in before['source_dispositions']})==927
shards={}
for src in sources:
    for section in src['own_sections']:
        path=Path(section['source_file'])
        if str(path) not in shards:
            assert hashlib.sha256(path.read_bytes()).hexdigest()==section['source_file_sha256']
            shards[str(path)]=json.JSONDecoder().raw_decode(path.read_text().split('var objectData =',1)[1].strip())[0]
        match=re.fullmatch(r'objectData\["(\d+)"\]\.data\[0\]\.categories\[(\d+)\]\.content\.value',section['source_locator'])
        assert match and match[1]==src['reference_key'].rsplit(':',1)[1]
        text=plain(shards[str(path)][match[1]]['data'][0]['categories'][int(match[2])]['content']['value'])
        assert text==section['text'], 'Own clause does not match canonical source location'
by={s['reference_key']:s for s in sources}
for row in report['source_dispositions']:
    src=by[row['reference_key']];sections={s['section_id']:s for s in src['own_sections']}
    for q in row['evidence']:assert q['section_id'] in sections and q['quote'] in sections[q['section_id']]['text']
    if row['decision']=='excluded_scope':assert row['exclusion_id'] in ['X01','X02'] and not row['uncovered_results']
    assert row['root_adjudicated'] and not row['coverage_is_complete'] and not row['automatic_adoption']
for name in ['mece-source-advisory-v22.json','quality-steward-v22-source-dispositions.json']:
    d=read(R/'data'/name);assert len(d['rows'])==len({r['reference_key'] for r in d['rows']})==825
    assert {r['reference_key'] for r in d['rows']}==set(by)
assert len(report['source_dispositions'])==166
assert not report['added_work_ids'] and not report['edited_work_ids'] and not report['global_mece_approved']
actual=[]
for book in ['a','b','c']:actual+=blocks(R/f'research/source-store/standards/raw/nist-sp800-63{book}.html',book,R)
assert actual==read(S/'nist-full-section-scope-v3.json')['blocks']
assert len(actual)==len({b['section_id'] for b in actual})==205
# Exercise repeated IDs with different bodies, the fault found in real NIST HTML.
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/'fixture.html';path.write_text('<h1 id="same">One</h1><p>First SHALL apply.</p><div><h2 id="same">Two</h2><p>Second SHALL differ.</p></div>')
    fixture=blocks(path,'c',Path(directory));assert len(fixture)==2
    assert fixture[0]['section_id']!=fixture[1]['section_id']
    assert 'First SHALL apply.' in fixture[0]['text'] and 'Second SHALL differ.' not in fixture[0]['text']
    assert 'Second SHALL differ.' in fixture[1]['text'] and 'First SHALL apply.' not in fixture[1]['text']
reviews=read(S/'nist-valid-two-model-reviews.json')['rows']
assert len(reviews)==len({r['opus']['section_id'] for r in reviews})==205
assert all(r['opus']['section_id']==r['sonnet']['section_id'] for r in reviews)
try:
    runner.execute({'id':'duplicate-input-fixture','expected_ids':['duplicate','duplicate']})
except AssertionError:
    pass
else:
    raise AssertionError('Duplicate assigned IDs must fail before prompt construction or paid requests')
for name,sha in report['source_hashes'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==sha
print(json.dumps({'v22_source_grounding':'passed','bian_own_nodes':825,'root_scope_dispositions':166,'nist_unique_sections':205,'duplicate_heading_fixture':'passed','global_mece_approved':False}))
