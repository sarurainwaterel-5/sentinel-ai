#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT_DIR="$PWD"
export BUILDX_CONFIG="$ROOT_DIR/.local/buildx"
export COMPOSE_BAKE=false
if [[ ! -f .env.local ]]; then
  python3 scripts/setup_local.py
fi
docker compose --env-file .env.local -f docker-compose.local.yml up -d --build
for attempt in {1..90}; do
  if curl -fsS http://127.0.0.1:8011/ready >/dev/null 2>&1; then
    printf 'Sentinel is available at http://127.0.0.1:8080. Login: .local/login.txt\n'
    exit 0
  fi
  sleep 2
done
printf 'The API did not become ready. Check docker compose logs api.\n' >&2
exit 1
