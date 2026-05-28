# RistOps

Backend for a restaurant operations platform. The system manages users, locations, and role-based
access control across multiple services.

## Documentation

[https://pcrt1697.github.io/ristops](https://pcrt1697.github.io/ristops)

To read the docs locally:

```bash
cd docs && python3 -m http.server 3000
```

Then open `http://localhost:3000`.

## Structure

| Directory | Description |
|-----------|-------------|
| [ristops-backend](ristops-backend/README.md) | Python backend (uv workspace) |
| ristops-web | Frontend (not yet scaffolded) |
| docker | Docker Compose files for local infrastructure |

## Infrastructure

To run the app locally:

```bash
RISTOPS_NEO4J_PWD=ristops1 RISTOPS_PG_PWD=ristops RISTOPS_REDIS_SESSION_PWD=ristops RISTOPS_REDIS_STREAM_PWD=ristops \
  docker-compose -f docker/docker-compose.local.yaml up --force-recreate -d
```

| Service | Description |
|---------|-------------|
| PostgreSQL | relational user store |
| Redis (sessions) | web session store |
| Redis (streams) | inter-service messaging |
| Neo4j | ACL graph store |
