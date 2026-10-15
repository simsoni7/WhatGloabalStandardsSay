import referenceIndex from './wgss/reference-index.json';
import {handleRequest} from './wgss/api';
import {ApiError,Actor,Runtime,getActor,hash,stmt,content,bounded,id,now,auditStmt,serializeSubmission,submission} from './wgss/core';
import {appliedRecords,isReviewedPublicTerm} from './wgss/publications';
import {imageMime} from './wgss/images';

const FRONTEND='https://simsoni7.github.io';
const allowedDatasets=new Set(['apache_ofbiz_accounting','apache_ofbiz_financial_entities','canada_government_financial_labels','cfpb_remittance','cfpb_remittance_receipt_labels','cfpd','eu_cpv_financial_services','malaysia_financial_dashboard','malaysia_financial_metadata','unicode_cldr_currency_names']);
const publicTerms=new Set((referenceIndex as any).terms.filter((row:any)=>allowedDatasets.has(row.datasetId)).map((row:any)=>row.id));
const publicReader:Actor={userId:'public-reference-reader',role:'contributor',service:false};
const PUBLIC_REVIEW_RESOURCES=['submissions','versions','audit','targets','reviewDraft','publicationHistory','file'];
const PUBLIC_REVIEW_ACTIONS=['prepareReviewDraft','reviewSubmission','createVersion'];
function visibleReviewItem({ownerId,...item}:any){return {...item,files:(item.files||[]).filter((file:any)=>file.role==='masked')};}
async function publicReviewer(request:Request):Promise<Actor>{const browser=request.headers.get('X-WGSS-Contribution-Token');const proof=browser&&/^[0-9a-f]{64}$/.test(browser)?'browser:'+browser:'ingress:'+(request.headers.get('cf-connecting-ip')||'shared-anonymous');return {userId:'public-reviewer:'+await hash('wgss-public-review-v1:'+proof),role:'admin',service:false};}
const UPLOAD_DAILY=500*1024*1024;
function allowedOrigin(request:Request,env:Runtime){const origin=request.headers.get('origin');const allowed=new Set([FRONTEND,'https://wgss-case-library.booknfoto461.chatgpt.site',new URL(request.url).origin]);for(const entry of (env.WGSS_PUBLIC_FRONTEND_ORIGINS||'').split(',')){try{const u=new URL(entry.trim());if(u.protocol==='https:'&&u.origin===entry.trim())allowed.add(u.origin);}catch{}}if(origin&&!allowed.has(origin))throw new ApiError(403,'origin_forbidden','허용된 WGSS 화면에서만 요청할 수 있습니다.');return origin;}
function cors(response:Response,origin:string|null){const headers=new Headers(response.headers);headers.set('Cache-Control','private, no-store');headers.set('X-Content-Type-Options','nosniff');headers.append('Vary','Origin');if(origin){headers.set('Access-Control-Allow-Origin',origin);headers.set('Access-Control-Allow-Methods','GET, POST, OPTIONS');headers.set('Access-Control-Allow-Headers','Content-Type, X-WGSS-Contribution-Token');headers.set('Access-Control-Max-Age','600');}return new Response(response.body,{status:response.status,statusText:response.statusText,headers});}
function errorResponse(error:unknown){const known=error instanceof ApiError;return Response.json({error:known?error.message:'요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.',code:known?error.code:'internal_error'},{status:known?error.status:500});}
async function capability(request:Request):Promise<Actor>{const token=request.headers.get('X-WGSS-Contribution-Token');if(!token||!/^[0-9a-f]{64}$/.test(token))throw new ApiError(401,'contribution_token_required','제안 확인 정보가 필요합니다. 화면을 새로 열어 다시 시도해 주세요.');return {userId:'contribution:'+await hash(token),role:'contributor',service:false};}
function internal(request:Request,body?:BodyInit,contentType?:string){const headers=new Headers(request.headers);headers.delete('origin');headers.delete('sec-fetch-site');headers.delete('X-WGSS-Contribution-Token');headers.delete('content-length');if(contentType)headers.set('Content-Type',contentType);return new Request(request.url,{method:request.method,headers,body:body??request.body,...(request.body&&body===undefined?{duplex:'half'}:{})} as RequestInit);}
async function bodyBytes(request:Request,limit:number){const rawLength=request.headers.get('content-length');if(rawLength&&Number(rawLength)>limit)throw new ApiError(413,'request_too_large','첨부할 수 있는 용량을 초과했습니다. 사진은 한 장에 8MB까지 가능합니다.');const reader=request.body?.getReader();if(!reader)return new Uint8Array();const parts:Uint8Array[]=[];let size=0;try{for(;;){const next=await reader.read();if(next.done)break;size+=next.value.byteLength;if(size>limit)throw new ApiError(413,'request_too_large','첨부할 수 있는 용량을 초과했습니다. 사진은 한 장에 8MB까지 가능합니다.');parts.push(next.value);}}finally{await reader.cancel().catch(()=>{});}const bytes=new Uint8Array(size);let offset=0;for(const part of parts){bytes.set(part,offset);offset+=part.byteLength;}return bytes;}
function quota(env:Runtime,key:string,amount:number,limit:number){return stmt(env,'INSERT INTO wgss_intake_quota (id,used,"limit",updated_at) VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET used=CASE WHEN used+excluded.used<="limit" THEN used+excluded.used ELSE NULL END,updated_at=excluded.updated_at',key,amount,limit,now());}
async function existing(env:Runtime,actor:Actor,sid:string){const row=await stmt(env,'SELECT * FROM wgss_submissions WHERE id=? AND owner_id=?',sid,actor.userId).first<any>();return row?{item:await serializeSubmission(env,row),reused:true}:null;}
async function create(env:Runtime,actor:Actor,input:any,request:Request){
 if(input.privacyConfirmed!==true)throw new ApiError(400,'privacy_confirmation_required','이름·연락처·계좌번호 등 개인정보를 가렸는지 확인해 주세요.');
 const sid='intake-'+actor.userId!.slice('contribution:'.length),prior=await existing(env,actor,sid);if(prior)return prior;
 if(!['translation_issue','text','screen'].includes(input.kind))throw new ApiError(400,'invalid_kind','제안할 자료의 종류를 확인해 주세요.');
 const title=bounded(input.title,'title',300,true),data=JSON.stringify(content(input)),time=now(),day=time.slice(0,10),hour=time.slice(0,13);
 // CF-Connecting-IP is supplied by the ingress. Never trust a caller's X-Forwarded-For.
 const ipKey=await hash(hour+':'+(request.headers.get('cf-connecting-ip')||'unavailable'));
 try{await env.DB.batch([
  quota(env,'create:global:'+day,1,100),quota(env,'create:ip:'+ipKey+':'+hour,1,10),
  stmt(env,'INSERT INTO wgss_submissions (id,owner_id,kind,status,version,title,content_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)',sid,actor.userId,input.kind,'pending',1,title,data,time,time),
  stmt(env,'INSERT INTO wgss_versions (id,submission_id,version,title,content_json,status,actor_id,created_at) VALUES (?,?,?,?,?,?,?,?)',id(),sid,1,title,data,'pending',actor.userId,time),
  auditStmt(env,actor,'submission.created',sid,{kind:input.kind,channel:'public-intake'}),
 ]);}catch(error){const raced=await existing(env,actor,sid);if(raced)return raced;if(/NOT NULL constraint failed: wgss_intake_quota\.used/.test(String(error)))throw new ApiError(429,'intake_quota','현재 제안 접수 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.');throw error;}
 return {item:await serializeSubmission(env,await submission(env,actor,sid))};
}
async function maskedUpload(request:Request,env:Runtime,actor:Actor){
 const bytes=await bodyBytes(request,9*1024*1024);let form:FormData;try{form=await new Response(bytes,{headers:{'Content-Type':request.headers.get('content-type')!}}).formData();}catch{throw new ApiError(400,'invalid_upload','사진 전송 정보를 읽지 못했습니다. 다시 첨부해 주세요.');}
 if(form.get('action')!=='upload'||form.get('role')!=='masked')throw new ApiError(403,'masked_only','개인정보를 가린 사진만 보낼 수 있습니다. 원본 사진은 접수하지 않습니다.');
 const source=await submission(env,actor,bounded(form.get('submissionId'),'submissionId',100,true));if(source.status!=='pending')throw new ApiError(409,'not_pending','검토 대기 중인 제안에만 사진을 추가할 수 있습니다.');
 const file=form.get('file');if(!file||typeof file==='string')throw new ApiError(400,'file_required','첨부할 사진을 선택해 주세요.');if(file.size<16||file.size>8*1024*1024)throw new ApiError(413,'file_size','사진은 한 장에 8MB까지 가능합니다.');
 const data=new Uint8Array(await file.arrayBuffer()),mime=imageMime(data);if(!mime||file.type!==mime)throw new ApiError(415,'invalid_image','PNG·JPEG·WebP 사진만 첨부할 수 있습니다.');
 const clientId=bounded(form.get('clientUploadId'),'clientUploadId',36);if(!clientId||! /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(clientId))throw new ApiError(400,'upload_id_required','사진 전송 확인 정보가 필요합니다. 다시 시도해 주세요.');
 const digest=await hash(data),prior=await stmt(env,'SELECT submission_id,sha256,role FROM wgss_files WHERE id=?',clientId).first<any>();
 if(prior){if(prior.submission_id!==source.id||prior.sha256!==digest||prior.role!=='masked')throw new ApiError(409,'upload_conflict','이미 전송된 사진 정보와 일치하지 않습니다.');return Response.json({item:await serializeSubmission(env,await submission(env,actor,source.id)),reused:true});}
 const key='upload:global:'+now().slice(0,10);try{await env.DB.batch([quota(env,key,data.byteLength,UPLOAD_DAILY)]);}catch(error){if(/NOT NULL constraint failed: wgss_intake_quota\.used/.test(String(error)))throw new ApiError(429,'upload_quota','오늘의 사진 접수 용량을 초과했습니다. 내일 다시 시도해 주세요.');throw error;}
 let retained=false;try{const response=await handleRequest(internal(request,bytes,request.headers.get('content-type')!),env,actor);if(response.ok){const result=await response.clone().json() as any;retained=!result.reused;}else{const winner=await stmt(env,'SELECT submission_id,sha256,role FROM wgss_files WHERE id=?',clientId).first<any>();if(winner?.submission_id===source.id&&winner.sha256===digest&&winner.role==='masked')return Response.json({item:await serializeSubmission(env,await submission(env,actor,source.id)),reused:true});}return response;}finally{if(!retained)await stmt(env,'UPDATE wgss_intake_quota SET used=MAX(0,used-?),updated_at=? WHERE id=?',data.byteLength,now(),key).run();}
}
function publicTermAllowed(type:string|null,target:string|null,patch?:any){return type!=='terms'||!!target&&(publicTerms.has(target)||isReviewedPublicTerm(patch,target));}
function publicPatch(patch:any){if(!patch?.commercialRights)return patch;const {reviewedBy,...review}=patch.commercialRights;return {...patch,commercialRights:review};}
async function deleteOwn(request:Request,env:Runtime,actor:Actor,input:any){
 const source=await submission(env,actor,bounded(input.id,'id',100,true));
 if(source.status!=='pending'&&source.status!=='deleting')throw new ApiError(403,'pending_only','검토 대기 중인 본인 제안만 취소할 수 있습니다.');
 if(input.expectedVersion!==source.version)throw new ApiError(409,'version_conflict','제안 상태가 바뀌었습니다. 새로고침 후 다시 시도해 주세요.');
 if(source.status==='pending'){
  // Claim the shared immutable next version before deletion. A concurrent
  // review must lose that same unique-version race, never erase an approval.
  try{await env.DB.batch([
   stmt(env,"INSERT INTO wgss_versions (id,submission_id,version,title,content_json,status,actor_id,created_at) SELECT ?,id,version+1,'','{}','deleting',?,? FROM wgss_submissions WHERE id=? AND version=? AND status='pending'",id(),actor.userId,now(),source.id,source.version),
   stmt(env,"UPDATE wgss_submissions SET version=version+1,status='deleting',privacy_reviewed=0,readability_reviewed=0,updated_at=? WHERE id=? AND version=? AND status='pending'",now(),source.id,source.version),
  ]);}catch{throw new ApiError(409,'version_conflict','제안 상태가 바뀌었습니다. 새로고침 후 다시 시도해 주세요.');}
  const current=await submission(env,actor,source.id);if(current.status!=='deleting'||current.version!==source.version+1)throw new ApiError(409,'version_conflict','검토가 시작되어 제안을 취소할 수 없습니다.');
  input={...input,expectedVersion:current.version};
 }
 return handleRequest(internal(request,JSON.stringify({...input,action:'deleteSubmission'}),'application/json'),env,actor);
}
export async function handleIntake(request:Request,inputEnv:Runtime):Promise<Response>{
 let origin:string|null=null;
 try{
  origin=allowedOrigin(request,inputEnv);const env={...inputEnv,WGSS_PRIVATE_SERVICE_ACCESS:'false'};
  if(request.method==='OPTIONS')return cors(new Response(null,{status:204}),origin);
  if(!['GET','POST'].includes(request.method))throw new ApiError(405,'method_not_allowed','지원하지 않는 요청 방식입니다.');
  const native=getActor(request.headers.get('oai-authenticated-user-id'),env,request.headers.get('oai-authenticated-user-email'));
  if(native.role==='admin')return cors(await handleRequest(internal(request),env,native),origin);
  const url=new URL(request.url),resource=url.searchParams.get('resource')||'session';
  if(request.method==='GET'){
   if(resource==='session'){if(env.WGSS_PUBLIC_REVIEW==='true'){const reviewer=await publicReviewer(request);return cors(Response.json({role:'admin',userId:reviewer.userId,serviceAccess:false,publicIntake:true,publicReview:true,reviewResources:[...PUBLIC_REVIEW_RESOURCES,'publications','recordVersions'],reviewActions:PUBLIC_REVIEW_ACTIONS}),origin);}return cors(Response.json({role:'anonymous',userId:null,serviceAccess:false,publicIntake:true}),origin);}
   if(env.WGSS_PUBLIC_REVIEW==='true'&&PUBLIC_REVIEW_RESOURCES.includes(resource)){
    if(resource==='file'){const file=await stmt(env,'SELECT role FROM wgss_files WHERE id=?',bounded(url.searchParams.get('id'),'id',100,true)).first<any>();if(!file)throw new ApiError(404,'not_found','사진을 찾을 수 없습니다.');if(file.role!=='masked')throw new ApiError(403,'masked_only','개인정보를 가린 사진만 검토할 수 있습니다.');}
    const response=await handleRequest(internal(request),env,await publicReviewer(request));
    if(resource==='targets'&&url.searchParams.get('type')==='terms'&&response.ok){const data=await response.json() as any;data.items=(data.items||[]).filter((row:any)=>publicTermAllowed('terms',row.id,row));return cors(Response.json(data),origin);}
    if(resource==='submissions'&&response.ok){const data=await response.json() as any;return cors(Response.json({...data,publicReview:true,items:(data.items||[]).map(visibleReviewItem)}),origin);}return cors(response,origin);
   }
   if(resource==='submissions'){const actor=await capability(request);return cors(await handleRequest(internal(request),env,actor),origin);}
   if(!['publications','recordVersions','file'].includes(resource))throw new ApiError(403,'private_resource','이 정보는 자료 관리자만 볼 수 있습니다.');
   if(resource==='file'&&request.headers.has('X-WGSS-Contribution-Token')){const actor=await capability(request),file=await stmt(env,'SELECT f.role,s.owner_id FROM wgss_files f JOIN wgss_submissions s ON s.id=f.submission_id WHERE f.id=?',bounded(url.searchParams.get('id'),'id',100,true)).first<any>();if(file?.owner_id===actor.userId&&file.role==='masked')return cors(await handleRequest(internal(request),env,actor),origin);}
   if(resource==='recordVersions'&&url.searchParams.get('type')==='terms'){const target=url.searchParams.get('id'),published=(await appliedRecords(env)).items.find(row=>row.type==='terms'&&row.targetId===target);if(!publicTermAllowed('terms',target,published?.patch))throw new ApiError(404,'not_found','공개된 용어를 찾을 수 없습니다.');}
   const response=await handleRequest(internal(request),env,publicReader);
   if(resource==='publications'&&response.ok){const data=await response.json() as any;data.items=(data.items||[]).filter((row:any)=>publicTermAllowed(row.type,row.targetId,row.patch)).map((row:any)=>({...row,patch:publicPatch(row.patch)}));return cors(Response.json(data),origin);}if(resource==='recordVersions'&&response.ok&&url.searchParams.get('type')==='terms'){const data=await response.json() as any;let merged:any={};data.items=(data.items||[]).filter((row:any)=>{merged={...merged,...row.fields};return publicTerms.has(url.searchParams.get('id')||'')||isReviewedPublicTerm(merged,url.searchParams.get('id'));}).map((row:any)=>({...row,fields:publicPatch(row.fields)}));return cors(Response.json(data),origin);}return cors(response,origin);
  }
  const type=request.headers.get('content-type')||'';
  if(type.startsWith('multipart/form-data'))return cors(await maskedUpload(request,env,await capability(request)),origin);
  if(!type.startsWith('application/json'))throw new ApiError(415,'json_required','자료 설명은 JSON, 사진은 파일 형식으로 보내 주세요.');
  let input:any;try{input=JSON.parse(new TextDecoder().decode(await bodyBytes(request,64000)));}catch(error){if(error instanceof ApiError)throw error;throw new ApiError(400,'invalid_json','제안 내용을 읽을 수 없습니다.');}
  if(!input||typeof input!=='object'||Array.isArray(input))throw new ApiError(400,'invalid_input','제안 내용을 확인해 주세요.');
  if(env.WGSS_PUBLIC_REVIEW==='true'&&PUBLIC_REVIEW_ACTIONS.includes(input.action)){const response=await handleRequest(internal(request,JSON.stringify(input),'application/json'),env,await publicReviewer(request));if(response.ok&&['reviewSubmission','createVersion'].includes(input.action)){const data=await response.json() as any;if(data.item)data.item=visibleReviewItem(data.item);return cors(Response.json(data),origin);}return cors(response,origin);}
  if(env.WGSS_PUBLIC_REVIEW==='true'&&!['createSubmission','deleteOwn','deleteSubmission'].includes(input.action))throw new ApiError(403,'public_review_action_forbidden','공개 자료 검토에서 사용할 수 없는 운영 기능입니다.');
  const actor=await capability(request);
  if(input.action==='createSubmission')return cors(Response.json(await create(env,actor,input,request)),origin);
  if(input.action==='deleteOwn'||input.action==='deleteSubmission')return cors(await deleteOwn(request,env,actor,input),origin);
  throw new ApiError(403,'admin_required','자료 검토와 운영 기능은 관리자만 실행할 수 있습니다.');
 }catch(error){return cors(errorResponse(error),origin);}
}
