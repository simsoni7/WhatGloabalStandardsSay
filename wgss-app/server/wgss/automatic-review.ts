import {ApiError,Actor,Runtime,stmt,rows,serializeSubmission,submission,bounded,now,id} from './core';
import {updateSubmission,createSubmission} from './submissions';

export const qualityActor:Actor={userId:'wgss-bedrock-quality-agent',role:'admin',service:true};
const encoder=new TextEncoder();
export async function verifyAutomaticRequest(request:Request,env:Runtime,body=''){
 const timestamp=request.headers.get('X-WGSS-Automation-Timestamp')||'',signature=request.headers.get('X-WGSS-Automation-Signature')||'';
 if(!env.BEDROCK_API_KEY||!/^\d{10}$/.test(timestamp)||Math.abs(Date.now()/1000-Number(timestamp))>300||!/^[0-9a-f]{64}$/.test(signature))throw new ApiError(401,'automation_signature','자동 검수 요청을 확인할 수 없습니다.');
 const url=new URL(request.url),message=['wgss-quality-v1',timestamp,request.method,url.pathname+url.search,body].join('\n');
 const key=await crypto.subtle.importKey('raw',encoder.encode(env.BEDROCK_API_KEY),{name:'HMAC',hash:'SHA-256'},false,['verify']);
 const bytes=Uint8Array.from(signature.match(/../g)!.map(x=>parseInt(x,16)));
 if(!await crypto.subtle.verify('HMAC',key,bytes,encoder.encode(message)))throw new ApiError(401,'automation_signature','자동 검수 서명이 일치하지 않습니다.');
}
export async function automaticQueue(env:Runtime){
 const items=await rows(env,"SELECT * FROM wgss_submissions WHERE status IN ('pending','held') ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END,created_at LIMIT 100");
 return {items:await Promise.all(items.map(x=>serializeSubmission(env,x)))};
}
export async function ingestAutomaticTerm(env:Runtime,input:any){
 if(!/^[0-9a-f]{64}$/.test(input.candidateKey||'')||!input.termEnglish||!input.termTarget)throw new ApiError(400,'automatic_material','원문 대응이 있는 검수 대상 용어가 필요합니다.');
 const u=new URL(input.sourceUrl||'');if(u.hostname!=='raw.githubusercontent.com'||!/^\/(unicode-org\/cldr-json|apache\/ofbiz-framework)\/[0-9a-f]{40}\//.test(u.pathname))throw new ApiError(400,'automatic_source','확인한 공식 원천 자료만 자동 접수합니다.');
 return createSubmission(env,qualityActor,{...input,kind:'text',proposalType:'term'});
}
export async function applyAutomaticReview(env:Runtime,input:any){
 const source=await submission(env,qualityActor,bounded(input.id,'id',100,true),true);
 if(!['pending','held'].includes(source.status))throw new ApiError(409,'not_reviewable','이미 처리된 자료입니다.');
 const q=input.quality;
 if(!q||!['claude-sonnet-5','claude-opus-5'].includes(q.model)||q.decision!=='approve'||typeof q.confidence!=='number'||q.confidence<0.95||q.confidence>1||q.privacyClear!==true||q.readable!==true||!Array.isArray(q.evidence)||!q.evidence.length||q.evidence.length>12)throw new ApiError(400,'quality_gate','자동 게시 기준을 충족하지 못했습니다.');
 for(const e of q.evidence)if(typeof e.url!=='string'||!/^https:\/\//.test(e.url)||!/^[0-9a-f]{64}$/.test(e.sha256||''))throw new ApiError(400,'quality_evidence','검수한 원문·이미지 근거가 필요합니다.');
 if(input.application?.type==='terms'&&!input.application.fields?.korean?.trim())throw new ApiError(400,'korean_required','한국어 설명을 확인한 후 자동 게시할 수 있습니다.');
 const quality={model:q.model,decision:'approve',confidence:q.confidence,evidence:q.evidence,reviewedAt:now(),method:'bedrock_evidence_review',koreanBasis:['source_korean_reused','ai_quality_reviewed'].includes(q.koreanBasis)?q.koreanBasis:null,koreanSourceUrl:typeof q.koreanSourceUrl==='string'&&/^https:\/\//.test(q.koreanSourceUrl)?q.koreanSourceUrl:null};
 const result=await updateSubmission(env,qualityActor,{...input,decision:'approved',reason:'Bedrock 품질검수 통과 · 원문·한국어 설명·이용 조건 확인',privacyReviewed:true,readabilityReviewed:true,automaticQuality:quality},true);
 await stmt(env,"INSERT INTO wgss_jobs (id,kind,actor_id,submission_id,status,model,result_json,created_at,completed_at) VALUES (?,?,?,?,?,?,?,?,?)",id(),'quality_gate',qualityActor.userId,source.id,'completed',q.model,JSON.stringify(quality),quality.reviewedAt,now()).run();
 return result;
}
export async function deferAutomaticReview(env:Runtime,input:any){
 const reason=bounded(input.reason,'reason',1800,true),source=await submission(env,qualityActor,bounded(input.id,'id',100,true),true);
 if(!['pending','held'].includes(source.status))throw new ApiError(409,'not_reviewable','이미 처리된 자료입니다.');
 const last=await stmt(env,'SELECT review_reason FROM wgss_versions WHERE submission_id=? AND version=?',source.id,source.version).first<any>();
 if(source.status==='held'&&last?.review_reason===reason)return {item:await serializeSubmission(env,source),reused:true};
 return updateSubmission(env,qualityActor,{id:source.id,expectedVersion:input.expectedVersion,decision:'held',reason,privacyReviewed:false,readabilityReviewed:false},true);
}
