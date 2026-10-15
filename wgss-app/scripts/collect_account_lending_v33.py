"""Frozen own-publisher account/lending v33 research; no automatic admission."""
import concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/account-lending-collection-v33-20261013';C.RUN=RUN
T=[
('al-nw-remove','natwest-uk','GB','en-GB','https://www.natwest.com/current-accounts/existing-customers/account-signatories.html','accounts'),
('al-nw-removalfaq','natwest-uk','GB','en-GB','https://www.natwest.com/support-centre/general-banking-information/general/changing-parties-to-an-account.html','accounts'),
('al-nw-poaremove','natwest-uk','GB','en-GB','https://www.natwest.com/support-centre/general-banking-information/general/removal-of-power-of-attorney-poa.html','identity'),
('al-nw-poa','natwest-uk','GB','en-GB','https://www.natwest.com/life-moments/caring-for-vulnerable-relatives/guide-to-power-of-attorney.html','identity'),
('al-hsbc-poafaq','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/third-party-access/faq/','identity'),
('al-hsbc-register','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/register/','identity'),
('al-hsbc-dispute','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/card-support/dispute-transaction/','servicing'),
('al-hsbc-disputetool','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/help/disputes-tool/','servicing'),
('al-nw-loandate','natwest-uk','GB','en-GB','https://www.natwest.com/support-centre/general-banking-information/general/how-do-i-change-my-loan-payment-date.html','lending'),
('al-nw-loanmanage','natwest-uk','GB','en-GB','https://www.natwest.com/loans/existing-customers.html','lending'),
('al-nw-termamend','natwest-uk','GB','en-GB','https://www.natwest.com/mortgages/existing-customers/term-amendment.html','lending'),
('al-lombard-lease','lombard-uk','GB','en-GB','https://www.lombard.co.uk/finance-options/finance-options-lease.html','lending'),
('al-lombard-legal','lombard-uk','GB','en-GB','https://www.lombard.co.uk/support/frequently-asked-questions/legal-faqs.html','lending'),
('al-lombard-terms','lombard-uk','GB','en-GB','https://www.lombard.co.uk/terms.html','lending'),
('al-lombard-contact','lombard-uk','GB','en-GB','https://www.lombard.co.uk/contact-us.html','market_evidence'),
('al-starling-poa','starling-uk','GB','en-GB','https://www.starlingbank.com/customer-support/third-party-account-access/','identity'),
('al-starling-legal','starling-uk','GB','en-GB','https://www.starlingbank.com/legal/','servicing'),
('al-kakao-moim','kakao','KR','ko','https://kakaobank.com/products/moim?scrollToSection=ai-moim','accounts'),
('al-hk-tdterms','hsbc-hk','HK','en','https://www.hsbc.com.hk/content/dam/hsbc/hk/docs/accounts/time-deposit-terms.pdf','savings'),
('al-hk-bizterms','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/-/media/media/hong-kong/pdfs/form-download-centre/general-terms-and-conditions-commercial-banking-effective-from-13-feb-2026.pdf','servicing')]
if __name__=='__main__':
 assert not(RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:S=list(pool.map(C.fetch,T))
 C.write(RUN/'sources.json',S);C.write(RUN/'baseline.json',C.read(R/'dist/data/bank-ui.json'));(RUN/'FROZEN').write_text('Frozen originals and assigned scope. No admission.\n')
 print([(s['id'],s['state'],len(s.get('text','')))for s in S])
