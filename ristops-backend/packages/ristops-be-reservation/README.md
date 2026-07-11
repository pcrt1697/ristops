# ristops-be-reservation

Reservation service. Owns venue reservation configuration (services, seatings, opening rules
and overrides), tables, and reservations, and computes slot availability.

[Full documentation](https://pcrt1697.github.io/ristops/#/services/be-reservation)

## Setup

Commands run from `ristops-backend/`.

```bash
RISTOPS_ENV_PATH=packages/ristops-be-reservation/.env \
RISTOPS_PG_PWD=ristops \
RISTOPS_BE_AUTHN_URL=http://localhost:8001 \
RISTOPS_BE_AUTHZ_URL=http://localhost:8002 \
  ristops start be-reservation --port 8004
```

## Dependencies

`ristops-lib-core`, `ristops-lib-be`, `ristops-lib-sql`, `ristops-lib-redis`
