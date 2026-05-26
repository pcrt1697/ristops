# ristops-bff-web

Backend-for-frontend for the web client. Exposes a GraphQL API and handles session-based authentication.

[Full documentation](https://pcrt1697.github.io/ristops/#/services/bff-web)

## Setup

Commands run from `ristops-backend/`.

```bash
RISTOPS_ENV_PATH=packages/ristops-bff-web/.env \
RISTOPS_BE_AUTHN_URL=http://localhost:8001 \
RISTOPS_REDIS_URL=redis://ristops:ristops@localhost:6379 \
  ristops start bff-web --port 8000
```

## Dependencies

`ristops-lib-core`, `ristops-lib-be`, `strawberry-graphql`, `starsessions`
