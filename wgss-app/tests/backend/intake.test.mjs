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
for(const name of ['core','submissions','jobs','images','publications','review-draft','vision-images','api'])await writeFile(join(output,'wgss',name+'.js'),ts.transpileModule(await readFile(join(root,'server/wgss',name+'.ts'),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,esModuleInterop:true,resolveJsonModule:true}}).outputText);
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
 assert.equal((await request(null,null,'session',{Origin:'https://intake.test'})).status,200);assert.equal((await request(null,null,'session',{Origin:'https://wgss-case-library.booknfoto461.chatgpt.site'})).status,200);
});

test('CORS accepts explicitly configured HTTPS frontends only',async()=>{
 const configured={...env,WGSS_PUBLIC_FRONTEND_ORIGINS:'https://3.36.58.188,http://insecure.example, https://bad.example/path'};
 for(const [origin,expected] of [['https://3.36.58.188',204],['http://3.36.58.188',403],['https://bad.example',403],['http://insecure.example',403]]){const r=await handleIntake(new Request(base,{method:'OPTIONS',headers:{Origin:origin}}),configured);assert.equal(r.status,expected);assert.equal(r.headers.get('access-control-allow-origin'),expected===204?origin:null);}
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
test('new term proposals preserve prefilled expressions and require administrator rights review before public posting',async()=>{
 const proposal=await create(token(),{kind:'translation_issue',proposalType:'term',termEnglish:'Account opening',termKorean:'계좌 개설',termTarget:'Opening an account',language:'en',workId:'test-work',sourceUrl:'https://example.org/terms'});
 assert.equal(proposal.item.current.proposalType,'term');assert.equal(proposal.item.current.termEnglish,'Account opening');assert.equal(proposal.item.current.termKorean,'계좌 개설');assert.equal(proposal.item.current.workId,'test-work');
 const application={type:'terms',operation:'add',expectedRevision:0,imageFileIds:[],fields:{english:'Account opening',korean:'계좌 개설',target:'Opening an account',language:'en',sourceUrl:'https://example.org/terms'}};
 const review={action:'reviewSubmission',id:proposal.item.id,expectedVersion:1,decision:'approved',privacyReviewed:true,readabilityReviewed:true,application};
 const missing=await request(null,review,'session',adminHeaders);assert.equal(missing.status,400);assert.equal(missing.body.code,'commercial_review_required');
 assert.equal((await DB.prepare('SELECT status FROM wgss_submissions WHERE id=?').bind(proposal.item.id).first()).status,'pending');
 const rights={confirmed:true,license:'CC0-1.0',evidenceUrl:'https://example.org/license',basis:'The contributor dedicated this original synthetic example under CC0.'};
 const invalid=await request(null,{...review,application:{...application,commercialRights:{...rights,license:'unknown'}}},'session',adminHeaders);assert.equal(invalid.status,400);
 const contributor=await request(proposal.cap,{...review,application:{...application,commercialRights:rights}});assert.equal(contributor.status,403);
 const approved=await request(null,{...review,application:{...application,commercialRights:rights}},'session',adminHeaders);assert.equal(approved.status,200,JSON.stringify(approved.body));
 const publicList=await request(null,null,'publications'),row=publicList.body.items.find(r=>r.targetId==='contribution:terms:'+proposal.item.id);assert(row);assert.equal(row.patch.datasetId,'wgss_reviewed_terms');assert.equal(row.patch.generationEligible,false);assert.equal(row.patch.commercialRights.reviewedBy,undefined);assert.match(row.patch.commercialRights.reviewSha,/^[0-9a-f]{64}$/);
 const history=await request(null,null,'resource=recordVersions&type=terms&id='+encodeURIComponent(row.targetId));assert.equal(history.status,200);assert.equal(history.body.items.length,1);assert.equal(history.body.items[0].fields.commercialRights.reviewedBy,undefined);
 const adminList=await request(null,null,'publications',adminHeaders),stored=adminList.body.items.find(r=>r.targetId===row.targetId);assert.equal(stored.patch.commercialRights.reviewedBy,'owner-user');
 const follow=await create(token(),{kind:'translation_issue',referenceId:row.targetId}),update={...review,id:follow.item.id,expectedVersion:1,application:{type:'terms',operation:'update',targetId:row.targetId,expectedRevision:1,imageFileIds:[],fields:{target:'Open an account'}}};
 assert.equal((await request(null,update,'session',adminHeaders)).body.code,'commercial_review_required');
 const updated=await request(null,{...update,application:{...update.application,commercialRights:rights}},'session',adminHeaders);assert.equal(updated.status,200,JSON.stringify(updated.body));
 const versions=await request(null,null,'resource=recordVersions&type=terms&id='+encodeURIComponent(row.targetId));assert.equal(versions.body.items.length,2);
});
after(async()=>{await miniflare.dispose();await rm(output,{recursive:true,force:true});});
async function publicReview(body=null,resource='session',headers={},moreEnv={}){const response=await handleIntake(new Request(base+'?'+(resource.includes('=')?resource:'resource='+resource),{method:body===null?'GET':'POST',headers:{Origin:frontend,...(body===null?{}:{'Content-Type':'application/json'}),...headers},...(body===null?{}:{body:JSON.stringify(body)})}),{...env,WGSS_PUBLIC_REVIEW:'true',...moreEnv});return {status:response.status,body:await response.json(),headers:response.headers};}
test('explicit public review provides shared review session and queue without exposing private originals or global controls',async()=>{
 const a=await create(),uploaded=await upload(a),fid=uploaded.body.item.files[0].id;const originalId=crypto.randomUUID(),originalKey='original/'+originalId;await BUCKET.put(originalKey,png);await DB.prepare('INSERT INTO wgss_files (id,submission_id,object_key,sha256,mime,size,role,review_status,created_at) VALUES (?,?,?,?,?,?,?,?,?)').bind(originalId,a.item.id,originalKey,await hash(png),'image/png',png.length,'original','pending',new Date().toISOString()).run();
 assert.equal((await request()).body.role,'anonymous');const session=await publicReview(null,'session',{'CF-Connecting-IP':'192.0.2.42'});assert.equal(session.status,200);assert.equal(session.body.role,'admin');assert.equal(session.body.publicReview,true);assert(session.body.userId.startsWith('public-reviewer:'));assert(!JSON.stringify(session.body).includes('192.0.2.42'));assert.deepEqual(session.body.reviewActions,['prepareReviewDraft','reviewSubmission','createVersion']);
 const queue=await publicReview(null,'submissions');assert.equal(queue.status,200);const row=queue.body.items.find(s=>s.id===a.item.id);assert(row);assert(!Object.hasOwn(row,'ownerId'));assert.deepEqual(row.files.map(f=>f.id),[fid]);
 for(const resource of ['versions&id='+a.item.id,'audit','targets&type=screens&q=Citi','reviewDraft&id='+a.item.id])assert.equal((await publicReview(null,'resource='+resource)).status,200,resource);
 const masked=await handleIntake(new Request(base+'?resource=file&id='+fid),{...env,WGSS_PUBLIC_REVIEW:'true'});assert.equal(masked.status,200);assert.deepEqual(new Uint8Array(await masked.arrayBuffer()),png);const raw=await publicReview(null,'resource=file&id='+originalId);assert.equal(raw.status,403);assert.equal(raw.body.code,'masked_only');
 for(const resource of ['settings','jobs','sources','comparisons'])assert.equal((await publicReview(null,resource)).status,403,resource);
 for(const action of ['updateSettings','runMarketScan','runDueJobs','runAiJob','runEvidenceBrief','saveComparison','deleteComparison'])assert.equal((await publicReview({action})).status,403,action);
 const ownedDelete=await publicReview({action:'deleteSubmission',id:a.item.id,expectedVersion:uploaded.body.item.version});assert.equal(ownedDelete.status,401);assert(await DB.prepare('SELECT id FROM wgss_submissions WHERE id=?').bind(a.item.id).first());
});
test('public curation can approve and publish an exact masked screen with optimistic version checks and hashed audit identity',async()=>{
 const a=await create(),uploaded=await upload(a),item=uploaded.body.item,fid=item.files[0].id;
 const input={action:'reviewSubmission',id:item.id,expectedVersion:item.version,decision:'approved',privacyReviewed:true,readabilityReviewed:true,maskedFileIds:[fid],application:{type:'screens',operation:'add',expectedRevision:0,imageFileIds:[fid],fields:{title:'Public collaborative review',providerId:'citi',language:'en',taskId:'signup'}}};
 const result=await publicReview(input,'session',{'CF-Connecting-IP':'198.51.100.7'});assert.equal(result.status,200,JSON.stringify(result.body));assert.equal(result.body.item.status,'approved');
 assert.equal((await publicReview(input)).status,409);const rows=await request(null,null,'publications');const published=rows.body.items.find(row=>row.patch.title==='Public collaborative review');assert(published);const audit=await publicReview(null,'audit');const review=audit.body.items.find(row=>row.entityId===item.id&&row.action==='submission.reviewed'&&row.details?.decision==='approved');assert(review);assert(review.actorId.startsWith('public-reviewer:'));assert(!JSON.stringify(review).includes('198.51.100.7'));
 const deniedDelete=await publicReview({action:'deleteSubmission',id:item.id,expectedVersion:result.body.item.version},'session',{'X-WGSS-Contribution-Token':a.cap});assert.equal(deniedDelete.status,403);assert.equal((await DB.prepare('SELECT status FROM wgss_submissions WHERE id=?').bind(item.id).first()).status,'approved');
});
test('public review can edit a contribution while create and upload continue to require contributor capability',async()=>{
 assert.equal((await publicReview({action:'createSubmission',kind:'screen',title:'No capability',privacyConfirmed:true})).status,401);
 const a=await create(),changed=await publicReview({action:'createVersion',id:a.item.id,expectedVersion:1,kind:'screen',title:'Publicly corrected title',text:'Editable review content'});assert.equal(changed.status,200,JSON.stringify(changed.body));assert.equal(changed.body.item.version,2);assert.equal(changed.body.item.status,'pending');
 const form=new FormData();form.set('action','upload');form.set('submissionId',a.item.id);form.set('role','masked');form.set('clientUploadId',crypto.randomUUID());form.set('file',new File([png],'masked.png',{type:'image/png'}));const response=await handleIntake(new Request(base,{method:'POST',body:form}),{...env,WGSS_PUBLIC_REVIEW:'true'});assert.equal(response.status,401);
});
test('public review AI preparation preserves privacy attestations, daily quota and advisory-only state',async()=>{
 const a=await create(),uploaded=await upload(a),item=uploaded.body.item,fid=item.files[0].id;await DB.prepare("DELETE FROM wgss_settings WHERE key='ai:lease' OR key LIKE 'ai:quota:%'").run();const originalFetch=globalThis.fetch;let calls=0;
 globalThis.fetch=async()=>{calls++;return Response.json({choices:[{finish_reason:'stop',message:{content:JSON.stringify({providerId:'citi',language:'en',taskId:'signup',purpose:'Account signup',screens:[{fileId:fid,title:'Create account',language:'en',taskId:'signup',purpose:'Start signup',ocrPhrases:[]}]})}}],usage:{prompt_tokens:100,completion_tokens:100}});};
 try{const settings={BEDROCK_API_KEY:'public-review-test-secret',WGSS_AI_DAILY_JOB_LIMIT:'1'};const result=await publicReview({action:'prepareReviewDraft',submissionId:item.id},'session',{},settings);assert.equal(result.status,200,JSON.stringify(result.body));assert.equal(result.body.status,'completed');assert.equal(result.body.privacyBasis,'contributor_masking_attestation');assert.equal(calls,1);assert.equal((await DB.prepare('SELECT status FROM wgss_submissions WHERE id=?').bind(item.id).first()).status,'pending');const forced=await publicReview({action:'prepareReviewDraft',submissionId:item.id,force:true},'session',{},settings);assert.equal(forced.status,429);assert.equal(forced.body.code,'ai_daily_limit');assert.equal(calls,1);}finally{globalThis.fetch=originalFetch;}
});
