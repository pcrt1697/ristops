drop schema if exists ristops_venue cascade;
create schema ristops_venue authorization ristops;

create table ristops_venue.venues (
  id uuid not null,
  name varchar(120) not null,
  address varchar(255) not null,
  description varchar(1000),
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id)
);
