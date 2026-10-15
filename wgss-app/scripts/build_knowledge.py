"""Build canonical source-backed SQLite graph and read-only JSON views.

No legacy scenario definition is read into the active corpus. Headings index
actual provider functions; they do not define the universe of financial cases.
"""
import hashlib,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist/data';I=ROOT/'research/data-v10/inputs';T=ROOT/'research/data-v10/source-texts'
def read(p):return json.loads(p.read_text())
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
iso=read(D/'iso-concept-index.json');audit=read(I/'audit.json');new=read(I/'new-evidence.json');reviewed=read(I/'records.json')+new['records'];screen_audit=read(I/'screen-audit.json')
targets=read(ROOT/'research/benchmark-targets.json')['products']
# Registry labels describe the supported service scope; do not infer personal
# versus business eligibility from a general help document.
for p in targets:
 if p['id']=='WISE':p['name']='Wise · 카드·송금·계정 서비스'
 if p['id']=='MONZO':p['name']='Monzo · 카드·계좌 서비스'
 if p['id']=='PAYPAL':p['name']='PayPal · 결제·환불'
provider_products={'Wise':'WISE','Monzo':'MONZO','PayPal':'PAYPAL','Citi':'CITI_RETAIL','CitiManager':'CITI_MANAGER','Revolut':'REVOLUT','금융결제원 Payinfo':'PAYINFO','Pay.UK':'PAYUK','토스':'TOSS'}
source_snapshots=[];nodes=[];relations=[]
iso_snap=iso['source']|{'id':'ISO-20260904','standard':'ISO20022','version':iso['version'],'sha256':iso['source']['archive_sha256'],'retrieved_at':iso['source']['retrieved_at']};source_snapshots.append(iso_snap)
for n in iso['concepts']:
 nodes.append({'id':'ISO20022:'+n['id'],'native_id':n['id'],'name':n['name'],'definition':n['definition_en'],'kind':'BusinessComponent','standard':'ISO20022','maturity':n['registration_status'],'source_snapshot_id':iso_snap['id'],'source_url':iso_snap['url'],'source_locator':n['source_locator'],'attributes':n['attributes']})
for r in iso['relations']:relations.append(r|{'id':'ISO20022:'+r['id'],'from_id':'ISO20022:'+r['from'],'to_id':'ISO20022:'+r['to'],'source_snapshot_id':iso_snap['id'],'standard':'ISO20022','assertion_kind':'original_XML_reference'})
standard_counts={'ISO20022':{'objects':len(iso['concepts']),'relations':len(iso['relations']),'attributes':sum(len(c['attributes']) for c in iso['concepts'])}}
for name in ['bian','fibo','nist']:
 c=read(I/(name+'-catalogue.json'));nodes+=c['nodes'];nodes+=c.get('operations',[]);relations+=c['relations'];source_snapshots+=c['source_snapshots'];standard_counts[name.upper()]=c['counts']
known={n['id'] for n in nodes};external=[]
for r in relations:
 for side in ['from_id','to_id']:
  uid=r[side]
  if uid not in known:
   assert uid.startswith('http'),f'Unresolved non-IRI relation endpoint {uid}'
   external.append({'id':uid,'native_id':uid,'name':uid.rsplit('/',1)[-1],'definition':None,'kind':'ExternalReference','standard':'External','maturity':'external definition not imported','source_snapshot_id':r['source_snapshot_id'],'source_url':r.get('source_url'),'source_locator':r.get('source_locator')});known.add(uid)
nodes+=external
# Official source identity checks and mapping interpretation are separate fields.
for n in nodes:n['reference_state']='official_source_parsed' if n['kind']!='ExternalReference' else 'unfetched_external_reference';n['definition_state']='original_source' if n.get('definition') else 'absent'
source_rows=[]
for s in audit['source_retrievals']:
 meta=s['source_metadata'];sid=s['source_id'];source_rows.append(meta|{'id':sid,'url':s.get('resolved_url') or s['requested_url'],'retrieved_at':s['checked_at'],'checked_at':s['checked_at'],'http_status':s['http_status'],'sha256':s.get('sha256'),'source_state':'retrieved' if s['http_status']==200 else 'unreachable','snapshot_id':'provider:'+sid+':20261002','title':s.get('title') or meta['title']})
