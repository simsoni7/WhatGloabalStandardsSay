"""Adopt only independently accepted, commercially licensed batch7 source IDs."""
import json,pathlib,hashlib,shutil,collections,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from glossary_app.expansion_review import reviewed_inputs

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def adopt():
 registry=ROOT/'datasets/language_packs/registry.json';reg=json.loads(registry.read_text());policyfile=registry.parent/'commercial_policy.json';policy=json.loads(policyfile.read_text());descriptors=json.loads((ROOT/'dictionary/sources.json').read_text());counts={}
 for item,rows in reviewed_inputs(ROOT):
  dataset=item['dataset_id']
  if dataset not in ['apache_ofbiz_financial_entities','malaysia_financial_dashboard']:continue
  base=registry.parent/dataset;base.mkdir(exist_ok=True);src=ROOT/('datasets/source_collection/batch7_permissive' if dataset.startswith('apache') else 'datasets/source_collection/batch7_asia')
  raw=src/('raw' if dataset.startswith('apache') else 'adopted_material');shutil.copytree(raw,base/'raw',dirs_exist_ok=True)
  for r in rows:
   r['availability']='present';r['dataset_state']='candidate';r['approved_translation']=None;r['human_review']=False;r['generation_eligible']=False
  (base/'evidence.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));save(base/'independent-review.json',item)
  licensefile='raw/LICENSE';noticefile='raw/NOTICE' if dataset.startswith('apache') else 'raw/NOTICE.txt';terms={'commercial_use':True,'license':'Apache-2.0' if dataset.startswith('apache') else 'MIT','license_file':licensefile,'attribution_required':True,'notice_file':noticefile}
  (base/'MODIFICATIONS.md').write_text('Selected financial labels only; same upstream keys, original source values retained; outer whitespace normalized where documented. Independent AI source review excludes listed suspicious observations. No financial expert approval, endorsement, or blanket license for unrelated datasets. Korean English-label aids are a separate enrichment layer.\n')
  manifest={'dataset_id':dataset,'dataset_version':rows[0]['dataset_version'],'entry_count':len(rows),'language_counts':dict(collections.Counter(r['target_language'] for r in rows)),'usage_terms':terms,'decision':'accepted_reference','adoption_review':{'human_review':False,'semantic_approval':False},'files_sha256':{str(p.relative_to(base)):sha(p) for p in base.rglob('*') if p.is_file() and p.name!='manifest.json'}};save(base/'manifest.json',manifest)
  if not any(r['dataset_id']==dataset for r in reg['packs']):reg['packs'].append({'dataset_id':dataset,'path':str(base.relative_to(ROOT)),'state':'candidate','decision':'accepted_reference','commercial_use':True})
  url=rows[0]['source'].get('license_url') or 'https://github.com/data-gov-my/datagovmy-meta/blob/'+rows[0]['dataset_version']+'/LICENSE'
  if dataset not in policy['approved_dataset_ids']:
   policy['approved_dataset_ids'].append(dataset);policy['evidence'].append({'dataset_id':dataset,'policy_url':url,'policy_snapshot':str((base/licensefile).relative_to(ROOT)),'policy_sha256':sha(base/licensefile),'attribution_review':str((base/'independent-review.json').relative_to(ROOT))})
  desc={'dataset_id':dataset,'name':'Apache OFBiz · 금융 계정·결제 표현' if dataset.startswith('apache') else '말레이시아 정부 · 말레이어 금융통계 지표명','publisher':'Apache Software Foundation' if dataset.startswith('apache') else 'Government of Malaysia / data-gov-my','authority':'공식 프로젝트의 고정 커밋과 원문·라이선스를 확인했습니다.','collection':'영어와 대상 언어의 동일 XML 키를 대응하고 기존 자료 및 배치 내 중복·의미 의심 후보를 제외했습니다.' if dataset.startswith('apache') else '정부 공식 datagovmy-meta 저장소의 영어·말레이어 금융 대시보드 JSON에서 동일 키의 실제 원문을 대응했습니다.','scope':'ERP 금융 계정·지급수단·청구·결제 라벨.' if dataset.startswith('apache') else '금리·통화량·가계부채·전자결제·준비금·연금 등 금융통계 지표명. 범용 은행 용어집은 아닙니다.','limitations':'문맥이 있는 원문 라벨이며 전문가 승인 번역이 아닙니다. 무조건적 자동 생성 참고에서 제외합니다.','license':terms['license']+' · 원출처 저작권·라이선스·변경 고지를 유지합니다.','commercial':True,'urls':[rows[0]['source'].get('repository') or 'https://github.com/apache/ofbiz-framework',url],'license_notice':(base/licensefile).read_text(),'attribution':'Original upstream labels selected with source keys retained. '+terms['license']+'; copyright and notices supplied.'}
  descriptors=[d for d in descriptors if d['dataset_id']!=dataset]+[desc];counts[dataset]=len(rows)
 save(registry,reg);save(policyfile,policy);save(ROOT/'dictionary/sources.json',descriptors);print(json.dumps(counts))
if __name__=='__main__':adopt()
