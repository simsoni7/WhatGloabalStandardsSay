import assert from 'node:assert/strict';
import {readFile,writeFile,mkdtemp,cp,readdir,rm,stat} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';
import {filterCommercialOutput} from '../scripts/filter-commercial-output.mjs';

const root=resolve(import.meta.dirname,'..');
const originalDir=join(root,'integration-data');
const source=JSON.parse(await readFile(join(originalDir,'catalog.json'),'utf8'));
const readJSON=async path=>JSON.parse(await readFile(path,'utf8'));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const blocked=new Set(source.dictionary.datasets.filter(d=>d.commercial!==true||d.layer!=='core').map(d=>d.id));
const allowed=new Set(source.dictionary.datasets.filter(d=>d.commercial===true&&d.layer==='core').map(d=>d.id));
// Count admitted source rows independently of metadata. New collection batches
// must not require changing a frozen total, or admit conditional rows with them.
const expectedIds=new Set(),expectedLanguages=new Set(),expectedDatasets=new Set();
for(const chunk of source.dictionary.chunks){
 const raw=await readJSON(join(root,chunk.path.replace(/^\//,'')));
 for(const row of raw.rows)if(allowed.has(row.datasetId)){
  assert.ok(!expectedIds.has(row.id),'source IDs are unique');
  expectedIds.add(row.id);expectedLanguages.add(row.language);expectedDatasets.add(row.datasetId);
 }
}
const checks=[];
function check(label,value){assert.ok(value,label);checks.push(label);}
async function signature(dir){
 const files=[];
 async function visit(path){for(const entry of await readdir(path,{withFileTypes:true})){const file=join(path,entry.name);if(entry.isDirectory())await visit(file);else files.push([file.slice(dir.length),sha(await readFile(file))]);}}
 await visit(dir);return JSON.stringify(files.sort(([a],[b])=>a.localeCompare(b)));
}
const sourceBefore=await signature(originalDir);
const temporary=!process.argv[2];
const output=temporary?await mkdtemp(join(tmpdir(),'wgss-commercial-output-')):resolve(process.argv[2]);
const base=process.env.WGSS_PUBLIC_BASE||'/outside-path/wgss/';
try{
 if(temporary){
  await cp(originalDir,join(output,'integration-data'),{recursive:true});
  const rewrite=value=>Array.isArray(value)?value.map(rewrite):value&&typeof value==='object'?Object.fromEntries(Object.entries(value).map(([k,v])=>[k,rewrite(v)])):typeof value==='string'&&value.startsWith('/integration-data/')?base+value.slice(1):value;
  async function project(path){for(const entry of await readdir(path,{withFileTypes:true})){const file=join(path,entry.name);if(entry.isDirectory())await project(file);else if(entry.name.endsWith('.json'))await writeFile(file,JSON.stringify(rewrite(await readJSON(file)))+'\n');}}
  await project(join(output,'integration-data'));
  // The filter must also remove orphan chunks that are absent from the index.
  await writeFile(join(output,'integration-data/terms/orphan.json'),JSON.stringify({rows:[{id:'blocked-orphan',datasetId:'mongolbank'}]}));
  await writeFile(join(output,'integration-data/provenance/orphan.json'),JSON.stringify({rows:[{evidence_id:'blocked-orphan',dataset_id:'mongolbank'}]}));
  await filterCommercialOutput({output,base});
  const firstPass=await signature(join(output,'integration-data'));
  await filterCommercialOutput({output,base});
  check('running the public projection again is byte-stable',await signature(join(output,'integration-data'))===firstPass);
 }
 const catalog=await readJSON(join(output,'integration-data/catalog.json'));
 const inventory=await readJSON(join(output,'integration-data/source-inventory.json'));
 const local=url=>join(output,url.slice(url.indexOf('integration-data/')));
 let count=0;const langs=new Set(),ids=new Set(),datasetCounts=new Map();
 for(const chunk of catalog.dictionary.chunks){
  const raw=await readFile(local(chunk.path)),proofRaw=await readFile(local(chunk.provenancePath));
  const rows=JSON.parse(raw).rows,proof=JSON.parse(proofRaw).rows;
  assert.equal(chunk.count,rows.length,'chunk count');assert.equal(chunk.bytes,raw.length,'chunk byte count');assert.equal(chunk.sha256,sha(raw),'chunk digest');assert.equal(chunk.provenanceSha256,sha(proofRaw),'provenance digest');
  assert.ok(rows.length>0,'no empty admitted chunks');
  const proofIds=new Set(proof.map(row=>row.evidence_id||row.id));
  assert.equal(proofIds.size,rows.length,'only surviving provenance IDs');
  const actualLanguages={},actualDatasets=new Set();
  for(const row of rows){assert.ok(allowed.has(row.datasetId)&&!blocked.has(row.datasetId),'only commercial core terms');assert.ok(proofIds.has(row.id),'term has provenance');assert.ok(!ids.has(row.id),'term IDs unique');ids.add(row.id);langs.add(row.language);count++;datasetCounts.set(row.datasetId,(datasetCounts.get(row.datasetId)||0)+1);actualLanguages[row.language]=(actualLanguages[row.language]||0)+1;actualDatasets.add(row.datasetId);}
  assert.deepEqual(chunk.languageCounts,Object.fromEntries(Object.entries(actualLanguages).sort(([a],[b])=>a.localeCompare(b))));assert.deepEqual(chunk.datasetIds,[...actualDatasets].sort());
  assert.ok(proof.every(row=>!row.dataset_id||allowed.has(row.dataset_id)),'no blocked provenance rows');
 }
 assert.deepEqual(ids,expectedIds,'every admitted source row, no extra or missing IDs');
 check('all public term chunks and provenance pass the dataset gate',count===expectedIds.size&&count>0);
 assert.deepEqual(langs,expectedLanguages,'exact admitted target languages');
 check('language total is calculated from surviving target rows',catalog.dictionary.languages.length===langs.size&&catalog.counts.dictionaryLanguages===langs.size);
 check('only admitted commercial core datasets are public',catalog.dictionary.datasets.length===expectedDatasets.size&&catalog.dictionary.datasets.every(d=>d.commercial===true&&d.layer==='core'&&allowed.has(d.id)));
 check('catalogue totals match the public rows',catalog.counts.dictionaryCore===count&&catalog.counts.dictionaryTotal===count&&catalog.counts.dictionaryConditional===0&&catalog.counts.dictionaryDatasets===expectedDatasets.size&&catalog.counts.dictionaryConditionalDatasets===0);
 check('dataset totals and target languages are recalculated',catalog.dictionary.datasets.every(d=>d.count===datasetCounts.get(d.id)&&d.languages.every(l=>langs.has(l))));
 check('mixed chunk 0068 retains only Malaysia rows',(await readJSON(join(output,'integration-data/terms/0068.json'))).rows.every(r=>r.datasetId==='malaysia_financial_metadata')&&(await readJSON(join(output,'integration-data/terms/0068.json'))).rows.length===99);
 check('mixed chunk 0088 retains only CLDR rows',(await readJSON(join(output,'integration-data/terms/0088.json'))).rows.every(r=>r.datasetId==='unicode_cldr_currency_names')&&(await readJSON(join(output,'integration-data/terms/0088.json'))).rows.length===174);
 const admittedFiles=new Set(catalog.dictionary.chunks.map(chunk=>local(chunk.path)));
 const admittedProofs=new Set(catalog.dictionary.chunks.map(chunk=>local(chunk.provenancePath)));
 for(const [dir,kept] of [['terms',admittedFiles],['provenance',admittedProofs]])for(const entry of await readdir(join(output,'integration-data',dir)))if(entry.endsWith('.json'))assert.ok(kept.has(join(output,'integration-data',dir,entry)),'guessed orphan URL cannot expose excluded rows');
 check('empty and orphan terms/provenance files are removed',true);
 check('full and conditional download packs are absent',!('downloads' in catalog.dictionary)&&!('downloads' in inventory));
 check('source inventory contains only admitted sources',inventory.datasets.length===expectedDatasets.size&&inventory.datasets.every(d=>allowed.has(d.id)));
 check('internal source quality metadata is not published',[...catalog.dictionary.datasets,...inventory.datasets].every(d=>!('metadata'in d)&&!('authority'in d)&&!('limitations'in d)&&!('collection'in d)&&!('sourceManifest'in d)));
 for(const original of source.dictionary.datasets.filter(d=>allowed.has(d.id))){const d=catalog.dictionary.datasets.find(d=>d.id===original.id);assert.equal(d.license,original.license);if(original.licenseNotice)assert.equal(d.licenseNotice,original.licenseNotice);if(original.metadata?.attribution)assert.equal(d.attribution,original.metadata.attribution);}
 check('original license, NOTICE and attribution strings are preserved',true);
 for(const key of ['screens','phrases','features']){
  // Paths are projected by the public builder; semantic observations stay exact.
  const strip=value=>Array.isArray(value)?value.map(strip):value&&typeof value==='object'?Object.fromEntries(Object.entries(value).map(([k,v])=>[k,strip(v)])):typeof value==='string'&&value.includes('/integration-data/')?value.slice(value.indexOf('/integration-data/')):value;
  const unproject=value=>Array.isArray(value)?value.map(unproject):value&&typeof value==='object'?Object.fromEntries(Object.entries(value).map(([k,v])=>[k,unproject(v)])):typeof value==='string'&&value.startsWith(base)?'/'+value.slice(base.length):value;
  if(temporary)assert.deepEqual(strip(unproject(catalog[key])),strip(source[key]),key+' observations unchanged');
 }
 check('financial screenshots, phrases and features are unchanged',true);
 check('private input build manifest is absent',!await stat(join(output,'integration-data/build-manifest.json')).then(()=>true,()=>false));
 check('source input files remain byte-identical',await signature(originalDir)===sourceBefore);
 console.log(JSON.stringify({status:'passed',checks:checks.length,rows:count,languages:langs.size,datasets:catalog.dictionary.datasets.length,output,items:checks},null,2));
}finally{if(temporary)await rm(output,{recursive:true,force:true});}
