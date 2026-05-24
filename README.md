# RistOps

Start with docker-compose:

```bash
RISTOPS_NEO4J_PWD=ristops1 RISTOPS_PG_PWD=ristops RISTOPS_REDIS_SESSION_PWD=ristops RISTOPS_REDIS_STREAM_PWD=ristops docker-compose -f docker/docker-compose.local.yaml up --force-recreate -d
```
