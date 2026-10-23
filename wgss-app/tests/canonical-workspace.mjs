import assert from 'node:assert/strict';
import {canonicalWorkspaceRedirect} from '../lib/canonical-workspace.mjs';
const official='https://3.36.58.188/WhatGloabalStandardsSay/wgss/';
for(const path of ['/', '/workspace', '/workspace/', '/workspace/index.html']){
 for(const method of ['GET','HEAD']){
  const response=canonicalWorkspaceRedirect(new Request('https://former.example'+path+'?tab=screens&reference=sample%3Aone',{method}));
  assert.equal(response.status,302);
  assert.equal(response.headers.get('Location'),official+'?tab=screens&reference=sample%3Aone');
  assert.equal(response.headers.get('Cache-Control'),'no-store');
 }
}
for(const path of ['/api/wgss','/integration-data/catalog.json','/public-screens','/workspace/app.js','/data/coverage.json'])assert.equal(canonicalWorkspaceRedirect(new Request('https://former.example'+path)),null);
assert.equal(canonicalWorkspaceRedirect(new Request('https://former.example/workspace/',{method:'POST'})),null);
console.log('Canonical entry: 14 route checks passed; historical routes and API retained');
