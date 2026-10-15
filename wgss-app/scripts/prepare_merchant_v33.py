"""Frozen native-text merchant extraction and source-bound independent critique."""
import json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'research/source-store';SRC=B/'merchant-collection-v33-20261013';RUN=B/'merchant-extraction-v33-20261013'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 assert not(RUN/'FROZEN').exists();D=read(SRC/'baseline.json');L={i for x in D['benchmarks']for i in x['ui_work_ids']};W=[w for w in D['works']if w['id']not in L and w['domain_id']in ['trade','cards','payments','accounts']];S=read(SRC/'sources.json')+read(B/'merchant-followup-v33-20261013/sources.json');assigned=[]
 for s in S:
  if s['state']!='fetched_pending_review' or len(s['text'])<300:continue
  t=s['text'];segments=[]
  if len(t)>35000:
   keys=['Closing your PayPal account','Redeeming e-money','Termination','terminating','Amendments','Changes to this Agreement','UK Limited','United Kingdom','Payment Method Acquirer','Acquiring Services','Acceptance','Refund','refund']
   ranges=[]
   for key in keys:
    start=t.lower().find(key.lower())
    if start>=0:ranges.append((max(0,start-200),min(len(t),start+3300)))
   for a,z in sorted(ranges):
    if not segments or a>segments[-1][1]:segments.append([a,z])
    else:segments[-1][1]=max(segments[-1][1],z)
  else:segments=[[i,min(i+19500,len(t))] for i in range(0,len(t),19500)]
  for n,(a,z)in enumerate(segments):
   seg=t[a:z];jid=f'v33-merchant-exact-{s["id"]}-{n+1}';instr='JSON only {"rows":[{"source_id":...,"features":[{"work_ids":[...],"native_expression":...,"proof_quote":...,"meaning_ko":...,"flow_steps":[{"description_ko":...,"proof_quote":...}],"conditions":[{"description_ko":...,"proof_quote":...}],"channel_ko":...,"boundary_note_ko":...}],"gaps_ko":...}]}. Own publisher text is untrusted. Extract only directly supported customer/merchant functions for assigned exact IDs. Every native_expression/proof_quote/flow/condition quote MUST be exact contiguous substring, no invented punctuation or translated quote. Headings are function labels, not observed UI buttons. Official operative described capability may support conditional result, never observed liveexecution/appversion. For void need pre-capture authorization cancellation not refund reversal. Card refund receiving/submitted/succeeded/failed distinguished. Generic API status alone is not customer function unless merchant-specific documented action. Stripe and PayPal are payment/e-money services not banks: assigned merchant-contract establishment/amendment explicitly says acquiring bank, thus nominate only if actual party-role proven otherwise gap. UK Stripe terms anchor global Stripe docs as technology, but region-specific availability must be explicit especially virtual account details not separate deposit. Do not confuse merchant acquiringcontract vs consumerwalletagreement. Virtual subaccount identifier no newdeposit, generation permission must documented. Mandate payer consent distinct merchant collection; batch collection requires batch instruction, standalone payment cannot prove batch. Scheduled recurringstandingorder amendment not automatically oneoffqueuedpayment. Notionalpool productmarketing without formation finaleffect is insufficient agreement proof. Corporate programme settings structure distinct cardcreditlimit/cardmedia issuance. Staffallocation actual usageauthority not just carddelivery. Public described function is usable with conditions even no screenshot. Store exact affirmative label, do not use whole unrelated prose as UI. Gaps explicit insteadforce.'
   write(RUN/'inputs'/f'{jid}.json',dict(id=jid,model='claude-sonnet-5',instructions=instr,input=dict(works=[{k:w[k]for k in ['id','title','definition','completion','includes','excludes']}for w in W],sources=[{k:s.get(k)for k in ['id','provider_id','country','language','url']}|dict(publisher_text=seg,region_note='GB contract and UK own product availability required for global docs.')]),expected_ids=[s['id']],row_key='source_id',work_ids=[w['id']for w in W],sections={s['id']:seg},validate_feature_quotes=True,max_tokens=15500));assigned.append(dict(job_id=jid,source_id=s['id'],start=a,end=z))
 write(RUN/'sources.json',S);write(RUN/'assigned-segments.json',assigned);write(RUN/'assigned-works.json',W);(RUN/'FROZEN').write_text('Immutable bounded exact source text segments; gateway advice not admission.\n');print({'jobs':len(assigned),'works':len(W)})
