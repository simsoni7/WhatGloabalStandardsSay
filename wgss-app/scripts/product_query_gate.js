'use strict';
// Uses production search code against an independent source inventory and semantic oracle.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const R=path.resolve(__dirname,'..'),core=require(path.join(R,'dist/backbone-core.js')),K=JSON.parse(fs.readFileSync(path.join(R,'dist/data/business-backbone.json'))),spec=JSON.parse(fs.readFileSync(path.join(R,'data/product-query-fixtures.json'))),results=[],issues=[];
const record=(query,kind,fn)=>{try{fn();results.push({query,kind,status:'passed'})}catch(e){issues.push({query,kind,error:e.message});results.push({query,kind,status:'failed'})}};
for(const row of K.product_inventory)record(row.term,'source-inventory',()=>{
 const profiles=core.products(K,row.term),goals=core.goals(K,row.term),gaps=core.inventory(K,row.term);
 if(row.disposition==='mapped'){assert(row.profile_ids.every(id=>profiles.some(p=>p.id===id)));assert(row.goal_ids.every(id=>goals.some(g=>g.id===id)))}
 else assert(gaps.some(g=>g.id===row.id),'known source term disappeared instead of visible gap');
});
for(const row of spec.cases)record(row.query,row.kind,()=>{
 const actual=core.productQuery(K,row.query),ids=actual.profiles.map(p=>p.id);
 if(row.kind==='product'){
  assert(row.expected_profiles.every(id=>ids.includes(id)),'intended product missing: '+ids);
  assert(!row.forbidden_profiles.some(id=>ids.includes(id)),'unrelated product matched: '+ids);
  if(row.expected_intent)assert.equal(actual.intent,row.expected_intent);
  if(row.unrecognized)assert.equal(actual.unrecognized,true,'unmatched action must not silently select a result');
 }else if(row.kind==='inventory-gap')assert(core.inventory(K,row.query).some(i=>i.term===row.expected_term));
 else if(row.kind==='goal')assert(core.goals(K,row.query).some(g=>g.id===row.expected_goal));
 else {assert.equal(ids.length,0);assert.equal(core.inventory(K,row.query).length,0);assert.equal(core.goals(K,row.query).length,0)}
});
const digest=names=>crypto.createHash('sha256').update(names.map(name=>fs.readFileSync(path.join(R,name))).join('|')).digest('hex');
const report={version:spec.version,scope:spec.scope,status:issues.length?'failed':'passed',source_fingerprint:digest(['data/product-profiles-review.json','data/product-vocabulary-inventory.json','data/product-query-fixtures.json','dist/backbone-core.js','dist/data/operations.json','data/business-backbone-review.json']),query_count:new Set(results.map(r=>r.query)).size,checks:results.length,source_inventory_checks:K.product_inventory.length,practitioner_checks:spec.cases.length,issues,results,semantic_mece_approved:false,full_screen_coverage_approved:false};
if(process.argv.includes('--write'))fs.writeFileSync(path.join(R,'data/product-discoverability-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({...report,results:undefined}));if(issues.length)process.exitCode=1;
