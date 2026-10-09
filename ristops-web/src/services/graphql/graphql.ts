/* eslint-disable */
import type { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';
export type Maybe<T> = T | null;
export type InputMaybe<T> = T | null | undefined;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  /** Date (isoformat) */
  Date: { input: string; output: string; }
  /** Date with time (isoformat) */
  DateTime: { input: string; output: string; }
  /** Time (isoformat) */
  Time: { input: string; output: string; }
};

/** Access control entry granting a role to a user on a resource. */
export type Acl = {
  __typename?: 'Acl';
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** ACL identifier. */
  id: Scalars['String']['output'];
  /** Resource the access was granted on. */
  resource: AuthorizationResource;
  /** Role granted on the resource. */
  role: Role;
  /** User the access was granted to (public view). */
  user: Member;
};

/** Authorization resource definition. */
export type AuthorizationResource = {
  __typename?: 'AuthorizationResource';
  /** ACL resource identifier */
  resourceId: Scalars['String']['output'];
  /** ACL resource type */
  resourceType: ResourceType;
};

/** One business date of the calendar window. */
export type CalendarDay = {
  __typename?: 'CalendarDay';
  /** Venue-local business date. */
  businessDate: Scalars['Date']['output'];
  /** Whether a closing removes every service that would otherwise run. */
  closed: Scalars['Boolean']['output'];
  /** Services a closing removes that date which still hold bookings. They are not in `services`, since they no longer run. */
  closedServices: Array<ClosedServiceSummary>;
  /** Deleted services that still hold bookings that date. They are not in `services`, since they no longer run. */
  deletedServices: Array<DeletedServiceSummary>;
  /** Services running that date. */
  services: Array<CalendarServiceSummary>;
};

/** How full one service is on one business date. */
export type CalendarServiceSummary = {
  __typename?: 'CalendarServiceSummary';
  /** Seats taken by live bookings on the date. */
  booked: Scalars['Int']['output'];
  /** Seats the service can take on the date. */
  capacity: Scalars['Int']['output'];
  /** Venue-local closing datetime (naive); the next day for an overnight opening. */
  closesAt: Scalars['DateTime']['output'];
  /** Venue-local opening datetime (naive). */
  opensAt: Scalars['DateTime']['output'];
  /** Whether booked seats exceed capacity. */
  overCapacity: Scalars['Boolean']['output'];
  /** Seats still free on the date; negative when over capacity. */
  remaining: Scalars['Int']['output'];
  /** Number of live bookings on the date. */
  reservationCount: Scalars['Int']['output'];
  /** Service the summary belongs to. */
  serviceId: Scalars['String']['output'];
  /** Name of that service. */
  serviceName: Scalars['String']['output'];
};

/** A service a closing removes from one date while it still holds bookings. */
export type ClosedServiceSummary = {
  __typename?: 'ClosedServiceSummary';
  /** Pending or confirmed bookings still held on the service that day, which staff need to resolve. */
  reservationCount: Scalars['Int']['output'];
  /** Service the closing removes. */
  serviceId: Scalars['String']['output'];
  /** Name of that service. */
  serviceName: Scalars['String']['output'];
};

/** A date range over which the linked services do not run. */
export type Closing = {
  __typename?: 'Closing';
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** First date of the closing period (inclusive). */
  dateFrom: Scalars['Date']['output'];
  /** Last date of the closing period (inclusive). */
  dateTo: Scalars['Date']['output'];
  /** Description of this closing. */
  description?: Maybe<Scalars['String']['output']>;
  /** Closing identifier. */
  id: Scalars['String']['output'];
  /** Services this closing applies to. */
  serviceIds: Array<Scalars['String']['output']>;
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Venue this closing belongs to. */
  venueId: Scalars['String']['output'];
};

/** Information to create a closing. */
export type ClosingCreateInput = {
  /** First date of the closing period (inclusive). */
  dateFrom: Scalars['Date']['input'];
  /** Last date of the closing period (inclusive). */
  dateTo: Scalars['Date']['input'];
  /** Description of this closing. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Services this closing applies to. Pass every service of the venue for a venue-wide shutdown. */
  serviceIds: Array<Scalars['ID']['input']>;
};

/** Closing search filter. */
export type ClosingFilterInput = {
  /** Include closings ending on or after this date. */
  dateFrom?: InputMaybe<Scalars['Date']['input']>;
  /** Include closings starting on or before this date. */
  dateTo?: InputMaybe<Scalars['Date']['input']>;
  /** Return only closings applying to this service. */
  serviceId?: InputMaybe<Scalars['ID']['input']>;
};

/** A single page of results with pagination metadata. */
export type ClosingPage = {
  __typename?: 'ClosingPage';
  /** Items in the current page. */
  items: Array<Closing>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Closing search query. */
export type ClosingSearchInput = {
  /** Filter parameters. */
  filter?: InputMaybe<ClosingFilterInput>;
  /** Pagination parameters. */
  pagination?: InputMaybe<PaginationInput>;
  /** Sort instructions. */
  sort?: Array<ClosingSortFieldSortInput>;
};

/** Fields a closing search may be sorted by. */
export const ClosingSortField = {
  CreatedAt: 'CREATED_AT',
  DateFrom: 'DATE_FROM',
  DateTo: 'DATE_TO',
  Id: 'ID'
} as const;

export type ClosingSortField = typeof ClosingSortField[keyof typeof ClosingSortField];
/** A single sort instruction. */
export type ClosingSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: ClosingSortField;
};

/** Closing fields to update (only provided fields change). */
export type ClosingUpdateInput = {
  /** New first date of the closing period (inclusive). */
  dateFrom?: InputMaybe<Scalars['Date']['input']>;
  /** New last date of the closing period (inclusive). */
  dateTo?: InputMaybe<Scalars['Date']['input']>;
  /** New description (null clears it). */
  description?: InputMaybe<Scalars['String']['input']>;
  /** New complete set of services this closing applies to. */
  serviceIds?: InputMaybe<Array<Scalars['ID']['input']>>;
};

/** Information to create a reservation. */
export type CreateReservationInput = {
  /** Customer email. */
  contactEmail?: InputMaybe<Scalars['String']['input']>;
  /** Customer name. */
  contactName: Scalars['String']['input'];
  /** Customer phone number. */
  contactPhoneNumber?: InputMaybe<Scalars['String']['input']>;
  /** Staff notes. */
  notes?: InputMaybe<Scalars['String']['input']>;
  /** Number of people. */
  partySize: Scalars['Int']['input'];
  /** Reservation date and time as venue-local wall-clock (naive, no offset). */
  reservationDate: Scalars['DateTime']['input'];
  /** Service to book into. The time must fall within its window on the date. */
  serviceId: Scalars['ID']['input'];
  /** Venue to book at. */
  venueId: Scalars['ID']['input'];
};

