"""Public time-deposit framework and verified business owner update followups."""
import concurrent.futures
from pathlib import Path
import collect_bank_gaps_v30 as C
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/account-lending-final-sources-v33-20261013';C.RUN=RUN
T=[('al-ncb-faq','ncb-hk','HK','en','https://www.ncb.com.hk/nanyang_bank/faq/?lang=enUS','savings'),('al-ncb-mobileguide','ncb-hk','HK','en','https://www.ncb.com.hk/nanyang_bank/resource/person_phoe_bank_serve_guide_en.pdf','savings'),('al-ncb-mobile','ncb-hk','HK','en','https://www.ncb.com.hk/nanyang_bank/eng/html/121112.html','savings'),('al-hk-ownerprocess','hsbc-hk','HK','en','https://www.business.hsbc.com.hk/en-gb/products/online-business-information-update','accounts')]
if __name__=='__main__':
 assert not(RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:S=list(pool.map(C.fetch,T))
 C.write(RUN/'sources.json',S);(RUN/'FROZEN').write_text('Originals frozen. No automated admission.\n');print([(s['id'],s['state'],len(s.get('text','')))for s in S])
