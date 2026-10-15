import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,copyFile,rm,readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createRequire} from 'node:module';
import ts from 'typescript';
import {Miniflare} from 'miniflare';

const root=resolve(import.meta.dirname,'../..'),output=await mkdtemp(join(tmpdir(),'wgss-api-'));
for(const name of ['core','submissions','jobs','images','publications','api']) {
  const source=await readFile(join(root,'server/wgss',`${name}.ts`),'utf8');
  await writeFile(join(output,`${name}.js`),ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,esModuleInterop:true,resolveJsonModule:true}}).outputText);
}
for(const name of ['known-sources.json','evidence-index.json','reference-index.json']) {try {await copyFile(join(root,'server/wgss',name),join(output,name));} catch(error){if(error.code!=='ENOENT')throw error;} }
const require=createRequire(import.meta.url),{handleRequest}=require(join(output,'api.js')),{getActor,hash}=require(join(output,'core.js'));
const miniflare=new Miniflare({modules:true,script:'export default { fetch(){return new Response("test")} }',compatibilityDate:'2026-05-15',d1Databases:{DB:'wgss-test'},r2Buckets:['BUCKET']});
const DB=await miniflare.getD1Database('DB'),BUCKET=await miniflare.getR2Bucket('BUCKET');
for(const file of (await readdir(join(root,'drizzle'))).filter(f=>f.endsWith('.sql')).sort())for(const sql of (await readFile(join(root,'drizzle',file),'utf8')).split('--> statement-breakpoint')) if(sql.trim())await DB.prepare(sql.trim()).run();
const env={DB,BUCKET,ADMIN_USER_IDS:'admin',BEDROCK_API_KEY:'test-private-key-do-not-echo',BEDROCK_SONNET_INPUT_USD_PER_MILLION:'3',BEDROCK_SONNET_OUTPUT_USD_PER_MILLION:'15'};
const admin=getActor('admin',env),alice=getActor('alice',env),bob=getActor('bob',env),anonymous=getActor(null,env);
const originalFetch=globalThis.fetch;
async function call(actor,body=null,resource='submissions',extraHeaders={}) {const request=new Request(`https://workspace.test/api/wgss?${resource.includes('=')?resource:`resource=${resource}`}`,body===null?{}:{method:'POST',headers:{'Content-Type':'application/json',...extraHeaders},body:JSON.stringify(body)}); const response=await handleRequest(request,env,actor);return {status:response.status,body:await response.json()};}
async function create(kind='text',text='Continue to the next step') {const response=await call(alice,{action:'createSubmission',kind,title:'Safe test reference',text,language:'en',country:'unknown'});assert.equal(response.status,200);return response.body.item;}
function defaultApplication(item,more={}) {const screen=item.kind==='screen';return {type:screen?'screens':'phrases',operation:'add',expectedRevision:0,imageFileIds:screen?(more.maskedFileIds||[more.maskedFileId].filter(Boolean)):[],fields:{...(screen?{title:'Synthetic reviewed screen'}:{text:'Synthetic reviewed phrase'}),providerId:'citi',language:'en',taskId:'signup'}};}
async function approve(item,more={}) {const result=await call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,application:defaultApplication(item,more),...more});assert.equal(result.status,200,JSON.stringify(result.body));return result.body.item;}
const png=Uint8Array.from(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a3ioAAAAASUVORK5CYII=','base64'));
async function uploadFile(item,role='masked',bytes=png,mime='image/png') {const form=new FormData();form.set('action','upload');form.set('submissionId',item.id);form.set('role',role);form.set('file',new File([bytes],'sensitive-customer-filename.png',{type:mime})); const response=await handleRequest(new Request('https://workspace.test/api/wgss',{method:'POST',body:form}),env,alice);return {status:response.status,body:await response.json()};}

test('runtime grants admin only to configured identities or explicit owner-private service boundary',()=>{
 assert.equal(getActor('first-caller',{}).role,'contributor'); assert.equal(getActor(null,{}).role,'anonymous');
 assert.equal(getActor('alice',{WGSS_ADMIN_EMAILS:'OWNER@EXAMPLE.TEST'},'owner@example.test').role,'admin');
 assert.equal(getActor(null,{WGSS_ADMIN_EMAILS:'owner@example.test'},'owner@example.test').role,'anonymous');
 assert.equal(getActor(null,{WGSS_PRIVATE_SERVICE_ACCESS:'true'}).role,'admin');
 assert.equal(getActor('bob',{WGSS_PRIVATE_SERVICE_ACCESS:'true'}).role,'contributor');
});
test('authentication and admin enforcement applies to real operations',async()=>{
 assert.equal((await call(anonymous)).status,401);
 for(const resource of ['jobs','audit','settings','sources'])assert.equal((await call(alice,null,resource)).status,403);
 assert.equal((await call(alice,{action:'updateSettings',settings:{scheduleEnabled:true},role:'admin'})).status,403);
 const item=await create();assert.equal((await call(bob,null,`resource=versions&id=${item.id}`)).status,403);
 assert.equal((await call(bob,{action:'createVersion',id:item.id,expectedVersion:1,text:'stolen'})).status,403);
});
test('source versions are immutable, reviews atomic, and stale review cannot overwrite a newer source',async()=>{
 const item=await create();const updated=await call(alice,{action:'createVersion',id:item.id,expectedVersion:1,text:'Submit application'});assert.equal(updated.body.item.version,2);
 const stale=await call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:1,decision:'approved',privacyReviewed:true,readabilityReviewed:true});assert.equal(stale.status,409);
 assert.equal((await call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:2,decision:'approved'})).status,400);
 const approved=await approve(updated.body.item,{reason:'Reviewed exact native label and source context'});assert.equal(approved.version,3);
 const versions=(await call(alice,null,`resource=versions&id=${item.id}`)).body.items;
 assert.deepEqual(versions.map(v=>v.version),[3,2,1]);assert.equal(versions[0].reviewReason,'Reviewed exact native label and source context');assert.equal(versions[2].content.text,'Continue to the next step');assert.equal(versions[1].content.text,'Submit application');
 const concurrent=await Promise.all([call(admin,{action:'createVersion',id:item.id,expectedVersion:3,text:'First edit'}),call(admin,{action:'createVersion',id:item.id,expectedVersion:3,text:'Second edit'})]);
 assert.deepEqual(concurrent.map(r=>r.status).sort(),[200,409]);
 const audit=(await call(admin,null,'audit')).body.items.filter(a=>a.entityId===item.id);assert.equal(audit.filter(a=>a.action==='submission.versioned').length,2);
});
test('uploads reject unsafe formats and MIME spoofing, retain UUID keys, and isolate quarantine reads',async()=>{
 const item=await create('screen');
 assert.equal((await uploadFile(item,'original',new TextEncoder().encode('<svg xmlns="http://www.w3.org/2000/svg"></svg>'),'image/svg+xml')).status,415);
 assert.equal((await uploadFile(item,'original',png,'image/jpeg')).status,415);
 const result=await uploadFile(item,'original');assert.equal(result.status,200);assert.equal(result.body.item.version,2);
 const file=result.body.item.files[0];assert.equal(file.reviewStatus,'pending');
 const stored=await DB.prepare('SELECT object_key FROM wgss_files WHERE id=?').bind(file.id).first();assert(!stored.object_key.includes('sensitive'));assert(stored.object_key.startsWith('quarantine/'));
 assert.equal((await handleRequest(new Request(`https://workspace.test/api/wgss?resource=file&id=${file.id}`),env,bob)).status,403);
 const own=await handleRequest(new Request(`https://workspace.test/api/wgss?resource=file&id=${file.id}`),env,alice);assert.equal(own.status,200);assert.equal(own.headers.get('Cache-Control'),'private, no-store');assert(!own.headers.get('Content-Disposition').includes('sensitive'));
 const approval=await call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:2,decision:'approved',privacyReviewed:true,readabilityReviewed:true});assert.equal(approval.status,400);
});
test('privacy gate prevents every unapproved outbound call; approved exact masked bytes are the only image egress',async()=>{
 let calls=0,lastBody;
 globalThis.fetch=async(url,options)=>{calls++;assert.equal(options.redirect,'manual');assert.equal(url,'https://frontier-llmgw.aipocnhbank.com/v1/chat/completions');lastBody=JSON.parse(options.body);return new Response('data: {"choices":[{"delta":{"content":"Advisory: label needs context."},"finish_reason":null}]}\n\ndata: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":100,"completion_tokens":20}}\n\ndata: [DONE]\n',{headers:{'content-type':'text/event-stream'}});};
 try {
 const item=await create('screen','Safe reviewed caption');
 assert.equal((await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'screen_review'})).status,409);assert.equal(calls,0);
 const original=await uploadFile(item,'original');const masked=await uploadFile(original.body.item,'masked');
 const file=masked.body.item.files.find(f=>f.role==='masked');const approved=await approve(masked.body.item,{maskedFileId:file.id});
 const result=await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'screen_review'});assert.equal(result.status,200);assert.equal(result.body.job.status,'completed');assert.equal(calls,1);
 assert.deepEqual(result.body.job.usage,{prompt_tokens:100,completion_tokens:20,total_tokens:120});assert.equal(result.body.job.cost.usd,0.0006);assert.equal(result.body.job.result.automaticallyApplied,false);
 assert.equal(lastBody.messages[1].content.filter(c=>c.type==='image_url').length,1);assert.equal(lastBody.messages[1].content[1].image_url.url,`data:image/png;base64,${Buffer.from(png).toString('base64')}`);
 assert.equal(result.body.job.result.evidence[1].fileId,file.id);assert.equal(result.body.job.result.evidence[1].sha256,await hash(png));
 const raw=await DB.prepare('SELECT object_key FROM wgss_files WHERE id=?').bind(file.id).first();await BUCKET.put(raw.object_key,new TextEncoder().encode('tampered masked image'));
 assert.equal((await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'screen_review'})).status,409);assert.equal(calls,1);
 const version=await call(admin,{action:'createVersion',id:item.id,expectedVersion:approved.version,text:'New unreviewed content'});assert.equal(version.status,200);
 assert.equal((await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'screen_review'})).status,409);assert.equal(calls,1);
 } finally {globalThis.fetch=originalFetch;}
});
test('gateway failure and truncation are retained honestly, without secrets or automatic publishing',async()=>{
 const item=await approve(await create());
 globalThis.fetch=async()=>new Response('private error test-private-key-do-not-echo',{status:429});
 try{const result=await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'translation_review'});assert.equal(result.body.job.status,'failed');assert.match(result.body.job.error,/HTTP 429/);assert(!JSON.stringify(result).includes(env.BEDROCK_API_KEY));}finally{globalThis.fetch=originalFetch;}
 globalThis.fetch=async()=>Response.json({choices:[{message:{content:'Incomplete advisory'},finish_reason:'length'}],usage:{prompt_tokens:12,completion_tokens:8}});
 try{const result=await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'quality_review'});assert.equal(result.body.job.status,'failed');assert.equal(result.body.job.result.truncated,true);assert.equal(result.body.job.result.automaticallyApplied,false);}finally{globalThis.fetch=originalFetch;}
});
test('saved comparisons persist and cannot be read or removed by another contributor',async()=>{
 const saved=await call(alice,{action:'saveComparison',name:'Country and stage match',referenceIds:['frozen-a','frozen-b'],context:{task:'signup',country:'unknown'}});assert.equal(saved.status,200);
 assert((await call(alice,null,'comparisons')).body.items.some(i=>i.id===saved.body.item.id));assert.equal((await call(bob,null,'comparisons')).body.items.length,0);
 assert.equal((await call(bob,{action:'deleteComparison',id:saved.body.item.id})).status,404);
 assert.equal((await call(alice,{action:'saveComparison',name:'Duplicate',referenceIds:['a','a']})).status,400);
});
test('market scan only reaches exact known HTTPS sources; redirects and failures are evidence statuses',async()=>{
 let calls=0;globalThis.fetch=async()=>{calls++;return new Response('',{status:302,headers:{location:'http://127.0.0.1/private'}});};
 try{
 for(const url of ['http://127.0.0.1','https://127.0.0.1/','https://example.invalid/','https://google.com/unknown-source'])assert.equal((await call(admin,{action:'runMarketScan',urls:[url]})).status,400);
 assert.equal(calls,0);const known=JSON.parse(await readFile(join(root,'server/wgss/known-sources.json'),'utf8'))[0];
 const result=await call(admin,{action:'runMarketScan',urls:[known,known]});assert.equal(calls,1);assert.equal(result.body.job.status,'failed');assert.equal(result.body.job.result.evidence[0].httpStatus,302);assert.equal(result.body.job.result.automaticallyApplied,false);
 globalThis.fetch=async()=>{calls++;return new Response('<html>Same official source body</html>',{headers:{'content-type':'text/html'}});};
 const scan1=(await call(admin,{action:'runMarketScan',urls:[known]})).body.job;assert.equal(scan1.status,'completed');assert.equal(scan1.result.evidence[0].changed,null);
 const scan2=(await call(admin,{action:'runMarketScan',urls:[known]})).body.job;assert.equal(scan2.result.evidence[0].changed,false);assert.equal(scan2.result.evidence[0].admission,'staged_only');
 }finally{globalThis.fetch=originalFetch;}
});
test('settings persist requested interval but cannot claim a running background scheduler',async()=>{
 const result=await call(admin,{action:'updateSettings',settings:{scheduleEnabled:true,intervalHours:12}});assert.equal(result.status,200);assert.equal(result.body.scheduler,'manual_only');
 assert.equal((await call(admin,null,'settings')).body.settings.intervalHours,12);assert(!JSON.stringify((await call(admin,null,'settings')).body).includes(env.BEDROCK_API_KEY));
});
test('deletion removes source versions, masked and original R2 media, and contribution AI results',async()=>{
 const item=await create('screen','Must disappear');const uploaded=await uploadFile(item,'original');const fs=await DB.prepare('SELECT object_key FROM wgss_files WHERE submission_id=?').bind(item.id).all();
 const deleted=await call(alice,{action:'deleteSubmission',id:item.id,expectedVersion:uploaded.body.item.version});assert.equal(deleted.status,200);
 for(const f of fs.results)assert.equal(await BUCKET.get(f.object_key),null);
 for(const table of ['wgss_versions','wgss_files','wgss_jobs'])assert.equal((await DB.prepare(`SELECT * FROM ${table} WHERE submission_id=?`).bind(item.id).all()).results.length,0);
 const audit=(await DB.prepare('SELECT * FROM wgss_audit WHERE entity_id=?').bind(item.id).all()).results;assert.equal(audit.length,1);assert.equal(audit[0].action,'submission.deleted');assert(!JSON.stringify(audit).includes('Must disappear'));
});
test('cross-site changes are rejected before writes',async()=>{assert.equal((await call(alice,{action:'createSubmission',kind:'text',title:'forbidden'},'submissions',{Origin:'https://evil.test'})).status,403);});

