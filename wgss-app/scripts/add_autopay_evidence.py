"""Add verified official-document evidence for the D03/S03 design task."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist/data'
read=lambda n:json.loads((D/n).read_text())
def write(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
sources=read('sources.json');observations=read('observations.json');cases=read('cases.json')
for case in cases:
 if case['id']=='D03' and '자동이체 해지' not in case['aliases']: case['aliases'].append('자동이체 해지')
sources=[s for s in sources if s['id'] not in {'S16','S17','S18','S19'}]
observations=[o for o in observations if o['id'] not in {'O37','O38','O39','O40','O41'}]
def src(id,provider,title,url,market,language,kind,locator,summary):
 sources.append(dict(id=id,provider=provider,title=title,url=url,market=market,language=language,source_type=kind,retrieved_at='2026-09-30',effective_from=None,app_version=None,ui_observed_at=None,locator=locator,summary=summary,review_status='agent_checked',independent_review=False))
src('S16','금융결제원 Payinfo','자동이체 해지서비스 이용안내','https://payinfo.or.kr/guide/useguide2.do','KR','ko','official_scheme_guide','자동이체 해지서비스 / STEP 05~09','자동납부·자동송금을 구분하고 해지 신청 접수, 금융회사별 실시간 또는 익영업일 처리, 당일 출금 가능성, 서비스 계약과 납부 의무가 별도로 남을 수 있음을 안내한다.')
src('S17','금융결제원 Payinfo','자동이체 통합관리 FAQ','https://payinfo.or.kr/cs/faq/qryListWebFaq.do','KR','ko','official_scheme_faq','자동이체서비스란 / 해지 취소 / 송금 종료일 / 처리중','자동납부는 요금청구기관이 시작하고 자동송금은 고객이 설정한다고 구분한다. 해지 신청 취소 가능성, 종료일 경과, 처리중 예외를 설명한다.')
src('S18','Pay.UK','Cancelling a Direct Debit','https://www.directdebit.co.uk/help/cancelling-a-direct-debit/','GB','en','official_scheme_guide','How do I cancel / When should I cancel / after cancellation','은행·앱에서 Direct Debit을 취소할 수 있으며, 최소 하루 전 안내, in-flight 가능성, 회사 통지와 취소 뒤 출금 시 환급 문의를 설명한다.')
src('S19','Monzo','Cancelling and identifying scheduled payments','https://monzo.com/help/payments-troubleshooting/how-to-authorise-different-payments-web','GB','en','official_help','Standing order / Direct Debit setup and cancellation','Standing order는 사용자가 금액·주기 등을 설정하고 Direct Debit은 회사에 계좌정보를 제공해 설정한다고 구분하며 각각의 현재 취소 경로를 안내한다.')
def claim(field,state='unknown',value=None,source_id=None,locator=None,basis=None):return dict(field=field,value=value,state=state,source_id=source_id,locator=locator,basis=basis)
def obs(id,case_id,source_id,provider,market,language,scope,expression,role,meaning,facts,claims,locator,notes):
 observations.append(dict(id=id,case_id=case_id,mapping_status='mapped',source_id=source_id,provider=provider,market=market,language=language,product_scope=scope,expression=expression,expression_role=role,meaning_ko=meaning,scene='action_entry',facts=facts,claims=claims,source_locator=locator,observed_in_app=False,review_status='agent_checked',independent_review=False,notes=notes))
obs('O37','D03','S16','금융결제원 Payinfo','KR','ko','Payinfo 자동이체 해지서비스의 자동납부 등록; 개별 금융회사 앱 일반화 금지','자동이체(납부)','feature_name','요금청구기관이 시작하는 향후 자동납부 등록의 해지를 신청한다.',{'object':'direct_debit_mandate','action':'revoke','automatic_payment_type':'collection'},[
 claim('revocation_effective_at','known','conditional','S16','해지서비스 / 실시간 또는 일부 익영업일 처리','explicit'),
 claim('pending_collections','known','conditional','S16','해지 당일 출금 예정 시 출금될 수 있음','explicit'),
 claim('creditor_notification')], '자동이체 해지서비스 / STEP 05~09',['서비스 계약·채무 해지가 아니며, 해지 신청 접수와 결과 확정을 분리한다.','실제 앱 화면은 관찰하지 않았다.'])
obs('O38','S03','S16','금융결제원 Payinfo','KR','ko','Payinfo 자동이체 해지서비스의 자동송금 등록; 개별 금융회사 앱 일반화 금지','자동이체(송금)','feature_name','사용자가 설정한 향후 반복 송금 지시의 해지를 신청한다.',{'object':'standing_order','action':'cancel','automatic_payment_type':'transfer'},[
 claim('cancellation_effective_at','known','conditional','S16','해지서비스 / 실시간 또는 일부 익영업일 처리','explicit'),
 claim('next_execution','known','conditional','S16','해지 당일 출금 예정 시 출금될 수 있음','explicit'),
 claim('pending_execution','known','conditional','S16','해지 당일 출금 예정 시 출금될 수 있음','explicit')], '자동이체 해지서비스 / STEP 05~09',['이미 실행된 송금의 취소나 회수를 뜻하지 않는다.','실제 앱 화면은 관찰하지 않았다.'])
obs('O39','D03','S18','Pay.UK','GB','en','영국 Direct Debit scheme 일반 안내; 한국·다른 결제망에 적용 금지','Cancelling a Direct Debit','feature_name','영국 Direct Debit의 향후 출금 권한을 은행·앱에서 취소하는 안내다.',{'object':'direct_debit_mandate','action':'revoke','automatic_payment_type':'collection'},[
 claim('revocation_effective_at','known','conditional','S18','When should I cancel','explicit'),
 claim('pending_collections','known','conditional','S18','payment might already be in flight','explicit'),
 claim('creditor_notification','known','required','S18','also worth telling the organisation','explicit')], 'How do I cancel / When should I cancel',['영국 시장·Direct Debit scheme 조건이며 한국 정책 근거가 아니다.','실제 앱 화면은 관찰하지 않았다.'])
obs('O40','D03','S19','Monzo','GB','en','Monzo 개인계좌의 Direct Debit 도움말; 도움말 경로이며 앱 버전 미확인','Direct Debit','feature_name','회사가 계좌정보를 받아 설정하는 지급 방식으로 standing order와 구분한다.',{'object':'direct_debit_mandate','action':'revoke','automatic_payment_type':'collection'},[
 claim('revocation_effective_at','known','conditional','S19','cancel at least 1 day before next payment','explicit'),
 claim('pending_collections','known','conditional','S19','otherwise they might still take the next payment','explicit'),
 claim('creditor_notification','known','required','S19','tell the company you have cancelled','explicit')], 'Direct Debit setup and cancellation',['영국 Monzo 도움말이며 다른 시장·상품에 일반화하지 않는다.','실제 앱 화면은 관찰하지 않았다.'])
obs('O41','S03','S19','Monzo','GB','en','Monzo 개인계좌의 standing order 도움말; 도움말 경로이며 앱 버전 미확인','Cancel standing order/scheduled payment','control_label','사용자가 설정한 반복 송금 지시를 앱에서 취소하는 조작 표기다.',{'object':'standing_order','action':'cancel','automatic_payment_type':'transfer'},[
 claim('cancellation_effective_at'),
 claim('next_execution','known','conditional','S19','cancel at least 1 day before next payment','explicit'),
 claim('pending_execution','known','conditional','S19','otherwise next payment might still be taken','explicit')], 'Standing order setup and cancellation',['Direct Debit과 함께 설명된 공통 하루 전 권고이며 정확한 효력 시점은 미확인이다.','실제 앱 화면은 관찰하지 않았다.'])
write('sources.json',sources);write('observations.json',observations);write('cases.json',cases)
m=read('manifest.json');m.update(observation_count=len(observations),source_count=len(sources),provider_count=len(set(s['provider'] for s in sources)),definition_only_count=sum(not any(o['case_id']==c['id'] for o in observations) for c in cases));write('manifest.json',m)
definition_doc=R/'docs/case-definitions.md'
if definition_doc.exists():
 text=definition_doc.read_text()
 text=text.replace('# WGSS 금융상황 정의 v0.2','# WGSS 금융상황 정의 v0.3')
 text=text.replace('모든 상황은 WGSS 정의 후보. ISO 인증 UI 문구가 아니다. 새 28개 상황의 업체 사례는 미수집.','모든 상황은 WGSS 정의 후보이며 ISO 인증 UI 문구가 아니다. 업체 근거가 없는 정의와 공식 문서 근거가 연결된 정의를 구분한다.')
 definition_doc.write_text(text)
print(f'{len(sources)} sources; {len(observations)} observations')
