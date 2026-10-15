#!/usr/bin/env bash
set -euo pipefail
DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if ! sudo -n test -s "$DEPLOY_DIR/letsencrypt/live/wgss-ip/fullchain.pem"; then echo 'A trusted IP certificate is required first.' >&2; exit 1; fi
if docker container inspect wgss-ec2-acme >/dev/null 2>&1; then docker rm -f wgss-ec2-acme >/dev/null; fi
if docker container inspect wgss-ec2-edge >/dev/null 2>&1; then docker rm -f wgss-ec2-edge >/dev/null; fi
docker run -d --name wgss-ec2-edge --restart unless-stopped --network host --read-only \
 --cap-drop ALL --cap-add NET_BIND_SERVICE --cap-add SETUID --cap-add SETGID --cap-add CHOWN \
 --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=64m \
 --mount "type=bind,src=$DEPLOY_DIR/nginx-https.conf,dst=/etc/nginx/nginx.conf,readonly" \
 --mount "type=bind,src=$DEPLOY_DIR/acme,dst=/var/www/acme,readonly" \
 --mount "type=bind,src=$DEPLOY_DIR/public,dst=/usr/share/nginx/html,readonly" \
 --mount "type=bind,src=$DEPLOY_DIR/letsencrypt,dst=/etc/letsencrypt,readonly" \
 nginx:1.28-alpine nginx -g 'daemon off;'
