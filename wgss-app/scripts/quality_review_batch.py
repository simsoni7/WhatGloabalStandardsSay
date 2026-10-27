"""Source-search and independent Bedrock quality agents for automatic publication.

Signed server operations preserve the ordinary publication transaction, history,
rights gate and image integrity checks. Uncertain material stays in human review.
"""
from __future__ import annotations
import argparse
import base64
import datetime as dt
import fcntl
import hashlib
import hmac
import html
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collection_batch import (Bedrock, Store, CheckedRedirect, USER_AGENT, atomic_json, digest,
                              fetch_bytes, norm, now, pair_key, safe_error, extract_ofbiz_pairs, proposal)


class ReviewModel(Bedrock):
    def call(self, *args, **kwargs):
        for attempt in range(2):
            try:
                return super().call(*args, **kwargs)
            except (urllib.error.HTTPError, json.JSONDecodeError, TimeoutError) as error:
                if attempt or isinstance(error, urllib.error.HTTPError) and error.code not in {429, 500, 502, 503, 504}:
                    raise
                time.sleep(2)


def signed_api(api, secret, payload=None, resource=None):
    url = api + ('?resource=' + resource if resource else '')
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode() if payload is not None else b''
    method = 'POST' if payload is not None else 'GET'
    parsed = urllib.parse.urlsplit(url)
    timestamp = str(int(time.time()))
    message = '\n'.join(['wgss-quality-v1', timestamp, method, parsed.path + ('?' + parsed.query if parsed.query else ''), body.decode()])
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    request = urllib.request.Request(url, data=body if method == 'POST' else None, headers={
        'User-Agent': USER_AGENT, 'Content-Type': 'application/json',
        'X-WGSS-Automation-Timestamp': timestamp, 'X-WGSS-Automation-Signature': signature})
    with urllib.request.build_opener(CheckedRedirect([])).open(request, timeout=90) as response:
        return json.loads(response.read(4 * 1024 * 1024))