/** Service information. */
export type CreateServiceInput = {
  /** Maximum number of seats bookable on any date the service runs. */
  capacity: Scalars['Int']['input'];
  /** First date the service runs on (inclusive). */
  dateFrom: Scalars['Date']['input'];
  /** Last date the service runs on (inclusive). Omit to run it indefinitely; set it equal to dateFrom for a one-shot service. */
  dateTo?: InputMaybe<Scalars['Date']['input']>;
  /** Description of the service. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Name of the service. */
  name: Scalars['String']['input'];
  /** Identifier of the venue this service belongs to. */
  venueId: Scalars['String']['input'];
};

/** Venue information. */
export type CreateVenueInput = {
  /** Address of the venue. */
  address: Scalars['String']['input'];
  /** Description of the venue. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Name of the venue. */
  name: Scalars['String']['input'];
};

/** A deleted service that still holds bookings on one date. */
export type DeletedServiceSummary = {
  __typename?: 'DeletedServiceSummary';
  /** Pending or confirmed bookings still held on the service that day, which staff need to resolve. */
  reservationCount: Scalars['Int']['output'];
  /** The deleted service. */
  serviceId: Scalars['String']['output'];
  /** Name of that service. */
  serviceName: Scalars['String']['output'];
};

/** Request to grant a role to a user on a resource. */
export type GrantAccessInput = {
  /** Optional expiry; the grant is ignored once this time passes. */
  expiresAt?: InputMaybe<Scalars['DateTime']['input']>;
  /** Resource identifier. */
  resourceId: Scalars['String']['input'];
  /** Resource type. */
  resourceType: ResourceType;
  /** Role to grant on the resource. */
  roleId: Scalars['String']['input'];
  /** ID of the user to grant access to. */
  userId: Scalars['String']['input'];
};

/** Input query to list grants. */
export type ListGrantsInput = {
  /** Resource identifier. */
  resourceId: Scalars['String']['input'];
  /** Resource type. */
  resourceType: ResourceType;
};

/** Input query to list roles. */
export type ListRolesInput = {
  /** Filter by permission using `contains` operator. */
  permission?: InputMaybe<Scalars['String']['input']>;
  /** Filter by role id using `contains` operator. */
  roleId?: InputMaybe<Scalars['String']['input']>;
  /** Filter by role name using `contains` operator. */
  roleName?: InputMaybe<Scalars['String']['input']>;
  /** Filter by the resource type the role can be assigned to. */
  scope?: InputMaybe<ResourceType>;
};

/** Public view of a user. */
export type Member = {
  __typename?: 'Member';
  /** Registration date. */
  createdAt: Scalars['DateTime']['output'];
  /** Display name of the member. */
  displayName?: Maybe<Scalars['String']['output']>;
  /** User identifier. */
  id: Scalars['String']['output'];
  /** Username of the member. */
  username: Scalars['String']['output'];
};

/** Member search filter. */
export type MemberFilterInput = {
  /** Filter by display name using `like` operator. */
  displayName?: InputMaybe<Scalars['String']['input']>;
  /** Filter by username using `like` operator. */
  username?: InputMaybe<Scalars['String']['input']>;
};

/** A single page of results with pagination metadata. */
export type MemberPage = {
  __typename?: 'MemberPage';
  /** Items in the current page. */
  items: Array<Member>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Member search query. */
export type MemberSearchInput = {
  /** Filter parameters. */
  filter?: InputMaybe<MemberFilterInput>;
  /** Pagination parameters. */
  pagination?: PaginationInput;
  /** Sort instructions. */
  sort?: Array<MemberSortFieldSortInput>;
};

/** Fields a member search may be sorted by. */
export const MemberSortField = {
  CreatedAt: 'CREATED_AT',
  DisplayName: 'DISPLAY_NAME',
  Id: 'ID',
  Username: 'USERNAME'
} as const;

export type MemberSortField = typeof MemberSortField[keyof typeof MemberSortField];
/** A single sort instruction. */
export type MemberSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: MemberSortField;
};

export type Mutation = {
  __typename?: 'Mutation';
  /** Activate a venue: owner action, valid from PENDING or CLOSED. */
  activateVenue: Venue;
  /** Cancel a reservation (customer-initiated). */
  cancelReservation: Reservation;
  /** Check a reservation in (records arrival). */
  checkInReservation: Reservation;
  /** Close a venue: owner action, valid only from ACTIVE. Soft — no data is lost. */
  closeVenue: Venue;
  /** Confirm (accept) a reservation. */
  confirmReservation: Reservation;
  /** Close one or more of a venue's services over a date range. */
  createClosing: Closing;
  /** Create a reservation. */
  createReservation: Reservation;
  /** Create a new service. */
  createService: Service;
  /** Create a new venue. */
  createVenue: Venue;
  /** Delete a closing. */
  deleteClosing: Scalars['Boolean']['output'];
  /** Delete a service. */
  deleteService: Scalars['Boolean']['output'];
  /** Disable a venue: app-admin action, valid from PENDING or ACTIVE. */
  disableVenue: Venue;
  /** Re-enable a venue: app-admin action, valid only from DISABLED. Lands on PENDING — the owner must still activate it, which requires at least one service configured. */
  enableVenue: Venue;
  /** Grant a role to a user on a resource */
  grantAccess: Acl;
  /** Mark a reservation as a no-show. */
  noShowReservation: Reservation;
  /** Reject (decline) a pending reservation. */
  rejectReservation: Reservation;
  /** Revoke a role from a user on a resource */
  revokeAccess: Scalars['Boolean']['output'];
  /** Update a closing. */
  updateClosing: Closing;
  /** Update current user data */
  updateMe: User;
  /** Update a reservation's editable fields. */
  updateReservation: Reservation;
  /** Update a service. */
  updateService: Service;
  /** Update user data by ID */
  updateUser: User;
  /** Update venue data */
  updateVenue: Venue;
  /** Replace a service's weekly opening hours. */
  upsertServiceOpenings: Array<Opening>;
  /** Withdraw a booking the venue can no longer honor (venue-initiated). */
  withdrawReservation: Reservation;
};


export type MutationActivateVenueArgs = {
  id: Scalars['ID']['input'];
};


export type MutationCancelReservationArgs = {
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
};


export type MutationCheckInReservationArgs = {
  arrivalTime?: InputMaybe<Scalars['Time']['input']>;
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
};


export type MutationCloseVenueArgs = {
  id: Scalars['ID']['input'];
};


export type MutationConfirmReservationArgs = {
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
};


export type MutationCreateClosingArgs = {
  id: Scalars['ID']['input'];
  input: ClosingCreateInput;
};


export type MutationCreateReservationArgs = {
  input: CreateReservationInput;
};


export type MutationCreateServiceArgs = {
  input: CreateServiceInput;
};


export type MutationCreateVenueArgs = {
  input: CreateVenueInput;
};