test('server evidence briefs reject client material and unknown IDs, and verify exact accepted citations',async()=>{
 const index=JSON.parse(await readFile(join(root,'server/wgss/evidence-index.json'),'utf8')),ref=index.references.find(r=>r.wording.length);
 let captured,calls=0;globalThis.fetch=async(url,options)=>{calls++;captured=JSON.parse(options.body);return Response.json({choices:[{message:{content:JSON.stringify({findings:[{referenceIds:[ref.id],quote:ref.wording[0],assessment:'Advisory stage comparison'}],limitations:['Only the selected source is covered.']})},finish_reason:'stop'}],usage:{prompt_tokens:100,completion_tokens:20}});};
 try {
 assert.equal((await call(alice,{action:'runEvidenceBrief',referenceIds:[ref.id]})).status,403);
 assert.equal((await call(admin,{action:'runEvidenceBrief',referenceIds:['invented']})).status,400);assert.equal(calls,0);
 const result=await call(admin,{action:'runEvidenceBrief',referenceIds:[ref.id],content:'DO NOT SEND arbitrary private client input'});assert.equal(result.body.job.status,'completed');assert.equal(result.body.job.result.groundingValidation,'passed');assert.equal(result.body.job.result.sourceVersion,index.version);assert.equal(result.body.job.result.sourceIndexHash,await hash(JSON.stringify(index)));assert.equal(result.body.job.result.evidence[0].originalSha,ref.originalSha);assert(!JSON.stringify(captured).includes('arbitrary private client'));
 globalThis.fetch=async()=>Response.json({choices:[{message:{content:JSON.stringify({findings:[{referenceIds:['invented'],quote:'not an exact quote',assessment:'Unsupported'}],limitations:[]})},finish_reason:'stop'}]});
 const invalid=await call(admin,{action:'runEvidenceBrief',referenceIds:[ref.id],model:'claude-opus-5'});assert.equal(invalid.body.job.status,'failed');assert.equal(invalid.body.job.result.groundingValidation,'failed');assert.equal(invalid.body.job.result.parsed,null);assert.match(invalid.body.job.result.text,/Unsupported/);
 }finally{globalThis.fetch=originalFetch;}
});
test('due-job interval claims deduplicate concurrent scheduler ticks and disable cleanly',async()=>{
 const known=JSON.parse(await readFile(join(root,'server/wgss/known-sources.json'),'utf8'))[0];
 await call(admin,{action:'updateSettings',settings:{scheduleEnabled:true,intervalHours:24,sourceUrls:[known]}});
 let calls=0;globalThis.fetch=async()=>{calls++;return new Response('Official public source',{headers:{'content-type':'text/plain'}});};
 try{
 assert.equal((await call(alice,{action:'runDueJobs'})).status,403);
 const results=await Promise.all([call(admin,{action:'runDueJobs'}),call(admin,{action:'runDueJobs'}),call(admin,{action:'runDueJobs'})]);
 assert.deepEqual(results.map(r=>r.body.status).sort(),['not_due','not_due','ran']);assert.equal(calls,1);
 assert.equal((await call(admin,{action:'runDueJobs'})).body.status,'not_due');
 await call(admin,{action:'updateSettings',settings:{scheduleEnabled:false}});assert.equal((await call(admin,{action:'runDueJobs'})).body.reason,'schedule_disabled');
 }finally{globalThis.fetch=originalFetch;}
});

