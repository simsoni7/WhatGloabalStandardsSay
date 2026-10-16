"""Import the reviewed v52 screen bundle without changing existing observations."""
from pathlib import Path
import argparse,hashlib,json,shutil

p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--app-root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
root=a.app_root;bundle=a.bundle
catalog_path=root/'integration-data/catalog.json';catalog=json.loads(catalog_path.read_text())
delta=json.loads((bundle/'catalog-delta.json').read_text());assets=json.loads((bundle/'assets-manifest.json').read_text())
batch_id='public-research-v52'
if any(b.get('id')==batch_id for b in catalog.get('researchBatches',[])):
    print('Batch already imported');raise SystemExit
assert not any(delta[k] for k in ['flows','canonicalWorks','features'])
screens=delta['screens'];phrases=delta['phrases'];ids={s['id'] for s in screens};pids={p['id'] for p in phrases}
assert len(ids)==len(screens) and len(pids)==len(phrases)
assert not ids&{s['id'] for s in catalog['screens']}
assert not pids&{p['id'] for p in catalog['phrases']}
assert not {s['originalSha'] for s in screens}&{s['originalSha'] for s in catalog['screens']}
assert {s['taskId'] for s in screens}<={t['id'] for t in catalog['tasks']}
by_path={x['imagePath']:x for x in assets}
for s in screens:
    assert s['imagePath'].startswith('/assets/research-expansion-v52/') and '..' not in s['imagePath']
    asset=by_path[s['imagePath']];raw=(bundle/'public-assets'/asset['file']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==s['originalSha']==asset['sha256']
    assert len(raw)==asset['bytes'] and set(s['phraseIds'])<=pids
    assert s['currentUiVersionVerified'] is False and s['collectorNavigationChainObserved'] is False
    assert s['sourceUrl'].startswith('https://')
for phrase in phrases:
    assert set(phrase['screenIds'])<=ids and phrase['text'].strip()
for s in screens:
    dest=root/'public'/s['imagePath'].lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(bundle/'public-assets'/by_path[s['imagePath']]['file'],dest)
proof=root/'source-data/research-v52';proof.mkdir(parents=True,exist_ok=True)
for name in ['catalog-delta.json','assets-manifest.json','source-provenance.json','integrity-audit.json','summary.json','collection-report.json','model-overrides.json','prior-exclusions.json']:
    shutil.copy2(bundle/name,proof/name)
shutil.copy2(bundle/'scripts/validate_delta.py',proof/'validate_delta.py')
known={p['id']:p for p in catalog['providers']}
for provider in delta['providers']:
    if provider['id'] not in known:
        provider={k:v for k,v in provider.items() if k!='existingProvider'};catalog['providers'].append(provider);known[provider['id']]=provider
catalog['screens'].extend(screens);catalog['phrases'].extend(phrases)
for provider in catalog['providers']:
    provider['screenCount']=sum(s['providerId']==provider['id'] for s in catalog['screens'])
    provider['phraseCount']=sum(s['providerId']==provider['id'] for s in catalog['phrases'])
non_toss=[s for s in catalog['screens'] if s.get('cohort')!='toss-v6']
c=catalog['counts'];c.update(screens=len(catalog['screens']),phrases=len(catalog['phrases']),uniqueImages=len({s['originalSha'] for s in catalog['screens']}),providers=len(catalog['providers']),unknownScreenCountries=sum(not s.get('country') for s in catalog['screens']),legacyScreens=len(non_toss),legacyUniqueImages=len({s['originalSha'] for s in non_toss}),legacyPhrases=sum(p.get('cohort')!='toss-v6' for p in catalog['phrases']))
catalog['builtFrom']='retained-data-and-reviewed-public-research'
catalog.setdefault('researchBatches',[]).append({'id':batch_id,'admittedAt':delta['createdAt'],'screens':len(screens),'phrases':len(phrases),'newCompletedFlows':0,'sourceProvenance':'source-data/research-v52/source-provenance.json'})
catalog['policies']['newCollection']=True
catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+'\n')
print(json.dumps({'screensAdded':len(screens),'phrasesAdded':len(phrases),'screens':c['screens'],'phrases':c['phrases']},ensure_ascii=False))
