import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];SRC=R/'research/source-store/bank-gap-extraction-v30-20261012';RUN=R/'research/source-store/bank-gap-retries2-v30-20261012'
def read(p):return json.loads(p.read_text())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not (RUN/'FROZEN').exists()
for old,new in [('v30-exact-hk-empf-member-faq-3','v30-retry-member-native'),('v30-exact-kr-samsung-restoration-1','v30-retry-insurance-native')]:
 j=read(SRC/'inputs'/f'{old}.json');j['id']=new;j['instructions']+=' Prior whole response failed exact-label validation. ALL native_expression/proof_quote MUST be literal substrings; choose short source-native "Early Retirement" rather than invented "Claim MPF Benefits – Early Retirement" and "Transfer MPF" rather than blended scheme title. For Samsung choose native heading "부활청약제도 안내" if verbatim. Source contains unusual doubled spaces, ZWSPs and punctuation; avoid long fragile snippets; short complete clauses better than ellipsis. Do not change meanings or conflate normal retirement and early payout. Keep assigned section intact.';write(RUN/'inputs'/f'{new}.json',j)
write(RUN/'sources.json',read(SRC/'sources.json'));(RUN/'FROZEN').write_text('Two exact native-label retries. Originals and all failed attempts retained.\n')
