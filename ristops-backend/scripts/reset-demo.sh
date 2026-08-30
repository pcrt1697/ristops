#!/usr/bin/env bash
#
# Reset and reseed the local demo environment, end to end.
#
# Runs, in order:
#   1. nuke  - drop the authn + venue + reservation SQL schemas and wipe the authz Neo4j graph
#   2. seed  - recreate the roles + admin ACL (authz) and the admin user (authn), in that
#              order — authz first, since it creates the app:* root resource that authn's
#              admin-created event (consumed asynchronously by be-authz) needs to exist
#   3. demo  - create the Game-of-Thrones demo users, venues, services, role
#              grants, activate the venues, and book the demo reservations
#
# PREREQUISITES
#   * Infra up (Postgres, Redis x2, Neo4j) from docker/.
#   * Backend services running: be-authn:8001, be-authz:8002, be-venue:8003,
#     be-reservation:8004. The demo-seed step calls their REST APIs and relies on
#     the be-authz Redis stream consumer to propagate the new users/venues before
#     roles are granted.
#
# Credentials and the JWT key location default to the local dev values (matching
# the IDE run configs) and can be overridden via environment variables, e.g.:
#
#   RISTOPS_ADMIN_PWD=secret ./scripts/reset-demo.sh
#
set -euo pipefail

# This script lives in <backend>/scripts/; resolve the backend root and run there.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${BACKEND_DIR}"

# --- Overridable configuration (defaults match the local dev setup) ---
: "${RISTOPS_ADMIN_PWD:=ristops1}"
: "${RISTOPS_PG_PWD:=ristops}"
: "${RISTOPS_NEO4J_PWD:=ristops1}"
: "${RISTOPS_REDIS_URL:=redis://ristops:ristops@localhost:6380}"
: "${RISTOPS_JWT_KEYS_LOCATION:=${SCRIPT_DIR}/data/}"
export RISTOPS_ADMIN_PWD RISTOPS_PG_PWD RISTOPS_NEO4J_PWD RISTOPS_REDIS_URL RISTOPS_JWT_KEYS_LOCATION

DEMO_DATA="packages/ristops-batch-demo/demo-data"

# Run a `ristops` command with a service-specific .env (RISTOPS_ENV_PATH).
ristops_with_env() {
  local env_path="$1"; shift
  RISTOPS_ENV_PATH="${BACKEND_DIR}/${env_path}" uv run ristops "$@"
}

step() {
  echo ""
  echo ">>> $1"
}

echo "=== RistOps demo reset (backend: ${BACKEND_DIR}) ==="

# 1. NUKE -------------------------------------------------------------------
step "Nuke authn SQL schema"
ristops_with_env packages/ristops-be-authn/.env sql-database nuke be-authn -f
step "Nuke venue SQL schema"
ristops_with_env packages/ristops-be-venue/.env sql-database nuke be-venue -f
step "Nuke reservation SQL schema"
ristops_with_env packages/ristops-be-reservation/.env sql-database nuke be-reservation -f
step "Nuke authz Neo4j graph"
ristops_with_env packages/ristops-be-authz/.env nuke-authz -f

# 2. SEED SERVICES ----------------------------------------------------------
# authz first: it creates the app:* root resource that seed-authn's admin-created event
# (consumed asynchronously by be-authz's Redis stream consumer) needs to already exist.
# Seeding authn first races that consumer against seed-authz and produces a transient
# "Failed to get resource app:*" 404 that only self-heals via Redis's XAUTOCLAIM retry.
step "Seed roles + admin ACL (authz)"
ristops_with_env packages/ristops-be-authz/.env seed-authz
step "Seed admin user (authn)"
ristops_with_env packages/ristops-be-authn/.env seed-authn

# 3. SEED DEMO --------------------------------------------------------------
step "Seed demo users, venues, services, role grants, activation, and reservations"
ristops_with_env packages/ristops-batch-demo/.env demo seed \
  --users "${DEMO_DATA}/users.json" \
  --venues "${DEMO_DATA}/venues.json" \
  --services "${DEMO_DATA}/services.json" \
  --reservations "${DEMO_DATA}/reservations.json" \
  --assignments "${DEMO_DATA}/assignments.json"

echo ""
echo "=== Demo reset complete ==="
