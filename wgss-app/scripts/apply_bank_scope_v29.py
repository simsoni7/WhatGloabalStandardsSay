# One-time v29 recorder/preparer. Already executed; frozen files must not be overwritten.
import copy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/bank-scope-v29-20261012'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def main():
 dest=R/'data/bank-ui-scope-v1_1-decisions.json';assert not dest.exists();current=read(R/'data/bank-ui-root-decisions.json');assert current['scope_version']=='bank-customer-ui-v1' and len(current['catalogue']['works'])==214
 write(R/'data/bank-ui-scope-v1-baseline.json',current);baseline=read(R/'dist/data/bank-ui.json');baseline['csv_artifacts']={name:(R/'dist/data'/name).read_text() for name in ['bank-ui-collection-matrix.csv','bank-ui-priority-matrix.csv','bank-ui-works.csv']};write(R/'data/bank-ui-baseline-v28.json',baseline)
 proposal=read(RUN/'root-corrected-proposals.json');review=read(next((RUN/'reviews/v29-scope-final-review').glob('*/proposal.json')));assert {x['id'] for x in review['result']['rows']}=={x['id'] for x in proposal['rows']};assert all(x['status'] in ['pass','correct'] for x in review['result']['rows']);d=copy.deepcopy(current);ws={w['id']:w for w in d['catalogue']['works']};changes=[];added=[]
 for row in proposal['rows']:
  if row['kind']=='metadata_correction':
   w=ws[row['id']];before={k:w[k] for k in row['changes']};w.update(row['changes']);w.setdefault('semantic_key_aliases',[])
   if 'semantic_key' in before:w['semantic_key_aliases'].append({'scope_version':'bank-customer-ui-v1','key':before['semantic_key']})
   changes.append({'work_id':row['id'],'before':before,'after':row['changes'],'root_decision':'correct_metadata_to_existing_intent','reason_ko':row['rationale_ko'],'automatic_adoption':False})
  else:
   w=copy.deepcopy(row['proposal']);w['scope_approved']=True;w['new_result_key']='account-restriction-review-request' if 'restriction' in w['object_key'] else 'payment-channel-profile-limit';w['standard_mapping_status']='provider_counterexample_extension_not_claimed_as_ISO_native_work';d['catalogue']['works'].append(w);added.append({'work_id':w['id'],'own_source':row['own_source'],'root_decision':'admit_distinct_customer_result','duplicate_boundary_work_ids':['WGSS-UI-DFEB572279B8','WGSS-UI-F94E9EA98403','WGSS-UI-90C17493858A'],'automatic_adoption':False})
 assert len(d['catalogue']['works'])==216 and len({tuple(w['semantic_key']) for w in d['catalogue']['works']})==216
 version='bank-customer-ui-v1.1';d['scope_version']=version;d['catalogue']['version']=version;d['catalogue']['scope']['version']=version;d['catalogue']['scope']['freeze_rule']='버전1의214개에자료수집중확인한독립고객결과2개를더하고필드불일치3개를정정한WGSS은행고객UI수집범위v1.1. 기존214개ID를보존하며ISO공식총수·세계전체MECE·업체지원승인을뜻하지않는다.'
 d['catalogue']['scope']['completeness_universe']+=' + v1.1: 금융사 자체 문서의 이용제한 해제 심사 신청과 지급채널 프로필 한도 변경 반례를 기존214개와 대조.'
 audit=d['catalogue']['audit'];audit['scope_revision']={'version':version,'baseline_works':214,'new_source_counterexamples':2,'metadata_corrections':3,'latest_revision_review_rows':5,'original_v1_full_review_rows':214,'global_financial_mece_approved':False};audit['known_customer_outcome_gaps']=0
 audit['gates'][-1]['note']='버전1의214개전수검토를보존하고v1.1의자체출처반례2개·필드정정3개를추가대조했다. 계좌·채널·심사요청·직접변경을구분하며표준만으로업체지원을추정하지않는다.'
 d['scope_revision_ledger']=str(dest.relative_to(R));write(R/'data/bank-ui-root-decisions.json',d)
 bank=read(R/'data/bank-ui-benchmark-dispositions.json');bank['scope_version']=version;write(R/'data/bank-ui-benchmark-dispositions.json',bank)
 plan=read(R/'data/bank-ui-collection-plan.json');plan.update(scope_version=version,denominator=216,collection_scope_works=216,scope_change=True,scope_revision_ledger=str(dest.relative_to(R)));plan['closed_definition_review_gaps']=[dict(x,status='resolved_in_v1.1',resolved_work_id=added[i]['work_id']) for i,x in enumerate(plan['definition_review_gaps'])];plan['definition_review_gaps']=[];write(R/'data/bank-ui-collection-plan.json',plan)
 capture=read(R/'data/bank-ui-capture-plan.json');capture.update(scope_version=version,planned_works=216,country_work_cells=648,scope_change=True);write(R/'data/bank-ui-capture-plan.json',capture)
 ledger={'scope_version':version,'baseline_scope_version':'bank-customer-ui-v1','baseline_works':214,'current_works':216,'new_works':added,'metadata_corrections':changes,'source_work_ids_preserved':sorted(ws),'source_unit_rule':'authorised_actor+direct_object+intended_result, no country/product/channel clones','root_reviewed':True,'global_financial_mece_approved':False,'automatic_adoption':False,'independent_human_review':False,'opus_review':read(next((RUN/'reviews/v29-scope-boundary-critic').glob('*/proposal.json'))),'sonnet_review':review,'root_model_disposition_ko':'초기채널일반화지적은현재증거를기업1차이용자·일일프로필로좁혀반영. 최종모델의correct는메타정정의정합성설명이며추가요구사항으로자동해석하지않음. 각원문·기존의도와루트에서대조.'};write(dest,ledger);print({'scope':version,'works':216,'new':2,'corrected':3})
if __name__=='__main__':main()
