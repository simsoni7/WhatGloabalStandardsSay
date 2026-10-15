"""Repeatable parallel expert reviews of public WGSS reference data only.

No model result is applied to definitions, source facts or the site. Reviewers
have no browser or authenticated-app access; primary-source verification is a
separate required task. Use --dry-run to inspect scope without an API call.
"""
import argparse,concurrent.futures,datetime,hashlib,json,os,urllib.request,urllib.error
from pathlib import Path
R=Path(__file__).resolve().parents[1]
ROLES={
 'evidence':('claude-sonnet-5','Audit claim strength and source traceability. Separate recommendation, obligation, conditional policy, current runtime fact, and unknown. Flag market/product scope and expression vs policy provenance. Supplied summaries are not fresh source verification.'),
 'ontology':('claude-opus-5','Critically audit financial object/action/stage boundaries, task selectors, unsupported screen roles, and definition gaps. Do not invent provider policy or merge dispatch, credit, request, result, and interest preview.'),
 'ux':('claude-sonnet-5','Audit the decision workflow contract: unknown conditions, real values and product references, context invalidation, screen roles, evidence gaps, readable handoff and success metrics. Suggest concrete user mistakes to test.')
}
def material(role):
 def read(n):return json.loads((R/'dist/data'/n).read_text())
 common={'cases':read('cases.json'),'design_tasks':read('design-tasks.json')}
 if role=='evidence':common.update(observations=read('observations.json'),sources=read('sources.json'))
 if role=='ux':common['workflow_contract']={'condition_states':['known','unknown','not_applicable','conflicting'],'known_requires':['value','product_reference','context_scope'],'context':['market','channel','screen_role','product'],'runtime_result_requires':'runtime signal and transaction reference','saving':'tab-local, explicit save only','export':'includes unresolved conditions; never approval','measurements':'human study not yet performed'}
 return common
def run(role,public_material,key,endpoint):
 model,instruction=ROLES[role]
 request_material=json.dumps(public_material,ensure_ascii=False,separators=(',',':'))
 snapshot=hashlib.sha256(request_material.encode()).hexdigest()
 prompt=instruction+' Return JSON {"findings":[{"priority":"P0|P1|P2","target":"record or field","problem":"brief","fix":"brief"}],"limitations":["brief"]}. Maximum 6 findings. No extra prose. Do not claim independent human review.\nPUBLIC_REFERENCE_DATA\n'+request_material
 body={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':2400,'temperature':1,'reasoning_effort':'low'}
 req=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','Accept':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=180) as resp:raw=json.load(resp)
 except urllib.error.HTTPError as e:raise RuntimeError(f'{role}: HTTP {e.code}; no credentials logged') from None
 except (urllib.error.URLError,TimeoutError):raise RuntimeError(f'{role}: gateway request failed; no credentials logged') from None
 choice=raw['choices'][0];content=choice['message']['content']
 if not isinstance(content,str):raise RuntimeError(f'{role}: non-text response')
 if key in content:raise RuntimeError(f'{role}: credential echo blocked')
 candidate=content.strip()
 if candidate.startswith('```'):candidate=candidate.split('\n',1)[1].rsplit('```',1)[0].strip()
 valid=False;parsed=None
 try:
  parsed=json.loads(candidate)
  valid=isinstance(parsed,dict) and isinstance(parsed.get('findings'),list) and isinstance(parsed.get('limitations'),list) and all(isinstance(x,dict) and x.get('priority') in ['P0','P1','P2'] and all(isinstance(x.get(k),str) for k in ['target','problem','fix']) for x in parsed['findings'])
 except json.JSONDecodeError:pass
 output={'role':role,'model':model,'run_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot_sha256':snapshot,'usage':raw.get('usage'),'finish_reason':choice.get('finish_reason'),'response':content,'parsed_response':parsed,'output_json_valid':valid,'applied_automatically':False,'independent_human_review':False}
 out_dir=R/'research/agent-runs';out_dir.mkdir(exist_ok=True)
 path=out_dir/(role+'-'+output['run_at'].replace(':','-')+'.json');path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
 return {'role':role,'model':model,'output_json_valid':valid,'saved':str(path.relative_to(R)),'usage':output['usage']}
def main():
 p=argparse.ArgumentParser();p.add_argument('--roles',nargs='+',choices=ROLES,default=list(ROLES));p.add_argument('--dry-run',action='store_true');a=p.parse_args()
 roles=list(dict.fromkeys(a.roles));public={role:material(role) for role in roles}
 if a.dry_run:
  print(json.dumps([{'role':r,'model':ROLES[r][0],'public_material_chars':len(json.dumps(public[r],ensure_ascii=False)),'applied_automatically':False} for r in roles]));return
 key=os.environ.get('BEDROCK_API_KEY');endpoint=os.environ.get('WGSS_LLM_CHAT_COMPLETIONS_URL','https://frontier-llmgw.aipocnhbank.com/v1/chat/completions')
 if not key:raise SystemExit('BEDROCK_API_KEY unavailable; no request sent')
 failed=False
 with concurrent.futures.ThreadPoolExecutor(max_workers=len(roles)) as pool:
  jobs={pool.submit(run,r,public[r],key,endpoint):r for r in roles}
  for job in concurrent.futures.as_completed(jobs):
   try:
    result=job.result();print(json.dumps(result));failed=failed or not result['output_json_valid']
   except RuntimeError as e:print(str(e));failed=True
 if failed:raise SystemExit(1)
if __name__=='__main__':main()
