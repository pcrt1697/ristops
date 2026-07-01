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
WHERE p.id IN ["user:get", "user:edit", "user:remove", "role:list", "resource:list", "acl:get"]
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
MATCH (r:Role {id: "venue.manager"})
MATCH (p:Permission)
WHERE p.id IN ("venue:get", "venue:edit", "acl:list", "acl:remove", "acl:add")
MERGE (r)-[:GRANTS]->(p);

// -- Venue Member role --
MERGE (:Role {id: "venue.member", name: "Venue Member", description: "Role with base access to the venue", scope: "venue"});

// Assign permissions to venue member role
MATCH (r:Role {id: "venue.member"})
MATCH (p:Permission {id: "venue:get"})
MERGE (r)-[:GRANTS]->(p);

// -- Venue Server role --
MERGE (:Role {id: "venue.server", name: "Venue Server", description: "Role with base access to venue orders", scope: "venue"});

// Assign permissions to venue owner role
MATCH (r:Role {id: "venue.server"})
MATCH (p:Permission {id: "venue:get"})
MERGE (r)-[:GRANTS]->(p);
