"""Materialize explicitly root-selected/corrected decisions; not model adoption."""
import copy,hashlib
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
STORE=ROOT/'research/source-store/mece-closure-20261005/sources'
by={w['id']:w for w in read(RUN/'catalogue-input.json')['works']}
sections=read(RUN/'targeted-sections.json')
def proposal(job):
 paths=list((RUN/'reviews'/job).glob('*/proposal.json'));assert len(paths)==1
 return {r['id']:r for r in read(paths[0])['result']['rows']}
first=proposal('boundary-v18-01');second=proposal('boundary-v18-02')
amend=proposal('targeted-v18-undertaking-amendment-bounded')
process=proposal('targeted-v18-process-proof-bounded')
actions=[]
def selected(i,row,job,reason):
 fields=copy.deepcopy(row['fields']);assert fields
 if isinstance(fields.get('applicability_conditions'),str):fields['applicability_conditions']=[fields['applicability_conditions']]
 actions.append(dict(work_id=i,decision='corrected_edit',fields=fields,job_id=job,
  evidence_section_ids=row['evidence_section_ids'],reason=reason,automatic_adoption=False))

# These rows have been compared to the full clauses. Correct proposal errors
# rather than marking every arrived row accepted.
i='WGSS-ADD-5CDA21892432';r=copy.deepcopy(first['SEMANTIC-'+i])
r['fields']['title']='법적 차단 계좌의 거래제한 해제'
r['fields']['applicability_conditions']=['보존된 미국 OFAC 2024 규정의 유효한 명령·허가·제재목록 해제 절차를 직접 근거로 합니다. 현재 적용 법령과 다른 관할의 해제 조건은 별도 확인합니다.',
 '기관 내부정책에 따른 일반 제한 해제는 이 근거만으로 입증되지 않으며 신규 독립 업무로 추정하지 않습니다.']
