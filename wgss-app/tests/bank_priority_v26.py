# Historical v1/v28 oracle retained; current v1.1 is independently checked in bank_expansion_v29.py.
"""Guard new country gaps, own ranges, same-example proofs and multi-screen provenance."""
import csv,hashlib,json
from collections import Counter
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v28.json');ledger=read(R/'data/bank-ui-collection-v26-decisions.json');private={b['id']:b for b in read(R/'data/bank-ui-benchmark-dispositions.json')['examples']};checks=[]
def check(name,ok):assert ok,name;checks.append(name)
rows=[b for b in d['benchmarks'] if b['source_id'].startswith(('V26:','V26S:'))];sources={batch['prefix']+':'+s['id']:s for batch in ledger['source_batches'] for s in read(R/batch['manifest'])};images={im['sha256']:im for im in read(R/'research/source-store/bank-priority-v26-20261011/guide-images.json')}
check('214 denominator unchanged, only 17 explicit admissions',len(d['works'])==214 and not ledger['scope_change'] and len(rows)==17 and {b['id'] for b in rows}=={x['example_id'] for x in ledger['admitted_examples']})
check('root disposition of all 19 candidates and 17 final critiques',len(ledger['row_dispositions'])==19 and sum(x['root_decision']=='reject' for x in ledger['row_dispositions'])==2 and len(ledger['final_root_dispositions'])==17 and all(not x['automatic_adoption'] for x in ledger['final_root_dispositions']))
check('country coverage increases without multiplying work IDs',d['priority_collection']=={'works':32,'cells':96,'reviewed_cells':96,'works_with_examples':32,'linked_cells':78,'screen_cells':16,'flow_and_condition_cells':39})
check('publication totals distinguish examples, works, guides and observations',d['benchmark_counts']['examples']==166 and d['benchmark_counts']['works_with_function_documents']==85 and d['benchmark_counts']['official_guide_screens']==28 and d['benchmark_counts']['observed_app_captures']==0 and d['benchmark_counts']['verified_app_ui_versions']==0)
for pub in rows:
 b=private[pub['id']];s=sources[b['source_id']];t=(R/s['snapshot_path']/'normalized.txt').read_text();raw=(R/s['snapshot_path']/'source.html').read_bytes()
 assert hashlib.sha256(t.encode()).hexdigest()==b['text_sha256'] and hashlib.sha256(raw).hexdigest()==b['raw_sha256']
 all_images=([b['screen_evidence']]+b.get('additional_screen_evidence',[])) if b.get('screen_evidence') else []
 qs=[b['proof'],b['function_proof']]+b['flow_step_proofs']+[x['proof'] for x in b['policy_claims']]
 for q in qs:
  if q['kind']=='normalized_text_character_range':assert t[q['start']:q['end']]==q['excerpt']
  else:
   e=next(e for e in all_images if e['image_sha256']==q['image_sha256']);im=Image.open(R/'dist'/e['image_path']);x0,y0,x1,y1=q['bbox_xyxy'];assert 0<=x0<x1<=im.width and 0<=y0<y1<=im.height and q['label'] in e['labels'] and q['review']=='root_visual_checked'
 assert len(b['flow_steps'])==len(b['flow_step_proofs']) and not b['observed_app_screen'] and b['verified_ui_version'] is None
 for e in all_images:
  im=images[e['image_sha256']];assert im['source_id']==b['source_id'] and any(i['url']==e['asset_url'] for i in s['images'])
  assert hashlib.sha256((R/im['private_path']).read_bytes()).hexdigest()==hashlib.sha256((R/'dist'/e['image_path']).read_bytes()).hexdigest()==e['image_sha256']
  assert e['visual_review']=='root_visual_checked' and not e['independent_human_review'] and e['source_version'] is None
  if e.get('display_region'):
   r=e['display_region'];im=Image.open(R/'dist'/e['image_path']);assert (r['original_width'],r['original_height'])==im.size and r['review']=='root_visual_checked'

 if b['provider_id']=='monzo':q=b['market_proof']['proof'];assert t[q['start']:q['end']]=='United Kingdom' and b['country']=='GB'
check('every label, result, step, condition and guide belongs to own frozen source',True)
b=private['BANK-BENCH-097'];t=sources[b['source_id']]['text'];start=t.index('How to catch up on missed payments with an Easy Bank Transfer');check('card debt steps all from missed-payment example, not early-payment section',all(q['start']>=start for q in b['flow_step_proofs']))
b=private['BANK-BENCH-106'];t=sources[b['source_id']]['text'];start=t.index('如何透過HSBC HK App啟動我的滙豐Mastercard®扣賬卡？');end=t.index('如何透過HSBC HK App為我的滙豐Mastercard®扣賬卡設定私人密碼？');check('activation proof all from Mastercard section, not UnionPay card section',start<=b['function_proof']['start']<end and all(start<=q['start']<end for q in b['flow_step_proofs']))
check('source contradiction kept unresolved with both own clauses',private['BANK-BENCH-108']['source_conflicts'][0]['resolution']=='unresolved_provider_confirmation_required' and len(private['BANK-BENCH-108']['source_conflicts'][0]['proofs'])==2 and '만 17세 미만' in private['BANK-BENCH-108']['conditions'])
check('entry-only document menu and repayment source setup not admitted',not any(b['id'] in ['BANK-BENCH-096','BANK-BENCH-111'] for b in d['benchmarks']))
check('balance uses native available-balance field, not deposit-capacity prose',private['BANK-BENCH-109']['expression']=='출금가능금액' and private['BANK-BENCH-109']['proof']['kind']=='official_image_region')
check('loan index, loan marketing and binding change not patched as submissions',not any(b['source_id'] in ['V26:uk-monzo-loan-index','V26:uk-monzo-loans','V26S:uk-monzo-date','V26S:uk-monzo-limit'] for b in rows))
check('all galleries counted by unique images, never by example copies',len({e['image_sha256'] for b in rows if b.get('screen_evidence') for e in [b['screen_evidence']]+b.get('additional_screen_evidence',[])})==12)
check('15 completed Bedrock jobs have prompt provenance and actual gateway model names',len(ledger['model_runs'])==15 and {j['model'] for j in ledger['model_runs']}=={'claude-opus-5','claude-sonnet-5'} and all(j['prompt_sha256'] and j['usage'] for j in ledger['model_runs']))
# Full publisher quotations are retained privately only, including nested conflict proofs.
def no_quotes(x):
 if isinstance(x,dict):return ('excerpt' not in x if x.get('kind')=='normalized_text_character_range' else True) and all(no_quotes(v) for v in x.values())
 if isinstance(x,list):return all(no_quotes(v) for v in x)
 return True
check('public data strips all long source excerpts recursively',no_quotes(d['benchmarks']))
print(json.dumps({'bank_priority_v26':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
