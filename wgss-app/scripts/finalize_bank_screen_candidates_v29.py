# One-time v29 recorder/preparer. Already executed; frozen files must not be overwritten.
import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/bank-screen-candidates-v29-20261012';RUN=R/'research/source-store/bank-screen-final-v29-20261012'
def read(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();rows=copy.deepcopy(read(P/'root-candidates.json')['examples']);critics=[r for p in P.glob('reviews/*/*/proposal.json') for r in read(p)['result']['rows']];assert len(critics)==22
changes=[]
for b in rows:
 c=next(x for x in critics if x['id']==b['id']);assert c['source_id']==b['source_id'] and c['work_id']==b['ui_work_ids'][0] and c['native_expression']==b['expression'];assert c['status'] in ['pass','correct']
 if c['status']=='correct':
  assert b['id']=='BANK-BENCH-201';changes.append(dict(id=b['id'],field='meaning',before=b['meaning'],after='타 기관 연금을 HL로 이관하도록 온라인 이관 지시를 제출합니다. 전화·우편 자료 요청과 후속 드로다운 신청은 별도이며 실제 이관 완료의 관찰 사례가 아닙니다.',reason_ko='상담·서류 요청을 이관 지시와 묶지 않도록 정정'));b['meaning']=changes[-1]['after']
 for e in ([b['screen_evidence']]+b.get('additional_screen_evidence',[])) if b.get('screen_evidence') else []:
  if e['source_asset_id']=='shinhan-img-10':
   e['labels']=['최근 입출금','전체내역보기'];e['display_region']=dict(bbox_xyxy=[0,1280,300,1630],original_width=300,original_height=1982,review='root_visual_checked')
  if e['source_asset_id']=='shinhan-img-28':e['labels']=['보내기취소']
  if e['source_asset_id']=='gb-fidelity-pdf-1-page-2':e['display_region']=dict(bbox_xyxy=[110,350,405,520],original_width=953,original_height=1348,review='root_visual_checked')
  if e['source_asset_id']=='gb-fidelity-pdf-6-page-2':e['display_region']=dict(bbox_xyxy=[110,82,550,329],original_width=953,original_height=1348,review='root_visual_checked')
 # Expose guide dates and keep source availability separate from execution.
 b['function_observation']='publisher_described_function';b['current_ui_verified']=False
write(RUN/'root-final-candidates.json',dict(examples=rows,root_corrections=changes,initial_critic_rows=critics,automatic_adoption=False));sources={'S29:'+s['id']:s for s in read(R/'research/source-store/bank-screen-expansion-v29-20261012/sources.json')};sources.update({'V24:'+s['id']:s for s in read(R/'research/source-store/bank-collection-v24-20261011/sources.json')});sources.update({'A28:'+s['id']:s for s in read(R/'research/source-store/bank-breadth-additional-v28-20261012/sources.json')});ws={w['id']:w for w in read(R/'data/bank-ui-root-decisions.json')['catalogue']['works']};write(RUN/'sources.json',list(sources.values()))
for i in range(0,len(rows),8):
 shard=rows[i:i+8];compact=[]
 for b in shard:
  w=ws[b['ui_work_ids'][0]];qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[c['proof'] for c in b['policy_claims']];t=sources[b['source_id']]['text'];compact.append(dict(candidate=b,actual_definition={k:w[k] for k in ['id','title','definition','completion','includes','excludes']},own_context=[t[max(0,q['start']-100):q['end']+130] for q in qs if q['kind']=='normalized_text_character_range']))
 jid=f'v29-final-critic-{i//8+1}';write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model='claude-sonnet-5',instructions='JSON only. EVERY exact candidate binding. Return {"rows":[{"id":...,"source_id":...,"work_id":...,"native_expression":...,"status":"pass"|"correct"|"reject","findings_ko":[...],"correction_ko":...}]}. Financial actor/object/result equivalence, exact proof and explicitly source-specific qualifications. Published guide screenshots are editorial functional references, never directly observed execution/current application version. Root-checked PDF raster page supports insurance benefits and outpatient claims, you cannot independently see pixels. No inferred labels/stages/country/version. Insurer vs bank publisher distinct; HSBC Life HealthyLife app guide Jan2025, despite stale Benefits+ metadata title. Bank-account restriction release review request not actual release. Business daily channel profile limit not per-account/credit/user permission limit. Forgotten LOGIN password reset restoring lost access not voluntary password change. Brokerage cash payout is transfer instruction, not physical cash. Pension drawdown benefit start not early payout; transfer instruction not phone document enquiry. Existing policy function descriptions valid at document level only, no execution channels inferred. Flag any unsupported step/condition. No automatic admission.',input=dict(rows=compact),expected_ids=[b['id'] for b in shard],row_key='id',work_ids=list(ws),candidate_bindings={b['id']:dict(source_id=b['source_id'],work_id=b['ui_work_ids'][0],native_expression=b['expression']) for b in shard},max_tokens=14000))
(RUN/'FROZEN').write_text('Corrected22 final bindings, original input unchanged.\n');print({'final_candidates':22,'jobs':3})
