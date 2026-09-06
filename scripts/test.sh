#!/usr/bin/env sh
set -eu

python3 -m compileall -q Code
test -f requirements.txt
SERVICE_BIND=127.0.0.1 SERVICE_PORT=8080 AGGREGATOR_IMAGE=ghcr.io/eubertoeth/aggregator_ausschreibungen:test POSTGRES_DB=aggregator POSTGRES_USER=aggregator POSTGRES_PASSWORD_HOST_FILE=/dev/null docker compose -f Docker/compose.production.yaml config --quiet
printf '%s\n' 'Application syntax checks passed.'