test('global model budget blocks over-limit egress and completed input hashes are reused',async()=>{
 const item=await approve(await create('text','Budget test wording'));
 let calls=0;globalThis.fetch=async()=>{calls++;return Response.json({choices:[{message:{content:'Budget-limited advisory'},finish_reason:'stop'}],usage:{prompt_tokens:5,completion_tokens:6}});};
 const key=`ai:quota:${new Date().toISOString().slice(0,10)}`;
 try{
 const first=await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'quality_review'});assert.equal(first.body.job.status,'completed');
 const second=await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'quality_review'});assert.equal(second.body.job.id,first.body.job.id);assert.equal(second.body.reused,true);assert.equal(calls,1);
 const previous=await DB.prepare('SELECT value_json FROM wgss_settings WHERE key=?').bind(key).first();
 await DB.prepare('UPDATE wgss_settings SET value_json=? WHERE key=?').bind('20',key).run();
 const blocked=await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'translation_review'});assert.equal(blocked.status,429);assert.equal(blocked.body.code,'ai_daily_limit');assert.equal(calls,1);
 await DB.prepare('UPDATE wgss_settings SET value_json=? WHERE key=?').bind(previous.value_json,key).run();
 }finally{globalThis.fetch=originalFetch;}
});
test('failed object purge leaves a locked retryable deletion, never an editable published shell',async()=>{
 const uploaded=(await uploadFile(await create('screen'),'original')).body.item;
 const actualDelete=env.BUCKET.delete.bind(env.BUCKET);env.BUCKET={...env.BUCKET,delete:async()=>{throw new Error('storage failure')}};
 try{const result=await call(alice,{action:'deleteSubmission',id:uploaded.id,expectedVersion:uploaded.version});assert.equal(result.status,500);const current=(await call(alice)).body.items.find(i=>i.id===uploaded.id);assert.equal(current.status,'deleting');assert.equal(current.version,uploaded.version+1);assert.equal((await call(alice,{action:'createVersion',id:uploaded.id,expectedVersion:current.version,text:'race'})).status,409);env.BUCKET=BUCKET;const retry=await call(alice,{action:'deleteSubmission',id:uploaded.id,expectedVersion:current.version});assert.equal(retry.status,200);}finally{env.BUCKET=BUCKET;}
});

