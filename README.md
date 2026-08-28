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
| [ristops-web](ristops-web/README.md) | React + TypeScript frontend (Vite) |
| [docker](docker/README.md) | Compose stacks: infrastructure, services, frontend, observability |

## Running locally

There are two Compose stacks. Every variable has a default, so neither needs a `.env` file.
See [docker/README.md](docker/README.md) for the full reference.

### Full stack

Everything in containers — infrastructure, backend services, frontend and observability:

```bash
docker compose -f docker/docker-compose.yaml up -d --build
```

It bootstraps itself: JWT keys, database schemas and the admin user are created by one-shot
init services before the applications start.

| Endpoint | URL |
|----------|-----|
| Web frontend | <http://localhost:5173> |
| bff-web | <http://localhost:8000> |
| be-authn / be-authz / be-venue / be-reservation | <http://localhost:8001> … `:8004` |
| Grafana | <http://localhost:3000> |

### Development

Infrastructure in containers, applications on the host:

```bash
docker compose -f docker/docker-compose.local.yaml up -d
```

Then start the backend services and the frontend:

```bash
cd ristops-backend && ristops start bff-web         # and be-authn, be-authz, be-venue, be-reservation
cd ristops-web && npm run dev
```

Database schemas are created automatically by the `init-db` one-shot service, which both
stacks run. On a fresh database, seed the admin user once:

```bash
cd ristops-backend
ristops seed-authz
ristops seed-authn
```

Each service's README has its full start command with the required environment variables.

## Infrastructure

| Service | Description |
|---------|-------------|
| PostgreSQL | relational user store |
| Redis (sessions) | web session store |
| Redis (streams) | inter-service messaging |
| Neo4j | ACL graph store |
| OpenTelemetry Collector | receives traces, metrics and logs from the services |
| Grafana LGTM | Loki, Tempo, Prometheus and Grafana in one container |
