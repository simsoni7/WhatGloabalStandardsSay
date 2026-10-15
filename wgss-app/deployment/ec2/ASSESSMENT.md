# WGSS EC2 deployment — 2026-10-16 KST

Live frontend: **https://3.36.58.188/WhatGloabalStandardsSay/wgss/**

The root address redirects there. HTTP redirects to HTTPS except the certificate challenge and health endpoint. GitHub Pages remains separate and unchanged. The EC2 copy uses the same commercial-only public export, already-reviewed masked images and central intake URL.

## What is hosted where

- EC2: static frontend and an anonymous public API proxy at `/api/wgss`.
- Existing Sites intake: authoritative D1 records, private R2 uploads, Bedrock requests and native operator login. The frontend ordinarily calls this HTTPS service directly; its `WGSS_PUBLIC_FRONTEND_ORIGINS` must explicitly include `https://3.36.58.188`.
- Operator pages redirect to `https://wgss-public-intake.booknfoto461.chatgpt.site/workspace/#admin`. Operator authentication is not implemented by trusting public headers on EC2.

This is a frontend and API-edge deployment, not a migration of the database or AI worker to EC2. No Wrangler development database was introduced.

## Actual verification

- Public IP 3.36.58.188, private IP 10.49.0.14, Seoul region.
- Let's Encrypt staging ACME validation passed, followed by a production IP certificate.
- `curl` and OpenSSL validated the public certificate with IP SAN `3.36.58.188`; issuer Let's Encrypt YE2. Current certificate expires 2026-10-22 18:56 KST.
- HTTPS app HTML returns 200 and `text/html; charset=utf-8`.
- Anonymous API session returns 200; forged operator headers cannot access the queue (401).
- Certificate renewal dry run and nginx reload passed.
- `wgss-ip-renew.timer` is enabled, checks every 6 hours plus jitter, and persists across reboot. The Docker container has `restart=unless-stopped`.

Ports 80/443 were unused. Existing services were preserved. The nginx container uses host networking, readonly filesystem and public assets, read-only TLS mount, and only bind/setuid/setgid/chown capabilities. TLS private keys and ACME accounts remain outside the document root and must never enter Git. No security group or firewall rules were changed. The successful external ACME challenge verifies inbound port 80 accessibility.

## Rebuild and restart

The deployed directory is `/home/ubuntu/wgss-ec2-deployment`.

1. Run `./build.sh` with Node22 available. `WGSS_SOURCE_DIR` and `WGSS_NODE_BIN` can override source and Node paths. The build regenerates the commercial-only public export from canonical source.
2. Run `./start-https.sh` to recreate the isolated container with the existing trusted certificate.
3. For a new host at the same IP and with free ports, `sudo ./bootstrap-tls.sh` first serves the webroot challenge, validates against staging, then requests production TLS and enables renewal. Docker must already be installed. Never change another service's listener automatically.
4. `sudo ./renew.sh --dry-run --run-deploy-hooks` tests renewal and the deployment hook; it does not replace production TLS with a staging certificate.

Safe repository files: `.gitignore`, `ASSESSMENT.md`, `build.sh`, `bootstrap-tls.sh`, `start-https.sh`, `renew.sh`, `nginx-http.conf`, `nginx-https.conf`, `wgss-ip-renew.service`, `wgss-ip-renew.timer`.

Do not commit `public`, `acme`, `letsencrypt`, `letsencrypt-staging`, `logs`, `tls`, runtime locks, certificate keys, ACME account data, or test output. The service unit intentionally names the deployed path above; update that path when relocating.

## Remaining operating considerations

A changing EC2 public IP requires a new IP certificate, nginx config and allowed frontend origin; an Elastic IP or maintained domain avoids unplanned address changes. IAM role/AWS CLI were absent, so the current association was not changed or guessed. A fully independent EC2 backend would additionally need durable SQL/object storage, verified operator login, backup/restore and queue migration/rollback.

The anonymous API proxy strips native identity headers, cookies and authorization. It shares the upstream proxy IP quota identity, so larger public usage needs a trusted edge rate-limit identity design. Do not forward arbitrary user-supplied IP or operator headers to solve that limitation.

Primary TLS reference: https://letsencrypt.org/2026/03/11/shorter-certs-certbot (Certbot5.4+ webroot, shortlived profile and IP address support). Current deployment uses Certbot5.8.0 and nginx1.28-alpine official Docker images.