for s in new['sources']:source_rows.append(s|{'retrieved_at':s['checked_at'],'sha256':s['source_sha256'],'source_state':'retrieved','snapshot_id':'provider:'+s['id']+':20261002','title':s.get('title') or s['url'].split('/')[-1]})
src={s['id']:s for s in source_rows}
for s in source_rows:source_snapshots.append({'id':s['snapshot_id'],'standard':'Provider','version':s['checked_at'],'url':s['url'],'sha256':s.get('sha256'),'retrieved_at':s['checked_at'],'http_status':s['http_status'],'source_state':s['source_state'],'scope':'Official help revision, not an authenticated app UI capture'})
def check_proof(p):
 assert p and p.get('excerpt') and p.get('locator'), 'Missing evidence locator'
 sid=p['source_id'];assert src[sid]['source_state']=='retrieved';assert p['source_sha256']==src[sid]['sha256'],'Source revision mismatch'
 path=T/(sid+'.normalized.txt')
 if path.exists():text=path.read_text().strip()
 else:text=' '.join((T/(sid+'.txt')).read_text().split())
 assert hashlib.sha256(text.encode()).hexdigest()==p['normalized_text_sha256'],'Normalized text hash mismatch: '+sid
 loc=p['locator'];assert text[loc['start']:loc['end']]==p['excerpt'],'Exact source locator mismatch: '+sid
 return p
# These display labels and aliases are editorial search vocabulary. Membership
# can only be created by a record with current source backing or original screen evidence.
headings={
 'card-lock':('카드 일시 잠금','카드',['카드 잠금','카드 정지','freeze','lock']),
 'card-unlock':('카드 잠금 해제','카드',['카드 잠금 해제','unfreeze','defrost']),
 'card-replacement':('분실·도난 카드 교체','카드',['카드 분실','카드 재발급','카드 분실신고','replace']),
 'card-security-restriction':('카드 보안 제한 해결','카드',['보안 제한','카드 해제 안됨']),
 'transfer-status':('송금 진행 상태','송금',['송금 상태','송금 완료','입금 대기']),
 'transfer-cancel':('송금 취소','송금',['송금 취소','이체 취소']),
 'refund':('결제·송금 환불','송금',['환불','환급','refund']),
 'direct-debit-end':('자동납부 동의 해지','자동이체',['자동이체 해지','자동이체 취소','direct debit']),
 'standing-order-end':('정기 송금 취소','자동이체',['자동이체 해지','자동이체 취소','정기 송금','standing order']),
 'fx-rate':('환율·환전 예상 금액 조회','환전',['환율','환전 예상','환율 계산기']),
 'identity-proofing':('신원 확인','신원·인증',['본인확인','본인 인증','신원 확인','신분증','identity verification']),
 'login-authentication':('계정 추가 인증','신원·인증',['로그인 인증','2단계 인증','2-step','추가 인증'])}
