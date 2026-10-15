"""Freeze the full BIAN source census against current definitions, never adopt it."""
import collections, hashlib, html, json, re
from html.parser import HTMLParser
from pathlib import Path
from run_mece_closure import ROOT, read, write

RUN = ROOT / 'research/source-store/mece-closure-20261006'
LAND = Path('/home/ubuntu/wgss-mece-review/landscape')

class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self, data): self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ('br','p','li'): self.parts.append('\n')

def plain(value):
    p=Text(); p.feed(value)
    return re.sub(r'[ \t]+',' ',html.unescape(''.join(p.parts))).strip()

def sections(node):
    path=LAND/node['source_file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==node['source_file_sha256']
    result=[]
    for n,doc in enumerate(node['documentation']):
        if 'content' in doc:
            text=plain(doc['content'].get('value',''))
            title=doc['title']
        else: text=doc['text']; title=doc['title']
        if text:
            result.append(dict(section_id=f"BIAN:{node['native_id']}:doc:{n}",text=text,title=title,
                native_id=node['native_id'],name=node['name'],source_url=node['source_url'],
                source_file=str(path),source_file_sha256=node['source_file_sha256'],
                source_locator=f"objectData[{json.dumps(node['native_id'])}].data[0].documentation[{n}]"))
    return result

def prepare():
    data=read(ROOT/'dist/data/operations.json')
    by={w['id']:w for w in data['works']}
    universe=[{k:w.get(k) for k in ('id','title','layer','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes')}
              for w in by.values()]
    hierarchy=read(LAND/'bian-capability-hierarchy.json')
    nodes=read(LAND/'bian-landscape-domains.json')+hierarchy['nodes']
    lookup={n['native_id']:n for n in nodes}
    children=collections.defaultdict(list);parents=collections.defaultdict(list)
    for edge in hierarchy['hierarchy_edges']:
        children[edge['from_id']].append(edge['to_id']);parents[edge['to_id']].append(edge['from_id'])
    prior={r['reference_key']:r for r in read(ROOT/'research/source-store/operation-v12/basis/actual-audit/reference-coverage-after-critical-review.json')['records']}
    critical={r['reference_key']:r for r in read(ROOT/'data/mece-closure-review.json')['source_dispositions']}
    refs=[]
    for node in nodes:
        kind='BusinessCapability' if node['native_id'] in {n['native_id'] for n in hierarchy['nodes']} else 'ServiceDomain'
        key=next(k for k in prior if k.endswith(':'+node['native_id']) and prior[k]['name']==node['name'])
        ctx=[]
        for relation,ids in [('parent',parents[node['native_id']]),('direct_child',children[node['native_id']])]:
            for i in ids:
                ctx.append(dict(relation=relation,native_id=i,name=lookup[i]['name'],sections=sections(lookup[i])))
        refs.append(dict(reference_key=key,name=node['name'],kind=kind,own_sections=sections(node),
            related_source_context=ctx,prior_proposal=prior[key],prior_root_review=critical.get(key)))
    assert len(refs)==927 and len({r['reference_key'] for r in refs})==927
    write(RUN/'source-input.json',refs)
    write(RUN/'catalogue-input.json',data)
    instructions='''Review ONE frozen BIAN source reference against CURRENT WGSS definitions. All old proposals are unapproved and their raw operation IDs are obsolete. Atomic unit is functional responsible role + direct financial object + independently completed result + necessary discriminator. A country/product/channel/CRUD variant is not another result. Do not accept name similarity as full coverage. Source noun or ancestor does not prove exact duty. Joint contract formation is one shared result; actor viewpoints alone not duplicates. A broad source may need several known results; parent is not an extra count. General HR/buildings/IT/marketing/business strategy, ordinary nonfinancial shipping, machine API plumbing are excluded only when the source actually says that; financial customer information, risk judgments, funding/liquidity management, fees, tax advice, obligation processing remain in scope. No definition/TBD is a specification gap, NOT automatically nonfinancial. Code/module/software support may be contextual noncountable implementation, not missing financial result.
Every assigned reference exactly once. Return concise JSON ONLY {rows:[{reference_key,decision:linked_specific|linked_composed|linked_partial|excluded_scope|noncountable_context|source_specification_gap|missing_work,work_ids:existingIDs,evidence:[{section_id,quote}],reason,coverage_components:[{result,work_ids,exclusion_id:null|X01|X02|X03|X05|X06,source_section_id}],uncovered_results:[],required_result:null|{title,actor_role,object_key,outcome_key,discriminator,definition,nearest_work_ids},exclusion_id:null|X01|X02|X03|X05|X06,remaining_action}]}.
Evidence quotes MUST be a short EXACT contiguous excerpt from the supplied section, not translation/ellipsis/paraphrase. If no substantive own text, cite explicit parent only as qualified context or leave evidence empty and mark specification gap. Each composed/partial source needs explicit component results and corresponding existing work IDs or explicit scope exclusions. A broad in-scope parent with constituent gaps is partial, never fully linked. Report source ambiguities without fabricating a process. Do not claim worldwide MECE, standard equivalence, human approval, or auto adoption. Korean short reasons, no fields unrelated to requested schema. Max ~140 words per row.'''
    scope=read(ROOT/'research/source-store/operation-v12/basis/scope.json')
    jobs=[]
    # Role definitions first, then hierarchical capabilities. Fixed inputs are
    # intentionally separate from the v1.7 run and cannot overwrite its audit.
    for start in range(0,len(refs),24):
        batch=refs[start:start+24]
        allowed={s['section_id']:s['text'] for r in batch for s in r['own_sections']}
        allowed.update({s['section_id']:s['text'] for r in batch for c in r['related_source_context'] for s in c['sections']})
        job=dict(id=f'scope-full-v18-{start//24+1:02}',model='claude-opus-5',max_tokens=14000,instructions=instructions,
            input=dict(references=batch,current_universe=universe,scope_exclusions=scope['explicit_exclusions']),
            row_key='reference_key',expected_ids=[r['reference_key'] for r in batch],work_ids=list(by),sections=allowed)
        path=RUN/'inputs'/(job['id']+'.json')
        if path.exists(): assert read(path)==job,'Frozen input changed'
        else: write(path,job)
        jobs.append(job['id'])
    write(RUN/'manifest.json',dict(input_version=data['version'],baseline_work_count=len(by),
        source_denominator=len(refs),catalogue_sha256=hashlib.sha256((ROOT/'dist/data/operations.json').read_bytes()).hexdigest(),
        jobs=jobs,automatic_adoption=False))
    print(json.dumps(dict(jobs=len(jobs),source_rows=len(refs),baseline_works=len(by))))

if __name__=='__main__': prepare()
