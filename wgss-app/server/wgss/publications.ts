import referenceIndex from './reference-index.json';
import {ApiError,Runtime,Actor,requireActor,stmt,rows,bounded,parse,id,now,actorId,hash} from './core';
const types=['screens','phrases','terms','features'] as const;
type EntityType=typeof types[number];
const index=referenceIndex as any;
const base=new Map<string,any>();
for(const type of types)for(const row of index[type])base.set(type+':'+row.id,row);
const sets={providerId:new Set(index.providers.map((r:any)=>r.id)),language:new Set(index.languages.map((r:any)=>r.id)),taskId:new Set(index.tasks.map((r:any)=>r.id)),workId:new Set(index.works.map((r:any)=>r.id))};
export const reviewedTermDataset='wgss_reviewed_terms';
const commercialLicenses=new Set(['CC0-1.0','CC-BY-4.0','MIT','Apache-2.0','Unicode-3.0','US-Public-Domain']);
export function isReviewedPublicTerm(patch:any,targetId?:string|null){const review=patch?.commercialRights;return !!patch&&patch.id===targetId&&String(targetId||'').startsWith('contribution:terms:')&&patch.datasetId===reviewedTermDataset&&patch.recordType==='contributed_term'&&patch.commercial===true&&patch.layer==='reviewed'&&review?.confirmed===true&&commercialLicenses.has(review.license)&&typeof review.basis==='string'&&review.basis.length>=10&&/^https:\/\//.test(review.evidenceUrl||'')&&/^\d{4}-\d{2}-\d{2}T/.test(review.reviewedAt||'')&&/^[0-9a-f]{64}$/.test(review.reviewSha||'');}
async function reviewedRights(actor:Actor,value:any){
 requireActor(actor,true);
 if(!value||value.confirmed!==true)throw new ApiError(400,'commercial_review_required','새 용어는 담당자가 상업 이용 조건 원문을 확인한 후 게시할 수 있습니다.');
 const license=bounded(value.license,'license',100,true),evidenceUrl=bounded(value.evidenceUrl,'rightsEvidenceUrl',2000,true),basis=bounded(value.basis,'rightsBasis',5000,true);
 if(!commercialLicenses.has(license))throw new ApiError(400,'commercial_license_required','상업 이용을 허용하는 이용 조건을 선택해 주세요.');
 try{const u=new URL(evidenceUrl);if(u.protocol!=='https:'||u.username||u.password||!u.hostname.includes('.')||u.hostname==='localhost')throw 0;}catch{throw new ApiError(400,'rights_url_required','이용 조건을 직접 확인한 HTTPS 원문 주소를 입력해 주세요.');}
 if(basis.length<10)throw new ApiError(400,'rights_basis_required','이 이용 조건이 제안한 자료에 적용되는 이유를 10자 이상 적어 주세요.');
 const record={confirmed:true,license,evidenceUrl,basis,reviewedBy:actorId(actor),reviewedAt:now(),reviewMethod:'operator_source_review'};
 return {...record,reviewSha:await hash(JSON.stringify(record))};
}
const fields:Record<EntityType,string[]>={screens:['title','providerId','language','taskId','stageLabel','sourceUrl','capturedAt','appVersion','collectionReferenceId','purpose','captureDateBasis'],phrases:['text','providerId','language','taskId','context','role','sourceUrl'],terms:['english','target','korean','definition','language','sourceUrl'],features:['expression','meaning','conditions','providerId','language','taskId','workId','sourceUrl']};
function checkedType(value:unknown):EntityType{if(!types.includes(value as EntityType))throw new ApiError(400,'invalid_target','반영할 자료 종류를 선택해 주세요.');return value as EntityType;}
export async function appliedRecords(env:Runtime){
 const all=await rows(env,'SELECT id,target_type,target_id,revision,source_submission_id,source_version,patch_json,state,created_at FROM wgss_publications ORDER BY revision,created_at,rowid');
 const merged=new Map<string,any>();
 for(const row of all){const key=row.target_type+':'+row.target_id;let current=merged.get(key);if(!current){current={type:row.target_type,targetId:row.target_id,revision:0,patch:{},appliedVersions:[]};merged.set(key,current);}current.revision=Math.max(current.revision,row.revision);if(row.state!=='applied')continue;Object.assign(current.patch,parse(row.patch_json));current.appliedVersions.push({id:row.id,revision:row.revision,sourceVersion:row.source_version,appliedAt:row.created_at});current.appliedAt=row.created_at;}
 return {items:[...merged.values()].filter(item=>item.patch.retired!==true)};
}
export async function targetLookup(env:Runtime,actor:Actor,typeValue:unknown,query:unknown){requireActor(actor,true);const type=checkedType(typeValue),q=bounded(query,'query',300).toLocaleLowerCase();const applied=(await appliedRecords(env)).items.filter(r=>r.type===type);const found=new Map(index[type].map((r:any)=>[r.id,{...r,revision:0}]));for(const item of applied){const prior=found.get(item.targetId) as any;if(!prior&&!item.patch.id)continue;found.set(item.targetId,{...prior,...item.patch,id:item.targetId,revision:item.revision});}const items=[...found.values()].filter((r:any)=>!q||[r.id,r.label,r.title,r.text,r.english,r.target,r.expression].some(v=>String(v||'').toLocaleLowerCase().includes(q))).slice(0,40);return {items};}
export async function publicationHistory(env:Runtime,actor:Actor,typeValue:unknown,targetId:unknown){requireActor(actor,true);const type=checkedType(typeValue),target=bounded(targetId,'targetId',200,true);return {items:(await rows(env,'SELECT * FROM wgss_publications WHERE target_type=? AND target_id=? ORDER BY revision DESC',type,target)).map(r=>({id:r.id,revision:r.revision,sourceSubmissionId:r.source_submission_id,sourceVersion:r.source_version,state:r.state,fields:parse(r.patch_json),createdAt:r.created_at}))};}
export async function recordVersions(env:Runtime,typeValue:unknown,targetId:unknown){const type=checkedType(typeValue),target=bounded(targetId,'targetId',200,true);return {items:(await rows(env,"SELECT revision,patch_json,created_at FROM wgss_publications WHERE target_type=? AND target_id=? AND state='applied' ORDER BY revision",type,target)).map(r=>({revision:r.revision,fields:parse(r.patch_json),createdAt:r.created_at}))};}
async function prepareSinglePublication(env:Runtime,actor:Actor,source:any,input:any,selectedFiles:string[],nextVersion:number){
 requireActor(actor,true);
 const plan=input.application;
 if(!plan||typeof plan!=='object'||Array.isArray(plan))throw new ApiError(400,'application_required','승인한 내용을 반영할 위치와 최종 내용을 지정해 주세요.');
 const type=checkedType(plan.type);if(!['add','update'].includes(plan.operation))throw new ApiError(400,'invalid_application','추가 또는 수정을 선택해 주세요.');
 if(!plan.fields||typeof plan.fields!=='object'||Array.isArray(plan.fields))throw new ApiError(400,'invalid_fields','반영할 최종 내용을 입력해 주세요.');
 const patch:any={};for(const [key,value] of Object.entries(plan.fields)){if(!fields[type].includes(key))throw new ApiError(400,'invalid_field','이 자료에서 수정할 수 없는 항목입니다: '+key);patch[key]=bounded(value,key,key==='definition'||key==='meaning'||key==='context'||key==='conditions'?5000:key==='sourceUrl'?2000:1000);}
 for(const [key,values] of Object.entries(sets))if(key in patch&&!values.has(patch[key]))throw new ApiError(400,'unknown_identity','등록되지 않은 '+key+'입니다.');
 const sourceCollection=bounded(parse(source.content_json).collectionReferenceId,'collectionReferenceId',200);
 if(sourceCollection){if(type!=='screens'||plan.operation!=='add')throw new ApiError(400,'collection_add_only','함께 수집한 화면 제안은 기존 화면을 교체하지 않고 새 화면으로 추가해야 합니다.');if(patch.collectionReferenceId&&patch.collectionReferenceId!==sourceCollection)throw new ApiError(400,'collection_conflict','제안한 수집 묶음과 반영할 묶음이 다릅니다.');patch.collectionReferenceId=sourceCollection;}
 if(patch.collectionReferenceId){
  if(type!=='screens'||plan.operation!=='add')throw new ApiError(400,'collection_add_only','함께 수집한 화면은 새 화면으로 추가해 주세요.');
  const originalAnchor=base.get('screens:'+patch.collectionReferenceId),anchorPatch=(await appliedRecords(env)).items.find(r=>r.type==='screens'&&r.targetId===patch.collectionReferenceId)?.patch;
  const collectionAnchor=originalAnchor?{...originalAnchor,...anchorPatch}:anchorPatch;
  if(!collectionAnchor?.id)throw new ApiError(400,'unknown_collection','함께 수집한 기준 화면을 찾을 수 없습니다.');
  if(collectionAnchor.providerId&&patch.providerId!==collectionAnchor.providerId)throw new ApiError(400,'collection_provider','같은 금융사의 화면만 수집 묶음에 추가할 수 있습니다.');
 }
 if(patch.sourceUrl){try{const u=new URL(patch.sourceUrl);if(u.protocol!=='https:'||u.username||u.password)throw 0;}catch{throw new ApiError(400,'invalid_url','출처에는 HTTPS 주소를 입력해 주세요.');}}
 if(patch.capturedAt&&!/^\d{4}-\d{2}-\d{2}$/.test(patch.capturedAt))throw new ApiError(400,'invalid_date','캡처일은 YYYY-MM-DD로 입력해 주세요.');
 const target=plan.operation==='update'?bounded(plan.targetId,'targetId',200,true):'';
 const previous=target?(await appliedRecords(env)).items.find(r=>r.type===type&&r.targetId===target):null;
 const original=target?base.get(type+':'+target):null;
 if(target&&!original&&(!previous||!previous.patch.id))throw new ApiError(400,'unknown_target','수정할 원본 자료를 찾을 수 없습니다.');
 if(!Number.isInteger(plan.expectedRevision)||plan.expectedRevision<0||(target&&(previous?.revision||0)!==plan.expectedRevision))throw new ApiError(409,'record_conflict','다른 검토자가 이 자료를 수정했습니다. 최신 내용을 다시 불러와 주세요.');
 if(type==='terms'&&target){if('english'in patch||'language'in patch)throw new ApiError(400,'term_identity','기존 용어의 원문과 언어는 유지합니다. 다른 언어는 새 용어로 추가해 주세요.');}
 const termRights=type==='terms'&&(plan.operation==='add'||previous?.patch.datasetId===reviewedTermDataset)?await reviewedRights(actor,plan.commercialRights):null;
 if(termRights&&(('sourceUrl'in patch&&!patch.sourceUrl)||(!patch.sourceUrl&&!previous?.patch.sourceUrl)))throw new ApiError(400,'term_source_required','새 용어의 원출처 링크를 입력해 주세요.');
 const required:Record<EntityType,string[]>={screens:['title','providerId','language','taskId'],phrases:['text','providerId','language','taskId'],terms:['english','target','language'],features:['expression','providerId','language','workId']};
 if(plan.operation==='add')for(const key of required[type])if(!patch[key])throw new ApiError(400,'missing_field','새 자료에 필요한 항목을 입력해 주세요: '+key);
 for(const key of required[type])if(key in patch&&!patch[key])throw new ApiError(400,'missing_field','필수 항목은 비울 수 없습니다: '+key);
 if(!Object.keys(patch).length)throw new ApiError(400,'empty_patch','반영할 내용이 없습니다.');
 if(plan.imageFileIds!==undefined&&!Array.isArray(plan.imageFileIds))throw new ApiError(400,'invalid_photos','사진 목록을 확인해 주세요.');
 const photoIds=plan.imageFileIds||[];
 if(photoIds.length>10||new Set(photoIds).size!==photoIds.length||photoIds.some((v:any)=>typeof v!=='string'||!selectedFiles.includes(v)))throw new ApiError(400,'photo_selection','반영할 사진을 개인정보 검토 목록에서도 선택해 주세요.');
 if(type==='features'&&(plan.operation==='add'||'sourceUrl'in patch)&&!patch.sourceUrl&&!photoIds.length)throw new ApiError(400,'feature_evidence','기능의 출처 링크 또는 검토한 사진이 필요합니다.');
 if(type==='screens'&&!photoIds.length&&plan.operation==='add')throw new ApiError(400,'image_required','새 화면에는 검토한 사진이 필요합니다.');
 if(type==='terms'&&photoIds.length)throw new ApiError(400,'invalid_photo_target','용어 항목에는 화면 사진을 직접 연결하지 않습니다.');
 if(plan.operation==='update'&&photoIds.length>1)throw new ApiError(400,'one_replacement','기존 자료 수정에는 사진 한 장을 선택해 주세요. 여러 사진은 새 화면으로 추가할 수 있습니다.');
 if(type!=='screens'&&photoIds.length>1)throw new ApiError(400,'one_reference_image','문구와 기능에는 근거 사진 한 장을 선택해 주세요.');
 const media:any[]=[];
 for(const fid of photoIds){const f=await stmt(env,"SELECT * FROM wgss_files WHERE id=? AND submission_id=? AND role='masked'",fid,source.id).first<any>();if(!f)throw new ApiError(400,'photo_not_owned','이 제안에 첨부된 가린 사진을 선택해 주세요.');const object=await env.BUCKET.get(f.object_key);if(!object||await hash(await object.arrayBuffer())!==f.sha256)throw new ApiError(409,'file_integrity','검토한 사진의 원본 바이트가 달라졌습니다.');media.push(f);}
 const count=type==='screens'&&plan.operation==='add'?media.length:1;const statements:any[]=[];const entries:any[]=[];
 for(let n=0;n<count;n++){
  const photo=media[n]||media[0],targetId=target||`contribution:${type}:${source.id}${type==='screens'?':'+photo.id:''}`;
  const current=target?previous:(await appliedRecords(env)).items.find(r=>r.type===type&&r.targetId===targetId);
  const expected=target?plan.expectedRevision:plan.expectedRevision;if((current?.revision||0)!==expected)throw new ApiError(409,'record_conflict','이미 반영된 자료입니다. 추가 대신 기존 자료 수정을 선택해 주세요.');
  let normalized:any={...patch};
  if(plan.operation==='add'){
   const common={id:targetId,providerId:patch.providerId||null,provider:patch.providerId?index.providers.find((p:any)=>p.id===patch.providerId)?.name:null,country:null,sourceUrl:patch.sourceUrl||null,collectedAt:patch.capturedAt||null,publicationDate:null,currentUiVersionVerified:false};
   if(type==='screens')normalized={...common,cohort:'contribution',sourceKind:'reviewed_contribution',flowId:null,collectionId:'submission:'+source.id,collectionOrder:n+1,purpose:'unknown',stage:'unknown',wording:[],phraseIds:[],navigationTaskIds:[],actualFinancialActionExecuted:false,...patch,title:count>1?patch.title+' · '+(n+1):patch.title};
   if(type==='phrases')normalized={...common,sourceKind:'reviewed_contribution',purpose:'unknown',stage:'unknown',screenIds:[],role:'ui_label',actualActionExecuted:false,...patch};
   if(type==='terms')normalized={id:targetId,datasetId:reviewedTermDataset,source:'검토 후 추가된 용어',recordType:'contributed_term',status:'operator_reviewed',koreanStatus:'operator_reviewed',layer:'reviewed',commercial:true,license:termRights!.license,commercialRights:termRights,generationEligible:false,approvedTranslation:null,approval:null,sourceConceptId:null,sourceUrl:patch.sourceUrl||null,...patch};
   if(type==='features')normalized={...common,workId:patch.workId,label:index.works.find((w:any)=>w.id===patch.workId)?.label,referenceId:targetId,status:'documented',absenceMeaning:'unknown',observedAppScreen:false,summaryKind:'WGSS_operator_review_not_verbatim_UI',...patch};
  }
  if(normalized.providerId)normalized.provider=index.providers.find((p:any)=>p.id===normalized.providerId)?.name;
  if(type==='terms'&&target&&termRights){normalized.commercialRights=termRights;normalized.license=termRights.license;}
  if(type==='terms'&&target){normalized.status='operator_reviewed';if('korean'in patch)normalized.koreanStatus='operator_reviewed';}
  if(photo){normalized.imageFileId=photo.id;normalized.imagePath='/api/wgss?resource=file&id='+encodeURIComponent(photo.id);normalized.originalSha=photo.sha256;normalized.sourceKind='reviewed_contribution';if(type==='screens'){Object.assign(normalized,{flowId:null,editorialGroupId:null,cohort:'contribution',purpose:'unknown',stage:'unknown',country:null,collectedAt:patch.capturedAt||null,publicationDate:null,appVersion:patch.appVersion||null,currentUiVersionVerified:false,actualFinancialActionExecuted:false,phraseIds:[],wording:[],hideLegacyPhrases:true});}if(type==='phrases')normalized.screenIds=[];}
  if(type==='screens'&&'taskId'in patch)normalized.navigationTaskIds=[];
  if(type==='features'){
   Object.assign(normalized,{summaryKind:'WGSS_operator_review_not_verbatim_UI',observedAppScreen:false,channelProofs:[],describedChannels:[]});
   const workId=patch.workId||previous?.patch.workId||original?.workId;
   if(!workId)throw new ApiError(400,'missing_work','연결할 업무 정의를 선택해 주세요.');normalized.workId=workId;normalized.label=index.works.find((w:any)=>w.id===workId)?.label;
   if('taskId'in normalized)normalized.taskIds=[normalized.taskId].filter(Boolean);
   if('sourceUrl'in patch||photo)normalized.evidence=[{url:patch.sourceUrl||normalized.imagePath,sourceKind:'operator_reviewed_reference',locator:'운영자 검토',collectedAt:null}];
  }
  if(type==='screens'&&plan.photoDetails){Object.assign(normalized,{id:targetId,collectionOrder:plan.photoDetails.collectionOrder,uploadedAt:photo.created_at,captureDateBasis:patch.captureDateBasis||'upload',capturedAt:patch.capturedAt,collectedAt:patch.capturedAt,captureDateVerified:false,purpose:patch.purpose||patch.stageLabel||'',stage:patch.stageLabel||''});await prepareDerived(env,actor,source,plan.photoDetails,normalized,photo,nextVersion,statements,entries);}else if(type==='screens'&&photo){normalized.id=targetId;await prepareDerived(env,actor,source,{},normalized,photo,nextVersion,statements,entries);}
  const pid=id(),revision=expected+1,time=now();statements.push(stmt(env,'INSERT INTO wgss_publications (id,target_type,target_id,revision,source_submission_id,source_version,patch_json,state,actor_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)',pid,type,targetId,revision,source.id,nextVersion,JSON.stringify(normalized),'applied',actorId(actor),time));entries.push({id:pid,type,targetId,revision});
 }
 return {statements,entries};
}


/** Upload day is a collection date supplied by this workflow, never a verified capture date. */
export function uploadDay(value:string){const timestamp=new Date(value);if(!Number.isFinite(timestamp.getTime()))throw new ApiError(400,'invalid_upload_date','사진 업로드 날짜를 확인할 수 없습니다.');return new Date(timestamp.getTime()+9*60*60*1000).toISOString().slice(0,10);}
function publicationStatement(env:Runtime,actor:Actor,source:any,nextVersion:number,type:EntityType,targetId:string,revision:number,patch:any){const pid=id();return {statement:stmt(env,'INSERT INTO wgss_publications (id,target_type,target_id,revision,source_submission_id,source_version,patch_json,state,actor_id,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)',pid,type,targetId,revision,source.id,nextVersion,JSON.stringify(patch),'applied',actorId(actor),now()),entry:{id:pid,type,targetId,revision}};}
async function prepareDerived(env:Runtime,actor:Actor,source:any,details:any,screen:any,photo:any,nextVersion:number,statements:any[],entries:any[]){
 if(!photo)throw new ApiError(400,'image_required','사진에 연결할 내용을 확인해 주세요.');
 // Supersede derived data in the same transaction as a replacement image. Version history stays intact.
 const current=(await appliedRecords(env)).items;
 for(const row of current.filter(r=>(r.type==='phrases'||r.type==='features')&&r.patch.derivedFromScreenId===screen.id)){
  const retired=publicationStatement(env,actor,source,nextVersion,row.type,row.targetId,row.revision+1,{retired:true,supersededAt:now(),supersededByImageFileId:photo.id});statements.push(retired.statement);entries.push(retired.entry);
 }
 const list=details.phrases??[];
 if(!Array.isArray(list)||list.length>100)throw new ApiError(400,'invalid_ocr','사진별 화면 문구는 100개까지 입력할 수 있습니다.');
 const sourceData={providerId:screen.providerId,provider:screen.provider,language:screen.language,taskId:screen.taskId,sourceUrl:screen.sourceUrl||null,collectedAt:screen.collectedAt||null,capturedAt:screen.capturedAt,captureDateBasis:screen.captureDateBasis,uploadedAt:photo.created_at,country:null,sourceKind:'reviewed_screen_ocr',derivedFromScreenId:screen.id,derivedFromImageSha:photo.sha256,imageFileId:photo.id,imagePath:screen.imagePath,originalSha:photo.sha256,actualActionExecuted:false,currentUiVersionVerified:false};
 const seen=new Set();screen.wording=[];screen.phraseIds=[];
 for(let n=0;n<list.length;n++){
  const value=list[n];if(!value||typeof value!=='object'||Array.isArray(value))throw new ApiError(400,'invalid_ocr','화면 문구 형식을 확인해 주세요.');
  const text=bounded(value.text,'text',1000,true),role=bounded(value.role||'ui_label','role',100),context=bounded(value.context||screen.stageLabel||'','context',5000);
  if(!['ui_label','button','heading','description','label','title','helper','error','navigation','body','link','message'].includes(role))throw new ApiError(400,'invalid_ocr_role','화면 문구의 쓰임을 확인해 주세요.');
  const key=text+'\u0000'+role;if(seen.has(key))continue;seen.add(key);
  const targetId=screen.id+':phrase:'+nextVersion+':'+n,patch={...sourceData,id:targetId,text,role,context,screenIds:[screen.id],purpose:screen.purpose||screen.stageLabel||'',stage:screen.stageLabel||'',retired:false};
  const publication=publicationStatement(env,actor,source,nextVersion,'phrases',targetId,1,patch);statements.push(publication.statement);entries.push(publication.entry);screen.phraseIds.push(targetId);screen.wording.push(text);
 }
 screen.hideLegacyPhrases=true;screen.derivedFeatureIds=[];
 if(details.feature===undefined||details.feature===null||details.feature===false)return;
 const value=details.feature;if(typeof value!=='object'||Array.isArray(value))throw new ApiError(400,'invalid_feature','화면에서 확인한 기능을 확인해 주세요.');
 const candidates=index.tasks.find((t:any)=>t.id===screen.taskId)?.workIds||[];
 const workId=bounded(value.workId|| (candidates.length===1?candidates[0]:''),'workId',200);
 if(!workId)throw new ApiError(400,'feature_work_required','이 화면의 기능에 해당하는 금융업무를 선택해 주세요.');
 if(!sets.workId.has(workId)||!candidates.includes(workId))throw new ApiError(400,'feature_work_conflict','선택한 화면 업무와 기능의 업무 정의가 다릅니다.');
 const expression=bounded(value.expression||screen.title,'expression',1000,true),meaning=bounded(value.meaning||screen.stageLabel||screen.purpose||'','meaning',5000);
 const targetId=screen.id+':feature:'+nextVersion,patch={...sourceData,id:targetId,workId,label:index.works.find((w:any)=>w.id===workId)?.label,taskIds:[screen.taskId],expression,meaning,conditions:'',referenceId:screen.id,screenIds:[screen.id],status:'screen_observed',observedAppScreen:true,absenceMeaning:'unknown',summaryKind:'reviewed_screen_UI_not_executed_function',evidence:[{url:screen.sourceUrl||screen.imagePath,imagePath:screen.imagePath,sourceKind:'reviewed_screen_ocr',collectedAt:screen.collectedAt,captureDateBasis:screen.captureDateBasis}],channelProofs:[],describedChannels:[],retired:false};
 const publication=publicationStatement(env,actor,source,nextVersion,'features',targetId,1,patch);statements.push(publication.statement);entries.push(publication.entry);screen.derivedFeatureIds.push(targetId);
}

export async function preparePublications(env:Runtime,actor:Actor,source:any,input:any,selectedFiles:string[],nextVersion:number){
 const plan=input.application;
 if(!plan||plan.photos===undefined)return prepareSinglePublication(env,actor,source,input,selectedFiles,nextVersion);
 requireActor(actor,true);
 if(plan.type!=='screens'||!Array.isArray(plan.photos)||!plan.photos.length||plan.photos.length>10)throw new ApiError(400,'invalid_photos','사진별 화면 정보를 확인해 주세요.');
 if(!plan.fields||typeof plan.fields!=='object'||Array.isArray(plan.fields))throw new ApiError(400,'invalid_fields','화면의 공통 내용을 확인해 주세요.');
 const photoIds=plan.photos.map((p:any)=>p?.fileId);
 if(new Set(photoIds).size!==photoIds.length||photoIds.some((fid:any)=>typeof fid!=='string'||!selectedFiles.includes(fid)))throw new ApiError(400,'photo_selection','개인정보를 검토한 사진을 한 번씩 선택해 주세요.');
 if(!Array.isArray(plan.imageFileIds)||plan.imageFileIds.length!==photoIds.length||plan.imageFileIds.some((fid:any)=>!photoIds.includes(fid)))throw new ApiError(400,'photo_selection','선택한 사진마다 화면 정보를 입력해 주세요.');
 if(plan.operation==='update'&&photoIds.length!==1)throw new ApiError(400,'one_replacement','기존 화면 교체에는 사진 한 장을 선택해 주세요.');
 const prepared={statements:[] as any[],entries:[] as any[]};
 for(let n=0;n<plan.photos.length;n++){
  const details=plan.photos[n];if(!details.fields||typeof details.fields!=='object'||Array.isArray(details.fields))throw new ApiError(400,'invalid_fields','사진별 화면 정보를 입력해 주세요.');
  if(!bounded(details.fields.title,'title',1000,true))throw new ApiError(400,'missing_field','사진마다 화면 이름을 입력해 주세요.');
  const file=await stmt(env,"SELECT * FROM wgss_files WHERE id=? AND submission_id=? AND role='masked'",details.fileId,source.id).first<any>();if(!file)throw new ApiError(400,'photo_not_owned','이 제안에 첨부된 가린 사진을 선택해 주세요.');
  const photoFields={...plan.fields,...details.fields};for(const key of ['title','providerId','language','taskId'])if(!photoFields[key])throw new ApiError(400,'missing_field','사진별 화면에 필요한 정보를 입력해 주세요: '+key);
  const basis=photoFields.captureDateBasis||'upload';if(!['upload','provided'].includes(basis))throw new ApiError(400,'invalid_date_basis','화면 날짜의 기준을 확인해 주세요.');
  if(basis==='upload')photoFields.capturedAt=uploadDay(file.created_at);else if(!photoFields.capturedAt)throw new ApiError(400,'invalid_date','직접 확인한 캡처일을 입력해 주세요.');
  photoFields.captureDateBasis=basis;
  const result=await prepareSinglePublication(env,actor,source,{...input,application:{...plan,fields:photoFields,imageFileIds:[details.fileId],photos:undefined,photoDetails:{...details,collectionOrder:n+1,uploadedAt:file.created_at}}},selectedFiles,nextVersion);
  prepared.statements.push(...result.statements);prepared.entries.push(...result.entries);
 }
 return prepared;
}