records=[];archived=[];features={};claim_rows=[]
for rr in reviewed:
 sid=rr['source_id'];intent=rr.get('provisional_normalized_intent');pid=provider_products.get(rr['provider'])
 if rr['status']!='verified_official_document':
  archived.append({'id':rr['id'],'type':'document','title':rr.get('expression') or rr['meaning_ko'],'status':rr['status'],'reason':rr.get('reason'),'source_id':sid,'product_id':pid,'raw':rr,'source_url':src[sid]['url'],'checked_at':rr['checked_at']});continue
 assert intent in headings and pid;support=check_proof(rr.get('function_support'))
 expression=None;expression_proof=None
 if rr.get('expression_status')=='document_wording_verified':expression_proof=check_proof(rr['expression_proof']);expression=rr['expression']
 fid='feature:'+':'.join((pid,intent,rr['market'],rr['language']))
 scope=rr['product_scope'];meaning=rr['meaning_ko'];claims=[]
 for c in rr['claims']:
  accepted=c.get('verification_status')=='supported' and c.get('state')=='known';p=check_proof(c['proof']) if accepted else None
  claims.append(c|{'value':c['value'] if accepted else None,'state':'known' if accepted else 'unknown','status':'source_checked' if accepted else 'unsupported' if c.get('verification_status')=='unsupported' else 'not_asserted','semantic_assessment':'editor_assessed' if accepted else 'not_assessed','locator':p['locator'] if p else None,'proof':p})
  claim_rows.append({'id':rr['id']+':'+c['field'],'reference_entity_id':fid,'feature_id':fid if pid!='PAYUK' else None,'policy_context_id':fid if pid=='PAYUK' else None,'record_id':rr['id'],'source_snapshot_id':src[c.get('source_id') or sid]['snapshot_id'],'field':c['field'],'value':c['value'] if accepted else None,'status':'source_checked' if accepted else 'unsupported' if c.get('verification_status')=='unsupported' else 'not_asserted','proof':p,'semantic_assessment':'editor_assessed' if accepted else 'not_assessed'})
 record={'id':rr['id'],'type':'document','task_id':intent,'reference_entity_id':fid,'feature_id':fid if pid!='PAYUK' else None,'policy_context_id':fid if pid=='PAYUK' else None,'product_id':pid,'benchmark':next(p for p in targets if p['id']==pid)['role']=='benchmark','feature_ids':[fid] if pid!='PAYUK' else [],'policy_context_ids':[fid] if pid=='PAYUK' else [],'market':rr['market'],'language':rr['language'],'channel':'unknown','title':expression or meaning,'expression':expression,'expression_proof':expression_proof,'expression_role':rr.get('expression_role'),'meaning':meaning,'claims':claims,'scope':scope,'source_id':sid,'source_url':src[sid]['url'],'source_sha256':src[sid]['sha256'],'source_snapshot_id':src[sid]['snapshot_id'],'checked_at':rr['checked_at'],'ui_version':None,'function_support':support,'notes':[rr['qualification']] if rr.get('qualification') else [],'status':'source_checked','semantic_assessment':'editor_assessed','independent_human_review':False,'locator':support['locator']}
 records.append(record)
 feature=features.setdefault(fid,{'id':fid,'intent_id':intent,'product_id':pid,'market':rr['market'],'language':rr['language'],'name':headings[intent][0],'label_origin':'editorial_search_descriptor','function_proofs':[],'record_ids':[],'entity_kind':'provider_function' if pid!='PAYUK' else 'scheme_policy_context','support_state':'source_backed_editor_assessed'})
 feature['function_proofs'].append(support);feature['record_ids'].append(rr['id'])