test('scheduled feedback review processes one held privacy-cleared derivative, keeps publication held, and invalidates on edit',async()=>{
 const pending=await create('screen','Unreviewed private draft MUST NOT BE SENT');
 const original=(await uploadFile(await create('screen','Reviewed safe screen caption'),'original')).body.item;
 const masked=(await uploadFile(original,'masked')).body.item,file=masked.files.find(f=>f.role==='masked');
 const heldResult=await call(admin,{action:'reviewSubmission',id:masked.id,expectedVersion:masked.version,decision:'held',privacyReviewed:true,readabilityReviewed:true,maskedFileId:file.id});assert.equal(heldResult.status,200);const held=heldResult.body.item;
 await call(admin,{action:'updateSettings',settings:{scheduleEnabled:true,intervalHours:24,sourceUrls:[]}});await DB.prepare("DELETE FROM wgss_settings WHERE key='schedule:lastRun'").run();
 let calls=0,captured;globalThis.fetch=async(url,options)=>{calls++;captured=JSON.parse(options.body);return Response.json({choices:[{message:{content:'Advisory screen review; operator decision required'},finish_reason:'stop'}],usage:{prompt_tokens:40,completion_tokens:12}});};
 try{
 const tick=await call(admin,{action:'runDueJobs'});assert.equal(tick.body.status,'ran');assert.equal(tick.body.jobIds.length,1);assert.equal(tick.body.jobs[0].kind,'screen_review');assert.equal(tick.body.automaticallyPublished,false);assert.equal(calls,1);assert(!JSON.stringify(captured).includes('MUST NOT BE SENT'));
 assert.equal((await DB.prepare('SELECT status FROM wgss_submissions WHERE id=?').bind(held.id).first()).status,'held');
 await DB.prepare("DELETE FROM wgss_settings WHERE key='schedule:lastRun'").run();const again=await call(admin,{action:'runDueJobs'});assert.equal(again.body.status,'skipped');assert.equal(calls,1);
 const edited=await call(admin,{action:'createVersion',id:held.id,expectedVersion:held.version,text:'Changed source needs new privacy review'});assert.equal(edited.body.item.privacyReviewed,false);assert.equal((await call(admin,{action:'runDueJobs'})).body.status,'skipped');assert.equal(calls,1);
 }finally{globalThis.fetch=originalFetch;await call(admin,{action:'updateSettings',settings:{scheduleEnabled:false}});}
});

