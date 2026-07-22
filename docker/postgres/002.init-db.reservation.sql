create table ristops_reservation.venues (
  id uuid not null,
  timezone text not null,
  status varchar(20) not null,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id)
);

create table ristops_reservation.services (
  id uuid not null,
  venue_id uuid not null,
  name varchar(120) not null,
  turn_time_m integer not null,
  advance_notice_m integer not null,
  slot_interval_m integer not null,
  grace_period_m integer not null,
  description varchar(1000),
  deleted_at timestamp with time zone,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id),
  foreign key(venue_id) references ristops_reservation.venues (id) on delete restrict
);
create index ix_ristops_reservation_services_venue_id on ristops_reservation.services (venue_id);
create index ix_ristops_reservation_services_name on ristops_reservation.services (name);

create table ristops_reservation.openings (
  id uuid not null,
  service_id uuid not null,
  weekday varchar(9) not null,
  capacity integer not null,
  start_time time without time zone not null,
  end_time time without time zone not null,
  description varchar(1000),
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id),
  constraint uq_opening_service_weekday unique (service_id, weekday),
  foreign key(service_id) references ristops_reservation.services (id) on delete cascade
);
create index ix_ristops_reservation_openings_service_id on ristops_reservation.openings (service_id);

create table ristops_reservation.opening_overrides (
  id uuid not null,
  service_id uuid not null,
  date_start date not null,
  date_end date not null,
  capacity integer not null,
  start_time time without time zone not null,
  end_time time without time zone not null,
  description varchar(1000),
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id),
  foreign key(service_id) references ristops_reservation.services (id) on delete cascade
);
create index ix_ristops_reservation_opening_overrides_service_id on ristops_reservation.opening_overrides (service_id);

create table ristops_reservation.closings (
  id uuid not null,
  service_id uuid not null,
  date_start date not null,
  date_end date not null,
  description varchar(1000),
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id),
  foreign key(service_id) references ristops_reservation.services (id) on delete cascade
);
create index ix_ristops_reservation_closings_service_id on ristops_reservation.closings (service_id);

create table ristops_reservation.service_occurrences (
  id uuid not null,
  service_id uuid not null,
  date date not null,
  status varchar(20) not null,
  started_at timestamp with time zone not null,
  ended_at timestamp with time zone,
  created_at timestamp with time zone default now() not null,
  updated_at timestamp with time zone default now() not null,
  primary key (id),
  constraint uq_service_occurrence_service_date unique (service_id, date),
  foreign key(service_id) references ristops_reservation.services (id) on delete cascade
);
create index ix_ristops_reservation_service_occurrences_service_id on ristops_reservation.service_occurrences (service_id);
