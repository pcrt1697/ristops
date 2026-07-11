# be-reservation

Reservation service. Owns venue reservation configuration, tables, and reservations, and
computes slot availability.

> Source: [ristops-be-reservation](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-be-reservation/README.md)

## Role in the architecture

`be-reservation` is a single deployable with a single PostgreSQL database. Configuration
(services, seatings, opening rules and per-date overrides), tables, and reservations all live
together so the availability check that prevents double-booking can be a single atomic
operation — the reason these concerns are not split across services.

Configuration is layered: base opening rules define the defaults, and dated overrides express
exceptions (modified hours or closures). Bookable slots are never stored; they are computed at
query time from the rules plus existing reservations. The service references venue IDs issued by
`be-venue` and reads venue metadata (including timezone) replicated locally, rather than calling
`be-venue` on hot paths.

For the decisions behind this design, see the be-reservation entries in the
[ADRs](../adr.md).

## Status

Service scaffold in place; the reservation configuration domain model is under active design.
