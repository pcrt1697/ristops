# ristops-be-authn

Authentication service. Manages users and issues ES256 JWT access and refresh tokens.

[Full documentation](https://pcrt1697.github.io/ristops/#/services/be-authn)

## Setup

Commands run from `ristops-backend/`. Generate the EC key pair once before the first run:

```bash
openssl ecparam -name prime256v1 -genkey -noout -out scripts/data/ec_private.pem
openssl ecparam -name prime256v1 -genkey -noout -out scripts/data/ec_refresh.pem
openssl ec -in scripts/data/ec_private.pem -pubout -out scripts/data/ec_public.pem
```

```bash
RISTOPS_ENV_PATH=packages/ristops-be-authn/.env \
RISTOPS_ADMIN_PWD=ristops1 \
RISTOPS_PG_PWD=ristops \
RISTOPS_JWT_KEYS_LOCATION=scripts/data/ \
RISTOPS_REDIS_URL=redis://ristops:ristops@localhost:6380 \
  ristops seed-authn

RISTOPS_ENV_PATH=packages/ristops-be-authn/.env \
RISTOPS_ADMIN_PWD=ristops1 \
RISTOPS_PG_PWD=ristops \
RISTOPS_JWT_KEYS_LOCATION=scripts/data/ \
RISTOPS_JWT_ACCESS_EXPIRATION_M=300 \
RISTOPS_REDIS_URL=redis://ristops:ristops@localhost:6380 \
  ristops start be-authn --port 8001
```

## Dependencies

`ristops-lib-core`, `ristops-lib-be`, `ristops-lib-sql`, `ristops-lib-redis`
