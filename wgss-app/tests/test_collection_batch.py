"""Collection correctness, evidence boundaries, queue recovery and replay tests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('collector', Path(__file__).resolve().parents[1] / 'scripts/collection_batch.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class CollectionTests(unittest.TestCase):
    def test_no_local_or_credential_urls(self):
        for url in ['http://example.com', 'https://user:secret@example.com', 'https://example.com:8443/', 'https://example.com/?access_token=secret', 'https://example.com/?state=xyz']:
            self.assertFalse(c.public_url_shape(url), url)
        with patch.object(c.socket, 'getaddrinfo', return_value=[(0, 0, 0, '', ('127.0.0.1', 443))]):
            self.assertFalse(c.public_url('https://example.com'))

    def test_exact_domain_boundary(self):
        self.assertTrue(c.public_url_shape('https://login.bank.test/x', ['bank.test']))
        self.assertFalse(c.public_url_shape('https://bank.test.attacker.test/x', ['bank.test']))
        self.assertFalse(c.public_url_shape('https://notbank.test/x', ['bank.test']))

    def test_only_original_pairs_survive(self):
        rows = [{'key': 'ko:USD', 'language': 'ko', 'english': 'US Dollar', 'target': '미국 달러'}]
        result = c.validate_pairs({'rows': [{'key': 'ko:USD', 'include': True, 'risk': 'none', 'target': 'invented'}]}, rows)
        self.assertEqual(result, rows)

    def test_pair_key_coverage_and_typed_decisions(self):
        rows = [{'key': 'a'}, {'key': 'b'}]
        for result in [{'rows': [{'key': 'a'}, {'key': 'a'}]}, {'rows': [{'key': 'a'}]}, {'rows': ['a', 'b']}]:
            with self.assertRaises(ValueError):
                c.validate_pairs(result, rows)
        self.assertEqual(c.validate_pairs({'rows': [{'key': 'a', 'include': 'true', 'risk': 'none'}, {'key': 'b', 'include': True, 'risk': 'alignment'}]}, rows), [])

    def test_active_tender_only(self):
        data = {'supplemental': {'currencyData': {'region': {'XX': [{'USD': {'_from': '1900-01-01'}}, {'OLD': {'_to': '1999-01-01'}}, {'XXX': {'_tender': 'false'}}, {'FUT': {'_from': '2100-01-01'}}]}}}}
        self.assertEqual(c.active_currencies(data, '2026-10-24'), {'USD'})

    def test_exact_explicit_source_key_alignment(self):
        en = {'main': {'en': {'numbers': {'currencies': {'USD': {'displayName': 'US Dollar'}, 'EUR': {'displayName': 'Euro'}}}}}}
        ko = {'main': {'ko': {'numbers': {'currencies': {'USD': {'displayName': '미국 달러'}, 'BAD': {'displayName': 'wrong'}}}}}}
        result = c.extract_currency_pairs(en, ko, 'ko', {'USD', 'EUR', 'BAD'})
        self.assertEqual([r['key'] for r in result], ['ko:USD'])

    def test_ofbiz_uses_exact_xml_key_and_preserves_original_locale(self):
        raw = '''<resource><property key="AccountBalance"><value xml:lang="en">Account balance</value><value xml:lang="hi-IN">खाते में शेष</value></property><property key="Generic"><value xml:lang="en">Close</value><value xml:lang="hi-IN">बंद</value></property></resource>'''.encode()
        result = c.extract_ofbiz_pairs(raw, ['hi', 'ko'])
        self.assertEqual(result['hi'][0]['english'], 'Account balance')
        self.assertEqual(result['hi'][0]['sourceLanguage'], 'hi-IN')
        self.assertEqual(len(result['hi']), 1)
        self.assertEqual(result['ko'], [])

    def test_term_queue_balances_languages(self):
        with tempfile.TemporaryDirectory() as directory:
            db = c.Store(Path(directory) / 'state.sqlite')
            for key, language in [('a', 'ko'), ('b', 'ko'), ('c', 'ko'), ('d', 'ja'), ('e', 'ja')]:
                db.add(key, 'term', {'language': language})
            self.assertEqual([json.loads(row['payload'])['language'] for row in db.pending('term', 4)], ['ko', 'ja', 'ko', 'ja'])

    def test_published_image_is_skipped_before_model_or_proposal(self):
        evidence = {'sourceUrl': 'https://example.com', 'visibleText': 'Sign in', 'imageSha256': 'already-published'}
        with patch.object(c, 'capture', return_value=evidence):
            model = unittest.mock.Mock()
            result = c.research_screen({}, Path('/unused'), model, [], set(), {'already-published'})
            self.assertEqual(result[0]['status'], 'unchanged')
            model.call.assert_not_called()

    def test_recent_delivery_limit_preserves_interactive_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            db = c.Store(Path(directory) / 'state.sqlite')
            for i in range(10):
                db.add(str(i), 'term', {'language': 'ko'})
            db.db.execute("UPDATE candidates SET status='submitted',submission_id=key,submitted_at=? WHERE key<>'9'", (c.now(),));db.db.commit()
            with patch.object(c, 'api_request') as api:
                result = c.deliver(db, 'https://example.com', {'term': 6, 'screen': 2})
                self.assertTrue(result['deferredByHourlyBudget'])
                api.assert_not_called()

    def test_screenshot_phrases_must_exist_in_viewport_text(self):
        raw = {'usable': True, 'containsPersonalData': False, 'overlayObscuresContent': False, 'kind': 'blank_form', 'title': 'Sign in', 'purpose': '로그인', 'language': 'en', 'taskId': 'login', 'phrases': ['Sign in', 'Forgot password', 'not in screenshot']}
        evidence = {'visibleText': 'Sign in\nForgot password', 'sourceUrl': 'https://example.com', 'links': []}
        result = c.validate_screen(raw, evidence, {'login'})
        self.assertEqual(result['phrases'], ['Sign in', 'Forgot password'])
        self.assertNotIn('visibleText', result)
        for key, value in [('containsPersonalData', True), ('containsPersonalData', None), ('overlayObscuresContent', True), ('overlayObscuresContent', None), ('usable', 'true'), ('kind', 'marketing'), ('taskId', 'invented')]:
            self.assertIsNone(c.validate_screen({**raw, key: value}, evidence, {'login'}))

    def test_queue_deduplicates_and_persists_capability_for_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            db = c.Store(Path(directory) / 'state.sqlite')
            self.assertTrue(db.add('a', 'term', {'a': 1}))
            before = dict(db.pending('term', 1)[0])
            self.assertFalse(db.add('a', 'term', {'a': 2}))
            after = dict(db.pending('term', 1)[0])
            self.assertEqual(before, after)
            self.assertEqual(db.counts(), {'term:staged': 1})

    def test_delivery_network_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            db = c.Store(Path(directory) / 'state.sqlite')
            db.add('a', 'term', {'english': 'US Dollar', 'target': '미국 달러', 'language': 'ko', 'sourceUrl': 'https://example.com', 'code': 'USD', 'revision': 'abc', 'englishSourceUrl': 'https://example.com/en', 'licenseUrl': 'https://example.com/LICENSE'})
            row = dict(db.pending('term', 1)[0])
            with patch.object(c, 'api_request', side_effect=TimeoutError()):
                self.assertEqual(len(c.deliver(db, 'https://example.com', {'term': 1, 'screen': 0})['errors']), 1)
            with patch.object(c, 'api_request', return_value={'item': {'id': 'existing-id'}, 'reused': True}) as api:
                self.assertEqual(c.deliver(db, 'https://example.com', {'term': 1, 'screen': 0})['term'], 1)
                self.assertEqual(api.call_args.args[1], row['token'])
            self.assertEqual(db.pending('term', 1), [])

    def test_image_upload_retry_uses_same_file_id(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'x.png'; image.write_bytes(b'actual-image-bytes')
            db = c.Store(Path(directory) / 'state.sqlite')
            payload = {'provider': 'A', 'providerId': '', 'title': 'Sign in', 'taskId': 'login', 'purpose': '로그인', 'phrases': ['Sign in'], 'sourceUrl': 'https://example.com', 'language': 'en', 'capturedAt': '2026-10-24', 'image': str(image), 'imageSha256': c.digest(image.read_bytes())}
            db.add('a', 'screen', payload)
            row = dict(db.pending('screen', 1)[0])
            with patch.object(c, 'api_request', side_effect=[{'item': {'id': 'same'}}, TimeoutError()]):
                c.deliver(db, 'https://example.com', {'term': 0, 'screen': 1})
            with patch.object(c, 'api_request', return_value={'item': {'id': 'same'}}) as api:
                self.assertEqual(c.deliver(db, 'https://example.com', {'term': 0, 'screen': 1})['screen'], 1)
                self.assertIn(row['file_id'].encode(), api.call_args.args[2])

    def test_errors_never_include_secrets_or_upstream_bodies(self):
        self.assertEqual(c.safe_error(ValueError('Bearer secret-value https://private.example')), 'ValueError')
        self.assertEqual(c.safe_error(RuntimeError('model_pair_coverage')), 'model_pair_coverage')


if __name__ == '__main__':
    unittest.main()