# These screen-to-intent assignments were visually reviewed from each original
# image and scope; they are not copied from legacy case IDs.
screen_intents={'UI001':'direct-debit-end','UI002':'direct-debit-end','UI003':'direct-debit-end','UI004':'card-replacement','UI005':'card-unlock','UI006':'fx-rate','UI007':'fx-rate'}
for sa in screen_audit:
 s=sa['original_record'];assert sa['local_integrity_ok'];assert hashlib.sha256((ROOT/'dist'/s['image_path']).read_bytes()).hexdigest()==s['image_sha256']
 intent=screen_intents[s['id']];pid=provider_products[s['provider']];fid='feature:'+':'.join((pid,intent,s['market'],s['language']));snapid='screen:'+s['id']+':'+s['image_sha256'][:12]
 source_snapshots.append({'id':snapid,'standard':'ProviderScreen','version':s['observed_at'],'url':s['source_url'],'sha256':s['image_sha256'],'source_document_sha256':s['source_sha256'],'retrieved_at':s['observed_at'],'scope':s['product_scope'],'http_status':sa.get('http_status')})
 rec={'id':s['id'],'type':'screen','task_id':intent,'reference_entity_id':fid,'feature_id':fid,'feature_ids':[fid],'product_id':pid,'benchmark':True,'market':s['market'],'language':s['language'],'channel':s['channel'],'title':s['title'],'expression':' · '.join(x['text'] for x in s['expressions']),'expressions':s['expressions'],'scope':s['product_scope'],'source_url':s['source_url'],'source_snapshot_id':snapid,'source_sha256':s['source_sha256'],'locator':s['source_locator'],'checked_at':s['last_checked_at'],'integrity_checked_at':sa['checked_at'],'ui_version':None,'image_path':s['image_path'],'image_sha256':s['image_sha256'],'evidence_kind':s['evidence_kind'],'policy_conflict':s['policy_match']=='conflicts_current_help','notes':[s['usage_note']],'conditions':[m['condition'] for m in s['case_mappings']],'status':'screen_preserved','semantic_assessment':'editor_assessed','independent_human_review':False,'current_source_state':sa['status']}
 records.append(rec);f=features.setdefault(fid,{'id':fid,'intent_id':intent,'product_id':pid,'market':s['market'],'language':s['language'],'name':headings[intent][0],'label_origin':'editorial_search_descriptor','function_proofs':[],'record_ids':[],'entity_kind':'provider_function','support_state':'source_derived_screen_editor_assessed'});f['record_ids'].append(s['id']);f['function_proofs'].append({'source_snapshot_id':snapid,'source_url':s['source_url'],'locator':s['source_locator'],'excerpt':rec['expression'],'image_sha256':s['image_sha256'],'proof_kind':s['evidence_kind']})
# Carefully scoped interpretive links. References are official; linking a
# provider function to a reference is a WGSS interpretation, never equivalence.
def find(standard,name,kind=None):
 matches=[n for n in nodes if n['standard']==standard and n['name']==name and (kind is None or n['kind']==kind)];assert len(matches)==1,(standard,name,len(matches));return matches[0]
seeds={
 'card-lock':[('ISO20022','PaymentCard','object_anchor'),('FIBO','payment card','supporting_semantic')],
 'card-unlock':[('ISO20022','PaymentCard','object_anchor'),('FIBO','payment card','supporting_semantic')],
 'card-replacement':[('ISO20022','PaymentCard','object_anchor'),('BIAN','Issued Device Administration','capability_context'),('FIBO','payment card','supporting_semantic')],
 'card-security-restriction':[('ISO20022','PaymentCard','object_anchor')],
 'transfer-status':[('ISO20022','PaymentInstruction','object_anchor'),('ISO20022','PaymentStatus','object_anchor'),('FIBO','payment','supporting_semantic'),('BIAN','Payment Order Initiation','capability_context')],
 'transfer-cancel':[('ISO20022','PaymentInstruction','object_anchor'),('BIAN','Payment Order Initiation','capability_context')],
 'refund':[('ISO20022','Payment','object_anchor'),('FIBO','payment','supporting_semantic')],
 'direct-debit-end':[('ISO20022','DirectDebitMandate','object_anchor')],
 'standing-order-end':[('ISO20022','CashStandingOrder','object_anchor'),('BIAN','Standing Order','capability_context')],
 'fx-rate':[('ISO20022','CurrencyExchange','object_anchor'),('FIBO','currency','supporting_semantic')],
 'identity-proofing':[('ISO20022','Person','subject_context'),('NIST','identity proofing','supporting_semantic')],
 'login-authentication':[('BIAN','Party Authentication','capability_context'),('NIST','authentication','supporting_semantic')]}
