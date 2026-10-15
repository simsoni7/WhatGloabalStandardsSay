"""User-local, one-shot capture of an explicitly selected existing Chromium tab.

Does not navigate, click, type, read cookies/storage/DOM, or send artifacts.
CDP itself is privileged; use a dedicated local Chrome profile, never a tunnel.
Requires Playwright >=1.60 for no_defaults (preserve the current browser setup).
"""
import argparse
import datetime
import hashlib
import json
import inspect
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOOPBACK = {'127.0.0.1', '::1'}
PNG = b'\x89PNG\r\n\x1a\n'


class CaptureError(Exception):
    pass


def endpoint_parts(value, schemes):
    try:
        p = urllib.parse.urlsplit(value)
        if p.scheme not in schemes or p.hostname not in LOOPBACK or not p.port:
            raise CaptureError('CDP endpoint must use a literal loopback address and explicit port')
        if p.username or p.password or p.query or p.fragment:
            raise CaptureError('Endpoint credentials, query and fragment are not accepted')
        return p
    except ValueError:
        raise CaptureError('Invalid endpoint') from None


def origin(value):
    try:
        p = urllib.parse.urlsplit(value)
        if p.scheme not in {'https', 'http'} or not p.hostname or p.username or p.password:
            raise CaptureError('Invalid page origin')
        if p.scheme == 'http' and p.hostname not in LOOPBACK:
            raise CaptureError('HTTP is allowed only for local synthetic fixtures')
        host = p.hostname.encode('idna').decode('ascii').lower()
        if ':' in host:
            host = '[' + host + ']'
        port = p.port
        suffix = '' if port is None or port == {'https': 443, 'http': 80}[p.scheme] else ':' + str(port)
        return p.scheme + '://' + host + suffix
    except ValueError:
        raise CaptureError('Invalid page origin') from None


def allowlist(values):
    result = set()
    for value in values:
        p = urllib.parse.urlsplit(value)
        if p.path not in {'', '/'} or p.query or p.fragment or '*' in value:
            raise CaptureError('Allowlist entries must be exact origins, without path, query or wildcard')
        result.add(origin(value))
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise CaptureError('CDP discovery redirect refused')


def websocket_endpoint(endpoint):
    p = endpoint_parts(endpoint, {'http'})
    if p.path not in {'', '/'}:
        raise CaptureError('Use the loopback HTTP CDP origin')
    request = urllib.request.Request(endpoint.rstrip('/') + '/json/version')
    # Do not inherit proxies or allow a discovery response to move the connection.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=5) as response:
        payload = response.read(65537)
    if len(payload) > 65536:
        raise CaptureError('CDP discovery response is too large')
    target = json.loads(payload).get('webSocketDebuggerUrl', '')
    w = endpoint_parts(target, {'ws'})
    if w.hostname != p.hostname or w.port != p.port or not w.path.startswith('/devtools/browser/'):
        raise CaptureError('CDP discovery must preserve the exact local address and port')
    return target


def known_work(work_id, catalogue):
    if not re.fullmatch(r'WGSS-UI-[A-F0-9]{12}', work_id or ''):
        raise CaptureError('Use a canonical WGSS-UI work ID')
    file = Path(catalogue)
    if not file.is_file() or file.stat().st_size > 8_000_000:
        raise CaptureError('Catalogue must be a JSON file below 8 MB')
    try:
        works = json.loads(file.read_text(encoding='utf-8'))['works']
        if not isinstance(works, list) or not all(isinstance(row, dict) and isinstance(row.get('id'), str) for row in works):
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise CaptureError('Catalogue must contain works with canonical ID fields') from None
    if work_id not in {row['id'] for row in works}:
        raise CaptureError('Unknown canonical work ID')


def selected_page(pages, index, allowed):
    if index < 0 or index >= len(pages):
        raise CaptureError('Selected tab index is unavailable; list tabs again')
    page = pages[index]
    if origin(page.url) not in allowed:
        raise CaptureError('Selected tab is outside the explicit origin allowlist')
    return page


def target_id(page):
    session = page.context.new_cdp_session(page)
    try:
        return session.send('Target.getTargetInfo')['targetInfo']['targetId']
    finally:
        session.detach()


def capture_bytes(page, allowed):
    # Retain exact URL only in memory, never in metadata or logs.
    before = page.url
    source_origin = origin(before)
    if source_origin not in allowed:
        raise CaptureError('Selected tab is outside the explicit origin allowlist')
    raw = page.screenshot(type='png', full_page=False, timeout=10000)
    if page.url != before:
        raise CaptureError('Tab location changed during capture; nothing saved')
    if not raw.startswith(PNG):
        raise CaptureError('No valid PNG capture')
    return raw, source_origin


