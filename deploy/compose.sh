#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST_DIR="${AGGREGATOR_HOST_DIR:-${ROOT_DIR}-host}"
ENV_FILE="${HOST_DIR}/.env"

if [[ ! -r "$ENV_FILE" ]]; then
  echo "Host action required: create ${ENV_FILE} from deploy/.env.example." >&2
  exit 1
fi

exec docker compose --env-file "$ENV_FILE" -f "$ROOT_DIR/Docker/compose.production.yaml" "$@"
