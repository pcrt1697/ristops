drop schema if exists ristops_authn cascade;
create schema ristops_authn authorization ristops;

create table ristops_authn.users (
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
