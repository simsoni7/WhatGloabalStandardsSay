"""Apply explicit root dispositions once; never adopt Bedrock JSON automatically."""
import copy,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/mece-closure-v21-20261011';STORE=RUN/'sources'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
ledger=read(R/'data/operation-backbone-dispositions.json')
assert not ledger.get('v21_results_applied'),'Already applied; frozen migration cannot be rerun'
before=read(RUN/'catalogue-before.json');by={w['id']:w for w in before['works']};assert len(by)==394
version='WGSS-operation-v1.11-review-20261011'
def text(sid,store=STORE):return (store/read(store/(sid+'.json'))['text_path']).read_text()
def paragraph(sid,needle,length=350,store=STORE):
    t=text(sid,store);at=t.index(needle);return t[at:at+length]
def ref(sid,quote,locator,store=STORE):
    m=read(store/(sid+'.json'));assert not m.get('functional_evidence_rejected')
    assert quote in text(sid,store)
    assert hashlib.sha256((store/m['raw_path']).read_bytes()).hexdigest()==m['sha256']
    assert hashlib.sha256((store/m['text_path']).read_bytes()).hexdigest()==m['text_sha256']
    return dict(id='WGSS-PROCESS-'+sid,name=sid.replace('_',' '),url=m['url'],locator=locator,exact_quote=quote,source_sha256=m['sha256'],source_store_relative=str(store.relative_to(R)),source_snapshot_id='WGSS-primary-functional-v21-20261011',context_requires_review=False,proof_scope='conditional_official_function_not_global_law_executed_contract_or_provider_ui',rationale='원문 책임·대상·완료 조건의 기능 근거입니다. 특정 관할·제출 약정 조건을 보편 권리로 주장하지 않습니다.')
loanstore=R/'research/source-store/mece-closure-v20-20261011/sources';loan='SEC_LOAN_MATURITY_SELECTED'
def line(n):
    m=re.search(r'^L'+str(n)+r': (.*)$',text(loan,loanstore),re.M);assert m;return m[1]
loanrefs=[ref(loan,line(n),'§2.9, L'+str(n),loanstore) for n in [962,964,965,966]]
policyref=ref('SEC_TRUST_POLICY_AUTHORITY','Consistent with the requirements of this Declaration of Trust, the Trustees shall establish policies from time to time with respect to investments and borrowings and the Trustees may establish policies with respect to other matters related to the administration of the Trust. Such policies shall be made in writing.','§3.8 Written Policies, L426')
registrationref=ref('FUND_POLICY_REGISTRATION',paragraph('FUND_POLICY_REGISTRATION','(1) a recital of the policy of the registrant',450),'2024 USC 15 §80a-8(b)(1)-(3)')
changeref=ref('FUND_POLICY_CHANGE',paragraph('FUND_POLICY_CHANGE','No registered investment company shall',1050),'2024 USC 15 §80a-13(a)(1)-(3)')
new=[];edits=[]
def add(suffix,title,layer,category,role,obj,result,definition,includes,excludes,near,refs,conditions,family):
    i='WGSS-MECE-'+suffix
    w=dict(id=i,title=title,layer=layer,category=category,actor_role=role,actor_label='금융 업무 책임자 · '+role.replace('_',' '),object_key=obj,outcome_key=result,outcome=result.replace('_',' '),discriminator=None,definition=definition,includes=includes,excludes=excludes,boundary=dict(related_ids=near,distinction='요청과 최종 권리 결과, 최초 성립과 기존 조건 변경을 구분합니다. 상품·관점·방법만으로 복제하지 않습니다.'),refs=copy.deepcopy(refs),status='edited',source_gaps=[],input_ids=[],origin_unit_id='MECE-CLOSURE-'+suffix,review_note='v21 root 원문 대조 편집입니다. 전체 MECE·관할 법률의 현재 유효성·특정 업체 UI 승인이 아닙니다.',definition_is_wgss_editorial=True,independent_human_review=False,mece_approved=False,applicability_conditions=conditions)
    new.append(w);return i,family
