"""Refresh the downloadable source package after a reviewed collection batch.

Includes Git-tracked and nonignored source files, never generated runtime data.
Run verify_source_data.py afterwards to validate every digest and source locator.
"""
from pathlib import Path
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
REPO=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True).strip())
PREFIX=ROOT.relative_to(REPO).as_posix()+'/'
manifest=ROOT/'SOURCE_DATA_MANIFEST.json'
data=json.loads(manifest.read_text())
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z','--',str(ROOT)],cwd=REPO).decode().split('\0')
paths=sorted({name.removeprefix(PREFIX) for name in files if name.startswith(PREFIX) and name!=PREFIX+manifest.name})
catalog=json.loads((ROOT/'integration-data/catalog.json').read_text())
allowed={x['id'] for x in catalog['dictionary']['datasets'] if x.get('commercial') is True and x.get('layer')=='core'}
rows=[]
for chunk in catalog['dictionary']['chunks']:
    rows.extend(json.loads((ROOT/chunk['path'].lstrip('/')).read_text())['rows'])
images=set()
for row in catalog['screens']+catalog['phrases']:
    if row.get('imagePath'):
        images.add(hashlib.sha256((ROOT/'public'/row['imagePath'].lstrip('/')).read_bytes()).hexdigest())
data['baseCommit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
data['data']={'screenCases':len(catalog['screens']),'phrases':len(catalog['phrases']),'distinctEvidenceImages':len(images),'dictionarySourcePairs':len(rows),'commercialDictionaryPairs':sum(r['datasetId'] in allowed for r in rows)}
data['files']=[]
for name in paths:
    path=ROOT/name
    if path.is_symlink():raise ValueError('Source package cannot contain symlinks: '+name)
    raw=path.read_bytes()
    data['files'].append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(paths),'data':data['data']},ensure_ascii=False))
