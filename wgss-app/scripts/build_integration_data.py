#!/usr/bin/env python3
"""Build a source-preserving browse layer from frozen admitted WGSS assets.

No network or model calls. Never mutates source datasets, assets or Git state.
The optional source paths make the build independently reproducible.
"""
import argparse
import collections
import csv
import hashlib
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_INPUT = pathlib.Path('/home/ubuntu/wgss-integration-20261015')

def load(path):
    return json.loads(path.read_text())

def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value) + b'\n')

def urls(value):
    """Find URL-valued fields at any depth, preserving their object paths."""
    found = []
    def visit(v, path):
        if isinstance(v, dict):
            for key, child in v.items():
                visit(child, path + [key])
        elif isinstance(v, list):
            for i, child in enumerate(v):
                visit(child, path + [str(i)])
        elif isinstance(v, str) and re.match(r'^https?://', v):
            found.append({'path': '.'.join(path), 'url': v})
    visit(value, [])
    return found

# Source aliases identify the same service; they do not merge related legal entities.
PROVIDERS = {
    'Citi': ('citi', 'Citi'), 'Chase': ('chase', 'Chase'),
    'PayPal': ('paypal', 'PayPal'), 'Wise': ('wise', 'Wise'),
    'HSBC UK': ('hsbc-uk', 'HSBC UK'), 'HSBC Hong Kong': ('hsbc-hk', 'HSBC Hong Kong'),
    'HSBC Broking': ('hsbc-broking-hk', 'HSBC Broking'),
    'HSBC Life': ('hsbc-life-hk', 'HSBC Life Hong Kong'),
    'HSBC Life Hong Kong': ('hsbc-life-hk', 'HSBC Life Hong Kong'),
    'NatWest': ('natwest-uk', 'NatWest'), 'Starling Bank': ('starling-uk', 'Starling Bank'),
    'Stripe': ('stripe-uk', 'Stripe'), '토스뱅크': ('toss-bank', '토스뱅크'),
    'Toss Bank': ('toss-bank', '토스뱅크'), 'Toss': ('toss-service', 'Toss'),
    '토스': ('toss-service', 'Toss'), '우리카드': ('woori-card', '우리카드'),
    '우리은행': ('woori-bank', '우리은행'),
    '카카오뱅크': ('kakao', '카카오뱅크'), 'KB국민은행': ('kb', 'KB국민은행'),
    '삼성화재': ('samsung-fire', '삼성화재'), '신한카드': ('shinhan-card', '신한카드'),
    'eMPF': ('empf-hk', 'eMPF Platform'), 'eMPF Platform': ('empf-hk', 'eMPF Platform'),
    'eMPF 平台': ('empf-hk', 'eMPF Platform'),
    'Dubai Islamic Bank': ('dib-ae', 'Dubai Islamic Bank'),
    'Dubai Islamic Bank PJSC': ('dib-ae', 'Dubai Islamic Bank'),
}
TASK_ALIASES = {
    'signup': ['회원가입', '회원 가입', '가입', '등록', 'sign up', 'signup', 'register', 'registration'],
    'login': ['로그인', '로그온', 'login', 'log in', 'sign in', 'sign on'],
    'password-recovery': ['비밀번호 찾기', '비밀번호 재설정', '암호 찾기', 'forgot password', 'password reset', 'account recovery'],
    'digital-service-close': ['탈퇴', '회원탈퇴', '서비스 탈퇴', '회원 탈퇴', 'close profile'],
    'account-opening': ['계좌개설', '계좌 개설', '통장 개설', 'open account', 'current account', 'checking account', 'savings account'],
    'card-application': ['카드신청', '카드 신청', '신용카드 발급', 'apply card', 'credit card application'],
}
EXTRA_TASKS = {'qna': '자주 묻는 질문', 'event': '이벤트·혜택', 'overview': '서비스 소개'}
COUNTRIES = {'US': '미국', 'GB': '영국', 'KR': '대한민국', 'HK': '홍콩', 'MY': '말레이시아', 'AE': '아랍에미리트', 'SG': '싱가포르', 'DE': '독일', 'BR': '브라질', 'ZA': '남아프리카공화국', 'FR': '프랑스'}

