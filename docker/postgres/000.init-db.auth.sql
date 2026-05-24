drop schema if exists ristops_auth cascade;
create schema ristops_auth authorization ristops;

create table ristops_auth.users (
  id uuid not null,
  username varchar(30) not null,
  display_name varchar(60),
  email varchar(320) not null,
  password varchar(255) not null,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id),
  unique (username),
  unique (email)
);


insert into ristops_auth.roles (id, name, description) values
('system.admin', 'Admin', 'Administrator: can do everything')
;

insert into permissions (id) values
('user.get'),
('user.list'),
('user.add'),
('user.edit'),
('user.remove')
;

insert into ristops_auth.role_permissions (id, role_id, permission_id)
select gen_random_uuid(), 'system.admin', id from permissions
;
