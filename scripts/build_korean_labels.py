"""Consolidate authored Korean English-label translations and original CFPD reading aids."""
import pathlib,json,hashlib,collections,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from glossary_app.korean_labels import english_key

def build():
 work=ROOT/'datasets/enrichment/korean_labels_work';entries={};inputs={}
 rows=[json.loads(l) for l in (ROOT/'dist/data/glossary_entries.jsonl').read_text().splitlines()]
 for file in (ROOT/'dist/community').glob('*.json'):rows+=json.loads(file.read_text()).get('rows',[])
 english={english_key(r['source_english']):r['source_english'] for r in rows}
 for r in rows:
  if r['dataset_id']=='cfpd' and r['target_language']=='ko':
   key=english_key(r['source_english']);entries[key]={'key':key,'english':r['source_english'],'korean':r['source_target'],'status':'source_korean_reused','origin':'cfpd_v1_original_korean_source','source_evidence_id':r['evidence_id'],'note':'같은 영어 표기의 CFPD 한국어 원문을 검색 보조로 재사용했습니다. 출처 간 개념 통합이나 다른 외국어 번역의 승인이 아닙니다.'}
 for part in ['1','2','3','extra']:
  source=work/(f'chunk_{part}.json' if part!='extra' else 'extra.json');raw=json.loads(source.read_text());expected={r['key']:r['english'] for r in raw} if isinstance(raw,list) else raw
  file=work/f'translated_{part}.jsonl';actual=[json.loads(l) for l in file.read_text().splitlines()];ids=[r['key'] for r in actual]
  if len(ids)!=len(set(ids)) or set(ids)!=set(expected):raise ValueError(f'Korean authored translation coverage mismatch for {part}: {len(ids)}/{len(expected)}')
  for r in actual:
   if r['key'] in entries or r['key']!=english_key(r['english']) or r['english']!=expected[r['key']] or r.get('status')!='ai_translated_unreviewed' or not re.search('[가-힣]',r.get('korean','')):raise ValueError('Invalid Korean translation: '+repr(r))
   entries[r['key']]={**r,'origin':'ai_authored_korean_translation'}
  inputs[file.name]={'rows':len(actual),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
 if set(english)!=set(entries):raise ValueError('Uncovered or extra English keys: '+repr(set(english)^set(entries)))
 out=ROOT/'datasets/enrichment/korean_english_labels.jsonl';out.write_text(''.join(json.dumps(entries[k],ensure_ascii=False)+'\n' for k in sorted(entries)))
 report={'field':'source_english_korean','scope':'Korean reading/search aid for English source label, independent of target translation approval','unique_english_labels':len(entries),'covered_observations':len(rows),'counts_by_origin':dict(collections.Counter(v['status'] for v in entries.values())),'human_translation_approvals_added':0,'missing_labels':0,'inputs':inputs,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()};(out.parent/'korean_label_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':build()