test.after(async()=>{globalThis.fetch=originalFetch;await miniflare.dispose();await rm(output,{recursive:true,force:true});});


test('truncated model output is retried with larger bound and both usages retained',async()=>{
 const item=await create('text','Public interface wording for retry boundary');
 const current=await call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:1,decision:'held',privacyReviewed:true,readabilityReviewed:true});
 const originalFetch=globalThis.fetch;const budgets=[];
 globalThis.fetch=async(url,options)=>{const b=JSON.parse(options.body);budgets.push(b.max_tokens);return Response.json({choices:[{message:{content:budgets.length===1?'Incomplete':'Complete advisory'},finish_reason:budgets.length===1?'length':'stop'}],usage:{prompt_tokens:10,completion_tokens:4,total_tokens:14}});};
 try{const result=await call(admin,{action:'runAiJob',submissionId:item.id,purpose:'quality_review'});assert.equal(result.body.job.status,'completed');assert.deepEqual(budgets,[1800,3600]);assert.equal(result.body.job.result.attempts.length,2);assert.equal(result.body.job.usage.total_tokens,28);assert.equal(result.body.job.result.automaticallyApplied,false);}finally{globalThis.fetch=originalFetch;}
});

test('multiple image approval checks every selected file and refuses the entire review on a bad file',async()=>{
 let item=await create('screen','Two safe synthetic screen examples');
 item=(await uploadFile(item)).body.item; item=(await uploadFile(item)).body.item;
 const ids=item.files.map(f=>f.id);
 const invalid=await call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,maskedFileIds:[ids[0],'missing-file']});
 assert.equal(invalid.status,400);
 let records=(await call(alice)).body.items.find(r=>r.id===item.id);
 assert.equal(records.version,item.version);assert.ok(records.files.every(f=>f.reviewStatus==='pending'));
 const approved=await approve(item,{maskedFileIds:ids});assert.ok(approved.files.every(f=>f.reviewStatus==='approved'));
 const published=(await call(bob,null,'published')).body.items.find(r=>r.id===item.id);assert.equal(published.files.length,2);
 const revised=await call(admin,{action:'createVersion',id:item.id,expectedVersion:approved.version,text:'Changed the source description'});
 assert.ok(revised.body.item.files.every(f=>f.reviewStatus==='pending'));
});

