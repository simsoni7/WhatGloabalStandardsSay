'use strict';
window.WGSSPublic=(()=>{
 const config={"base":"/WhatGloabalStandardsSay/wgss/","backendBase":"https://wgss-case-library.booknfoto461.chatgpt.site","snapshotAt":"2026-10-15T16:38:10.336287+00:00"};let snapshot;
 const load=()=>snapshot||(snapshot=fetch(config.base+'approved-snapshot.json',{credentials:'omit'}).then(r=>{if(!r.ok)throw Error('공개 자료를 불러오지 못했습니다.');return r.json()}));
 async function fetchJSON(url,options={}){
  const u=new URL(url,location.href);
  if(u.pathname==='/api/wgss'){
   if(options.method&&options.method!=='GET')throw Error('제안과 관리는 운영 서버에서 이용해 주세요.');
   const resource=u.searchParams.get('resource');
   if(resource==='session')return {userId:null,role:'public_reader',publicSnapshot:true};
   const data=await load();
   if(resource==='publications')return {items:data.items};
   if(resource==='recordVersions'&&u.searchParams.get('type')==='screens')return {items:data.versions[u.searchParams.get('id')]||[]};
   throw Error('이 기능은 운영 서버에서 이용할 수 있습니다.');
  }
  if(['/integration-data/','/assets/','/workspace/'].some(p=>u.pathname.startsWith(p)))u.pathname=config.base+u.pathname.slice(1);
  const r=await fetch(u.href,{credentials:'omit',...options});if(!r.ok)throw Error('자료를 불러오지 못했습니다 ('+r.status+').');return r.json();
 }
 function handoff(kind,prefill={}){const ref=prefill.referenceId;const target=new URL('/workspace/',config.backendBase);target.hash=ref?'screens':kind==='admin'?'admin':'contribute';if(ref)target.searchParams.set('reference',ref);document.querySelector('#app').innerHTML='<section class="intro"><h1>'+(kind==='admin'?'자료 관리':'자료 제안')+'</h1><p>현재 제안 접수와 관리는 운영 계정에서 사용할 수 있습니다.</p><p>공개 화면에서는 금융사의 화면과 표현을 로그인 없이 찾아볼 수 있습니다.</p><a class="button primary" target="_blank" rel="noopener noreferrer" href="'+target.href+'">운영 서버에서 열기</a> <a class="text-button" href="#screens">레퍼런스 찾기로 돌아가기</a></section>';}
 return {fetchJSON,handoff,config};
})();