# CurrencyExchange BIAN is OTC execution, not an online indicative rate calculator.
# DirectDebitMandate BIAN is corporate/creditor servicing, not a personal revocation.
mapping_rationales={
 'PaymentCard':'카드 접근·전자지급 수단의 업무 대상을 참고합니다. 임시 잠금과 교체의 실제 효력은 금융사 자료로 구분합니다.',
 'PaymentInstruction':'송금 지시의 대상을 참고합니다. 지시 제출·처리·취소 가능 시점은 금융사 원문 기록으로 구분합니다.',
 'PaymentStatus':'사업자가 보고한 지급 상태를 참고합니다. UI 상태 문구를 ISO 코드 또는 수취인 입금 완료와 동치로 두지 않습니다.',
 'Payment':'금전 전달의 개념을 참고합니다. 환불 시작과 실제 계정 반영을 구분하며 개별 계약상 의무를 추정하지 않습니다.',
 'DirectDebitMandate':'출금에 대한 동의·권한의 대상을 참고합니다. 동의 철회와 서비스 계약·채무 해지를 구분합니다.',
 'CashStandingOrder':'고객이 지정하는 정기 지급 지시를 참고합니다. 출금권자가 청구하는 자동납부와 구분합니다.',
 'CurrencyExchange':'통화 변환의 개념을 예상 금액 계산의 대상으로 참고합니다. 실제 환전 실행이나 현재 거래 견적을 뜻하지 않습니다.',
 'Person':'신원확인의 대상인 사람을 참고합니다. ISO가 신원확인 절차나 보증 수준을 정한 것으로 해석하지 않습니다.',
 'Issued Device Administration':'원문이 명시한 카드 등 발급 장치의 교체 관리 범위를 참고합니다. 일반적인 임시 잠금·취소 정책과 동치로 두지 않습니다.',
 'Payment Order Initiation':'고객의 지급 정보와 지시를 받아 거래를 조직하는 업무 범위를 참고합니다. 송금 상태·취소 효력을 이 API 정의에서 추론하지 않습니다.',
 'Standing Order':'고객의 주기적 지급 지시 업무 범위를 참고합니다. 특정 금융사의 취소 효력이나 처리중 예외를 추론하지 않습니다.',
 'Party Authentication':'은행 상품·서비스 접근을 위한 인증 업무 범위를 참고합니다. 신원증명·권한부여 또는 보증 수준과 동일시하지 않습니다.',
 'payment card':'계좌나 신용 계정의 자금에 접근하는 지급 카드라는 의미를 참고합니다. 발급사별 제한·복구 정책은 별도의 원문을 따릅니다.',
 'payment':'의무 이행을 위한 금전 전달이라는 의미를 참고합니다. 지급·환급 상태와 실제 수취 계정 반영은 별도로 확인합니다.',
 'currency':'계산기에서 변환 대상인 통화의 의미를 참고합니다. 환전 실행 서비스·적용 환율의 근거로 사용하지 않습니다.',
 'identity proofing':'주장된 신원을 수집·확인하는 절차의 의미로 Wise 문서 확인을 분류합니다. 로그인 인증과 구분하며 IAL이나 준수를 판정하지 않습니다.',
 'authentication':'등록 계정에 연결된 인증 수단의 보유·제어 확인이라는 의미를 추가 인증 해석에 참고합니다. 항상 비밀번호+OTP라거나 AAL을 충족한다고 추론하지 않습니다.'}
mappings=[]
for f in features.values():
 for standard,name,role in seeds[f['intent_id']]:
  n=find(standard,name);assert n['kind']!='ExternalReference' and n.get('definition')
  mappings.append({'id':f['id']+'::'+n['id'],'reference_entity_id':f['id'],'feature_id':f['id'] if f['entity_kind']=='provider_function' else None,'policy_context_id':f['id'] if f['entity_kind']=='scheme_policy_context' else None,'target_entity_kind':f['entity_kind'],'task_id':f['intent_id'],'concept_id':n['id'],'concept_name':n['name'],'standard':standard,'role':role,'status':'editor_assessed','reference_status':'official_source_parsed','equivalence_asserted':False,'rationale':mapping_rationales[n['name']],'concept_definition_evidence':{'definition':n['definition'],'source_snapshot_id':n['source_snapshot_id'],'locator':n['source_locator'],'source_url':n['source_url']},'function_evidence':f['function_proofs'][0],'scope_caveat':'객체·업무 범위의 참고 연결이며 UI 절차, 정책 일치, 표준 준수 또는 보증 수준을 뜻하지 않습니다.','source_snapshot_id':n['source_snapshot_id']})