end,fend=add('CREDIT-FACILITY-END','약정 신용한도 이용권 종료','customer','lending-trade','credit_facility_holder','committed_credit_availability_right','terminate_committed_credit_availability_right',
 '약정 신용한도 보유자가 계약상 종료권을 유효하게 행사하여 효력일에 이후 자금을 이용할 수 있는 약정 권리를 종료시키는 결과. 종료 통지의 제출만 완료된 상태와 구분하며, 이미 인출한 대출의 원리금 채무 소멸을 뜻하지 않는다.',
 ['약정상 조건을 충족한 전부 종료권 행사의 효력 발생'],['해지 요청·통지 제출만 완료','남아 있는 한도의 부분 감액','미상환 원리금 지급·대출채무 소멸','신디케이트 가입·대주 지위 양도','단순 만기 상태 표시·자동 만료를 별도 행위로 복제'],
 ['WGSS-9A4B541DD443','WGSS-CB2F5FE40642','WGSS-860722E7067D','WGSS-MECE-LENDER-POSITION-ASSIGNMENT'],loanrefs,
 ['2016년 SEC 제출 약정 §2.9의 차주 종료권을 조건부 기능 근거로 사용합니다. 모든 상품에 차주의 일방 해지권이 있다고 주장하지 않습니다.','해당 약정의 통지기한·동시 선상환 후 익스포저 조건·효력일 및 다른 조달의 성립을 전제로 한 철회 예외를 확인해야 합니다. 금액·기한은 개별 조건입니다.','§2.9(c)는 대리인의 대주 통지 전달을 기술합니다. 대리인의 독립적인 승인·법적 효력 확정 권한을 주장하거나 별도 업무로 추가하지 않습니다.'],'lending')
reduction,fred=add('CREDIT-FACILITY-REDUCTION','약정 신용한도 부분 감액','customer','lending-trade','credit_facility_holder','committed_credit_availability_amount','reduce_committed_credit_availability_preserving_facility',
 '약정 신용한도 보유자가 계약상 감액권을 유효하게 행사하여 효력일에 이후 이용할 수 있는 약정 금액을 영구 축소하되, 신용한도 이용관계 자체는 유지하는 결과. 변경 요청 제출, 내부 여신 익스포저 한도 설정 및 전부 종료와 구분한다.',
 ['약정 이용관계를 유지하는 부분 감액의 효력 발생'],['감액 요청·통지 제출만 완료','전부 종료로 이용관계 자체가 사라지는 결과','신규 신용한도 계약 성립','증액 승인·자동 증액을 이 감액 근거로 주장','기관 내부 익스포저 한도 설정','신용카드 이용한도 변경·송금 운영한도 설정'],
 ['WGSS-9EAFFE368698','WGSS-CB2F5FE40642',end,'WGSS-779616C3F2C3','WGSS-EFEFBF6B2926','WGSS-300AFCA6B252'],loanrefs,
 ['2016년 제출 약정의 부분 감액권만 입증합니다. 모든 기관·상품의 변경권 또는 증액 승인을 같은 원문으로 주장하지 않습니다.','완료 조건은 단순 접수가 아니라 약정 요건 충족 후 효력일에 이용 가능 약정액이 영구 축소되는 것입니다. 해당 약정에서는 대주별 Applicable Percentage에 따라 적용됩니다.','부분 감액은 관계 유지, 전부 종료는 권리 소멸이라는 결과가 다릅니다. 금액 크기만으로 여러 업무를 만들지 않습니다.'],'lending')
