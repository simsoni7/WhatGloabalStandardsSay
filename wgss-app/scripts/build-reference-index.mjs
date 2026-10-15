// Derived administrator target IDs. Rebuilt from the same preserved browse data on every release.
import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'..');
const read=async path=>JSON.parse(await readFile(resolve(root,path),'utf8'));
const catalog=await read('integration-data/catalog.json'),out={};
const extensions=await read('integration-data/task-extensions.json');for(const task of extensions.tasks)if(!catalog.tasks.some(row=>row.id===task.id))catalog.tasks.push(task);
for(const type of ['screens','phrases','features'])out[type]=catalog[type].map(row=>Object.fromEntries(['id','title','text','label','providerId','taskId','language','workId','collectionId','cohort'].map(key=>[key,row[key]??null])));
out.terms=[];
for(const chunk of catalog.dictionary.chunks)for(const row of (await read(chunk.path.replace(/^\//,''))).rows)out.terms.push({id:row.id,datasetId:row.datasetId,label:(row.english+' / '+row.target).slice(0,160),language:row.language,layer:row.layer,chunkPath:chunk.path});
out.providers=catalog.providers.map(({id,name,aliases})=>({id,name,aliases:aliases||[]}));
out.tasks=catalog.tasks.map(({id,label,aliases,workIds,groupId})=>({id,label,aliases:aliases||[],workIds:workIds||[],groupId:groupId||null}));
out.languages=catalog.languages;
out.works=catalog.canonicalWorks.map(({id,label})=>({id,label}));
await writeFile(resolve(root,'server/wgss/reference-index.json'),JSON.stringify(out)+'\n');
console.log('Known publication targets:', ['screens','phrases','terms','features'].reduce((sum,type)=>sum+out[type].length,0));
