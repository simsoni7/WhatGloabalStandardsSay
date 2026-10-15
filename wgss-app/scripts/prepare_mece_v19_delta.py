"""Freeze reviews of the actual post-decision catalogue and steward objections."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'research/source-store/mece-closure-20261011'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
d=read(ROOT/'dist/data/operations.json');root=read(ROOT/'data/mece-v19-root-dispositions.json');by={w['id']:w for w in d['works']}
write(RUN/'catalogue-after.json',d)
compact=[{k:w[k] for k in ['id','title','actor_role','object_key','outcome_key','discriminator','definition','includes','excludes']} for w in d['works']]
ids=list(dict.fromkeys(r['work_id'] for r in root['actions']))
sections={ref['id']+'|'+str(n):ref['exact_quote'] for w in d['works'] for n,ref in enumerate(w['refs']) if ref.get('exact_quote')}
for n,start in enumerate(range(0,len(ids),9),1):
    assigned=ids[start:start+9]
    job={'id':f'current-delta-v19-{n:02}','model':'claude-opus-5','max_tokens':20000,
      'instructions':'''Return JSON only {"rows":[{"id":assigned work id,"decision":"retain|needs_boundary_edit|merge_existing|needs_source","work_ids":relevant current IDs only,"evidence_section_ids":supplied section IDs only,"reason":Korean,"next_action":Korean}]}.
Review the actual current definitions, whole catalogue, original functional quotes and root qualifications. You are advisory; no automatic adoption or global/human approval. Check genuine responsibility/direct object/result, parent-child overlap, counterpart clones, source gaps and overbroad legal claims. Source text may specify a function without being legislation; use actual functions, not names. Distinguish bank service access authority from debtor collection authority and master legal coverage. Policy output vs risk information vs transaction judgment are different only with explicit objects. A filed contract FORM with blank date proves a described responsibility, not an executed contract, SEC approval, current universal law, or UI. Safekeeping assumption is not ledger movement, key control or transfer of legal trust title. Plan artifact is not goals, advice or assessment. Securities loan effect is a condition on actual transfers, not a separate state work. Do not fix source audit incompleteness by pretending these definitions have global CE coverage. Return exactly assigned IDs.''',
      'input':{'catalogue':compact,'assigned_definitions':[by[i] for i in assigned],'root_qualifications':root['root_qualifications'],'sections':sections},
      'expected_ids':assigned,'row_key':'id','work_ids':list(by),'sections':sections,'grounded_section_ids':True}
    write(RUN/'inputs'/(job['id']+'.json'),job)
assigned=root['added_work_ids'];job={'id':'quality-steward-v19','model':'claude-sonnet-5','max_tokens':20000,
 'instructions':'''Act as the product quality steward representing the user. Return JSON only {"rows":[{"id":assigned definition ID,"decision":"no_new_defect|boundary_defect|source_overclaim|overlap_or_gap","work_ids":current catalogue IDs only,"evidence_section_ids":supplied IDs only,"reason":Korean,"next_action":Korean}],"system_findings":[{"id":string,"severity":"high|medium|low","reason":Korean,"next_action":Korean}]}.
Try to falsify each newly admitted financial result against the whole catalogue and original quotes. Verify root qualifications are followed. No global/human approval. An administration/maintain verb does not prove all lifecycle outcomes. Check exclusions/constraints and counterpart/method/time clones, role types, missing result discovery and source validation. Specifically consider third-party service access vs direct-debit collection authority; master contractual coverage; safekeeping acceptance vs appointment/position move/trust ownership; policies vs generic corporate management. Assess whether the remaining work, source CE counts and standards-scope plan hide blockers. Current 382 registration is not an approved global total and collection remains blocked. Do not demand screenshots to establish a standards function; provider UI admission is a later separate gate. Return exactly assigned definition rows and bounded actionable system findings.''',
 'input':{'catalogue':compact,'assigned_definitions':[by[i] for i in assigned],'root_decisions':root,'checkpoint':read(ROOT/'data/mece-closure-review.json'),'sections':sections},
 'expected_ids':assigned,'row_key':'id','work_ids':list(by),'sections':sections,'grounded_section_ids':True}
write(RUN/'inputs'/(job['id']+'.json'),job)
print(json.dumps({'current_count':len(by),'delta_ids':len(ids),'jobs':3}))
