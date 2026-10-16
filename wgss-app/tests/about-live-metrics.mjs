import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import vm from 'node:vm';

const root=resolve(import.meta.dirname,'..');
const context=vm.createContext({URL,URLSearchParams,location:{search:'',origin:'https://example.test'},document:{addEventListener(){}}});
// Load production definitions without starting network or browser event handlers.
const app=await readFile(resolve(root,'integration-ui/app.js'),'utf8');
vm.runInContext(app.slice(0,app.indexOf("window.addEventListener('hashchange'")),context);
for(const name of ['publications.js','dictionary.js','about.js'])vm.runInContext(await readFile(resolve(root,'integration-ui',name),'utf8'),context);
const run=code=>vm.runInContext(code,context);
const checked=[];
function check(name,condition){assert.ok(condition,name);checked.push(name);}

const base={dictionary:{datasets:[{id:'official',commercial:true,layer:'core',count:2},{id:'blocked',commercial:false,layer:'core',count:900}],chunks:[{path:'/terms/one',layer:'core',datasetIds:['official'],languageCounts:{es:1,ko:1}},{path:'/terms/blocked',layer:'core',datasetIds:['blocked'],languageCounts:{zz:900}}]},screens:[{id:'one',providerId:'citi',originalSha:'image-one'},{id:'two',providerId:'citi',originalSha:'image-one'},{id:'three',providerId:'wise',originalSha:'image-two'}],phrases:[{id:'phrase-one'}],features:[],counts:{dictionaryTotal:902},providers:Array.from({length:50},(_,i)=>({id:'provider-'+i}))};
context.fixture=base;
run('WGSSApplied.initialize(fixture)');
const baseline=run('WGSSAbout.metrics(state.catalog,state.terms)');
check('counts only commercially permitted core pairs',baseline.dictionaryRows===2&&baseline.languageCount===2&&!baseline.languageCounts.has('zz'));
check('counts providers with screens rather than all provider metadata',baseline.screenProviders===2);
check('counts shared image hashes once and screen cases separately',baseline.uniqueImages===2&&baseline.screens.length===3);

context.extension={id:'new-source',commercial:true,layer:'core',count:3};
run("fixture.dictionary.datasets.push(extension);fixture.dictionary.chunks.push({path:'/terms/new',layer:'core',datasetIds:['new-source'],languageCounts:{fr:2,es:1}});fixture.screens.push({id:'four',providerId:'new-bank',originalSha:'image-three'});WGSSApplied.initialize(fixture)");
const expanded=run('WGSSAbout.metrics(state.catalog,state.terms)');
check('new source and language metadata update automatically',expanded.dictionaryRows===5&&expanded.languageCount===3&&expanded.datasets.length===2&&expanded.languageCounts.get('es')===2);
check('new financial company and image update automatically',expanded.screenProviders===3&&expanded.uniqueImages===3&&expanded.screens.length===4);

