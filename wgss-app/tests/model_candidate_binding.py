"""A correct row ID must not approve the wrong source/work/label."""
import importlib.util,json,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
spec=importlib.util.spec_from_file_location('binding_runner',R/'scripts/run_mece_closure.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
job={'id':'adversarial-bindings','model':'claude-sonnet-5','instructions':'test fixture only; no API','input':{},'expected_ids':['A','B'],'row_key':'id','work_ids':['WA','WB'],'candidate_bindings':{'A':{'source_id':'SA','work_id':'WA','native_expression':'LA'},'B':{'source_id':'SB','work_id':'WB','native_expression':'LB'}}}
calls=[]
def mock(model,prompt,max_tokens):
 calls.append(True);return {'model':model,'finish_reason':'stop','usage':{'fixture':True},'response':json.dumps({'rows':[{'id':'A','source_id':'SB','work_id':'WB','native_expression':'LB','status':'pass'},{'id':'B','source_id':'SA','work_id':'WA','native_expression':'LA','status':'pass'}]})}
m.call_stream=mock
with tempfile.TemporaryDirectory(prefix='wgss-binding-qa-') as temp:
 m.RUN=Path(temp)
 try:m.execute(job)
 except RuntimeError:pass
 else:raise AssertionError('swapped source bindings accepted')
 assert len(calls)==3 and len(list(m.RUN.rglob('raw-*.json')))==3 and not list(m.RUN.rglob('proposal.json'))
print(json.dumps({'model_candidate_binding':'passed','checks':1,'fixture_only':True,'api_called':False}))
