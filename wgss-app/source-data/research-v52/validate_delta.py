"""Validate the portable reviewed reference bundle without network calls or mutation."""
from pathlib import Path
import json,hashlib,argparse,collections
p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--app-root',type=Path);a=p.parse_args();r=a.bundle;d=json.load(open(r/'catalog-delta.json'));assets=json.load(open(r/'assets-manifest.json'));provenance=json.load(open(r/'source-provenance.json'));ss=d['screens'];pp=d['phrases'];ids={s['id'] for s in ss};phrases={p['id'] for p in pp};assert len(ids)==len(ss) and len(phrases)==len(pp);assert len({s['originalSha'] for s in ss})==len(ss);assert len(assets)==len(ss)==len(provenance);assert not any(d[k] for k in ['flows','canonicalWorks','features'])
providers={p['id'] for p in d['providers']};am={a['imagePath']:a for a in assets};prov={p['screenId']:p for p in provenance}
for s in ss:
 assert s['providerId'] in providers and not s['collectorNavigationChainObserved'] and not s['applicationInputObserved'];assert s['publicationDate'] is None and not s['currentUiVersionVerified'];assert s['phraseIds'] and set(s['phraseIds'])<=phrases
 asset=am[s['imagePath']];raw=(r/'public-assets'/asset['file']).read_bytes();assert len(raw)==asset['bytes'];assert hashlib.sha256(raw).hexdigest()==s['originalSha']==asset['sha256']==prov[s['id']]['displayedImageSha256'];assert s['imagePath'].startswith('/assets/research-expansion-v52/')
 assert s['sourceKind'] in ['publisher_ui_example','direct_public_capture'];assert s['sourceUrl'].startswith('https://');assert not prov[s['id']]['financialValuesSubmitted'] and not prov[s['id']]['authenticatedSessionObserved']
 if s['sourceKind']=='publisher_ui_example':assert s['publisherAssetUrl'] and s['platform']=='publisher-example'
for p in pp:
 assert set(p['screenIds'])<=ids and len(p['screenIds'])==1;assert p['text'].strip() and len(p['text'])<=500;assert p['id'] in next(s['phraseIds'] for s in ss if s['id']==p['screenIds'][0])
if a.app_root:
 base=json.load(open(a.app_root/'integration-data/catalog.json'));assert not ids&{s['id'] for s in base['screens']};assert not {s['originalSha'] for s in ss}&{s['originalSha'] for s in base['screens']};assert not phrases&{p['id'] for p in base['phrases']};assert {s['taskId'] for s in ss}<={t['id'] for t in base['tasks']};known={p['id']:p['name'] for p in base['providers']}
 for p in d['providers']:
  if p['id'] in known:assert p['name']==known[p['id']]
print(json.dumps({'status':'passed','screens':len(ss),'phrases':len(pp),'publicAssets':len(assets),'sourceClasses':dict(collections.Counter(s['sourceKind'] for s in ss)),'financialAdmissions':0,'observedCompletedFlows':0}))
