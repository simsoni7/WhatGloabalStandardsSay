import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const source=await readFile(new URL('../deployment/public-intake/dist/server/index.js',import.meta.url),'utf8');
const {default:worker}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const original=globalThis.fetch,calls=[];
try{
 globalThis.fetch=async url=>{calls.push(String(url));if(String(url).startsWith('https://3.36.58.188/'))throw Error('IP egress unavailable');return Response.json({screens:[{imagePath:'/WhatGloabalStandardsSay/wgss/assets/test.png'}],dictionary:{chunks:[{path:'/WhatGloabalStandardsSay/wgss/integration-data/terms/001.json'}]}});};
 const r=await worker.fetch(new Request('https://intake.test/integration-data/catalog.json'),{});assert.equal(r.status,200);const json=await r.json();assert.equal(calls.length,2);assert(json.screens[0].imagePath.startsWith('https://simsoni7.github.io/'));assert(json.dictionary.chunks[0].path.startsWith('https://simsoni7.github.io/'));
 globalThis.fetch=async()=>new Response('unavailable',{status:503});assert.equal((await worker.fetch(new Request('https://intake.test/integration-data/catalog.json'),{})).status,502);
 console.log('Native catalogue fallback and matching source origins: passed');
}finally{globalThis.fetch=original;}
