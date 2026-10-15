"""Current issuer/trustee membershipresult counterexamples, not pendingapplications."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-mpf-sources-v33-20261013';base.RUN=RUN
T=[('ip33-bea-membership','bea-mpf-hk','HK','en','https://www.hkbea.com/html/en/bea-mpf-ksid-ispage.html','protection'),('ip33-bea-brochure','bea-mpf-hk','HK','en','https://www.hkbea.com/pdf/MPF-Scheme-Brochure/sb_is_eng.pdf','protection'),('ip33-aia-mpf-journey','aia-mpf-hk','HK','en','https://www.aia.com.hk/en/products/mpf/mpf-journey-employer','protection')]
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(base.fetch,T))
 base.write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('Currentprimaryown MPFissuer/membershipresult documents; role distinctfromAIAinsurer.\n');print({'sources':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]})
