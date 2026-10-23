// Keep the former workspace entry tied to the official reader and review queue.
// Leave historical routes and private service/data bindings untouched.
const paths=new Set(['/', '/workspace', '/workspace/', '/workspace/index.html']);
export const officialWorkspaceUrl='https://3.36.58.188/WhatGloabalStandardsSay/wgss/';
export function canonicalWorkspaceScript(){
  return 'location.replace('+JSON.stringify(officialWorkspaceUrl)+'+location.search+location.hash);\n';
}
export function canonicalWorkspaceDocument(version=''){
  return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>WGSS</title><script src="/workspace/canonical-entry.js?v='+version+'"></script><noscript><meta http-equiv="refresh" content="0;url='+officialWorkspaceUrl+'"></noscript></head><body><p><a href="'+officialWorkspaceUrl+'">WGSS 열기</a></p></body></html>\n';
}
export function canonicalWorkspaceRedirect(request){
  const from=new URL(request.url);
  if(!['GET','HEAD'].includes(request.method)||!paths.has(from.pathname))return null;
  const destination=new URL(officialWorkspaceUrl);
  destination.search=from.search;
  return new Response(null,{status:302,headers:{Location:destination.href,'Cache-Control':'no-store'}});
}
