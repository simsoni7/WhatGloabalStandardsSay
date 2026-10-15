"""Check real boundary regressions rather than editorial count targets."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
data=json.loads((R/'dist/data/operations.json').read_text())
by={w['id']:w for w in data['works']}
checks=0
def check(ok, message):
    global checks
    assert ok, message
    checks+=1
insurance=[by[i] for i in ['WGSS-ECD7907DE4BA','WGSS-72879CC650A0','WGSS-MECE-INSURANCE-ACCEPTANCE','WGSS-4E2F205250BC']]
check(len({w['outcome_key'] for w in insurance})==4, 'proposal / risk decision / acceptance / document are distinct')
check('ownership' not in by['WGSS-B41573DD9A49']['outcome_key'] and 'key_control' in by['WGSS-B41573DD9A49']['outcome_key'], 'key control does not assert asset ownership')
check(by['WGSS-CE6010277573']['object_key']!=by['WGSS-B9749BC4EE73']['object_key'], 'personal data consent is not payment authority')
check(all(not any(r['id'].endswith(':41780') for r in by[i]['refs']) for i in ['WGSS-CE6010277573','WGSS-9798312430EF']), 'wrong payment-consent source removed')
check(by['WGSS-CE6010277573']['actor_role']=='data_subject', 'administrator cannot grant another person consent')
check(by['WGSS-D8EDFDFBAFAC']['object_key']!=by['WGSS-DC21011E8515']['object_key'] and by['WGSS-D8EDFDFBAFAC']['outcome_key']=='determine_collateral_asset_eligibility', 'collateral eligibility and value are distinct results')
check('WGSS-1B39BB0943F9' not in by and 'WGSS-992EB3CF75F6' not in by, 'settlement and authentication viewpoint clones removed')
check('WGSS-0C78B43732B6' not in by and all(i in by for i in ['WGSS-B3C21A43D010','WGSS-7B8A6581BE10']), 'dispute umbrella cannot duplicate filing and adjudication')
check('WGSS-1A4E02C9F8A5' not in by and any('신규' in x for x in by['WGSS-CCF615A45814']['includes']), 'pension merge preserves contribution variant')
check(by['WGSS-647DCADA33FC']['outcome_key']=='submit_pension_early_withdrawal_request', 'early withdrawal request never implies approval')
check(by['WGSS-MECE-CUSTOMER-INVOICE']['object_key']!=by['WGSS-587877289E94']['object_key'], 'invoice delivery differs from fee amount decision')
check(not data['audit']['global_mece_proof'] and not data['audit']['new_provider_collection_allowed'], 'editing or test success must not certify MECE')
ledger=json.loads((R/'data/operation-backbone-dispositions.json').read_text())
invoice=next(r for r in ledger['input_mapping_overrides'] if r['input_id']=='lending-trade-invoice financing advance-draw-51')
check(set(invoice['work_ids'])=={'WGSS-MECE-RECEIVABLE-ADVANCE-DISBURSEMENT','WGSS-DE4E23D3BB89'} and set(invoice['selection_conditions'])==set(invoice['work_ids']) and all(i not in invoice['work_ids'] for i in ['WGSS-MECE-INVOICE-FINANCE-PAYMENT-REQUEST','WGSS-610BF7A63589']), 'actual invoice finance disbursement preserves both contract structures and cannot use request or title purchase as payment')
check('WGSS-B0E67CF66BA2' not in by and by['WGSS-6CA6BDD01105']['actor_role']=='reinsurance_contract_counterparty', 'reinsurance cession and acceptance cannot clone a shared contract')
loan=by['WGSS-F4E90272B38B']
check(loan['outcome_key']=='agree_individual_securities_loan_terms' and any('§1.3' in s for s in loan['applicability_conditions']), 'loan terms agreement must preserve the transfer condition for loan effectiveness')
request=by['WGSS-MECE-INVOICE-FINANCE-PAYMENT-REQUEST']
check('Sent' in request['definition'] and 'submit' in request['outcome_key'], 'invoice finance request must not claim disbursement')
treasury=by['WGSS-MECE-BANK-TREASURY-POSITION']
check(treasury['object_key']!=by['WGSS-C1405A805E6A']['object_key'] and treasury['object_key']!=by['WGSS-7219DCE0C54F']['object_key'], 'bank-wide treasury information must not be replaced by trading or customer positions')
access=by['WGSS-MECE-SERVICING-ACTIVITY-AUTHORITY']
check(access['object_key']!=by['WGSS-B5B544940BAB']['object_key'] and any('채무자' in s for s in access['excludes']), 'bank service access permission cannot assert debtor collection authority')
master=by['WGSS-MECE-MASTER-ACTIVITY-COVERAGE']
check(master['outcome_key']!=by['WGSS-MECE-MASTER-AGREEMENT-FORMATION']['outcome_key'] and master['object_key']!=access['object_key'], 'agreement formation and distinct constraint coverage judgments cannot be mixed')
safe=by['WGSS-MECE-SECURITIES-SAFEKEEPING-RECEIPT']
check(any('효력일 공란' in c and 'SEC 승인' in c for c in safe['applicability_conditions']) and any('거절' in c for c in safe['applicability_conditions']), 'a filed custody form must not assert execution or acceptance of rejected assets')
check(safe['outcome_key']!=by['WGSS-D490EDEAC5CD']['outcome_key'] and any('법적 소유권' in c for c in safe['excludes']), 'safekeeping acceptance is not a ledger transfer or trust title assumption')
limit=by['WGSS-779616C3F2C3']
check(limit['object_key']=='counterparty_credit_exposure_limit' and '심사 없이' not in limit['definition'] and limit['outcome_key']!=by['WGSS-CB2F5FE40642']['outcome_key'], 'an internal exposure cap must not inherit contractual credit-facility diligence waivers')
checkpoint=json.loads((R/'data/mece-closure-review.json').read_text())
check(all(r['next_action'] not in ['없음','none',''] and r.get('done_conditions') for r in checkpoint['remaining_work']), 'an open financial boundary needs an actionable proof/comparison task and done criteria')
check(all(g['state']=='pending' for g in checkpoint['execution_plan'] if g['id'] in ['source_disposition','standards_scope','meaning_and_coverage','version_freeze']), 'closing local hypotheses cannot erase source/standard/whole-catalogue blockers')
assignment=by['WGSS-MECE-LENDER-POSITION-ASSIGNMENT'];participation=by['WGSS-MECE-LOAN-PARTICIPATION-SALE']
check(assignment['object_key']!=participation['object_key'] and any('義務' in r.get('exact_quote','') or 'rights and obligations' in r.get('exact_quote','') for r in assignment['refs']) and any('remain unchanged' in r.get('exact_quote','') for r in participation['refs']), 'lender-position assignment and economic participation have opposite original-lender obligation conditions')
check(by['WGSS-MECE-REGISTERED-HOLDER-TRANSFER']['object_key']!=by['WGSS-11940117C228']['object_key'] and any('Until a transfer is so recorded' in r.get('exact_quote','') for r in by['WGSS-MECE-REGISTERED-HOLDER-TRANSFER']['refs']), 'registered holder effectiveness is not nominee holding or custody position movement')
check(any('Class' in c and 'Series' in c for c in by['WGSS-MECE-FUND-SERIES-ESTABLISHMENT']['applicability_conditions']) and '클래스' not in by['WGSS-MECE-FUND-SERIES-ESTABLISHMENT']['includes'][0], 'class-level expense allocation cannot assert estate segregation')
check(any('수수료' in c or '판매 수수료' in c for c in by['WGSS-MECE-FUND-NAV']['applicability_conditions']), 'NAV is not guaranteed to equal the final fee-inclusive transaction price')
check(any('예상값과 확률분포' in c for c in by['WGSS-MECE-INVESTMENT-OUTCOME-PROJECTION']['applicability_conditions']), 'scalar forecasts and distributions must not create method clones')
end=by['WGSS-MECE-CARD-NETWORK-PARTICIPATION-END']
check(any('자발적' in c for c in end['includes']) and any('운영기관' in c for c in end['includes']) and any('잔존' in c for c in end['excludes']), 'one participation end preserves different causes and surviving duties')
check('재보험' in by['WGSS-72879CC650A0']['definition'] and any('재보험계약 성립' in c for c in by['WGSS-72879CC650A0']['excludes']), 'reinsurance internal underwriting broadens a shared role without cloning contract formation')
v21path=R/'data/mece-v21-root-dispositions.json'
if v21path.exists():
 v21=json.loads(v21path.read_text())
 check({r['id'] for r in checkpoint['remaining_work']}=={'CANDIDATE-ServiceDomain:37849#0','CANDIDATE-ServiceDomain:46157#0','CANDIDATE-BusinessCapability:64574#0'}, 'regulatory ambiguity, bank funding and account-control uncovered responsibilities must remain pending')
 request_end=by['WGSS-9A4B541DD443'];request_change=by['WGSS-9EAFFE368698']
 facility_end=by['WGSS-MECE-CREDIT-FACILITY-END'];facility_reduction=by['WGSS-MECE-CREDIT-FACILITY-REDUCTION']
 check('overdraft' not in request_end['object_key'] and 'overdraft' not in request_change['object_key'] and '당좌대월' in str(request_end['includes']), 'generalised committed-facility requests preserve overdraft variants without product clones')
 check(all(any('구속적 통지' in x for x in w['excludes']) and not any(r['id']=='WGSS-PROCESS-SEC_LOAN_MATURITY_SELECTED' for r in w['refs']) for w in [request_end,request_change]), 'provider-decision applications must not absorb a binding exercise of contractual termination/reduction rights')
 check(len({w['outcome_key'] for w in [request_end,request_change,facility_end,facility_reduction,by['WGSS-CB2F5FE40642']]})==5, 'formation, end/change requests and actual full/partial credit-right effects have different completion results')
 check(any('원리금' in s for s in facility_end['excludes']) and any('소멸' in s for s in facility_end['excludes']) and facility_end['object_key']!=by['WGSS-860722E7067D']['object_key'], 'termination of future commitment cannot assert prior loan liability extinguished or repaid')
 check('관리대리인이' not in facility_end['definition'] and '관리대리인이' not in facility_reduction['definition'] and any('대리인의 독립적인 승인' in c for c in facility_end['applicability_conditions']), 'contractual capacity effect must not invent agent legal-effect approval')
 check('유지' in facility_reduction['definition'] and facility_reduction['outcome_key']!=facility_end['outcome_key'] and any('증액' in c for c in facility_reduction['excludes']), 'partial reduction preserves the credit relation and does not claim an unsupported increase result')
 policy=by['WGSS-D04C78B35E3E'];amend=by['WGSS-MECE-FUND-POLICY-AMENDMENT']
 check('shariah' not in policy['object_key'] and '샤리아' in str(policy['includes']) and policy['object_key']!=by['WGSS-AF6645904647']['object_key'], 'fund rule generalisation must preserve Sharia conditions and differ from an individual investment mandate')
 check(amend['actor_role']==policy['actor_role'] and amend['outcome_key']!=policy['outcome_key'] and '필요한 경우에만' in amend['definition'] and '모든 펀드의 필수 절차' in amend['definition'], 'a holder vote is an applicable policy-amendment condition, not an additional viewpoint work or universal requirement')
 check(any('shall establish policies' in r.get('exact_quote','') for r in policy['refs']) and any('shall become effective' in r.get('exact_quote','') for r in by['WGSS-CB2F5FE40642']['refs']), 'adoption and credit formation need actual operative authority/effect proof rather than noun-only references')
 check(len(checkpoint['source_followups'])==5 and any(r['id']=='V21-CE-SYNDICATED-SERVICING' for r in checkpoint['source_followups']) and any(r['id']=='V22-CENSUS-FINANCIAL-BOUNDARIES' for r in checkpoint['source_followups']), 'prior servicing responsibilities and newly identified financial scope boundaries must both remain visible')
else:
 check(any(r['id']=='CANDIDATE-ServiceDomain:38742#0' and '신디케이트 가입' in r['next_action'] for r in checkpoint['remaining_work']), 'loan maturity cannot map commitment termination to joining a syndicate')
print(json.dumps({'status':'passed','boundary_checks':checks,'global_mece_approved':False}))
