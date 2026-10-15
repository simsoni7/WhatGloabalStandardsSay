"""Followup original collection under new immutable v33 source identity."""
import concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/account-lending-followup-v33-20261013';C.RUN=RUN
T=[
('al-lombard-contact-follow','lombard-uk','GB','en-GB','https://www.lombard.co.uk/support/contact-us.html','market_evidence'),
('al-lombard-market','lombard-uk','GB','en-GB','https://www.lombard.co.uk/assets/sustainable-finance.html','market_evidence'),
('al-lombard-sitelegal','lombard-uk','GB','en-GB','https://www.lombard.co.uk/toolbar/terms-conditions.html','market_evidence'),
('al-hk-ownerupdate','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/business-information-update','accounts'),
('al-hsbc-futureplanner','hsbc-uk','GB','en-GB','https://www.hsbc.co.uk/wealth/planning/future-planner/','servicing'),
('al-kakao-mobileterms','kakao','KR','ko','https://www.kakaobank.com/view/corp/policy/service','identity'),
('al-nw-terms','natwest-uk','GB','en-GB','https://www.natwest.com/content/dam/natwest/personal/current-accounts/documents/your-current-account-terms.pdf.coredownload.pdf','accounts'),
('al-starling-webterms','starling-uk','GB','en-GB','https://www.starlingbank.com/docs/legal/terms/Online-Banking-Terms.pdf','identity')]
if __name__=='__main__':
 assert not(RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:S=list(pool.map(C.fetch,T))
 C.write(RUN/'sources.json',S);(RUN/'FROZEN').write_text('Frozen originals. No automatic admission.\n');print([(s['id'],s['state'],len(s.get('text','')))for s in S])
