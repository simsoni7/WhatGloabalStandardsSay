"""Compile only explicitly curated navigation; never infer proof or MECE status."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def build():
 source=R/'data/business-backbone-review.json';r=json.loads(source.read_text());d=json.loads((R/'dist/data/operations.json').read_text());by={w['id']:w for w in d['works']};ass={a['id']:a for a in r['assignments']};assert len(ass)==len(r['assignments']) and set(ass)==set(by);assert r['operation_version']==d['version'];families={f['id'] for f in r['families']};goals=r['goals'];assert len({g['id'] for g in goals})==len(goals)
 for g in goals:assert set(g['canonical_work_ids']+g['optional_work_ids'])<=by.keys() and g['family_id'] in families
 compact=[]
 for i,w in by.items():
  assert ass[i]['family_id'] in families
  aliases=list(dict.fromkeys(w.get('aliases',[])+[a for g in goals if i in g['canonical_work_ids'] for a in g['aliases']]))
  compact.append({**{k:w[k] for k in ['id','title','layer','status','actor_role','object_key','outcome_key']},'aliases':aliases,'family_id':ass[i]['family_id'],'navigation_ambiguous':ass[i]['ambiguous']})
 products=json.loads((R/'data/product-profiles-review.json').read_text());inventory=json.loads((R/'data/product-vocabulary-inventory.json').read_text());profiles=products['product_profiles'];sources=products['product_sources'];profile_ids={p['id'] for p in profiles};source_ids={s['id'] for s in sources};goal_ids={g['id'] for g in goals}
 assert products['root_adjudicated'] and not products['whole_mece_approved']
 assert len(profile_ids)==len(profiles) and len(source_ids)==len(sources)
 for p in profiles:
  assert p['family_id'] in families and set(p['source_ids'])<=source_ids
  assert len({s['id'] for s in p['steps']})==len(p['steps'])
  for s in p['steps']:
   assert set(s['work_ids'])<=by.keys()
   assert set(s.get('review_candidate_ids',[]))<=by.keys()
   assert not any(by[i]['status']=='unresolved' for i in s['work_ids']),('unresolved work presented as directly linked',p['id'],s['id'])
   if s.get('review_candidate_ids'):assert s['gap'] and all(by[i]['status']=='unresolved' for i in s['review_candidate_ids'])
   assert s['work_ids'] or s['gap'],('silent empty step',p['id'],s['id'])
   if any(by[i]['status']=='unresolved' for i in s['work_ids']):assert s['gap'],('unresolved work concealed',p['id'],s['id'])
 assert len({i['id'] for i in inventory['items']})==len(inventory['items'])
 for i in inventory['items']:
  assert i['source_id'] in source_ids and set(i['profile_ids'])<=profile_ids and set(i['goal_ids'])<=goal_ids
  assert (i['disposition']=='mapped' and (i['profile_ids'] or i['goal_ids']) and not i['gap_reason']) or (i['disposition']=='gap' and i['gap_reason'] and not i['profile_ids'] and not i['goal_ids']),('unreviewed inventory term',i['id'])
  for gid in i['goal_ids']:
   goal=next(g for g in goals if g['id']==gid)
   if i['term'] not in goal['aliases']:goal['aliases'].append(i['term'])
 steps=[s for p in profiles for s in p['steps']];gaps=sum(bool(s['gap']) or not s['work_ids'] for s in steps)
 quality={'inventory_version':inventory['version'],'scope':inventory['scope'],'inventory_count':len(inventory['items']),'profile_count':len(profiles),'source_count':len(sources),'inventory_mapped':sum(i['disposition']=='mapped' for i in inventory['items']),'inventory_gap':sum(i['disposition']=='gap' for i in inventory['items']),'step_count':len(steps),'gap_step_count':gaps,'mapped_step_count':sum(bool(s['work_ids']) for s in steps),'unresolved_work_count':sum(w['status']=='unresolved' for w in by.values()),'global_finance_ready':False,'query_count':0,'gates':[{'id':'inventory-disposition','label':'원문 발견 명칭 전수 판정','status':'passed','note':'연결 또는 미연결 사유를 빠짐없이 기록했습니다.'},{'id':'product-stage-results','label':'상품의 화면 단계·독립 결과 연결','status':'pending','note':str(gaps)+'개 단계에 연결·근거 보강이 남아 있습니다.'},{'id':'whole-finance-mece','label':'금융 전체의 의미 중복·누락 검증','status':'pending','note':'상품·명칭·탐색 단계의 수를 업무 총수로 승인하지 않습니다.'}]}
 report_path=R/'data/product-discoverability-report.json'
 fingerprint=hashlib.sha256(b'|'.join((R/name).read_bytes() for name in ['data/product-profiles-review.json','data/product-vocabulary-inventory.json','data/product-query-fixtures.json','dist/backbone-core.js','dist/data/operations.json','data/business-backbone-review.json'])).hexdigest()
 report=json.loads(report_path.read_text()) if report_path.exists() else {}
 current=report.get('source_fingerprint')==fingerprint and report.get('status')=='passed'
 quality['query_count']=report['query_count'] if current else 0
 quality['gates'].insert(1,{'id':'practitioner-search','label':'대표 어휘·조건 검색 회귀','status':'passed' if current else 'pending','note':str(report['checks'])+'개 검사 통과 · 금융 전체 정의 완료의 판정 아님' if current else '입력·검색 코드가 변경되어 회귀 검사를 다시 실행해야 합니다.'})
 b={'version':r['version'],'operation_version':d['version'],'families':r['families'],'goals':goals,'works':compact,'counting_contract':r['counting_contract'],'canonical_count':len(by),'path_count':len(goals),'counts_by_family':dict(collections.Counter(a['family_id'] for a in ass.values())),'whole_mece_approved':False,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'product_profiles':profiles,'product_sources':sources,'product_inventory':inventory['items'],'product_quality':quality}
 (R/'dist/data/business-backbone.json').write_text(json.dumps(b,ensure_ascii=False,separators=(',',':'))+'\n');print(json.dumps({'canonical_work_count':len(by),'navigation_family_count':len(families),'navigation_path_count':len(goals),'whole_mece_approved':False}))
if __name__=='__main__':build()
