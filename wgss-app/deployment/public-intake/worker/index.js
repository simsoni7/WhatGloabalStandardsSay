import {handleIntake} from '../../../server/intake.ts';
import {getActor} from '../../../server/wgss/core.ts';
import assets from './assets.json';
import governance from './governance.json';
const defaultPublicBase='https://3.36.58.188/WhatGloabalStandardsSay/wgss/';
function absolute(value,readerBase=defaultPublicBase){if(Array.isArray(value))return value.map(v=>absolute(v,readerBase));if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,absolute(v,readerBase)]));if(typeof value==='string'&&value.startsWith('/WhatGloabalStandardsSay/wgss/'))return new URL(value,readerBase).href;return value;}
export default {async fetch(request,env){
 const publicBase=env.WGSS_PUBLIC_READER_BASE||defaultPublicBase;
 const url=new URL(request.url);
 if(url.pathname==='/api/wgss'){
  if(url.searchParams.get('resource')==='governance'){
   const actor=getActor(request.headers.get('oai-authenticated-user-id'),{...env,WGSS_PRIVATE_SERVICE_ACCESS:'false'},request.headers.get('oai-authenticated-user-email'));
   return actor.role==='admin'?Response.json(governance,{headers:{'Cache-Control':'no-store'}}):Response.json({error:'관리자 권한이 필요합니다.'},{status:403});
  }
  return handleIntake(request,env);
 }
 if(url.pathname==='/health')return Response.json({service:'wgss-public-intake',ready:true,rateLimitIdentity:request.headers.has('cf-connecting-ip')?'per-address':'shared-fallback'});
 if(url.pathname==='/integration-data/catalog.json'){
  // Some Worker egress paths cannot fetch an IP-literal origin. The preserved
  // public mirror supplies identical base data; approvals still use this API.
  for(const reader of [...new Set([publicBase,'https://simsoni7.github.io/WhatGloabalStandardsSay/wgss/'])]){
   try{const response=await fetch(reader+'integration-data/catalog.json',{cache:'no-store',signal:AbortSignal.timeout(5000)});if(response.ok)return Response.json(absolute(await response.json(),reader));}catch{}
  }
  return new Response('공개 자료를 불러오지 못했습니다.',{status:502});
 }
 if(url.pathname==='/workspace'||url.pathname==='/workspace/')return new Response(assets['index.html'],{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'}});
 const name=url.pathname.replace(/^\/workspace\//,'');
 if(url.pathname.startsWith('/workspace/')&&Object.hasOwn(assets,name))return new Response(assets[name],{headers:{'Content-Type':name.endsWith('.js')?'application/javascript; charset=utf-8':name.endsWith('.css')?'text/css; charset=utf-8':'application/json; charset=utf-8','X-Content-Type-Options':'nosniff'}});
 return Response.redirect(publicBase,302);
}};
