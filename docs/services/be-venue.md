# be-venue

Venue registry service. Owns the canonical list of venues and acts as the root identity
reference for all other domain services.

> Source: [ristops-be-venue](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-be-venue/README.md)

## Role in the architecture

`be-venue` is intentionally thin. It manages the lifecycle of venue records and issues the
venue IDs that `be-reservation`, `be-menu`, and `be-order` reference. Keeping it as a
standalone service means venue identity has a clear owner from the start, avoiding a
retro-fit when lifecycle operations (enable/disable, metadata) are introduced later.

Staff assignment is not a venue concern — it is handled by `be-authz` via ACL rules on
venue resources.