export type MutationDeleteClosingArgs = {
  closingId: Scalars['ID']['input'];
  id: Scalars['ID']['input'];
};


export type MutationDeleteServiceArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDisableVenueArgs = {
  id: Scalars['ID']['input'];
};


export type MutationEnableVenueArgs = {
  id: Scalars['ID']['input'];
};


export type MutationGrantAccessArgs = {
  input: GrantAccessInput;
};


export type MutationNoShowReservationArgs = {
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
};


export type MutationRejectReservationArgs = {
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
};


export type MutationRevokeAccessArgs = {
  input: RevokeAccessInput;
};


export type MutationUpdateClosingArgs = {
  closingId: Scalars['ID']['input'];
  id: Scalars['ID']['input'];
  input: ClosingUpdateInput;
};


export type MutationUpdateMeArgs = {
  input: UpdateUserInput;
};


export type MutationUpdateReservationArgs = {
  id: Scalars['ID']['input'];
  input: UpdateReservationInput;
};


export type MutationUpdateServiceArgs = {
  id: Scalars['ID']['input'];
  input: UpdateServiceInput;
};


export type MutationUpdateUserArgs = {
  id: Scalars['ID']['input'];
  input: UpdateUserInput;
};


export type MutationUpdateVenueArgs = {
  id: Scalars['ID']['input'];
  input: UpdateVenueInput;
};


export type MutationUpsertServiceOpeningsArgs = {
  input: Array<OpeningUpsertInput>;
  serviceId: Scalars['ID']['input'];
};


export type MutationWithdrawReservationArgs = {
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
};

/** A service's opening hours on one weekday. */
export type Opening = {
  __typename?: 'Opening';
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Description of this opening. */
  description?: Maybe<Scalars['String']['output']>;
  /** Time the service closes. An end at or before the start runs overnight, closing on the following day. */
  endTime: Scalars['Time']['output'];
  /** Opening identifier. */
  id: Scalars['String']['output'];
  /** Service this opening belongs to. */
  serviceId: Scalars['String']['output'];
  /** Time the service opens. */
  startTime: Scalars['Time']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Day of the week this opening applies to. */
  weekday: Weekday;
};

/** One weekday's opening hours within an openings upsert. */
export type OpeningUpsertInput = {
  /** Description of this opening. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Time the service closes. */
  endTime: Scalars['Time']['input'];
  /** Time the service opens. */
  startTime: Scalars['Time']['input'];
  /** Day of the week this opening applies to. */
  weekday: Weekday;
};

/** Pagination parameters. */
export type PaginationInput = {
  /** 0-indexed page number. */
  page?: Scalars['Int']['input'];
  /** Items per page. */
  pageSize?: Scalars['Int']['input'];
};

/** List of app permissions. */
export type PermissionsList = {
  __typename?: 'PermissionsList';
  /** List of permissions. */
  permissions: Array<Scalars['String']['output']>;
};

export type Query = {
  __typename?: 'Query';
  /** List app permissions */
  listPermissions: PermissionsList;
  /** List app roles */
  listRoles: RolesList;
  /** List services for a venue. */
  listServices: Array<Service>;
  /** Fetch authenticated user */
  me: User;
  /** Fetch a member (public user view) by ID */
  member: Member;
  /** Fetch roles assigned to the authenticated user on a resource */
  myGrants: UserRoleGrants;
  /** Fetch a reservation by ID. */
  reservation: Reservation;
  /** Per-day, per-service occupancy of a venue over a date window. */
  reservationCalendar: Array<CalendarDay>;
  /** Search a venue's reservations. */
  reservations: ReservationPage;
  /** Fetch role by ID */
  role: Role;
  /** Search members (public user view) */
  searchMembers: MemberPage;
  /** Search users with their granted roles on a resource (direct or inherited) */
  searchResourceGrants: ResourceUserGrantsPage;
  /** Search venues the user has access to. */
  searchVenues: VenuePage;
  /** Fetch service by ID */
  service: Service;
  /** A service's weekly opening hours. */
  serviceOpenings: Array<Opening>;
  /** Fetch user by ID */
  user: User;
  /** Fetch venue by ID */
  venue: Venue;
  /** Search a venue's closings. */
  venueClosings: ClosingPage;
};


export type QueryListPermissionsArgs = {
  input?: InputMaybe<Scalars['String']['input']>;
};


export type QueryListRolesArgs = {
  input: ListRolesInput;
};


export type QueryListServicesArgs = {
  includeDeleted?: InputMaybe<Scalars['Boolean']['input']>;
  name?: InputMaybe<Scalars['String']['input']>;
  venueId: Scalars['ID']['input'];
};


export type QueryMemberArgs = {
  id: Scalars['ID']['input'];
};


export type QueryMyGrantsArgs = {
  input: ListGrantsInput;
};


export type QueryReservationArgs = {
  id: Scalars['ID']['input'];
};


export type QueryReservationCalendarArgs = {
  dateFrom: Scalars['Date']['input'];
  dateTo: Scalars['Date']['input'];
  venueId: Scalars['ID']['input'];
};


export type QueryReservationsArgs = {
  input: ReservationSearchInput;
};


export type QueryRoleArgs = {
  roleId: Scalars['String']['input'];
};


export type QuerySearchMembersArgs = {
  input: MemberSearchInput;
};


export type QuerySearchResourceGrantsArgs = {
  input: SearchResourceGrantsInput;
};


export type QuerySearchVenuesArgs = {
  input: VenueSearchInput;
};


export type QueryServiceArgs = {
  id: Scalars['ID']['input'];
};


export type QueryServiceOpeningsArgs = {
  includeDeleted?: InputMaybe<Scalars['Boolean']['input']>;
  serviceId: Scalars['ID']['input'];
};


export type QueryUserArgs = {
  id: Scalars['ID']['input'];
};


export type QueryVenueArgs = {
  id: Scalars['ID']['input'];
};


export type QueryVenueClosingsArgs = {
  id: Scalars['ID']['input'];
  input?: InputMaybe<ClosingSearchInput>;
};

/** A reservation. */
export type Reservation = {
  __typename?: 'Reservation';
  /** Actual arrival time, once checked in. */
  arrivalTime?: Maybe<Scalars['Time']['output']>;
  /** Customer email. */
  contactEmail?: Maybe<Scalars['String']['output']>;
  /** Customer name. */
  contactName: Scalars['String']['output'];
  /** Customer phone number. */
  contactPhoneNumber?: Maybe<Scalars['String']['output']>;
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Reservation identifier. */
  id: Scalars['String']['output'];
  /** Free-form staff notes. */
  notes?: Maybe<Scalars['String']['output']>;
  /** Number of people. */
  partySize: Scalars['Int']['output'];
  /** Reservation date and time as venue-local wall-clock (naive, no offset). */
  reservationDate: Scalars['DateTime']['output'];
  /** Service this reservation is booked into. */
  serviceId: Scalars['String']['output'];
  /** Current status. */
  status: ReservationStatus;
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Venue this reservation belongs to. */
  venueId: Scalars['String']['output'];
  /** Set when the reservation no longer fits the current schedule (needs attention). */
  violation?: Maybe<ReservationViolation>;
};

