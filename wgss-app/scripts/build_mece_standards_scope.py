"""Describe exact imported standard universes without calling them work counts."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
iso_path=R/'dist/data/iso-concept-index.json';iso=read(iso_path)
fibo_path=R/'research/source-store/standards/fibo-catalogue.json';fibo=read(fibo_path)
nist_path=R/'research/source-store/standards/nist-catalogue.json';nist=read(nist_path)
bian_path=R/'research/source-store/mece-closure-20261006/source-input.json';bian=read(bian_path)
scope=[
 dict(id='ISO20022',version=iso['version'],role='직접 대상·속성·관계의 의미 기준',unit='BusinessComponent',units=[n['id'] for n in iso['concepts']],
      source_count=len(iso['concepts']),related_count=len(iso['relations']),scope='20260904 e-Repository의 BusinessComponent 791개와 직접 속성·컴포넌트 간 관계',
      limitation='메시지 구성요소·코드셋은 업무 분모에 넣지 않음. 전체 Business Process Catalogue 수록·업무 변환 검토 완료가 아님.',
      work_mapping_review_complete=False,scope_input=str(iso_path.relative_to(R))),
 dict(id='BIAN',version='14.0.0 public portal snapshot 2026-10-02',role='업무 수행 책임·명시된 기능의 대조 기준',unit='ServiceDomain / BusinessCapability',
      units=[n['reference_key'] for n in bian],source_count=len(bian),related_count=None,
      scope='ServiceDomain 341개 + BusinessCapability 586개. 각각 자체 기능 정의를 판정',
      limitation='노드와 원자 금융 결과는 다대다. 명세 공백·부분 결과·공식 릴리스 요약 수와의 충돌은 남아 있음.',
      work_mapping_review_complete=False,scope_input=str(bian_path.relative_to(R))),
 dict(id='FIBO',version=fibo['source_snapshots'][0]['version'],role='권리·의무·계약 구조와 개념 관계 보완',unit='named schema term',
      units=[n['id'] for n in fibo['nodes']],source_count=len(fibo['nodes']),related_count=len(fibo['relations']),
      scope=fibo['scope_note'],limitation='FND·FBC·LOAN·IND의 Release 성숙도 모듈만 수록. 다른 금융영역·외부 import·익명 관계를 수록 완료로 표시하지 않음. 비수록은 금융업무 범위 제외가 아님.',
      work_mapping_review_complete=False,scope_input=str(fibo_path.relative_to(R))),
 dict(id='NIST',version='SP800-63-4 / A-4 / B-4 / C-4 final',role='신원확인·인증·연합·자격증명 결과 구분',unit='informative term / selected section',
      units=[n['id'] for n in nist['nodes']],source_count=len(nist['nodes']),related_count=0,
      scope=f'정보성 용어 {nist["counts"]["glossary_terms"]}개 + 선택 원문 절 {nist["counts"]["selected_sections"]}개',
      limitation='정보성 용어와 규범 기능 절을 구분. 선택 절 외의 모든 필수 요건·생애주기 대조 완료가 아니며 금융 법적 의무 기준도 아님.',
      work_mapping_review_complete=False,scope_input=str(nist_path.relative_to(R)))
]
for row in scope:
    row['source_input_sha256']=hashlib.sha256((R/row['scope_input']).read_bytes()).hexdigest()
    assert len(row['units'])==len(set(row['units']))==row['source_count']
record=dict(version='WGSS-standard-scope-v19-20261011',scope_kind='exact_imported_concept_universes_not_financial_work_denominator',
    standards=scope,global_mece_approved=False,automatic_adoption=False,
    open_scope_tasks=[
      dict(id='ISO-PROCESS-SCOPE',next_action='Business Process Catalogue에서 현재 BusinessComponent만으로 드러나지 않는 직접 결과의 대조 범위를 고정합니다.'),
      dict(id='FIBO-NONIMPORTED-CONTEXT',next_action='비수록 금융 모듈·외부 관계의 금융 결과 영향과 현재 정의 연결을 확인합니다. 비수록을 업무 제외로 간주하지 않습니다.'),
      dict(id='NIST-NORMATIVE-RESULTS',next_action='선택 절 밖의 연합 assertion 검증·계정 연결·인증수단 복구 등 수행 결과가 현재 지원 업무에 포함되는지 규범 절로 대조합니다.')])
(R/'data/mece-standards-scope-v19.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'standard_scope_units':{s['id']:s['source_count'] for s in scope},'financial_work_total_claim':False}))
