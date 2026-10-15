"""Verify the downloadable source/data package with Python 3 standard library only."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[1]
errors=[]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def path_for(url):
    path=url.split('?',1)[0].lstrip('/')
    return R/'public'/path if path.startswith('assets/') else R/path
def require(path,expected=None):
    if not path.is_file(): errors.append('Missing: '+str(path.relative_to(R)));return
    if expected and sha(path)!=expected:errors.append('SHA mismatch: '+str(path.relative_to(R)))
m=R/'SOURCE_DATA_MANIFEST.json'
if m.exists():
    manifest=json.loads(m.read_text())
    for file in manifest['files']:require(R/file['path'],file['sha256'])
else:
    errors.append('SOURCE_DATA_MANIFEST.json is required')
c=json.loads((R/'integration-data/catalog.json').read_text())
images={};rows=0;commercial_rows=0;provenance=0
for kind in ['screens','phrases']:
    for row in c[kind]:
        if row.get('imagePath'):
            p=path_for(row['imagePath']);require(p,row.get('originalSha'))
            if p.is_file():images[sha(p)]=str(p.relative_to(R))
for chunk in c['dictionary']['chunks']:
    path=path_for(chunk['path']);require(path,chunk.get('sha256'))
    proof=path_for(chunk['provenancePath']);require(proof,chunk.get('provenanceSha256'));provenance+=1
    if path.is_file():
        content=json.loads(path.read_text());assert len(content['rows'])==chunk['count'];rows+=len(content['rows'])
        admitted={x['id'] for x in c['dictionary']['datasets'] if x.get('commercial') is True and x.get('layer')=='core'}
        commercial_rows+=sum(x.get('datasetId') in admitted for x in content['rows'])
if m.exists():
    actual={'screenCases':len(c['screens']),'phrases':len(c['phrases']),'distinctEvidenceImages':len(images),'dictionarySourcePairs':rows,'commercialDictionaryPairs':commercial_rows}
    for key,value in manifest['data'].items():
        if actual[key]!=value:errors.append('Data count mismatch: '+key)
result={'verified':not errors,'filesChecked':len(manifest['files']) if m.exists() else 0,'screenCases':len(c['screens']),'phrases':len(c['phrases']),'distinctEvidenceImages':len(images),'dictionarySourcePairs':rows,'commercialDictionaryPairs':commercial_rows,'dictionaryChunks':len(c['dictionary']['chunks']),'provenanceFiles':provenance,'errors':errors}
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(0 if result['verified'] else 1)