class SourceSearchAgent:
    """Retrieve exact official originals and Korean dictionary matches before AI."""
    def __init__(self, app_root, cache):
        self.app_root, self.cache = app_root, cache
        cache.mkdir(parents=True, exist_ok=True)
        self.korean = {}
        self.catalog = json.loads((app_root / 'integration-data/catalog.json').read_text())
        allowed = {x['id'] for x in self.catalog['dictionary']['datasets'] if x.get('commercial') and x.get('layer') == 'core'}
        for chunk in self.catalog['dictionary']['chunks']:
            for row in json.loads((app_root / chunk['path'].lstrip('/')).read_text())['rows']:
                if row.get('datasetId') not in allowed:
                    continue
                if row.get('language') == 'ko' and row.get('target'):
                    self.korean.setdefault(norm(row['english']).casefold(), []).append({'korean': row['target'], 'url': row['sourceUrl'], 'sha256': digest(row), 'kind': 'existing_original_korean_row'})

    def read(self, url, expected=None):
        path = self.cache / (digest(url) + '.bin')
        raw = path.read_bytes() if path.exists() else fetch_bytes(url, ['raw.githubusercontent.com'])
        if expected and digest(raw) != expected:
            raise ValueError('source_hash_mismatch')
        if not path.exists():
            path.write_bytes(raw)
        return raw

    def currency_name_search(self, code):
        """Search an official bank's currency-code table; never ingest exchange rates."""
        url='https://obank.kbstar.com/quics?page=C101423'
        path=self.cache/'kb-currency-names.html'
        raw=path.read_bytes() if path.exists() else fetch_bytes(url,['obank.kbstar.com'])
        if not path.exists():path.write_bytes(raw)
        for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',raw.decode('utf-8','replace'),re.S|re.I):
            cells=[norm(html.unescape(re.sub('<[^>]+>',' ',x))) for x in re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S|re.I)]
            if len(cells)>1 and cells[0]==code and re.search('[가-힣]',cells[1]) and not re.search(r'\d',cells[1]):
                name=norm(cells[1].replace('(',' ').replace(')',''))
                return {'korean':name,'url':url,'sha256':digest(raw),'kind':'official_bank_currency_code_label'}
        return None

    def material(self, payload):
        url = payload['sourceUrl']
        u = urllib.parse.urlsplit(url)
        if u.hostname != 'raw.githubusercontent.com' or not re.fullmatch(r'/(unicode-org/cldr-json|apache/ofbiz-framework)/[0-9a-f]{40}/.+', u.path):
            raise ValueError('source_requires_operator_review')
        raw = self.read(url, payload.get('sourceSha256'))
        english_raw = self.read(payload['englishSourceUrl'], payload.get('englishSourceSha256'))
        license_raw = self.read(payload['licenseUrl'], payload.get('licenseSha256'))
        evidence = [{'url': url, 'sha256': digest(raw), 'kind': 'exact_source'},
                    {'url': payload['englishSourceUrl'], 'sha256': digest(english_raw), 'kind': 'english_source'},
                    {'url': payload['licenseUrl'], 'sha256': digest(license_raw), 'kind': 'license'}]
        source_korean,alternate_korean = None,None
        if payload['license'] == 'Unicode-3.0' and '/unicode-org/cldr-json/' in url:
            if not license_raw.startswith(b'UNICODE LICENSE V3'):
                raise ValueError('license_not_verified')
            code, language = payload['code'], payload['language']
            observed_target = json.loads(raw)['main'][language]['numbers']['currencies'][code]['displayName']
            observed_english = json.loads(english_raw)['main']['en']['numbers']['currencies'][code]['displayName']
            korean_url = re.sub(r'/main/[^/]+/currencies.json$', '/main/ko/currencies.json', url)
            korean_raw = self.read(korean_url)
            korean = json.loads(korean_raw)['main']['ko']['numbers']['currencies'][code]['displayName']
            source_korean = {'korean': korean, 'url': korean_url, 'sha256': digest(korean_raw), 'kind': 'same_currency_code_korean'}
            try:
                bank_name=self.currency_name_search(code)
                if bank_name and norm(bank_name['korean'])!=norm(korean):alternate_korean=bank_name
            except Exception:
                pass  # The primary source remains usable; absence is not invented evidence.
        elif payload['license'] == 'Apache-2.0' and '/apache/ofbiz-framework/' in url:
            if b'Apache License' not in license_raw or b'Version 2.0' not in license_raw:
                raise ValueError('license_not_verified')
            found = [x for x in extract_ofbiz_pairs(raw, [payload['language']])[payload['language']] if x['code'] == payload['code']]
            if len(found) != 1:
                raise ValueError('source_key_mismatch')
            observed_english, observed_target = found[0]['english'], found[0]['target']
            base = url.split('/applications/')[0]
            notice_url = base + '/NOTICE'
            notice = self.read(notice_url, payload.get('noticeSha256'))
            evidence.append({'url': notice_url, 'sha256': digest(notice), 'kind': 'attribution_notice'})
        else:
            raise ValueError('license_not_verified')
        if norm(observed_english) != norm(payload['english']) or norm(observed_target) != norm(payload['target']):
            raise ValueError('source_pair_mismatch')
        matches = self.korean.get(norm(payload['english']).casefold(), [])
        if not source_korean and matches and len({norm(x['korean']) for x in matches}) == 1:
            source_korean = matches[0]
        if source_korean:
            evidence.append({k: v for k, v in source_korean.items() if k != 'korean'})
        if alternate_korean:
            evidence.append({k:v for k,v in alternate_korean.items() if k!='korean'})
        return {'payload': payload, 'evidence': evidence, 'sourceKorean': source_korean,
                'alternateKorean':alternate_korean,'koreanCandidates': matches[:4], 'licenseVerified': True, 'sourcePairVerified': True}


