#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST_DIR="${AGGREGATOR_HOST_DIR:-${ROOT_DIR}-host}"
ENV_FILE="${HOST_DIR}/.env"

if [[ ! -r "$ENV_FILE" ]]; then
  echo "Host action required: create ${ENV_FILE} from deploy/.env.example." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
# shellcheck disable=SC1091
source "$ROOT_DIR/deploy/requirements.sh"

missing=0
for variable in "${REQUIRED_ENV_VARS[@]}"; do
  if [[ -z "${!variable:-}" ]]; then
    echo "Host action required: set ${variable} in ${ENV_FILE}." >&2
    missing=1
  fi
done
for variable in "${REQUIRED_SECRET_PATH_VARS[@]}"; do
  path="${!variable:-}"
  if [[ -n "$path" && ! -s "$path" ]]; then
    echo "Host action required: create the non-empty secret file configured by ${variable}." >&2
    missing=1
  fi
done
if (( missing )); then
  echo "Deployment stopped; the running containers were not changed." >&2
  exit 1
fi

"$ROOT_DIR/deploy/compose.sh" config --quiet
