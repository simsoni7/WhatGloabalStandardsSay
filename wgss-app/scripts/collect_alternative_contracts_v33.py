"""Own operative contract follow-up for remaining partnership and prepaid-sale units."""
import concurrent.futures
import collect_bank_gaps_v30 as c
c.RUN=c.R/'research/source-store/alternative-contracts-v33-20261013'
if __name__=='__main__':
 assert not (c.RUN/'FROZEN').exists()
 ts=[('alt-dib-musharika','dib-ae','AE','en','https://dib.ae/business/products-services/musharika','alternative'),('alt-dib-card-index','dib-ae','AE','en','https://dib.ae/terms-and-conditions-cpr','alternative'),('alt-dib-salam-terms','dib-ae','AE','en','https://www.dib.ae/docs/default-source/cpr/tc/cards-tc-salam-cards-tc-en.pdf?sfvrsn=fe85915e_46','alternative')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:ss=list(p.map(c.fetch,ts))
 c.write(c.RUN/'sources.json',ss);(c.RUN/'FROZEN').write_text('Search-discovered own publisher originals; index links allow provenance check.\n');print([(s['id'],s['state'],len(s.get('text',''))) for s in ss])
