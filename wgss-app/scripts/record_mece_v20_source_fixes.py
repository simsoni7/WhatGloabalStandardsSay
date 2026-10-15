"""Root source corrections after current-delta and Sonnet counterexamples."""
import json,copy,hashlib
from pathlib import Path
from prepare_mece_v18 import plain
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/mece-closure-v20-20261011';S=RUN/'sources'
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
l=read(R/'data/operation-backbone-dispositions.json');assert not l.get('v20_source_fixes_applied'),'Already applied; do not rerun'
by={w['id']:w for w in read(R/'dist/data/operations.json')['works']};edits={r['id']:r for r in l['edits']}
def q(sid,needle,n):
 t=(S/(sid+'.txt')).read_text();at=t.find(needle);assert at>=0,(sid,needle);return t[at:at+n]
def primary(sid,quote):
 m=read(S/(sid+'.json'));assert quote in (S/m['text_path']).read_text();return dict(id='WGSS-PROCESS-'+sid,name=sid,url=m['url'],locator='operative clause: '+quote[:65],source_sha256=m['sha256'],source_snapshot_id='WGSS-functional-source-fix-v20-20261011',source_store_relative=str(S.relative_to(R)),exact_quote=quote,context_requires_review=False,proof_scope=m['source_kind']+'_function_only_not_global_law_or_ui',rationale='변경 정의의 직접 기능을 확인한 원문이며 현재 보편적 정책·서비스·화면 근거로 승격하지 않습니다.')
def setfields(i,fields):
 if i in edits:edits[i]['fields'].update(fields)
 else:
  e=dict(id=i,fields=fields,reason='v20 현재 변경 정의의 기능 근거와 경계 보완');l['edits'].append(e);edits[i]=e
def addrefs(i,refs):
 old=copy.deepcopy(by[i]['refs'])
 for r in old:
  if r['id'].startswith('BIAN:') and not r.get('exact_quote'):r.update(context_requires_review=True,proof_scope='legacy_function_context_not_anchored_clause')
 setfields(i,{'refs':old+refs})
scheme='WGSS-MECE-CARD-NETWORK-PARTICIPATION-END'
addrefs(scheme,[primary('VISA_CORE_RULES',q('VISA_CORE_RULES','Voluntary termination of membership will not be effective',225))])
addrefs('WGSS-8080B7031AAB',[primary('BOA_DEPOSIT_RATE_APPLICATION',q('BOA_DEPOSIT_RATE_APPLICATION','Fixed rate means',176)),primary('BOA_DEPOSIT_RATE_APPLICATION',q('BOA_DEPOSIT_RATE_APPLICATION','At our discretion',99))])
setfields('WGSS-8080B7031AAB',{'applicability_conditions':by['WGSS-8080B7031AAB'].get('applicability_conditions',[])+['제공자 예금약정의 고정·변동 금리 적용·변경 기능과 FIBO 금리·재설정 개념을 대조한 편집 정의입니다. 해당 약정의 무통지 변경권을 다른 은행·관할·상품의 권리로 일반화하지 않습니다.']})
addrefs('WGSS-BACKBONE-FX-QUOTE',[primary('WISE_QUOTE_INFORMATION',q('WISE_QUOTE_INFORMATION','Unauthenticated quotes let you fetch',438))])
setfields('WGSS-BACKBONE-FX-QUOTE',{'applicability_conditions':by['WGSS-BACKBONE-FX-QUOTE'].get('applicability_conditions',[])+['Wise의 비인증 견적은 예시 환율·비용을 미리 제공하는 기능이며, 실제 송금 요청에는 별도 인증 견적이 필요합니다. 문서 조회는 실제 최신 화면 관측이나 다른 제공자의 가용성 증거가 아닙니다.']})
n=next(r for r in read(R/'research/source-store/mece-closure-20261006/source-input.json') if r['reference_key']=='ServiceDomain:32699');s=next(s for s in n['own_sections'] if s['section_id']=='BIAN:32699:doc:0');p=Path(s['source_file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==s['source_file_sha256'];raw=json.JSONDecoder().raw_decode(p.read_text().split('var objectData =',1)[1].strip())[0];docs=[(k,c) for k,c in enumerate(raw['32699']['data'][0]['categories']) if c['type']=='documentation'];k,c=docs[0];quote="A bank offers factoring services to buy a customers' accounts receivable at a discount to provide short term liquidity.";assert quote in plain(c['content']['value'])
ref=dict(id='BIAN:14.0.0:portal:32699',name=n['name'],url=s['source_url'],locator=f'objectData["32699"].data[0].categories[{k}].content.value',exact_quote=quote,source_sha256=s['source_file_sha256'],context_requires_review=False,source_snapshot_id='BIAN-14-public-portal-2026-10-02',proof_scope='own_factoring_purchase_function_not_advance_execution_or_provider_ui',rationale='원문이 직접 기술한 할인매입 기능입니다. 매입채권 선지급 의무의 실제 지급과 구분합니다.')
addrefs('WGSS-610BF7A63589',[ref])
nav='WGSS-MECE-FUND-NAV';setfields(nav,{'excludes':by[nav]['excludes']+['판매수수료·환매비용 적용 후 최종 거래가격 확정']})
l['v20_source_fixes_applied']=True;write(R/'data/operation-backbone-dispositions.json',l)
ids=[scheme,'WGSS-8080B7031AAB','WGSS-BACKBONE-FX-QUOTE','WGSS-610BF7A63589',nav]
write(R/'data/mece-v20-source-fixes.json',dict(version='WGSS-source-fixes-v20-20261011',work_ids=ids,automatic_adoption=False,independent_human_review=False,global_mece_approved=False))
print(json.dumps({'source_fixes':4,'boundary_fix':1}))
