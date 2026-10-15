"""Freeze a second model's full-row check; suggestions remain advisory."""
import json
from run_mece_closure import ROOT,read,write
RUN=ROOT/'research/source-store/mece-closure-v22-20261011'

def prepare():
    prepared=[]
    for p in sorted((RUN/'reviews').glob('census-*/*/proposal.json')):
        proposal=read(p); original=read(RUN/'inputs'/(proposal['job_id']+'.json'))
        jid=proposal['job_id'].replace('census','steward')
        if (RUN/'inputs'/(jid+'.json')).exists():continue
        instructions=original['instructions']+'''\nYou are a separate Sonnet quality steward. Independently verify EACH proposed row against the own original clauses and actual definitions. Do not agree from model authority. Return the SAME full row schema for all references, with an extra critique field {opus_retained:boolean,problem:null|short reason}. Correct false exclusions (financial data/fees/customer support/risk/control/funding cannot be ordinary enterprise strategy by default), invented independent results, role-only product clones, broad-parent full mapping that skips responsibilities, unspecified text disguised as complete coverage, and mismatched direct objects/completion conditions. A phrase 'includes' in the proposed mapping is not actual evidence. Compare existing includes/excludes before selecting IDs. Preserve ambiguities as specific gaps and no unsupported process inflation. Every reference exactly once.'''
        job={**original,'id':jid,'model':'claude-sonnet-5','instructions':instructions,
             'input':{**original['input'],'opus_proposal':proposal['result']}}
        write(RUN/'inputs'/(jid+'.json'),job);prepared.append(jid)
    print(json.dumps({'prepared':prepared}))

if __name__=='__main__':prepare()
