from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'dist/data'
VERSION='0.1.0'; DATE='2026-09-29'
def write(name,obj): (D/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
sources=[]
def src(id,provider,title,url,market,section,summary):
 sources.append(dict(id=id,provider=provider,title=title,url=url,market=market,language='en',source_type='official_help',retrieved_at=DATE,effective_from=None,app_version=None,ui_observed_at=None,locator=section,summary=summary,review_status='agent_checked',independent_review=False))
src('S01','Wise','카드 일시 정지와 해제','https://wise.com/help/articles/2977977/how-do-i-freeze-or-unfreeze-my-wise-card','unspecified','How to freeze / What happens / Why cannot unfreeze','일시 정지와 해제 방법, 정기결제 차단, 기존 승인·오프라인 거래 예외, 보안 제한 시 지원 문의를 안내한다.')
src('S02','Citi','Quick Lock 기능 안내','https://www.cardbenefits.citi.com/','US','Credit & Account Protection / Citi Quick Lock','일부 Citi 카드의 임시 잠금은 신규 구매·현금서비스를 차단하고 정기 거래 등을 유지한다. 발견한 카드를 다시 잠금 해제할 수 있다.')
src('S03','Monzo','카드 정지와 해제','https://monzo.com/help/monzo-card-pin/freezing-defrosting','GB','Freezing and defrosting your card','앱에서 정지와 해제 조작을 안내한다. 이 문서에는 정기결제 예외가 명시되지 않는다.')
src('S04','Monzo','분실·손상·도난 카드 대응','https://monzo.com/help/emergencies/monzo-card-lost-damaged-stolen','GB','Lost or damaged cards / Stolen cards','카드 정지 이후 새 카드 주문과 사유 선택을 안내한다. 기존 카드 복구 가능 여부는 이 문서만으로 확정하지 않는다.')
src('S05','Wise','분실·도난 카드 교체','https://wise.com/help/articles/2935777/my-wise-card-was-lost-or-stolen','unspecified','Replacing your card','분실·도난 시 교체하면 기존 카드는 영구 차단되며 복구할 수 없다고 안내한다.')
src('S06','Revolut','미국 카드 정지','https://help.revolut.com/en-US/help/card-payments-withdrawals/ping-other-card-security-settings/freezing-or-blocking-your-card/','US','How to freeze a card','앱과 웹의 정지·해제 조작을 안내한다. 신규 시도 결제는 실패한다고 설명하지만 기존 승인·정기결제 예외는 따로 확정하지 않는다.')
src('S07','Wise','송금 추적 상태','https://wise.com/help/articles/2452305/how-do-i-check-my-transfers-status','unspecified','Understanding your transfer timeline','자금 수령 대기, 사업자 수령·환전, 수취 은행으로의 발송 상태를 구분한다.')
src('S08','Wise','완료 표시와 미도착','https://wise.com/help/articles/2977950/why-does-it-say-my-transfers-complete-when-the-money-hasnt-arrived-yet','unspecified','Introductory explanation','완료 표시는 수취 은행에 돈을 보냈다는 뜻이며 수취인 계좌 입금과 동일한 확정이 아니다.')
src('S09','Wise','송금 취소','https://wise.com/help/articles/2971625/how-do-i-cancel-my-transfer','unspecified','Unpaid / Paid but status unchanged / Processing / Complete','단계에 따라 직접 취소, 지원팀 요청, 취소 불가를 구분한다. 이미 송금했어도 사업자 수령 전 취소라면 환불은 자금 도착을 기다려야 한다.')
src('S10','Wise','송금 취소 사유','https://wise.com/help/articles/2971425/why-was-my-transfer-cancelled','unspecified','You did not pay / We needed more information','미지급과 추가 정보 미제공 등 취소 사유를 설명한다. 일부 상황에서 환불 전 재개가 가능하므로 취소를 항상 영구 종결로 보지 않는다.')
src('S11','Wise','환불 소요 시간','https://wise.com/help/articles/2971476/how-long-do-refunds-take','unspecified','Why has not my refund been processed yet','원래 자금이나 반환 자금이 사업자에게 도착해야 환불을 처리할 수 있다.')
src('S12','PayPal','미국 결제와 요청 상태','https://www.paypal.com/us/cshelp/article/what-does-the-status-of-my-payment-or-money-request-mean-on-my-paypal-account-help668','US','Payment / Money request','같은 상태명도 결제와 돈 요청에서 뜻이 달라진다. 수취 미수락, 완료, 환불과 반환을 구분한다.')
src('S13','PayPal','미수락 결제 취소 조건','https://www.paypal.com/us/cshelp/article/why-is-the-payment-i-sent-pending-or-unclaimed-can-i-cancel-it-help111','US','Unregistered recipient / Recipient preferences','미등록 연락처로 보낸 경우와 수취인의 수락 설정 때문에 대기하는 경우의 직접 취소 가능 여부가 다르다.')
src('S14','PayPal','미국 환불 추적','https://www.paypal.com/us/cshelp/article/where-is-my-refund-help130','US','Refund Tracker / Common refund statuses','환불 개시, 처리, 발송, 금융기관 대기와 완료 표시를 구분한다. 완료 후에도 미수령이면 은행 참조 번호로 확인하도록 안내한다.')
src('S15','Revolut','보안 시스템의 카드 제한','https://help.revolut.com/en-PL/help/card-payments-withdrawals/paying-by-card-issues/declined-card-payments/payment-declined-by-security-system/','PL','If your card is frozen','보안 제한 후 앱에서 거래 확인 절차를 거친다. 거래를 인정하는 경우와 인정하지 않는 경우의 처리 경로가 다르다.')

cases=[]
def case(id,name,domain,definition,selector,include,exclude,critical,aliases,related,question):
 cases.append(dict(id=id,version=VERSION,status='proposed',name=name,domain=domain,definition=definition,selector=selector,includes=include,excludes=exclude,critical_fields=critical,aliases=aliases,related=related,disambiguation_question=question,definition_owner='WGSS',review_status='agent_checked',independent_review=False))
case('C01','사용자가 카드를 잠글 때','카드','카드 이용자가 기존 카드의 이용을 일시 제한하도록 요청하는 상황.',{'object':'card','action':'restrict','initiator':'user','permanence':'temporary'},['앱에서 임시 잠금 선택'],['기관 보안 제한','영구 폐기','계좌 동결'],['recurring','pending','self_restore'],['카드 잠그기','카드를 잠그고 싶어요','카드 잠궈','카드 정지','카드 일시 정지','freeze','lock'],['C02','C03','C04'],'직접 잠그려는 건가요, 이미 금융사가 제한한 건가요?')
case('C02','직접 잠근 카드를 해제할 때','카드','사용자가 요청했던 일시 제한을 해제하는 상황. 추가 제한이 없다는 전제는 별도 확인한다.',{'object':'card','action':'restore','restriction_origin':'user','permanence':'temporary'},['사용자 잠금 해제'],['기관 제한의 임의 해제','교체된 카드 복구'],['self_restore','restriction_origin'],['카드 잠금 해제','unfreeze','defrost','unlock'],['C01','C04'],'직접 잠근 카드인가요, 기관의 보안 제한인가요?')
case('C03','분실·도난 카드를 교체할 때','카드','분실·도난을 이유로 대체 카드를 신청하는 상황. 기존 카드의 영구 차단 여부는 별도 조건이다.',{'object':'card','action':'replace','reason':['lost','stolen']},['분실 또는 도난에 따른 교체'],['단순 잠금','유효기간 갱신','손상만을 이유로 교체'],['old_card_restore','reason'],['카드 분실','재발급','카드 잃어버림','lost','stolen','replace'],['C01','C02'],'일시 잠금이 필요한가요, 새 카드가 필요한가요?')
case('C04','기관의 보안 제한을 해결할 때','카드','금융사가 적용한 카드 제한에 대해 확인·문의 등 해제에 필요한 절차를 밟는 상황.',{'object':'card','action':'resolve','restriction_origin':'provider'},['의심 거래 확인','지원팀 문의'],['사용자가 설정한 잠금의 직접 해제','계좌 전체의 동결'],['self_restore','next_action'],['보안 제한','카드 해제가 안돼요','blocked','카드 정지 해제 안됨'],['C02'],'제한을 건 주체와 요구되는 확인 절차가 확인됐나요?')
case('T01','송금 자금 수령을 기다릴 때','송금','송금 사업자가 처리에 필요한 자금을 아직 받지 못한 상태를 안내한다.',{'object':'transfer','action':'status','milestone':'awaiting_funding'},['송금 신청 후 자금 도착 대기'],['수취인의 입금 대기','사업자가 이미 받은 자금의 처리'],['milestone','payer_debited'],['송금 접수','송금 자금 대기','입금 대기','being processed'],['T02','T05'],'누가 돈을 기다리나요: 송금 사업자인가요, 수취인인가요?')
case('T02','사업자가 송금을 처리할 때','송금','송금 사업자가 검토·환전 등 내부 처리를 진행하는 상태를 안내한다. 자금 수령 여부는 별도 확인한다.',{'object':'transfer','action':'status','milestone':'provider_processing'},['환전 또는 지급수단 검토'],['사업자 자금 수령 대기만 확인','수취 은행에 이미 발송'],['funds_received','milestone'],['송금 처리 중','money received','pending','환전'],['T01','T03'],'어느 주체가 어떤 처리를 진행하고 있나요?')
case('T03','수취 금융기관에 보냈을 때','송금','사업자가 수취 금융기관 또는 지급망으로 자금을 발송한 단계. 수취 계정 반영은 별도 사실이다.',{'object':'transfer','action':'status','milestone':'dispatched'},['수취 은행에 송금 발송'],['수취 계정 입금 확정'],['beneficiary_credit','milestone'],['송금 완료','transfer sent','complete','돈 보냈는데 안옴'],['T04'],'확인된 것은 은행으로 발송인가요, 수취 계정 입금인가요?')
case('T04','수취 계정 반영을 안내할 때','송금','업체가 수취 계정에 자금이 반영됐다고 설명하는 상태. 계정 유형을 별도로 한정한다.',{'object':'transfer','action':'status','milestone':'beneficiary_credited'},['수취 계정 반영을 명시하는 안내'],['발송만 확인','환불 완료','계정 종류를 모르면서 외부 은행 입금으로 단정'],['account_type','beneficiary_credit'],['입금 완료','송금 완료','completed','수취 완료'],['T03'],'수취 계정은 외부 은행 계좌인가요, 서비스 계정인가요?')
case('T05','수취인이 결제를 수락하기 전','송금','수취인의 수락·등록 등 절차가 남아 지급이 완결되지 않은 상황.',{'object':'transfer','action':'status','milestone':'awaiting_acceptance'},['미수락 지급'],['송금 사업자의 자금 수령 대기','돈 요청의 미지급'],['self_cancel','pending_reason'],['미수락','unclaimed','수취 대기','pending'],['T06','T07'],'수취인이 등록되지 않았나요, 수락 설정 때문에 대기하나요?')
case('T06','송금을 취소하려 할 때','송금','송금 취소의 실행 가능 여부와 경로를 확인하거나 취소를 요청하는 상황.',{'object':'transfer','action':'cancel'},['직접 취소','지원팀에 취소 가능 여부 문의','취소 불가 안내'],['취소 결과 확인','환불 도착 확인'],['self_cancel','funds_received','refund_credit'],['송금 취소','cancel transfer','취소 가능','잘못 보낸 돈'],['T05','T07','R01'],'현재 송금 단계와 직접 취소 버튼 유무가 확인됐나요?')
case('T07','취소 결과를 확인할 때','송금','송금의 취소가 보고된 상태를 안내한다. 자금 반환과 재개 가능성은 따로 확인한다.',{'object':'transfer','action':'status','milestone':'cancelled'},['취소 결과 안내','자동 취소 안내'],['취소 요청만 접수','환불 도착 확정'],['refund_credit','resume'],['송금 취소됨','cancelled','canceled','자동 취소'],['T06','R01'],'취소 외에 자금 반환이나 재개 가능성도 확인됐나요?')
case('R01','환불 개시·처리를 기다릴 때','환불','자금 반환이 개시됐거나 진행 중이지만 수취 금융기관으로 발송됐다고 확인되기 전의 상황.',{'object':'refund','action':'status','milestone':'pending'},['반환 자금 도착 대기','환불 처리 중'],['환불 발송 확인','원래 송금 수취인에게 지급'],['refund_credit','reason'],['환불 대기','환불 처리 중','refund initiated','refund processing'],['R02','R03'],'환불은 시작됐나요, 외부 기관으로 이미 보냈나요?')
case('R02','환불을 금융기관으로 보냈을 때','환불','환불 자금을 은행·카드사에 보냈으나 최종 계정 반영은 별도로 확인해야 하는 상황.',{'object':'refund','action':'status','milestone':'dispatched'},['은행·카드사로 환불 발송','금융기관의 환불 처리 대기'],['원래 송금 발송','환불 수령 확정'],['refund_credit','account_type'],['환불 보냄','환불 보냈는데 안옴','환불 보냈는데 안 와요','refund sent','refund pending'],['R01','R03'],'발송과 실제 계정 반영 중 어디까지 확인됐나요?')
case('R03','업체가 환불 완료로 표시할 때','환불','업체가 자금 반환을 완료로 표시하는 상황. 실제 수령 확정과 예외 안내의 강도를 별도로 기록한다.',{'object':'refund','action':'status','milestone':'reported_complete'},['환불 완료 표시'],['취소 완료만 확인','환불 발송만 확인'],['refund_credit','account_type'],['환불 완료','refund completed','returned','denied'],['R02'],'실제 수령을 확인했나요, 업체 완료 표시만 확인했나요?')

facts_meta={
'recurring':('정기결제','unknown'),'pending':('이미 승인된 결제','unknown'),'self_restore':('직접 해제','unknown'),'old_card_restore':('기존 카드 복구','unknown'),'next_action':('다음 행동','unknown'),'beneficiary_credit':('수취 계정 반영','unknown'),'account_type':('반영 대상 계정','unknown'),'self_cancel':('직접 취소','unknown'),'funds_received':('사업자 자금 수령','unknown'),'payer_debited':('송금인 출금','unknown'),'refund_credit':('환불 계정 반영','unknown'),'resume':('취소 후 재개','unknown'),'pending_reason':('대기 이유','unknown'),'reason':('처리 이유','unknown'),'milestone':('확인된 단계','unknown'),'restriction_origin':('제한 주체','unknown')}
records=[]
def rec(id,cid,sid,label,role,meaning,facts,conditions=None,scene=None,locator=None,status='mapped'):
 s=next(s for s in sources if s['id']==sid);c=next((c for c in cases if c['id']==cid),None)
 selectors={k:(v[0] if isinstance(v,list) else v) for k,v in c['selector'].items()} if c else {}
 selectors.update(facts)
 claims=[]
 for k,v in (conditions or {}).items():
  # Known observations require a specific source locator; unknown does not claim evidence of absence.
  claims.append(dict(field=k,value=v['value'] if isinstance(v,dict) else v,state=v.get('state','known') if isinstance(v,dict) else 'known',source_id=sid,locator=locator or s['locator'],basis='explicit' if not isinstance(v,dict) else v.get('basis','explicit')))
 for k in (c['critical_fields'] if c else []):
  if k not in [x['field'] for x in claims]:claims.append(dict(field=k,value=None,state='unknown',source_id=None,locator=None,basis=None))
 records.append(dict(id=id,case_id=cid,mapping_status=status,source_id=sid,provider=s['provider'],market=s['market'],language='en',product_scope='출처에 명시된 상품·흐름에 한정',expression=label,expression_role=role,meaning_ko=meaning,scene=scene or ('action_entry' if role in ['control_label','feature_name'] else 'status'),facts=selectors,claims=claims,source_locator=locator or s['locator'],observed_in_app=False,review_status='agent_checked',independent_review=False,notes=[]))
rec('O01','C01','S01','Freeze card','control_label','사용자가 카드 이용을 일시 제한한다.',{},dict(recurring='blocked',pending='continues',self_restore='allowed'),locator='How to freeze / What happens / Why cannot unfreeze')
rec('O02','C02','S01','Unfreeze card','control_label','사용자가 설정한 카드 잠금을 해제한다.',{},dict(self_restore='allowed',restriction_origin='user'),locator='How to unfreeze / Why cannot unfreeze')
rec('O03','C04','S01',None,'no_ui_label','보안상 제한된 카드는 직접 해제할 수 없어 지원팀에 문의한다.',{},dict(self_restore='blocked',next_action='contact_support'),locator='Why cannot I unfreeze my card')
rec('O04','C01','S02','Quick Lock','feature_name','신규 구매 등을 제한하면서 정기 거래는 유지한다.',{},dict(recurring='allowed',self_restore='allowed'),locator='Credit & Account Protection / Quick Lock')
rec('O05','C02','S02',None,'no_ui_label','찾은 카드의 임시 잠금을 다시 해제할 수 있다고 설명한다.',{},dict(self_restore='allowed',restriction_origin='user'),locator='Quick Lock: found card can be unlocked')
rec('O06','C01','S03','Freeze','control_label','앱에서 카드를 잠그는 조작.',{},dict(self_restore='allowed'))
rec('O07','C02','S03','Defrost','control_label','앱에서 카드 잠금을 푸는 조작.',{},dict(self_restore='allowed',restriction_origin='user'))
rec('O08','C03','S04','Order a new card','control_label','분실·도난 후 카드 정지와 새 카드 주문을 안내한다.',{'reason':'lost'},{'old_card_restore':{'value':None,'state':'unknown'},'reason':'lost_or_stolen'},locator='Lost or damaged cards / Stolen cards')
rec('O09','C03','S05',None,'no_ui_label','교체된 기존 카드는 영구 차단되며 다시 해제할 수 없다.',{'reason':'stolen'},dict(old_card_restore='blocked',reason='lost_or_stolen'),locator='Replacing your card')
rec('O10','C01','S06','Freeze','control_label','미국 도움말에서 카드 정지 조작을 안내한다.',{},dict(self_restore='allowed'),locator='How to freeze a card')
rec('O11','C02','S06','Unfreeze','control_label','미국 도움말에서 카드 해제 조작을 안내한다.',{},dict(self_restore='allowed',restriction_origin='user'),locator='How to freeze a card: unfreeze instructions')
rec('O12','C04','S15',None,'no_ui_label','기관 보안 제한 후 앱에서 의심 거래를 확인하는 절차를 안내한다.',{},dict(self_restore='conditional',next_action='review_transaction'),locator='If your card is frozen')
rec('O13','T01','S07',"Your money's being processed",'status_label','송금 사업자가 송금인의 은행에서 오는 자금을 기다린다.',{},dict(milestone='awaiting_funding',funds_received='not_received'),locator='Understanding your transfer timeline / first stage')
rec('O14','T02','S07','Money received','status_label','사업자가 자금을 받았고 환전을 진행한다.',{},dict(funds_received='received',milestone='provider_processing'),locator='Understanding your transfer timeline / second stage')
rec('O15','T03','S07','Transfer Sent','status_label','수취 은행으로 자금을 보냈고 이후 은행 처리가 남아 있다.',{},dict(milestone='dispatched',beneficiary_credit={'value':'not_established','state':'known'}),locator='Understanding your transfer timeline / third stage')
rec('O16','T03','S08','Complete','status_label','업체의 완료 표시는 수취 은행 발송을 뜻한다. 실제 입금과 같지 않다.',{},dict(milestone='dispatched',beneficiary_credit='not_established'),locator='Opening explanation')
rec('O17','T06','S09','Cancel transfer','control_label','아직 지급하지 않은 송금의 직접 취소.',{'funding_state':'unpaid'},dict(self_cancel='allowed',funds_received='not_received',refund_credit={'state':'not_applicable','value':None}),locator='Transfer set up but not paid')
rec('O18','T06','S09','Cancel transfer','control_label','송금인이 돈을 보냈어도 사업자가 수령하기 전이면 직접 취소할 수 있다.',{'funding_state':'in_transit'},dict(self_cancel='allowed',funds_received='not_received',refund_credit='pending'),locator='Paid but transfer status not updated')
rec('O19','T06','S09',None,'no_ui_label','사업자 처리 중에는 직접 취소가 불가하고 지원팀 취소 시도도 보장되지 않는다.',{'funding_state':'received'},dict(self_cancel='blocked',funds_received='received',next_action='contact_support'),locator='Transfer is being processed',scene='unavailable')
rec('O20','T06','S09',None,'no_ui_label','업체가 완료로 표시한 송금은 이미 수취 금융 시스템에 있어 취소할 수 없다.',{'funding_state':'dispatched'},dict(self_cancel='blocked',next_action='contact_recipient'),locator='Transfer is complete',scene='unavailable')
rec('O21','T07','S10',None,'no_ui_label','기한 내 자금 지급이 없으면 송금이 자동 취소된다.',{'reason':'unpaid'},dict(refund_credit={'state':'not_applicable','value':None},resume='new_transfer_required'),locator='You did not pay for your transfer')
rec('O22','T07','S10',None,'no_ui_label','정보 미제공으로 취소돼도 환불 전 정보를 내면 일부 송금은 재개될 수 있다.',{'reason':'missing_information'},dict(resume='conditional',refund_credit='not_established'),locator='We needed more information from you')
rec('O23','R01','S11',None,'no_ui_label','환불 처리에 앞서 원래 자금이 사업자에게 도착하기를 기다린다.',{},dict(refund_credit='pending',reason='await_original_funds'),locator='Why has not my refund been processed yet')
rec('O24','T02','S12','Pending','status_label','지급수단 검증 등 업체 검토 때문에 결제가 아직 수취인에게 전달되지 않았다.',{},dict(milestone='provider_processing'),locator='Payment / Pending')
rec('O25','T05','S12','Unclaimed','status_label','수취인이 결제를 수락하거나 받지 않은 상태.',{},dict(pending_reason='recipient_not_accepted'),locator='Payment / Unclaimed')
rec('O26','T04','S12','Completed','status_label','업체가 수취 계정에 돈이 들어갔다고 설명한다. 외부 은행 계좌인지는 이 문서만으로 확정하지 않는다.',{},dict(beneficiary_credit='provider_reports_credited',account_type='recipient_account_unspecified'),locator='Payment / Completed')
rec('O27','R03','S12','Returned','status_label','미수락으로 인해 돈이 송금인 계정으로 돌아왔다고 설명한다.',{},dict(refund_credit='provider_reports_credited',account_type='sender_account_unspecified'),locator='Payment / Returned')
rec('O28','T06','S13','Cancel','control_label','확인된 계정에 등록되지 않은 연락처로 보낸 미수락 결제는 직접 취소할 수 있다.',{'pending_reason':'unregistered_recipient'},dict(self_cancel='allowed',pending_reason='unregistered_recipient'),locator='Unregistered email or phone / cancel on web')
rec('O29','T06','S13',None,'no_ui_label','수취인의 수락 설정 때문에 대기하는 결제는 송금인이 직접 취소할 수 없다.',{'pending_reason':'recipient_preferences'},dict(self_cancel='blocked',pending_reason='recipient_preferences'),locator='Recipient does not automatically accept',scene='unavailable')
rec('O30','T07','S13',None,'no_ui_label','미수락 결제는 30일 후 자동 취소되며 원래 지급수단으로 반환 절차가 진행된다.',{'reason':'unclaimed_timeout'},dict(refund_credit='pending'),locator='Automatic cancellation after 30 days')
rec('O31','R01','S14','Refund Initiated','status_label','환불 절차가 개시됐다.',{},dict(refund_credit='pending',reason='refund_initiated'),locator='Refund Tracker / First Step')
rec('O32','R01','S14','Refund Processing','status_label','원래 카드·은행 지급수단으로 환불을 처리 중이다.',{},dict(refund_credit='pending',reason='refund_processing'),locator='Refund Tracker / Second Step')
rec('O33','R02','S14','Refund Sent','status_label','환불을 은행·카드사에 발송했지만 해당 기관의 처리가 남아 있을 수 있다.',{},dict(refund_credit='not_established',account_type='original_card_or_bank'),locator='Refund Tracker / Second Step')
rec('O34','R02','S14','Refund Pending','status_label','환불 자금이 은행·카드사에서 추가 처리를 기다린다.',{},dict(refund_credit='not_established',account_type='original_card_or_bank'),locator='Refund Tracker / Third Step')
rec('O35','R03','S14','Refund Completed','status_label','업체의 마지막 환불 단계 표시. 미수령 시 은행·카드사에 확인하라는 예외가 함께 있다.',{},dict(refund_credit='expected_not_observed',account_type='original_card_or_bank'),locator='Refund Tracker / Third Step')
# A deliberate non-match: same word, different financial object. Do not pollute the transfer taxonomy.
rec('O36',None,'S12','Pending','status_label','돈 요청을 받은 사람이 아직 지급하지 않았다는 뜻. 송금 처리 중과 다르다.',{'object':'money_request','action':'status','milestone':'unpaid'},locator='Money request / Pending',status='out_of_scope')
for r in records:
 if r['id'] in ['O01','O02']:r['notes'].append('사용자가 설정한 일시 정지에 한정. 기관이 별도 보안 제한한 경우 C04를 검토한다.')
 if r['source_id']=='S14':r['product_scope']='은행·카드로 결제한 전액 환불 추적; 혼합 지급수단 제외'
 if r['source_id']=='S02':r['product_scope']='미국 Citi 카드 혜택 페이지에 설명된 일부 카드; 계정별 적용 확인 필요'
 if r['source_id']=='S15':r['product_scope']='폴란드 영어 도움말의 카드 보안 제한 흐름'
 if r['source_id'] in ['S01','S05','S07','S08','S09','S10','S11']:r['notes'].append('국가 미지정 영어 도움말. 영국 정책으로 추정하지 않음.')
 if r['source_id']=='S14':r['notes'].append('환불 추적기의 상태명. 다른 결제 화면의 동일 단어와 합치지 않음.')
 if r['id']=='O16':r['notes'].append('S07의 Transfer Sent와 같은 의미 단계의 별도 표기. 버전·채널이 같다는 근거는 없음.')

write('sources.json',sources);write('cases.json',cases);write('observations.json',records)
write('field-labels.json',{k:v[0] for k,v in facts_meta.items()})
write('manifest.json',dict(version=VERSION,retrieved_at=DATE,scope=['카드 제한·복구','송금 상태·취소','환불 단계'],case_count=len(cases),observation_count=len(records),source_count=len(sources),provider_count=len(set(s['provider'] for s in sources)),ui_capture_count=0,independent_review_count=0,bedrock_status='not_run',release_status='review_candidate',known_gaps=['공식 영어 문서 기반; 실앱 화면은 미관찰','한국어는 WGSS 설명이며 업체의 한국어 UI가 아님','독립 검토자 합의도와 실제 업무 시간 절감은 미측정','법규 준수나 국제 표준 인증을 의미하지 않음']))
# Machine-readable schema; conditions preserve unknown, not-applicable and conflicting separately.
claim={'type':'object','required':['field','value','state','source_id','locator','basis'],'additionalProperties':False,'properties':{'field':{'type':'string'},'value':{'type':['string','null']},'state':{'enum':['known','unknown','not_applicable','conflicting']},'source_id':{'type':['string','null']},'locator':{'type':['string','null']},'basis':{'enum':['explicit','inferred',None]}},'allOf':[{'if':{'properties':{'state':{'const':'known'}}},'then':{'properties':{'value':{'type':'string','minLength':1},'source_id':{'type':'string','minLength':1},'locator':{'type':'string','minLength':1},'basis':{'enum':['explicit','inferred']}}}},{'if':{'properties':{'state':{'enum':['unknown','not_applicable']}}},'then':{'properties':{'value':{'type':'null'}}}}]}
props={k:{'type':'string'} for k in ['id','source_id','provider','market','language','product_scope','meaning_ko','scene','source_locator','review_status']}
props.update(case_id={'type':['string','null']},mapping_status={'enum':['mapped','needs_review','out_of_scope']},expression={'type':['string','null']},expression_role={'enum':['control_label','status_label','feature_name','no_ui_label','api_code']},facts={'type':'object','additionalProperties':{'type':['string','boolean','null']}},claims={'type':'array','items':claim},observed_in_app={'type':'boolean'},independent_review={'type':'boolean'},notes={'type':'array','items':{'type':'string'}})
write('observation.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','title':'WGSS Observation v0.1','type':'array','items':{'type':'object','required':list(props),'additionalProperties':False,'properties':props}})
caseprops={k:{'type':'string'} for k in ['id','version','status','name','domain','definition','disambiguation_question','definition_owner','review_status']}
caseprops.update(selector={'type':'object','minProperties':2,'additionalProperties':{'oneOf':[{'type':'string'},{'type':'array','items':{'type':'string'},'minItems':1}]}},independent_review={'type':'boolean'})
for k in ['includes','excludes','critical_fields','aliases','related']:caseprops[k]={'type':'array','items':{'type':'string'},'minItems':1}
write('case.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','title':'WGSS Case Definition v0.1','type':'array','items':{'type':'object','required':list(caseprops),'additionalProperties':False,'properties':caseprops}})
with (ROOT/'research/independent-review.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['observation_id','source_url','locator','raw_expression','reviewer_case_id','reviewer_scene','reviewer_notes'])
 for r in records:w.writerow([r['id'],next(s['url'] for s in sources if s['id']==r['source_id']),r['source_locator'],r['expression'] or '','','',''])
print(f'{len(cases)} definitions; {len(records)} observations including 1 explicit exclusion; {len(sources)} sources')
