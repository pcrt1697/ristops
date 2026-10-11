#!/usr/bin/env bash
#
# Regenerates the committed API schemas of the backend:
#   - the OpenAPI schema of every app registered under the `ristops.cli.commands.openapi.export`
#     entry-point group, written to ristops-backend/packages/ristops-<app>/openapi.json
#   - the GraphQL SDL of bff-web, written to ristops-web/graphql/schema.gql, where the frontend codegen reads it
#
# Run by the `export-api-schemas` pre-commit hook. It always rewrites every file and exits non-zero
# only when an export fails; pre-commit detects the modified files and stops the commit.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGES_DIR="${REPO_ROOT}/ristops-backend/packages"

run() {
  uv run --project "${REPO_ROOT}/ristops-backend" "$@"
}

apps="$(run python -c 'from importlib.metadata import entry_points; print(*sorted(e.name for e in entry_points(group="ristops.cli.commands.openapi.export")), sep="\n")')"
if [[ -z "${apps}" ]]; then
  echo "No app registered under ristops.cli.commands.openapi.export" >&2
  exit 1
fi

for app in ${apps}; do
  package_dir="${PACKAGES_DIR}/ristops-${app}"
  if [[ ! -d "${package_dir}" ]]; then
    echo "App ${app} does not follow the ristops-<app> package naming: ${package_dir} not found" >&2
    exit 1
  fi
  run ristops openapi export "${app}" -f "${package_dir}/openapi.json" -o
done

run ristops graphql-bff export-schema -f "${REPO_ROOT}/ristops-web/graphql/schema.gql" -o
