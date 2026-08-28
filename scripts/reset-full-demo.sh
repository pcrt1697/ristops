#!/usr/bin/env bash
#
# Full reset of the containerized demo environment, from nothing to a seeded demo.
#
# Runs, in order:
#   1. down  - stop the current stack, if any (must happen before wiping data below —
#              deleting a bind-mounted data directory out from under a running database
#              is how you get a corrupted store, not a clean one)
#   2. wipe  - delete ~/.ristops (Postgres/Redis/Neo4j data). Safe if it doesn't exist.
#   3. up    - rebuild and start the full stack, waiting for every service to report
#              healthy rather than just started (reset-demo.sh below fires HTTP requests
#              at be-authn/be-authz immediately, so "started" isn't enough)
#   4. demo  - hand off to ristops-backend/scripts/reset-demo.sh, which nukes/seeds the
#              application-level data and loads the Game-of-Thrones demo fixtures
#
# Lives at the repo root rather than under docker/ or ristops-backend/ because it spans
# both, plus a host directory neither of them owns.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker/docker-compose.yaml"

step() {
  echo ""
  echo ">>> $1"
}

echo "=== RistOps full demo reset (repo: ${REPO_ROOT}) ==="

step "Stop the current stack (if any)"
docker compose -f "${COMPOSE_FILE}" down

step "Wipe ~/.ristops (Postgres/Redis/Neo4j data)"
rm -rf "${HOME}/.ristops"

step "Rebuild and start the full stack, waiting for every service to be healthy"
docker compose -f "${COMPOSE_FILE}" up -d --build --wait --wait-timeout 300

step "Feed demo data"
# reset-demo.sh resolves its own paths from its own location, so it runs correctly from
# any working directory — no `cd` needed here.
"${REPO_ROOT}/ristops-backend/scripts/reset-demo.sh"

echo ""
echo "=== Full demo reset complete ==="
