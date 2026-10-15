"""Synthetic-only tests: selected local tab, no secret exports, live disconnect.

No bank endpoint, real account, or actual user browser is used.
"""
import contextlib
import hashlib
import http.server
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('collector', ROOT / 'scripts/local_session_capture.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
checks = 0


def check(value):
    global checks
    assert value
    checks += 1


def refused(function, *args):
    try:
        function(*args)
    except tool.CaptureError:
        check(True)
        return
    raise AssertionError('Expected explicit refusal')


for url in ['http://example.com:9222', 'http://localhost:9222', 'http://127.0.0.1',
            'http://u:p@127.0.0.1:9222', 'http://127.0.0.1:9222/?key=secret',
            'http://127.0.0.1:9222/#secret', 'ws://127.0.0.1:9222/devtools/browser/a']:
    refused(tool.endpoint_parts, url, {'http'})
check(tool.endpoint_parts('http://127.0.0.1:9222', {'http'}).port == 9222)
check(tool.endpoint_parts('http://[::1]:9222', {'http'}).hostname == '::1')
refused(tool.allowlist, ['https://*.bank.example'])
refused(tool.allowlist, ['https://bank.example/path'])
refused(tool.allowlist, ['https://bank.example?secret=x'])
refused(tool.allowlist, ['http://bank.example'])
check(tool.origin('https://bank.example/account/SECRET?token=TOKEN#private') == 'https://bank.example')
check(tool.origin('https://bank.example:443/') == 'https://bank.example')
catalogue = ROOT / 'dist/data/bank-ui.json'
work_id = json.loads(catalogue.read_text())['works'][0]['id']
tool.known_work(work_id, catalogue)
check(True)
refused(tool.known_work, 'WGSS-UI-000000000000', catalogue)
refused(tool.known_work, 'WGSS-LEGACY-123', catalogue)


class FakePage:
    def __init__(self, url, changes=False):
        self.url = url
        self.changes = changes

    def screenshot(self, **kwargs):
        check(kwargs == {'type': 'png', 'full_page': False, 'timeout': 10000})
        if self.changes:
            self.url = 'https://bank.example/other'
        return tool.PNG + b'fixture'


refused(tool.selected_page, [FakePage('https://bank.example')], 2, {'https://bank.example'})
refused(tool.selected_page, [FakePage('https://other.example')], 0, {'https://bank.example'})
refused(tool.capture_bytes, FakePage('https://bank.example/before', True), {'https://bank.example'})
with tempfile.TemporaryDirectory() as tmp:
    with patch.dict(os.environ, {'HOME': tmp}):
        refused(tool.private_store, str(Path(tmp) / 'outside'))
        base = Path(tmp) / '.wgss-capture-store'
        outside = Path(tmp) / 'outside'
        outside.mkdir()
        base.symlink_to(outside, target_is_directory=True)
        refused(tool.private_store, None)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'<html><title>PRIVATE_TITLE</title><body>WGSS synthetic fixture<button>Send money</button></body></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        cdp_port = port_socket.getsockname()[1]
    page_origin = 'http://127.0.0.1:' + str(server.server_port)
    private_url = page_origin + '/ACCOUNT_PRIVATE?token=QUERY_PRIVATE#FRAGMENT_PRIVATE'
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(str(Path(tmp) / 'synthetic-profile'), headless=True,
                    args=['--remote-debugging-address=127.0.0.1', '--remote-debugging-port=' + str(cdp_port)])
        page = context.pages[0]
        page.goto(private_url)
        context.add_cookies([{'name': 'auth', 'value': 'COOKIE_PRIVATE', 'url': page_origin}])
        endpoint = 'http://127.0.0.1:' + str(cdp_port)
        command = [sys.executable, str(ROOT / 'scripts/local_session_capture.py')]
        common = ['--endpoint', endpoint, '--allow-origin', page_origin]
        env = dict(os.environ, HOME=tmp)
        listed = subprocess.run(command + ['list-tabs'] + common, env=env, capture_output=True, text=True, timeout=30)
        check(listed.returncode == 0)
        row = json.loads(listed.stdout)['tabs'][0]
        args = ['--tab-index', str(row['tab_index']), '--tab-id', row['tab_id'], '--tab-state', row['tab_state'], '--work-id', work_id,
                '--market', 'KR', '--locale', 'ko-KR', '--provider-id', 'synthetic-bank', '--catalog', str(catalogue)]
        captured = subprocess.run(command + ['capture'] + common + args, env=env, capture_output=True, text=True, timeout=30)
        check(captured.returncode == 0)
        check(page.title() == 'PRIVATE_TITLE')  # Client disconnect did not close or navigate the browser.
        check(context.cookies()[0]['value'] == 'COOKIE_PRIVATE')  # User session still local and unchanged.
        check(page.url == private_url)
        store = Path(tmp) / '.wgss-capture-store/web'
        records = list(store.glob('*.json'))
        check(len(records) == 1 and len(list(store.glob('*.png'))) == 1)
        data = json.loads(records[0].read_text())
        check(data['source_origin'] == page_origin and data['ui_version'] is None)
        check(not data['published'] and not data['sent_to_cloud'] and not data['financial_completion_verified'])
        image = next(store.glob('*.png'))
        check(hashlib.sha256(image.read_bytes()).hexdigest() == data['image_sha256'])
        check(image.stat().st_mode & 0o777 == 0o600)
        outputs = listed.stdout + listed.stderr + captured.stdout + captured.stderr + records[0].read_text()
        for secret in ['PRIVATE_TITLE', 'ACCOUNT_PRIVATE', 'QUERY_PRIVATE', 'FRAGMENT_PRIVATE', 'COOKIE_PRIVATE']:
            check(secret not in outputs)
        bad = [arg if arg != row['tab_id'] else 'wrong-tab' for arg in args]
        rejected = subprocess.run(command + ['capture'] + common + bad, env=env, capture_output=True, text=True, timeout=30)
        check(rejected.returncode == 2 and len(list(store.glob('*.png'))) == 1)
        page.goto(page_origin + '/DIFFERENT_PRIVATE')
        changed = subprocess.run(command + ['capture'] + common + args, env=env, capture_output=True, text=True, timeout=30)
        check(changed.returncode == 2 and len(list(store.glob('*.png'))) == 1)
        context.close()
    server.shutdown()
print(json.dumps({'status': 'passed', 'checks': checks, 'real_service_validated': False,
                  'synthetic_local_cdp_capture': True, 'live_bank_sessions': 0}))
