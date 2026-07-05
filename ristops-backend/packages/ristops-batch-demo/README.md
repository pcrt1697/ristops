# ristops-batch-demo

Demo package for batch processing commands. Not production code — exists to illustrate how batch
jobs integrate with the CLI and the rest of the platform.

## `demo seed`

Populates a running stack with Game-of-Thrones-themed demo data by calling the real backend REST
APIs (authn, venue, authz): it registers users, creates venues, and grants venue roles.

```bash
ristops demo seed \
  --users packages/ristops-batch-demo/demo-data/users.json \
  --venues packages/ristops-batch-demo/demo-data/venues.json \
  --assignments packages/ristops-batch-demo/demo-data/assignments.json \
  --admin-password <admin_pwd>
```

Options:

| Option                | Env var             | Description                                   |
|-----------------------|---------------------|-----------------------------------------------|
| `-u/--users`          |                     | Path to the users JSON file (required).       |
| `-v/--venues`         |                     | Path to the venues JSON file (required).      |
| `-a/--assignments`    |                     | Path to the assignments JSON file (required). |
| `-e/--admin-email`    |                     | Admin email (default `admin@ristops.com`).    |
| `-p/--admin-password` | `RISTOPS_ADMIN_PWD` | Admin password (required).                    |

Service base URLs are read from `BackendServiceSettings` (`RISTOPS_BE_AUTHN_URL`,
`RISTOPS_BE_VENUE_URL`, `RISTOPS_BE_AUTHZ_URL`) and must include the `/api` prefix.

### Config files (split by domain)

`users.json` (authn) — `password` falls back to `username` when omitted:

```json
{ "users": [ { "username": "the_headless", "email": "...", "display_name": "Eddard Stark" } ] }
```

`venues.json` (venue) — `key` is a symbolic reference used by assignments:

```json
{ "venues": [ { "key": "stark", "name": "House Stark", "address": "...", "description": "..." } ] }
```

`assignments.json` (authz) — grants a role to users on a venue, referenced by key/username:

```json
{ "assignments": [ { "venue": "stark", "role_id": "venue.owner", "usernames": ["the_headless"] } ] }
```

Usernames double as passwords, so every username must be at least 8 characters.

### Prerequisites

The stack must be running and already seeded with the admin user and roles:

```bash
ristops seed-authn -p <admin_pwd>   # admin user (authn)
ristops seed-authz                  # roles + admin ACL (authz)
```

Because there is no user-lookup-by-username API, the seed maps usernames to ids from the creation
responses in-memory and is **not** idempotent. Re-run against a freshly reset dataset.

The whole nuke → seed-services → seed-demo flow is scripted (defaults match the local dev setup, and
requires the backend services to be running):

```bash
./scripts/reset-demo.sh
```

Equivalent manual steps:

```bash
ristops sql-database nuke be-authn -f
ristops sql-database nuke be-venue -f
ristops nuke-authz -f
ristops seed-authn -p <admin_pwd>
ristops seed-authz
ristops demo seed --users ... --venues ... --assignments ... --admin-password <admin_pwd>
```