policychange,fpolicy=add('FUND-POLICY-AMENDMENT','펀드 투자정책 변경 확정','institution','investments-custody','fund_investment_policy_authority','existing_collective_investment_policy','make_collective_investment_policy_amendment_effective',
 '펀드 차원의 투자정책 책임자가 기존 허용·배제 자산, 차입·집중 등 운용 규칙의 변경에 필요한 권한·승인 요건을 충족하여 변경된 정책을 유효하게 확정하는 결과. 지분권자 의결은 해당 정책 변경의 효력 조건이며 별도 관점 업무로 복제하지 않는다.',
 ['기존 펀드 투자정책의 유효 변경','적용 규칙이 요구하는 지분권자 의결을 충족한 근본 정책 변경'],['최초 투자정책 헌장 수립','의결 제안·변경 요청만 제출','지분권자 의결 횟수·정책별 상품명을 별도 결과로 복제','개인 투자자의 일임 운용지침 합의','펀드 법적 관계·시리즈 분리 책임재산 설정','정책에 따른 개별 매매 실행'],
 ['WGSS-D04C78B35E3E','WGSS-AF6645904647','WGSS-MECE-FUND-SERIES-ESTABLISHMENT'],[changeref,registrationref],
 ['2024 미국법전 §80a-13(a)의 해당 등록 투자회사·정책에 한정된 기능 근거입니다. 모든 국가·펀드·정책의 변경에 동일한 지분권자 과반 의결이 필요하다고 주장하지 않습니다.','주체·정관·정책 종류에 맞는 권한과 변경 효력 조건을 확인합니다. 승인 조건 충족 전에는 변경 완료로 표시하지 않습니다.'],'securities')
def context_refs(i):
    refs=copy.deepcopy(by[i]['refs'])
    for r in refs:
        if not r.get('exact_quote'):
            r.update(context_requires_review=True,proof_scope='concept_or_legacy_context_not_direct_functional_proof')
    return refs
def edit(i,**fields):
    fields['review_note']='v21 전체 현행 정의·원문 기능 경계를 대조했습니다. 세계 금융 전체 MECE 확정 또는 현재 업체 UI 관측은 아닙니다.'
    edits.append(dict(id=i,fields=fields,reason='상품 범위·요청/효력 및 최초/변경 경계를 직접 결과 단위로 정리했습니다.'))
edit('WGSS-D04C78B35E3E',title='펀드 투자정책 헌장 수립',actor_role='fund_investment_policy_authority',actor_label='펀드 투자정책 책임자',object_key='collective_investment_policy_charter',outcome_key='establish_collective_investment_policy_charter',outcome='establish collective investment policy charter',discriminator=None,
 definition='펀드 차원의 투자정책 책임자가 단일 투자정책으로 운용되는 자금풀의 허용·배제 자산 및 차입·집중 등 운용 규칙을 최초 헌장으로 확정하는 결과. 일반 펀드와 샤리아 기준을 적용하는 펀드는 동일 결과의 적용 조건으로 보존한다.',
 includes=['펀드 차원의 최초 투자정책 헌장 수립','샤리아 자산 허용·배제 기준을 적용한 정책 수립'],excludes=['기존 펀드 투자정책 변경 확정','개별 투자자의 일임 운용지침 합의','샤리아 전문위원회의 별도 적격성 심사','신탁 법적 관계·시리즈 분리 책임재산 설정','정책 등록·보고서 제출 자체','회계·운용보수·성과보수 처리'],
 refs=context_refs('WGSS-D04C78B35E3E')+[policyref,registrationref],applicability_conditions=['제출된 투자신탁 선언서 §3.8은 수탁이사들의 서면 정책 수립 책임을 조건부로 입증합니다. 모든 펀드의 동일 책임 주체·서면 요건으로 일반화하지 않습니다.','미국법전 §80a-8(b)는 등록 투자회사의 정책 기재 요건이며 법인 설립·등록 제출 또는 감독기관 승인 완료를 뜻하지 않습니다.','기존 샤리아 조건을 유지합니다. 허용·배제 자산은 해당 펀드의 정책 조건이며 상품명으로 별도 업무를 만들지 않습니다.'])
