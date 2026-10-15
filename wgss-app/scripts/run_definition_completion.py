"""Bounded, resumable Bedrock definition research. Advisory only; no active writes."""
import argparse,concurrent.futures,hashlib,json,re,time
from pathlib import Path
from bedrock_gateway import call_stream
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/definition-completion-20261004';P.mkdir(parents=True,exist_ok=True)
def write(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def prepare():
 D=json.loads((R/'dist/data/operations.json').read_text());K=json.loads((R/'dist/data/business-backbone.json').read_text());V=json.loads((R/'data/product-vocabulary-inventory.json').read_text());reg=json.loads((R/'research/source-store/operation-v12/catalogue/reference-registry.json').read_text());reg.update(json.loads((R/'research/source-store/operation-v12/review/external-reference-disposition.json').read_text())['refs']);by={w['id']:w for w in D['works']};jobs=[]
 groups={'credit-facility':['overdraft','credit-facility'],'loan-lifecycle':['card-loan','unsecured-loan','mortgage','rent-loan','emergency-loan','secured-loan','guaranteed-loan','refinance'],'card-credit':['cash-advance','payment-revolving','credit-card'],'savings-accounts':['installment-savings','group-account','fx-account'],'investment-wrappers':['cma','isa','irp','pension-savings'],'securities-results':['mmf','bonds','rp','structured-securities','etf']}
 universe=[{k:w.get(k) for k in ['id','title','actor_role','object_key','outcome_key','discriminator']} for w in D['works']]
 for name,ids in groups.items():
  profiles=[p for p in K['product_profiles'] if p['id'] in ids];steps=[{'profile_id':p['id'],**s} for p in profiles for s in p['steps'] if s.get('gap') or not s['work_ids']];focus_ids={i for p in profiles for s in p['steps'] for i in s['work_ids']+s.get('review_candidate_ids',[])};focus=[by[i] for i in sorted(focus_ids)];refs={r['id'] for w in focus for r in w['refs']};standard=[reg[i] for i in refs if i in reg];terms=['Savings Account','Current Account','Term Deposit'] if name=='savings-accounts' else ['Credit Card','Card Billing & Payments'] if name=='card-credit' else ['Consumer Loan','Credit Facility'] if 'loan' in name or 'credit-facility' in name else []
  standard += [v for v in reg.values() if v.get('name') in terms];sids={i for p in profiles for i in p['source_ids']};docs=[s for s in K['product_sources'] if s['id'] in sids]
  jobs.append({'id':name,'model':'claude-opus-5','scope':{'profiles':profiles,'gap_steps':steps,'focus_works':focus,'standard_definitions':list({v['id']:v for v in standard}.values()),'primary_sources':docs,'existing_universe':universe}})
 unlinked=[w for w in D['works'] if w['status']=='unresolved' and w['id'] not in {i for job in jobs for w in job['scope']['focus_works'] for i in [w['id']]}]
 jobs.append({'id':'residual-definitions','model':'claude-opus-5','scope':{'focus_works':unlinked,'standard_definitions':list({r['id']:reg[r['id']] for w in unlinked for r in w['refs'] if r['id'] in reg}.values()),'existing_universe':universe}})
 gaps=[i for i in V['items'] if i['disposition']=='gap']
 for start in range(0,len(gaps),8):jobs.append({'id':'inventory-'+str(start//8+1).zfill(2),'model':'claude-sonnet-5','scope':{'inventory':gaps[start:start+8],'existing_universe':universe,'known_profiles':[{k:p[k] for k in ['id','title','definition','features','source_ids']} for p in K['product_profiles']]}})
 manifest={'version':'WGSS-definition-completion-20261004','input_version':D['version'],'canonical_review_count':len(D['works']),'unresolved_count':sum(w['status']=='unresolved' for w in D['works']),'gap_step_count':sum(bool(s.get('gap')) or not s['work_ids'] for p in K['product_profiles'] for s in p['steps']),'inventory_gap_count':len(gaps),'jobs':[{'id':j['id'],'model':j['model'],'input_file':str(P/'inputs'/(j['id']+'.json'))} for j in jobs],'automatic_adoption':False,'global_mece_approved':False}
 for j in jobs:
  file=P/'inputs'/(j['id']+'.json')
  if file.exists():assert json.loads(file.read_text())==j,'Frozen input changed; start a new run directory'
  else:write(file,j)
 write(P/'manifest.json',manifest);return manifest
def clauses(scope):
 ids={s['id'] for s in scope.get('primary_sources',[])};sources=[];base=R/'research/source-store/products-20261004'
 keywords=['약정결제비율','최소결제비율','일부결제금액이월약정','신청','해지','상환방법','기간연장','연장 신청','대출 절차','상환','중도해지','납입','예금종류','만기','기여','설정','환매','유통시장','발행시장','IRP','ISA','CMA']
 for sid in sorted(ids):
  f=base/(sid+'.txt')
  if not f.exists():continue
  t=f.read_text();snippets=[]
  for term in keywords:
   # Exclude repeated navigation from substantive quote selection when possible.
   offsets=[m.start() for m in re.finditer(re.escape(term),t)]
   for at in offsets[-2:]:
    excerpt=t[max(0,at-100):at+500]
    if not any(excerpt in s['text'] for s in snippets):snippets.append({'locator':{'file':f.name,'char_start':max(0,at-100),'char_end':min(len(t),at+500)},'text':excerpt})
    if len(snippets)>=10:break
   if len(snippets)>=10:break
  source=next(s for s in scope['primary_sources'] if s['id']==sid);sources.append({'source_id':sid,'url':source['url'],'source_sha256':source['sha256'],'selected_public_clauses':snippets,'not_ui_benchmark':True})
 return sources
def run(name):
 j=json.loads((P/'inputs'/(name+'.json')).read_text());scope=j['scope'];supp=P/'supplements'/(name+'.json');extra=json.loads(supp.read_text()) if supp.exists() else {};scope={**scope,'public_source_clauses':clauses(scope),'root_source_supplement':extra}
 prompt='''WGSS financial ontology research specialist. Work from these frozen public definitions/selected clauses. CURRENT rows are REVIEW DEFINITIONS, not global MECE approved. Need finish financial work definitions, not reactively patch keywords. Canonical unit=one actor responsibility + direct financial object/right/obligation/info + one intended independently completable result + materially necessary discriminator. Productnames, country, UI label, actor alias, API verb, source noun, journey step doNOT automaticallycreatework. First compare candidate against existing universe. A product-specialised version of same responsibility/result should reuse generic definition with conditions. Parent and child cannot both count same result. Request≠acceptance≠institutiondecision≠disbursement≠settlement≠credit; informationretrieval≠computation≠approval. Loanclosing≠principalpayment≠interestsettlement≠collateralrelease. Changes should prefer precise supported edits/merges over arbitrary newwork; don't force source gap if original necessary evidence exists in input. Don't fabricate role beyond source. Need concrete actionable definition proposals, sources and counterexamples, not endless generic suggestions. EXACT source quote from supplied public clauses/standarddefinition only. Original fullpages/keys/customerdata notprovided. Regional policy doesn'tprove worldwide rights. No fees/tax/creditlimits copied as globalstandard. Data gaps in unseen input doNOTprove wholecataloguemissing. No new case IDs or automatic approval. Return completeJSON nofences: {job_id,definition_proposals:[{local_id,title_ko,actor_role,object_key,outcome_key,discriminator,definition,includes:[],excludes:[],existing_relation:"reuse|edit|merge_candidate|split_candidate|new_candidate|needs_source",existing_work_ids:[],source_proofs:[{source_id,url,locator,exact_quote,proof_scope}],scope_conditions:[],role_result_boundary,independent_failure_example,counting_decision}],step_dispositions:[{profile_id,step_id,decision:"reuse|define|conditional|candidate|not_separate_work|needs_source",existing_work_ids:[],proposal_local_ids:[],reason}],inventory_dispositions:[{inventory_id,product_type,existing_profile_ids:[],meaning_conditions:[],related_work_ids:[],needed_sources:[],decision}],boundary_tests:[{description,facts,expected_result,forbidden_inference}],additional_primary_urls:[],unresolved:[]}. At most20definitionproposals and15tests. All assigned gaps must get an explicit disposition; preserve genuine unknowns but resolve sourced gaps. BIAN action/API layers may contain CRUD operations not financial atomicworks. Information objects may be meaningful financialresults; don'tremovequeries justbecause no financialasset changes. Regulatory/local-specific rights mayneedconditions. Explain separate clientrequest vs providerresult. Output Korean descriptions readable. JOB INPUT:'''+json.dumps({'id':name,'scope':scope},ensure_ascii=False,separators=(',',':'))
 sha=hashlib.sha256(prompt.encode()).hexdigest();target=P/'reviews'/name/sha;target.mkdir(parents=True,exist_ok=True);out=target/'proposal.json'
 if out.exists():print(name,'cached',flush=True);return
 (target/'prompt.txt').write_text(prompt)
 for n in range(1,4):
  try:
   raw=call_stream(j['model'],prompt,max_tokens=24000);write(target/f'raw-{n}.json',raw);assert raw['finish_reason']=='stop','truncated';t=raw['response'];o=json.loads(t[t.find('{'):t.rfind('}')+1]);valid={w['id'] for w in scope['existing_universe']}
   for row in o.get('definition_proposals',[]):assert set(row.get('existing_work_ids',[]))<=valid,'unknown work ID'
   assigned={(s['profile_id'],s['id']) for s in scope.get('gap_steps',[])};covered={(s['profile_id'],s['step_id']) for s in o.get('step_dispositions',[])};assert assigned<=covered,'missing step dispositions'
   assigned_inventory={i['id'] for i in scope.get('inventory',[])};assert assigned_inventory<={i['inventory_id'] for i in o.get('inventory_dispositions',[])},'missing inventory dispositions'
   write(out,{'job_id':name,'model':raw['model'],'prompt_sha256':sha,'usage':raw['usage'],'proposal':o,'automatic_adoption':False});print(name,'completed',flush=True);return
  except Exception as e:print(name,'attempt',n,type(e).__name__,str(e)[:90],flush=True)
 raise RuntimeError(name+' incomplete')
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true');parser.add_argument('jobs',nargs='*');args=parser.parse_args()
 if args.prepare:print(json.dumps(prepare(),ensure_ascii=False));raise SystemExit(0)
 manifest=json.loads((P/'manifest.json').read_text());selected=args.jobs or [j['id'] for j in manifest['jobs']];assert set(selected)<={j['id'] for j in manifest['jobs']}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,selected))
