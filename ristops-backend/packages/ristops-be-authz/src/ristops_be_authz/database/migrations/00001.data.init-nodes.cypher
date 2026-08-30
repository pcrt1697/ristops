// -- Root resource --
MERGE (:Resource {resource_type: "app", resource_id: "*"});

// -- Create permissions --
// wildcard permission to do everything on the resource
MERGE (:Permission {id: "*"});

MERGE (:Permission {id: "resource:add"});
MERGE (:Permission {id: "resource:remove"});
MERGE (:Permission {id: "resource:list"});

MERGE (:Permission {id: "user:get"});
MERGE (:Permission {id: "user:remove"});
MERGE (:Permission {id: "user:edit"});

MERGE (:Permission {id: "role:get"});
MERGE (:Permission {id: "role:list"});

MERGE (:Permission {id: "permission:list"});

MERGE (:Permission {id: "acl:get"});
MERGE (:Permission {id: "acl:add"});
MERGE (:Permission {id: "acl:remove"});
MERGE (:Permission {id: "acl:list"});

MERGE (:Permission {id: "venue:add"});
MERGE (:Permission {id: "venue:get"});
MERGE (:Permission {id: "venue:edit"});
MERGE (:Permission {id: "venue:remove"});
MERGE (:Permission {id: "venue:list"});
MERGE (:Permission {id: "venue:activate"});
MERGE (:Permission {id: "venue:close"});
MERGE (:Permission {id: "venue:disable"});
MERGE (:Permission {id: "venue:enable"});

MERGE (:Permission {id: "service:add"});
MERGE (:Permission {id: "service:get"});
MERGE (:Permission {id: "service:edit"});
MERGE (:Permission {id: "service:remove"});
MERGE (:Permission {id: "service:list"});

MERGE (:Permission {id: "schedule:add"});
MERGE (:Permission {id: "schedule:get"});
MERGE (:Permission {id: "schedule:edit"});
MERGE (:Permission {id: "schedule:remove"});
MERGE (:Permission {id: "schedule:list"});

MERGE (:Permission {id: "reservation:add"});
MERGE (:Permission {id: "reservation:get"});
MERGE (:Permission {id: "reservation:edit"});
MERGE (:Permission {id: "reservation:list"});
MERGE (:Permission {id: "reservation:confirm"});
MERGE (:Permission {id: "reservation:reject"});
MERGE (:Permission {id: "reservation:cancel"});
MERGE (:Permission {id: "reservation:check-in"});
MERGE (:Permission {id: "reservation:no-show"});
MERGE (:Permission {id: "reservation:withdraw"});

// -- Admin role --
MERGE (:Role {id: "admin", name: "Admin", description: "Administrator role with full access", scope: "app"});

// Assign permissions to admin role
MATCH (r:Role {id: "admin"})
MATCH (p:Permission {id: "*"})
MERGE (r)-[:GRANTS]->(p);

// -- Member role --
MERGE (:Role {id: "member", name: "Member", description: "Base role to let users access the app and manage their own account", scope: "user"});

// Assign permissions to member role
MATCH (r:Role {id: "member"})
MATCH (p:Permission)
WHERE p.id IN ["user:get", "user:edit", "user:remove", "role:list", "resource:list", "acl:get", "role:get"]
MERGE (r)-[:GRANTS]->(p);

// -- Developer role --
MERGE (:Role {id: "developer", name: "Developer", description: "Role with all fine grained permissions on the app", scope: "app"});

// Assign permissions to developer role
MATCH (r:Role {id: "developer"})
MATCH (p:Permission)
WHERE p.id <> "*" AND NOT p.id STARTS WITH "app:"
MERGE (r)-[:GRANTS]->(p);

// -- Venue Owner role --
MERGE (:Role {id: "venue.owner", name: "Venue Owner", description: "Role with full access to the venue", scope: "venue"});

// Assign permissions to venue owner role
MATCH (r:Role {id: "venue.owner"})
MATCH (p:Permission {id: "*"})
MERGE (r)-[:GRANTS]->(p);

// -- Venue Manager role --
MERGE (:Role {id: "venue.manager", name: "Venue Manager", description: "Role with permissions manage venue ACL, update venue information", scope: "venue"});

// Assign permissions to venue manager role
// Deliberately excludes venue lifecycle control: venue:activate/close is owner-only
// self-service, venue:disable/enable is app-admin-only (checked against the app resource, see
// be-venue's perform_action route). Also excludes venue:add/venue:list (checked against the
// app resource — inert on a venue-scoped role) and venue:remove (no endpoint checks it).
MATCH (r:Role {id: "venue.manager"})
MATCH (p:Permission)
WHERE p.id IN ["acl:list", "acl:remove", "acl:add", "venue:get", "venue:edit", "service:add", "service:get", "service:edit", "service:remove", "service:list", "schedule:add", "schedule:get", "schedule:edit", "schedule:remove", "schedule:list", "reservation:add", "reservation:get", "reservation:edit", "reservation:list", "reservation:confirm", "reservation:reject", "reservation:cancel", "reservation:check-in", "reservation:no-show", "reservation:withdraw"]
MERGE (r)-[:GRANTS]->(p);

// -- Venue Bartender role --
MERGE (:Role {id: "venue.bartender", name: "Venue Bartender", description: "Role with base access to venue orders", scope: "venue"});

// Assign permissions to venue bartender role
MATCH (r:Role {id: "venue.bartender"})
MATCH (p:Permission)
WHERE p.id IN ["venue:get", "service:get", "service:list", "schedule:get", "schedule:list", "reservation:get", "reservation:list"]
MERGE (r)-[:GRANTS]->(p);

// -- Venue Chef role --
MERGE (:Role {id: "venue.chef", name: "Venue Chef", description: "Role with base access to venue orders", scope: "venue"});

// Assign permissions to venue chef role
MATCH (r:Role {id: "venue.chef"})
MATCH (p:Permission)
WHERE p.id IN ["venue:get", "service:get", "service:list", "schedule:get", "schedule:list", "reservation:get", "reservation:list"]
MERGE (r)-[:GRANTS]->(p);

// -- Venue Server role --
MERGE (:Role {id: "venue.server", name: "Venue Server", description: "Role with base access to venue orders", scope: "venue"});

// Assign permissions to venue server role
// Front-of-house: view schedule/reservations plus mark arrivals (check-in) and no-shows.
// confirm/reject/cancel stay manager-only (owner covers everything via its wildcard grant).
MATCH (r:Role {id: "venue.server"})
MATCH (p:Permission)
WHERE p.id IN ["venue:get", "service:get", "service:list", "schedule:get", "schedule:list", "reservation:get", "reservation:list", "reservation:check-in", "reservation:no-show"]
MERGE (r)-[:GRANTS]->(p);


// Register the `expires_at` property key. A grant with no expiry sets it to null, which Cypher
// treats as a delete, so the key would otherwise never exist and every authorization query
// reading it would warn (UnknownPropertyKeyWarning). Writing it once registers the key
// permanently — tokens are never garbage-collected — so the seed node goes away again.
CREATE (a:Acl {id: '__expires_at_key_seed__', expires_at: '1970-01-01T00:00:00+00:00'});
MATCH (a:Acl {id: '__expires_at_key_seed__'}) DELETE a;
