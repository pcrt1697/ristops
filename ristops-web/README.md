# ristops-web

React frontend for RistOps. Communicates exclusively with `ristops-bff-web` via REST (auth
endpoints) and GraphQL (data queries and mutations).

## Setup

```bash
npm install
npm dev
```

The dev server runs on `http://localhost:5173`. The BFF is expected at the URL configured in
`.env` (`VITE_RISTOPS_BFF_URL`, default `http://localhost:8000`).

## GraphQL types

TypeScript types for GraphQL queries and mutations are generated from the BFF schema. Before
running codegen, export the current schema from `ristops-backend/`:

```bash
ristops graphql-bff export-schema -f ../ristops-web/graphql/schema.gql --overwrite
```

Then regenerate the types:

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
