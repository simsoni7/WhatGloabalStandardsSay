"""One-time root admission, explicit trial-country revision and all66 gap audit."""
import collections,copy,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/collection-root-v33-20261013';COLD=R/'research/source-store/collection-root-corrections-v33-20261013'
def read(p):return json.loads(p.read_text())
PENDING=[]
def write(p,d):PENDING.append((p,copy.deepcopy(d)))
def proposal_rows(folder):return [v for p in folder.glob('reviews/*/*/proposal.json') for v in read(p)['result']['rows']]
def target_rows(folder):
 d=read(folder/'new-provider-targets.json');return d if isinstance(d,list) else d.get('rows',d.get('providers',[]))
if __name__=='__main__':
 dest=R/'data/bank-ui-collection-v33-decisions.json';assert not dest.exists();c=read(RUN/'root-candidates.json');prior=read(R/'data/bank-ui-collection-v32-decisions.json');base=read(R/'data/bank-ui-baseline-v32.json');sources={b['prefix']+':'+s['id']:s for b in c['source_batches'] for s in read(R/b['manifest'])};final={v['id']:v for v in proposal_rows(RUN)};corrected={b['id']:b for b in read(COLD/'root-candidates.json')['examples']};final.update({v['id']:v for v in proposal_rows(COLD)});assert len(final)==len(c['examples']);rows=[];root=[];staged=copy.deepcopy(c['staged_candidates'])
 for original in c['examples']:
  b=copy.deepcopy(corrected.get(original['id'],original));v=final[b['id']];assert (v['source_id'],v['work_id'],v['native_expression'])==(b['source_id'],b['ui_work_ids'][0],b['expression'])
  if v['status']=='reject':staged.append(dict(candidate_id=b['candidate_id'],source_id=b['source_id'],work_id=b['ui_work_ids'][0],reason_ko=' '.join(v['findings_ko'])));continue
  assert v['status']=='pass',(b['id'],v)
  s=sources[b['source_id']];assert s['state']=='fetched_pending_review';assert hashlib.sha256((R/s['snapshot_path']/s['raw_filename']).read_bytes()).hexdigest()==b['raw_sha256'];assert hashlib.sha256(s['text'].encode()).hexdigest()==b['text_sha256']
  for q in [b['proof'],b['function_proof']]+b['flow_step_proofs']+[p['proof'] for p in b['policy_claims']]:assert s['text'][q['start']:q['end']]==q['excerpt']
  # Stale intermediate model annotations remain in frozen handoffs, not final examples.
  for key in list(b):
   if 'critic' in key or key=='review_recommendation':b.pop(key)
  if b['candidate_id'] in ['ALT-V33-1','ALT-V33-2','ALT-V33-3']:b['reference_document_version']='상품설명서 2026-01-01'
  b['root_function_admitted']=True;rows.append(b);root.append(dict(example_id=b['id'],candidate_id=b['candidate_id'],source_id=b['source_id'],work_id=b['ui_work_ids'][0],root_decision='admit_qualified_publisher_function_not_observed_execution',model_status=v['status'],cold_correction_review=b['id'] in corrected,automatic_adoption=False))
 assert len(rows)==52
 # Root verifies a geography study separately from unchanged216 financial units.
 market_folder=R/'research/source-store/market-final-v33-20261013';market=read(market_folder/'proposal.json');mr=proposal_rows(market_folder);assert len(mr)==1 and mr[0]['status']=='pass'
 for target in market['provider_targets']:
  proof=target['country_proof'];s=sources[proof['source_id']];q=proof['proof'];assert s['text'][q['start']:q['end']]==q['excerpt'];assert s['raw_sha256']==proof['raw_sha256'] and s['text_sha256']==proof['text_sha256']
 market.update(root_reviewed=True,root_decision='admit_explicit_initial_country_study_not_local_availability',reviewed_at='2026-10-13',source_review=mr,admitted_reference_languages=dict(MY=['en','ms'],AE=['en']));write(R/'data/bank-ui-market-study-v33.json',market)
 runs=[];attempt_count=0
 families=['merchant-','account-lending-','insurance-investment-','alternative-','market-','collection-root']
 for folder in (R/'research/source-store').glob('*v33-20261013'):
  if not any(folder.name.startswith(f) for f in families):continue
  attempt_count+=len(list(folder.glob('reviews/*/*/attempt-*.json')))
  for p in folder.glob('reviews/*/*/proposal.json'):
   j=read(p);runs.append({k:j[k] for k in ['job_id','model','prompt_sha256','usage']}|dict(run_manifest=str(p.relative_to(R))))
 assert len({(v['job_id'],v['prompt_sha256']) for v in runs})==len(runs)
 fresh=[s for b in c['new_source_batches'] for s in read(R/b['manifest'])];stats=dict(source_records=len(fresh),retrieved_source_records=sum(s['state']=='fetched_pending_review' for s in fresh),unique_original_hashes=len({s['raw_sha256'] for s in fresh if s['state']=='fetched_pending_review'}),failed_source_records=sum(s['state']!='fetched_pending_review' for s in fresh),http200_error_bodies_excluded=['S33:al-hsbc-hk-businessterms'],private_text_page_render_not_ui=['account-lending-assets-v33-20261013/ncb-guide-page-09.png'])
 ledger=dict(scope_version=base['version'],denominator=216,scope_change=False,reviewed_at='2026-10-13',prior_root_ledger='data/bank-ui-collection-v32-decisions.json',source_batches=c['source_batches'],new_source_batches=c['new_source_batches'],provider_id_aliases=c['provider_id_aliases'],source_owner_corrections=prior['source_owner_corrections'],priority_cell_dispositions=prior['priority_cell_dispositions'],admitted_examples=root,final_source_review=list(final.values()),staged_candidates=staged,staged_semantic_routes=prior['staged_semantic_routes']+[dict(source_id=s['source_id'],candidate_ko='미채택 결과 · '+s['candidate_id'],reason_ko=s['reason_ko']) for s in staged],semantic_field_review_queue=c['semantic_field_review_queue'],source_language_corrections=c['source_language_corrections'],issuer_role_interpretation=prior['issuer_role_interpretation'],market_study_revision='data/bank-ui-market-study-v33.json',source_inventory_stats=stats,model_runs=runs,api_attempt_records=attempt_count,guide_images_admitted=0,product_images_admitted=0,raw_asset_inventory=1,all_initial_unlinked_works_assigned=66,independent_human_review=False,automatic_adoption=False,observed_app_captures=0,verified_app_ui_versions=0,failed_exact_outputs_preserved=True,cold_reviews_without_stale_advisory_text=True);write(dest,ledger)
 bank=read(R/'data/bank-ui-benchmark-dispositions.json');assert len(bank['examples'])==271;bank['examples']+=rows;bank['collection_batches'].append(dict(batch='collection-v33',root_ledger=str(dest.relative_to(R)),scope_change=False,market_study_revision=ledger['market_study_revision']));write(R/'data/bank-ui-benchmark-dispositions.json',bank)
 plan=read(R/'data/bank-ui-collection-plan.json');plan.update(plan_version='collection-v33',reviewed_at='2026-10-13',priority_audit_ledger=str(dest.relative_to(R)),strategy_review_ledger=str(dest.relative_to(R)),public_collection_audit_ledger='data/bank-ui-public-collection-v33.json',priority_countries=market['priority_countries'],market_study_revision=ledger['market_study_revision'],latest_execution=dict(batch='collection-v33',admitted_new_examples=len(rows),new_guide_images=0,new_product_images=0,bedrock_successful_jobs=len(runs),api_attempt_records=attempt_count,official_source_inventory=stats,all_initial_unlinked_works_assigned=66,actual_app_captures=0,scope_change=False))
 for code in ['MY','AE']:plan['countries'].append(dict(country=code,languages=market['admitted_function_reference_languages'][code],providers=[t['name'] for t in market['provider_targets'] if t['country']==code],study_stage='initial_own_source_references',independent_local_language_review=False,all_scoped_works_available=False))
 newtargets=[]
 for n in ['merchant-handoff-v33-20261013','merchant-bank-handoff-v33-20261013','account-lending-handoff-v33-20261013','insurance-investment-final-handoff-v33-20261013']:
  newtargets+=target_rows(R/'research/source-store'/n)
 newtargets+=market['provider_targets'];admitted_provider_ids={b['provider_id'] for b in rows};known={t['id'] for t in plan['provider_targets']}
 for original in newtargets:
  t=copy.deepcopy(original);t['id']=t.get('id',t.get('provider_id'));t['name']=t.get('name',t.get('provider_name'));assert t['id']
  if t['id'] in known:continue
  t.setdefault('official_url',t.get('source_url'));t.setdefault('languages',sorted({b['language'] for b in rows if b['provider_id']==t['id']}) or ['en']);t.setdefault('platforms_ko',['현지 공식 금융 기능 안내']);t.setdefault('channels_ko','공식 상품·도움말·계약 자료');t.setdefault('selection_basis_ko','미연결 고객 결과의 자체 기능·국가 근거 보완. 시장 대표성 미검증.');t['root_admitted']=t['id'] in admitted_provider_ids;t['research_status_ko']='공식 기능 원문 연결 승인 · 실제 화면·UI 버전·시장 대표성 미검증' if t['root_admitted'] else '공식 자료 조사 대상 · 현재 정의에 맞는 기능 연결은 보류';t['representativeness_proven']=False
  cp=t.get('country_proof');cp=cp.get('proof',cp) if cp else t.get('market_proof');sid=t.get('source_id') or (t.get('country_proof') or {}).get('source_id')
  if cp and cp.get('excerpt'):
   s=sources[sid];assert s['text'][cp['start']:cp['end']]==cp['excerpt'],(t['id'],sid);assert t['country']==s['country']
  plan['provider_targets'].append(t);known.add(t['id'])
 plan['secondary_market_targets']=[t for t in plan.get('secondary_market_targets',[]) if t['country'] not in ['MY','AE']]
 plan['secondary_market_targets'].append(dict(id='bisb-bh',name='Bahrain Islamic Bank',country='BH',official_url='https://www.bisb.com/',platforms_ko=['공식 은행 약관 후보'],research_status_ko='자체 약관 후보 원문만 수집. 현재 5개국 집계와 금융 기능 사례에는 승격하지 않음.',representativeness_proven=False))
 for ticket in c['semantic_field_review_queue']:
  plan['definition_review_gaps'].append(dict(id=ticket.get('id',ticket['work_id']),work_id=ticket['work_id'],label_ko=next(w['title'] for w in base['works'] if w['id']==ticket['work_id'])+' · 정의 조건 재검토',reason_ko=ticket.get('reason_ko',ticket.get('issue_ko')),source_url=sources[ticket['source_id']]['url'],root_decision='stage_definition_field_review_not_silent_scope_change',automatic_adoption=False))
 plan['phases'][0]['exit_condition_ko']='216개 업무 × 현재 5개 조사 국가의 연결·공란을 공개합니다. 조사 대상 조합을 현지 제공 여부로 해석하지 않고 자체 원문의 기능·언어·조건을 검토합니다.';plan['phases'][3]['status_ko']='MY·AE 초기 자료 확장 · 현지 실무 검토 미완료';write(R/'data/bank-ui-collection-plan.json',plan)
 capture=read(R/'data/bank-ui-capture-plan.json');capture['countries']=[p['country'] for p in plan['countries']];capture['country_work_cells']=1080;capture['market_study_revision']=ledger['market_study_revision'];write(R/'data/bank-ui-capture-plan.json',capture)
 # Every initial66 gap gets exactlyone root disposition, overlapping research pools merge.
 oldcovered={w for b in base['benchmarks'] for w in b['ui_work_ids']};initial={w['id'] for w in base['works']}-oldcovered;by={w:[] for w in initial};gap_folders=['merchant-handoff-v33-20261013','account-lending-handoff-v33-20261013','insurance-investment-final-handoff-v33-20261013','merchant-bank-audit-v33-20261013']
 for name in gap_folders:
  payload=read(R/'research/source-store'/name/'gap-audit.json')
  for g in payload if isinstance(payload,list) else payload['rows']:
   if g['work_id'] in by:by[g['work_id']].append(g)
 for w in base['works']:
  if w['id'] not in initial or w['domain_id']!='alternative':continue
  by[w['id']].append(dict(work_id=w['id'],reviewed_source_ids=['A33:'+s['id'] for s in fresh if s['id'].startswith('alt-')],reason_ko='현지 금융사 자체 무다라바 투자계좌·공동출자·이자라·제작금융 문서를 검토했습니다. 무라바하 고정가격만으로 원가·이익 공개 조건을 추정하지 않았고, 살람의 보증문구만으로 전액 선지급·미래 인도 계약을 추정하지 않았습니다.',next_search_ko='수탁 스테이킹 종료 지시와 자산 회수 조건, 원가·이익 공개 실자산 매매계약, 전액 선지급 살람 실행조건의 직접 자체 문서를 보강합니다.',disposition='bounded_alternative_review'))
 assert len(by)==66 and all(by.values()),[w for w,g in by.items() if not g];newcovered={w for b in rows for w in b['ui_work_ids']};auditrows=[]
 for w in base['works']:
  if w['id'] not in initial:continue
  gs=by[w['id']];sids=sorted({sid for g in gs for sid in g['reviewed_source_ids']});assert all(sid in sources for sid in sids),(w['id'],sids);st=[s for s in staged if s['work_id']==w['id']];status='linked' if w['id'] in newcovered else 'candidate_not_admitted' if st else 'insufficient_direct_result' if any(g.get('disposition',g.get('status')) in ['insufficient_direct_result','insufficient_evidence','positive_candidate','candidate_pending_root_review'] for g in gs) else 'no_relevant_source_found';reason='공식 자체 원문의 해당 고객 결과를 최종 검토해 연결했습니다. 실제 개인 금융거래·설치 앱 UI는 관찰하지 않았습니다.' if status=='linked' else ' '.join(s['reason_ko'] for s in st) if st else ' '.join(dict.fromkeys(g['reason_ko'] for g in gs))
  auditrows.append(dict(work_id=w['id'],title=w['title'],reviewed_source_ids=sids,root_status=status,reason_ko=reason,next_search_ko='공식 조작 화면·현지 적용 조건을 보강하고 판본·실무 적용성을 확인합니다.' if status=='linked' else ' '.join(dict.fromkeys(g.get('next_search_ko',g.get('next_search_direction_ko','직접 결과를 설명한 현지 자체 문서를 추가 조사합니다.')) for g in gs)),root_example_ids=[b['id'] for b in rows if w['id'] in b['ui_work_ids']],reviewed_sources=[dict(source_id=sid,url=sources[sid]['url'],state=sources[sid]['state'],raw_sha256=sources[sid].get('raw_sha256')) for sid in sids],review_pool_count=len(gs),provider_support_inferred=False))
 assert len(auditrows)==len({g['work_id'] for g in auditrows})==66
 audit=dict(scope_version=base['version'],denominator=216,baseline_collection_version='collection-v32',initial_unlinked_works=66,newly_linked_works=len(initial&newcovered),remaining_unlinked_works=len(initial-newcovered),root_status_counts=dict(collections.Counter(g['root_status'] for g in auditrows)),rows=auditrows,artifact_path='data/bank-ui-public-collection-v33.json',previous_audit_artifact='data/bank-ui-public-collection-v32.json',review_scope='bounded_official_original_inventory_not_exhaustive_worldwide_provider_search',requires_user_account_for_public_collection=False,all_provider_support_examined=False,automatic_adoption=False);write(R/'data/bank-ui-public-collection-v33.json',audit)
 for path,payload in PENDING:
  path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 print({'admitted_examples':len(rows),'new_work_links':len(initial&newcovered),'remaining':len(initial-newcovered),'gateway_jobs':len(runs),'attempts':attempt_count,'source_stats':stats,'new_targets':len(plan['provider_targets'])-22,'audit_statuses':audit['root_status_counts']})
