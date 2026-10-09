# be-authn

Authentication service. Manages users and issues ES256 JWT access and refresh tokens.
Other services validate tokens by fetching the public key from this service's JWKS endpoint.

> Source: [ristops-be-authn](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-be-authn/README.md)

## Token design

Two separate tokens are issued on login: a short-lived access token (15 min by default) and a
longer-lived refresh token (24 h). The separation limits the exposure window of a leaked token
while avoiding frequent re-authentication.

Both tokens are ES256 JWTs, signed with separate EC key pairs. Using different keys for access
and refresh means a refresh token cannot be used as an access token even if the algorithm and
structure are identical.

The public key is exposed at `/.well-known/jwks.json`. Other services fetch and cache it at
startup via `ClientTokenDecoder` — after the initial fetch there is no runtime dependency on
`be-authn` for token validation.

## User lifecycle and event propagation

Every user write operation (create, delete) publishes an event to a Redis stream so that
`be-authz` can keep its ACL graph in sync without polling. The event carries `correlation_id` and a
W3C `traceparent`, so the consumer continues the producer's trace across the service boundary.

| Operation | Redis event | Effect in be-authz |
|-----------|------------|---------------------|
| Create user | `UserLifecycleEvent(created)` | Creates `User` node + default ACL |
| Delete user | `UserLifecycleEvent(deleted)` | Removes `User` node and ACLs |

## Members

Assigning a role needs to find a user, but a full user record includes the email address. Besides
the user endpoints, `be-authn` therefore exposes a separate **member** view: any authenticated
user can search members by display name and read one by ID, and gets back only what an assignment
UI needs, with no email. Members are a projection of the same user records, not a second store.

## Key pair setup

The EC key pair must be generated once before the first run. Both an access key and a separate
refresh key are required:

```bash
openssl ecparam -name prime256v1 -genkey -noout -out scripts/data/ec_private.pem
openssl ecparam -name prime256v1 -genkey -noout -out scripts/data/ec_refresh.pem
openssl ec -in scripts/data/ec_private.pem -pubout -out scripts/data/ec_public.pem
```

The directory is passed via `RISTOPS_JWT_KEYS_LOCATION`.
