'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),core=require(path.join(root,'dist/backbone-core.js'));
const k=JSON.parse(fs.readFileSync(path.join(root,'dist/data/business-backbone.json'))),d=JSON.parse(fs.readFileSync(path.join(root,'dist/data/operations.json'))),b=JSON.parse(fs.readFileSync(path.join(root,'dist/data/library.json'))),by=Object.fromEntries(d.works.map(w=>[w.id,w]));let checks=0;
const check=(name,ok)=>{assert.ok(ok,name);checks++;};
check('all canonical IDs accessible without restricting to observed examples',k.works.length===d.works.length&&new Set(k.works.map(w=>w.id)).size===d.works.length);
check('primary family partition does not claim semantic MECE',Object.values(k.counts_by_family).reduce((a,c)=>a+c,0)===d.works.length&&k.whole_mece_approved===false);
check('all curated paths resolve',k.goals.every(g=>g.canonical_work_ids.concat(g.optional_work_ids).every(i=>by[i])));
check('all family links resolve',k.works.every(w=>k.families.some(f=>f.id===w.family_id)));
const found=q=>core.goals(k,q,'');
for(const q of ['송금','송금하기','돈 보내기'])check(q+' exposes initiation and both geographic contexts',['goal-send-money-init','goal-domestic-transfer','goal-international-transfer'].every(i=>found(q).some(g=>g.id===i)));
for(const [q,i] of [['국내송금','goal-domestic-transfer'],['해외송금','goal-international-transfer'],['내계좌이체','goal-own-account-transfer'],['계좌 개설','goal-account-open'],['카드 신청','goal-card-apply'],['주식매수','goal-securities-order'],['펀드 환매','goal-fund-redeem']])check(q+' reaches its intended path',found(q).some(g=>g.id===i));
const contexts=k.goals.filter(g=>['goal-send-money-init','goal-domestic-transfer','goal-international-transfer','goal-own-account-transfer'].includes(g.id));
check('domestic overseas and ownership paths reuse one canonical instruction',contexts.every(g=>g.canonical_work_ids.length===1&&g.canonical_work_ids[0]==='WGSS-DF4BF34CD9B3'));
check('initiation never borrows status or cancellation evidence',contexts.every(g=>g.reference_task_ids.length===0));
check('overseas never makes FX execution mandatory',k.goals.find(g=>g.id==='goal-international-transfer').canonical_work_ids.every(i=>i!=='WGSS-38FCE46AB7D8'));
for(const [name,facts,expected] of [
 ['crossborder samecurrency',{origin_jurisdiction:'US',destination_jurisdiction:'GB',pay_currency:'USD',receive_currency:'USD',fx_required:false},{geography:'cross_border',fx:'not_required'}],
 ['domestic foreigncurrency',{origin_jurisdiction:'KR',destination_jurisdiction:'KR',pay_currency:'USD',receive_currency:'USD',fx_required:false},{geography:'domestic',fx:'not_required'}],
 ['nationality insufficient',{payer_nationality:'KR',recipient_nationality:'US',pay_currency:'KRW',receive_currency:'USD'},{geography:'unknown',fx:'unknown'}],
 ['one jurisdiction missing',{origin_jurisdiction:'US'},{geography:'unknown',fx:'unknown'}],
 ['currency difference is not observed FXexecution',{origin_jurisdiction:'KR',destination_jurisdiction:'KR',pay_currency:'KRW',receive_currency:'USD'},{geography:'domestic',fx:'unknown'}],
 ['explicit exchange adds independent outcome',{origin_jurisdiction:'US',destination_jurisdiction:'GB',fx_required:true},{geography:'cross_border',fx:'required'}]]){
 const actual=core.transferContext(facts);check(name,Object.entries(expected).every(([key,value])=>actual[key]===value)&&actual.canonical_work_ids[0]==='WGSS-DF4BF34CD9B3');
}
check('instruction submission does not assert recipient credited',by['WGSS-DF4BF34CD9B3'].outcome_key==='submit_credit_transfer_instruction'&&by['WGSS-DF4BF34CD9B3'].excludes.some(s=>s.includes('수취인 입금')));
check('payment funding not final interbank settlement',by['WGSS-96C318236155'].outcome_key==='make_funds_available_for_payment_rail_settlement'&&by['WGSS-96C318236155'].excludes.some(s=>s.includes('최종 결제')));
check('indicative FX information distinct from currency exchange',by['WGSS-BACKBONE-FX-QUOTE'].object_key!==by['WGSS-38FCE46AB7D8'].object_key&&by['WGSS-BACKBONE-FX-QUOTE'].discriminator==='information_only_not_binding_quote_or_currency_exchange');
check('pending cancellation not post execution recall',by['WGSS-3755DC0A622A'].object_key!==by['WGSS-BF2EC9C9E0D9'].object_key&&by['WGSS-BF2EC9C9E0D9'].excludes.some(s=>s.includes('입금 완료')));
check('standing order not debit mandate',by['WGSS-B6D7A72FE1F6'].object_key!==by['WGSS-A2A55984D53B'].object_key);
check('positive intent indexing does not search negated exclusions',!core.works(k,'구속력 있는 개별 거래 견적 수락','').some(w=>w.id==='WGSS-BACKBONE-FX-QUOTE'));
check('partial expert prompts cannot declare existing mandate missing',Boolean(by['WGSS-B5B544940BAB']));
check('book transfer responsibility and source-backed insurance formation stages remain distinct',by['WGSS-F92805EAE41E'].layer==='institution'&&by['WGSS-F92805EAE41E'].actor_role==='account_servicer'&&by['WGSS-ECD7907DE4BA'].outcome_key==='submit_insurance_proposal'&&by['WGSS-MECE-INSURANCE-ACCEPTANCE'].outcome_key==='form_insurance_contract_by_acceptance'&&by['WGSS-ECD7907DE4BA'].refs.some(r=>r.id==='WGSS-PROCESS-KR_INSURANCE_FORMATION'));
check('no provider evidence or native app observations invented',b.counts.provider_features===21&&b.counts.native_app_captures===0&&d.audit.new_provider_collection_allowed===false);
console.log(JSON.stringify({status:'passed',checks,canonical_count:k.canonical_count,navigation_paths:k.path_count,whole_mece_approved:false}));
