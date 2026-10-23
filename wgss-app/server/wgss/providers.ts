import referenceIndex from './reference-index.json';
import {ApiError,Runtime,Actor,requireActor,rows,stmt,bounded,now,hash,auditStmt,parse} from './core';

export const providerKinds=['bank','payment','wallet','other'] as const;
const key=(value:string)=>value.normalize('NFKC').toLocaleLowerCase().replace(/[\s\p{P}]+/gu,'');
export async function providerList(env:Runtime){
 const registered=await rows(env,'SELECT id,name,kind,source_url,aliases_json FROM wgss_providers ORDER BY created_at,id');
 return [...referenceIndex.providers.map(p=>({...p,origin:'source',kind:'unspecified',aliases:[] as string[]})),...registered.map(p=>({id:p.id,name:p.name,kind:p.kind,sourceUrl:p.source_url||'',aliases:parse(p.aliases_json,[]),origin:'registered'}))];
}
export async function createProvider(env:Runtime,actor:Actor,input:any){
 requireActor(actor,true);
 const name=bounded(input.name,'name',120,true).trim(),kind=bounded(input.kind||'other','kind',30,true),sourceUrl=bounded(input.sourceUrl,'sourceUrl',2000);
 if(!key(name)||/[<>\x00-\x1f]/.test(name))throw new ApiError(400,'provider_name','회사·서비스 이름을 입력해 주세요.');
 if(!providerKinds.includes(kind as any))throw new ApiError(400,'provider_kind','회사·서비스 종류를 선택해 주세요.');
 if(input.aliases!==undefined&&(!Array.isArray(input.aliases)||input.aliases.length>10))throw new ApiError(400,'provider_aliases','다른 이름은 10개까지 입력할 수 있습니다.');
 const aliases=[...new Set((input.aliases||[]).map((a:any)=>bounded(a,'alias',120,true).trim()))] as string[];
 if(aliases.some(a=>!key(a)||/[<>\x00-\x1f]/.test(a)))throw new ApiError(400,'provider_aliases','다른 이름을 확인해 주세요.');
 if(sourceUrl){try{const u=new URL(sourceUrl);if(u.protocol!=='https:'||u.username||u.password)throw 0;}catch{throw new ApiError(400,'provider_url','공식 사이트는 HTTPS 주소를 입력해 주세요.');}}
 const choices=await providerList(env),keys=new Set([name,...aliases].map(key));
 const matches=choices.filter(p=>[p.id,p.name,...p.aliases].some(value=>keys.has(key(value))));
 if(matches.length>1)throw new ApiError(409,'provider_alias_conflict','입력한 이름들이 서로 다른 등록 항목과 겹칩니다. 기존 목록을 확인해 주세요.');
 if(matches.length)return {item:matches[0],reused:true};
 const normalized=key(name),providerId='registered-'+(await hash(normalized)).slice(0,24),time=now();
 try{await env.DB.batch([
  stmt(env,'INSERT INTO wgss_providers (id,name,normalized_name,kind,source_url,aliases_json,created_at,created_by) VALUES (?,?,?,?,?,?,?,?)',providerId,name,normalized,kind,sourceUrl,JSON.stringify(aliases),time,actor.userId||'service'),
  ...[...keys].map(name=>stmt(env,'INSERT INTO wgss_provider_names (normalized_name,provider_id) VALUES (?,?)',name,providerId)),
  auditStmt(env,actor,'provider.created',providerId,{name,kind,sourceUrl,aliases}),
 ]);}catch(error){const prior=(await providerList(env)).find(p=>[p.id,p.name,...p.aliases].some(value=>keys.has(key(value))));if(prior)return {item:prior,reused:true};throw error;}
 return {item:{id:providerId,name,kind,sourceUrl,aliases,origin:'registered'},reused:false};
}
