"""Small Sonnet review of public, visually checked screen labels and mappings.

No image bytes, example customer names, credentials or browser session state
are sent. This text-based AI check is not an independent visual/human review.
"""
import hashlib
import json
import os
import datetime
import urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1]
dataset=json.loads((root/'dist/data/screen-evidence.json').read_text())
public=[{k:r[k] for k in ['id','provider','evidence_kind','screen_role','case_mappings','expressions','ui_version','version_status','policy_match','usage_note']} for r in dataset['records']]
material=json.dumps(public,ensure_ascii=False)
prompt='''Audit these editor-inspected public financial UI references. Return compact JSON
{"findings":[{"id":"UI...","severity":"high|medium|low","problem":"...","fix":"..."}],"acceptable_boundaries":["..."]}.
Do not infer app versions, completed transactions, card restriction origin, or current policy from a guide or marketing illustration.
Check especially Defrost versus Freeze, request receipt versus completion, commercial versus retail card products,
Lost/Stolen branch versus Damaged, and FX quote versus execution. Max 5 findings, concise JSON only.
This is text-based supplementary AI review of already visually checked labels, not a fresh visual audit.
'''+material
key=os.environ.get('BEDROCK_API_KEY')
if not key:raise SystemExit('Gateway key unavailable; no request made')
body={'model':'claude-sonnet-5','messages':[{'role':'user','content':prompt}],'max_tokens':1600,'temperature':1,'reasoning_effort':'low'}
endpoint=os.environ.get('WGSS_LLM_CHAT_COMPLETIONS_URL','https://frontier-llmgw.aipocnhbank.com/v1/chat/completions')
req=urllib.request.Request(endpoint,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
with urllib.request.urlopen(req,timeout=180) as response:raw=json.load(response)
content=raw['choices'][0]['message']['content']
if key in content:raise SystemExit('Credential echo blocked')
candidate=content.strip()
if candidate.startswith('```'):candidate=candidate.split('\n',1)[1].rsplit('```',1)[0].strip()
parsed=json.loads(candidate)
assert isinstance(parsed.get('findings'),list) and isinstance(parsed.get('acceptable_boundaries'),list)
result={'model':'claude-sonnet-5','reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'input_sha256':hashlib.sha256(material.encode()).hexdigest(),'usage':raw.get('usage'),'review':parsed,
        'image_bytes_sent':False,'independent_human_review':False,'applied_automatically':False}
(root/'research/screen-sonnet-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'review_saved','findings':len(parsed['findings']),'usage':result['usage']}))
