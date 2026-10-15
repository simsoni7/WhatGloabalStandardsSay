"""Publish the current UI check report and a reproducible, credential-free bundle."""
from pathlib import Path
import json
import zipfile

root = Path(__file__).resolve().parents[1]
data = root / 'dist/data'
report = json.loads((data / 'validation-report.json').read_text())
browser = json.loads((root / 'research/practitioner-browser-report.json').read_text())
screens = json.loads((root / 'research/screen-browser-report.json').read_text())
screen_data = json.loads((root / 'research/screen-validation-report.json').read_text())
coverage_browser = json.loads((root / 'research/coverage-browser-report.json').read_text())
coverage_data = json.loads((root / 'research/coverage-validation-report.json').read_text())
assert all(r['status'] == 'passed' for r in (browser, screens, screen_data, coverage_browser, coverage_data))
report.update(version='0.8.0', dataset_version='0.4.0', screen_evidence=screen_data, coverage=coverage_data, browser={
    'status': browser['status'], 'checks': browser['checks'] + screens['checks'] + coverage_browser['checks'],
    'items': browser['details'] + screens['items'] + coverage_browser['items'], 'viewports': ['1440x1000', '390x844'],
    'native_webmcp': 'not_tested_in_this_ui_review',
})
report['taxonomy'] = json.loads((root/'research/taxonomy-validation-report.json').read_text())
report.pop('workbench_browser', None)
report.pop('model_browser', None)
report['bedrock'] = json.loads((root/'research/bedrock-status.json').read_text())
(data / 'validation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
paths = [root/'README.md', root/'AGENTS.md', *sorted((root/'docs').glob('*.md')),
         *sorted((root/'dist').glob('*.html')), *sorted((root/'dist').glob('*.js')),
         *sorted((root/'dist').glob('*.css')), *sorted(data.glob('*.json')),
         *sorted((root/'scripts').glob('*.py')), *sorted((root/'tests').glob('*.py')),
         *sorted((root/'tests').glob('*.cjs')), root/'research/practitioner-browser-report.json',
         *sorted((root/'research').glob('screen-*.json')), root/'research/collection-backlog.json',
         *sorted((root/'research').glob('coverage-*.json')), *sorted((root/'research').glob('quality-steward*.json')),
         *sorted((root/'research/quality-steward').glob('*.json')),
         root/'research/benchmark-targets.json',root/'research/platform-discovery.json',
         *sorted((root/'research').glob('taxonomy-*.json')), root/'research/iso-domain-model-inventory.json',
         *sorted((root/'research/taxonomy-v1').glob('*.json')),
         root/'scripts/capture-requirements.txt', *sorted((root/'dist/evidence').glob('*'))]
with zipfile.ZipFile(data/'wgss-design-v0.8.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for path in paths:
        z.write(path, str(path.relative_to(root)))
print(f'Packaged {len(paths)} files for UI v0.8')
