#!/usr/bin/env bash
set -euo pipefail
DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$EUID" != 0 ]]; then exec sudo -n "$0" "$@"; fi
mkdir -p "$DEPLOY_DIR"/{acme/.well-known/acme-challenge,letsencrypt-staging,letsencrypt,logs}
if [[ ! -s "$DEPLOY_DIR/letsencrypt/live/wgss-ip/fullchain.pem" ]]; then
 if ss -H -ltn 'sport = :80' | read -r _; then echo 'Port 80 is occupied. Preserve the existing service and review its configuration first.' >&2; exit 1; fi
 docker run -d --name wgss-ec2-acme --restart unless-stopped --network host --read-only \
  --cap-drop ALL --cap-add NET_BIND_SERVICE --cap-add SETUID --cap-add SETGID --cap-add CHOWN \
  --security-opt no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=32m \
  --mount "type=bind,src=$DEPLOY_DIR/nginx-http.conf,dst=/etc/nginx/nginx.conf,readonly" \
  --mount "type=bind,src=$DEPLOY_DIR/acme,dst=/var/www/acme,readonly" \
  nginx:1.28-alpine nginx -g 'daemon off;'
 cert_args=(certonly --non-interactive --agree-tos --register-unsafely-without-email --preferred-profile shortlived --webroot --webroot-path /var/www/acme --ip-address 3.36.58.188 --cert-name wgss-ip)
 for stage in staging production; do
  cert_dir="$DEPLOY_DIR/letsencrypt"; extra=()
  if [[ "$stage" == staging ]]; then cert_dir="$DEPLOY_DIR/letsencrypt-staging"; extra=(--staging); fi
  docker run --rm --network host \
   --mount "type=bind,src=$DEPLOY_DIR/acme,dst=/var/www/acme" \
   --mount "type=bind,src=$cert_dir,dst=/etc/letsencrypt" \
   --mount "type=bind,src=$DEPLOY_DIR/logs,dst=/var/log/letsencrypt" \
   certbot/certbot:v5.8.0 "${cert_args[@]}" "${extra[@]}"
 done
fi
"$DEPLOY_DIR/start-https.sh"
systemctl link "$DEPLOY_DIR/wgss-ip-renew.service" "$DEPLOY_DIR/wgss-ip-renew.timer"
systemctl daemon-reload
systemctl enable --now wgss-ip-renew.timer