examples=[];tasks=[]
for f in features.values():
 rs=[r for r in records if r['reference_entity_id']==f['id']];p=next(p for p in targets if p['id']==f['product_id']);examples.append({'id':'__'.join((f['intent_id'],f['product_id'],f['market'],f['language'])),'reference_entity_id':f['id'],'feature_id':f['id'] if f['entity_kind']=='provider_function' else None,'policy_context_id':f['id'] if f['entity_kind']=='scheme_policy_context' else None,'task_id':f['intent_id'],'product_id':p['id'],'provider':p['company'],'product':p['name'],'role':p['role'],'market':f['market'],'language':f['language'],'record_ids':f['record_ids'],'feature_ids':[f['id']] if f['entity_kind']=='provider_function' else [],'policy_context_ids':[f['id']] if f['entity_kind']=='scheme_policy_context' else [],'screen_ids':[r['id'] for r in rs if r['type']=='screen'],'channels':sorted({r['channel'] for r in rs if r['channel']!='unknown'}),'policy_conflict':any(r.get('policy_conflict') for r in rs),'support_state':f['support_state'],'entity_kind':f['entity_kind']})
for intent,(title,category,aliases) in headings.items():
 fs=[f for f in features.values() if f['intent_id']==intent]
 if not fs:continue
 refs={m['concept_id'] for m in mappings if m['task_id']==intent};concepts=[n for n in nodes if n['id'] in refs]
 tasks.append({'id':intent,'title':title,'category':category,'aliases':aliases,'feature_ids':[f['id'] for f in fs if f['entity_kind']=='provider_function'],'policy_context_ids':[f['id'] for f in fs if f['entity_kind']=='scheme_policy_context'],'definition':'출처로 확인된 금융사 기능을 묶은 검색 표제입니다. 기업별 적용 범위와 조건은 사례에서 확인하세요.','definition_owner':'WGSS editorial navigation, not a financial case standard','stages':[],'concepts':concepts,'critical_fields':sorted({c['field'] for r in records if r['task_id']==intent and r['type']=='document' for c in r['claims']})})
products=[]
for p in targets:
 rs=[r for r in records if r['product_id']==p['id']];products.append(p|{'record_count':len(rs),'screen_count':sum(r['type']=='screen' for r in rs),'feature_count':sum(f['product_id']==p['id'] and f['entity_kind']=='provider_function' for f in features.values()),'policy_context_count':sum(f['product_id']==p['id'] and f['entity_kind']=='scheme_policy_context' for f in features.values()),'task_ids':sorted({r['task_id'] for r in rs}),'observed_channels':sorted({r['channel'] for r in rs if r['channel']!='unknown'})})
