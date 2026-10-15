// Public projection only. Commercial permission still carries the source's
// attribution, copyright, NOTICE and license conditions; it is not a waiver.
import {readFile,writeFile,mkdir,rm,readdir} from 'node:fs/promises';
import {resolve,join,dirname,sep} from 'node:path';
import {createHash} from 'node:crypto';

const sourceRoot=resolve(import.meta.dirname,'..');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const json=async path=>JSON.parse(await readFile(path,'utf8'));
const writeJSON=async(path,value)=>{const bytes=Buffer.from(JSON.stringify(value)+'\n');await mkdir(dirname(path),{recursive:true});await writeFile(path,bytes);return bytes;};
const sortCounts=counts=>Object.fromEntries([...counts].sort(([a],[b])=>a.localeCompare(b)));
const increment=(map,key)=>map.set(key,(map.get(key)||0)+1);

export async function filterCommercialOutput({output,base}){
  if(!output||!base||!base.startsWith('/')||!base.endsWith('/'))throw Error('Public output and base are required');
  output=resolve(output);
  if(output===sourceRoot||sourceRoot.startsWith(output+sep))throw Error('Refusing to filter the source checkout');
  const dataDir=join(output,'integration-data');
  const catalogPath=join(dataDir,'catalog.json');
  const catalog=await json(catalogPath);
  const navigation=await json(join(sourceRoot,'integration-data/task-extensions.json'));
  for(const task of navigation.tasks)if(!catalog.tasks.some(row=>row.id===task.id))catalog.tasks.push({...task});
  const dictionary=catalog.dictionary;
  if(!dictionary||!Array.isArray(dictionary.datasets)||!Array.isArray(dictionary.chunks))throw Error('Missing dictionary catalogue');
  const admitted=dictionary.datasets.filter(dataset=>dataset.commercial===true&&dataset.layer==='core');
  const allowed=new Set(admitted.map(dataset=>dataset.id));
  const resolveAsset=(url,directory)=>{
    if(typeof url!=='string')throw Error('Missing public dictionary asset path');
    const relative=url.startsWith(base)?url.slice(base.length):url.startsWith('/integration-data/')?url.slice(1):null;
    if(relative===null||!relative.startsWith('integration-data/'+directory+'/')||/[?#\\]/.test(relative))throw Error('Invalid public dictionary asset path: '+url);
    const path=resolve(output,relative);
    if(!path.startsWith(resolve(dataDir,directory)+sep))throw Error('Dictionary asset escaped its directory');
    return path;
  };
  const chunkFiles=new Set(),proofFiles=new Set(),seenIds=new Set();
  const keptChunks=[],languageCounts=new Map(),datasetCounts=new Map(),datasetLanguages=new Map();
  let total=0;
  for(const chunk of dictionary.chunks){
    const termPath=resolveAsset(chunk.path,'terms');
    const proofPath=resolveAsset(chunk.provenancePath,'provenance');
    const original=await json(termPath);
    if(!Array.isArray(original.rows))throw Error('Dictionary chunk has no rows');
    const rows=original.rows.filter(row=>allowed.has(row.datasetId));
    if(!rows.length){await rm(termPath,{force:true});await rm(proofPath,{force:true});continue;}
    const ids=new Set(),chunkLanguages=new Map(),chunkDatasets=new Set();
    for(const row of rows){
      if(!row.id||seenIds.has(row.id))throw Error('Duplicate or missing public term ID');
      if(row.layer!=='core')throw Error('Admitted dataset contains a non-core row');
      seenIds.add(row.id);ids.add(row.id);total++;
      increment(languageCounts,row.language);increment(chunkLanguages,row.language);increment(datasetCounts,row.datasetId);
      if(!datasetLanguages.has(row.datasetId))datasetLanguages.set(row.datasetId,new Set());
      datasetLanguages.get(row.datasetId).add(row.language);chunkDatasets.add(row.datasetId);
    }
    const originalProof=await json(proofPath);
    if(!Array.isArray(originalProof.rows))throw Error('Dictionary provenance has no rows');
    const proofRows=originalProof.rows.filter(row=>ids.has(row.evidence_id||row.id)&&(!row.dataset_id||allowed.has(row.dataset_id)));
    const proofIds=new Set(proofRows.map(row=>row.evidence_id||row.id));
    if(proofIds.size!==ids.size||[...ids].some(id=>!proofIds.has(id)))throw Error('Public term is missing original provenance');
    const termBytes=await writeJSON(termPath,{...original,rows});
    const proofBytes=await writeJSON(proofPath,{...originalProof,rows:proofRows});
    const next={...chunk,count:rows.length,bytes:termBytes.length,sha256:hash(termBytes),layer:'core',languageCounts:sortCounts(chunkLanguages),datasetIds:[...chunkDatasets].sort(),provenanceSha256:hash(proofBytes)};
    delete next.sourceSha256;delete next.sourceProvenanceSha256;
    keptChunks.push(next);chunkFiles.add(termPath);proofFiles.add(proofPath);
  }
  // Drop orphan files as well as catalogued empty chunks. A guessed URL must
  // not bypass the same dataset gate that applies to the visible search UI.
  for(const [directory,kept] of [['terms',chunkFiles],['provenance',proofFiles]]){
    const path=join(dataDir,directory);
    for(const entry of await readdir(path,{withFileTypes:true})){
      if(!entry.isFile()||!entry.name.endsWith('.json'))continue;
      const file=join(path,entry.name);if(!kept.has(file))await rm(file,{force:true});
    }
  }
  const publicDataset=dataset=>{
    const metadata=dataset.metadata||{};
    const value={id:dataset.id,name:dataset.name,count:datasetCounts.get(dataset.id)||0,layer:'core',commercial:true,license:dataset.license,urls:Array.isArray(dataset.urls)?dataset.urls:[],languages:[...(datasetLanguages.get(dataset.id)||[])].sort()};
    // These are original legal notices, not the source's internal quality notes.
    const legal={publisher:dataset.publisher||metadata.publisher,licenseNotice:dataset.licenseNotice||metadata.license_notice,attribution:dataset.attribution||metadata.attribution,usageTerms:dataset.usageTerms,correspondingSourceUrl:dataset.correspondingSourceUrl,sourceInventoryUrl:dataset.sourceInventoryUrl};
    for(const [key,item] of Object.entries(legal))if(item!==null&&item!==undefined&&item!=='')value[key]=item;
    return value;
  };
  dictionary.datasets=admitted.map(publicDataset).filter(dataset=>dataset.count>0);
  dictionary.chunks=keptChunks;
  const languageIds=new Set(languageCounts.keys());
  const languageLabels=new Map([...(catalog.languages||[]),...(dictionary.languages||[])].map(row=>[row.id,row]));
  dictionary.languages=[...languageIds].sort().map(id=>languageLabels.get(id)||{id,label:id});
  dictionary.defaultLayer='core';dictionary.conditionalRequiresOptIn=false;
  delete dictionary.downloads;
  // Practitioner filters retain observed screen/phrase languages in addition
  // to the admitted dictionary's target languages.
  const browseLanguages=new Set(languageIds);
  for(const row of [...(catalog.screens||[]),...(catalog.phrases||[]),...(catalog.features||[])])if(row.language)browseLanguages.add(row.language);
  catalog.languages=[...browseLanguages].sort().map(id=>languageLabels.get(id)||{id,label:id});
  Object.assign(catalog.counts,{dictionaryCore:total,dictionaryConditional:0,dictionaryTotal:total,dictionaryLanguages:languageIds.size,dictionaryDatasets:dictionary.datasets.length,dictionaryCoreDatasets:dictionary.datasets.length,dictionaryConditionalDatasets:0});
  const oldInventory=await json(join(dataDir,'source-inventory.json'));
  await writeJSON(join(dataDir,'source-inventory.json'),{
    schemaVersion:oldInventory.schemaVersion||1,
    release:oldInventory.release||dictionary.release,
    datasets:dictionary.datasets,
    transformationNotice:'Selected source-language pairs retain their original labels and source locators. Public search includes only commercially permitted core datasets. Preserve each source copyright, attribution, license and NOTICE when reusing or redistributing the data.'
  });
  await rm(join(dataDir,'build-manifest.json'),{force:true});
  await writeJSON(catalogPath,catalog);
  return catalog;
}
