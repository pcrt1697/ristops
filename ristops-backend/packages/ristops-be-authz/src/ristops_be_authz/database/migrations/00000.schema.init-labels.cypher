// Unique constraints (also create indexes automatically)
CREATE CONSTRAINT migration_id IF NOT EXISTS FOR (m:Migration) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT role_id IF NOT EXISTS FOR (r:Role) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT permission_id IF NOT EXISTS FOR (p:Permission) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT resource_id IF NOT EXISTS FOR (r:Resource) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT acl_id IF NOT EXISTS FOR (a:Acl) REQUIRE a.id IS UNIQUE;

// Additional indexes
CREATE INDEX resource_resource_id IF NOT EXISTS FOR (r:Resource) ON (r.resource_id);
CREATE INDEX resource_resource_type IF NOT EXISTS FOR (r:Resource) ON (r.resource_type);
