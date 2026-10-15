#!/usr/bin/env python3
"""Immutable upstream snapshots and deterministic intake audit; no dataset adoption."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

SOURCES = [
    dict(id='malaysia_financial_metadata', repo='data-gov-my/datagovmy-meta', baseline='a34682cf22a1da9de5520a27f5f3fc5f7c86b06f', license='MIT', obligations='Retain Government of Malaysia copyright and MIT license; review metadata context before adoption.', files=['LICENSE','data-catalogue/bop_balance.json','data-catalogue/interestrates.json','data-catalogue/federal_finance_year_revenue.json','data-catalogue/state_finance_revenue.json']),
    dict(id='apache_ofbiz', repo='apache/ofbiz-framework', baseline='b8b72d556e829d4a0818f8a4fed57e0750efcacb', license='Apache-2.0', obligations='Retain LICENSE and NOTICE; state modifications.', files=['LICENSE', 'NOTICE', 'applications/accounting/config/AccountingUiLabels.xml']),
    dict(id='gnucash', repo='Gnucash/gnucash', baseline='9e39744aac80f2737d291fcbea3fff2d357b28a5', license='GPL-2.0-or-GPL-3.0', obligations='Separate copyleft source pack; preserve PO copyrights and corresponding source.', files=['LICENSE', 'po/vi.po', 'po/ru.po']),
    dict(id='mifos', repo='openMF/community-app', baseline='45ec7b82e9b14424a53ce9e8a847811f37f431bd', license='MPL-2.0', obligations='Preserve file-level copyleft, notices and corresponding source.', files=['LICENSE.txt'] + ['app/global-translations/locale-' + language + '.json' for language in ['en', 'km', 'vi', 'ko', 'es', 'hi', 'ne', 'id']]),
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def fetch(url):
    # Default TLS verification remains enabled. No external API keys or proxies.
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'FinancialGlossarySourceMonitor/1.0'}), timeout=45) as response:
        data = response.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise ValueError('Source exceeds 20 MiB limit')
    return data

def research(output):
    report = {'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'sources': [], 'automatic_adoption': False, 'human_semantic_approval': False}
    for source in SOURCES:
        item = {**source, 'files': [], 'errors': []}
        try:
            result = subprocess.run(['git', 'ls-remote', 'https://github.com/' + source['repo'] + '.git', 'HEAD'], capture_output=True, text=True, check=True, timeout=60)
            commit = result.stdout.split()[0]
            if not re.fullmatch('[0-9a-f]{40}', commit):
                raise ValueError('Invalid upstream commit')
            item['upstream_commit'] = commit
            for path in source['files']:
                record = {'path': path, 'snapshots': {}}
                for label, revision in [('baseline', source['baseline']), ('candidate', commit)]:
                    url = 'https://raw.githubusercontent.com/' + source['repo'] + '/' + revision + '/' + path
                    data = fetch(url)
                    relative = Path('snapshots') / source['id'] / revision / path
                    destination = output / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
                    record['snapshots'][label] = {'file': relative.as_posix(), 'url': url, 'sha256': sha(data), 'bytes': len(data)}
                record['changed'] = record['snapshots']['baseline']['sha256'] != record['snapshots']['candidate']['sha256']
                item['files'].append(record)
        except Exception as error:
            item['errors'].append(type(error).__name__ + ': ' + str(error))
        report['sources'].append(item)
    save_json(output / 'intake.json', report)
    print(json.dumps({'sources': len(report['sources']), 'errors': sum(bool(s['errors']) for s in report['sources'])}))

def audit(output):
    intake = json.loads((output / 'intake.json').read_text())
    results = []
    for source in intake['sources']:
        problems = list(source['errors'])
        changes = []
        for record in source['files']:
            for snapshot in record['snapshots'].values():
                relative = Path(snapshot['file'])
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Unsafe snapshot path')
                data = (output / relative).read_bytes()
                if sha(data) != snapshot['sha256'] or len(data) != snapshot['bytes']:
                    raise ValueError('Snapshot integrity failure: ' + str(relative))
                try:
                    if record['path'].endswith('.json'):
                        if not isinstance(json.loads(data), dict):
                            problems.append('JSON localization is not an object: ' + record['path'])
                    elif record['path'].endswith('.xml'):
                        ET.fromstring(data)
                    elif record['path'].endswith('.po'):
                        decoded = data.decode('utf-8-sig')
                        if 'msgid ' not in decoded or 'msgstr ' not in decoded:
                            problems.append('PO structure missing: ' + record['path'])
                except (ValueError, UnicodeError, ET.ParseError) as error:
                    problems.append('Invalid source syntax: ' + record['path'] + ' (' + type(error).__name__ + ')')
            if record['changed']:
                changes.append(record['path'])
                if Path(record['path']).name in ['LICENSE', 'LICENSE.txt', 'NOTICE']:
                    problems.append('License/notice changed; fresh rights review required')
        if len(source['files']) != len(next(s['files'] for s in SOURCES if s['id'] == source['id'])):
            problems.append('Incomplete source snapshot')
        results.append({'source': source['id'], 'upstream_commit': source.get('upstream_commit'), 'changed_files': changes, 'issues': problems, 'status': 'blocked_pending_review' if problems else 'candidate_pending_review' if changes else 'unchanged', 'commercial_license_baseline': source['license'], 'obligations': source['obligations'], 'semantic_approval': False, 'adoption_allowed': False})
    progress = {'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'workflow': 'Deterministic source monitoring; not an AI or financial expert review', 'core_dataset_modified': False, 'approved_translations_added': 0, 'sources': results}
    save_json(output / 'progress.json', progress)
    print(json.dumps(progress, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['research', 'audit'])
    parser.add_argument('--output', type=Path, default=Path('automation'))
    args = parser.parse_args()
    if args.mode == 'research':
        research(args.output)
    else:
        audit(args.output)

if __name__ == '__main__':
    main()
