import test,{after,beforeEach} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,copyFile,mkdir,rm,readdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {createRequire} from 'node:module';
import ts from 'typescript';
import {Miniflare} from 'miniflare';

const root=resolve(import.meta.dirname,'../..'),output=await mkdtemp(join(tmpdir(),'wgss-intake-'));
await mkdir(join(output,'wgss'));
for(const name of ['core','submissions','jobs','images','publications','api'])await writeFile(join(output,'wgss',name+'.js'),ts.transpileModule(await readFile(join(root,'server/wgss',name+'.ts'),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,esModuleInterop:true,resolveJsonModule:true}}).outputText);
for(const name of ['known-sources.json','evidence-index.json','reference-index.json'])await copyFile(join(root,'server/wgss',name),join(output,'wgss',name));
await writeFile(join(output,'intake.js'),ts.transpileModule(await readFile(join(root,'server/intake.ts'),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,esModuleInterop:true,resolveJsonModule:true}}).outputText);
const require=createRequire(import.meta.url),{handleIntake}=require(join(output,'intake.js')),{hash}=require(join(output,'wgss/core.js'));
const miniflare=new Miniflare({modules:true,script:'export default { fetch(){return new Response("test")} }',compatibilityDate:'2026-05-15',d1Databases:{DB:'wgss-intake-test'},r2Buckets:['BUCKET']});
const DB=await miniflare.getD1Database('DB'),BUCKET=await miniflare.getR2Bucket('BUCKET');
for(const file of (await readdir(join(root,'drizzle'))).filter(f=>f.endsWith('.sql')).sort())for(const sql of (await readFile(join(root,'drizzle',file),'utf8')).split('--> statement-breakpoint'))if(sql.trim())await DB.prepare(sql.trim()).run();
await DB.prepare('CREATE TABLE IF NOT EXISTS wgss_intake_quota (id TEXT PRIMARY KEY NOT NULL,used INTEGER NOT NULL,"limit" INTEGER NOT NULL,updated_at TEXT NOT NULL)').run();
const env={DB,BUCKET,WGSS_ADMIN_EMAILS:'owner@example.test',WGSS_PRIVATE_SERVICE_ACCESS:'true'}; // Intake must override this unsafe legacy flag.
const base='https://intake.test/api/wgss',frontend='https://simsoni7.github.io',adminHeaders={'oai-authenticated-user-id':'owner-user','oai-authenticated-user-email':'owner@example.test'};
const token=()=>crypto.getRandomValues(new Uint8Array(32)).reduce((str,n)=>str+n.toString(16).padStart(2,'0'),'');
const png=Uint8Array.from(Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a3ioAAAAASUVORK5CYII=','base64'));
async function request(cap,body=null,resource='session',headers={}){const r=await handleIntake(new Request(base+'?'+(resource.includes('=')?resource:'resource='+resource),{method:body===null?'GET':'POST',headers:{Origin:frontend,...(cap?{'X-WGSS-Contribution-Token':cap}:{}),...(body===null?{}:{'Content-Type':'application/json'}),...headers},...(body===null?{}:{body:JSON.stringify(body)})}),env);return {status:r.status,headers:r.headers,body:await r.json()};}
async function create(cap=token(),more={},headers={}){const r=await request(cap,{action:'createSubmission',kind:'screen',title:'Test source',text:'A customer screen',sourceUrl:'https://bank.example/signup',privacyConfirmed:true,...more},'session',headers);assert.equal(r.status,200,JSON.stringify(r.body));return {cap,item:r.body.item};}
async function upload({cap,item},uploadId=crypto.randomUUID(),data=png,role='masked'){const form=new FormData();for(const [key,value]of Object.entries({action:'upload',submissionId:item.id,role,clientUploadId:uploadId}))form.set(key,value);form.set('file',new File([data],'untrusted-customer-name.png',{type:'image/png'}));const r=await handleIntake(new Request(base,{method:'POST',headers:{Origin:frontend,'X-WGSS-Contribution-Token':cap},body:form}),env);return {status:r.status,body:await r.json()};}
beforeEach(async()=>{await DB.prepare('DELETE FROM wgss_intake_quota').run();});

test('CORS allows GitHub and same host, rejects unrelated origins and preflights',async()=>{
 const options=await handleIntake(new Request(base,{method:'OPTIONS',headers:{Origin:frontend,'Access-Control-Request-Headers':'content-type,x-wgss-contribution-token'}}),env);assert.equal(options.status,204);assert.equal(options.headers.get('access-control-allow-origin'),frontend);assert(!options.headers.has('access-control-allow-credentials'));assert(options.headers.get('access-control-allow-headers').includes('X-WGSS-Contribution-Token'));
 const bad=await request(null,null,'session',{Origin:'https://evil.example'});assert.equal(bad.status,403);assert(!bad.headers.has('access-control-allow-origin'));
 assert.equal((await request(null,null,'session',{Origin:'https://intake.test'})).status,200);
});
test('capability is a 256-bit header, shared admin keys and private-service flag grant no privileges',async()=>{
 const session=await request();assert.equal(session.body.role,'anonymous');assert.equal(session.body.serviceAccess,false);
 for(const cap of [null,'x','a'.repeat(63),'g'.repeat(64),'A'.repeat(64)])assert.equal((await request(cap,{action:'createSubmission',privacyConfirmed:true})).status,401);
 assert.equal((await request(null,null,'jobs',{'X-WGSS-Admin-Key':'guess'})).status,403);
 assert.equal((await request(token(),{action:'reviewSubmission'})).status,403);
 for(const action of ['runAiJob','runDueJobs','updateSettings','createVersion','saveComparison'])assert.equal((await request(token(),{action})).status,403);
 assert.equal((await request(null,null,'jobs',adminHeaders)).status,200);
});
test('privacy acknowledgment is required and create retries are atomically idempotent',async()=>{
 assert.equal((await request(token(),{action:'createSubmission',kind:'screen',title:'No consent'})).status,400);
 const cap=token(),body={action:'createSubmission',kind:'screen',title:'Retry source',privacyConfirmed:true};
 const results=await Promise.all([request(cap,body),request(cap,body)]);assert(results.every(r=>r.status===200),JSON.stringify(results));assert.equal(results[0].body.item.id,results[1].body.item.id);
 const row=await DB.prepare('SELECT COUNT(*) AS count FROM wgss_submissions WHERE owner_id=?').bind('contribution:'+await hash(cap)).first();assert.equal(row.count,1);
 const quota=await DB.prepare("SELECT used FROM wgss_intake_quota WHERE id LIKE 'create:global:%'").first();assert.equal(quota.used,1);
 const replay=await request(cap,{...body,title:'Do not overwrite'});assert.equal(replay.body.reused,true);assert.equal(replay.body.item.title,'Retry source');assert(!JSON.stringify(replay.body).includes(cap));
});
test('contributors see only their own queue and cannot alter somebody else’s proposal',async()=>{
 const a=await create(),b=await create();const own=await request(a.cap,null,'submissions');assert(own.body.items.some(i=>i.id===a.item.id));assert(!own.body.items.some(i=>i.id===b.item.id));
 assert.equal((await request(a.cap,{action:'deleteOwn',id:b.item.id,expectedVersion:1})).status,403);
 for(const resource of ['submissions','published','versions','targets','publicationHistory','audit','settings','sources'])assert.equal((await request(null,null,resource)).status,resource==='submissions'?401:403);
});
test('masked photos retain exact SHA and upload retries do not duplicate storage or daily quota',async()=>{
 const item=await create(),firstId=crypto.randomUUID(),first=await upload(item,firstId);assert.equal(first.status,200,JSON.stringify(first.body));assert.equal(first.body.item.files[0].sha256,await hash(png));
 const replay=await upload(item,firstId);assert.equal(replay.status,200);assert.equal(replay.body.reused,true);assert.equal(replay.body.item.files.length,1);
 const second=await upload({cap:item.cap,item:first.body.item});assert.equal(second.status,200);assert.equal(second.body.item.files.length,2);
 const quota=await DB.prepare("SELECT used FROM wgss_intake_quota WHERE id LIKE 'upload:global:%'").first();assert.equal(quota.used,png.length*2);
 const row=await DB.prepare('SELECT object_key FROM wgss_files WHERE id=?').bind(firstId).first();assert(!row.object_key.includes('untrusted'));assert.deepEqual(new Uint8Array(await (await BUCKET.get(row.object_key)).arrayBuffer()),png);
 const changed=Uint8Array.from(png);changed[changed.length-1]^=1;assert.equal((await upload(item,firstId,changed)).status,409);
});
test('raw uploads are blocked; unapproved masked files are private except to their owner capability',async()=>{
 const a=await create();assert.equal((await upload(a,crypto.randomUUID(),png,'original')).status,403);const uploaded=await upload(a),fid=uploaded.body.item.files[0].id;
 const file=await handleIntake(new Request(base+'?resource=file&id='+fid,{headers:{Origin:frontend}}),env);assert.equal(file.status,403);
 const stranger=await handleIntake(new Request(base+'?resource=file&id='+fid,{headers:{Origin:frontend,'X-WGSS-Contribution-Token':token()}}),env);assert.equal(stranger.status,403);
 const owner=await handleIntake(new Request(base+'?resource=file&id='+fid,{headers:{Origin:frontend,'X-WGSS-Contribution-Token':a.cap}}),env);assert.equal(owner.status,200);
 const bad=await upload(a,crypto.randomUUID(),new TextEncoder().encode('<svg>not a PNG image</svg>'));assert.equal(bad.status,415);
});
test('IP/hour and global/day create limits fail atomically without charging failed submissions',async()=>{
 for(let n=0;n<10;n++)await create();assert.equal((await request(token(),{action:'createSubmission',kind:'text',title:'Blocked',privacyConfirmed:true})).status,429);
 assert.equal((await DB.prepare("SELECT used FROM wgss_intake_quota WHERE id LIKE 'create:global:%'").first()).used,10);
 await DB.prepare("UPDATE wgss_intake_quota SET used=100 WHERE id LIKE 'create:global:%'").run();assert.equal((await request(token(),{action:'createSubmission',kind:'text',title:'Global blocked',privacyConfirmed:true},'session',{'CF-Connecting-IP':'192.0.2.12'})).status,429);
});
test('upload byte limits and daily quota reject excess bytes and leave no stored photo',async()=>{
 const a=await create(),day=new Date().toISOString().slice(0,10);await DB.prepare('INSERT INTO wgss_intake_quota (id,used,"limit",updated_at) VALUES (?,?,?,?)').bind('upload:global:'+day,500*1024*1024,500*1024*1024,new Date().toISOString()).run();assert.equal((await upload(a)).status,429);
 assert.equal((await request(a.cap,null,'submissions')).body.items.find(i=>i.id===a.item.id).files.length,0);
 const large=await handleIntake(new Request(base,{method:'POST',headers:{Origin:frontend,'X-WGSS-Contribution-Token':a.cap,'Content-Type':'application/json','Content-Length':'64001'},body:'{}'}),env);assert.equal(large.status,413);
});
test('admin review exposes only approved records/photos, and contributors cannot cancel approved references',async()=>{
 const a=await create(),image=await upload(a),item=image.body.item,fid=item.files[0].id;
 const approved=await request(null,{action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,maskedFileIds:[fid],application:{type:'screens',operation:'add',expectedRevision:0,imageFileIds:[fid],fields:{title:'Public approved capture',providerId:'citi',language:'en',taskId:'signup'}}},'session',adminHeaders);assert.equal(approved.status,200,JSON.stringify(approved.body));
 const publicRows=await request(null,null,'publications');const row=publicRows.body.items.find(r=>r.patch.title==='Public approved capture');assert(row);assert(!JSON.stringify(publicRows.body).includes('ownerId'));assert(!JSON.stringify(publicRows.body).includes('source_submission_id'));
 const photo=await handleIntake(new Request(base+'?resource=file&id='+fid),env);assert.equal(photo.status,200);assert.deepEqual(new Uint8Array(await photo.arrayBuffer()),png);
 assert.equal((await request(a.cap,{action:'deleteOwn',id:item.id,expectedVersion:approved.body.item.version})).status,403);
 const versions=await request(null,null,'resource=recordVersions&type=screens&id='+encodeURIComponent(row.targetId));assert.equal(versions.status,200);assert.equal(versions.body.items.length,1);
});
test('only existing commercially permitted terms can appear in public overlays or histories',async()=>{
 const index=JSON.parse(await readFile(join(root,'server/wgss/reference-index.json'),'utf8')),allowed=index.terms.find(r=>r.datasetId==='apache_ofbiz_accounting');assert(allowed,'reference-index terms must retain datasetId for the fail-closed allowlist');
 const source=await create(token(),{kind:'text'});
 for(const [targetId,patch]of [[allowed.id,{target:'allowed-public'}],['mongolbank:fake',{target:'forbidden-commercial'}],['contribution:terms:community',{id:'contribution:terms:community',datasetId:'wgss-community',target:'forbidden-community'}]])await DB.prepare("INSERT INTO wgss_publications (id,target_type,target_id,revision,source_submission_id,source_version,patch_json,state,actor_id,created_at) VALUES (?,'terms',?,1,?,1,?,'applied','admin',?)").bind(crypto.randomUUID(),targetId,source.item.id,JSON.stringify(patch),new Date().toISOString()).run();
 const pub=await request(null,null,'publications');assert(pub.body.items.some(r=>r.targetId===allowed.id));assert(!pub.body.items.some(r=>r.targetId==='mongolbank:fake'||r.targetId==='contribution:terms:community'));
 assert.equal((await request(null,null,'resource=recordVersions&type=terms&id=mongolbank:fake')).status,404);
 const admin=await request(null,null,'publications',adminHeaders);assert(admin.body.items.some(r=>r.targetId==='contribution:terms:community'));
});
test('pending proposal cancellation purges files and publications through the existing deletion path',async()=>{
 const a=await create(),uploaded=await upload(a),item=uploaded.body.item,fid=item.files[0].id;
 const result=await request(a.cap,{action:'deleteOwn',id:item.id,expectedVersion:item.version});assert.equal(result.status,200,JSON.stringify(result.body));assert.equal(result.body.deleted,true);
 assert.equal(await DB.prepare('SELECT id FROM wgss_files WHERE id=?').bind(fid).first(),null);assert.equal(await DB.prepare('SELECT id FROM wgss_submissions WHERE id=?').bind(item.id).first(),null);
});
test('a review that wins the cancellation race cannot have its approved reference erased',async()=>{
 const a=await create(token(),{kind:'text'});let raced=false;
 const racingDB={batch:DB.batch.bind(DB),prepare(sql){const prepared=DB.prepare(sql);return {bind(...args){const bound=prepared.bind(...args);return {all:bound.all.bind(bound),run:bound.run.bind(bound),async first(){const snapshot=await bound.first();if(!raced&&sql==='SELECT * FROM wgss_submissions WHERE id=?'&&args[0]===a.item.id){raced=true;const result=await request(null,{action:'reviewSubmission',id:a.item.id,expectedVersion:1,decision:'approved',privacyReviewed:true,readabilityReviewed:true,application:{type:'phrases',operation:'add',expectedRevision:0,fields:{text:'Approved in the race',providerId:'citi',language:'en',taskId:'signup'}}},'session',adminHeaders);assert.equal(result.status,200,JSON.stringify(result.body));}return snapshot;}};}};}};
 const result=await handleIntake(new Request(base,{method:'POST',headers:{Origin:frontend,'Content-Type':'application/json','X-WGSS-Contribution-Token':a.cap},body:JSON.stringify({action:'deleteOwn',id:a.item.id,expectedVersion:1})}),{...env,DB:racingDB});assert.equal(result.status,409);
 assert.equal((await DB.prepare('SELECT status FROM wgss_submissions WHERE id=?').bind(a.item.id).first()).status,'approved');
 const pub=await request(null,null,'publications');assert(pub.body.items.some(row=>row.patch.text==='Approved in the race'));
});
test('simultaneous retries of the same photo converge on one file and one byte charge',async()=>{
 const a=await create(),fid=crypto.randomUUID(),out=await Promise.all([upload(a,fid),upload(a,fid)]);assert(out.every(r=>r.status===200),JSON.stringify(out));
 assert.equal((await DB.prepare('SELECT COUNT(*) AS count FROM wgss_files WHERE id=?').bind(fid).first()).count,1);
 const amount=await DB.prepare("SELECT used FROM wgss_intake_quota WHERE id LIKE 'upload:global:%'").first();assert.equal(amount.used,png.length);
});
test('collection contributions append new screens with a verified anchor and never replace the existing screen',async()=>{
 const anchor='toss-v6:TOSS-019',a=await create(token(),{collectionReferenceId:anchor,referenceId:'',provider:'toss-service',language:'ko',task:'signup'});assert.equal(a.item.current.collectionReferenceId,anchor);
 const image=await upload(a),item=image.body.item,fid=item.files[0].id,review={action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,maskedFileIds:[fid],application:{type:'screens',operation:'add',expectedRevision:0,imageFileIds:[fid],fields:{title:'Another supplied Toss capture',providerId:'toss-service',language:'ko',taskId:'signup'}}};
 const replace=await request(null,{...review,application:{...review.application,operation:'update',targetId:anchor}},'session',adminHeaders);assert.equal(replace.status,400);assert.equal(replace.body.code,'collection_add_only');
 const wrongCompany=await request(null,{...review,application:{...review.application,fields:{...review.application.fields,providerId:'citi'}}},'session',adminHeaders);assert.equal(wrongCompany.status,400);assert.equal(wrongCompany.body.code,'collection_provider');
 const approved=await request(null,review,'session',adminHeaders);assert.equal(approved.status,200,JSON.stringify(approved.body));
 const pub=await request(null,null,'publications'),added=pub.body.items.find(row=>row.patch.title==='Another supplied Toss capture');assert(added);assert.notEqual(added.targetId,anchor);assert.equal(added.patch.collectionReferenceId,anchor);assert.equal(added.patch.cohort,'contribution');assert.equal(added.patch.collectionId,'submission:'+item.id);
 assert(!pub.body.items.some(row=>row.targetId===anchor));
});
test('unknown collection anchors fail review without publishing or changing source status',async()=>{
 const a=await create(token(),{collectionReferenceId:'missing-screen'}),image=await upload(a),item=image.body.item,fid=item.files[0].id;
 const reviewed=await request(null,{action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,maskedFileIds:[fid],application:{type:'screens',operation:'add',expectedRevision:0,imageFileIds:[fid],fields:{title:'Unverified collection',providerId:'citi',language:'en',taskId:'signup'}}},'session',adminHeaders);assert.equal(reviewed.status,400);assert.equal(reviewed.body.code,'unknown_collection');
 assert.equal((await DB.prepare('SELECT status FROM wgss_submissions WHERE id=?').bind(item.id).first()).status,'pending');
});
after(async()=>{await miniflare.dispose();await rm(output,{recursive:true,force:true});});