/** Reservation search filter. */
export type ReservationFilterInput = {
  /** Include reservations on or after this business date. */
  dateFrom?: InputMaybe<Scalars['Date']['input']>;
  /** Include reservations on or before this business date. */
  dateTo?: InputMaybe<Scalars['Date']['input']>;
  /** Filter to reservations booked into this service. */
  serviceId?: InputMaybe<Scalars['ID']['input']>;
  /** Filter to reservations in any of these statuses. */
  status?: InputMaybe<Array<ReservationStatus>>;
  /** Venue to list reservations for. Mandatory. */
  venueId: Scalars['ID']['input'];
  /** Return only reservations that violate the current schedule. */
  violationsOnly?: Scalars['Boolean']['input'];
};

/** A single page of results with pagination metadata. */
export type ReservationPage = {
  __typename?: 'ReservationPage';
  /** Items in the current page. */
  items: Array<Reservation>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Reservation search query. */
export type ReservationSearchInput = {
  /** Filter parameters (venue mandatory). */
  filter: ReservationFilterInput;
  /** Pagination parameters. */
  pagination?: PaginationInput;
  /** Sort instructions. */
  sort?: Array<ReservationSortFieldSortInput>;
};

/** Fields a reservation search may be sorted by. */
export const ReservationSortField = {
  CreatedAt: 'CREATED_AT',
  Id: 'ID',
  ReservationDate: 'RESERVATION_DATE'
} as const;

export type ReservationSortField = typeof ReservationSortField[keyof typeof ReservationSortField];
/** A single sort instruction. */
export type ReservationSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: ReservationSortField;
};

/** Lifecycle status of a reservation. */
export const ReservationStatus = {
  Canceled: 'CANCELED',
  CheckedIn: 'CHECKED_IN',
  Confirmed: 'CONFIRMED',
  NoShow: 'NO_SHOW',
  Pending: 'PENDING',
  Rejected: 'REJECTED',
  Withdrawn: 'WITHDRAWN'
} as const;

export type ReservationStatus = typeof ReservationStatus[keyof typeof ReservationStatus];
/** Why a reservation no longer fits its service's current schedule. */
export const ReservationViolation = {
  Closed: 'CLOSED',
  NoService: 'NO_SERVICE',
  OutsideHours: 'OUTSIDE_HOURS'
} as const;

export type ReservationViolation = typeof ReservationViolation[keyof typeof ReservationViolation];
/** Fields a resource grants search may be sorted by. */
export const ResourceGrantSortField = {
  DisplayName: 'DISPLAY_NAME',
  Id: 'ID',
  Username: 'USERNAME'
} as const;

export type ResourceGrantSortField = typeof ResourceGrantSortField[keyof typeof ResourceGrantSortField];
/** A single sort instruction. */
export type ResourceGrantSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: ResourceGrantSortField;
};

/** Resource grants search filter. */
export type ResourceGrantsFilterInput = {
  /** Filter by display name using `like` operator. */
  displayName?: InputMaybe<Scalars['String']['input']>;
  /** Filter by permission using `contains` operator. */
  permission?: InputMaybe<Scalars['String']['input']>;
  /** Filter by role id using `contains` operator. */
  roleId?: InputMaybe<Scalars['String']['input']>;
  /** Filter by role name using `contains` operator. */
  roleName?: InputMaybe<Scalars['String']['input']>;
  /** Filter by the scope (resource type) of the roles the user holds. */
  scope?: InputMaybe<ResourceType>;
  /** Filter by username using `like` operator. */
  username?: InputMaybe<Scalars['String']['input']>;
};

export const ResourceType = {
  Acl: 'ACL',
  App: 'APP',
  Permission: 'PERMISSION',
  Reservation: 'RESERVATION',
  Role: 'ROLE',
  Service: 'SERVICE',
  User: 'USER',
  Venue: 'VENUE'
} as const;

export type ResourceType = typeof ResourceType[keyof typeof ResourceType];
/** A user and the roles they hold on a resource (direct or inherited). */
export type ResourceUserGrants = {
  __typename?: 'ResourceUserGrants';
  /** Roles the user holds on the resource. */
  grants: Array<RoleGrant>;
  /** The user the grants belong to (public view). */
  user: Member;
};