# Fix the old misleading section anchor: use the actual operative paragraph.
path=ROOT/'research/source-store/operation-v12/closure-20261004/definitions/sources/OFAC_UNBLOCKING_RULE.txt'
t=path.read_text();at=t.rfind('§ 501.603');sid='OFAC_UNBLOCKING_RULE:operative:'+str(at)
sections[sid]=dict(section_id=sid,text=t[at:at+1900],name='OFAC 2024 operative unblocking paragraph',
 source_url='https://ofac.treasury.gov/media/933481/download?inline=',source_locator='31 CFR 501.603(b)(3)(i)(A)-(D), PDF page 4',
 source_file=str(path),source_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
r['evidence_section_ids']=[sid]
selected(i,r,'boundary-v18-01','집행 조문을 직접 고정하고 법적 차단 해제 결과로 한정합니다. AccountContract 명사에서 내부정책상 해제 권한을 추정한 부분은 반려합니다.')

for i in ['WGSS-EAB16CB1D4C4','WGSS-AF6645904647','WGSS-F4E90272B38B']:
 r=copy.deepcopy(first['SEMANTIC-'+i])
 if i=='WGSS-F4E90272B38B':
  r['fields'].update(definition='증권 차입자와 대여자가 증권의 대차계약을 성립시키는 결과. 하나의 공유 계약 결과를 관점별로 복제하지 않으며 실제 인도·반환과는 구별합니다.',
   discriminator='securities_loan_contract_formation_not_repo_sale_and_repurchase_or_delivery',includes=['증권 대차계약의 성립'])
  r['fields']['excludes']+=['일반 금전소비대차 계약 성립', '차입자·대여자 관점만 바꾼 동일 계약 성립', '증권의 실제 인도·반환 실행']
 if i=='WGSS-AF6645904647':r['fields']['layer']=by[i]['layer']
 selected(i,r,'boundary-v18-01','원문이 정의한 직접 결과를 유지하면서 역할·일반 경영분석·계좌 개설·대차 인도와의 경계를 교정했습니다.')

i='WGSS-3DFF635AF396';r=copy.deepcopy(second['SEMANTIC-'+i])
r['fields']['includes']=['타카풀 참가자 위험 일부에 대한 상호보장 풀 출재관계 성립']
r['fields']['excludes']+=['원수 타카풀 참가자에 대한 배상의무의 법적 이전(경개)', '단순히 샤리아 라벨만 붙인 재래식 재보험 출재']
selected(i,r,'boundary-v18-02','IFSB 27의 위험 공유 풀과 재래식 재보험자 인수의 차이를 보존합니다. 원수 배상의무 자체가 법적으로 이전된다는 주장은 제외하고, 실제 위험공유 구조가 없는 라벨 변형은 새 업무로 세지 않습니다.')

i='WGSS-3C503665EDE3';r=copy.deepcopy(second['SEMANTIC-'+i])
r['fields']['includes']=['반환 선택이 있는 클로즈드엔드 리스의 만기 계약 종료 처리']
r['fields']['definition']='리스제공자가 반환 선택이 있는 리스의 만기 종료를 처리하여 계약의 계속 사용관계가 끝나는 결과. 종료에 따른 물건 검사·반환·잔여 부담금은 적용 절차이며 담보권 해지 자체와 구별합니다.'
r['fields']['applicability_conditions']=['FRB의 미국 클로즈드엔드 차량 리스 만기 절차를 직접 근거로 합니다. 다른 리스 유형·중도 종료 권한은 별도 계약 확인이 필요합니다.']
selected(i,r,'boundary-v18-02','BIAN의 leasing 일반 운영과 FRB 만기 반환 절차를 대조하여 입증된 만기 종료로 한정합니다. 미입증 중도 해지 권한과 담보권 해지를 섞지 않습니다.')

for i in ['WGSS-BB9E69AF7B7D','WGSS-A3D3B2A84738']:
 r=copy.deepcopy(process[i])
 if i=='WGSS-BB9E69AF7B7D':
  r['fields']['title']='연금제도 가입 등록'
  r['fields']['applicability_conditions']=['NEST의 사용자·권한 있는 관리자 등록 절차가 직접 근거입니다. 가입관계와 상품 자격목록 판정을 구별하며 다른 제도의 신청 경로는 별도 확인합니다.']
  r['evidence_section_ids']=[s for s in r['evidence_section_ids'] if s.startswith('NEST_ENROLMENT_PROCESS:')]
 else:
  r['fields'].update(title='담보 말소용 문서 발급',outcome_key='issue_mortgage_satisfaction_document_for_lien_release')
  r['fields']['applicability_conditions']=['Chase 미국 주택담보대출의 완제 후 말소용 문서 발급·등록관청 송부 절차입니다. 등록관청의 실제 말소와 기관의 문서 발급은 다른 결과입니다.']
 selected(i,r,'targeted-v18-process-proof-bounded','공식 절차가 뒷받침하는 실제 책임 주체·문서 결과로 교정했습니다. 앞선 근거 없는 역할 고정 또는 이미 말소된 사실의 증명이라는 제안은 반려했습니다.')

i='WGSS-A876ACA7DC86';r=copy.deepcopy(amend[i])
r['fields']['applicability_conditions']=['보증: URDG/ISDGP가 편입된 경우의 변경 효력 조건', '화환신용장: UCP600이 편입된 경우의 변경 효력 조건',
 '스탠바이 등 다른 준거규칙은 해당 계약을 확인합니다. 모든 스탠바이에 URDG를 일괄 적용하지 않습니다.', '사전 합의된 자동변경 조항은 해당 준거규칙·계약상 조건에 따라 적용합니다.']
selected(i,r,'targeted-v18-undertaking-amendment-bounded','두 ICC 원문 모두 발행인 구속과 수익자 수락을 기술합니다. 동일 조건을 다른 완료조건처럼 설명한 제안을 반려하고 기존 발행확약 조건변경으로 통합합니다. 최초 발행·서류심사·실제 지급을 포함하지 않습니다.')
actions.append(dict(work_id='WGSS-F1BBF631D3AB',decision='merged',target_ids=[i],job_id='targeted-v18-undertaking-amendment-bounded',
 evidence_section_ids=amend['WGSS-F1BBF631D3AB']['evidence_section_ids'],reason='상품별 준거규칙 조건을 통합 정의에 보존하되 동일 발행확약 조건변경 결과를 두 번 세지 않습니다.',automatic_adoption=False))

i='WGSS-F92805EAE41E'
fields=dict(title='계좌 간 자금이체 실행',includes=by[i]['includes']+['스윕·캐시 컨센트레이션 목적의 동일 계좌 자금이전 실행'],
 excludes=by[i]['excludes']+['스윕 지시·약정 등록', '실제 이동 없는 노셔널 풀링'],definition=by[i]['definition'])
actions.append(dict(work_id=i,decision='corrected_edit',fields=fields,job_id='targeted-v18-process-proof-bounded',
 evidence_section_ids=process['WGSS-B947CF3FC565']['evidence_section_ids'],reason='HSBC에서 실제 스윕 자금이동을 확인했습니다. 같은 자금이동의 자동·집중 목적은 새 업무가 아니며 지시 등록·무이동 풀링과 구별합니다.',automatic_adoption=False))
actions.append(dict(work_id='WGSS-B947CF3FC565',decision='merged',target_ids=[i],job_id='targeted-v18-process-proof-bounded',
 evidence_section_ids=process['WGSS-B947CF3FC565']['evidence_section_ids'],reason='기존 계좌간 자금이체 실행의 목적·자동화 변형으로 연결합니다. 같은 실행 결과를 중복 집계하지 않습니다.',automatic_adoption=False))

# Preserve the rejected unsupported financial duty as an excluded hypothesis,
# not a finding that no financial provider anywhere can offer notice services.
r=proposal('boundary-v18-03')['SOURCE-WGSS-B33218BC1C8A']
actions.append(dict(work_id='WGSS-B33218BC1C8A',decision='rejected_unproven_candidate',target_ids=[],job_id='boundary-v18-03',
 evidence_section_ids=r['evidence_section_ids'],reason='보험자 통지의무는 근거가 없습니다. FINRA의 통상 법원 지정 법률사무소 통지와 IBKR의 조건부 서비스 범위를 보존하고 미입증 금융기관 책임 후보를 집계에서 제거합니다. 금융기관의 실제 통지서비스가 세계 어디에도 없다는 뜻은 아닙니다.',automatic_adoption=False))
write(RUN/'root-boundary-sections.json',sections)
write(ROOT/'data/mece-v18-boundary-dispositions.json',dict(version='WGSS-root-boundaries-v18-20261006',input_version=read(RUN/'catalogue-input.json')['version'],
 actions=actions,unresolved_input_ids=['lending-trade-invoice financing advance-draw-51','institution-processing-consolidated treasury position-determine and hedge-51'],
 rejected_findings=[dict(job_id='boundary-v18-01',work_id='WGSS-BB9E69AF7B7D',reason='기존 HR·Pension 명사로 고객 가입자의 등록 책임을 고정한 편집 제안은 반려하고 NEST 절차로 재검토했습니다.'),
 dict(job_id='boundary-v18-02',work_id='WGSS-A876ACA7DC86',reason='보증만 발행 시 구속된다는 수락조건 차이 주장은 ICC 원문에 반합니다.'),
 dict(job_id='boundary-v18-02',work_id='WGSS-F1BBF631D3AB',reason='수익자 수락을 신용장만의 완료조건으로 사용한 구분자는 사실 오류입니다.')],
 automatic_adoption=False,global_mece_approved=False,independent_human_review=False))
print('13 explicit root actions; 2 input relationships require further result coverage')