test('retrying a completed image upload does not create a duplicate file or revision',async()=>{
 const item=await create('screen'),clientId=crypto.randomUUID();
 async function retry(role='masked') {const form=new FormData();form.set('action','upload');form.set('submissionId',item.id);form.set('role',role);form.set('clientUploadId',clientId);form.set('file',new File([png],'local-only.png',{type:'image/png'}));const response=await handleRequest(new Request('https://workspace.test/api/wgss',{method:'POST',body:form}),env,alice);return {status:response.status,body:await response.json()};}
 const first=await retry();assert.equal(first.status,200);
 const repeated=await retry();assert.equal(repeated.status,200);assert.equal(repeated.body.reused,true);assert.equal(repeated.body.item.files.length,1);assert.equal(repeated.body.item.version,first.body.item.version);
 assert.equal((await retry('original')).status,409);
 const response=await handleRequest(new Request('https://workspace.test/api/wgss?resource=file&id='+clientId),env,alice);assert.equal(response.status,200);assert.deepEqual(new Uint8Array(await response.arrayBuffer()),png);
});

test('approval requires a typed destination and cannot mutate source on a validation failure',async()=>{
 const item=await create();
 const payload={action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true};
 assert.equal((await call(admin,payload)).status,400);
 for(const application of [
  {type:'phrases',operation:'update',targetId:'missing',expectedRevision:0,fields:{text:'Changed'}},
  {type:'phrases',operation:'add',expectedRevision:0,fields:{text:'Changed',providerId:'imaginary',language:'en',taskId:'signup'}},
  {type:'terms',operation:'add',expectedRevision:0,fields:{english:'Test',target:'Test',language:'en',generationEligible:true}},
  {type:'phrases',operation:'add',expectedRevision:0,fields:{text:'Changed',providerId:'citi',language:'en',taskId:'signup',sourceUrl:'javascript:alert(1)'}}
 ])assert.equal((await call(admin,{...payload,application})).status,400);
 const stored=(await call(alice)).body.items.find(r=>r.id===item.id);assert.equal(stored.status,'pending');assert.equal(stored.version,item.version);
});