const reviewed={id:'contribution:terms:approved',datasetId:'wgss_reviewed_terms',recordType:'contributed_term',layer:'reviewed',commercial:true,english:'Account',target:'Konto',language:'de',commercialRights:{confirmed:true,license:'CC0-1.0',basis:'Synthetic rights evidence for regression testing.',evidenceUrl:'https://example.test/rights',reviewedAt:'2026-10-16T00:00:00Z',reviewSha:'a'.repeat(64)}};
context.publications=[{type:'terms',targetId:reviewed.id,revision:1,patch:reviewed},{type:'terms',targetId:'official:1',revision:1,patch:{target:'Corrected existing term'}}];
run('fetchJSON=async()=>({items:publications})');
await run('WGSSApplied.refresh()');
const beforeChunks=run('WGSSAbout.metrics(state.catalog,state.terms)');
check('approved new pair is counted before lazy chunks load',beforeChunks.dictionaryRows===6&&beforeChunks.reviewedTermCount===1&&beforeChunks.languageCount===4&&beforeChunks.languageCounts.get('de')===1);
context.loadedRows=[{id:'official:1',datasetId:'official',layer:'core',language:'es',english:'Account',target:'Cuenta'},{id:'official:2',datasetId:'official',layer:'core',language:'ko',english:'Account',target:'계좌'}];
run('WGSSApplied.ingestTerms(loadedRows)');
const afterChunks=run('WGSSAbout.metrics(state.catalog,state.terms)');
check('loading dictionary chunks and existing corrections cannot inflate totals',afterChunks.dictionaryRows===beforeChunks.dictionaryRows&&afterChunks.languageCount===beforeChunks.languageCount);
check('repeated added record IDs count once',run('WGSSAbout.metrics(state.catalog,[...state.terms,...state.terms]).reviewedTermCount')===1);
check('approved additions remain separate from institutional source count',afterChunks.datasets.length===2);
run("state.query='Konto';state.language='de'");
check('approved term passes the normal search and language filter',run('WGSSDictionary.visibleRows().length===1&&WGSSDictionary.visibleRows()[0].id===publications[0].targetId'));
run("state.language='es'");
check('approved term still respects the selected language',run('WGSSDictionary.visibleRows().length===0'));
for(const patch of [{commercial:false},{layer:'conditional'},{datasetId:'unreviewed'},{id:'not-a-contribution'},{commercialRights:{...reviewed.commercialRights,confirmed:false}},{commercialRights:{...reviewed.commercialRights,license:'CC-BY-NC-4.0'}},{commercialRights:{...reviewed.commercialRights,reviewSha:''}},{commercialRights:{...reviewed.commercialRights,evidenceUrl:'http://example.test/rights'}}]){
 context.invalid={...reviewed,...patch};
 check('unapproved or restricted term rejected: '+JSON.stringify(patch),run('!allowedTerm(invalid)&&WGSSAbout.metrics(state.catalog,[invalid]).reviewedTermCount===0'));
}
run("fixture.dictionary.chunks.push({path:'/terms/mixed',layer:'core',datasetIds:['official','blocked'],languageCounts:{zz:100}});fixture.dictionary.datasets[0].count++;WGSSApplied.initialize(fixture)");
const mixed=run('WGSSAbout.metrics(state.catalog,state.terms)');
check('mixed chunks do not advertise blocked target languages',!mixed.languageCounts.has('zz')&&mixed.languageCount===null&&!mixed.languageTotalsComplete);

// Verify real source metadata against the admitted original chunk rows. This
// automatically covers every newly registered dataset instead of freezing 16,424.
const catalog=JSON.parse(await readFile(resolve(root,'integration-data/catalog.json'),'utf8'));
const admitted=new Set(catalog.dictionary.datasets.filter(d=>d.commercial===true&&d.layer==='core').map(d=>d.id));
const counts=new Map(),languages=new Map(),chunks=[];
for(const chunk of catalog.dictionary.chunks){
 const rows=JSON.parse(await readFile(resolve(root,chunk.path.replace(/^\//,'')),'utf8')).rows.filter(r=>admitted.has(r.datasetId));
 if(!rows.length)continue;
 const languageCounts={};
 for(const row of rows){assert.equal(row.layer,'core');counts.set(row.datasetId,(counts.get(row.datasetId)||0)+1);languages.set(row.language,(languages.get(row.language)||0)+1);languageCounts[row.language]=(languageCounts[row.language]||0)+1;}
 chunks.push({...chunk,datasetIds:[...new Set(rows.map(r=>r.datasetId))],languageCounts});
}
catalog.dictionary.datasets=catalog.dictionary.datasets.filter(d=>admitted.has(d.id)&&counts.has(d.id));
for(const dataset of catalog.dictionary.datasets)assert.equal(dataset.count,counts.get(dataset.id),'Dataset metadata drift: '+dataset.id);
catalog.dictionary.chunks=chunks;
context.actual=catalog;
const actual=run('WGSSAbout.metrics(actual,[])');
check('real admitted pair total equals original source rows',actual.dictionaryRows===[...counts.values()].reduce((a,b)=>a+b,0));
check('real language graph equals original admitted languages',actual.languageTotalsComplete&&actual.languageCount===languages.size&&[...languages].every(([id,count])=>actual.languageCounts.get(id)===count));
console.log(JSON.stringify({status:'passed',checks:checked.length,realPublic:{pairs:actual.dictionaryRows,languages:actual.languageCount,datasets:actual.datasets.length,screens:actual.screens.length,screenProviders:actual.screenProviders,uniqueImages:actual.uniqueImages},items:checked},null,2));
