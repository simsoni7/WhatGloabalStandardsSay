"""Freeze actionable closure tickets and bounded reviews; never adopt proposals."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'research/source-store/mece-closure-20261011'
def read(p): return json.loads(p.read_text())
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
catalogue=read(ROOT/'dist/data/operations.json')
progress=read(ROOT/'data/mece-closure-review.json')
sources=read(ROOT/'research/source-store/mece-closure-20261006/source-input.json')
by={r['reference_key']:r for r in sources}
scope=read(ROOT/'research/source-store/operation-v12/basis/scope.json')
write(RUN/'catalogue-before.json',catalogue)
write(RUN/'checkpoint-before.json',progress)
write(RUN/'source-input.json',sources)
compact=[{k:w[k] for k in ['id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes']} for w in catalogue['works']]
extra={
 'REINSURANCE-RISK-DECISION':[], 'TREASURY-RATE-PUBLICATION':['ServiceDomain:46157'],
 'MASTER-AGREEMENT-LIFECYCLE':['ServiceDomain:31459','ServiceDomain:28808'],
 'CORRESPONDENT-RECIPROCITY':['ServiceDomain:34643'],
 'NETWORK-PARTICIPATION-LIFECYCLE':['ServiceDomain:36870'],
 'SECURITIES-LOAN-LIFECYCLE':[],
}
tickets=[]
for row in progress['remaining_work']:
    keys=[]
    if row['id'].startswith('CANDIDATE-'): keys=[row['id'].removeprefix('CANDIDATE-').split('#')[0]]
    if row['id'].startswith('SOURCE-RESULT-'): keys=extra[row['id'].removeprefix('SOURCE-RESULT-')]
    sections=[s for k in keys for s in by[k]['own_sections']]
    if row['id'].endswith('REINSURANCE-RISK-DECISION'):
        for s in sources:
            if 'reinsurance' in s['name'].lower(): sections+=s['own_sections']
    if row['id'].endswith('SECURITIES-LOAN-LIFECYCLE'):
        text=(ROOT/'research/source-store/mece-closure-20261005/sources/SEC_FILED_SECURITIES_LOAN.txt').read_text()
        sections.append({'section_id':'PRIMARY:SEC-LOAN','text':text})
    tickets.append({**row,'source_keys':keys,'sections':sections,
        'done_conditions':['실제 원문에서 책임·직접 대상·독립 완료 결과 확인','현재 전체 정의와 중복·상위/하위 포함 비교','복합 결과를 분해하고 원문이 입증하지 않는 결과는 갭으로 보존','root 판정과 원문 앵커를 별도 기록; 변경 시 전체 회귀'],
        'decision_options':['register_independent_result','covered_existing_result','reject_unproven_hypothesis_preserve_source_gap','split_to_atomic_followups','excluded_explicit_scope'],
        'automatic_adoption':False})
write(RUN/'tickets.json',tickets)
instructions='''You are the WGSS substantive closure reviewer. Return JSON only: {"rows":[{"id":exact assigned ticket id,"decision":one decision option,"work_ids":existing IDs only,"evidence_section_ids":supplied own section IDs only,"reason":Korean,"atomic_results":[{"title":Korean,"actor_role":snake_case,"object_key":snake_case,"outcome_key":snake_case,"discriminator":string or null,"definition":Korean,"nearest_work_ids":existing IDs only,"evidence_section_ids":supplied IDs only,"recommendation":"add|covered|gap|excluded","reason":Korean}],"next_action":concrete Korean action or "closed"}]}.
Review the entire current catalogue to prevent keyword patches and nominal product clones. Follow the declared scope. No human/global approval. A sparse noun, source parent, counterpart viewpoint, method, date, bank name, or status must not manufacture independent work. A financial policy or authority with a genuinely different direct object can be in scope; generic HR/marketing/IT is excluded. Creation/request/judgment/execution are distinct only when directly specified. Do not assume generic maintain proves every lifecycle verb. For each financial result clearly specified by a supplied clause, say if an existing definition really includes its full scope, needs a boundary edit or is missing. Keep unsupported legal duties and unspecified results as gaps. A new result is a recommendation, never registration. Return exactly assigned IDs, no extra rows. Do not echo evidence quotes: cite supplied section IDs. Empty evidence means a proof gap. Never set next_action to none/없음 for an open result. Consider policy directives vs independent large-trade approval, access mandate formation vs activity coverage judgment, closed unit trust transfer vs fund creation/nominee registration, financial performance corrections vs law compliance, trader authority vs customer channel access, syndicated participation rights vs membership/pool securitization, fund legal formation vs charter, funding parent vs atomic funding outcomes, NAV vs valuation, plan artifact vs goals/advice/assessment, issuer entitlement/payment vs custodian payment, future portfolio value vs current instrument value, ordinary safekeeping vs crypto/plan custody, account control compound vs reconciliation/payment approval.'''
for n,start in enumerate(range(0,len(tickets),7),1):
    batch=tickets[start:start+7];sections={s['section_id']:s['text'] for t in batch for s in t['sections']}
    job={'id':f'closure-tickets-v19-{n:02}','model':'claude-opus-5','max_tokens':24000,'instructions':instructions,
         'input':{'scope':scope,'catalogue':compact,'tickets':batch},'expected_ids':[t['id'] for t in batch],
         'row_key':'id','work_ids':[w['id'] for w in compact],'sections':sections,'grounded_section_ids':True}
    write(RUN/'inputs'/(job['id']+'.json'),job)
# Explicit root-selected nonfinancial operational domains. Selection is a review
# batch, not an exclusion rule; own clauses must still justify each disposition.
ids=['29101','29475','30604','30904','30911','31008','31034','32097','33231','33514','33924','34170','34291','35210','36108','36250','37168','37174','37520','38385']
batch=[by['ServiceDomain:'+i] for i in ids]
sections={s['section_id']:s['text'] for t in batch for s in t['own_sections']}
job={'id':'scope-own-text-v19-01','model':'claude-opus-5','max_tokens':16000,
 'instructions':'''Return JSON only {"rows":[{"reference_key":exact assigned key,"decision":"excluded_scope|source_specification_gap|requires_financial_decomposition","exclusion_id":"X01|X03|X06" or null,"work_ids":[],"evidence_section_ids":own supplied IDs only,"reason":Korean,"financial_results_if_any":[],"next_action":Korean}]}. Apply scope to OWN text, never labels/ancestors alone. Every explicit financial responsibility in any own clause must be preserved. A workforce expense/payroll operation is an excluded employer duty; a bank's client payment service is included. Internal IT operation is excluded, but customer authentication/authority outcomes are included and prevent blanket exclusion. Read all own clauses. Return exactly assigned keys. No global approval or automatic adoption.''',
 'input':{'scope':scope,'sources':batch},'expected_ids':[x['reference_key'] for x in batch],
 'row_key':'reference_key','work_ids':[],'sections':sections,'grounded_section_ids':True}
write(RUN/'inputs'/(job['id']+'.json'),job)
print(json.dumps({'tickets':len(tickets),'definition_snapshot':len(compact),'scope_rows':len(batch),'jobs':5}))
