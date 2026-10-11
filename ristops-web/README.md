# ristops-web

React frontend for RistOps. Communicates exclusively with `ristops-bff-web` via REST (auth
endpoints) and GraphQL (data queries and mutations).

## Setup

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:5173`. The BFF is expected at the URL configured in
`.env` (`VITE_RISTOPS_BFF_URL`, default `http://localhost:8000`), and must be running — either
on the host or from the Compose stack.

## Container

The full Compose stack serves this app as a production build behind nginx, on the same port
5173, so the dev server has to be stopped first:

```bash
docker compose -f ../docker/docker-compose.yaml up -d --build web
```

Vite inlines `VITE_*` variables at build time, so `VITE_RISTOPS_BFF_URL` is a **build argument**
rather than runtime configuration — changing it requires rebuilding the image. Its value must be
reachable from the browser (`http://localhost:8000`), never a Compose service name.

## GraphQL types

TypeScript types for GraphQL queries and mutations are generated from the BFF schema,
committed at `graphql/schema.gql`. The `export-api-schemas` pre-commit hook keeps it in sync with
the backend; to export it by hand, from `ristops-backend/`:

```bash
ristops graphql-bff export-schema -f ../ristops-web/graphql/schema.gql --overwrite
```

Regenerate the types:

```bash
npm run graphql:gen
```

`graphql-codegen` reads `graphql/schema.gql` and all `src/**/*.graphql` operation documents and
regenerates `src/services/graphql/graphql.ts`.

## Stack

- React 19 + TypeScript, Vite
- Ant Design 6 (UI components)
- TanStack Query v5 (server state)
- React Router v7
- graphql-request + GraphQL Codegen
