// Explicit public projection. Never copy runtime secrets, private queues or raw captures.
import {readFile,writeFile,mkdir,readdir,copyFile,rm} from 'node:fs/promises';
import {resolve,join,dirname,relative} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),output=resolve(process.argv[2]||join(root,'pages-output'));
if(output===root||root.startsWith(output+'/'))throw Error('Output must be separate from source');
const base=process.env.WGSS_PUBLIC_BASE||'/WhatGloabalStandardsSay/wgss/';
if(!/^\/[A-Za-z0-9_/-]+\/$/.test(base))throw Error('Invalid public base path');
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const snapshot=JSON.parse(await readFile(join(root,'public-snapshot.json'),'utf8'));
await rm(output,{recursive:true,force:true});await mkdir(output,{recursive:true});
function rewrite(value){
 if(Array.isArray(value))return value.map(rewrite);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,rewrite(v)]));
 if(typeof value==='string'&&['/integration-data/','/assets/','/workspace/'].some(prefix=>value.startsWith(prefix)))return base+value.slice(1);
 return value;
}
async function put(path,bytes){const target=join(output,path);await mkdir(dirname(target),{recursive:true});await writeFile(target,bytes);}
async function json(path,value){await put(path,JSON.stringify(value)+'\n');}
async function copyDirectory(source,prefix){for(const item of await readdir(source,{withFileTypes:true})){const path=join(source,item.name),dest=join(prefix,item.name);if(item.isSymbolicLink())throw Error('Symlinks cannot enter public export');if(item.isDirectory())await copyDirectory(path,dest);else{const raw=await readFile(path);if(item.name.endsWith('.json'))await json(dest,rewrite(JSON.parse(raw)));else await put(dest,raw);}}}
await copyDirectory(join(root,'integration-data'),'integration-data');
await copyDirectory(join(root,'public/assets'),'assets');
await put('favicon.svg',await readFile(join(root,'public/favicon.svg')));
const catalog=JSON.parse(await readFile(join(output,'integration-data/catalog.json'),'utf8'));
// Historical provenance is immutable source; publication authorization is recorded separately.
catalog.publicRelease={authorizedBy:'project_owner_request',authorizedDate:'2026-10-16',sourceCommit:snapshot.sourceCommit,snapshotAt:snapshot.exportedAt,liveUpdates:false};
catalog.policies.tossImport='101 exact independently reviewed masked v6 copies. Project owner authorized public release on 2026-10-16. Capture date, original URL, operator and UI version remain unknown. Groups are not verified navigation.';
for(const row of catalog.screens)if(row.cohort==='toss-v6'){if(!row.approval?.privacyPassed||!row.approval?.privateReleaseEligible)throw Error('Unreviewed Toss image');row.sourceAccess=row.access;row.access='public_owner_authorized';}
for(const chunk of catalog.dictionary.chunks){
 const file=chunk.path.slice(base.length),bytes=await readFile(join(output,file));chunk.sourceSha256=chunk.sha256;chunk.sha256=sha(bytes);chunk.bytes=bytes.length;
 const proof=await readFile(join(output,chunk.provenancePath.slice(base.length)));chunk.sourceProvenanceSha256=chunk.provenanceSha256;chunk.provenanceSha256=sha(proof);
}
await json('integration-data/catalog.json',catalog);
await json('approved-snapshot.json',rewrite(snapshot));
const config={base,backendBase:snapshot.backendBase,snapshotAt:snapshot.exportedAt};
const adapter=`'use strict';
window.WGSSPublic=(()=>{
 const config=${JSON.stringify(config)};let snapshot;
 const load=()=>snapshot||(snapshot=fetch(config.base+'approved-snapshot.json',{credentials:'omit'}).then(r=>{if(!r.ok)throw Error('공개 자료를 불러오지 못했습니다.');return r.json()}));
 async function fetchJSON(url,options={}){
  const u=new URL(url,location.href);
  if(u.pathname==='/api/wgss'){
   if(options.method&&options.method!=='GET')throw Error('제안과 관리는 운영 서버에서 이용해 주세요.');
   const resource=u.searchParams.get('resource');
   if(resource==='session')return {userId:null,role:'public_reader',publicSnapshot:true};
   const data=await load();
   if(resource==='publications')return {items:data.items};
   if(resource==='recordVersions'&&u.searchParams.get('type')==='screens')return {items:data.versions[u.searchParams.get('id')]||[]};
   throw Error('이 기능은 운영 서버에서 이용할 수 있습니다.');
  }
  if(['/integration-data/','/assets/','/workspace/'].some(p=>u.pathname.startsWith(p)))u.pathname=config.base+u.pathname.slice(1);
  const r=await fetch(u.href,{credentials:'omit',...options});if(!r.ok)throw Error('자료를 불러오지 못했습니다 ('+r.status+').');return r.json();
 }
 function handoff(kind,prefill={}){const ref=prefill.referenceId;const target=new URL('/workspace/',config.backendBase);target.hash=ref?'screens':kind==='admin'?'admin':'contribute';if(ref)target.searchParams.set('reference',ref);document.querySelector('#app').innerHTML='<section class="intro"><h1>'+(kind==='admin'?'자료 관리':'자료 제안')+'</h1><p>현재 제안 접수와 관리는 운영 계정에서 사용할 수 있습니다.</p><p>공개 화면에서는 금융사의 화면과 표현을 로그인 없이 찾아볼 수 있습니다.</p><a class="button primary" target="_blank" rel="noopener noreferrer" href="'+target.href+'">운영 서버에서 열기</a> <a class="text-button" href="#screens">레퍼런스 찾기로 돌아가기</a></section>';}
 return {fetchJSON,handoff,config};
})();\n`;
await put('pages-runtime.js',adapter);
let app=await readFile(join(root,'integration-ui/app.js'),'utf8');
app=app.replace(/async function fetchJSON\(url,options=\{\}\)\{[^\n]+\}/,'async function fetchJSON(url,options={}){return WGSSPublic.fetchJSON(url,options)}');
app=app.replace('function renderContribution(prefill={}){','function renderContribution(prefill={}){WGSSPublic.handoff("contribute",prefill);return;');
app=app.replace('async function renderAdmin(){','async function renderAdmin(){WGSSPublic.handoff("admin");return;');
if(app.includes("const r=await fetch(url,{credentials:'same-origin'"))throw Error('Public API adapter was not installed');
await put('app.js',app);
for(const name of ['publications.js','styles.css'])await put(name,await readFile(join(root,'integration-ui',name)));
let html=await readFile(join(root,'integration-ui/index.html'),'utf8');
html=html.replaceAll('/workspace/',base).replace('href="/favicon.svg"','href="'+base+'favicon.svg"');
html=html.replace('<script defer src="'+base+'publications.js">','<script defer src="'+base+'pages-runtime.js"></script><script defer src="'+base+'publications.js">');
const published=new Date(snapshot.exportedAt).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
html=html.replace('</header>','</header><p class="publication-date">공개 자료 반영 '+published+' (KST)</p>');
await put('index.html',html);await put('.nojekyll','');
await put('styles.css',(await readFile(join(output,'styles.css'),'utf8'))+'\n.publication-date{max-width:1248px;margin:12px auto 0;padding:0 32px;font-size:12px;color:#616161;}\n');
// Verify every admitted image is still the exact reviewed file, after path projection.
for(const row of catalog.screens){if(!row.imagePath)continue;const path=row.imagePath.slice(base.length),bytes=await readFile(join(output,path));if(row.originalSha&&sha(bytes)!==row.originalSha)throw Error('Image SHA mismatch: '+row.id);}
const manifest=[];
async function inventory(dir){for(const item of await readdir(dir,{withFileTypes:true})){const path=join(dir,item.name);if(item.isDirectory())await inventory(path);else{const raw=await readFile(path);manifest.push({path:relative(output,path).replaceAll('\\','/'),bytes:raw.length,sha256:sha(raw)});}}}
await inventory(output);
if(manifest.some(f=>/(^|\/)(\.env|\.dev\.vars|quarantine|source-store|capture-store|node_modules)(\/|$)/.test(f.path)))throw Error('Private data entered export');
await json('publication-manifest.json',{schema:'wgss-pages-release/v1',sourceCommit:snapshot.sourceCommit,snapshotAt:snapshot.exportedAt,publicAuthorizationDate:'2026-10-16',backendLive:false,screens:catalog.screens.length,phrases:catalog.phrases.length,dictionaryRows:catalog.counts.dictionaryTotal,files:manifest});
console.log(JSON.stringify({output,files:manifest.length,bytes:manifest.reduce((n,f)=>n+f.bytes,0),screens:catalog.screens.length,phrases:catalog.phrases.length,backendLive:false}));