# Canonical persistence with explicit referential integrity and forbidden
# equivalence assertions. All public counts below are SQL-derived.
path=ROOT/'data/wgss.sqlite';path.parent.mkdir(exist_ok=True);temporary=path.with_suffix('.building.sqlite');temporary.unlink(missing_ok=True);db=sqlite3.connect(temporary);db.execute('PRAGMA foreign_keys=ON')
db.executescript('''
CREATE TABLE snapshot(id TEXT PRIMARY KEY,publisher TEXT NOT NULL,sha256 TEXT,data TEXT NOT NULL);
CREATE TABLE concept(id TEXT PRIMARY KEY,standard TEXT NOT NULL,kind TEXT NOT NULL,name TEXT NOT NULL,snapshot_id TEXT REFERENCES snapshot(id),data TEXT NOT NULL);
CREATE TABLE relation(id TEXT PRIMARY KEY,from_id TEXT NOT NULL REFERENCES concept(id),to_id TEXT NOT NULL REFERENCES concept(id),kind TEXT NOT NULL,snapshot_id TEXT REFERENCES snapshot(id),data TEXT NOT NULL);
CREATE TABLE product(id TEXT PRIMARY KEY,data TEXT NOT NULL);
CREATE TABLE reference_entity(id TEXT PRIMARY KEY,product_id TEXT NOT NULL REFERENCES product(id),intent_id TEXT NOT NULL,support_state TEXT NOT NULL,entity_kind TEXT CHECK(entity_kind IN ('provider_function','scheme_policy_context')),data TEXT NOT NULL);
CREATE TABLE record(id TEXT PRIMARY KEY,reference_entity_id TEXT NOT NULL REFERENCES reference_entity(id),snapshot_id TEXT NOT NULL REFERENCES snapshot(id),kind TEXT NOT NULL,status TEXT NOT NULL,data TEXT NOT NULL);
CREATE TABLE claim(id TEXT PRIMARY KEY,reference_entity_id TEXT NOT NULL REFERENCES reference_entity(id),record_id TEXT NOT NULL REFERENCES record(id),snapshot_id TEXT NOT NULL REFERENCES snapshot(id),status TEXT NOT NULL CHECK(status IN ('source_checked','unsupported','not_asserted')),data TEXT NOT NULL CHECK(json_valid(data)) CHECK(COALESCE((status='source_checked' AND json_type(data,'$.proof')='object' AND json_type(data,'$.value') NOT IN ('null') AND json_type(data,'$.value') IS NOT NULL) OR (status!='source_checked' AND json_type(data,'$.value')='null' AND json_type(data,'$.proof')='null'),0)));
CREATE TABLE mapping(id TEXT PRIMARY KEY,reference_entity_id TEXT NOT NULL REFERENCES reference_entity(id),concept_id TEXT NOT NULL REFERENCES concept(id),role TEXT CHECK(role IN ('object_anchor','subject_context','capability_context','supporting_semantic')),assessment TEXT NOT NULL,equivalence INTEGER NOT NULL DEFAULT 0 CHECK(equivalence=0),data TEXT NOT NULL);
CREATE TABLE heading(id TEXT PRIMARY KEY,title TEXT NOT NULL,data TEXT NOT NULL);
CREATE TABLE heading_feature(heading_id TEXT REFERENCES heading(id),reference_entity_id TEXT REFERENCES reference_entity(id),PRIMARY KEY(heading_id,reference_entity_id));
CREATE TABLE archive(id TEXT PRIMARY KEY,status TEXT NOT NULL,data TEXT NOT NULL);
''')
for s in source_snapshots:db.execute('INSERT INTO snapshot VALUES(?,?,?,?)',(s['id'],s['standard'],s.get('sha256'),canonical(s)))
for n in nodes:db.execute('INSERT INTO concept VALUES(?,?,?,?,?,?)',(n['id'],n['standard'],n['kind'],n['name'],n['source_snapshot_id'],canonical(n)))
for r in relations:db.execute('INSERT INTO relation VALUES(?,?,?,?,?,?)',(r['id'],r['from_id'],r['to_id'],r['kind'],r['source_snapshot_id'],canonical(r)))
for p in products:db.execute('INSERT INTO product VALUES(?,?)',(p['id'],canonical(p)))
for f in features.values():db.execute('INSERT INTO reference_entity VALUES(?,?,?,?,?,?)',(f['id'],f['product_id'],f['intent_id'],f['support_state'],f['entity_kind'],canonical(f)))
for r in records:db.execute('INSERT INTO record VALUES(?,?,?,?,?,?)',(r['id'],r['reference_entity_id'],r['source_snapshot_id'],r['type'],r['status'],canonical(r)))
for c in claim_rows:db.execute('INSERT INTO claim VALUES(?,?,?,?,?,?)',(c['id'],c['reference_entity_id'],c['record_id'],c['source_snapshot_id'],c['status'],canonical(c)))
for m in mappings:db.execute('INSERT INTO mapping VALUES(?,?,?,?,?,?,?)',(m['id'],m['reference_entity_id'],m['concept_id'],m['role'],m['status'],0,canonical(m)))
for t in tasks:
 db.execute('INSERT INTO heading VALUES(?,?,?)',(t['id'],t['title'],canonical(t)))
 for fid in t['feature_ids']+t['policy_context_ids']:db.execute('INSERT INTO heading_feature VALUES(?,?)',(t['id'],fid))
