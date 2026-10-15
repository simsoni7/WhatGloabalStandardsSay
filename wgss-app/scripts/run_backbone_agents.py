"""Manual parallel Bedrock experts. Advisory JSON never edits definitions."""
import concurrent.futures,hashlib,json,sys
from pathlib import Path
from bedrock_gateway import call_stream
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/backbone-20261004';P.mkdir(parents=True,exist_ok=True)
works=json.loads((R/'dist/data/operations.json').read_text())['works'];library=json.loads((R/'dist/data/library.json').read_text());ids={w['id'] for w in works}
if not (P/'input-351.json').exists():(P/'input-351.json').write_text(json.dumps(works,ensure_ascii=False,indent=2))
reg=json.loads(Path('/home/ubuntu/wgss-operation-v12/catalogue/reference-registry.json').read_text());reg.update(json.loads(Path('/home/ubuntu/wgss-operation-v12/review/external-reference-disposition.json').read_text())['refs'])
compact=[{k:w.get(k) for k in ['id','title','category','layer','actor_role','object_key','outcome_key','discriminator','definition']} for w in works]
payments=[w for w in works if w['category']=='payments-cards' or w['id'] in ['WGSS-F92805EAE41E','WGSS-38FCE46AB7D8']];refs=[reg[r['id']] for w in payments for r in w['refs'] if r['id'] in reg];refs=list({r['id']:r for r in refs}.values())
common='''WGSS is for product practitioners designing financial screens. User found that searching 송금 fails to show 송금하기, 국내송금, 해외송금. Currentmain UI uses12 provider-evidence headings, separateadmin351work catalogue. Diagnose semantics not only synonyms. Existing351 are REVIEW ROWS, notMECEapproved. Model proposals nevereditdataautomatically. Separate canonical atomic responsibility/result, composite journey, contextualscenario/search label, providerobservation, sourceconcept. Nationality/homecountry/currency alone doNOTdetermine domestic/crossborder: require origin/destination servingjurisdictions; unknownstaysunknown. Domesticforeigncurrency andcrossbordersamecurrency counterexamples. FX may beoptionalindependentoutcome. Instructionacceptance doesnotprovebeneficiarycredited. A one-owner categorisationpartition is NOTsemanticMECEproof. No hallucinatedproviderwording/screens. ShortKorean readable labels. ReturncompleteJSON, nofences,compactstrings.\n'''
prompts={
'architecture':common+'''You are ontology architect. Propose practical skeleton acrossALL351. Return {families:[{id,label,definition,excludes:[],work_ids:[]}],counting_contract:{canonical_unit,scenario_rule,journey_rule,role_rule},failure_patterns:[],migration_rules:[],unresolved:[]}. 12-20 major navigationalfamilies, stableplainIDs. EveryexistingIDin EXACTLYONEprimaryfamily fornavigation; crosslinksoptionalnotextra count. Nameslikely계좌·예금/송금·지급/카드/대출/담보/투자/보험/연금/신원·접근/고객정보/분쟁/기관처리 ... choose coherentfinancialobject+outcome boundary avoidmiscbucket or mix actorperspectiveas topfamily. Originalcategoryproduct labelsarenotMECEtruth. Everyfamily explainstableboundary. Ifgeneralfinancialcontractcoversproducts markscopeproblem, don'tinventexacttotal. Thisassignment is advisoryclassification only.\nALL351:'''+json.dumps(compact,ensure_ascii=False,separators=(',',':')),
'payments':common+'''You are financialpayment domainarchitect. Critically reviewprovidedpaymentworkdefinitions andPRIMARYregistry. Return {findings:[{work_ids:[],problem,action:"keep|rename|edit|merge_candidate|split_candidate|source_gap",reason,source_ids:[]}],canonical_flow:[{stage,label,work_ids:[],direct_result,not_implied:[]}],scenarios:[{id,title,canonical_ids:[],context,not_new_work_reason,unresolved_policy:[]}],boundary_tests:[{id,description,facts,expected_work_ids:[],expected_context,forbidden_inference}],decisions_needed:[]}. Need domestic/international transfer, ownaccounttransfer,thirdparty,scheduledvsstandingorder vsdirectdebit, FXquotevsexchange, customerrequest vsbankaccept/execution vsinterbanksettlement vsbeneficiarycredit, amendment/cancel vsrecall vsrefund, statusvsconfirmation. 15-25 counterexamples. Identifyrealoverlap genericpaymentsettlement vsbanktransfer execution/internalbookentry, notrubberstamp. Missingworkassertrequiresprimaryquote ifprovided otherwisegap. Don'tmerge oneentityrequest withcounterpartyaccept justbecauseonejourney. Don'tmanufactureconsumertransfer withbusinessnounonly. Definitionsoriginalreviewgaps notpermissiontogeneratebankpolicy.\nPAYMENTROWS:'''+json.dumps(payments,ensure_ascii=False,separators=(',',':'))+'\nPRIMARY:'+json.dumps(refs,ensure_ascii=False,separators=(',',':'))+'\nWEB:'+json.loads((P/'primary-search.json').read_text()),
'discoverability':common+'''You are productquality adversary and UXtaxonomy designer. ReviewALL351 andcurrent12searchtopics. Needusergoalsfirstwithoutinflatingworkcount. Return {diagnosis:[],goals:[{id,title,aliases:[],canonical_work_ids:[],missing_result:null|string,scenario_labels:[],existing_reference_task_ids:[]}],smoke_queries:[{query,expected_goal_ids:[],unresolved_policy:[]}],pitfalls:[]}. 35-50 practical customer/institutiondesigngoalsacrossaccountopening/cardapply/sendmoney/domestic/international/currencyexchange/loans/insurance/pensions/authentication/change password/dataaccess/etc. Each goalmapsactualIDs or explicitmissing notinventedIDs. domestic/international appear userfriendly pathways tosamepaymentoperation withconditions; not arbitrarilyduplicatecases. Existingreferences linkedONLYsameintent. Completion/status/recall reference notproofsendmoney initiation; nativebankappscreensnotprovided. Needcommon basicoperations absent12headingindex. Querymatchesmustusepositiveintent vocabulary notallincludes/excludes (negation falsepositive). List not pretendmececovered350.\nALL351:'''+json.dumps(compact,ensure_ascii=False,separators=(',',':'))+'\nCURRENT12:'+json.dumps([{k:t[k] for k in ['id','title','category','aliases']} for t in library['tasks']],ensure_ascii=False)
}
# Bound substantive reviews to small source-backed slices. Large modes remain
# explicit options; navigation classification never establishes semantic MECE.
family_sample=[]
for category in sorted({w['category'] for w in works}):
 family_sample.extend([{k:w[k] for k in ['id','title','actor_role','object_key','outcome_key']} for w in works if w['category']==category][:5])
