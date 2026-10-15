"""Import a pinned official ISO 20022 BusinessComponent subset; never infer edges."""
import argparse, hashlib, json, urllib.request, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL='https://www.iso20022.org/sites/default/files/media/file/20260904_ISO20022_2013_eRepository.zip'
XMI='{http://www.omg.org/XMI}id'; TYPE='{http://www.w3.org/2001/XMLSchema-instance}type'
LABELS={
 'Account':'계좌', 'CashAccount':'현금 계좌', 'Balance':'잔액', 'CashBalance':'현금 잔액',
 'Entry':'기장 항목', 'CashEntry':'현금 거래 기장', 'AccountPartyRole':'계좌 관계자의 역할',
 'AccountOwnerRole':'계좌 소유자 역할', 'AccountServicerRole':'계좌 관리기관 역할',
 'Payment':'지급', 'PaymentExecution':'지급 실행', 'PaymentInitiation':'최초 지급 지시',
 'PaymentInstruction':'지급 지시', 'PaymentStatus':'지급 상태', 'PaymentPartyRole':'지급 참여자 역할',
 'CreditTransfer':'이체 지급', 'DirectDebit':'수취인 주도 출금', 'Mandate':'권한 위임',
 'DirectDebitMandate':'출금 동의', 'StandingOrder':'반복 지시', 'CashStandingOrder':'정기 이체 지시',
 'CurrencyExchange':'환전·통화 변환', 'Interest':'이자', 'InterestCalculation':'이자 계산',
 'Loan':'대출', 'Deposit':'예치·예금', 'CashLoanDeposit':'현금 대차·예치 약정',
 'PaymentCard':'지급 카드', 'CardPayment':'카드 지급', 'Charges':'수수료',
 'AccountContract':'계좌 계약', 'CashAccountContract':'현금 계좌 계약', 'AccountStatus':'계좌 상태',
 'IndividualPayment':'개별 지급', 'Contract':'계약', 'Debt':'채무',
}
def extract(path):
 digest=hashlib.sha256(Path(path).read_bytes()).hexdigest();rows=[]
 assert digest=='fb1504abc9df0d445880faedeb0aad208047820a61bd1754bb571c1419ae1c88','Pinned archive hash changed; review the new snapshot before importing'
 with zipfile.ZipFile(path) as z:
  member=z.namelist()[0]
  for _,e in ET.iterparse(z.open(member),events=['end']):
   if e.tag=='topLevelDictionaryEntry':
    if e.get(TYPE)=='iso20022:BusinessComponent':
     rows.append({'a':dict(e.attrib),'elements':[dict(x.attrib) for x in e]})
    e.clear()
 byid={r['a'][XMI]:r for r in rows};selected={r['a'][XMI] for r in rows if r['a']['name'] in LABELS}
 assert len(selected)==len(LABELS),'Selected name missing from pinned repository'
 concepts=[];relations=[]
 for r in rows:
  a=r['a'];uid=a[XMI]
  if uid not in selected:continue
  concepts.append({'id':uid,'name':a['name'],'label_ko':LABELS[a['name']],
   'kind':'BusinessComponent','definition_en':a.get('definition',''),
   'registration_status':a.get('registrationStatus'), 'source_id':'ISO-20260904',
   'attributes':[{'id':x[XMI],'name':x['name'],'definition_en':x.get('definition',''),
    'registration_status':x.get('registrationStatus'),'min_occurs':x.get('minOccurs'),
    'max_occurs':x.get('maxOccurs')} for x in r['elements'] if x.get(TYPE)=='iso20022:BusinessAttribute']})
  parent=a.get('superType')
  if parent in selected:
   relations.append({'id':uid+'::superType','kind':'generalization','from':uid,'to':parent,
    'name':'superType','opposite_id':None,'min_occurs':None,'max_occurs':None,
    'registration_status':a.get('registrationStatus'),'source_id':'ISO-20260904'})
  for x in r['elements']:
   if x.get(TYPE)=='iso20022:BusinessAssociationEnd' and x.get('type') in selected:
    relations.append({'id':x[XMI],'kind':'association_end','from':uid,'to':x['type'],
     'name':x['name'],'opposite_id':x.get('opposite'),'min_occurs':x.get('minOccurs'),
     'max_occurs':x.get('maxOccurs'),'registration_status':x.get('registrationStatus'),
     'source_id':'ISO-20260904'})
 return {'version':'0.2.0','source':{'id':'ISO-20260904','title':'ISO 20022 e-Repository · 20260904 snapshot',
  'url':URL,'landing_url':'https://www.iso20022.org/iso20022-repository/e-repository',
  'model_url':'https://www.iso20022.org/iso20022-repository/business-model',
  'license_url':'https://www.iso20022.org/intellectual-property-rights',
  'retrieved_at':'2026-09-30','snapshot_label':'20260904 (배포 파일명)',
  'archive_sha256':digest,'archive_member':member,'total_business_components':len(rows),
  'scope':'Selected BusinessComponents, direct attributes and intra-subset association ends / generalizations.',
  'limitations':['전체 모델 또는 모든 업무 프로세스의 수록이 아님','양방향 association end는 서로 다른 항목으로 보존','관계는 상태 전이나 처리 순서가 아님','생략된 다중성은 null로 보존; 0 또는 무한으로 추정하지 않음','한국어 이름과 UI 연결은 WGSS 해석; ISO 승인 번역이 아님']},
  'concepts':concepts,'relations':relations}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--download',action='store_true');a=p.parse_args()
 if a.download:
  with urllib.request.urlopen(URL,timeout=90) as r:Path(a.archive).write_bytes(r.read())
 out=extract(a.archive);(ROOT/'dist/data/business-model.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(f"Imported {len(out['concepts'])} concepts / {len(out['relations'])} directed relations from {out['source']['total_business_components']} BusinessComponents")
