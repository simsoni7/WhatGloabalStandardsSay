"""Review catalogue invariants and selected semantic boundary corrections."""
import collections,csv,json,sqlite3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'dist/data/operations.json').read_text());audit=json.loads((R/'dist/data/operation-audit.json').read_text())
works=d['works'];by={w['id']:w for w in works};mapping=audit['input_to_work_ids'];checks=[]
def check(label,ok):assert ok,label;checks.append(label)
check('registered total equals unique actual definitions',len(works)==len(by)==d['audit']['registered_count'])
check('three layer counts partition definitions',dict(collections.Counter(w['layer'] for w in works))==d['audit']['counts_by_layer'])
check('editing states do not masquerade as MECE approval',d['audit']['mece_approved_count']==0 and not d['audit']['source_scope_ce_accepted'] and not any(w['mece_approved'] for w in works))
check('provider collection gate remains closed',d['audit']['new_provider_collection_allowed'] is False)
initial_decisions=['정의 정리 제안','병합','결과 분리','집계 제외','판정 보류']
check('all original candidates have an explicit disposition',len(mapping)==503 and len([x for x in audit['decisions'] if x['decision'] in initial_decisions])==503)
check('all candidate and reference mapping targets exist',all(t in by for ts in mapping.values() for t in ts) and all(t in by for r in d['omission_matrix'] for t in r['work_ids']))
check('every nearest-boundary link resolves',all(t in by for w in works for t in w['boundary']['related_ids']))
check('every listed row has direct unit boundary and reference fields',all(w['actor_role'] and w['object_key'] and w['outcome_key'] and w['definition'] and w['includes'] and w['excludes'] and w['boundary']['distinction'] for w in works))
check('normalised keys have no compound slash or whitespace',all(not any(c in (w[k] or '') for c in ' /') for w in works for k in ['actor_role','object_key','outcome_key','discriminator']))
check('reference manifest 927 IDs preserved',len(d['omission_matrix'])==len({r['id'] for r in d['omission_matrix']})==927)
check('reference proposals never silently approved',not any(r['editorial_approved'] for r in d['omission_matrix']))
actual_tuples=[tuple(w[k] for k in ['actor_role','object_key','outcome_key','discriminator']) for w in works]
check('no merge cycles orphan targets or identical normalised tuple',not d['audit']['compiler_blockers'] and len(actual_tuples)==len(set(actual_tuples)))
def find(batch,n):return next(k for k in mapping if k.startswith(batch+'-') and int(k.rsplit('-',1)[1])==n)
def m(batch,n):return mapping[find(batch,n)]
check('cash and payment standing instructions share one definition',m('accounts-deposits',43)==m('payments-cards',19))
check('card repayments reuse debt payment rather than product clone',m('payments-cards',46)==m('lending-trade',18)==m('lending-trade',19))
check('bank draft split resolves two independent outcomes',len(m('payments-cards',11))==2 and m('payments-cards',1)[0] in m('payments-cards',11) and m('institution-processing',26)[0] in m('payments-cards',11))
check('refund alias targets refund only rather than void',len(m('payments-cards',61))==1 and m('payments-cards',61)[0] in m('payments-cards',45) and '환불' in by[m('payments-cards',61)[0]]['title'])
check('balance and history are separate objects across product contexts',len(m('payments-cards',64))==2 and m('payments-cards',64)==m('lending-trade',65))
check('compound holder input preserves protection and election as distinct results',set(m('institution-processing',57))=={'WGSS-86C3A7BB3CD6','WGSS-B076A6656970'} and m('investments-custody',35)==['WGSS-86C3A7BB3CD6'] and m('investments-custody',35)!=m('investments-custody',28))
check('backend bookkeeping and schedule engine excluded',all(not m(b,n) for b,n in [('institution-processing',25),('institution-processing',76),('institution-processing',86),('investments-custody',7),('payments-cards',63)]))
future=by[m('investments-custody',47)[0]]
check('generic derivative parent narrowed to sourced future obligation',future['object_key']=='future_contract' and future['discriminator']=='bilateral_future_delivery_obligation_not_option_right' and any('옵션' in x for x in future['excludes']))
check('financial provider roles do not appear in the customer partition',all(w['layer']=='institution' for w in works if w['actor_role'] in ['vasp','islamic_financial_institution','staking_service_provider','issuing_bank']))
check('single permission and saved preference retain separate outcomes',by['WGSS-B9749BC4EE73']['object_key']!=by['WGSS-2BD7038B026C']['object_key'])
check('named source-scope and semantic audits cover all original inputs',d['audit']['closure_summary']['bian_total_reviewed']==927 and d['audit']['closure_summary']['semantic_definitions_reviewed']==377 and d['audit']['closure_summary']['source_gap_definitions_reviewed']==29)
check('new card loss notice is distinct from temporary locking',any(w['object_key']=='payment_device_loss_notice' and 'WGSS-FE439C56F389' in w['boundary']['related_ids'] for w in works))
check('compound repo and collateral parents do not inflate count',not {'WGSS-EB2135D783F7','WGSS-6FF7D1580755','WGSS-9C5BC9831A6C'}&set(by))
aml=m('institution-processing',98)
check('AML sanctions parent splits into two independently sourced results',len(aml)==2 and {by[i]['object_key'] for i in aml}=={'unusual_activity_investigation_finding','sanctions_screening_alert'} and all(by[i]['refs'] and by[i]['layer']=='institution' for i in aml) and 'WGSS-42A60B60852D' not in by)
check('bond counsel responsibility is confined to municipal opinion preparation',by['WGSS-BD200449B25E']['actor_role']=='bond_counsel' and by['WGSS-BD200449B25E']['layer']=='support' and by['WGSS-BD200449B25E']['object_key']=='municipal_bond_legal_opinion')
check('scheme-specific purification keeps source responsibility and conditions',by['WGSS-22752E8D4759']['actor_role']=='islamic_fund_manager' and any('말레이시아' in s for s in by['WGSS-22752E8D4759']['applicability_conditions']))
check('collateral giver duplicate merges without deleting valuation responsibility',m('investments-custody',43)[0]=='WGSS-3EBB4AA4749F' and 'WGSS-1C46D6607F57' not in by and 'WGSS-DC21011E8515' in by)
redemption=by['WGSS-99C71CF7F867']
check('token redemption confined to legally redeemable monetary claim',redemption['object_key']=='e_money_token_monetary_claim' and any('상환청구권이 없는' in s for s in redemption['applicability_conditions']) and 'WGSS-ADD-555BDFC74CD7' in redemption['boundary']['related_ids'])
with (R/'dist/data/operations.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
check('CSV exposes every definition exactly once',{r['id'] for r in rows}==set(by) and len(rows)==len(works))
with sqlite3.connect(R/'data/operations-review.sqlite') as db:
 check('separate review database reconciles without orphans',db.execute('SELECT COUNT(*) FROM operation').fetchone()[0]==len(works) and db.execute('SELECT COUNT(*) FROM candidate').fetchone()[0]==503 and not db.execute('PRAGMA foreign_key_check').fetchall())
 check('source additions remain independently counted and traceable',db.execute('SELECT COUNT(*) FROM source_addition').fetchone()[0]==d['audit']['source_grounded_addition_count'])
print(json.dumps({'status':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