test('different submissions editing the same record are atomic and stale target revisions cannot win',async()=>{
 const index=JSON.parse(await readFile(join(root,'server/wgss/reference-index.json'))),target=index.phrases[0];
 const a=await create(),b=await create();
 const application={type:'phrases',operation:'update',targetId:target.id,expectedRevision:0,fields:{text:'Reviewed label change'},imageFileIds:[]};
 const review=item=>call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,application});
 const responses=await Promise.all([review(a),review(b)]);assert.deepEqual(responses.map(r=>r.status).sort(),[200,409]);
 let applied=(await call(bob,null,'publications')).body.items.find(r=>r.targetId===target.id);assert.equal(applied.patch.text,'Reviewed label change');assert.equal(applied.revision,1);assert.equal(applied.patch.id,undefined);
 const winner=responses.find(r=>r.status===200).body.item,loser=responses[0].status===200?b:a;
 assert.equal((await call(alice)).body.items.find(r=>r.id===loser.id).status,'pending');
 assert.equal((await call(alice,null,`resource=publicationHistory&type=phrases&id=${target.id}`)).status,403);
 assert.equal((await call(admin,null,`resource=publicationHistory&type=phrases&id=${target.id}`)).body.items.length,1);
 assert.equal((await call(admin,{action:'createVersion',id:winner.id,expectedVersion:winner.version,text:'Further proposed change'})).status,200);
 applied=(await call(bob,null,'publications')).body.items.find(r=>r.targetId===target.id);assert.equal(applied.patch.text,'Reviewed label change');
 const stored=(await call(admin)).body.items.find(r=>r.id===winner.id);
 assert.equal((await call(admin,{action:'deleteSubmission',id:winner.id,expectedVersion:stored.version})).status,200);
 applied=(await call(bob,null,'publications')).body.items.find(r=>r.targetId===target.id);assert.deepEqual(applied.patch,{});assert.equal(applied.revision,1);
 assert.equal((await review(loser)).status,409);
 const next=await call(admin,{action:'reviewSubmission',id:loser.id,expectedVersion:loser.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,application:{...application,expectedRevision:1}});assert.equal(next.status,200);
});

test('multiple approved photos become actual screen records and survive a pending revision without exposing originals',async()=>{
 let item=await create('screen');item=(await uploadFile(item,'original')).body.item;item=(await uploadFile(item)).body.item;item=(await uploadFile(item)).body.item;
 const photos=item.files.filter(r=>r.role==='masked').map(r=>r.id),original=item.files.find(r=>r.role==='original');
 const approved=await approve(item,{maskedFileIds:photos});
 let applied=(await call(bob,null,'publications')).body.items.filter(r=>r.type==='screens'&&r.targetId.includes(item.id));
 assert.equal(applied.length,2);assert.deepEqual(applied.map(r=>r.patch.imageFileId).sort(),photos.sort());assert.ok(applied.every(r=>r.patch.flowId===null&&r.patch.collectedAt===null));
 assert.equal((await call(admin,{action:'createVersion',id:item.id,expectedVersion:approved.version,text:'Pending next version'})).status,200);
 for(const fid of photos)assert.equal((await handleRequest(new Request(`https://workspace.test/api/wgss?resource=file&id=${fid}`),env,bob)).status,200);
 assert.equal((await handleRequest(new Request(`https://workspace.test/api/wgss?resource=file&id=${original.id}`),env,bob)).status,403);
 const current=(await call(admin)).body.items.find(r=>r.id===item.id);assert.equal((await call(admin,{action:'deleteSubmission',id:item.id,expectedVersion:current.version})).status,200);
 applied=(await call(bob,null,'publications')).body.items.filter(r=>r.targetId.includes(item.id));assert.ok(applied.every(r=>Object.keys(r.patch).length===0));
 assert.equal((await call(admin,null,'resource=targets&type=screens&q='+encodeURIComponent(item.id))).body.items.length,0);
 for(const fid of photos)assert.equal((await handleRequest(new Request(`https://workspace.test/api/wgss?resource=file&id=${fid}`),env,bob)).status,404);
});

