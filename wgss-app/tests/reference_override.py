"""A merged historical source cannot resurrect quarantined functional proof."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_operations import apply_closure
canonical={'id':'CANONICAL','layer':'institution','actor_role':'account_servicer','object_key':'financial_account','outcome_key':'account_result','discriminator':None,'outcome':'account result','actor_label':'account servicer','input_ids':['current'],'refs':[{'id':'SOURCE','url':'https://example.invalid/source','locator':'own clause','context_requires_review':True,'proof_scope':'concept_context'}],'boundary':{'related_ids':[]},'review_note':'root review'}
retired=copy.deepcopy(canonical);retired.update(id='RETIRED',input_ids=['old']);retired['refs'][0]['context_requires_review']=False
closure={'additions':[],'edits':[{'id':'CANONICAL','fields':{'refs':copy.deepcopy(canonical['refs'])},'reason':'explicit source quarantine','reference_override_is_authoritative':True}],'merges':[{'from':'RETIRED','into':'CANONICAL','reason':'same financial result'}],'rejected_merge_proposals':[]}
rows,mapping,aliases,decisions=apply_closure(copy.deepcopy([canonical,retired]),{'old-input':['RETIRED']},copy.deepcopy(closure))
assert len(rows)==1 and rows[0]['refs'][0]['context_requires_review'], 'retired source restored an unproved operative claim'
assert mapping['old-input']==['CANONICAL'] and set(rows[0]['input_ids'])=={'old','current'}, 'source quarantine cannot remove the merged financial input'
closure['edits'][0].pop('reference_override_is_authoritative')
legacy,_,_,_=apply_closure(copy.deepcopy([canonical,retired]),{'old-input':['RETIRED']},closure)
assert not legacy[0]['refs'][0]['context_requires_review'], 'new authoritative semantics must not silently rewrite old unadjudicated reference histories'
print(json.dumps({'reference_override_checks':'passed','checks':3}))
