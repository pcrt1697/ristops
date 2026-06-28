# CLAUDE.md — frontend

Guidance for the frontend (`ristops-web`), a React + TypeScript app (Vite, antd, TanStack
Query, graphql-request). Repo-wide rules live in the root `CLAUDE.md` and apply here too — in
particular, discuss implementation options before writing components or utilities.

## Directory conventions

The top level is sliced by kind/layer; colocate code with the thing it belongs to and promote
to a shared location only when it is genuinely generic.

```text
src/
  commons/      # generic, app-agnostic helpers: hooks.ts (React hooks), utils.ts (pure functions)
  components/   # UI components, grouped by feature (acl/, venue/, layout/, routing/, table/)
  context/      # React contexts and their providers/hooks
  domain/<d>/   # per-domain logic: <d>.api.ts, <d>.hooks.ts, <d>.types.ts, <d>.graphql, <d>.utils.ts
  pages/        # route-level pages
  services/     # infrastructure: graphql client, rest client, generated GraphQL types, common config
```

* Domain-specific helpers live in the domain folder (e.g. `domain/auth/authz.utils.ts`).
* Component-specific render helpers live next to the component (e.g. `components/table/utils.tsx`).
* Only truly generic helpers go in `commons/`.

## GraphQL codegen

* GraphQL operations are authored in `src/**/*.graphql` files (colocated per domain).
* `src/services/graphql/graphql.ts` and `gql.ts` are **generated** — never hand-edit them.
* After changing any `.graphql` file or the schema, run `npm run graphql:gen`.
* `graphql/schema.gql` mirrors the bff-web Strawberry schema; regenerate it from the backend.

## Data fetching & UI patterns

* Fetch through TanStack Query via per-domain `use*` hooks; keep raw `gqlRequest` calls in
  the domain's `*.api.ts`.
* Prefer backend filtering/pagination: pass the query's filter inputs to the backend instead
  of fetching everything and filtering client-side.
* Debounce live filter inputs with `useDebounced` from `commons/hooks.ts`.
* Gate UI on permissions with `useCan(resource, ...permissions)`; use `RequirePermission`
  for route/section-level gating.
