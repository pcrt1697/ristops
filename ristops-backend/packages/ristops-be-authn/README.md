# RistOps-Auth backend

Generate secret key pair:

```bash
# cwd -> project root 
openssl ecparam -name prime256v1 -genkey -noout -out ./scripts/data/ec_private.pem
openssl ecparam -name prime256v1 -genkey -noout -out ./scripts/data/ec_refresh.pem
openssl ec -in ./scripts/data/ec_private.pem -pubout -out ./scripts/data/ec_public.pem
```

Run FastAPI app:

```bash
RISTOPS_KEYS_LOCATION="./scripts/data/" RISTOPS_ENV_PATH="./packages/ristops-be-auth/.env" RISTOPS_ADMIN_PWD="ristops" RISTOPS_PG_PWD="ristops" uv run ristops start "ristops_be_auth.app:APP"
```
