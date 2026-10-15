"""One-time own-source access/payments gap collection; HTTP success is not admission."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/access-collection-v32-20261013';C.RUN=RUN
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 T=[
 ('access-monzo-switch','monzo','GB','en-GB','https://monzo.com/help/switching-to-monzo/cass-full-switch-what','payments'),
 ('access-monzo-joint','monzo','GB','en-GB','https://monzo.com/current-account/joint-account','accounts'),
 ('access-monzo-joint-ownership','monzo','GB','en-GB','https://monzo.com/help/joint-accounts/what-joint-account','accounts'),
 ('access-monzo-cash','monzo','GB','en-GB','https://monzo.com/help/payments-getting-started/cash-deposit-how-to','payments'),
 ('access-monzo-logout','monzo','GB','en-GB','https://monzo.com/help/app-help/logging-out','identity'),
 ('access-monzo-data','monzo','GB','en-GB','https://monzo.com/help/legal-stuff/data-subject-access-request-web','identity'),
 ('access-monzo-request','monzo','GB','en-GB','https://monzo.com/help/monzo-with-friends/monzo-me-how-to','payments'),
 ('access-monzo-ddguarantee','monzo','GB','en-GB','https://monzo.com/help/payments-getting-started/direct-debit-guarantee-what/','payments'),
 ('access-monzo-ddfraud','monzo','GB','en-GB','https://monzo.com/learn/money-safety/what-is-direct-debit-fraud','payments'),
 ('access-monzo-orderedit','monzo','GB','en-GB','https://monzo.com/help/payments-getting-started/bb-web-edit-cancel-st-order','payments'),
 ('access-monzo-otherprivacy','monzo','GB','en-GB','https://monzo.com/legal/files/plus/monzo-plus-other-accounts-in-monzo-privacy-notice/version-1-1.pdf','identity'),
 ('access-hk-accounts','hsbc-hk','HK','en','https://www.hsbc.com.hk/help/faq/accounts/','accounts'),
 ('access-uk-mandate','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/life-events/third-party-mandate/','identity'),
 ('access-uk-thirdfaq','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/third-party-access/faq/','identity'),
 ('access-uk-forms','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/customer-forms/','accounts'),
 ('access-uk-fraudreply','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/security-centre/received-a-text/','servicing'),
 ('access-uk-name','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/banking-made-easy/update-your-details/change-name/','identity'),
 ('access-uk-esign','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/electronic-signatures/','identity'),
 ('access-kakao-moim','kakaobank','KR','ko','https://kakaobank.com/products/moim?scrollToSection=ai-moim','accounts')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:S=list(p.map(C.fetch,T))
 extra=[]
 for sid,needle,newid,family in [('access-uk-forms','Personal representatives closure','access-uk-estateform','accounts'),('access-uk-forms','Credit Card Direct Debit form, from HSBC','access-uk-ddform','payments'),('access-uk-mandate','Third party mandate form','access-uk-mandateform','identity')]:
  src=next(s for s in S if s['id']==sid);ls=[l for l in src.get('links',[]) if needle.lower() in l['label'].lower() and '.pdf' in l['url']]
  if ls:extra.append((newid,src['provider_id'],src['country'],src['language'],ls[0]['url'],family))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:S+=list(p.map(C.fetch,extra))
 C.write(RUN/'sources.json',S);C.write(RUN/'baseline.json',C.read(R/'dist/data/bank-ui.json'));(RUN/'FROZEN').write_text('Originals frozen. No automated benchmark or observed-UI admission.\n');print(json.dumps({'sources':len(S),'fetched':sum(s['state']=='fetched_pending_review' for s in S),'results':[(s['id'],s['state'],len(s.get('text',''))) for s in S]}))
