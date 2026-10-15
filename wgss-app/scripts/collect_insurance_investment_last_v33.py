"""Last missing personalisedquote/proxy ownsource counterexamples."""
import concurrent.futures,json
from pathlib import Path
import collect_bank_gaps_v30 as base
R=Path(__file__).resolve().parents[1];RUN=R/'research/source-store/insurance-investment-last-sources-v33-20261013';base.RUN=RUN
T=[('ip33-aviva-quoteapp','aviva-uk','GB','en-GB','https://www.aviva.com/newsroom/news-and-research-overview/news-releases/2026/03/aviva-launches-insurance-app-on-chatgpt/','protection'),('ip33-ii-agm-guide','ii-uk','GB','en-GB','https://www.ii.co.uk/analysis-commentary/your-agm-guide-what-you-can-do-and-how-do-it-ii521588','wealth'),('ip33-ii-about','ii-uk','GB','en-GB','https://www.ii.co.uk/about-us','wealth')]
if __name__=='__main__':
 assert not (RUN/'FROZEN').exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(base.fetch,T))
 base.write(RUN/'sources.json',ss);(RUN/'FROZEN').write_text('Current ownquote andproxy classification sources; no personalexecution.\n');print({'sources':[(s['id'],s['state'],len(s.get('text',''))) for s in ss]})
