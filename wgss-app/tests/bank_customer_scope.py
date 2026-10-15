# Historical v1/v28 oracle retained; current v1.1 is independently checked in bank_expansion_v29.py.
"""Check customer boundaries, exact source inventories and the scoped denominator."""
import collections,csv,hashlib,json,re
from pathlib import Path
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/bank-ui-v23-20261011'
def read(p):return json.loads(p.read_text())
root=read(R/'data/bank-ui-scope-v1-baseline.json');d=read(R/'data/bank-ui-baseline-v28.json');works=d['works'];ids={w['id']:w for w in works};by={w['id'][-12:]:w for w in works};checks=[]
def check(name,ok):assert ok,name;checks.append(name)
check('finite scope approved, global finance not approved',d['status']=='confirmed_editorial_scope_v1' and root['root_approved'] and not d['global_financial_industry_mece_approved'])
check('customer core, extensions and support reconcile',len(works)==214 and sum(d['counts'][x] for x in ['core','extension','support'])==214)
check('domains are a display partition of all results',sum(d['counts']['by_domain'].values())==214 and len(d['domains'])==12)
check('distinct object/result keys, not just unique IDs',len({tuple(w['semantic_key']) for w in works})==214)
check('all legacy definitions disposed exactly once',len(root['legacy_dispositions'])==397 and len({r['legacy_id'] for r in root['legacy_dispositions']})==397)
check('institutional CSD and collateral exchange not customer work',all(k not in by for k in ['5E40B4146DF7','418C70F97764','4DFD5C8CE5A2','FB3A5CCA0EA8','F1C01AF2132D','FC7875047641','455DE4CBA874']))
for a,b,label in [('E99864B2D351','D268419B0483','service activation versus member joining'),('E1B3E50E5BED','7345035435DD','service end versus member departure'),('4012B26180F6','0565EE7BB053','financial account end versus digital access end'),('D4DF22E05F69','C45F080F8F9A','loss notice withdrawal versus unlock'),('F94E9EA98403','57106ED8458D','proofing versus authentication'),('748AAD37AC82','8D6F981E0EF8','certificate issue versus authenticator binding'),('8AB4CAD58603','591B10169113','interest collection versus recorded history'),('44B3F0605C30','2425A1EB82D8','submitted-case status versus existing mandate terms'),('86F2DD937522','38F747CB7079','credit change application versus binding amendment'),('4C7F1EEDC6B6','5CF08A29AAAD','partial credit reduction versus whole availability end'),('DFEB572279B8','86F2DD937522','self safety limit versus credit terms decision'),('F695E90DA8E7','591B10169113','issued document versus interactive history'),('8C8F9954FAF2','404A86BD87E0','confirmed balance versus projection')]:
    check(label,tuple(by[a]['semantic_key'])!=tuple(by[b]['semantic_key']))
check('same-object changes and ending produce different effects',by['533D687C4408']['object_key']==by['19FB8877A06C']['object_key'] and by['533D687C4408']['outcome_key']!=by['19FB8877A06C']['outcome_key'])
check('country and batch do not multiply transfer work',sum(w['object_key']=='payment_order' and w['outcome_key']=='submit_credit_transfer_instruction' for w in works)==1)
check('every result has source concepts and availability is separate',all(w['refs'] and w['scope_approved'] and not w['provider_availability_claimed'] for w in works))
check('historical IDs do not masquerade as current exclusion references',not any(re.search(r'WGSS-(?!UI-)',s) for w in works for s in w['includes']+w['excludes']))
for w in works:
    exact=[r['legacy_id'] for r in root['legacy_dispositions'] if r['root_decision']=='mapped' and w['id'] in r['ui_work_ids']]
    assert w['legacy_ids']==exact,w['title']
check('comparison references not counted as exact legacy mappings',True)
release=root['release_advisory_dispositions'];check('214 final reviews retained and separately root-disposed',len(release)==214 and {r['id'] for r in release}==set(ids) and all(not r['automatic_adoption'] for r in release))
source=read(P/'root-source-screening.json');check('927 own nodes verified, empty originals disclosed',source['own_clause_verified']==927 and len(source['rows'])==927 and source['counts']['source_undefined']==79)
soup=BeautifulSoup((P/'sources/hsbc-uk-ui-inventory.html').read_bytes(),'html.parser');actual={}
for ti,t in enumerate(soup.select('table')):
    if ti%2:continue
    for ri,row in enumerate(t.select('tr')):
        cells=row.find_all(['td','th'])
        if cells and ri:actual[f'HSBCUK:table:{ti}:row:{ri}']=' '.join(' '.join(cells[0].stripped_strings).split())
check('real 65 labels, not model-created compound labels',len(actual)==65 and all(actual[r['id']]==r['observed_label'] for r in root['official_inventory']))
check('all official functions have explicit scoped dispositions',all(set(r['ui_work_ids'])<=set(ids) and r['root_decision'] in ['linked_result','composed_or_conditional_context'] for r in root['official_inventory']))
sources={s['id']:s for f in ['sources.json','extra-sources.json','supplement-sources.json','final-sources.json','closure-sources.json','last-proof-sources.json'] for s in read(P/f)}
sources={f'V23:{id}':s for id,s in sources.items()}
sources.update({f'V24:{s["id"]}':s for s in read(R/'research/source-store/bank-collection-v24-20261011/sources.json')})
for prefix,batch in [('V25','bank-priority-v25-20261011'),('V25S','bank-priority-v25-supplement-20261011'),('V26','bank-priority-v26-20261011'),('V26S','bank-priority-v26-supplement-20261011'),('V27','bank-priority-v27-20261012'),('F27','bank-kakao-faq-v27-20261012'),('X27','bank-kakao-faq-v27-extra-20261012'),('W27','bank-public-capture-v27-clean-final-20261012'),('B28','bank-breadth-v28-20261012-own'),('N28','bank-breadth-additional-v28-20261012-own'),('A28','bank-breadth-additional-v28-20261012'),('T28','bank-trade-forms-v28-20261012')]:
    sources.update({prefix+':'+x['id']:x for x in read(R/'research/source-store'/batch/'sources.json')})
for b in d['benchmarks']:
    s=sources[b['source_id']];q=b['proof']
    if q['kind']=='normalized_text_character_range':assert s['text'][q['start']:q['end']]==b['expression']
    else:
        assert q['kind']=='official_image_region' and q['label']==b['expression'] and q['image_sha256']==b['screen_evidence']['image_sha256'] and b['expression'] in b['screen_evidence']['labels']
        assert hashlib.sha256((R/'dist'/b['screen_evidence']['image_path']).read_bytes()).hexdigest()==q['image_sha256']
        assert q['review']=='root_visual_checked'
    assert b['text_sha256']==hashlib.sha256(s['text'].encode()).hexdigest();assert b['raw_sha256']==s['raw_sha256'];assert not b['observed_app_screen'] and b['verified_ui_version'] is None
check('every admitted feature expression has exact preserved proof',True)
check('coverage does not fabricate screenshots',d['benchmark_counts']['observed_app_captures']==0 and d['benchmark_counts']['works_with_function_documents']==85 and d['benchmark_counts']['unlinked_works']==129 and d['benchmark_counts']['official_guide_screens']==28)
rows=list(csv.DictReader(__import__('io').StringIO(d['csv_artifacts']['bank-ui-works.csv'].lstrip('\ufeff'))));check('download is the same complete denominator',len(rows)==214 and {r['id'] for r in rows}==set(ids))
print(json.dumps({'bank_customer_scope':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