def private_store(value):
    raw_base = Path.home() / '.wgss-capture-store'
    if raw_base.is_symlink():
        raise CaptureError('Capture base directory must not be a symbolic link')
    base = raw_base.resolve()
    requested = Path(value).expanduser().absolute() if value else raw_base / 'web'
    if requested != raw_base and raw_base not in requested.parents:
        raise CaptureError('Raw captures must remain under ~/.wgss-capture-store')
    for component in [requested, *requested.parents]:
        if component == raw_base.parent:
            break
        if component.is_symlink():
            raise CaptureError('Capture store components must not be symbolic links')
    path = requested.resolve()
    if path != base and base not in path.parents:
        raise CaptureError('Raw captures must remain under ~/.wgss-capture-store')
    if path.exists() and path.is_symlink():
        raise CaptureError('Capture directory must not be a symbolic link')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    return path


def save_capture(raw, record, store):
    digest = hashlib.sha256(raw).hexdigest()
    # Unique per capture; repeated screens must not overwrite source context.
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    stem = stamp + '-' + digest
    record.update(image_sha256=digest, observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    for suffix, payload in [('.png', raw), ('.json', (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode())]:
        fd = os.open(store / (stem + suffix), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as output:
            output.write(payload)
    return stem


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['list-tabs', 'capture'])
    parser.add_argument('--endpoint', default='http://127.0.0.1:9222')
    parser.add_argument('--allow-origin', action='append', required=True)
    parser.add_argument('--tab-index', type=int)
    parser.add_argument('--tab-id')
    parser.add_argument('--tab-state')
    parser.add_argument('--work-id')
    parser.add_argument('--catalog', '--catalogue', dest='catalogue', default=str(ROOT / 'dist/data/bank-ui.json'))
    parser.add_argument('--market', choices=['KR', 'GB', 'HK'])
    parser.add_argument('--locale', choices=['ko-KR', 'en-GB', 'en-HK', 'zh-HK'])
    parser.add_argument('--provider-id')
    parser.add_argument('--store')
    args = parser.parse_args(argv)
    allowed = allowlist(args.allow_origin)
    if args.action == 'capture':
        if args.tab_index is None or not args.tab_id or not args.tab_state or not args.work_id or not args.market or not args.locale or not args.provider_id:
            raise CaptureError('Capture needs tab index, tab ID, tab state, work ID, market, locale and provider ID')
        known_work(args.work_id, args.catalogue)
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,79}', args.provider_id):
            raise CaptureError('Invalid provider ID')
        store = private_store(args.store)
    ws = websocket_endpoint(args.endpoint)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        if 'no_defaults' not in inspect.signature(playwright.chromium.connect_over_cdp).parameters:
            raise CaptureError('Install Playwright >=1.60; default-changing attachment is refused')
        # Stopping Playwright disconnects the client; never call browser.close().
        browser = playwright.chromium.connect_over_cdp(ws, no_defaults=True, timeout=10000)
        pages = [page for context in browser.contexts for page in context.pages]
        if args.action == 'list-tabs':
            rows = []
            for index, page in enumerate(pages):
                try:
                    o = origin(page.url)
                except CaptureError:
                    continue
                if o in allowed:
                    rows.append({'tab_index': index, 'tab_id': target_id(page), 'tab_state': hashlib.sha256(page.url.encode()).hexdigest(), 'origin': o})
            print(json.dumps({'tabs': rows, 'titles_and_paths_omitted': True}))
            return
        page = selected_page(pages, args.tab_index, allowed)
        if target_id(page) != args.tab_id:
            raise CaptureError('Selected tab identity changed; list tabs again')
        if hashlib.sha256(page.url.encode()).hexdigest() != args.tab_state:
            raise CaptureError('Selected tab location changed; list tabs again')
        raw, source_origin = capture_bytes(page, allowed)
        record = {
            'schema_version': 'wgss-local-capture-v31',
            'work_id_candidate': args.work_id,
            'provider_id_declared': args.provider_id,
            'market_declared': args.market,
            'locale_declared': args.locale,
            'source_origin': source_origin,
            'channel': 'web',
            'browser_version': browser.version,
            'ui_version': None,
            'authentication_state': 'not_inspected',
            'evidence_status': 'pending_financial_visual_privacy_review',
            'contains_personal_data': 'assumed_yes_until_local_review',
            'capability_scope': 'privileged_local_cdp_used_only_for_tab_identity_and_screenshot',
            'evidence_basis': 'user_declared_metadata_over_locally_observed_viewport',
            'published': False,
            'sent_to_cloud': False,
            'sent_to_model': False,
            'financial_completion_verified': False,
        }
        stem = save_capture(raw, record, store)
        print(json.dumps({'status': record['evidence_status'], 'local_artifact': stem, 'published': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Never echo service URLs, network response bodies or Playwright traces.
        message = str(error) if isinstance(error, CaptureError) else 'Local capture failed (' + type(error).__name__ + ')'
        print(message, file=sys.stderr)
        raise SystemExit(2)
