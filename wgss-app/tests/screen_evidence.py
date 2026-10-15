"""Source provenance, image integrity and financial boundary checks."""
import json
import hashlib
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'dist/data/screen-evidence.json').read_text())
schema=json.loads((ROOT/'dist/data/screen-evidence.schema.json').read_text())
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
Draft202012Validator(schema).validate(data)
check('screen evidence schema',True)
records=data['records'];cases={c['id'] for c in json.loads((ROOT/'dist/data/cases.json').read_text())}
check('unique targets and IDs',len({r['id'] for r in records})==len(records)==len({r['target_id'] for r in records}))
check('case mappings resolve',all(m['case_id'] in cases for r in records for m in r['case_mappings']))
check('published images match visually reviewed immutable hashes',all(hashlib.sha256((ROOT/'dist'/r['image_path']).read_bytes()).hexdigest()==r['image_sha256']==r['reviewed_image_sha256'] for r in records))
check('no local source or OCR dump published',all('image_local_path' not in r and 'source_original_path' not in r and 'ocr_text' not in r for r in records))
check('native app capture and independent human review not fabricated',data['authenticated_app_captures']==0 and not data['independent_human_review'])
check('app version not inferred from document date',all(r['ui_version'] is None and r['version_status']!='verified' for r in records))
monzo=next(r for r in records if r['target_id']=='monzo-defrost')
check('Defrost image maps to unlock, not freeze',monzo['case_mappings'][0]['case_id']=='C02' and any(x['text']=='Defrost card' for x in monzo['expressions']))
receipt=next(r for r in records if r['target_id']=='payinfo-receipt')
check('application receipt is not revocation completion',receipt['screen_role']=='request_receipt' and receipt['expressions'][1]['text']=='신청접수')
check('Payinfo debit screenshots not applied to standing orders',all([m['case_id'] for m in r['case_mappings']]==['D03'] for r in records if r['provider']=='금융결제원 Payinfo'))
check('outdated policy text is marked on both affected screens',all(r['policy_match']=='conflicts_current_help' for r in records if r['target_id'] in ['payinfo-request','payinfo-receipt']))
citi=next(r for r in records if r['target_id']=='citimanager-replace')
check('commercial card branch and retail card scope are separated',citi['case_mappings'][0]['relation']=='conditional_branch' and '법인' in citi['product_scope'] and citi['source_published_at']=='2025-08')
wise=[r for r in records if r['provider']=='Wise']
check('FX quote is not execution and mobile web is not native app',len(wise)==2 and all(r['evidence_kind']=='live_public_web' and r['channel']=='web' and r['screen_role']=='quote_preview' and r['case_mappings'][0]['case_id']=='F01' for r in wise))
report={'status':'passed','checks':len(checks),'items':checks,'records':len(records),'case_count':len({m['case_id'] for r in records for m in r['case_mappings']})}
(ROOT/'research/screen-validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
