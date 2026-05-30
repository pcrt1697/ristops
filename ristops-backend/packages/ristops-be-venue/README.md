# ristops-be-venue

Venue registry service. Manages the canonical list of venues referenced by all other domain
services.

[Full documentation](https://pcrt1697.github.io/ristops/#/services/be-venue)

## Setup

Commands run from `ristops-backend/`.

```bash
RISTOPS_ENV_PATH=packages/ristops-be-venue/.env \
RISTOPS_PG_PWD=ristops \
RISTOPS_BE_AUTHN_URL=http://localhost:8001 \
RISTOPS_BE_AUTHZ_URL=http://localhost:8002 \
  ristops start be-venue --port 8004
```

## Dependencies

`ristops-lib-core`, `ristops-lib-be`, `ristops-lib-sql`, `ristops-lib-redis`
