"""Explicit root proof corrections after the current-catalogue audit."""
import copy,hashlib,json
from pathlib import Path
from prepare_mece_v18 import plain
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/mece-closure-20261011'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
ledger=read(R/'data/operation-backbone-dispositions.json');assert not ledger.get('v19_source_fixes_applied')
by={w['id']:w for w in read(R/'dist/data/operations.json')['works']}
sections={s['section_id']:s for r in read(RUN/'source-input.json') for s in r['own_sections']}
def anchored(sid,quote):
 s=sections[sid];n=s['native_id'];p=Path(s['source_file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==s['source_file_sha256']
 raw=json.JSONDecoder().raw_decode(p.read_text().split('var objectData =',1)[1].strip())[0]
 docs=[(i,c) for i,c in enumerate(raw[n]['data'][0]['categories']) if c['type']=='documentation'];i,c=docs[int(sid.rsplit(':',1)[1])]
 assert quote in plain(c['content']['value'])
 return dict(id='BIAN:14.0.0:portal:'+n,name=s['name'],url=s['source_url'],locator=f'objectData["{n}"].data[0].categories[{i}].content.value',
   source_sha256=s['source_file_sha256'],source_snapshot_id='BIAN-14-public-portal-2026-10-02',exact_quote=quote,
   quote_normalisation='HTML text extraction using prepare_mece_v18.plain',context_requires_review=False,
   proof_scope='own_functional_clause_not_global_law_or_provider_ui',rationale='직접 기능·책임 원문 인용을 보완했습니다.')
config={
 'WGSS-5F8FC967D676':[('BIAN:43057:doc:3',"Maintain customers' channel/device access profiles (allowed uses and limits)")],
 'WGSS-DF3339F2234C':[('BIAN:36225:doc:0','This Service Domain implements a process by which the most appropriate valuation method is selected and applied in the context of the valuation request and the purpose of the valuation.')],
 'WGSS-D490EDEAC5CD':[('BIAN:43878:doc:3','Process securities deposits and withdrawals'),('BIAN:31179:doc:0','This includes administering the physical movements of securities, safe storage, the processing of associated dividends and interest and securities reporting')],
 'WGSS-779616C3F2C3':[('BIAN:29628:doc:0','the overall Credit Limit for the customer, which is the bank-internal maximum credit exposure that the bank is willing to have with the customer.')]
}
records=[]
for i,evidence in config.items():
 refs=copy.deepcopy(by[i]['refs']);new=[anchored(*q) for q in evidence];replace={r['id'] for r in new}
 refs=[r for r in refs if r['id'] not in replace]+new
 if i=='WGSS-DF3339F2234C':
  for ref in refs:
   if ref['id']!='BIAN:14.0.0:portal:36225':
    ref.update(context_requires_review=True,proof_scope='model_product_or_asset_concept_context_not_valuation_process')
 fields=dict(refs=refs)
 reason='검토 입력에 빠진 직접 BIAN 기능 원문을 실제 shard·인용·해시로 고정했습니다.'
 if i=='WGSS-779616C3F2C3':
  for existing in refs:
   if existing['id']=='BIAN:14.0.0:portal:33185':
    existing.update(context_requires_review=True,proof_scope='limit_oversight_context_not_limit_establishment',rationale='원문은 한도·익스포저 감독을 설명하며 설정 결과의 직접 근거로 사용하지 않습니다.')
  store=RUN/'sources';meta=read(store/'BCBS_CREDIT_RISK_2025.json');text=(store/meta['text_path']).read_text()
  quote='Banks should establish overall credit limits at the level of individual borrowers and counterparties, and groups of connected counterparties'
  assert quote in text
  refs.append(dict(id='WGSS-PROCESS-BCBS_CREDIT_RISK_2025',name='BCBS credit risk guidance · Principle 5',url=meta['url'],
    locator='CRI10 Principle 5 / paragraphs 10.34–10.35',source_snapshot_id='WGSS-primary-process-20261011',source_sha256=meta['sha256'],
    exact_quote=quote,source_store_relative=str(store.relative_to(R)),context_requires_review=False,
    proof_scope='supervisory_guidance_function_not_universal_law_or_provider_ui',rationale='차주·거래상대방별 전체 익스포저 한도 설정 책임의 공식 감독 지침 근거입니다.'))
  fields.update(title='기관 여신 익스포저 한도 설정',object_key='counterparty_credit_exposure_limit',outcome_key='establish_counterparty_credit_exposure_limit',
    definition='여신 책임자가 차주·거래상대방 또는 연결된 거래상대방 집단에 대해 은행이 부담할 전체 신용 익스포저 한도를 설정하는 결과. 은행 내부 위험 부담 한도이며 고객에게 자금 이용권을 약정하는 신용한도 계약과 구분합니다.',
    includes=['차주·거래상대방별 전체 신용 익스포저 한도 설정','연결된 거래상대방 집단의 통합 한도 설정'],
    excludes=['고객과의 약정형 신용한도 계약 성립','개별 대출 인수심사 결정','설정된 한도의 초과 여부 감시','기관 신용·마진 의사결정 정책 지침 확정','일반 업종·지역 전략 수립'],
    discriminator='internal_counterparty_exposure_limit_not_contractual_credit_facility_or_policy',
    applicability_conditions=['BCBS 2025 신용위험관리 원칙 5와 현재 CRI10 통합 지침의 기능 근거입니다. 모든 관할에서 직접 법적 의무라는 주장이 아닙니다.','BIAN Credit Facility 원문의 bank-internal maximum credit exposure를 내부 한도의 의미 근거로 사용합니다. 상품별 심사 면제는 약정 구조의 설명이며 본 한도 설정 결과에 포함하지 않습니다.'],
    boundary=dict(related_ids=['WGSS-CB2F5FE40642','WGSS-1740AFFB2840','WGSS-5001E20F90A5','WGSS-MECE-CREDIT-MARGIN-POLICY'],
      distinction='내부 최대 위험 부담 한도, 고객과의 자금 이용권 약정, 개별 신용 심사, 기존 한도 감시는 직접 대상·결과가 다릅니다.'),
    review_note='신용시설 약정의 상품별 심사 면제 설명을 내부 한도 정의에서 제거하고, BCBS 한도 설정 기능과 BIAN 내부 익스포저 의미로 교정했습니다. 전체 MECE 승인은 아닙니다.')
  reason=fields['review_note']
 ledger['edits'].append(dict(id=i,fields=fields,reason=reason,phase='v19-current-source-correction',automatic_adoption=False))
 records.append(dict(id=i,decision='root_source_and_boundary_corrected',reason=reason,automatic_adoption=False))
ledger['v19_source_fixes_applied']=True;write(R/'data/operation-backbone-dispositions.json',ledger)
write(R/'data/mece-v19-source-fixes.json',dict(version='WGSS-v19-source-fixes-20261011',rows=records,automatic_adoption=False,global_mece_approved=False))
print(json.dumps({'current_definition_source_fixes':len(records),'count_changed':False}))
