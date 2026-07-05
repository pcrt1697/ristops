# ristops-be-authz

Authorization service. Manages ACLs, roles, and permissions in a Neo4j graph and enforces access
control for the rest of the platform.

[Full documentation](https://pcrt1697.github.io/ristops/#/services/be-authz)

## Setup

Commands run from `ristops-backend/`.

```bash
RISTOPS_ENV_PATH=packages/ristops-be-authz/.env \
RISTOPS_NEO4J_PWD=ristops1 \
  ristops seed-authz

# Reset (DESTRUCTIVE): delete all nodes, then reseed with the command above.
RISTOPS_ENV_PATH=packages/ristops-be-authz/.env \
RISTOPS_NEO4J_PWD=ristops1 \
  ristops nuke-authz

RISTOPS_ENV_PATH=packages/ristops-be-authz/.env \
RISTOPS_NEO4J_PWD=ristops1 \
RISTOPS_REDIS_URL=redis://ristops:ristops@localhost:6380 \
  ristops start be-authz --port 8002
```

## Dependencies

`ristops-lib-core`, `ristops-lib-be`, `ristops-lib-neo4j`, `ristops-lib-redis`
