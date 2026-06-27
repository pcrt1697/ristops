// -- Root resource --
MERGE (:Resource {resource_type: "app", resource_id: "*"});

// -- Create permissions --
// wildcard permission to do everything on the resource
MERGE (:Permission {id: "*"});

MERGE (:Permission {id: "resource~add"});
MERGE (:Permission {id: "resource~remove"});
MERGE (:Permission {id: "resource~list"});

MERGE (:Permission {id: "user~get"});
MERGE (:Permission {id: "user~remove"});
MERGE (:Permission {id: "user~edit"});

MERGE (:Permission {id: "role~get"});
MERGE (:Permission {id: "role~list"});

MERGE (:Permission {id: "permission~list"});

MERGE (:Permission {id: "acl~get"});
MERGE (:Permission {id: "acl~add"});
MERGE (:Permission {id: "acl~remove"});
MERGE (:Permission {id: "acl~list"});

MERGE (:Permission {id: "venue~add"});
MERGE (:Permission {id: "venue~get"});
MERGE (:Permission {id: "venue~edit"});
MERGE (:Permission {id: "venue~remove"});

// -- Admin role --
MERGE (:Role {id: "admin", name: "Admin", description: "Administrator role with full access"});

// Assign permissions to admin role
MATCH (r:Role {id: "admin"})
MATCH (p:Permission {id: "*"})
MERGE (r)-[:GRANTS]->(p);

// -- Member role --
MERGE (:Role {id: "member", name: "Member", description: "Base role to let users access the app and manage their own account"});

// Assign permissions to member role
MATCH (r:Role {id: "member"})
MATCH (p:Permission)
WHERE p.id IN ["user~get", "user~edit", "user~remove", "role~list", "resource~list", "acl~get"]
MERGE (r)-[:GRANTS]->(p);