/** A single page of results with pagination metadata. */
export type ResourceUserGrantsPage = {
  __typename?: 'ResourceUserGrantsPage';
  /** Items in the current page. */
  items: Array<ResourceUserGrants>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Request to revoke a role from a user on a resource. */
export type RevokeAccessInput = {
  /** Resource identifier. */
  resourceId: Scalars['String']['input'];
  /** Resource type. */
  resourceType: ResourceType;
  /** Role to revoke on the resource. */
  roleId: Scalars['String']['input'];
  /** ID of the user to revoke access from. */
  userId: Scalars['String']['input'];
};

/** Role entity information. */
export type Role = {
  __typename?: 'Role';
  /** Description of the role. */
  description: Scalars['String']['output'];
  /** Role identifier. */
  id: Scalars['String']['output'];
  /** Name of the role. */
  name: Scalars['String']['output'];
  /** List of permissions granted by the role. */
  permissions: Array<Scalars['String']['output']>;
  /** Resource type this role can be assigned to. */
  scope: ResourceType;
};

/** A role granted to a user on a resource. */
export type RoleGrant = {
  __typename?: 'RoleGrant';
  /** Assignment date. */
  assignedAt: Scalars['DateTime']['output'];
  /** Optional grant expiry time. */
  expiresAt?: Maybe<Scalars['DateTime']['output']>;
  /** Resource the role is granted on. */
  resource: AuthorizationResource;
  /** Role granted on the resource. */
  role: Role;
};

/** List of app roles. */
export type RolesList = {
  __typename?: 'RolesList';
  /** List of roles. */
  roles: Array<Role>;
};

/** Resource grants search query. */
export type SearchResourceGrantsInput = {
  /** Filter parameters. */
  filter?: InputMaybe<ResourceGrantsFilterInput>;
  /** Pagination parameters. */
  pagination?: PaginationInput;
  /** Resource identifier. */
  resourceId: Scalars['String']['input'];
  /** Resource type. */
  resourceType: ResourceType;
  /** Sort instructions. */
  sort?: Array<ResourceGrantSortFieldSortInput>;
};

/** Service entity information. */
export type Service = {
  __typename?: 'Service';
  /** Maximum number of seats bookable on any date the service runs. */
  capacity: Scalars['Int']['output'];
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** First date the service runs on (inclusive). */
  dateFrom: Scalars['Date']['output'];
  /** Last date the service runs on (inclusive); null runs it indefinitely. */
  dateTo?: Maybe<Scalars['Date']['output']>;
  /** Deletion date, if the service has been deleted. */
  deletedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Description of the service. */
  description?: Maybe<Scalars['String']['output']>;
  /** Service identifier. */
  id: Scalars['String']['output'];
  /** Name of the service. */
  name: Scalars['String']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Venue this service belongs to. */
  venue: Venue;
};

/** Direction of a sort clause. */
export const SortDirection = {
  Asc: 'ASC',
  Desc: 'DESC'
} as const;

export type SortDirection = typeof SortDirection[keyof typeof SortDirection];
/** Reservation fields to update (only provided fields change). */
export type UpdateReservationInput = {
  /** New customer name. */
  contactName?: InputMaybe<Scalars['String']['input']>;
  /** New phone number (null clears it). */
  contactPhoneNumber?: InputMaybe<Scalars['String']['input']>;
  /** New staff notes (null clears them). */
  notes?: InputMaybe<Scalars['String']['input']>;
  /** New party size. */
  partySize?: InputMaybe<Scalars['Int']['input']>;
  /** New reservation date and time as venue-local wall-clock (naive, no offset). */
  reservationDate?: InputMaybe<Scalars['DateTime']['input']>;
  /** Move the booking to this service, checked like a new booking. Gives a booking left on a closed or deleted service a new one. */
  serviceId?: InputMaybe<Scalars['ID']['input']>;
};

/** Service information to update. */
export type UpdateServiceInput = {
  /** New maximum number of seats bookable on any date the service runs. */
  capacity?: InputMaybe<Scalars['Int']['input']>;
  /** New first date the service runs on (inclusive). */
  dateFrom?: InputMaybe<Scalars['Date']['input']>;
  /** New last date the service runs on (null runs it indefinitely). */
  dateTo?: InputMaybe<Scalars['Date']['input']>;
  /** New description of the service (null clears it). */
  description?: InputMaybe<Scalars['String']['input']>;
  /** New name of the service. */
  name?: InputMaybe<Scalars['String']['input']>;
};

/** User information to update. */
export type UpdateUserInput = {
  /** New display name of the user. */
  displayName?: InputMaybe<Scalars['String']['input']>;
  /** New email address of the user. */
  email?: InputMaybe<Scalars['String']['input']>;
  /** New password of the user. */
  password?: InputMaybe<Scalars['String']['input']>;
  /** New username of the user. */
  username?: InputMaybe<Scalars['String']['input']>;
};

/** Venue information to update. */
export type UpdateVenueInput = {
  /** New address of the venue. */
  address?: InputMaybe<Scalars['String']['input']>;
  /** New description of the venue. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** New name of the venue. */
  name?: InputMaybe<Scalars['String']['input']>;
};

/** User entity information. */
export type User = {
  __typename?: 'User';
  /** Registration date. */
  createdAt: Scalars['DateTime']['output'];
  /** Display name of the user. */
  displayName?: Maybe<Scalars['String']['output']>;
  /** Email address of the user. */
  email: Scalars['String']['output'];
  /** User identifier. */
  id: Scalars['String']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Username of the user. */
  username: Scalars['String']['output'];
};

/** Resource the user has access to, given a specific set of permissions. */
export type UserRoleGrant = {
  __typename?: 'UserRoleGrant';
  /** Resource identifier. */
  resource: AuthorizationResource;
  /** Role assigned on the resource. */
  role: Role;
};

/** Resources the user has access to, given a specific set of permissions. */
export type UserRoleGrants = {
  __typename?: 'UserRoleGrants';
  /** List of resources the user has access to, given a specific set of permissions. */
  grants: Array<UserRoleGrant>;
};

/** Venue entity information. */
export type Venue = {
  __typename?: 'Venue';
  /** Address of the venue. */
  address: Scalars['String']['output'];
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Description of the venue. */
  description?: Maybe<Scalars['String']['output']>;
  /** Venue identifier. */
  id: Scalars['String']['output'];
  /** Name of the venue. */
  name: Scalars['String']['output'];
  /** Current lifecycle status of the venue. */
  status: VenueStatus;
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
};

/** Venue search filter. */
export type VenueFilterInput = {
  /** Filter by venue name using `like` operator. */
  name?: InputMaybe<Scalars['String']['input']>;
};

/** A single page of results with pagination metadata. */
export type VenuePage = {
  __typename?: 'VenuePage';
  /** Items in the current page. */
  items: Array<Venue>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Venue search query. */
export type VenueSearchInput = {
  /** Filter parameters. */
  filter?: InputMaybe<VenueFilterInput>;
  /** Pagination parameters. */
  pagination?: PaginationInput;
  /** Sort instructions. */
  sort?: Array<VenueSortFieldSortInput>;
};

/** Fields a venue search may be sorted by. */
export const VenueSortField = {
  CreatedAt: 'CREATED_AT',
  Id: 'ID',
  Name: 'NAME'
} as const;

export type VenueSortField = typeof VenueSortField[keyof typeof VenueSortField];
/** A single sort instruction. */
export type VenueSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: VenueSortField;
};

/** Lifecycle status of a venue. */
export const VenueStatus = {
  Active: 'ACTIVE',
  Closed: 'CLOSED',
  Disabled: 'DISABLED',
  Pending: 'PENDING'
} as const;

export type VenueStatus = typeof VenueStatus[keyof typeof VenueStatus];
/** Day of the week an opening applies to. */
export const Weekday = {
  Friday: 'FRIDAY',
  Monday: 'MONDAY',
  Saturday: 'SATURDAY',
  Sunday: 'SUNDAY',
  Thursday: 'THURSDAY',
  Tuesday: 'TUESDAY',
  Wednesday: 'WEDNESDAY'
} as const;

export type Weekday = typeof Weekday[keyof typeof Weekday];
export type ListMyGrantsQueryVariables = Exact<{
  input: ListGrantsInput;
}>;


export type ListMyGrantsQuery = { __typename?: 'Query', myGrants: { __typename?: 'UserRoleGrants', grants: Array<{ __typename?: 'UserRoleGrant', resource: { __typename?: 'AuthorizationResource', resourceId: string, resourceType: ResourceType }, role: { __typename?: 'Role', id: string, name: string, description: string, permissions: Array<string>, scope: ResourceType } }> } };

export type ListRolesQueryVariables = Exact<{
  input: ListRolesInput;
}>;


export type ListRolesQuery = { __typename?: 'Query', listRoles: { __typename?: 'RolesList', roles: Array<{ __typename?: 'Role', id: string, scope: ResourceType, name: string, description: string, permissions: Array<string> }> } };

export type ListPermissionsQueryVariables = Exact<{
  query?: InputMaybe<Scalars['String']['input']>;
}>;


export type ListPermissionsQuery = { __typename?: 'Query', listPermissions: { __typename?: 'PermissionsList', permissions: Array<string> } };

export type SearchResourceGrantsQueryVariables = Exact<{
  input: SearchResourceGrantsInput;
}>;


export type SearchResourceGrantsQuery = { __typename?: 'Query', searchResourceGrants: { __typename?: 'ResourceUserGrantsPage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'ResourceUserGrants', user: { __typename?: 'Member', id: string, username: string, displayName?: string | null }, grants: Array<{ __typename?: 'RoleGrant', assignedAt: string, expiresAt?: string | null, role: { __typename?: 'Role', id: string, name: string, description: string, permissions: Array<string>, scope: ResourceType }, resource: { __typename?: 'AuthorizationResource', resourceId: string, resourceType: ResourceType } }> }> } };

export type SearchMembersQueryVariables = Exact<{
  input: MemberSearchInput;
}>;


export type SearchMembersQuery = { __typename?: 'Query', searchMembers: { __typename?: 'MemberPage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'Member', id: string, username: string, displayName?: string | null }> } };

export type GrantAccessMutationVariables = Exact<{
  input: GrantAccessInput;
}>;


export type GrantAccessMutation = { __typename?: 'Mutation', grantAccess: { __typename?: 'Acl', id: string } };

export type RevokeAccessMutationVariables = Exact<{
  input: RevokeAccessInput;
}>;


export type RevokeAccessMutation = { __typename?: 'Mutation', revokeAccess: boolean };

export type GetMeQueryVariables = Exact<{ [key: string]: never; }>;


export type GetMeQuery = { __typename?: 'Query', me: { __typename?: 'User', id: string, username: string, displayName?: string | null, email: string, createdAt: string, updatedAt: string } };

export type UpdateMeMutationVariables = Exact<{
  input: UpdateUserInput;
}>;


export type UpdateMeMutation = { __typename?: 'Mutation', updateMe: { __typename?: 'User', id: string, username: string, displayName?: string | null, email: string, createdAt: string, updatedAt: string } };

export type ReservationFieldsFragment = { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string };

export type GetReservationQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetReservationQuery = { __typename?: 'Query', reservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type SearchReservationsQueryVariables = Exact<{
  input: ReservationSearchInput;
}>;


export type SearchReservationsQuery = { __typename?: 'Query', reservations: { __typename?: 'ReservationPage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string }> } };

export type ReservationCalendarQueryVariables = Exact<{
  venueId: Scalars['ID']['input'];
  dateFrom: Scalars['Date']['input'];
  dateTo: Scalars['Date']['input'];
}>;


export type ReservationCalendarQuery = { __typename?: 'Query', reservationCalendar: Array<{ __typename?: 'CalendarDay', businessDate: string, closed: boolean, services: Array<{ __typename?: 'CalendarServiceSummary', serviceId: string, serviceName: string, opensAt: string, closesAt: string, capacity: number, booked: number, remaining: number, reservationCount: number, overCapacity: boolean }>, closedServices: Array<{ __typename?: 'ClosedServiceSummary', serviceId: string, serviceName: string, reservationCount: number }>, deletedServices: Array<{ __typename?: 'DeletedServiceSummary', serviceId: string, serviceName: string, reservationCount: number }> }> };

export type CreateReservationMutationVariables = Exact<{
  input: CreateReservationInput;
}>;


export type CreateReservationMutation = { __typename?: 'Mutation', createReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type UpdateReservationMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: UpdateReservationInput;
}>;


export type UpdateReservationMutation = { __typename?: 'Mutation', updateReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type ConfirmReservationMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
}>;


export type ConfirmReservationMutation = { __typename?: 'Mutation', confirmReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type RejectReservationMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
}>;


export type RejectReservationMutation = { __typename?: 'Mutation', rejectReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type CancelReservationMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
}>;


export type CancelReservationMutation = { __typename?: 'Mutation', cancelReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type CheckInReservationMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  arrivalTime?: InputMaybe<Scalars['Time']['input']>;
  notes?: InputMaybe<Scalars['String']['input']>;
}>;


export type CheckInReservationMutation = { __typename?: 'Mutation', checkInReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type NoShowReservationMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
}>;


export type NoShowReservationMutation = { __typename?: 'Mutation', noShowReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type WithdrawReservationMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  notes?: InputMaybe<Scalars['String']['input']>;
}>;


export type WithdrawReservationMutation = { __typename?: 'Mutation', withdrawReservation: { __typename?: 'Reservation', id: string, venueId: string, serviceId: string, status: ReservationStatus, reservationDate: string, partySize: number, arrivalTime?: string | null, contactName: string, contactPhoneNumber?: string | null, contactEmail?: string | null, notes?: string | null, violation?: ReservationViolation | null, createdAt: string, updatedAt: string } };

export type OpeningFieldsFragment = { __typename?: 'Opening', id: string, serviceId: string, weekday: Weekday, startTime: string, endTime: string, description?: string | null };

export type ClosingFieldsFragment = { __typename?: 'Closing', id: string, venueId: string, dateFrom: string, dateTo: string, serviceIds: Array<string>, description?: string | null, createdAt: string, updatedAt: string };

export type ListServiceOpeningsQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
}>;


export type ListServiceOpeningsQuery = { __typename?: 'Query', serviceOpenings: Array<{ __typename?: 'Opening', id: string, serviceId: string, weekday: Weekday, startTime: string, endTime: string, description?: string | null }> };

export type UpsertServiceOpeningsMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input: Array<OpeningUpsertInput> | OpeningUpsertInput;
}>;


export type UpsertServiceOpeningsMutation = { __typename?: 'Mutation', upsertServiceOpenings: Array<{ __typename?: 'Opening', id: string, serviceId: string, weekday: Weekday, startTime: string, endTime: string, description?: string | null }> };

export type SearchClosingsQueryVariables = Exact<{
  id: Scalars['ID']['input'];
  input?: InputMaybe<ClosingSearchInput>;
}>;


export type SearchClosingsQuery = { __typename?: 'Query', venueClosings: { __typename?: 'ClosingPage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'Closing', id: string, venueId: string, dateFrom: string, dateTo: string, serviceIds: Array<string>, description?: string | null, createdAt: string, updatedAt: string }> } };

export type CreateClosingMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: ClosingCreateInput;
}>;


export type CreateClosingMutation = { __typename?: 'Mutation', createClosing: { __typename?: 'Closing', id: string, venueId: string, dateFrom: string, dateTo: string, serviceIds: Array<string>, description?: string | null, createdAt: string, updatedAt: string } };

export type UpdateClosingMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  closingId: Scalars['ID']['input'];
  input: ClosingUpdateInput;
}>;


export type UpdateClosingMutation = { __typename?: 'Mutation', updateClosing: { __typename?: 'Closing', id: string, venueId: string, dateFrom: string, dateTo: string, serviceIds: Array<string>, description?: string | null, createdAt: string, updatedAt: string } };

export type DeleteClosingMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  closingId: Scalars['ID']['input'];
}>;


export type DeleteClosingMutation = { __typename?: 'Mutation', deleteClosing: boolean };

export type ServiceFieldsFragment = { __typename?: 'Service', id: string, name: string, description?: string | null, dateFrom: string, dateTo?: string | null, capacity: number, deletedAt?: string | null, createdAt: string, updatedAt: string };

export type GetServiceQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetServiceQuery = { __typename?: 'Query', service: { __typename?: 'Service', id: string, name: string, description?: string | null, dateFrom: string, dateTo?: string | null, capacity: number, deletedAt?: string | null, createdAt: string, updatedAt: string, venue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } } };

export type ListServicesQueryVariables = Exact<{
  venueId: Scalars['ID']['input'];
  name?: InputMaybe<Scalars['String']['input']>;
  includeDeleted?: InputMaybe<Scalars['Boolean']['input']>;
}>;


export type ListServicesQuery = { __typename?: 'Query', listServices: Array<{ __typename?: 'Service', id: string, name: string, description?: string | null, dateFrom: string, dateTo?: string | null, capacity: number, deletedAt?: string | null, createdAt: string, updatedAt: string }> };

export type CreateServiceMutationVariables = Exact<{
  input: CreateServiceInput;
}>;


export type CreateServiceMutation = { __typename?: 'Mutation', createService: { __typename?: 'Service', id: string, name: string, description?: string | null, dateFrom: string, dateTo?: string | null, capacity: number, deletedAt?: string | null, createdAt: string, updatedAt: string } };

export type UpdateServiceMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: UpdateServiceInput;
}>;


export type UpdateServiceMutation = { __typename?: 'Mutation', updateService: { __typename?: 'Service', id: string, name: string, description?: string | null, dateFrom: string, dateTo?: string | null, capacity: number, deletedAt?: string | null, createdAt: string, updatedAt: string } };

export type DeleteServiceMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeleteServiceMutation = { __typename?: 'Mutation', deleteService: boolean };

export type SearchVenuesQueryVariables = Exact<{
  input: VenueSearchInput;
}>;


export type SearchVenuesQuery = { __typename?: 'Query', searchVenues: { __typename?: 'VenuePage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string }> } };

export type GetVenueQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetVenueQuery = { __typename?: 'Query', venue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } };

export type CreateVenueMutationVariables = Exact<{
  input: CreateVenueInput;
}>;


export type CreateVenueMutation = { __typename?: 'Mutation', createVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } };

export type UpdateVenueMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: UpdateVenueInput;
}>;


export type UpdateVenueMutation = { __typename?: 'Mutation', updateVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } };

export type ActivateVenueMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type ActivateVenueMutation = { __typename?: 'Mutation', activateVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } };

export type CloseVenueMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type CloseVenueMutation = { __typename?: 'Mutation', closeVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } };

export type DisableVenueMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DisableVenueMutation = { __typename?: 'Mutation', disableVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } };

export type EnableVenueMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type EnableVenueMutation = { __typename?: 'Mutation', enableVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } };

export const ReservationFieldsFragmentDoc = {"kind":"Document","definitions":[{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<ReservationFieldsFragment, unknown>;
export const OpeningFieldsFragmentDoc = {"kind":"Document","definitions":[{"kind":"FragmentDefinition","name":{"kind":"Name","value":"OpeningFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Opening"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"description"}}]}}]} as unknown as DocumentNode<OpeningFieldsFragment, unknown>;
export const ClosingFieldsFragmentDoc = {"kind":"Document","definitions":[{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ClosingFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Closing"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"serviceIds"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<ClosingFieldsFragment, unknown>;
export const ServiceFieldsFragmentDoc = {"kind":"Document","definitions":[{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ServiceFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Service"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<ServiceFieldsFragment, unknown>;
export const ListMyGrantsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListMyGrants"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ListGrantsInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"myGrants"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"grants"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resource"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resourceId"}},{"kind":"Field","name":{"kind":"Name","value":"resourceType"}}]}},{"kind":"Field","name":{"kind":"Name","value":"role"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}}]}}]}}]}}]}}]} as unknown as DocumentNode<ListMyGrantsQuery, ListMyGrantsQueryVariables>;
export const ListRolesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListRoles"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ListRolesInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listRoles"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"roles"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]}}]} as unknown as DocumentNode<ListRolesQuery, ListRolesQueryVariables>;
export const ListPermissionsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListPermissions"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"query"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listPermissions"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"query"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]} as unknown as DocumentNode<ListPermissionsQuery, ListPermissionsQueryVariables>;
export const SearchResourceGrantsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchResourceGrants"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"SearchResourceGrantsInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchResourceGrants"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"user"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}}]}},{"kind":"Field","name":{"kind":"Name","value":"grants"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"role"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}}]}},{"kind":"Field","name":{"kind":"Name","value":"resource"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resourceId"}},{"kind":"Field","name":{"kind":"Name","value":"resourceType"}}]}},{"kind":"Field","name":{"kind":"Name","value":"assignedAt"}},{"kind":"Field","name":{"kind":"Name","value":"expiresAt"}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchResourceGrantsQuery, SearchResourceGrantsQueryVariables>;
export const SearchMembersDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchMembers"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"MemberSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchMembers"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchMembersQuery, SearchMembersQueryVariables>;
export const GrantAccessDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"GrantAccess"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"GrantAccessInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"grantAccess"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<GrantAccessMutation, GrantAccessMutationVariables>;
export const RevokeAccessDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"RevokeAccess"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"RevokeAccessInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"revokeAccess"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}]}]}}]} as unknown as DocumentNode<RevokeAccessMutation, RevokeAccessMutationVariables>;
export const GetMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetMe"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"me"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetMeQuery, GetMeQueryVariables>;
export const UpdateMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateMe"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateUserInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateMe"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateMeMutation, UpdateMeMutationVariables>;
export const GetReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"reservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<GetReservationQuery, GetReservationQueryVariables>;
export const SearchReservationsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchReservations"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ReservationSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"reservations"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<SearchReservationsQuery, SearchReservationsQueryVariables>;
export const ReservationCalendarDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ReservationCalendar"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"dateFrom"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Date"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"dateTo"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"Date"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"reservationCalendar"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"venueId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"dateFrom"},"value":{"kind":"Variable","name":{"kind":"Name","value":"dateFrom"}}},{"kind":"Argument","name":{"kind":"Name","value":"dateTo"},"value":{"kind":"Variable","name":{"kind":"Name","value":"dateTo"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"businessDate"}},{"kind":"Field","name":{"kind":"Name","value":"closed"}},{"kind":"Field","name":{"kind":"Name","value":"services"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceName"}},{"kind":"Field","name":{"kind":"Name","value":"opensAt"}},{"kind":"Field","name":{"kind":"Name","value":"closesAt"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"booked"}},{"kind":"Field","name":{"kind":"Name","value":"remaining"}},{"kind":"Field","name":{"kind":"Name","value":"reservationCount"}},{"kind":"Field","name":{"kind":"Name","value":"overCapacity"}}]}},{"kind":"Field","name":{"kind":"Name","value":"closedServices"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceName"}},{"kind":"Field","name":{"kind":"Name","value":"reservationCount"}}]}},{"kind":"Field","name":{"kind":"Name","value":"deletedServices"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceName"}},{"kind":"Field","name":{"kind":"Name","value":"reservationCount"}}]}}]}}]}}]} as unknown as DocumentNode<ReservationCalendarQuery, ReservationCalendarQueryVariables>;
export const CreateReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CreateReservationInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<CreateReservationMutation, CreateReservationMutationVariables>;
export const UpdateReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateReservationInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<UpdateReservationMutation, UpdateReservationMutationVariables>;
export const ConfirmReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"ConfirmReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"notes"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"confirmReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"notes"},"value":{"kind":"Variable","name":{"kind":"Name","value":"notes"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<ConfirmReservationMutation, ConfirmReservationMutationVariables>;
export const RejectReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"RejectReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"notes"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"rejectReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"notes"},"value":{"kind":"Variable","name":{"kind":"Name","value":"notes"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<RejectReservationMutation, RejectReservationMutationVariables>;
export const CancelReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CancelReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"notes"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"cancelReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"notes"},"value":{"kind":"Variable","name":{"kind":"Name","value":"notes"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<CancelReservationMutation, CancelReservationMutationVariables>;
export const CheckInReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CheckInReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"arrivalTime"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Time"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"notes"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"checkInReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"arrivalTime"},"value":{"kind":"Variable","name":{"kind":"Name","value":"arrivalTime"}}},{"kind":"Argument","name":{"kind":"Name","value":"notes"},"value":{"kind":"Variable","name":{"kind":"Name","value":"notes"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<CheckInReservationMutation, CheckInReservationMutationVariables>;
export const NoShowReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"NoShowReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"notes"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"noShowReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"notes"},"value":{"kind":"Variable","name":{"kind":"Name","value":"notes"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<NoShowReservationMutation, NoShowReservationMutationVariables>;
export const WithdrawReservationDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"WithdrawReservation"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"notes"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"withdrawReservation"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"notes"},"value":{"kind":"Variable","name":{"kind":"Name","value":"notes"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ReservationFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ReservationFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Reservation"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"reservationDate"}},{"kind":"Field","name":{"kind":"Name","value":"partySize"}},{"kind":"Field","name":{"kind":"Name","value":"arrivalTime"}},{"kind":"Field","name":{"kind":"Name","value":"contactName"}},{"kind":"Field","name":{"kind":"Name","value":"contactPhoneNumber"}},{"kind":"Field","name":{"kind":"Name","value":"contactEmail"}},{"kind":"Field","name":{"kind":"Name","value":"notes"}},{"kind":"Field","name":{"kind":"Name","value":"violation"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<WithdrawReservationMutation, WithdrawReservationMutationVariables>;
export const ListServiceOpeningsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListServiceOpenings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceOpenings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"serviceId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"OpeningFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"OpeningFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Opening"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"description"}}]}}]} as unknown as DocumentNode<ListServiceOpeningsQuery, ListServiceOpeningsQueryVariables>;
export const UpsertServiceOpeningsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpsertServiceOpenings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"OpeningUpsertInput"}}}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"upsertServiceOpenings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"serviceId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"OpeningFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"OpeningFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Opening"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"description"}}]}}]} as unknown as DocumentNode<UpsertServiceOpeningsMutation, UpsertServiceOpeningsMutationVariables>;
export const SearchClosingsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchClosings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"ClosingSearchInput"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"venueClosings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ClosingFields"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ClosingFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Closing"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"serviceIds"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<SearchClosingsQuery, SearchClosingsQueryVariables>;
export const CreateClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ClosingCreateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ClosingFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ClosingFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Closing"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"serviceIds"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<CreateClosingMutation, CreateClosingMutationVariables>;
export const UpdateClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ClosingUpdateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"closingId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ClosingFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ClosingFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Closing"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"serviceIds"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<UpdateClosingMutation, UpdateClosingMutationVariables>;
export const DeleteClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"closingId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}}}]}]}}]} as unknown as DocumentNode<DeleteClosingMutation, DeleteClosingMutationVariables>;
export const GetServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"service"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ServiceFields"}},{"kind":"Field","name":{"kind":"Name","value":"venue"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ServiceFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Service"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<GetServiceQuery, GetServiceQueryVariables>;
export const ListServicesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListServices"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"name"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"includeDeleted"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Boolean"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listServices"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"venueId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"name"},"value":{"kind":"Variable","name":{"kind":"Name","value":"name"}}},{"kind":"Argument","name":{"kind":"Name","value":"includeDeleted"},"value":{"kind":"Variable","name":{"kind":"Name","value":"includeDeleted"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ServiceFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ServiceFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Service"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<ListServicesQuery, ListServicesQueryVariables>;
export const CreateServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CreateServiceInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createService"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ServiceFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ServiceFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Service"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<CreateServiceMutation, CreateServiceMutationVariables>;
export const UpdateServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateServiceInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateService"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"FragmentSpread","name":{"kind":"Name","value":"ServiceFields"}}]}}]}},{"kind":"FragmentDefinition","name":{"kind":"Name","value":"ServiceFields"},"typeCondition":{"kind":"NamedType","name":{"kind":"Name","value":"Service"}},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"dateFrom"}},{"kind":"Field","name":{"kind":"Name","value":"dateTo"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]} as unknown as DocumentNode<UpdateServiceMutation, UpdateServiceMutationVariables>;
export const DeleteServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteService"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}]}}]} as unknown as DocumentNode<DeleteServiceMutation, DeleteServiceMutationVariables>;
export const SearchVenuesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchVenues"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"VenueSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchVenues"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchVenuesQuery, SearchVenuesQueryVariables>;
export const GetVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"venue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetVenueQuery, GetVenueQueryVariables>;
export const CreateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CreateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<CreateVenueMutation, CreateVenueMutationVariables>;
export const UpdateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateVenueMutation, UpdateVenueMutationVariables>;
export const ActivateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"ActivateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"activateVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<ActivateVenueMutation, ActivateVenueMutationVariables>;
export const CloseVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CloseVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"closeVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<CloseVenueMutation, CloseVenueMutationVariables>;
export const DisableVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DisableVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"disableVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<DisableVenueMutation, DisableVenueMutationVariables>;
export const EnableVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"EnableVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"enableVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<EnableVenueMutation, EnableVenueMutationVariables>;