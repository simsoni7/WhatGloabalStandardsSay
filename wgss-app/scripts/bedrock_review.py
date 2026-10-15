"""Optional, bounded WGSS review through the Frontier Chat Completions API.

The gateway uses the existing BEDROCK_API_KEY as an HTTP bearer credential. It
sends public source summaries and WGSS data, not workspace files or secrets.
Responses are saved for review and are never applied automatically.
"""
import os,json,urllib.request,urllib.error,sys,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]
key=os.environ.get('BEDROCK_API_KEY','')
if not key:
 print('Gateway unavailable: BEDROCK_API_KEY is empty. No request sent.');sys.exit(2)
endpoint=os.environ.get('WGSS_LLM_CHAT_COMPLETIONS_URL','https://frontier-llmgw.aipocnhbank.com/v1/chat/completions')
fast_model=os.environ.get('WGSS_LLM_FAST_MODEL','claude-sonnet-5')
review_model=os.environ.get('WGSS_LLM_REVIEW_MODEL','claude-opus-5')
mode=sys.argv[1] if len(sys.argv)>1 else 'boundary-review'
if mode not in ['smoke','blind-classification','boundary-review']:raise SystemExit('Use smoke, blind-classification or boundary-review')
model=os.environ.get('WGSS_LLM_MODEL_OVERRIDE') or (review_model if mode=='boundary-review' else fast_model)
load=lambda n:json.loads((R/'dist/data'/n).read_text())
cases=load('cases.json');obs=load('observations.json')
if mode=='smoke':
 material=None
 instruction='Reply with exactly WGSS_OK and nothing else.'
elif mode=='blind-classification':
 # Exclude previous case IDs, synthetic selector facts and claim labels from the independent call.
 material=[{k:r[k] for k in ['id','expression','expression_role','meaning_ko','product_scope','source_id','source_locator']} for r in obs]
 instruction='Classify the supplied observations against definitions, or return needs_context/out_of_scope. Do not infer bank-account credit from Complete or direct app observation from help text. This is an AI second pass, not independent human validation. Return JSON with id, case_id or null, status, reason. No extra prose.'
else:
 material={'review_scope':'Definition boundaries only. Provider evidence is reviewed by the Sonnet classification pass.'}
 instruction='Review these financial UI situation definitions critically. Identify overlapping selectors, mixed business stages, missing exclusions, ambiguous disambiguation questions, and misleading definitions. Do not assess provider evidence in this pass. Return compact JSON with only the 5 highest-priority findings [{severity,record_or_case_id,problem,proposed_fix}] and no more than 3 brief limitations. Keep each string under 240 characters. Do not declare human approval or measured accuracy.'
compact_cases=[{k:c[k] for k in ['id','name','domain','definition','selector','includes','excludes','critical_fields','disambiguation_question']} for c in cases]
definitions=compact_cases if mode=='boundary-review' else cases
prompt=instruction if mode=='smoke' else instruction+'\nDEFINITIONS\n'+json.dumps(definitions,ensure_ascii=False,separators=(',',':'))+'\nMATERIAL\n'+json.dumps(material,ensure_ascii=False,separators=(',',':'))
# Frontier routes these Claude 5 models through LiteLLM. Both currently accept
# temperature=1 only; deterministic behavior is requested in the prompt and
# validated structurally after the call instead of relying on temperature=0.
body={'model':model,'messages':[{'role':'user','content':prompt}],
 'max_tokens':64 if mode=='smoke' else 3200 if mode=='boundary-review' else 8000,'temperature':1,
 'reasoning_effort':'low'}
req=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'application/json'},method='POST')
try:
 with urllib.request.urlopen(req,timeout=180) as resp:result=json.load(resp)
except urllib.error.HTTPError as e:
 print('Gateway request failed. HTTP',e.code,'No credentials logged.');sys.exit(3)
except (urllib.error.URLError,TimeoutError) as e:
 print('Gateway request failed.',type(e).__name__,'No credentials logged.');sys.exit(4)
choice=(result.get('choices') or [{}])[0]
content=(choice.get('message') or {}).get('content','')
if isinstance(content,list):content='\n'.join(x.get('text','') for x in content if isinstance(x,dict))
if key in content:raise SystemExit('Response blocked: secret echo')
if mode=='smoke' and content.strip()!='WGSS_OK':raise SystemExit('Smoke test failed: unexpected model response')
output={'mode':mode,'provider':'Frontier LLM Gateway','api_format':'OpenAI Chat Completions','model':result.get('model') or model,'run_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'usage':result.get('usage'),'finish_reason':choice.get('finish_reason'),'response':content,'independent_human_review':False,'applied_automatically':False}
(R/'research'/f'bedrock-{mode}.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
if mode!='smoke':
 candidate=content.strip()
 if candidate.startswith('```'):
  candidate=candidate.split('\n',1)[1] if '\n' in candidate else ''
  if candidate.endswith('```'):candidate=candidate[:-3].rstrip()
 try: parsed=json.loads(candidate)
 except json.JSONDecodeError:raise SystemExit('Model response saved but rejected: expected complete JSON')
 output['parsed_response']=parsed;output['output_json_valid']=True
 (R/'research'/f'bedrock-{mode}.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
status_path=R/'research/bedrock-status.json'
try: previous=json.loads(status_path.read_text())
except (FileNotFoundError,json.JSONDecodeError): previous={}
tested_models=list(dict.fromkeys([*previous.get('tested_models',[]),output['model']]))
status={'status':'connected','successful_calls':previous.get('successful_calls',0)+1,'last_mode':mode,'last_run_at':output['run_at'],'http_status':200,'api_format':output['api_format'],'endpoint_origin':'https://frontier-llmgw.aipocnhbank.com','model':output['model'],'tested_models':tested_models,'credential_logged':False}
status_path.write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'mode':mode,'status':'ok','usage':result.get('usage'),'saved':f'research/bedrock-{mode}.json'}))
