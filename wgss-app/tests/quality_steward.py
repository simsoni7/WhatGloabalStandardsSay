"""Check dry-run/cache gates without any network request or credentials."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
env=dict(os.environ);env.pop('BEDROCK_API_KEY',None)
with tempfile.TemporaryDirectory(prefix='wgss-quality-test-') as tmp:
    base=[sys.executable,str(ROOT/'scripts/run_quality_steward.py'),'--phase','coverage','--root',str(ROOT),'--output',tmp]
    def run(extra):return subprocess.run(base+extra,env=env,capture_output=True,text=True)
    dry=run(['--dry-run']);assert dry.returncode==0
    report=json.loads((Path(tmp)/'quality-steward-coverage-dry-run.json').read_text())
    assert report['status']=='dry_run_no_request' and report['input_bytes']<16000
    assert report['model_requested']=='claude-sonnet-5' and report['source_snapshot_sha256']
    # This temporary success marker is a cache fixture, not a real model result.
    report['status']='succeeded';success=Path(tmp)/'quality-steward-coverage.json';success.write_text(json.dumps(report))
    cached=run([]);assert cached.returncode==0
    assert json.loads(cached.stdout)['tokens_consumed_this_invocation']==0
    before=success.read_bytes();assert run(['--dry-run']).returncode==0 and success.read_bytes()==before
    report['source_snapshot_sha256']['dist/data/library.json']='changed_fixture_hash';success.write_text(json.dumps(report))
    stale=run([]);assert stale.returncode!=0
    assert json.loads(success.read_text())['status']=='blocked_missing_credential'
    assert 'Gateway credential unavailable' in stale.stderr
    assert not report['independent_human_review'] and not report['image_bytes_sent'] and not report['ocr_sent']
print(json.dumps({'status':'passed','checks':5,'gateway_calls':0,'temporary_fixture_only':True}))
