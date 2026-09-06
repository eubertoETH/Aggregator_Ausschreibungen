#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${AGGREGATOR_DEPLOY_SYNCED:-}" != "1" && -d "$ROOT_DIR/.git" ]]; then
  git -C "$ROOT_DIR" pull --ff-only
  AGGREGATOR_DEPLOY_SYNCED=1 exec "$ROOT_DIR/deploy/deploy.sh"
fi

"$ROOT_DIR/deploy/preflight.sh"
"$ROOT_DIR/deploy/compose.sh" pull app scheduler db
"$ROOT_DIR/deploy/compose.sh" up -d --no-build --force-recreate app scheduler
"$ROOT_DIR/deploy/compose.sh" ps
