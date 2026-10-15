import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile} from 'node:fs/promises';
const root=new URL('../../',import.meta.url),dictionary=await readFile(new URL('integration-ui/dictionary.js',root),'utf8'),publications=await readFile(new URL('integration-ui/publications.js',root),'utf8');
const esc=value=>String(value??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
test('approved commercial contributed terms appear with the three expressions; rejected rights stay hidden',()=>{
 const state={catalog:{dictionary:{datasets:[{id:'allowed',commercial:true,layer:'core'}]}},terms:[{id:'new',datasetId:'wgss_reviewed_terms',commercial:true,layer:'reviewed',commercialRights:{confirmed:true,reviewSha:'a'.repeat(64)},english:'Open account',korean:'계좌 개설',target:'Open an account',language:'en'},{id:'blocked',datasetId:'mongolbank',english:'Must stay hidden',layer:'core'}],wordMode:'terms',termPage:1};
 const context=vm.createContext({state,arr:x=>Array.isArray(x)?x:[],esc,termMatches:()=>true,labelFor:()=> '영어',openDialog(){},link:()=>''});vm.runInContext(dictionary+';globalThis.dictionary=WGSSDictionary;',context);
 const html=context.dictionary.termsMarkup();assert(html.includes('Open account'));assert(html.includes('계좌 개설'));assert(html.includes('Open an account'));assert(html.includes('검토 후 추가된 용어'));assert(!html.includes('Must stay hidden'));
 state.terms=[];const empty=context.dictionary.termsMarkup();assert(empty.includes('검색된 용어가 없습니다.'));assert(empty.includes('data-action="add-search-material" data-kind="terms"'));
});
test('term-review form prefills the submitted expressions and records an explicit commercial review',async()=>{
 const nodes={'#apply-type':{value:'terms'},'#apply-operation':{value:'add'},'#apply-fields':{},'#apply-target-field':{},'#apply-preview':{}},state={reviewItem:{kind:'translation_issue',title:'계좌 개설',current:{proposalType:'term',termEnglish:'Open account',termKorean:'계좌 개설',termTarget:'Open an account',language:'en',sourceUrl:'https://example.org/terms'}},catalog:{providers:[],tasks:[],languages:[{id:'en',label:'영어'}],canonicalWorks:[],screens:[],phrases:[],features:[]},terms:[]};
 const context=vm.createContext({state,document:{addEventListener(){}},$:key=>nodes[key],$$:()=>[],arr:x=>Array.isArray(x)?x:[],esc,optionList:()=>'',labelFor:()=> '영어',link:()=>'',FormData:class{getAll(){return []}}});vm.runInContext(publications+';globalThis.applied=WGSSApplied;',context);await context.applied.mount();
 assert(nodes['#apply-fields'].innerHTML.includes('value="Open account"'));assert(nodes['#apply-fields'].innerHTML.includes('>계좌 개설</textarea>'));assert(nodes['#apply-fields'].innerHTML.includes('>Open an account</textarea>'));assert(nodes['#apply-fields'].innerHTML.includes('id="apply-rights-confirmed"'));
 Object.assign(nodes,{'#apply-rights-confirmed':{checked:true},'#apply-rights-license':{value:'CC0-1.0'},'#apply-rights-url':{value:'https://example.org/license'},'#apply-rights-basis':{value:'Original material dedicated under CC0.'}});
 const application=context.applied.application({});assert.equal(application.type,'terms');assert.equal(application.commercialRights.confirmed,true);assert.equal(application.commercialRights.license,'CC0-1.0');assert.equal(application.commercialRights.evidenceUrl,'https://example.org/license');
});
