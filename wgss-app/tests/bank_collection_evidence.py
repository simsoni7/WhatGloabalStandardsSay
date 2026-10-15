# Historical v1/v28 oracle retained; current v1.1 is independently checked in bank_expansion_v29.py.
"""Verify original image provenance, local-market gaps and channel qualifications."""
import csv,hashlib,json
from pathlib import Path
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];P=R/'research/source-store/bank-collection-v24-20261011'
def read(p):return json.loads(p.read_text())
d=read(R/'data/bank-ui-baseline-v28.json');root=read(R/'data/bank-ui-collection-v24-decisions.json');checks=[]
def check(name,ok):assert ok,name;checks.append(name)
works={w['id'] for w in d['works']};rows=d['benchmarks'];plan=d['collection_plan']
check('collection cannot alter the confirmed denominator',len(works)==214 and root['denominator']==214 and root['scope_change'] is False)
check('all country-work gaps retained',len(d['collection_matrix'])==642 and len({(c['country'],c['ui_work_id']) for c in d['collection_matrix']})==642)
covered={id for b in rows for id in b['ui_work_ids']}
check('distinct work coverage not source/image counts',len(covered)==85 and d['benchmark_counts']['unlinked_works']==129 and len(rows)==166)
for cell in d['collection_matrix']:
    expected=[b for b in rows if b['country']==cell['country'] and cell['ui_work_id'] in b['ui_work_ids']]
    assert cell['example_ids']==[b['id'] for b in expected]
    assert cell['provider_ids']==sorted({b['provider_id'] for b in expected})
    assert cell['screen_example_ids']==[b['id'] for b in expected if b.get('screen_evidence')]
check('country-work coverage agrees with original admitted rows',True)
sources={s['id']:s for s in read(P/'sources.json')};images=read(P/'guide-images.json');hashes={x['sha256']:x for x in images}
for b in rows:
    if not b.get('screen_evidence') or not b['source_id'].startswith('V24:'):continue
    screen=b['screen_evidence'];im=hashes[screen['image_sha256']];src=sources[im['source_id'][4:]]
    assert hashlib.sha256((R/'dist'/screen['image_path']).read_bytes()).hexdigest()==im['sha256']
    assert hashlib.sha256((R/im['private_path']).read_bytes()).hexdigest()==im['sha256']
    assert any(x['url']==screen['asset_url'] for x in src['images'])
    raw=(R/src['snapshot_path']/'source.html').read_bytes();assert hashlib.sha256(raw).hexdigest()==b['raw_sha256']
    assert b['country']=='HK' and b['language']=='zh-Hant' and b['evidence_type']=='official_guide_screen'
    assert not b['observed_app_screen'] and b['app_os'] is None and b['verified_ui_version'] is None
check('guide assets are unmodified original images linked from native official source',True)
check('one repeated account image does not inflate screen totals',sum(bool(b.get('screen_evidence')) for b in rows if b['source_id'].startswith('V24:'))==7 and len(hashes)==6 and d['benchmark_counts']['official_guide_screens']==28)
check('no global Wise help falsely attributed to UK',not any(b['source_id']=='V24:wise-send-global' for b in rows) and plan['staged_sources'][0]['country'] is None)
check('candidate platforms distinct from admitted providers',len(plan['provider_targets'])==10 and d['benchmark_counts']['providers']==8 and all(not t['representativeness_proven'] for t in plan['provider_targets']))
check('new limited-account review not patched onto self-selected limits',len(plan['definition_review_gaps'])==2 and not any(b['source_id']=='V24:kakao-limit' for b in rows))
check('only 32 explicit canonical priority works',plan['priority_works']==32 and all(set(g['ui_work_ids'])<=works for g in plan['priority_groups']))
uk=BeautifulSoup((R/'research/source-store/bank-ui-v23-20261011/sources/hsbc-uk-ui-inventory.html').read_bytes(),'html.parser')
for b in rows:
    if b['provider_id']!='hsbc-uk' or not b.get('native_locator'):continue
    for proof in b['channel_proofs']:
        import re
        ti,ri,ci=map(int,re.findall(r'\[(\d+)\]',proof['locator']))
        cell=uk.select('table')[ti].select('tr')[ri].find_all(['th','td'])[ci]
        if proof['state']=='described_available':assert cell.select('.icon-agree')
        if proof['state']=='not_available_in_comparison':assert cell.select('.icon-minimize')
        if proof['condition_native']:assert proof['condition_native']==' '.join(cell.stripped_strings)
check('channel availability comes from native cells, not model guess',True)
statement=next(b for b in rows if b['expression']=='Latest statement - View, download or print')
check('statement personal-loan exclusion retained',statement['channel_proofs'][1]['condition_native']=='Excluding personal loans' and '개인대출' in statement['conditions'])
check('application not mislabeled as approved credit change',all(b['ui_work_ids']==['WGSS-UI-86F2DD937522'] for b in rows if b['expression'] in ['Request a higher limit','금리인하요구권 신청하기']))
csvrows=list(csv.DictReader(__import__('io').StringIO(d['csv_artifacts']['bank-ui-collection-matrix.csv'].lstrip('\ufeff'))))
check('complete downloadable matrix includes blank cells',len(csvrows)==642 and sum(r['evidence_state']=='not_collected' for r in csvrows)==d['collection_counts']['empty_country_work_cells'])
check('Bedrock proposals have explicit root decisions',len(root['native_row_dispositions'])==65 and len(root['model_runs'])==4 and all(not x['automatic_adoption'] for x in root['native_row_dispositions']))
print(json.dumps({'bank_collection_evidence':'passed','checks':len(checks),'items':checks},ensure_ascii=False))
