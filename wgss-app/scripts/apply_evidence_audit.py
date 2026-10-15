"""Explicit, author-reviewed corrections from the v0.4 primary-source audit."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist/data'
read=lambda n:json.loads((D/n).read_text())
def write(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
obs=read('observations.json');sources=read('sources.json')
for o in obs:
 if o['id'] in ('O39','O40'):
  next(c for c in o['claims'] if c['field']=='creditor_notification')['value']='recommended'
 if o['id'] in ('O37','O38'):
  o['source_id']='S17';o['source_locator']='자동이체 FAQ / 자동이체(납부)·자동이체(송금) 구분'
 if o['id']=='O41':
  p=next(c for c in o['claims'] if c['field']=='pending_execution')
  p.update(value=None,state='unknown',source_id=None,locator=None,basis=None)
  note='공통 취소 권고 문단만으로 정기 송금의 처리중 예외를 별도 확인하지 못했다.'
  if note not in o['notes']:o['notes'].append(note)
write('observations.json',obs)
for s in sources:
 if s['id'] in ('S16','S17','S18','S19'):s['last_checked_at']='2026-09-30T23:31:27Z'
write('sources.json',sources)
m=read('manifest.json');m.update(version='0.4.0',retrieved_at=max(s['retrieved_at'] for s in sources),design_task_count=4)
m['known_gaps']=['공식 한국어·영어 문서 기반; 실앱 화면은 미관찰','WGSS가 작성한 한국어 설명·초안은 원문 표기와 구분','독립 검토자 합의도와 실제 업무 시간 절감은 미측정','법규 준수나 국제 표준 인증을 의미하지 않음','26개 정의는 업체 사례가 없으며 구조·확인 조건만 제공']
write('manifest.json',m)
fields=read('field-labels.json');fields.update(status_signal='실제 처리 신호·거래 식별자',rate_basis='이율 기준');write('field-labels.json',fields)
definition_doc=R/'docs/case-definitions.md'
if definition_doc.exists():definition_doc.write_text(definition_doc.read_text().replace('# WGSS 금융상황 정의 v0.3','# WGSS 금융상황 정의 · 릴리스 v0.4'))
print('Evidence audit applied; source retrieval dates retained')
