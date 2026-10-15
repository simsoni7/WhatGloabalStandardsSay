#!/usr/bin/env python3
"""Independent source-contract checks for the generated integration browse layer."""
import collections
import csv
import hashlib
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = pathlib.Path('/home/ubuntu/wgss-integration-20261015')
TOSS = pathlib.Path('/home/ubuntu/wgss-toss-reclassification-v6')
OUT = ROOT/'integration-data'

def load(p): return json.loads(p.read_text())
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def local(url):
    assert url.startswith('/integration-data/')
    return ROOT/url.lstrip('/')
def read_csv(name):
    with (TOSS/'deliverables'/name).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

class IntegrationData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load(OUT/'catalog.json')
        cls.screens = {r['id']:r for r in cls.catalog['screens']}
        cls.phrases = {r['id']:r for r in cls.catalog['phrases']}
        html = (SOURCE/'source/dictionary/financial-dictionary.html').read_text()
        cls.dictionary = json.loads(re.search(r'<template[^>]*id="data"[^>]*>(.*?)</template>',html,re.S)[1])
        original = list(cls.dictionary['rows'])
        for p in (SOURCE/'source/dictionary/data').glob('*.json'):
            original.extend(load(p)['rows'])
        cls.original_terms = {r['evidence_id']:r for r in original}
        cls.terms, cls.provenance = {}, {}
        for chunk in cls.catalog['dictionary']['chunks']:
            for r in load(local(chunk['path']))['rows']: cls.terms[r['id']] = r
            for r in load(local(chunk['provenancePath']))['rows']: cls.provenance[r['evidence_id']] = r
        cls.release = load(TOSS/'quality/release-index.json')
        cls.toss = {r['image_id']:r for r in cls.release['items']}

    def test_separate_units_and_cardinalities(self):
        c = self.catalog['counts']
        self.assertEqual((len(self.screens),len(self.phrases)),(183,736))
        self.assertEqual((c['legacyScreens'],c['legacyUniqueImages'],c['legacyPhrases']),(82,74,301))
        self.assertEqual((c['tossScreens'],c['tossUniqueImages'],c['tossNativePhrases']),(101,101,435))
        self.assertEqual(len({s['originalSha'] for s in self.screens.values()}),175)
        self.assertEqual((c['canonicalWorks'],c['canonicalReferences'],c['documentedWorks']),(216,323,189))
        self.assertEqual((c['dictionaryCore'],c['dictionaryConditional'],c['dictionaryLanguages']),(20239,6006,47))
        self.assertEqual(len(self.original_terms),26245)
        self.assertEqual(len(self.catalog['flows']),39)
        self.assertEqual(len(self.catalog['sequenceGroups']),43)

    def test_every_dictionary_raw_observation_unchanged(self):
        self.assertEqual(self.provenance,self.original_terms)
        self.assertEqual(set(self.terms),set(self.original_terms))
        for id,raw in self.original_terms.items():
            row = self.terms[id]
            self.assertEqual((row['datasetId'],row['sourceConceptId'],row['english'],row['target'],row['korean'],row['language']),
                (raw['dataset_id'],raw.get('source_concept_id'),raw['source_english'],raw['source_target'],raw.get('source_english_korean'),raw['target_language']))
            self.assertEqual(row['koreanStatus'],(raw.get('korean_expression') or {}).get('status'))
            self.assertIsNone(row['approvedTranslation'])
            self.assertIsNone(row['approval'])
            if row['layer']=='conditional': self.assertFalse(row['generationEligible'])
            self.assertTrue(local(row['provenancePath']).exists())

    def test_dictionary_chunk_integrity_and_license_separation(self):
        count = collections.Counter()
        for chunk in self.catalog['dictionary']['chunks']:
            p=local(chunk['path']); rows=load(p)['rows']
            self.assertEqual(digest(p),chunk['sha256'])
            self.assertEqual(p.stat().st_size,chunk['bytes'])
            self.assertLess(p.stat().st_size,300000)
            self.assertEqual(digest(local(chunk['provenancePath'])),chunk['provenanceSha256'])
            self.assertLess(local(chunk['provenancePath']).stat().st_size,25*1024*1024)
            self.assertEqual(len(rows),chunk['count'])
            self.assertEqual(dict(collections.Counter(r['language'] for r in rows)),chunk['languageCounts'])
            self.assertEqual({r['layer'] for r in rows},{chunk['layer']})
            count.update(r['layer'] for r in rows)
        self.assertEqual(count,{'core':20239,'conditional':6006})
        datasets=self.catalog['dictionary']['datasets']
        self.assertEqual(collections.Counter(d['layer'] for d in datasets),{'core':12,'conditional':3})
        for d in datasets:
            self.assertTrue(d['license'])
            if d['layer']=='conditional':
                self.assertTrue(d['usageTerms']['copyleft'])
                self.assertTrue(d['usageTerms']['source_distribution_required'])
                self.assertTrue(d['licenseNotice'])
                self.assertTrue(d['correspondingSourceUrl'])
        self.assertTrue(self.catalog['dictionary']['conditionalRequiresOptIn'])

    def test_nested_source_urls_and_pdf_locators(self):
        def values(v):
            if isinstance(v,dict):
                return [s for x in v.values() for s in values(x)]
            if isinstance(v,list): return [s for x in v for s in values(x)]
            return [v] if isinstance(v,str) and re.match(r'^https?://',v) else []
        for id,raw in self.original_terms.items():
            self.assertEqual(self.terms[id]['sourceUrlCount'],len(values(raw.get('source') or {})))
        cfpd=[r for r in self.terms.values() if r['datasetId']=='cfpd']
        self.assertEqual(len(cfpd),10089)
        self.assertTrue(all(r['sourceUrl'] is None for r in cfpd))
        self.assertTrue(all(r['sourceLocator']['sha256'] and r['sourceLocator']['pdf_page_start'] for r in cfpd))
        self.assertTrue(all(r['sourceInventoryUrl'].endswith('#cfpd') for r in cfpd))
        receipt=next(r for r in self.terms.values() if r['id']=='cfpb_receipt:ar:row1')
        self.assertEqual(receipt['sourceUrl'],'https://files.consumerfinance.gov/f/documents/cfpb_send-money-abroad_ar.pdf')
        self.assertEqual(receipt['sourceLocator']['page'],1)

    def test_legacy_screen_metadata_and_all_image_bytes(self):
        source=load(SOURCE/'analysis/published-screen-index.json')
        for raw in source:
            id=raw['cohort']+':'+(raw['case_id'] or 'standalone')+':'+raw['screen_id']
            row=self.screens[id]
            self.assertEqual((row['taskId'],row['country'],row['language'],row['purpose'],row['stage'],row['sourceUrl'],row['collectedAt']),
                (raw['task_id'],raw['country'],raw['language'],raw['purpose_code'],raw['stage_code'],raw['source_url'],raw['collected_at']))
            self.assertEqual(digest(ROOT/'dist'/raw['image_path']),row['originalSha'])
        for row in self.phrases.values():
            if row.get('imagePath'):
                path=local(row['imagePath']) if row['imagePath'].startswith('/integration-data/') else ROOT/'dist'/row['imagePath'].lstrip('/')
                self.assertEqual(digest(path),row['originalSha'])

    def test_flow_and_phrase_references_are_contextual(self):
        for flow in self.catalog['flows']:
            screens=[self.screens[id] for id in flow['screenIds']]
            self.assertEqual([s['index'] for s in screens],sorted(s['index'] for s in screens))
            for s in screens:
                self.assertEqual(s['flowId'],flow['id'])
                self.assertEqual((s['taskId'],s['country'],s['purpose']),(flow['taskId'],flow['country'],flow['purpose']))
        legacy=[]
        for version in [38,42,44,45,46,48]: legacy.extend(load(ROOT/f'dist/data/wording-references-v{version}.json')['items'])
        self.assertEqual(len(legacy),301)
        for original in legacy:
            row=self.phrases[original['id']]
            self.assertEqual(row['text'],original['label'])
            self.assertEqual(row['country'],original.get('country'))
            self.assertEqual(row['sourceUrl'],original.get('source_url'))
            for sid in row['screenIds']:
                screen=self.screens[sid]
                self.assertEqual(screen['originalSha'],original['image_sha256'])
                self.assertEqual(screen['providerId'],row['providerId'])
                if original.get('step_id'): self.assertEqual(screen['sourceScreenId'],original['step_id'])
                self.assertIn(original['id'],screen['phraseIds'])

    def test_documentary_feature_matrix_exact_admitted_references(self):
        bank=load(ROOT/'dist/data/bank-ui.json')
        refs={r['id']:r for r in bank['benchmarks'] if r.get('root_function_admitted')}
        expected={(id,wid) for id,r in refs.items() for wid in r['ui_work_ids']}
        self.assertEqual({(f['referenceId'],f['workId']) for f in self.catalog['features']},expected)
        self.assertEqual(len(expected),325)
        for f in self.catalog['features']:
            ref=refs[f['referenceId']]
            self.assertEqual(f['country'],ref['country'])
            self.assertEqual(f['evidence'][0]['url'],ref['source_url'])
            self.assertEqual(f['evidence'][0]['rawSha'],ref['raw_sha256'])
            self.assertEqual(f['status'],'documented')
            self.assertEqual(f['absenceMeaning'],'unknown')
            self.assertFalse(f['observedAppScreen'])
        self.assertFalse(self.catalog['policies']['globalMeceApproved'])
        providers={p['id']:p for p in self.catalog['providers']}
        self.assertIn('toss-service',providers)
        self.assertIn('toss-bank',providers)
        self.assertIsNone(providers['empf-hk']['operatorId'])
        self.assertEqual(providers['empf-hk']['entityKind'],'service')
        self.assertTrue({'eMPF','eMPF Platform','eMPF 平台'}<=set(providers['empf-hk']['aliases']))

    def test_toss_exact_approved_copies_and_unknown_metadata(self):
        release_sha=digest(TOSS/'quality/release-index.json')
        classification={r['원본ID']:r for r in read_csv('토스-v6-101장-분류검토.csv')}
        groups={g['id']:g for g in self.catalog['sequenceGroups']}
        for id,item in self.toss.items():
            screen=self.screens['toss-v6:'+id]
            self.assertEqual(digest(local(screen['imagePath'])),item['masked_sha256'])
            self.assertEqual(screen['originalSha'],item['masked_sha256'])
            self.assertEqual(screen['approval']['releaseIndexSha256'],release_sha)
            self.assertTrue(item['privacy_passed'] and item['semantic_review_passed'] and item['private_release_eligible'])
            self.assertEqual(screen['taskLabel'],item['task_ko'])
            self.assertEqual(screen['category'],item['primary_category_ko'])
            self.assertEqual(screen['taskLabel'],classification[id]['업무 설명(편집)'])
            self.assertEqual(screen['index'],int(classification[id]['순서']))
            for field in ['sourceUrl','capturedAt','collectedAt','appVersion','operatorId','country','flowId']:
                self.assertIsNone(screen[field])
            self.assertEqual(screen['platform'],'unknown')
            self.assertEqual(screen['access'],'owner-private')
            self.assertEqual(screen['stage'],'unknown')
            self.assertEqual(screen['purpose'],'unknown')
            self.assertIn(screen['id'],groups[screen['editorialGroupId']]['screenIds'])
            for n,button in enumerate(item['native_buttons']):
                phrase=self.phrases['TOSS-v6-'+id+'-button-'+str(n)]
                self.assertEqual((phrase['text'],phrase['role']),(button['literal_label'],button['role']))
                self.assertFalse(phrase['actualActionExecuted'])
        for group in groups.values():
            self.assertFalse(group['observedNavigation'])
            self.assertEqual(group['orderKind'],'file-order-affinity-only')
        paths=[str(p.relative_to(OUT)) for p in (OUT/'toss-v6').rglob('*') if p.is_file()]
        self.assertEqual(len([p for p in paths if p.endswith('.png')]),101)
        self.assertFalse(any('before' in p or 'ocr' in p.lower() or 'original' in p.lower() for p in paths))

    def test_navigation_crosswalk_keeps_source_meaning_and_ambiguous_gaps(self):
        mapping=load(ROOT/'data/integration-navigation-crosswalk.json')
        self.assertFalse(mapping['canonicalMappingApproved'])
        self.assertFalse(mapping['observedFlowInferred'])
        self.assertEqual(len(mapping['items']),101)
        self.assertEqual(self.screens['toss-v6:TOSS-049']['navigationTaskIds'],['card-close'])
        self.assertEqual(self.screens['toss-v6:TOSS-062']['navigationTaskIds'],['digital-service-close'])
        self.assertEqual(self.screens['toss-v6:TOSS-064']['navigationTaskIds'],['account-close'])
        for sid in ['TOSS-014','TOSS-076','TOSS-092']:
            self.assertEqual(self.screens['toss-v6:'+sid]['navigationTaskIds'],[])
        for row in mapping['items']:
            screen=self.screens[row['screenId']]
            self.assertEqual(screen['taskId'],screen['editorialGroupId'])
            self.assertEqual(screen['originalSha'],row['imageSha256'])
            self.assertEqual(screen['purpose'],'unknown')
            self.assertEqual(screen['stage'],'unknown')
            self.assertFalse(screen['canonicalFinancialAdmission'])
            for pid in screen['phraseIds']:
                self.assertEqual(set(self.phrases[pid]['navigationTaskIds']),set(row['taskIds']))

    def test_frozen_input_manifest_and_no_unmanifested_outputs(self):
        manifest=load(OUT/'build-manifest.json')
        roots={'repository':ROOT,'integration-source':SOURCE,'toss-v6-source':TOSS}
        for r in manifest['inputs']:
            self.assertEqual(digest(roots[r['root']]/r['path']),r['sha256'])
        self.assertEqual(digest(OUT/'catalog.json'),manifest['catalogSha256'])
        generated={str(p.relative_to(OUT)) for p in OUT.rglob('*') if p.is_file()}
        self.assertEqual(generated,set(manifest['generatedFiles'])|{'build-manifest.json'})
        self.assertTrue(all((OUT/p).stat().st_size<25*1024*1024 for p in generated))

if __name__=='__main__': unittest.main(verbosity=2)
