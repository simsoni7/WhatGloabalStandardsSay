#!/usr/bin/env bash
set -euo pipefail
DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${WGSS_SOURCE_DIR:-/home/ubuntu/wgss-github/wgss-app}"
NODE_BIN="${WGSS_NODE_BIN:-/tmp/wgss-toolchain/bin/node}"
# Keep the same base as GitHub Pages and call the central intake directly.
# Central WGSS_PUBLIC_FRONTEND_ORIGINS must include https://3.36.58.188.
WGSS_PUBLIC_BASE=/WhatGloabalStandardsSay/wgss/ "$NODE_BIN" "$SOURCE_DIR/scripts/build-github-pages.mjs" "$DEPLOY_DIR/public/WhatGloabalStandardsSay/wgss"