for i,title,obj,outcome,definition,inc,exc in [
 ('WGSS-9A4B541DD443','약정 신용한도 해지 요청 제출','committed_credit_facility_termination_request','submit_committed_credit_facility_termination_request','약정 신용한도 보유자가 계약상 경로로 한도의 전부 해지 요청·통지를 제출하는 결과. 직접 완료는 제출이며, 효력일의 이용권 종료나 이미 인출한 원리금 정산을 포함하지 않는다.',['계좌 연계 당좌대월을 포함한 약정 신용한도 전부 해지 요청·통지 제출'],['부분 한도 변경 요청','효력일의 약정 이용권 종료','원리금 상환·채무 소멸']),
 ('WGSS-9EAFFE368698','약정 신용한도 변경 요청 제출','committed_credit_facility_amount_change_request','submit_committed_credit_facility_amount_change_request','약정 신용한도 보유자가 한도의 증액·감액 요청·통지를 제출하는 결과. 요청 제출은 승인·효력 발생·실제 자금 이용과 구분하며, 증액과 감액은 요청 내용 조건이다.',['계좌 연계 당좌대월을 포함한 약정 신용한도 금액 변경 요청·통지 제출'],['전부 해지 요청','기관 승인 또는 약정 금액 변경 효력 발생','송금 운영한도·신용카드 한도 변경','실제 인출·지급'])]:
    edit(i,title=title,object_key=obj,outcome_key=outcome,outcome=outcome.replace('_',' '),discriminator='submission_only_not_legal_effect_or_fund_disbursement',definition=definition,includes=inc,excludes=exc,refs=context_refs(i)+loanrefs,
         applicability_conditions=['HSBC 당좌대월 안내의 고객 요청과 제출 대출약정 §2.9의 통지라는 기능 사례를 함께 사용합니다. 요청 승인이 필요하다는 조건을 모든 통지로 일반화하지 않습니다.','해당 약정의 종료·감액 통지는 원칙적으로 취소불능이지만 다른 조달 성립 조건이 실패하면 철회 가능한 예외가 있습니다. 모든 요청의 보편 취소불능성을 주장하지 않습니다.'])
edit('WGSS-CB2F5FE40642',excludes=by['WGSS-CB2F5FE40642']['excludes']+['기존 약정 이용권의 전부 종료·부분 감액','한도 변경·해지 요청 제출'],refs=context_refs('WGSS-CB2F5FE40642'))
edit('WGSS-MECE-LENDER-POSITION-ASSIGNMENT',excludes=by['WGSS-MECE-LENDER-POSITION-ASSIGNMENT']['excludes']+['약정 신용한도 이용권의 전부 종료·부분 감액'])
assert len(new)==3 and len(edits)==5
ledger['additions']+=new
existing={e['id']:e for e in ledger['edits']}
for e in edits:
    if e['id'] in existing:existing[e['id']]['fields'].update(e['fields']);existing[e['id']]['reason']=e['reason']
    else:ledger['edits'].append(e)
ledger.update(new_version=version,v21_results_applied=True);write(R/'data/operation-backbone-dispositions.json',ledger)
nav=read(R/'data/business-backbone-review.json');nav['operation_version']=version
for i,f in [(end,fend),(reduction,fred),(policychange,fpolicy)]:nav['assignments'].append(dict(id=i,family_id=f,ambiguous=False,reason='独立 결과에 따른 탐색 경로; 전체 금융 모수 승인이 아닙니다.'))
write(R/'data/business-backbone-review.json',nav)
prior=read(R/'data/mece-v20-root-dispositions.json');tickets=read(RUN/'checkpoint-before.json')['remaining_work']
closed={'CANDIDATE-ServiceDomain:44473#0':['WGSS-D04C78B35E3E',policychange],'CANDIDATE-ServiceDomain:38742#0':[end,reduction,'WGSS-9A4B541DD443','WGSS-9EAFFE368698','WGSS-860722E7067D','WGSS-1A0EF50D7D0F']}
rows=[];remaining=[]
for t in tickets:
    done=t['id'] in closed
    reason=('펀드 최초 정책과 기존 정책 변경을 직접 원문으로 분리하고 상품 전용 정의를 일반화했습니다. 펀드 전체 CE는 추가 원문 그룹에 남습니다.' if t['id'].endswith('44473#0') else '신용약정 해지·감액의 요청 제출과 유효 권리 변경을 분리했습니다. 대리인 승인을 만들지 않았으며 신디케이트 가입·원금 상환과도 구분했습니다. 전체 대출 조성·서비싱 CE는 후속에 남습니다.') if done else t['next_action']
    rows.append(dict(id=t['id'],state='closed_root_decision' if done else 'pending_source_boundary',work_ids=closed.get(t['id'],t['work_ids']),reason=reason,automatic_adoption=False))
    if not done:remaining.append(copy.deepcopy(t))