def complete_korean(materials, model):
    missing = []
    for item in materials:
        supplied = (item.get('item') or {}).get('current', {}).get('termKorean', '').strip()
        alternate=item.get('alternateKorean')
        if alternate and (not supplied or norm(supplied)==norm((item['sourceKorean'] or {}).get('korean',''))):
            missing.append(item)
        elif supplied:
            item['korean'] = supplied
            item['koreanBasis'] = 'source_korean_reused' if item['sourceKorean'] and norm(supplied) == norm(item['sourceKorean']['korean']) else 'ai_quality_reviewed'
        elif item['sourceKorean']:
            item['korean'] = item['sourceKorean']['korean']
            item['koreanBasis'] = 'source_korean_reused'
        else:
            missing.append(item)
    if missing:
        rows = [{'key': x['key'], 'english': x['payload']['english'], 'target': x['payload']['target'], 'language': x['payload']['language'], 'source': x['payload'].get('sourceName'), 'retrievedKoreanCandidates': [v for v in [x.get('sourceKorean'),x.get('alternateKorean')]+x['koreanCandidates'] if v]} for x in missing]
        raw = model.call('''You are the Korean explanation research agent. Official original pairs and retrieved Korean dictionary matches are below. Prefer an exact applicable retrieved original. Otherwise write a concise Korean financial UI explanation based strictly on the original English and target context; it is AI-authored and will undergo independent review. Do not invent definitions, banking availability or source citations. If meaning is genuinely ambiguous return korean="". Keep complete sentence instructions as sentences. Return JSON {"rows":[{"key":"exact key","korean":"Korean explanation"}]} for every key exactly once. Evidence:\n''' + json.dumps(rows, ensure_ascii=False), max_tokens=7000)
        by_key = covered_rows(raw, rows)
        for item in missing:
            item['korean'] = str(by_key[item['key']].get('korean', '')).strip()[:1000]
            item['koreanBasis'] = 'ai_quality_reviewed'
            for source in [item.get('sourceKorean'),item.get('alternateKorean')]+item['koreanCandidates']:
                if source and norm(source['korean'])==norm(item['korean']):
                    item['sourceKorean']=source;item['koreanBasis']='source_korean_reused';break
    return materials


def covered_rows(raw, rows):
    values = raw.get('rows') if isinstance(raw, dict) else None
    if not isinstance(values, list) or len(values) != len(rows) or any(not isinstance(v, dict) for v in values):
        raise ValueError('quality_key_coverage')
    found = {x.get('key'): x for x in values}
    if len(found) != len(rows) or set(found) != {x['key'] for x in rows}:
        raise ValueError('quality_key_coverage')
    return found


def approve_decision(row):
    return (row.get('decision') == 'approve' and isinstance(row.get('confidence'), (int, float))
            and not isinstance(row['confidence'], bool) and .95 <= row['confidence'] <= 1
            and all(row.get(x) is True for x in ['pairAccurate', 'koreanAccurate', 'financeRelevant', 'privacyClear', 'readable']))


def quality_terms(materials, model):
    rows = [{'key': x['key'], 'english': x['payload']['english'], 'target': x['payload']['target'], 'language': x['payload']['language'],
             'korean': x['korean'], 'koreanBasis': x['koreanBasis'], 'sourceKorean': x['sourceKorean'],
             'context': x['payload'].get('sourceName'), 'sourcePairVerified': x['sourcePairVerified'], 'licenseVerified': x['licenseVerified']} for x in materials]
    raw = model.call('''You are the independent financial-language quality reviewer, separate from the collection and Korean explanation agents. Evidence was fetched and exact source keys/hashes/rights verified by code. Judge the actual original pairing, Korean explanation, financial relevance and readability. Simple exact currency names, accounting labels and clear instructions may pass automatically. Do not require human review merely because AI produced the Korean explanation; verify its actual meaning. Hold ambiguous meanings, mismatches, garbling, private data or incomplete Korean. Never rewrite originals or invent sources. Return ONLY {"rows":[{"key":"exact key","decision":"approve|hold","confidence":0.0,"pairAccurate":true,"koreanAccurate":true,"financeRelevant":true,"privacyClear":true,"readable":true,"reason":"concise Korean reason"}]}, exactly one per key. Approval requires every boolean true and confidence >=0.95. Evidence:\n''' + json.dumps(rows, ensure_ascii=False), max_tokens=9000)
    return covered_rows(raw, rows)


