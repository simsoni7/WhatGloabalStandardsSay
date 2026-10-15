// Explicit public projection. Never copy runtime secrets, private queues or raw captures.
import {readFile,writeFile,mkdir,readdir,copyFile,rm} from 'node:fs/promises';
import {resolve,join,dirname,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {filterCommercialOutput} from './filter-commercial-output.mjs';
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
const catalog=await filterCommercialOutput({output,base});
// Historical provenance is immutable source; publication authorization is recorded separately.
catalog.publicRelease={authorizedBy:'project_owner_request',authorizedDate:'2026-10-16',sourceCommit:snapshot.sourceCommit,snapshotAt:snapshot.exportedAt,liveUpdates:true};
catalog.policies.tossImport='101 exact independently reviewed masked v6 copies. Project owner authorized public release on 2026-10-16. Capture date, original URL, operator and UI version remain unknown. Groups are not verified navigation.';
for(const row of catalog.screens)if(row.cohort==='toss-v6'){if(!row.approval?.privacyPassed||!row.approval?.privateReleaseEligible)throw Error('Unreviewed Toss image');row.sourceAccess=row.access;row.access='public_owner_authorized';}
for(const chunk of catalog.dictionary.chunks){
 const file=chunk.path.slice(base.length),bytes=await readFile(join(output,file));chunk.sourceSha256=chunk.sha256;chunk.sha256=sha(bytes);chunk.bytes=bytes.length;
 const proof=await readFile(join(output,chunk.provenancePath.slice(base.length)));chunk.sourceProvenanceSha256=chunk.provenanceSha256;chunk.provenanceSha256=sha(proof);
}
await json('integration-data/catalog.json',catalog);
const releaseInputs=['index.html','app.js','publications.js','about.js','dictionary.js','operations.js','styles.css','about.css','dictionary.css','operations.css','operations-plan.json'];
const release=sha(JSON.stringify(catalog)+(await Promise.all(releaseInputs.map(name=>readFile(join(root,'integration-ui',name),'utf8')))).join('\n')+await readFile(import.meta.filename,'utf8')).slice(0,16);
const intakeBase=process.env.WGSS_INTAKE_BASE||'https://wgss-public-intake.booknfoto461.chatgpt.site';
const allowedTermIds=new Set();for(const chunk of catalog.dictionary.chunks)for(const row of JSON.parse(await readFile(join(output,chunk.path.slice(base.length)),'utf8')).rows)allowedTermIds.add(row.id);
let approved={...snapshot,backendBase:intakeBase,liveUpdates:true};
try{const response=await fetch(intakeBase+'/api/wgss?resource=publications',{signal:AbortSignal.timeout(10000)});if(!response.ok)throw Error('Live snapshot unavailable');const data=await response.json();approved={...approved,exportedAt:new Date().toISOString(),items:data.items,versions:{}};for(const entry of approved.items.filter(e=>e.type==='screens')){const r=await fetch(intakeBase+'/api/wgss?resource=recordVersions&type=screens&id='+encodeURIComponent(entry.targetId),{signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error('Version snapshot unavailable');approved.versions[entry.targetId]=(await r.json()).items;}}catch{console.warn('Using the retained approved snapshot as the offline fallback');}
approved.items=(approved.items||[]).filter(e=>e.type!=='terms'||allowedTermIds.has(e.targetId));
await json('approved-snapshot.json',rewrite(approved));
const config={base,intakeBase,release,snapshotAt:approved.exportedAt};
await json('release.json',{release});
const adapter=`'use strict';
window.WGSSPublic=(()=>{
 const config=${JSON.stringify(config)};let token;
 function beginContribution(){token=[...crypto.getRandomValues(new Uint8Array(32))].map(v=>v.toString(16).padStart(2,'0')).join('');}
 function remotePaths(value){if(Array.isArray(value))return value.map(remotePaths);if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,remotePaths(v)]));if(typeof value==='string'&&value.startsWith('/api/wgss?'))return config.intakeBase+value;return value;}
 async function fetchJSON(url,options={}){
  const u=new URL(url,location.href);let headers=new Headers(options.headers||{});
  if(u.pathname==='/api/wgss'){
   if(u.searchParams.get('resource')==='session'&&(!options.method||options.method==='GET'))return {userId:null,role:'public_reader',publicIntake:true};
   u.hostname=new URL(config.intakeBase).hostname;u.protocol='https:';u.port='';
   if(options.method==='POST'){if(!token)beginContribution();headers.set('X-WGSS-Contribution-Token',token);}
  }else if(['/integration-data/','/assets/','/workspace/'].some(p=>u.pathname.startsWith(p)))u.pathname=config.base+u.pathname.slice(1);
  if(u.origin===location.origin&&u.pathname.startsWith(config.base))u.searchParams.set('v',config.release);
  let r;try{r=await fetch(u.href,{...options,headers,credentials:'omit',signal:options.signal||AbortSignal.timeout(options.method==='POST'?30000:10000)});if(!r.ok&&(!options.method||options.method==='GET')&&u.pathname==='/api/wgss')throw Error('live_unavailable');}catch(e){const resource=u.searchParams.get('resource');if(u.pathname==='/api/wgss'&&(!options.method||options.method==='GET')&&['publications','recordVersions'].includes(resource)){const saved=await fetch(config.base+'approved-snapshot.json?v='+config.release,{credentials:'omit'}).then(r=>{if(!r.ok)throw e;return r.json()});if(!document.querySelector('#api-fallback')){const note=document.createElement('p');note.id='api-fallback';note.className='publication-date';note.setAttribute('role','status');note.textContent='최신 승인 자료에 연결하지 못해 '+new Date(saved.exportedAt).toLocaleString('ko-KR')+'에 저장한 자료를 보여드립니다. 새로고침으로 다시 확인해 주세요.';document.querySelector('header').after(note);}return remotePaths({items:resource==='publications'?saved.items:(saved.versions[u.searchParams.get('id')]||[])});}throw e;}let data;try{data=await r.json()}catch{throw Error('서버 응답을 읽지 못했습니다. 잠시 후 다시 시도해 주세요.');}if(!r.ok)throw Error(data.error||'자료를 불러오지 못했습니다 ('+r.status+').');return remotePaths(data);
 }
 let checking=false;
 async function checkRelease(){if(checking||document.visibilityState==='hidden')return;checking=true;try{const response=await fetch(config.base+'release.json',{cache:'no-store',credentials:'omit',signal:AbortSignal.timeout(5000)});if(!response.ok)return;const data=await response.json();if(!/^[a-f0-9]{16}$/.test(data.release)||data.release===config.release||document.querySelector('#release-update'))return;const note=document.createElement('aside');note.id='release-update';note.className='release-update';note.setAttribute('role','status');note.innerHTML='<span>새 버전이 있습니다. 작성 중인 내용은 먼저 보내거나 복사해 주세요.</span><button type="button" class="button secondary">새 버전 열기</button>';note.querySelector('button').addEventListener('click',()=>{const u=new URL(location.href);u.searchParams.set('release',data.release);location.assign(u.href);});document.querySelector('header').after(note);}catch{}finally{checking=false;}}
 document.addEventListener('visibilitychange',checkRelease);setInterval(checkRelease,60000);
 return {fetchJSON,beginContribution,config,checkRelease};
})();\n`;
await put('pages-runtime.js',adapter);
let app=await readFile(join(root,'integration-ui/app.js'),'utf8');
app=app.replace(/async function fetchJSON\(url,options=\{\}\)\{[^\n]+\}/,'async function fetchJSON(url,options={}){return WGSSPublic.fetchJSON(url,options)}');
if(app.includes("const r=await fetch(url,{credentials:'same-origin'"))throw Error('Public API adapter was not installed');
await put('app.js',app);
for(const name of ['publications.js','styles.css','about.js','about.css','dictionary.js','dictionary.css','operations.js','operations.css','operations-plan.json'])await put(name,await readFile(join(root,'integration-ui',name)));
let html=await readFile(join(root,'integration-ui/index.html'),'utf8');
html=html.replaceAll('/workspace/',base).replace('href="/favicon.svg"','href="'+base+'favicon.svg"');
html=html.replace('<script defer src="'+base+'publications.js">','<script defer src="'+base+'pages-runtime.js"></script><script defer src="'+base+'publications.js">');
const published=new Date(approved.exportedAt).toLocaleString('ko-KR',{timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
html=html.replace('</header>','</header><p class="publication-date">공개 자료 반영 '+published+' (KST)</p>');
await put('index.html',html);await put('.nojekyll','');
await put('styles.css',(await readFile(join(output,'styles.css'),'utf8'))+'\n.release-update{display:flex;flex-wrap:wrap;align-items:center;gap:12px;max-width:1248px;margin:12px auto;padding:12px 32px;border-bottom:1px solid #e5e5e5;font-size:14px;}.publication-date{max-width:1248px;margin:12px auto 0;padding:0 32px;font-size:12px;color:#616161;}\n');
const filesToVersion=['pages-runtime.js','publications.js','app.js','styles.css','about.js','about.css','dictionary.js','dictionary.css','operations.js','operations.css'];
for(const name of filesToVersion){const token=sha(await readFile(join(output,name))).slice(0,16);html=html.replaceAll(base+name+'"',base+name+'?v='+token+'"');}
html=html.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta name="wgss-release" content="'+release+'">');
await put('index.html',html);
// Verify every admitted image is still the exact reviewed file, after path projection.
for(const row of catalog.screens){if(!row.imagePath)continue;const path=row.imagePath.slice(base.length),bytes=await readFile(join(output,path));if(row.originalSha&&sha(bytes)!==row.originalSha)throw Error('Image SHA mismatch: '+row.id);}
const manifest=[];
async function inventory(dir){for(const item of await readdir(dir,{withFileTypes:true})){const path=join(dir,item.name);if(item.isDirectory())await inventory(path);else{const raw=await readFile(path);manifest.push({path:relative(output,path).replaceAll('\\','/'),bytes:raw.length,sha256:sha(raw)});}}}
await inventory(output);
if(manifest.some(f=>/(^|\/)(\.env|\.dev\.vars|quarantine|source-store|capture-store|node_modules)(\/|$)/.test(f.path)))throw Error('Private data entered export');
await json('publication-manifest.json',{schema:'wgss-pages-release/v1',release,sourceCommit:snapshot.sourceCommit,snapshotAt:snapshot.exportedAt,publicAuthorizationDate:'2026-10-16',backendLive:true,screens:catalog.screens.length,phrases:catalog.phrases.length,dictionaryRows:catalog.counts.dictionaryTotal,files:manifest});
console.log(JSON.stringify({output,files:manifest.length,bytes:manifest.reduce((n,f)=>n+f.bytes,0),screens:catalog.screens.length,phrases:catalog.phrases.length,backendLive:true}));
