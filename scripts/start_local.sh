#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT_DIR="$PWD"
export BUILDX_CONFIG="$ROOT_DIR/.local/buildx"
export COMPOSE_BAKE=false
if [[ ! -f .env.local ]]; then
  python3 scripts/setup_local.py
fi
docker compose --env-file .env.local -f docker-compose.local.yml up -d --build --wait --wait-timeout 180
printf 'Sentinel is available at http://127.0.0.1:8080. Login: .local/login.txt\n'
