#!/usr/bin/env bash
set -euo pipefail
DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec 9>"$DEPLOY_DIR/.renew.lock"
flock -n 9 || exit 0
docker run --rm --network host \
 --mount "type=bind,src=$DEPLOY_DIR/acme,dst=/var/www/acme" \
 --mount "type=bind,src=$DEPLOY_DIR/letsencrypt,dst=/etc/letsencrypt" \
 --mount "type=bind,src=$DEPLOY_DIR/logs,dst=/var/log/letsencrypt" \
 certbot/certbot:v5.8.0 renew --non-interactive --no-random-sleep-on-renew \
 --deploy-hook 'touch /etc/letsencrypt/.wgss-renewed' "$@"
if [[ -f "$DEPLOY_DIR/letsencrypt/.wgss-renewed" ]]; then
 docker exec wgss-ec2-edge nginx -t
 docker exec wgss-ec2-edge nginx -s reload
 rm "$DEPLOY_DIR/letsencrypt/.wgss-renewed"
fi