followups=copy.deepcopy(prior['source_followups'])
followups.append(dict(id='V21-CE-SYNDICATED-SERVICING',title='신디케이트 대출 조성·서비싱 추가 책임',next_action='BIAN의 Mandate Letter·Term Sheet 협상, 트랜치 준비, 만기 시 기관 수납·채무 기록을 기존 책임에 명시적으로 연결합니다. 포괄 조성·만기 처리를 새 부모 업무로 등록하지 않으며 미포함 결과·입증 공백을 보존합니다.',source_ids=['SEC_LOAN_MATURITY_SELECTED']))
sources=[]
for native,ids,reason in [
 ('44473',['WGSS-ADD-D0A1ACA9428E','WGSS-ADD-555BDFC74CD7','WGSS-D04C78B35E3E',policychange,'WGSS-MECE-FUND-SERIES-ESTABLISHMENT'],'펀드 차원의 정책 헌장·변경과 투자자 유입·유출·분리 책임재산을 분리했습니다. 회계·세무·보고·보수·총괄 서비싱의 전체 포함은 미확정입니다.'),
 ('38742',['WGSS-MECE-LENDER-POSITION-ASSIGNMENT','WGSS-MECE-LOAN-PARTICIPATION-SALE','WGSS-1A0EF50D7D0F','WGSS-860722E7067D','WGSS-DE4E23D3BB89',end,reduction],'대주 지위 이전·참여분 매각, 신용약정 종료·감액, 차주 만기 지급과 분담금 정산을 연결했습니다. 약정 종료를 신디케이트 가입에 연결하지 않습니다. Mandate/Term Sheet 및 기관 수납·기록 전체 범위는 추가 검토입니다.')]:
    s=copy.deepcopy(next(s for s in read(R/'data/mece-closure-review.json')['source_dispositions'] if s['reference_key']=='ServiceDomain:'+native))
    s.update(work_ids=ids,reason=reason,review_phase='v21-own-source-root-review');sources.append(s)
root=dict(version='WGSS-mece-closure-v21-20261011',input_version=before['version'],output_version=version,rows=rows,remaining_work=remaining,added_work_ids=[w['id'] for w in new],edited_work_ids=[e['id'] for e in edits],source_dispositions=sources,source_followups=followups,automatic_adoption=False,independent_human_review=False,global_mece_approved=False,root_corrections=['상품명은 복제 기준이 아닙니다. 기존 당좌대월 요청을 약정 신용한도 요청으로 일반화합니다.','대리인의 통지 전달을 독립적인 승인·법적 효력 확정 권한으로 바꾸지 않습니다.','전부 종료와 관계를 유지하는 부분 감액은 권리 소멸과 금액 변경이라는 다른 결과입니다.','정책 변경의 의결은 효력 조건이며 관점별 승인 업무로 복제하지 않습니다.','원문 일부를 연결해도 전체 금융계정 통제·규제 시정·조달 부모는 미해결 결과가 남으면 종결하지 않습니다.'])
write(R/'data/mece-v21-root-dispositions.json',root)
p=read(R/'data/mece-closure-review.json');p.update(version=root['version'],output_version=version,current_stage='v21_actual_delta_review_pending',technical_validation=dict(state='pending',automatic_adoption=False));write(R/'data/mece-closure-review.json',p)
print(json.dumps({'before':394,'added':len(new),'edited':len(edits),'after':397,'local_tickets_closed':len(closed),'remaining':len(remaining),'source_followup_groups':len(followups)}))