focus_ids={'WGSS-DF4BF34CD9B3','WGSS-96C318236155','WGSS-F92805EAE41E','WGSS-3755DC0A622A','WGSS-BF2EC9C9E0D9','WGSS-BF85DE091C72','WGSS-48C3932662D4','WGSS-B6D7A72FE1F6','WGSS-A2A55984D53B','WGSS-38FCE46AB7D8','WGSS-AFF4499574AA','WGSS-BACKBONE-FX-QUOTE'}
focus=[w for w in works if w['id'] in focus_ids]
focus_refs=[reg[r['id']] for w in focus for r in w['refs'] if r['id'] in reg]
prompts['architecture-small']=common+'Ontologyarchitect: propose navigationalfamilies and countingcontract, neversemanticMECEapproval. Request/accept/execute/settle/confirm are separate resultfacets, not necessarily topmenus. Financialproducts and roles do not multiplycanonicalworkcount. Informationresults remain inscope. JSON {families:[{id,label,definition,excludes:[]}],counting_contract:{canonical_unit,scenario_rule,journey_rule,role_rule},failure_patterns:[],migration_rules:[],unresolved:[]}. SAMPLE:'+json.dumps(family_sample,ensure_ascii=False)
prompts['payments-small']=common+'Paymentarchitect criticallycompare onlythese focusedresponsibilities. BIANPaymentSettlement is fundsavailable for railsettlement, notfinalinterbanksettlement. ISOBookEntry neitherfixesactor norbank/ownershipsame. Submission notcredited, recallrequest notrefundcredited, FXinformation notexchange. Do notcall omittednonfocusedID missing inwholecatalogue. JSON {findings:[{work_ids:[],problem,action,reason,source_ids:[]}],canonical_flow:[{stage,label,work_ids:[],direct_result,not_implied:[]}],boundary_tests:[{id,description,facts,expected_work_ids:[],expected_context,forbidden_inference}],decisions_needed:[]}. 14counterexamples. FOCUS:'+json.dumps(focus,ensure_ascii=False)+' PRIMARY:'+json.dumps(focus_refs,ensure_ascii=False)
def run(name):
 prompt=prompts[name];sha=hashlib.sha256(prompt.encode()).hexdigest();out=P/(name+'.json')
 if out.exists():
  cached=json.loads(out.read_text())
  if cached.get('prompt_sha256')==sha:print(name,'cached',flush=True);return cached['proposal']
 (P/(name+'.prompt.txt')).write_text(prompt)
 for n in range(1,4):
  try:
   raw=call_stream('claude-sonnet-5' if name=='discoverability' else 'claude-opus-5',prompt);(P/f'{name}.raw-{n}.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2));assert raw['finish_reason']=='stop','truncated output'
   text=raw['response'];proposal=json.loads(text[text.find('{'):text.rfind('}')+1])
   if name=='architecture':
    assigned=[i for f in proposal['families'] for i in f['work_ids']];assert len(assigned)==len(ids) and set(assigned)==ids,'complete IDpartition'
   if name=='discoverability':assert all(set(g['canonical_work_ids'])<=ids for g in proposal['goals'])
   if name in ['payments','payments-small']:assert all(set(r['work_ids'])<=ids for r in proposal['findings'])
   out.write_text(json.dumps({'prompt_sha256':sha,'model':raw['model'],'usage':raw['usage'],'proposal':proposal,'automatically_adopted':False},ensure_ascii=False,indent=2));print(name,'completed',flush=True);return proposal
  except Exception as e:print(name,'attempt',n,type(e).__name__,str(e)[:120],flush=True)
 raise RuntimeError(name+' incomplete')
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('agents',nargs='*',help='architecture-small, payments-small, discoverability; large modes explicitly available')
args=parser.parse_args()
selected=args.agents or ['architecture-small','payments-small','discoverability']
if any(name not in prompts for name in selected):parser.error('Unknown agent name')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 list(pool.map(run,selected))
print('all selected experts completed',flush=True)
