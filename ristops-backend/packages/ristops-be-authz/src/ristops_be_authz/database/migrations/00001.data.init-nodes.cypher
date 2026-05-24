// -- Root resource --
MERGE (:Resource {id: "app~*", resource_id: "*", resource_type: "app"});

// -- Create permissions --
// wildcard permission to do everything on the resource
MERGE (:Permission {id: "*"});
MERGE (:Permission {id: "resource~add"});
MERGE (:Permission {id: "resource~remove"});

// -- Admin role --
MERGE (:Role {id: "admin", name: "Admin", description: "Administrator role with full access"});

// Assign permissions to admin role
MATCH (r:Role {id: "admin"})
MATCH (p:Permission {id: "*"})
MERGE (r)-[:GRANTS]->(p);

// -- Member role --
MERGE (:Role {id: "member", name: "Member", description: "Base role to let users access the app and manage its own account"});

// Assign permissions to member role
MATCH (r:Role {id: "member"})
MATCH (p:Permission {id: "*"})
MERGE (r)-[:GRANTS]->(p);
