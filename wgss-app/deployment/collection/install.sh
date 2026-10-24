#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m venv /home/ubuntu/wgss-collection-runtime/.venv
/home/ubuntu/wgss-collection-runtime/.venv/bin/pip install -r deployment/collection/requirements.txt
/home/ubuntu/wgss-collection-runtime/.venv/bin/python -m playwright install chromium
# The key crosses stdin only, then remains host-encrypted outside the checkout.
python3 - <<'PY'
import os, subprocess
key = os.environ.get('BEDROCK_API_KEY', '')
if not key:
    raise SystemExit('BEDROCK_API_KEY must be present in the installer environment.')
subprocess.run(['sudo','-n','install','-d','-m','700','/etc/credstore.encrypted'],check=True)
r = subprocess.run(['sudo','-n','systemd-creds','encrypt','--with-key=host','--name=bedrock-api-key','-','/etc/credstore.encrypted/wgss-bedrock'],input=key.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if r.returncode:
    raise SystemExit('Encrypted credential installation failed; value not logged.')
subprocess.run(['sudo','-n','chmod','600','/etc/credstore.encrypted/wgss-bedrock'],check=True)
PY
sudo -n systemd-analyze verify deployment/collection/wgss-collection.service deployment/collection/wgss-collection.timer
sudo -n install -m 644 deployment/collection/wgss-collection.service /etc/systemd/system/wgss-collection.service
sudo -n install -m 644 deployment/collection/wgss-collection.timer /etc/systemd/system/wgss-collection.timer
sudo -n systemctl daemon-reload
sudo -n systemctl enable --now wgss-collection.timer
sudo -n systemctl start --no-block wgss-collection.service
systemctl list-timers wgss-collection.timer --all --no-pager
