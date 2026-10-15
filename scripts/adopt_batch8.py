"""Import independently accepted Malaysian financial metadata observations."""
import json,pathlib,sys,shutil,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from glossary_app.expansion_review import reviewed_inputs
from adopt_batch7 import sha,save

def adopt():
 dataset='malaysia_financial_metadata';items=[(i,rows) for i,rows in reviewed_inputs(ROOT) if i['dataset_id']==dataset];assert len(items)==1;item,rows=items[0]
 base=ROOT/'datasets/language_packs'/dataset;base.mkdir(exist_ok=True);source=ROOT/'datasets/source_collection/batch8_malaysia';shutil.copytree(source/'raw',base/'raw',dirs_exist_ok=True)
 terms={'license':'MIT','commercial_use':True,'attribution_required':True,'license_file':'raw/LICENSE'}
 for r in rows:r.update(availability='present',dataset_state='candidate',generation_eligible=False,approved_translation=None,human_review=False)
 (base/'evidence.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));save(base/'independent-review.json',item)
 (base/'MODIFICATIONS.md').write_text('Selected financial metadata labels; same upstream JSON field/key preserved. Original English/Malay source values and definitions retained; outer whitespace normalization documented. Exact prior pairs and selected repeated English variants excluded. No normative translation equivalence or expert approval. Korean English-label translations are a separate contextual enrichment, not upstream text.\n')
 manifest={'dataset_id':dataset,'dataset_version':rows[0]['dataset_version'],'entry_count':len(rows),'language_counts':dict(collections.Counter(r['target_language'] for r in rows)),'decision':'accepted_reference','usage_terms':terms,'adoption_review':{'human_review':False,'semantic_approval':False},'files_sha256':{str(p.relative_to(base)):sha(p) for p in base.rglob('*') if p.is_file() and p.name!='manifest.json'}};save(base/'manifest.json',manifest)
 path=base.parent/'registry.json';reg=json.loads(path.read_text())
 if not any(r['dataset_id']==dataset for r in reg['packs']):reg['packs'].append({'dataset_id':dataset,'path':str(base.relative_to(ROOT)),'state':'candidate','decision':'accepted_reference','commercial_use':True})
 save(path,reg);path=base.parent/'commercial_policy.json';policy=json.loads(path.read_text());licenseurl=rows[0]['source']['repository']+'/blob/'+rows[0]['dataset_version']+'/LICENSE'
 if dataset not in policy['approved_dataset_ids']:policy['approved_dataset_ids'].append(dataset);policy['evidence'].append({'dataset_id':dataset,'policy_url':licenseurl,'policy_snapshot':str((base/'raw/LICENSE').relative_to(ROOT)),'policy_sha256':sha(base/'raw/LICENSE'),'attribution_review':str((base/'independent-review.json').relative_to(ROOT))})
 save(path,policy)
 path=ROOT/'dictionary/sources.json';descs=json.loads(path.read_text());descs=[d for d in descs if d['dataset_id']!=dataset];descs.append({'dataset_id':dataset,'name':'말레이시아 정부 · 금융통계 항목·재정 용어','publisher':'Government of Malaysia / data-gov-my','authority':'정부 공식 datagovmy-meta 저장소의 고정 커밋과 MIT 라이선스를 확인했습니다.','collection':'금리·국채·재정·국제수지 등 통계 메타데이터 JSON에서 영어·말레이어의 같은 필드·사전 키를 대응하고 원문과 정의를 보존했습니다.','scope':'금융통계 지표·분류·자료 제목. 국제수지의 Current Account 등은 해당 통계 문맥으로 읽어야 합니다.','limitations':'범용 은행 용어집이 아닌 통계 메타데이터입니다. 원문 정합성은 번역 정확성이나 전문가 승인이 아니며 무조건적 자동 생성 참고에서는 제외합니다.','license':'MIT · 정부 원출처 저작권과 라이선스를 유지합니다.','commercial':True,'urls':[rows[0]['source']['repository'],licenseurl],'license_notice':(base/'raw/LICENSE').read_text(),'attribution':'Government of Malaysia / data-gov-my, MIT. Selected unchanged metadata labels; selection and normalization described in source pack.'});save(path,descs)
 print(json.dumps({'adopted':dataset,'pairs':len(rows)}))
if __name__=='__main__':adopt()