test('term corrections preserve identity and rights; new terms remain separate from expert approval',async()=>{
 const index=JSON.parse(await readFile(join(root,'server/wgss/reference-index.json'))),term=index.terms[0],item=await create('translation_issue');
 const base={action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true};
 const application={type:'terms',operation:'update',targetId:term.id,expectedRevision:0,fields:{target:'Reviewed synthetic correction'},imageFileIds:[]};
 assert.equal((await call(admin,{...base,application:{...application,fields:{english:'Change identity'}}})).status,400);
 const approved=await call(admin,{...base,application});assert.equal(approved.status,200);
 const patch=(await call(bob,null,'publications')).body.items.find(r=>r.type==='terms'&&r.targetId===term.id).patch;assert.equal(patch.target,'Reviewed synthetic correction');assert.equal(patch.generationEligible,undefined);assert.equal(patch.license,undefined);
 const added=await create('translation_issue');await approve(added,{application:{type:'terms',operation:'add',expectedRevision:0,imageFileIds:[],fields:{english:'Synthetic term',target:'Synthetic target',language:'en'}}});
 const community=(await call(bob,null,'publications')).body.items.find(r=>r.type==='terms'&&r.targetId.includes(added.id)).patch;assert.equal(community.generationEligible,false);assert.equal(community.approvedTranslation,null);assert.equal(community.layer,'community');
});

test('company features need a known work and evidence rather than the submitted description',async()=>{
 const index=JSON.parse(await readFile(join(root,'server/wgss/reference-index.json'))),item=await create();
 const application={type:'features',operation:'add',expectedRevision:0,imageFileIds:[],fields:{expression:'Synthetic feature',providerId:'citi',language:'en',workId:index.works[0].id}};
 const payload={action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,application};
 assert.equal((await call(admin,payload)).status,400);
 const result=await call(admin,{...payload,application:{...application,fields:{...application.fields,sourceUrl:'https://example.com/synthetic-source'}}});assert.equal(result.status,200);
 const entry=(await call(bob,null,'publications')).body.items.find(r=>r.type==='features'&&r.targetId.includes(item.id));assert.equal(entry.patch.expression,'Synthetic feature');assert.equal(entry.patch.meaning,undefined);assert.equal(entry.patch.evidence[0].url,'https://example.com/synthetic-source');assert.equal(entry.patch.observedAppScreen,false);
});

test('screen replacement preserves an approved version without inheriting old image observations',async()=>{
 const index=JSON.parse(await readFile(join(root,'server/wgss/reference-index.json'))),target=index.screens[0];
 let item=await create('screen');item=(await uploadFile(item)).body.item;const fid=item.files[0].id;
 const application={type:'screens',operation:'update',targetId:target.id,expectedRevision:0,imageFileIds:[fid],fields:{title:'Synthetic latest screenshot'}};
 await approve(item,{maskedFileIds:[fid],application});
 const entry=(await call(bob,null,'publications')).body.items.find(r=>r.type==='screens'&&r.targetId===target.id);assert.equal(entry.patch.imageFileId,fid);assert.equal(entry.patch.title,'Synthetic latest screenshot');assert.equal(entry.patch.flowId,null);assert.equal(entry.patch.collectedAt,null);assert.equal(entry.patch.purpose,'unknown');assert.equal(entry.patch.currentUiVersionVerified,false);assert.deepEqual(entry.patch.phraseIds,[]);
 const history=await call(bob,null,`resource=recordVersions&type=screens&id=${encodeURIComponent(target.id)}`);assert.equal(history.status,200);assert.equal(history.body.items.length,1);assert.equal(history.body.items[0].fields.imageFileId,fid);assert.equal(history.body.items[0].ownerId,undefined);
 assert.equal((await call(anonymous,null,`resource=recordVersions&type=screens&id=${encodeURIComponent(target.id)}`)).status,401);
});
test('held and rejected proposals never change practitioner records',async()=>{
 for(const decision of ['held','rejected']){const item=await create();const result=await call(admin,{action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision,reason:'Not ready to apply'});assert.equal(result.status,200);assert.ok(!(await call(bob,null,'publications')).body.items.some(r=>r.targetId.includes(item.id)));}
});