def build(source, dist, out, toss_source):
    inputs = []
    def read(path):
        inputs.append(path)
        return load(path)
    dictionary_path = source / 'source/dictionary/financial-dictionary.html'
    inputs.append(dictionary_path)
    raw = dictionary_path.read_text()
    dictionary = json.loads(re.search(r'<template[^>]*id="data"[^>]*>(.*?)</template>', raw, re.S)[1])
    base_rows = dictionary['rows']
    components = {}
    all_rows = list(base_rows)
    for component in dictionary['community_catalog']['components']:
        path = source / 'source/dictionary/data' / component['file']
        if sha(path) != component['sha256']:
            raise ValueError('Conditional source hash mismatch: ' + component['dataset_id'])
        data = read(path)
        if len(data['rows']) != component['entry_count']:
            raise ValueError('Conditional source count mismatch')
        components[data['dataset_id']] = data
        all_rows.extend(data['rows'])
    assert len(base_rows) == 20239 and len(all_rows) == 26245
    assert len({r['target_language'] for r in all_rows}) == 47
    assert len({r['evidence_id'] for r in all_rows}) == len(all_rows)
    source_meta = {s['dataset_id']: s for s in dictionary['sources']}
    datasets = []
    for dataset_id, rows in __import__('itertools').groupby(sorted(all_rows, key=lambda r: r['dataset_id']), key=lambda r: r['dataset_id']):
        rows = list(rows)
        meta = source_meta[dataset_id]
        conditional = components.get(dataset_id)
        datasets.append({'id': dataset_id, 'name': meta['name'], 'count': len(rows),
            'layer': 'conditional' if conditional else 'core', 'license': meta['license'],
            'commercial': meta.get('commercial'), 'urls': meta.get('urls', []),
            'languages': sorted({r['target_language'] for r in rows}), 'metadata': meta,
            'usageTerms': conditional.get('usage_terms') if conditional else None,
            'licenseNotice': conditional.get('license_notice') if conditional else meta.get('license_notice'),
            'correspondingSourceUrl': conditional.get('corresponding_source_url') if conditional else None,
            'sourceManifest': conditional.get('source_manifest') if conditional else None,
            'sourceInventoryUrl': '/integration-data/source-inventory.json#' + dataset_id})
    chunks = []
    original_by_id = {r['evidence_id']: r for r in all_rows}
    # Replace only our generated chunk files; source data are never modified.
    for subdir in ['terms', 'provenance']:
        for old in (out/subdir).glob('[0-9][0-9][0-9][0-9].json'):
            old.unlink()
    chunk_rows, chunk_size = [], 0
    def flush():
        nonlocal chunk_rows, chunk_size
        if not chunk_rows:
            return
        path = f'terms/{len(chunks)+1:04d}.json'
        provenance_path = f'provenance/{len(chunks)+1:04d}.json'
        for row in chunk_rows:
            row['provenancePath'] = '/integration-data/' + provenance_path
        # Full unchanged observations are fetched only when provenance is needed.
        write(out/provenance_path, {'schemaVersion': 1, 'rows': [original_by_id[r['id']] for r in chunk_rows]})
        target = out / path
        write(target, {'schemaVersion': 1, 'rows': chunk_rows})
        chunks.append({'path': '/integration-data/' + path, 'count': len(chunk_rows),
            'bytes': target.stat().st_size, 'sha256': sha(target), 'layer': chunk_rows[0]['layer'],
            'languageCounts': dict(collections.Counter(r['language'] for r in chunk_rows)),
            'datasetIds': sorted({r['datasetId'] for r in chunk_rows}),
            'provenancePath': '/integration-data/' + provenance_path,
            'provenanceSha256': sha(out/provenance_path)})
        chunk_rows, chunk_size = [], 0
    for original in all_rows:
        src = original.get('source') or {}
        nested_urls = urls(src)
        direct = src.get('url') or src.get('source_url')
        if not direct:
            direct = next((u['url'] for u in nested_urls if u['path'].rsplit('.',1)[-1] in {'url','source_url','target_url','download_url'}), None)
        layer = 'conditional' if original['dataset_id'] in components else 'core'
        row = {'id': original['evidence_id'], 'datasetId': original['dataset_id'],
            'sourceConceptId': original.get('source_concept_id'), 'datasetVersion': original.get('dataset_version'),
            'english': original['source_english'], 'korean': original.get('source_english_korean'),
            'target': original['source_target'], 'language': original['target_language'],
            'recordType': original.get('record_type'), 'definition': original.get('definition'),
            'status': original.get('equivalence_status') or original.get('alignment_status') or 'unknown',
            'alignmentStatus': original.get('alignment_status'), 'alignmentBasis': original.get('alignment_basis'),
            'koreanStatus': (original.get('korean_expression') or {}).get('status'),
            'sourceUrl': direct, 'sourceLocator': {k:v for k,v in src.items() if k in {
                'file','source_file','sha256','source_sha256','page','pdf_page_start','pdf_page_end',
                'location','source_key','id','key','record_id','source_id','source_locator'}},
            'sourceInventoryUrl': '/integration-data/source-inventory.json#' + original['dataset_id'],
            'license': original.get('license') or source_meta[original['dataset_id']]['license'],
            'layer': layer, 'generationEligible': original.get('generation_eligible', False),
            'approvedTranslation': original.get('approved_translation'), 'approval': original.get('approval'),
            'reviewStatus': original.get('review_status'),
            'jurisdiction': original.get('source_jurisdiction') or original.get('jurisdiction'),
            'sourceUrlCount': len(nested_urls)}
        size = len(encoded(row))
        if chunk_rows and (chunk_size + size > 250000 or chunk_rows[-1]['layer'] != layer):
            flush()
        chunk_rows.append(row)
        chunk_size += size + 1
    flush()
    write(out / 'source-inventory.json', {'schemaVersion': 1, 'release': dictionary['release_ref'],
        'datasets': datasets, 'downloads': dictionary['downloads'],
        'transformationNotice': 'Original labels, IDs and source locators preserved. Added browse aliases and field projections; Korean helpers do not approve target-language equivalence. Conditional copyleft sources remain a separate opt-in reference layer. Preserve source copyright/license notices and corresponding-source obligations.'})

    bank = read(dist / 'data/bank-ui.json')
    admitted = [b for b in bank['benchmarks'] if b.get('root_function_admitted')]
    assert len(bank['works']) == 216 and len(admitted) == 323
    works = {w['id']: w for w in bank['works']}
    tasks_raw = read(dist / 'data/user-work-catalog-v44.json')
    tasks = []
    for t in tasks_raw['tasks']:
        tasks.append({'id': t['id'], 'label': t['label'],
            'aliases': list(dict.fromkeys(t.get('aliases', []) + TASK_ALIASES.get(t['id'], []))),
            'groupId': t['group_id'], 'purposeCodes': t.get('purpose_codes', []),
            'workIds': t.get('work_ids', []), 'scopeNote': t.get('scope_note'),
            'aliasRole': 'navigation_only', 'screenCount': 0})
    for tid, label in EXTRA_TASKS.items():
        if tid not in {t['id'] for t in tasks}:
            tasks.append({'id': tid, 'label': label, 'aliases': [], 'groupId': 'reference', 'purposeCodes': [], 'workIds': [], 'screenCount': 0, 'aliasRole': 'navigation_only'})
    work_tasks = collections.defaultdict(list)
    for t in tasks:
        for work_id in t['workIds']:
            work_tasks[work_id].append(t['id'])
    providers = {}
    def provider(name, source_id=None, country=None):
        pid, display = PROVIDERS.get(name, (source_id or re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-'), name))
        if not pid:
            raise ValueError('Unidentified provider: ' + name)
        if pid not in providers:
            providers[pid] = {'id': pid, 'name': display, 'aliases': [], 'sourceIds': [],
                'operatorId': None, 'entityKind': 'service' if pid == 'empf-hk' else 'provider-brand',
                'identityBasis': 'existing source provider identity; operators not inferred',
                'countries': [], 'screenCount': 0, 'phraseCount': 0, 'featureCount': 0}
        p = providers[pid]
        if name not in p['aliases']: p['aliases'].append(name)
        if source_id and source_id not in p['sourceIds']: p['sourceIds'].append(source_id)
        if country and country not in p['countries']: p['countries'].append(country)
        return pid
    flow_raw = {}
    flows = []
    for version in [44,45,46,48]:
        for c in read(dist / f'data/public-flow-cases-v{version}.json')['cases']:
            fid = f'v{version}:' + c['id']
            flow_raw[fid] = c
            flows.append({'id': fid, 'sourceCaseId': c['id'], 'taskId': c['task_id'],
                'providerId': provider(c['provider'], c.get('provider_id'), c.get('country')),
                'provider': c['provider'], 'country': c.get('country'), 'language': c.get('language'),
                'purpose': c.get('purpose_code', 'unknown'), 'platform': c.get('platform'),
                'screenIds': [], 'limit': c.get('limit_ko'), 'state': c.get('case_state'),
                'terminal': c.get('terminal'), 'collectorNavigationChainObserved': c.get('collector_navigation_chain_observed'),
                'orderKind': 'publisher-sequence' if version==46 else 'recorded-reference-order',
                'orderNote': '기록 순서이며 필수 업무 절차나 완료를 뜻하지 않습니다.'})
    flow_by_id = {f['id']: f for f in flows}
    assets = {}
    for version in [39,42]:
        for a in read(dist / f'data/public-screen-assets-v{version}.json')['assets']:
            assets[(f'v{version}', a['id'])] = a
    index = read(source / 'analysis/published-screen-index.json')
    screens = []
    for row in index:
        fid = row['cohort'] + ':' + row['case_id'] if row.get('case_id') else None
        case = flow_raw.get(fid, {})
        step = next((s for s in case.get('steps', []) if s['id']==row['screen_id']), {})
        asset = assets.get((row['cohort'], row['screen_id']), {})
        sid = row['cohort'] + ':' + (row.get('case_id') or 'standalone') + ':' + row['screen_id']
        image = dist / row['image_path']
        if sha(image) != row['image_sha256']: raise ValueError('Screen hash mismatch: ' + sid)
        screen = {'id': sid, 'sourceScreenId': row['screen_id'], 'cohort': row['cohort'],
            'taskId': row['task_id'], 'providerId': provider(row['provider'], case.get('provider_id'), row.get('country')),
            'provider': row['provider'], 'country': row.get('country'), 'language': row.get('language'),
            'platform': row.get('platform'), 'imagePath': '/' + row['image_path'],
            'sourceUrl': row.get('source_url'), 'collectedAt': row.get('collected_at'),
            'publicationDate': row.get('publication_date') or step.get('publication_date') or asset.get('publication_date'),
            'purpose': row.get('purpose_code', 'unknown'), 'stage': row.get('stage_code', 'unknown'),
            'stageLabel': step.get('stage_label_ko'), 'title': step.get('title_native') or asset.get('title') or row['screen_id'],
            'sourceKind': row.get('source_class'), 'flowId': fid,
            'index': next((i+1 for i,s in enumerate(case.get('steps', [])) if s['id']==row['screen_id']), 1),
            'wording': step.get('observed_labels') or asset.get('observed_labels', []), 'phraseIds': [],
            'originalSha': row['image_sha256'], 'limit': case.get('limit_ko') or asset.get('note_ko'),
            'metadataBasis': row.get('metadata_basis'), 'currentUiVersionVerified': False,
            'applicationInputObserved': step.get('application_input_observed'),
            'applicationInputScope': step.get('application_input_scope'),
            'sourceHtmlSha': step.get('source_html_sha256') or asset.get('source_html_sha256'),
            'sourceTextSha': step.get('source_text_sha256'), 'sourceProof': step.get('source_proof')}
        screens.append(screen)
        if fid: flow_by_id[fid]['screenIds'].append(sid)
    for f in flows:
        f['screenIds'].sort(key=lambda sid: next(s['index'] for s in screens if s['id']==sid))
    phrases = []
    for version in [38,42,44,45,46,48]:
        for item in read(dist / f'data/wording-references-v{version}.json')['items']:
            pid = provider(item['provider'], item.get('provider_id'), item.get('country'))
            matches = [s for s in screens if s['originalSha']==item.get('image_sha256') and s['providerId']==pid
                and (not item.get('case_id') or (s['flowId'] and flow_by_id[s['flowId']]['sourceCaseId']==item['case_id']))
                and (not item.get('step_id') or s['sourceScreenId']==item['step_id'])]
            for s in matches: s['phraseIds'].append(item['id'])
            phrases.append({'id': item['id'], 'text': item['label'], 'providerId': pid,
                'provider': item['provider'], 'country': item.get('country'), 'language': item.get('language'),
                'taskId': item.get('task_id') or (matches[0]['taskId'] if len({s['taskId'] for s in matches})==1 else None),
                'purpose': item.get('purpose_code', 'unknown'), 'stage': item.get('stage_code', 'unknown'),
                'role': item.get('role_detail') or item.get('element_kind'), 'context': item.get('context_ko'),
                'screenIds': [s['id'] for s in matches], 'imagePath': '/' + item['image_path'] if item.get('image_path') else None,
                'sourceUrl': item.get('source_url'), 'collectedAt': item.get('collected_at'),
                'publicationDate': item.get('publication_date'), 'dateKind': item.get('date_kind'),
                'sourceKind': item.get('source_kind'), 'originalSha': item.get('image_sha256'),
                'currentUiVersionVerified': False, 'evidence': item.get('evidence'),
                'sourceElementKind': item.get('source_element_kind') or item.get('element_kind'),
                'sourceRoleDetail': item.get('source_role_detail') or item.get('role_detail')})
    features = []
    for b in admitted:
        pid = provider(b['provider_name'], b.get('provider_id'), b.get('country'))
        for wid in b['ui_work_ids']:
            assert wid in works
            features.append({'id': b['id'] + ':' + wid, 'referenceId': b['id'],
                'taskId': work_tasks[wid][0] if work_tasks[wid] else None, 'taskIds': work_tasks[wid],
                'workId': wid, 'label': works[wid]['title'], 'domainId': works[wid]['domain_id'],
                'providerId': pid, 'provider': b['provider_name'], 'country': b.get('country'),
                'language': b.get('language'), 'expression': b['expression'], 'meaning': b.get('meaning'),
                'conditions': b.get('conditions'), 'status': 'documented', 'absenceMeaning': 'unknown',
                'evidence': [{'id': b['id'], 'url': b['source_url'], 'locator': b.get('native_locator') or b.get('proof'),
                    'sourceKind': b.get('evidence_type'), 'collectedAt': b.get('collected_at'),
                    'rawSha': b.get('raw_sha256'), 'textSha': b.get('text_sha256'), 'sourceId': b.get('source_id')}],
                'observedAppScreen': b.get('observed_app_screen'), 'describedChannels': b.get('described_channels', []),
                'channelProofs': b.get('channel_proofs', []), 'policyStatus': b.get('policy_status'),
                'summaryKind': 'WGSS_editorial_summary_not_verbatim_UI'})
    # Independently cleared v6 copies only. Filename proximity is editorial
    # affinity, not a collector-observed navigation chain or canonical admission.
    toss_index_path = toss_source / 'quality/release-index.json'
    release = read(toss_index_path)
    approval = read(toss_source/'deliverables/검수상태.json')
    file_inventory = read(toss_source/'deliverables/파일목록.json')
    release_sha = sha(toss_index_path)
    assert approval['release_index_SHA256'] == file_inventory['release_index_sha256'] == release_sha
    assert release['eligible_count'] == len(release['items']) == 101
    assert release['whole101_review_complete'] and approval['whole101_review_complete']
    def read_csv(name):
        path = toss_source/'deliverables'/name
        inputs.append(path)
        return list(csv.DictReader(path.open(encoding='utf-8-sig')))
    classification = read_csv('토스-v6-101장-분류검토.csv')
    buttons = read_csv('토스-v6-검수된-버튼문구.csv')
    groups = read_csv('토스-v6-파일순서-유사구간43.csv')
    assert len(classification)==101 and len(buttons)==435 and len(groups)==43
    classified = {r['원본ID']:r for r in classification}
    files = {f['path']: f for f in file_inventory['files']}
    evidence = {e['image_id']:e for e in approval['exact_image_evidence']}
    sequence_groups = []
    for g in groups:
        gid = 'toss-v6:' + g['구간ID']
        sequence_groups.append({'id': gid, 'sourceGroupId': g['구간ID'],
            'label': g['구간 설명(편집)'], 'confidence': g['구간 유사성 확신'],
            'scope': g['판정 범위'], 'startFileIndex': int(g['시작 파일 순서']),
            'endFileIndex': int(g['끝 파일 순서']), 'screenIds': [],
            'orderKind': 'file-order-affinity-only', 'observedNavigation': False})
        tasks.append({'id': gid, 'label': g['구간 설명(편집)'], 'aliases': [],
            'groupId': 'toss-v6-editorial', 'purposeCodes': [], 'workIds': [],
            'scopeNote': g['판정 범위'], 'aliasRole': 'navigation_only',
            'sourceKind': 'reviewed-editorial-file-affinity', 'canonicalMappingApproved': False,
            'screenCount': 0})
    group_by_id = {g['id']:g for g in sequence_groups}
    approved_toss = []
    toss_pid = provider('Toss')
    for item in release['items']:
        tid = item['image_id']
        c = classified[tid]
        assert all(item[k] is True for k in ['privacy_passed','semantic_review_passed','private_release_eligible'])
        assert item['source_url'] is None and item['captured_at'] is None and item['app_version'] is None
        png = toss_source/'deliverables/images'/(tid+'.png')
        expected = item['masked_sha256']
        assert sha(png) == sha(pathlib.Path(item['approved_image_path'])) == expected
        assert c['분석사본SHA256'] == files['images/'+tid+'.png']['sha256'] == evidence[tid]['image_sha256'] == expected
        assert evidence[tid]['privacy_passed'] and evidence[tid]['semantic_review_passed']
        # Hash evidence without reading its potentially private text into the model.
        for refkey, hashkey in [('privacy_clearance_ref','privacy_clearance_sha256'),
                ('semantic_evidence_ref','semantic_evidence_sha256'), ('analysis_artifact_path','analysis_artifact_sha256')]:
            if item.get(refkey):
                assert sha(pathlib.Path(item[refkey])) == item[hashkey], (tid,refkey)
        inputs.append(png)
        image_relative = 'toss-v6/images/' + tid + '.png'
        (out/image_relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(png, out/image_relative)
        gid = 'toss-v6:' + c['파일 순서 유사 구간ID']
        sid = 'toss-v6:' + tid
        wording = [b['literal_label'] for b in item['native_buttons']]
        if item.get('heading_literal'): wording = [item['heading_literal']] + wording
        screen = {'id': sid, 'sourceScreenId': tid, 'cohort': 'toss-v6',
            'taskId': gid, 'taskLabel': item['task_ko'], 'category': item['primary_category_ko'],
            'providerId': toss_pid, 'provider': 'Toss', 'operatorId': None, 'country': None,
            'language': 'ko', 'platform': 'unknown', 'imagePath': '/integration-data/'+image_relative,
            'sourceUrl': None, 'collectedAt': None, 'capturedAt': None, 'appVersion': None,
            'publicationDate': None, 'purpose': 'unknown', 'stage': 'unknown', 'stageLabel': None,
            'title': item.get('heading_literal') or '원문 제목 미확인', 'headingStatus': item['heading_status'],
            'sourceKind': 'approved_masked_user_capture', 'flowId': None, 'index': int(c['순서']),
            'editorialGroupId': gid, 'wording': wording, 'phraseIds': [], 'originalSha': expected,
            'imageVersion': 'approved-masked-v6', 'access': 'owner-private',
            'limit': item.get('qa_note'), 'metadataBasis': 'v6 independently reviewed masked pixels; operator/source/capture date/version unknown',
            'currentUiVersionVerified': False, 'applicationInputObserved': None,
            'canonicalFinancialAdmission': False, 'actualFinancialActionExecuted': False,
            'reviewProvenance': item.get('review_provenance'),
            'approval': {'privacyPassed': True,'semanticReviewPassed': True,'privateReleaseEligible': True,
                'releaseIndexSha256': release_sha, 'imageSha256': expected},
            'sourceInventoryUrl': '/integration-data/toss-v6/release-provenance.json#'+tid}
        for n,b in enumerate(item['native_buttons']):
            phrase_id = 'TOSS-v6-'+tid+'-button-'+str(n)
            screen['phraseIds'].append(phrase_id)
            phrases.append({'id': phrase_id, 'text': b['literal_label'], 'providerId': toss_pid,
                'provider': 'Toss', 'country': None, 'language': 'ko', 'taskId': gid,
                'purpose': 'unknown', 'stage': 'unknown', 'role': b['role'],
                'context': item['task_ko'], 'screenIds': [sid], 'imagePath': screen['imagePath'],
                'sourceUrl': None, 'collectedAt': None, 'publicationDate': None, 'dateKind': 'unknown',
                'sourceKind': 'approved_masked_user_capture', 'originalSha': expected,
                'currentUiVersionVerified': False, 'access': 'owner-private', 'cohort': 'toss-v6',
                'sourceInventoryUrl': screen['sourceInventoryUrl'], 'actualActionExecuted': False})
        screens.append(screen)
        group_by_id[gid]['screenIds'].append(sid)
        next(t for t in tasks if t['id']==gid)['aliases'].extend([item['task_ko'],item['primary_category_ko']])
        approved_toss.append({'id': tid,'sequence':int(c['순서']),'imagePath':screen['imagePath'],
            'maskedSha256':expected,'taskLabel':item['task_ko'],'category':item['primary_category_ko'],
            'editorialGroupId':gid, 'heading':item.get('heading_literal'),'headingStatus':item['heading_status'],
            'nativeButtons':item['native_buttons'],'privacyPassed':True,'semanticReviewPassed':True,
            'privateReleaseEligible':True,'sourceUrl':None,'capturedAt':None,'appVersion':None,'operatorId':None,
            'reviewProvenance':item.get('review_provenance'), 'qaNote':item.get('qa_note'),
            'privacyEvidenceSha':item.get('privacy_clearance_sha256'),
            'semanticEvidenceSha':item.get('semantic_evidence_sha256')})
    write(out/'toss-v6/release-provenance.json', {'schemaVersion':1,'access':'owner-private',
        'releaseIndexSha256':release_sha,'sourceReleaseScope':release['release_scope'],
        'integrationAdmission':'Authorized internal owner-private use of 101 exact independently approved masked copies',
        'sourceFiles':{'classificationSha256':sha(toss_source/'deliverables/토스-v6-101장-분류검토.csv'),
            'buttonPhrasesSha256':sha(toss_source/'deliverables/토스-v6-검수된-버튼문구.csv'),
            'fileAffinitySha256':sha(toss_source/'deliverables/토스-v6-파일순서-유사구간43.csv')},
        'usableBlindOutputCount':95,'nativeOnlyNoUsableBlindOutputCount':6,
        'maskedValuesReconstructed':False,'canonicalFinancialAdmissions':0,'items':approved_toss,
        'sequenceGroups':sequence_groups})
    for p in providers.values():
        p['screenCount'] = sum(s['providerId']==p['id'] for s in screens)
        p['phraseCount'] = sum(s['providerId']==p['id'] for s in phrases)
        p['featureCount'] = len({s['workId'] for s in features if s['providerId']==p['id']})
        p['countries'].sort()
    crosswalk = read(ROOT/'data/integration-navigation-crosswalk.json')
    navigation = {r['screenId']:r for r in crosswalk['items']}
    known_tasks = {t['id'] for t in tasks if t['groupId'] != 'toss-v6-editorial'}
    for screen in screens:
        if screen['id'] not in navigation: continue
        row = navigation[screen['id']]
        assert row['imageSha256'] == screen['originalSha']
        assert set(row['taskIds']) <= known_tasks
        screen['navigationTaskIds'] = row['taskIds']
        screen['navigationMappingScope'] = 'search-and-browse-only'
        screen['navigationMappingBasis'] = row['basis']
    for phrase in phrases:
        related = [navigation[sid] for sid in phrase['screenIds'] if sid in navigation]
        if related:
            phrase['navigationTaskIds'] = sorted({tid for r in related for tid in r['taskIds']})
            phrase['navigationMappingScope'] = 'search-and-browse-only'
    for t in tasks:
        t['screenCount'] = sum(t['id'] in [s['taskId']]+s.get('navigationTaskIds',[]) for s in screens)
        t['featureCount'] = len({s['referenceId'] for s in features if t['id'] in s['taskIds']})
    counts = {'screens': len(screens), 'uniqueImages': len({s['originalSha'] for s in screens}),
        'flows': len(flows), 'phrases': len(phrases), 'canonicalWorks': len(works),
        'canonicalReferences': len(admitted), 'featureRows': len(features),
        'documentedWorks': len({f['workId'] for f in features}), 'providers': len(providers),
        'dictionaryCore': len(base_rows), 'dictionaryConditional': len(all_rows)-len(base_rows),
        'dictionaryTotal': len(all_rows), 'dictionaryLanguages': 47, 'dictionaryDatasets': len(datasets),
        'dictionaryCoreDatasets': 12, 'dictionaryConditionalDatasets': 3,
        'unknownScreenCountries': sum(s['country'] is None for s in screens),
        'legacyScreens':82,'legacyUniqueImages':74,'legacyPhrases':301,
        'tossScreens':101,'tossUniqueImages':len({s['maskedSha256'] for s in approved_toss}),
        'tossNativePhrases':435,'tossEditorialGroups':43,'tossUsableBlindOutputs':95,'tossNativeOnlyOutputs':6}
    assert (counts['screens'], counts['uniqueImages'], counts['flows'], counts['phrases']) == (183,175,39,736)
    languages = [{'id': k, 'label': v} for k,v in dictionary['languages'].items()]
    country_ids = sorted({p['country'] for p in screens+phrases+features if p.get('country')})
    catalog = {'schemaVersion': 1, 'builtFrom': 'frozen-existing-admitted-data', 'counts': counts,
        'tasks': tasks, 'taskGroups': tasks_raw['groups'], 'providers': sorted(providers.values(), key=lambda p:p['name']),
        'countries': [{'id': c, 'label': COUNTRIES.get(c,c)} for c in country_ids], 'languages': languages,
        'screens': screens, 'flows': flows, 'sequenceGroups':sequence_groups, 'phrases': phrases, 'features': features,
        'canonicalWorks': [{'id': w['id'], 'label': w['title'], 'definition': w['definition'],
            'domainId': w['domain_id'], 'aliases': w.get('aliases', []), 'actorRole': w.get('actor_role'),
            'objectKey': w.get('object_key'), 'outcomeKey': w.get('outcome_key')} for w in works.values()],
        'dictionary': {'release': dictionary['release_ref'], 'datasets': datasets, 'chunks': chunks,
            'languages': languages, 'defaultLayer': 'core', 'conditionalRequiresOptIn': True,
            'downloads': dictionary['downloads'], 'sourceInventoryPath': '/integration-data/source-inventory.json'},
        'policies': {'globalMeceApproved': False, 'featureAbsence': 'unknown',
            'countryUnknown': 'null; never inferred from language', 'aliases': 'navigation_only',
            'comparison': 'Require known matching task, purpose and stage; inspect requested field objects separately.',
            'termLinks': 'No automatic phrase-to-term equivalence; text search results are discovery candidates.',
            'tossImport': '101 exact independently reviewed masked v6 copies; owner-private only. Original URL/capture date/version/operator unknown. File-affinity groups are not observed flows.',
            'newCollection': False, 'currentUiVersionVerified': False}}
    write(out / 'catalog.json', catalog)
    write(out / 'build-manifest.json', {'schemaVersion': 1, 'inputs': [
        {'path': str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p.relative_to(source) if p.is_relative_to(source) else p.relative_to(toss_source)),
         'root': 'repository' if p.is_relative_to(ROOT) else ('integration-source' if p.is_relative_to(source) else 'toss-v6-source'), 'sha256': sha(p)} for p in sorted(set(inputs))],
        'catalogSha256': sha(out/'catalog.json'), 'counts': counts,
        'generatedFiles': ['catalog.json','source-inventory.json','toss-v6/release-provenance.json']+
            [s['imagePath'].removeprefix('/integration-data/') for s in approved_toss]+
            [path.removeprefix('/integration-data/') for c in chunks for path in [c['path'],c['provenancePath']]]})
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    print(f'{len(chunks)} dictionary chunks; catalogue {len(encoded(catalog)):,} bytes')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=pathlib.Path, default=DEFAULT_INPUT)
    parser.add_argument('--dist-root', type=pathlib.Path, default=ROOT/'dist')
    parser.add_argument('--output', type=pathlib.Path, default=ROOT/'integration-data')
    parser.add_argument('--toss-source', type=pathlib.Path, default=pathlib.Path('/home/ubuntu/wgss-toss-reclassification-v6'))
    args = parser.parse_args()
    build(args.source_root, args.dist_root, args.output, args.toss_source)
