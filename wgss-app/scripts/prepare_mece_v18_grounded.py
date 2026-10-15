"""New immutable retry inputs: select original clauses without retyping them."""
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-20261006'
jobs=[]
for path in sorted((RUN/'inputs').glob('scope-full-v18-*.json')):
 job=read(path);job['id']=job['id'].replace('scope-full-v18','scope-grounded-v18')
 job['grounded_section_ids']=True
 job['instructions']=job['instructions'].replace('evidence:[{section_id,quote}]','evidence_section_ids:[suppliedSectionIDs]')
 start=job['instructions'].index('Evidence quotes MUST')
 end=job['instructions'].index('Each composed/partial')
 job['instructions']=job['instructions'][:start]+'''Select ONLY supplied section IDs in evidence_section_ids; do not output quotes or an evidence field. Original text is retained separately and exact quotation is extracted by code, not retyped by the model. If no substantive own text, cite explicit parent only as qualified context or leave IDs empty and mark specification gap. '''+job['instructions'][end:]
 target=RUN/'inputs'/(job['id']+'.json')
 if target.exists():assert read(target)==job
 else:write(target,job)
 jobs.append(job['id'])
write(RUN/'grounded-manifest.json',dict(jobs=jobs,rows=927,supersedes='scope-full-v18 literal-quote attempts',automatic_adoption=False))
print(' '.join(jobs))
