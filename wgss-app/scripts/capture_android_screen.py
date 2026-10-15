"""Read-only screen/version capture from an explicitly selected test device.

No navigation, login, transactions, APK downloads, security bypasses or automatic
publishing. Authenticated images stay in the ignored local capture store until
case, version and privacy review. Never pass account credentials to this tool.
"""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--serial',required=True);p.add_argument('--package',required=True);p.add_argument('--case-id',required=True);args=p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_.:-]+',args.serial) or not re.fullmatch(r'[a-zA-Z0-9_.]+',args.package):raise SystemExit('Invalid device or package identifier')
    cases=json.loads((ROOT/'dist/data/cases.json').read_text())
    if not any(c['id']==args.case_id for c in cases):raise SystemExit('Unknown case ID')
    base=['adb','-s',args.serial]
    def call(command):return subprocess.run(base+command,capture_output=True,check=True,timeout=20).stdout
    if call(['get-state']).decode().strip()!='device':raise SystemExit('Selected test device is not ready')
    activity=call(['shell','dumpsys','activity','activities']).decode(errors='replace')
    resumed=[line for line in activity.splitlines() if 'mResumedActivity' in line or 'topResumedActivity' in line]
    if not any(re.search(r'\b'+re.escape(args.package)+r'/',line) for line in resumed):raise SystemExit('Selected app is not in the foreground')
    package=call(['shell','dumpsys','package',args.package]).decode(errors='replace')
    version=re.search(r'\bversionName=([^\s]+)',package);build=re.search(r'\bversionCode=(\d+)',package)
    if not version or not build:raise SystemExit('Cannot verify installed app version')
    raw=call(['exec-out','screencap','-p'])
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise SystemExit('Screen capture was blocked or did not produce PNG')
    digest=hashlib.sha256(raw).hexdigest();store=ROOT/'research/capture-store/android';store.mkdir(parents=True,exist_ok=True)
    (store/(digest+'.png')).write_bytes(raw)
    record={'case_id_candidate':args.case_id,'package':args.package,'app_version':version.group(1),'build':build.group(1),
            'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'image_sha256':digest,
            'status':'pending_visual_and_privacy_review','financial_case_not_yet_verified':True,'published':False}
    (store/(digest+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':record['status'],'app_version':record['app_version'],'published':False}))
if __name__=='__main__':main()
