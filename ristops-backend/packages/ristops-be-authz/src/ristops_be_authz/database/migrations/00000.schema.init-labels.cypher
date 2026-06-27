// Unique constraints (also create indexes automatically)
CREATE CONSTRAINT migration_id IF NOT EXISTS FOR (m:Migration) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT role_id IF NOT EXISTS FOR (r:Role) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT permission_id IF NOT EXISTS FOR (p:Permission) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT resource_identity IF NOT EXISTS FOR (r:Resource) REQUIRE (r.resource_type, r.resource_id) IS UNIQUE;
CREATE CONSTRAINT acl_id IF NOT EXISTS FOR (a:Acl) REQUIRE a.id IS UNIQUE;

// Text indexes for searching the replicated user read-model by name (CONTAINS / ENDS WITH).
CREATE TEXT INDEX user_username IF NOT EXISTS FOR (u:User) ON (u.username);
CREATE TEXT INDEX user_display_name IF NOT EXISTS FOR (u:User) ON (u.display_name);
