#!/usr/bin/env bash
# nginx/test/run.sh
#
# Shell-based equivalent of `make test`, for environments without make
# (e.g. plain Git Bash on Windows). Runs the smoke-test compose stack
# and exits with the tester container's status code.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.test.yml"

cleanup() {
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker compose -f "$COMPOSE_FILE" up \
    --build \
    --abort-on-container-exit \
    --exit-code-from tester