def term_application(item):
    p = item['payload']
    return {'type': 'terms', 'operation': 'add', 'expectedRevision': 0, 'imageFileIds': [],
            'fields': {'english': p['english'], 'target': p['target'], 'language': p['language'], 'korean': item['korean'],
                       'definition': item['korean'], 'sourceUrl': p['sourceUrl']},
            'commercialRights': {'confirmed': True, 'license': p['license'], 'evidenceUrl': p['licenseUrl'],
                                 'basis': f'공식 저장소의 고정 버전 {p["revision"]} 원문과 LICENSE를 조회하고 파일 해시를 확인했습니다. 원출처와 이용 조건 고지를 보존합니다.'}}


def public_api(api, resource):
    request = urllib.request.Request(api + '?' + resource, headers={'User-Agent': USER_AGENT, 'Origin': 'https://3.36.58.188'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read(8 * 1024 * 1024))


def process_screens(items, search, model, api, secret, report, limit, store=None):
    providers = public_api(api, 'resource=providers')['items']
    allowed_providers = [{'id': x['id'], 'name': x['name']} for x in providers]
    tasks = [{'id': x['id'], 'label': x['label']} for x in search.catalog['tasks'] if x.get('groupId') != 'toss-v6-editorial']
    languages = {x['id'] for x in search.catalog['languages']}
    for item in [x for x in items if x['kind'] == 'screen'][:limit]:
        hold_reason = '이미지의 개인정보·내용·분류를 확정하지 못했습니다. 담당자 확인이 필요합니다.'
        try:
            files = [x for x in item['files'] if x['role'] == 'masked']
            if not files:
                hold_reason='첨부 사진이 없어 화면과 문구를 확인할 수 없습니다.'
                raise ValueError('screen_image_missing')
            if len(files) > 3 or not (re.fullmatch('intake-[0-9a-f]{64}', item['id']) or item.get('privacyReviewed')):
                raise ValueError('privacy_or_image_scope_requires_review')
            photos, evidence = [], []
            for file in files:
                url = api + '?resource=file&id=' + urllib.parse.quote(file['id'])
                raw = fetch_bytes(url, [urllib.parse.urlsplit(api).hostname], 8 * 1024 * 1024)
                if digest(raw) != file['sha256'] or file['mime'] not in {'image/png','image/jpeg','image/webp'}:
                    raise ValueError('image_requires_operator_review')
                prompt = '''Inspect this exact masked screenshot and contributor comment as evidence. Return JSON {"title":"visible heading or concise title","providerId":"allowed ID or empty","language":"BCP47","taskId":"allowed ID or empty","purpose":"Korean explanation","phrases":["exact visible UI phrase"],"privacyClear":true/false,"readable":true/false,"uncertain":true/false}. Do not accept cookie/challenge/error-only images or infer banking completion. Personal names, account identifiers/balances must be absent. Preserve original visible wording. If confident, use known company/service/task and language. Do not infer screen language from the comment language. Comment: ''' + json.dumps(item['current'], ensure_ascii=False) + '\nCompanies: ' + json.dumps(allowed_providers, ensure_ascii=False) + '\nTasks: ' + json.dumps(tasks, ensure_ascii=False)
                draft = model.call(prompt, raw, max_tokens=5000)
                review = model.call('''Independently verify this screenshot metadata and OCR draft. Return ONLY {"decision":"approve|hold","confidence":0.0,"pairAccurate":true,"koreanAccurate":true,"financeRelevant":true,"privacyClear":true,"readable":true,"reason":"Korean reason"}. Require correct visible original phrases, company/language/task, useful specific UI and no private information. A dimming cookie overlay, challenge, illegibility or ambiguity means hold. Confidence >=0.95 and all checks true are required to publish. Draft:\n''' + json.dumps(draft, ensure_ascii=False), raw, max_tokens=1800)
                if not approve_decision(review) or draft.get('privacyClear') is not True or draft.get('readable') is not True or draft.get('uncertain') is not False:
                    hold_reason = str(review.get('reason') or hold_reason)[:1400]
                    raise ValueError('screen_quality_uncertain')
                if draft.get('providerId') not in {x['id'] for x in providers} or draft.get('taskId') not in {x['id'] for x in tasks} or draft.get('language') not in languages:
                    raise ValueError('screen_identity_uncertain')
                phrases = list(dict.fromkeys(x.strip() for x in draft.get('phrases', []) if isinstance(x, str) and 1 < len(x.strip()) <= 1000))[:40]
                if not phrases or not draft.get('title') or not draft.get('purpose'):
                    raise ValueError('screen_metadata_incomplete')
                photos.append({'fileId': file['id'], 'fields': {'title': draft['title'][:250], 'providerId': draft['providerId'], 'language': draft['language'], 'taskId': draft['taskId'], 'purpose': draft['purpose'][:1000], 'stageLabel': draft['purpose'][:1000], 'capturedAt': item['current'].get('capturedAt') or file['createdAt'][:10], 'captureDateBasis': 'provided' if item['current'].get('capturedAt') else 'upload', 'sourceUrl': item['current'].get('sourceUrl', '')}, 'phrases': [{'text': x, 'role': 'ui_label'} for x in phrases]})
                evidence.append({'url': url, 'sha256': file['sha256'], 'kind': 'exact_masked_image'})
            target = item['current'].get('referenceId')
            revision = 0
            if target:
                histories = public_api(api, 'resource=recordVersions&type=screens&id=' + urllib.parse.quote(target))['items']
                revision = max((x['revision'] for x in histories), default=0)
            application = {'type': 'screens', 'operation': 'update' if target else 'add', 'targetId': target or '', 'expectedRevision': revision,
                           'fields': {'sourceUrl': item['current'].get('sourceUrl', '')}, 'imageFileIds': [x['id'] for x in files], 'photos': photos}
            signed_api(api, secret, {'action': 'applyAutomaticReview', 'id': item['id'], 'expectedVersion': item['version'], 'maskedFileIds': [x['id'] for x in files], 'application': application,
                                     'quality': {'model': model.model, 'decision': 'approve', 'confidence': review['confidence'], 'privacyClear': True, 'readable': True, 'evidence': evidence}})
            report['screensPublished'] += len(files)
            if store:
                store.db.execute("UPDATE candidates SET status='published' WHERE submission_id=?",(item['id'],));store.db.commit()
        except Exception as error:
            report['held'].append({'id': item['id'], 'code': safe_error(error)})
            if isinstance(error, ValueError):
                signed_api(api, secret, {'action': 'deferAutomaticReview', 'id': item['id'], 'expectedVersion': item['version'], 'reason': '자동 검수 보류: '+hold_reason+' (' + safe_error(error) + ')'})


def run_quality(app_root, state_dir, api, secret, max_terms=40, max_calls=24, max_screens=2,retry_held=False):
    with (state_dir / 'quality.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {'status': 'already_running'}
        store = Store(state_dir / 'collection.sqlite')
        model = ReviewModel(secret, 'claude-sonnet-5', max_calls)
        search = SourceSearchAgent(app_root, state_dir / 'quality-sources')
        report = {'startedAt': now(), 'status': 'running', 'termsPublished': 0, 'screensPublished': 0, 'held': [], 'errors': []}
        queue = signed_api(api, secret, resource='automaticQueue')['items']
        live = {x['id']: x for x in queue}
        # Existing public/manual decisions are authoritative. Never revise an approved,
        # rejected, or edited source solely because an old local row is still queued.
        public_items = public_api(api, 'resource=submissions')['items']
        all_live = {x['id']: x for x in public_items}
        statuses="('staged','submitted','needs_review')" if retry_held else "('staged','submitted')"
        rows = store.db.execute("SELECT * FROM candidates WHERE kind='term' AND status IN "+statuses+" ORDER BY created_at,key").fetchall()
        materials = []
        for row in rows:
            if len(materials) >= max_terms:
                break
            payload = json.loads(row['payload'])
            item = live.get(row['submission_id'])
            if row['submission_id'] and not item:
                known = all_live.get(row['submission_id'])
                if known and known['status'] == 'approved':
                    store.db.execute("UPDATE candidates SET status='published' WHERE key=?", (row['key'],));store.db.commit()
                continue
            if item and (norm(item['current'].get('termEnglish')) != norm(payload['english']) or norm(item['current'].get('termTarget')) != norm(payload['target']) or item['current'].get('sourceUrl') != payload['sourceUrl'] or item['current'].get('language') != payload['language']):
                report['held'].append({'id': item['id'], 'code': 'edited_source_requires_review'})
                continue
            try:
                material = search.material(payload)
                material.update(key=row['key'], row=dict(row), item=item)
                materials.append(material)
            except Exception as error:
                report['held'].append({'id': row['submission_id'], 'code': safe_error(error)})
        for start in range(0, len(materials), 20):
            batch = materials[start:start + 20]
            try:
                complete_korean(batch, model)
                decisions = quality_terms(batch, model)
                for material in batch:
                    decision = decisions[material['key']]
                    row, payload, item = material['row'], material['payload'], material['item']
                    if not material['korean'] or not approve_decision(decision):
                        report['held'].append({'id': row['submission_id'], 'code': 'quality_uncertain', 'reason': decision.get('reason', '')})
                        if not item:
                            submitted = proposal(payload, 'term')
                            submitted.update(action='ingestAutomaticTerm', candidateKey=row['key'].split(':', 1)[1], termKorean=material['korean'])
                            item = signed_api(api, secret, submitted)['item']
                        signed_api(api, secret, {'action': 'deferAutomaticReview', 'id': item['id'], 'expectedVersion': item['version'], 'reason': '자동 검수 보류: ' + str(decision.get('reason') or '원문 대응이나 한국어 설명을 확정하지 못했습니다.')[:1500]})
                        store.db.execute("UPDATE candidates SET status='needs_review',submission_id=? WHERE key=?", (item['id'], row['key']));store.db.commit()
                        continue
                    payload['korean'] = material['korean']
                    if not item:
                        submitted = proposal(payload, 'term')
                        submitted.update(action='ingestAutomaticTerm', candidateKey=row['key'].split(':', 1)[1], termKorean=material['korean'])
                        item = signed_api(api, secret, submitted)['item']
                        store.db.execute("UPDATE candidates SET status='submitted',submission_id=?,submitted_at=? WHERE key=?", (item['id'], now(), row['key']));store.db.commit()
                    if item['status'] == 'approved':
                        store.db.execute("UPDATE candidates SET status='published' WHERE key=?", (row['key'],));store.db.commit()
                        continue
                    quality = {'model': model.model, 'decision': 'approve', 'confidence': decision['confidence'], 'privacyClear': True, 'readable': True,
                               'evidence': material['evidence'], 'koreanBasis': material['koreanBasis'], 'koreanSourceUrl': (material['sourceKorean'] or {}).get('url')}
                    signed_api(api, secret, {'action': 'applyAutomaticReview', 'id': item['id'], 'expectedVersion': item['version'], 'maskedFileIds': [], 'application': term_application(material), 'quality': quality})
                    store.db.execute("UPDATE candidates SET status='published',payload=?,error=NULL WHERE key=?", (json.dumps(payload, ensure_ascii=False), row['key']));store.db.commit()
                    report['termsPublished'] += 1
                    print(json.dumps({'qualityPublished': payload['code'], 'language': payload['language'], 'korean': material['korean']}, ensure_ascii=False), flush=True)
            except Exception as error:
                report['errors'].append({'stage': 'term_batch', 'code': safe_error(error)})
        process_screens(queue, search, model, api, secret, report, max_screens,store)
        report.update(completedAt=now(), status='partial' if report['errors'] else 'completed', bedrock={'attempted': model.calls, 'completed': model.succeeded, 'tokens': model.tokens}, queue=store.counts())
        atomic_json(state_dir / 'quality-latest.json', report)
        atomic_json(state_dir / 'quality-runs' / (report['startedAt'].replace(':', '-') + '.json'), report)
        return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--max-terms', type=int, default=40)
    parser.add_argument('--max-calls', type=int, default=24)
    parser.add_argument('--retry-held',action='store_true')
    args = parser.parse_args()
    credential = Path(os.environ.get('CREDENTIALS_DIRECTORY', '/nonexistent')) / 'bedrock-api-key'
    secret = credential.read_text().strip() if credential.exists() else os.environ['BEDROCK_API_KEY']
    print(json.dumps(run_quality(args.app_root, args.state_dir, 'https://wgss-public-intake.booknfoto461.chatgpt.site/api/wgss', secret, args.max_terms, args.max_calls,retry_held=args.retry_held), ensure_ascii=False))