for r in archived:db.execute('INSERT INTO archive VALUES(?,?,?)',(r['id'],r['status'],canonical(r)))
assert not db.execute('PRAGMA foreign_key_check').fetchall()
def count(sql):return db.execute(sql).fetchone()[0]
counts={'search_tasks':count('SELECT count(*) FROM heading'),'provider_features':count("SELECT count(*) FROM reference_entity WHERE entity_kind='provider_function'"),'scheme_policy_contexts':count("SELECT count(*) FROM reference_entity WHERE entity_kind='scheme_policy_context'"),'examples':len(examples),'document_records':count("SELECT count(*) FROM record WHERE kind='document'"),'screen_records':count("SELECT count(*) FROM record WHERE kind='screen'"),'records':count('SELECT count(*) FROM record'),'iso_objects':len(iso['concepts']),'iso_relations':len(iso['relations']),'products':count('SELECT count(*) FROM product'),'benchmark_products':sum(p['role']=='benchmark' for p in products),'application_mappings':count('SELECT count(*) FROM mapping'),'claims_source_checked':count("SELECT count(*) FROM claim WHERE status='source_checked'"),'claims_unsupported':count("SELECT count(*) FROM claim WHERE status='unsupported'"),'claims_not_asserted':count("SELECT count(*) FROM claim WHERE status='not_asserted'"),'quarantined_records':count("SELECT count(*) FROM archive WHERE status='quarantined'"),'excluded_records':count("SELECT count(*) FROM archive WHERE status!='quarantined'"),'tasks_with_reference':len(tasks),'tasks_with_screen':len({r['task_id'] for r in records if r['type']=='screen'}),'native_app_captures':0,'verified_ui_versions':0,'independent_human_reviews':0}
db.commit();db.close();temporary.replace(path)
standard_catalogue={'version':'1.0.0','source_snapshots':[s for s in source_snapshots if s['standard'] not in ['Provider','ProviderScreen']],'nodes':nodes,'relations':relations,'counts_by_standard':standard_counts,'limitations':['표준의 객체·서비스 자원·용어·절은 서로 다른 단위입니다. 이를 더해 금융업무 총수로 삼지 않습니다.','FIBO 원문에 포함된 외부 IRI 참조는 정의를 가져온 용어와 구분합니다.','BIAN 작업은 공식 API의 작업이며 금융사 UI 기능 수가 아닙니다.','WGSS 연결은 해석이며 표준 간 동치 또는 금융사 준수 판정이 아닙니다.']}
dump(D/'standards.json',standard_catalogue)
library={'version':'1.0.0','scope_note':'검색 표제는 원문에서 확인한 금융사 기능을 찾는 편집용 분류입니다. 기존 42개 상황 정의·26개 검색 표제·176개 분류는 활성 데이터의 근간이나 분모로 사용하지 않습니다. 객체와 기업 기능의 연결은 표준 원문을 참조한 WGSS 해석이며 표준 준수 인증이 아닙니다.','tasks':tasks,'features':[f for f in features.values() if f['entity_kind']=='provider_function'],'policy_contexts':[f for f in features.values() if f['entity_kind']=='scheme_policy_context'],'examples':examples,'records':records,'sources':source_rows,'products':products,'mappings':mappings,'iso_source':iso['source'],'standard_counts':standard_counts,'standard_snapshots':standard_catalogue['source_snapshots'],'counts':counts,'archived_records':archived,'legacy_definitions_policy':'historical_only; no active scenario FK','database_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'build_inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [I/'audit.json',ROOT/'research/benchmark-targets.json',I/'records.json',I/'new-evidence.json',I/'screen-audit.json',D/'iso-concept-index.json',I/'bian-catalogue.json',I/'fibo-catalogue.json',I/'nist-catalogue.json']}}
dump(D/'library.json',library);dump(ROOT/'research/data-v10/build-report.json',{'counts':counts,'standards':standard_counts,'database_sha256':library['database_sha256'],'foreign_key_check':'passed','llm_counting':False});print(json.dumps({'counts':counts,'standards':standard_counts},ensure_ascii=False))
