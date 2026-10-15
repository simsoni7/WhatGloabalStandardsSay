import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/bank-gap-candidates-v30-20261012';RUN=R/'research/source-store/bank-gap-final-v30-20261012'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists();orig=read(P/'root-candidates.json');critic=[]
for name in ['bank-gap-candidates-v30-20261012','bank-gap-critic-retries-v30-20261012']:
 for p in (R/'research/source-store'/name).glob('reviews/*/*/proposal.json'):critic+=read(p)['result']['rows']
assert len(critic)==17,len(critic);rows=[];rejects=[]
for b in copy.deepcopy(orig['examples']):
 c=next(x for x in critic if x['id']==b['id']);assert (c['source_id'],c['work_id'],c['native_expression'])==(b['source_id'],b['ui_work_ids'][0],b['expression'])
 if c['status']=='reject':rejects.append(dict(example_id=b['id'],source_id=b['source_id'],work_id=b['ui_work_ids'][0],root_decision='stage_not_admit',reason_ko=c['correction_ko'],automatic_adoption=False));continue
 assert c['status']=='pass',(b['id'],c);rows.append(b)
 for e in ([b['screen_evidence']]+b.get('additional_screen_evidence',[])) if b.get('screen_evidence') else []:
  aid=e['source_asset_id']
  if aid=='hk-empf-invest-app-page-6':e.update(labels=['Fund Rebalancing','Switch out','Switch in','Next'],display_region=dict(bbox_xyxy=[520,298,712,810],original_width=953,original_height=1348,review='root_visual_checked'))
  if aid=='hk-empf-invest-web-page-6':e.update(labels=['Fund Switching Instruction','Fund Rebalancing','Next'],display_region=dict(bbox_xyxy=[85,285,540,1275],original_width=953,original_height=1348,review='root_visual_checked'))
  if aid=='hk-empf-invest-app-page-11':e.update(labels=['Change of Investment Mandate','Next'],display_region=dict(bbox_xyxy=[315,86,503,1056],original_width=953,original_height=1348,review='root_visual_checked'))
 if b['source_id'] in ['S30:hk-trade-form-0','S30:hk-trade-form-1']:b['channel']='공식 PDF 신청양식 · 실행 접수 채널은 별도 확인'
assert {x['example_id'] for x in rejects}=={'BANK-BENCH-211','BANK-BENCH-217','BANK-BENCH-222'}
write(RUN/'root-final-candidates.json',dict(examples=rows,rejected_candidates=rejects,initial_critic_rows=critic,automatic_adoption=False));sources={'S30:'+s['id']:s for s in read(R/'research/source-store/bank-gap-collection-v30-20261012/sources.json')};ws={w['id']:w for w in read(R/'dist/data/bank-ui.json')['works']};write(RUN/'sources.json',list(sources.values()))
for i in range(0,len(rows),5):
 shard=rows[i:i+5];compact=[]
 for b in shard:
  w=ws[b['ui_work_ids'][0]];t=sources[b['source_id']]['text'];qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']];compact.append(dict(candidate=b,actual_definition={k:w[k] for k in ['id','title','definition','completion','includes','excludes']},own_source_contexts=[t[max(0,q['start']-160):q['end']+240] for q in qs]))
 jid='v30-final-critic-'+str(i//5+1);write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model='claude-sonnet-5',instructions='JSON only. Return {"rows":[{"id":...,"source_id":...,"work_id":...,"native_expression":...,"status":"pass"|"correct"|"reject","findings_ko":[...],"correction_ko":...}]}. Every bound candidate exact, never swap similarly named trade-form-0(collection) and trade-form-1(guarantee). pass=all own proof valid with stated limitations; correct=actual change needed, describe it; reject=unsupported equivalence. Qualified official function evidence is allowed, never observed execution/current UI. PDF operative customer request forms support submission not bank issuance/approval; do not infer paper-only submission channel if not explicit. Invoice debts explicitly purchased and funding provided, not arbitrary secured lending. Account opening financial custody distinct login membership. eMPF pension admin operator distinct issuer/trustee; existing assets vs future contributions keep separate branch scopes. Early request Permanent Departure not ordinary65 pension payout. eDDA/DDA permission limit not channel general dailycap. MPF enrolment and HL third-party shareholder voting candidates have been staged, not admitted. Samsung public frontend insurance application template may substantiate described offer-submission wording only; no real personal result or availability/current application version. Employee pension INSURANCE application is offer submission and not pension plan enrolment; source batch-processing after21st means no establishedcontract. Root has seen official guide pixels, you cannot independently see them; do not say root failed to view them or imply installed-app observation. No automatic/human approval.',input=dict(rows=compact),expected_ids=[b['id'] for b in shard],row_key='id',work_ids=list(ws),candidate_bindings={b['id']:dict(source_id=b['source_id'],work_id=b['ui_work_ids'][0],native_expression=b['expression']) for b in shard},max_tokens=15000))
(RUN/'FROZEN').write_text('14 source-reviewed nominations;3 staged rejections.\n');print({'final_nominees':len(rows),'rejections':len(rejects),'jobs':3})
