import knownSources from './known-sources.json';
import {appliedRecords,targetLookup,publicationHistory,recordVersions} from './publications';
import {ApiError, Runtime, Actor, requireActor, actorId, id, now, stmt, rows, parse, bounded, auditStmt, submission, serializeSubmission, validModel, getSettings, schedulerStatus} from './core';
import {createSubmission,updateSubmission,upload,deleteSubmission} from './submissions';
import {runAiJob,runMarketScan,serializeJob,safeSource,runEvidenceBrief,runDueJobs} from './jobs';

export async function getResource(request: Request, env: Runtime, actor: Actor): Promise<Response | object> {
  const url=new URL(request.url),resource=url.searchParams.get('resource')||'session';
  if(resource==='session') return {userId:actor.userId,role:actor.role,serviceAccess:actor.service,adminConfigured:!!(env.ADMIN_USER_IDS||env.WGSS_OWNER_USER_ID||env.WGSS_ADMIN_EMAILS||env.WGSS_PRIVATE_SERVICE_ACCESS==='true')};
  requireActor(actor);
  if(resource==='publications')return appliedRecords(env);
  if(resource==='recordVersions')return recordVersions(env,url.searchParams.get('type'),url.searchParams.get('id'));
  if(resource==='targets')return targetLookup(env,actor,url.searchParams.get('type'),url.searchParams.get('q'));
  if(resource==='publicationHistory')return publicationHistory(env,actor,url.searchParams.get('type'),url.searchParams.get('id'));
  if(resource==='submissions' || resource==='published') {
    const data = resource==='published' ? await rows(env,"SELECT * FROM wgss_submissions WHERE status='approved' ORDER BY updated_at DESC LIMIT 200") : actor.role==='admin' ? await rows(env,'SELECT * FROM wgss_submissions ORDER BY updated_at DESC LIMIT 200') : await rows(env,'SELECT * FROM wgss_submissions WHERE owner_id=? ORDER BY updated_at DESC LIMIT 200',actor.userId);
    const items=await Promise.all(data.map(s=>serializeSubmission(env,s)));
    if(resource==='published') return {items:items.map(({ownerId,...item})=>({...item,files:item.files.filter((f:any)=>f.role==='masked'&&f.reviewStatus==='approved')}))};
    return {items};
  }
  if(resource==='file') {
    const file=await stmt(env,'SELECT f.*,s.owner_id,s.status FROM wgss_files f JOIN wgss_submissions s ON s.id=f.submission_id WHERE f.id=?',bounded(url.searchParams.get('id'),'id',100,true)).first<any>();
    if(!file)throw new ApiError(404,'not_found','Image not found.');
    const applied = file.role==='masked' ? await stmt(env,"SELECT id FROM wgss_publications WHERE state='applied' AND json_extract(patch_json,'$.imageFileId')=? AND json_extract(patch_json,'$.originalSha')=? LIMIT 1",file.id,file.sha256).first() : null;
    if(actor.role!=='admin' && file.owner_id!==actor.userId && !applied && !(file.status==='approved'&&file.role==='masked'&&file.review_status==='approved'&&file.reviewed_sha256===file.sha256)) throw new ApiError(403,'forbidden','This image is quarantined.');
    const object=await env.BUCKET.get(file.object_key); if(!object)throw new ApiError(404,'not_found','Image not found.');
    return new Response(object.body,{headers:{'Content-Type':file.mime,'Content-Length':String(file.size),'Content-Disposition':`inline; filename="reference-${file.id}.${file.mime==='image/png'?'png':file.mime==='image/jpeg'?'jpg':'webp'}"`,'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; sandbox"}});
  }
  if(resource==='versions') {
    const source=await submission(env,actor,bounded(url.searchParams.get('id'),'id',100,true));
    const items=await rows(env,'SELECT * FROM wgss_versions WHERE submission_id=? ORDER BY version DESC',source.id);
    return {items:items.map(v=>({id:v.id,submissionId:v.submission_id,version:v.version,title:v.title,content:parse(v.content_json),status:v.status,reviewReason:v.review_reason,createdAt:v.created_at}))};
  }
  if(resource==='comparisons') {
    const items=await rows(env,'SELECT * FROM wgss_comparisons WHERE owner_id=? ORDER BY created_at DESC LIMIT 100',actorId(actor));
    return {items:items.map(c=>({id:c.id,name:c.name,referenceIds:parse(c.reference_ids_json,[]),context:parse(c.context_json),createdAt:c.created_at}))};
  }
  requireActor(actor,true);
  if(resource==='jobs') return {items:(await rows(env,'SELECT * FROM wgss_jobs ORDER BY created_at DESC LIMIT 100')).map(serializeJob)};
  if(resource==='audit') return {items:(await rows(env,'SELECT * FROM wgss_audit ORDER BY created_at DESC LIMIT 200')).map(a=>({id:a.id,actorId:a.actor_id,action:a.action,entityId:a.entity_id,details:parse(a.details_json),createdAt:a.created_at}))};
  if(resource==='settings') return {settings:await getSettings(env),scheduler:schedulerStatus(env),gatewayConfigured:!!env.BEDROCK_API_KEY};
  if(resource==='sources') { const query=(url.searchParams.get('q')||'').toLowerCase(); return {items:knownSources.filter(s=>s.toLowerCase().includes(query)).slice(0,50),total:knownSources.length}; }
  throw new ApiError(404,'unknown_resource','Unknown resource.');
}
async function limitedRequestBody(request: Request, limit: number) { if(Number(request.headers.get('content-length')||0)>limit) throw new ApiError(413,'request_too_large','Request is too large.'); const reader=request.body?.getReader(); if(!reader)return new Uint8Array(); const chunks=[]; let length=0; try { for(;;){ const {done,value}=await reader.read(); if(done)break; length+=value.byteLength; if(length>limit)throw new ApiError(413,'request_too_large','Request is too large.'); chunks.push(value); } } finally { await reader.cancel().catch(()=>{}); } const bytes=new Uint8Array(length); let offset=0; for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;} return bytes; }
export async function mutate(request: Request, env: Runtime, actor: Actor) {
  requireActor(actor); const origin=request.headers.get('origin');
  if(origin && origin!==new URL(request.url).origin)throw new ApiError(403,'origin_forbidden','Cross-origin changes are not allowed.');
  if(request.headers.get('sec-fetch-site')==='cross-site')throw new ApiError(403,'origin_forbidden','Cross-site changes are not allowed.');
  if(request.headers.get('content-type')?.startsWith('multipart/form-data')) {
    const body=await limitedRequestBody(request,9*1024*1024); const form=await new Response(body,{headers:{'Content-Type':request.headers.get('content-type')!}}).formData();
    if(form.get('action')!=='upload')throw new ApiError(400,'invalid_action','Invalid upload action.'); return upload(env,actor,form);
  }
  if(!request.headers.get('content-type')?.startsWith('application/json'))throw new ApiError(415,'json_required','Use JSON or multipart form data.');
  let input:any; try { input=JSON.parse(new TextDecoder().decode(await limitedRequestBody(request,64000))); } catch(error) { if(error instanceof ApiError)throw error; throw new ApiError(400,'invalid_json','Invalid JSON body.'); }
  if(!input || typeof input!=='object' || Array.isArray(input))throw new ApiError(400,'invalid_input','Expected a JSON object.');
  if(input.action==='createSubmission')return createSubmission(env,actor,input);
  if(input.action==='createVersion')return updateSubmission(env,actor,input,false);
  if(input.action==='reviewSubmission')return updateSubmission(env,actor,input,true);
  if(input.action==='deleteSubmission')return deleteSubmission(env,actor,input);
  if(input.action==='saveComparison') {
    const name=bounded(input.name,'name',120,true),refs=input.referenceIds;
    if(!Array.isArray(refs)||refs.length<2||refs.length>3||refs.some(r=>typeof r!=='string'||!r||r.length>200)||new Set(refs).size!==refs.length)throw new ApiError(400,'invalid_comparison','Choose two or three distinct reference IDs.');
    const context=input.context||{}; if(typeof context!=='object'||Array.isArray(context)||JSON.stringify(context).length>4000)throw new ApiError(400,'invalid_context','Invalid comparison context.');
    const cid=id(),time=now(); await env.DB.batch([stmt(env,'INSERT INTO wgss_comparisons (id,owner_id,name,reference_ids_json,context_json,created_at) VALUES (?,?,?,?,?,?)',cid,actorId(actor),name,JSON.stringify(refs),JSON.stringify(context),time),auditStmt(env,actor,'comparison.saved',cid,{referenceCount:refs.length})]);
    return {item:{id:cid,name,referenceIds:refs,context,createdAt:time}};
  }
  if(input.action==='deleteComparison') {
    const cid=bounded(input.id,'id',100,true),item=await stmt(env,'SELECT id FROM wgss_comparisons WHERE id=? AND owner_id=?',cid,actorId(actor)).first(); if(!item)throw new ApiError(404,'not_found','Comparison not found.');
    await env.DB.batch([stmt(env,'DELETE FROM wgss_comparisons WHERE id=? AND owner_id=?',cid,actorId(actor)),auditStmt(env,actor,'comparison.deleted',cid)]); return {deleted:true};
  }
  requireActor(actor,true);
  if(input.action==='runDueJobs')return runDueJobs(env,actor);
  if(input.action==='runEvidenceBrief')return runEvidenceBrief(env,actor,input);
  if(input.action==='runAiJob')return runAiJob(env,actor,input);
  if(input.action==='runMarketScan')return runMarketScan(env,actor,input);
  if(input.action==='updateSettings') {
    const value=input.settings; if(!value||typeof value!=='object')throw new ApiError(400,'invalid_settings','Settings are required.');
    const previous=await getSettings(env),merged={...previous,...value};
    if(typeof merged.scheduleEnabled!=='boolean'||!Number.isInteger(merged.intervalHours)||merged.intervalHours<1||merged.intervalHours>720||!Array.isArray(merged.sourceUrls)||merged.sourceUrls.length>5)throw new ApiError(400,'invalid_settings','Invalid interval or source selection.');
    const settings={scheduleEnabled:merged.scheduleEnabled,intervalHours:merged.intervalHours,sourceUrls:[...new Set(merged.sourceUrls.map(safeSource))],marketQuery:bounded(merged.marketQuery,'marketQuery',500),model:validModel(merged.model)};
    await env.DB.batch([stmt(env,'INSERT INTO wgss_settings (key,value_json,updated_at) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at','workspace',JSON.stringify(settings),now()),auditStmt(env,actor,'settings.updated','workspace',{scheduleRequested:settings.scheduleEnabled,sourceCount:settings.sourceUrls.length})]);
    return {settings,scheduler:schedulerStatus(env)};
  }
  throw new ApiError(400,'invalid_action','Unknown action.');
}
export async function handleRequest(request: Request, env: Runtime, actor: Actor) {
  try { if(!env.DB || !env.BUCKET)throw new ApiError(503,'storage_not_configured','Workspace storage is not configured.');
    const result=request.method==='GET'?await getResource(request,env,actor):request.method==='POST'?await mutate(request,env,actor):null;
    if(result===null)return Response.json({error:'Method not allowed.',code:'method_not_allowed'},{status:405,headers:{Allow:'GET, POST'}});
    return result instanceof Response?result:Response.json(result,{headers:{'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});
  } catch(error) { const known=error instanceof ApiError; return Response.json({error:known?error.message:'The workspace request failed. Retry or contact the administrator.',code:known?error.code:'internal_error'},{status:known?error.status:500,headers:{'Cache-Control':'private, no-store'}}); }
}
