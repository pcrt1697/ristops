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

/** A seat-count delta applied on top of the resolved capacity for a date range. */
export type CapacityOverride = {
  __typename?: 'CapacityOverride';
  /** Signed change to the resolved seat count. */
  capacityDelta: Scalars['Int']['output'];
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Last date of the override period (inclusive). */
  dateEnd: Scalars['Date']['output'];
  /** First date of the override period (inclusive). */
  dateStart: Scalars['Date']['output'];
  /** Description of this capacity override. */
  description?: Maybe<Scalars['String']['output']>;
  /** Capacity override identifier. */
  id: Scalars['String']['output'];
  /** Identifier of the service this override belongs to. */
  serviceId: Scalars['String']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Weekday the override applies to within the range; null means every day. */
  weekday?: Maybe<Weekday>;
};

/** New capacity override information. Bulk: one row is created per weekday in `weekdays`; omitted/empty, or all seven, means every day. */
export type CapacityOverrideCreateInput = {
  /** Signed change to the resolved seat count. */
  capacityDelta: Scalars['Int']['input'];
  /** Last date of the override period (inclusive). */
  dateEnd: Scalars['Date']['input'];
  /** First date of the override period (inclusive). */
  dateStart: Scalars['Date']['input'];
  /** Description of this capacity override. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Weekdays to scope to; provide multiple to create one row per weekday. */
  weekdays?: InputMaybe<Array<Weekday>>;
};

/** A single page of results with pagination metadata. */
export type CapacityOverridePage = {
  __typename?: 'CapacityOverridePage';
  /** Items in the current page. */
  items: Array<CapacityOverride>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Capacity-override search query. */
export type CapacityOverrideSearchInput = {
  /** Filter parameters. */
  filter?: InputMaybe<ScheduleDateFilter>;
  /** Pagination parameters. */
  pagination?: InputMaybe<PaginationInput>;
  /** Sort instructions. */
  sort?: Array<CapacityOverrideSortFieldSortInput>;
};

/** Fields a capacity-override search may be sorted by. */
export const CapacityOverrideSortField = {
  CreatedAt: 'CREATED_AT',
  DateEnd: 'DATE_END',
  DateStart: 'DATE_START',
  Id: 'ID'
} as const;

export type CapacityOverrideSortField = typeof CapacityOverrideSortField[keyof typeof CapacityOverrideSortField];
/** A single sort instruction. */
export type CapacityOverrideSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: CapacityOverrideSortField;
};

/** Capacity override fields to update. Unset fields are not modified. The weekday scope is immutable — delete and recreate to re-scope it. */
export type CapacityOverrideUpdateInput = {
  /** New signed seat-count change. */
  capacityDelta?: InputMaybe<Scalars['Int']['input']>;
  /** New last date (inclusive). */
  dateEnd?: InputMaybe<Scalars['Date']['input']>;
  /** New first date (inclusive). */
  dateStart?: InputMaybe<Scalars['Date']['input']>;
  /** New description of this override. */
  description?: InputMaybe<Scalars['String']['input']>;
};

/** Candidate period+weekdays to check for conflicts before writing. Bulk `weekdays` mirror a create; omit/empty or all seven means every day. */
export type ConflictCheckInput = {
  /** Last date of the candidate period (inclusive). */
  dateEnd: Scalars['Date']['input'];
  /** First date of the candidate period (inclusive). */
  dateStart: Scalars['Date']['input'];
  /** Exclude this row from the check (use when previewing an edit of it). */
  excludeId?: InputMaybe<Scalars['ID']['input']>;
  /** Weekdays to check; provide multiple for a bulk candidate. */
  weekdays?: InputMaybe<Array<Weekday>>;
};

/** Which kind of exception a conflicting row belongs to. */
export const ConflictSource = {
  CapacityOverride: 'CAPACITY_OVERRIDE',
  OpeningOverride: 'OPENING_OVERRIDE',
  ServiceClosing: 'SERVICE_CLOSING',
  VenueClosing: 'VENUE_CLOSING'
} as const;

export type ConflictSource = typeof ConflictSource[keyof typeof ConflictSource];
/** Service information. */
export type CreateServiceInput = {
  /** Minimum notice required before a reservation slot, in minutes. */
  advanceNoticeM: Scalars['Int']['input'];
  /** Description of the service. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Minutes past a reservation's start time before it may be marked as a no-show. */
  gracePeriodM: Scalars['Int']['input'];
  /** Name of the service. */
  name: Scalars['String']['input'];
  /** Interval between reservation slots, in minutes. */
  slotIntervalM: Scalars['Int']['input'];
  /** Reservation duration, in minutes. */
  turnTimeM: Scalars['Int']['input'];
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
  /** Close a venue: owner action, valid only from ACTIVE. Soft — no data is lost. */
  closeVenue: Venue;
  /** Create a new capacity override for a service. */
  createCapacityOverride: Array<CapacityOverride>;
  /** Create a new opening override for a service. */
  createOpeningOverride: Array<OpeningOverride>;
  /** Create a new service. */
  createService: Service;
  /** Create a new closing for a service. */
  createServiceClosing: Array<ServiceClosing>;
  /** Create a new venue. */
  createVenue: Venue;
  /** Create a new venue-wide closing. */
  createVenueClosing: Array<VenueClosing>;
  /** Delete a capacity override. */
  deleteCapacityOverride: Scalars['Boolean']['output'];
  /** Delete an opening override. */
  deleteOpeningOverride: Scalars['Boolean']['output'];
  /** Delete a service. */
  deleteService: Scalars['Boolean']['output'];
  /** Delete a closing. */
  deleteServiceClosing: Scalars['Boolean']['output'];
  /** Delete a venue-wide closing. */
  deleteVenueClosing: Scalars['Boolean']['output'];
  /** Disable a venue: app-admin action, valid from PENDING or ACTIVE. */
  disableVenue: Venue;
  /** Re-enable a venue: app-admin action, valid only from DISABLED. Lands on PENDING — the owner must still activate it, which requires at least one service configured. */
  enableVenue: Venue;
  /** Grant a role to a user on a resource */
  grantAccess: Acl;
  /** Revoke a role from a user on a resource */
  revokeAccess: Scalars['Boolean']['output'];
  /** Update a capacity override. */
  updateCapacityOverride: CapacityOverride;
  /** Update current user data */
  updateMe: User;
  /** Update an opening override. */
  updateOpeningOverride: OpeningOverride;
  /** Update a service. */
  updateService: Service;
  /** Update a closing. */
  updateServiceClosing: ServiceClosing;
  /** Update user data by ID */
  updateUser: User;
  /** Update venue data */
  updateVenue: Venue;
  /** Update a venue-wide closing. */
  updateVenueClosing: VenueClosing;
  /** Replace the full set of weekly openings for a service. */
  upsertServiceOpenings: Array<Opening>;
};


export type MutationActivateVenueArgs = {
  id: Scalars['ID']['input'];
};


export type MutationCloseVenueArgs = {
  id: Scalars['ID']['input'];
};


export type MutationCreateCapacityOverrideArgs = {
  id: Scalars['ID']['input'];
  input: CapacityOverrideCreateInput;
};


export type MutationCreateOpeningOverrideArgs = {
  id: Scalars['ID']['input'];
  input: OpeningOverrideCreateInput;
};


export type MutationCreateServiceArgs = {
  input: CreateServiceInput;
};


export type MutationCreateServiceClosingArgs = {
  id: Scalars['ID']['input'];
  input: ServiceClosingCreateInput;
};


export type MutationCreateVenueArgs = {
  input: CreateVenueInput;
};


export type MutationCreateVenueClosingArgs = {
  id: Scalars['ID']['input'];
  input: VenueClosingCreateInput;
};


export type MutationDeleteCapacityOverrideArgs = {
  capacityOverrideId: Scalars['ID']['input'];
  id: Scalars['ID']['input'];
};


export type MutationDeleteOpeningOverrideArgs = {
  id: Scalars['ID']['input'];
  overrideId: Scalars['ID']['input'];
};


export type MutationDeleteServiceArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteServiceClosingArgs = {
  closingId: Scalars['ID']['input'];
  id: Scalars['ID']['input'];
};


export type MutationDeleteVenueClosingArgs = {
  closingId: Scalars['ID']['input'];
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


export type MutationRevokeAccessArgs = {
  input: RevokeAccessInput;
};


export type MutationUpdateCapacityOverrideArgs = {
  capacityOverrideId: Scalars['ID']['input'];
  id: Scalars['ID']['input'];
  input: CapacityOverrideUpdateInput;
};


export type MutationUpdateMeArgs = {
  input: UpdateUserInput;
};


export type MutationUpdateOpeningOverrideArgs = {
  id: Scalars['ID']['input'];
  input: OpeningOverrideUpdateInput;
  overrideId: Scalars['ID']['input'];
};


export type MutationUpdateServiceArgs = {
  id: Scalars['ID']['input'];
  input: UpdateServiceInput;
};


export type MutationUpdateServiceClosingArgs = {
  closingId: Scalars['ID']['input'];
  id: Scalars['ID']['input'];
  input: ServiceClosingUpdateInput;
};


export type MutationUpdateUserArgs = {
  id: Scalars['ID']['input'];
  input: UpdateUserInput;
};


export type MutationUpdateVenueArgs = {
  id: Scalars['ID']['input'];
  input: UpdateVenueInput;
};


export type MutationUpdateVenueClosingArgs = {
  closingId: Scalars['ID']['input'];
  id: Scalars['ID']['input'];
  input: VenueClosingUpdateInput;
};


export type MutationUpsertServiceOpeningsArgs = {
  id: Scalars['ID']['input'];
  openings: Array<OpeningUpsertInput>;
};

/** A service's weekly opening for a given weekday. */
export type Opening = {
  __typename?: 'Opening';
  /** Maximum number of reservable seats. */
  capacity: Scalars['Int']['output'];
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Description of this opening. */
  description?: Maybe<Scalars['String']['output']>;
  /** Time the service closes. */
  endTime: Scalars['Time']['output'];
  /** Opening identifier. */
  id: Scalars['String']['output'];
  /** Identifier of the service this opening belongs to. */
  serviceId: Scalars['String']['output'];
  /** Time the service opens. */
  startTime: Scalars['Time']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Day of the week this opening applies to. */
  weekday: Weekday;
};

/** A one-off opening override replacing base hours for a date range. */
export type OpeningOverride = {
  __typename?: 'OpeningOverride';
  /** Overridden maximum number of reservable seats. */
  capacity: Scalars['Int']['output'];
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Last date of the override period (inclusive). */
  dateEnd: Scalars['Date']['output'];
  /** First date of the override period (inclusive). */
  dateStart: Scalars['Date']['output'];
  /** Description of this override. */
  description?: Maybe<Scalars['String']['output']>;
  /** Overridden closing time. */
  endTime: Scalars['Time']['output'];
  /** Override identifier. */
  id: Scalars['String']['output'];
  /** Identifier of the service this override belongs to. */
  serviceId: Scalars['String']['output'];
  /** Overridden opening time. */
  startTime: Scalars['Time']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Weekday the override applies to within the range; null means every day. */
  weekday?: Maybe<Weekday>;
};

/** New opening override information. Bulk: one row is created per weekday in `weekdays`; omitted/empty, or all seven, means every day. */
export type OpeningOverrideCreateInput = {
  /** Overridden maximum number of reservable seats. */
  capacity: Scalars['Int']['input'];
  /** Last date of the override period (inclusive). */
  dateEnd: Scalars['Date']['input'];
  /** First date of the override period (inclusive). */
  dateStart: Scalars['Date']['input'];
  /** Description of this override. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Overridden closing time. */
  endTime: Scalars['Time']['input'];
  /** Overridden opening time. */
  startTime: Scalars['Time']['input'];
  /** Weekdays to scope to; provide multiple to create one row per weekday. */
  weekdays?: InputMaybe<Array<Weekday>>;
};

/** A single page of results with pagination metadata. */
export type OpeningOverridePage = {
  __typename?: 'OpeningOverridePage';
  /** Items in the current page. */
  items: Array<OpeningOverride>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Opening-override search query. */
export type OpeningOverrideSearchInput = {
  /** Filter parameters. */
  filter?: InputMaybe<ScheduleDateFilter>;
  /** Pagination parameters. */
  pagination?: InputMaybe<PaginationInput>;
  /** Sort instructions. */
  sort?: Array<OpeningOverrideSortFieldSortInput>;
};

/** Fields an opening-override search may be sorted by. */
export const OpeningOverrideSortField = {
  CreatedAt: 'CREATED_AT',
  DateEnd: 'DATE_END',
  DateStart: 'DATE_START',
  Id: 'ID'
} as const;

export type OpeningOverrideSortField = typeof OpeningOverrideSortField[keyof typeof OpeningOverrideSortField];
/** A single sort instruction. */
export type OpeningOverrideSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: OpeningOverrideSortField;
};

/** Opening override fields to update. Unset fields are not modified. The weekday scope is immutable — delete and recreate to re-scope it. */
export type OpeningOverrideUpdateInput = {
  /** New overridden capacity. */
  capacity?: InputMaybe<Scalars['Int']['input']>;
  /** New last date (inclusive). */
  dateEnd?: InputMaybe<Scalars['Date']['input']>;
  /** New first date (inclusive). */
  dateStart?: InputMaybe<Scalars['Date']['input']>;
  /** New description of this override. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** New overridden closing time. */
  endTime?: InputMaybe<Scalars['Time']['input']>;
  /** New overridden opening time. */
  startTime?: InputMaybe<Scalars['Time']['input']>;
};

/** A single weekly opening within a bulk upsert. */
export type OpeningUpsertInput = {
  /** Maximum number of reservable seats. */
  capacity: Scalars['Int']['input'];
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
  /** Preview which existing capacity overrides a candidate period would conflict with. */
  serviceCapacityOverrideConflicts: Array<ScheduleConflict>;
  /** Search the capacity overrides for a service. */
  serviceCapacityOverrides: CapacityOverridePage;
  /** Preview which existing service or venue closings a candidate period would conflict with. */
  serviceClosingConflicts: Array<ScheduleConflict>;
  /** Search the closings for a service. */
  serviceClosings: ServiceClosingPage;
  /** Preview which existing opening overrides a candidate period would conflict with. */
  serviceOpeningOverrideConflicts: Array<ScheduleConflict>;
  /** Search the opening overrides for a service. */
  serviceOpeningOverrides: OpeningOverridePage;
  /** List the weekly openings for a service. */
  serviceOpenings: Array<Opening>;
  /** Fetch user by ID */
  user: User;
  /** Fetch venue by ID */
  venue: Venue;
  /** Preview which existing venue closings a candidate period would conflict with. */
  venueClosingConflicts: Array<ScheduleConflict>;
  /** Search the venue-wide closings for a venue. */
  venueClosings: VenueClosingPage;
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


export type QueryServiceCapacityOverrideConflictsArgs = {
  id: Scalars['ID']['input'];
  input: ConflictCheckInput;
};


export type QueryServiceCapacityOverridesArgs = {
  id: Scalars['ID']['input'];
  input?: InputMaybe<CapacityOverrideSearchInput>;
};


export type QueryServiceClosingConflictsArgs = {
  id: Scalars['ID']['input'];
  input: ConflictCheckInput;
};


export type QueryServiceClosingsArgs = {
  id: Scalars['ID']['input'];
  input?: InputMaybe<ServiceClosingSearchInput>;
};


export type QueryServiceOpeningOverrideConflictsArgs = {
  id: Scalars['ID']['input'];
  input: ConflictCheckInput;
};


export type QueryServiceOpeningOverridesArgs = {
  id: Scalars['ID']['input'];
  input?: InputMaybe<OpeningOverrideSearchInput>;
};


export type QueryServiceOpeningsArgs = {
  id: Scalars['ID']['input'];
  includeDeleted?: InputMaybe<Scalars['Boolean']['input']>;
};


export type QueryUserArgs = {
  id: Scalars['ID']['input'];
};


export type QueryVenueArgs = {
  id: Scalars['ID']['input'];
};


export type QueryVenueClosingConflictsArgs = {
  id: Scalars['ID']['input'];
  input: ConflictCheckInput;
};


export type QueryVenueClosingsArgs = {
  id: Scalars['ID']['input'];
  input?: InputMaybe<VenueClosingSearchInput>;
};

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

/** An existing row that conflicts with a candidate period+weekday. */
export type ScheduleConflict = {
  __typename?: 'ScheduleConflict';
  /** Last date of the conflicting row (inclusive). */
  conflictingDateEnd: Scalars['Date']['output'];
  /** First date of the conflicting row (inclusive). */
  conflictingDateStart: Scalars['Date']['output'];
  /** Identifier of the existing conflicting row. */
  conflictingId: Scalars['String']['output'];
  /** Weekday scope of the conflicting row; null means every day. */
  conflictingWeekday?: Maybe<Weekday>;
  /** Which kind of exception the conflicting row is. */
  source: ConflictSource;
  /** Weekday from the candidate this conflict applies to; null means every day. */
  weekday?: Maybe<Weekday>;
};

/** Date-range filter for schedule exceptions. */
export type ScheduleDateFilter = {
  /** Include items whose period ends on or after this date. */
  dateFrom?: InputMaybe<Scalars['Date']['input']>;
  /** Include items whose period starts on or before this date. */
  dateTo?: InputMaybe<Scalars['Date']['input']>;
  /** Return results even if the parent service has been deleted. */
  includeDeleted?: InputMaybe<Scalars['Boolean']['input']>;
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
  /** Minimum notice required before a reservation slot, in minutes. */
  advanceNoticeM: Scalars['Int']['output'];
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Deletion date, if the service has been deleted. */
  deletedAt?: Maybe<Scalars['DateTime']['output']>;
  /** Description of the service. */
  description?: Maybe<Scalars['String']['output']>;
  /** Minutes past a reservation's start time before it may be marked as a no-show. */
  gracePeriodM: Scalars['Int']['output'];
  /** Service identifier. */
  id: Scalars['String']['output'];
  /** Name of the service. */
  name: Scalars['String']['output'];
  /** Interval between reservation slots, in minutes. */
  slotIntervalM: Scalars['Int']['output'];
  /** Reservation duration, in minutes. */
  turnTimeM: Scalars['Int']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Venue this service belongs to. */
  venue: Venue;
};

/** A one-off closing for a date range. */
export type ServiceClosing = {
  __typename?: 'ServiceClosing';
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Last date of the closing period (inclusive). */
  dateEnd: Scalars['Date']['output'];
  /** First date of the closing period (inclusive). */
  dateStart: Scalars['Date']['output'];
  /** Description of this closing. */
  description?: Maybe<Scalars['String']['output']>;
  /** Closing identifier. */
  id: Scalars['String']['output'];
  /** Identifier of the service this closing belongs to. */
  serviceId: Scalars['String']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Weekday the closing applies to within the range; null means every day. */
  weekday?: Maybe<Weekday>;
};

/** New closing information. Bulk: one row is created per weekday in `weekdays`; omitted/empty, or all seven, means every day. */
export type ServiceClosingCreateInput = {
  /** Last date of the closing period (inclusive). */
  dateEnd: Scalars['Date']['input'];
  /** First date of the closing period (inclusive). */
  dateStart: Scalars['Date']['input'];
  /** Description of this closing. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Weekdays to scope to; provide multiple to create one row per weekday. */
  weekdays?: InputMaybe<Array<Weekday>>;
};

/** A single page of results with pagination metadata. */
export type ServiceClosingPage = {
  __typename?: 'ServiceClosingPage';
  /** Items in the current page. */
  items: Array<ServiceClosing>;
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
export type ServiceClosingSearchInput = {
  /** Filter parameters. */
  filter?: InputMaybe<ScheduleDateFilter>;
  /** Pagination parameters. */
  pagination?: InputMaybe<PaginationInput>;
  /** Sort instructions. */
  sort?: Array<ServiceClosingSortFieldSortInput>;
};

/** Fields a closing search may be sorted by. */
export const ServiceClosingSortField = {
  CreatedAt: 'CREATED_AT',
  DateEnd: 'DATE_END',
  DateStart: 'DATE_START',
  Id: 'ID'
} as const;

export type ServiceClosingSortField = typeof ServiceClosingSortField[keyof typeof ServiceClosingSortField];
/** A single sort instruction. */
export type ServiceClosingSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: ServiceClosingSortField;
};

/** Closing fields to update. Unset fields are not modified. The weekday scope is immutable — delete and recreate to re-scope it. */
export type ServiceClosingUpdateInput = {
  /** New last date (inclusive). */
  dateEnd?: InputMaybe<Scalars['Date']['input']>;
  /** New first date (inclusive). */
  dateStart?: InputMaybe<Scalars['Date']['input']>;
  /** New description of this closing. */
  description?: InputMaybe<Scalars['String']['input']>;
};

/** Direction of a sort clause. */
export const SortDirection = {
  Asc: 'ASC',
  Desc: 'DESC'
} as const;

export type SortDirection = typeof SortDirection[keyof typeof SortDirection];
/** Service information to update. */
export type UpdateServiceInput = {
  /** New minimum notice required before a reservation slot, in minutes. */
  advanceNoticeM?: InputMaybe<Scalars['Int']['input']>;
  /** New description of the service. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** New minutes past a reservation's start time before it may be marked as a no-show. */
  gracePeriodM?: InputMaybe<Scalars['Int']['input']>;
  /** New name of the service. */
  name?: InputMaybe<Scalars['String']['input']>;
  /** New interval between reservation slots, in minutes. */
  slotIntervalM?: InputMaybe<Scalars['Int']['input']>;
  /** New reservation duration, in minutes. */
  turnTimeM?: InputMaybe<Scalars['Int']['input']>;
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

/** A venue-wide closing: closes every service of a venue for a date range. */
export type VenueClosing = {
  __typename?: 'VenueClosing';
  /** Creation date. */
  createdAt: Scalars['DateTime']['output'];
  /** Last date of the closing period (inclusive). */
  dateEnd: Scalars['Date']['output'];
  /** First date of the closing period (inclusive). */
  dateStart: Scalars['Date']['output'];
  /** Description of this venue closing. */
  description?: Maybe<Scalars['String']['output']>;
  /** Venue closing identifier. */
  id: Scalars['String']['output'];
  /** Last update date. */
  updatedAt: Scalars['DateTime']['output'];
  /** Identifier of the venue this closing belongs to. */
  venueId: Scalars['String']['output'];
  /** Weekday the closing applies to within the range; null means every day. */
  weekday?: Maybe<Weekday>;
};

/** New venue closing information. Bulk: one row is created per weekday in `weekdays`; omitted/empty, or all seven, means every day. */
export type VenueClosingCreateInput = {
  /** Last date of the closing period (inclusive). */
  dateEnd: Scalars['Date']['input'];
  /** First date of the closing period (inclusive). */
  dateStart: Scalars['Date']['input'];
  /** Description of this venue closing. */
  description?: InputMaybe<Scalars['String']['input']>;
  /** Weekdays to scope to; provide multiple to create one row per weekday. */
  weekdays?: InputMaybe<Array<Weekday>>;
};

/** A single page of results with pagination metadata. */
export type VenueClosingPage = {
  __typename?: 'VenueClosingPage';
  /** Items in the current page. */
  items: Array<VenueClosing>;
  /** 0-indexed page number. */
  page: Scalars['Int']['output'];
  /** Number of items per page. */
  pageSize: Scalars['Int']['output'];
  /** Total number of items across all pages. */
  total: Scalars['Int']['output'];
  /** Total number of pages. */
  totalPages: Scalars['Int']['output'];
};

/** Venue-closing search query. */
export type VenueClosingSearchInput = {
  /** Filter parameters. */
  filter?: InputMaybe<ScheduleDateFilter>;
  /** Pagination parameters. */
  pagination?: InputMaybe<PaginationInput>;
  /** Sort instructions. */
  sort?: Array<VenueClosingSortFieldSortInput>;
};

/** Fields a venue-closing search may be sorted by. */
export const VenueClosingSortField = {
  CreatedAt: 'CREATED_AT',
  DateEnd: 'DATE_END',
  DateStart: 'DATE_START',
  Id: 'ID'
} as const;

export type VenueClosingSortField = typeof VenueClosingSortField[keyof typeof VenueClosingSortField];
/** A single sort instruction. */
export type VenueClosingSortFieldSortInput = {
  /** Sort direction. */
  direction?: SortDirection;
  /** Field to sort by. */
  field: VenueClosingSortField;
};

/** Venue closing fields to update. Unset fields are not modified. The weekday scope is immutable — delete and recreate to re-scope it. */
export type VenueClosingUpdateInput = {
  /** New last date (inclusive). */
  dateEnd?: InputMaybe<Scalars['Date']['input']>;
  /** New first date (inclusive). */
  dateStart?: InputMaybe<Scalars['Date']['input']>;
  /** New description of this closing. */
  description?: InputMaybe<Scalars['String']['input']>;
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

export type ListServiceOpeningsQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  includeDeleted?: InputMaybe<Scalars['Boolean']['input']>;
}>;


export type ListServiceOpeningsQuery = { __typename?: 'Query', serviceOpenings: Array<{ __typename?: 'Opening', id: string, serviceId: string, weekday: Weekday, capacity: number, startTime: string, endTime: string, description?: string | null, createdAt: string, updatedAt: string }> };

export type UpsertServiceOpeningsMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  openings: Array<OpeningUpsertInput> | OpeningUpsertInput;
}>;


export type UpsertServiceOpeningsMutation = { __typename?: 'Mutation', upsertServiceOpenings: Array<{ __typename?: 'Opening', id: string, serviceId: string, weekday: Weekday, capacity: number, startTime: string, endTime: string, description?: string | null, createdAt: string, updatedAt: string }> };

export type SearchOpeningOverridesQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input?: InputMaybe<OpeningOverrideSearchInput>;
}>;


export type SearchOpeningOverridesQuery = { __typename?: 'Query', serviceOpeningOverrides: { __typename?: 'OpeningOverridePage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'OpeningOverride', id: string, serviceId: string, dateStart: string, dateEnd: string, weekday?: Weekday | null, capacity: number, startTime: string, endTime: string, description?: string | null, createdAt: string, updatedAt: string }> } };

export type CreateOpeningOverrideMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input: OpeningOverrideCreateInput;
}>;


export type CreateOpeningOverrideMutation = { __typename?: 'Mutation', createOpeningOverride: Array<{ __typename?: 'OpeningOverride', id: string }> };

export type UpdateOpeningOverrideMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  overrideId: Scalars['ID']['input'];
  input: OpeningOverrideUpdateInput;
}>;


export type UpdateOpeningOverrideMutation = { __typename?: 'Mutation', updateOpeningOverride: { __typename?: 'OpeningOverride', id: string } };

export type DeleteOpeningOverrideMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  overrideId: Scalars['ID']['input'];
}>;


export type DeleteOpeningOverrideMutation = { __typename?: 'Mutation', deleteOpeningOverride: boolean };

export type SearchServiceClosingsQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input?: InputMaybe<ServiceClosingSearchInput>;
}>;


export type SearchServiceClosingsQuery = { __typename?: 'Query', serviceClosings: { __typename?: 'ServiceClosingPage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'ServiceClosing', id: string, serviceId: string, dateStart: string, dateEnd: string, weekday?: Weekday | null, description?: string | null, createdAt: string, updatedAt: string }> } };

export type CreateServiceClosingMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input: ServiceClosingCreateInput;
}>;


export type CreateServiceClosingMutation = { __typename?: 'Mutation', createServiceClosing: Array<{ __typename?: 'ServiceClosing', id: string }> };

export type UpdateServiceClosingMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  closingId: Scalars['ID']['input'];
  input: ServiceClosingUpdateInput;
}>;


export type UpdateServiceClosingMutation = { __typename?: 'Mutation', updateServiceClosing: { __typename?: 'ServiceClosing', id: string } };

export type DeleteServiceClosingMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  closingId: Scalars['ID']['input'];
}>;


export type DeleteServiceClosingMutation = { __typename?: 'Mutation', deleteServiceClosing: boolean };

export type SearchCapacityOverridesQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input?: InputMaybe<CapacityOverrideSearchInput>;
}>;


export type SearchCapacityOverridesQuery = { __typename?: 'Query', serviceCapacityOverrides: { __typename?: 'CapacityOverridePage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'CapacityOverride', id: string, serviceId: string, dateStart: string, dateEnd: string, weekday?: Weekday | null, capacityDelta: number, description?: string | null, createdAt: string, updatedAt: string }> } };

export type CreateCapacityOverrideMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input: CapacityOverrideCreateInput;
}>;


export type CreateCapacityOverrideMutation = { __typename?: 'Mutation', createCapacityOverride: Array<{ __typename?: 'CapacityOverride', id: string }> };

export type UpdateCapacityOverrideMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  capacityOverrideId: Scalars['ID']['input'];
  input: CapacityOverrideUpdateInput;
}>;


export type UpdateCapacityOverrideMutation = { __typename?: 'Mutation', updateCapacityOverride: { __typename?: 'CapacityOverride', id: string } };

export type DeleteCapacityOverrideMutationVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  capacityOverrideId: Scalars['ID']['input'];
}>;


export type DeleteCapacityOverrideMutation = { __typename?: 'Mutation', deleteCapacityOverride: boolean };

export type SearchVenueClosingsQueryVariables = Exact<{
  venueId: Scalars['ID']['input'];
  input?: InputMaybe<VenueClosingSearchInput>;
}>;


export type SearchVenueClosingsQuery = { __typename?: 'Query', venueClosings: { __typename?: 'VenueClosingPage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'VenueClosing', id: string, venueId: string, dateStart: string, dateEnd: string, weekday?: Weekday | null, description?: string | null, createdAt: string, updatedAt: string }> } };

export type CreateVenueClosingMutationVariables = Exact<{
  venueId: Scalars['ID']['input'];
  input: VenueClosingCreateInput;
}>;


export type CreateVenueClosingMutation = { __typename?: 'Mutation', createVenueClosing: Array<{ __typename?: 'VenueClosing', id: string }> };

export type UpdateVenueClosingMutationVariables = Exact<{
  venueId: Scalars['ID']['input'];
  closingId: Scalars['ID']['input'];
  input: VenueClosingUpdateInput;
}>;


export type UpdateVenueClosingMutation = { __typename?: 'Mutation', updateVenueClosing: { __typename?: 'VenueClosing', id: string } };

export type DeleteVenueClosingMutationVariables = Exact<{
  venueId: Scalars['ID']['input'];
  closingId: Scalars['ID']['input'];
}>;


export type DeleteVenueClosingMutation = { __typename?: 'Mutation', deleteVenueClosing: boolean };

export type OpeningOverrideConflictsQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input: ConflictCheckInput;
}>;


export type OpeningOverrideConflictsQuery = { __typename?: 'Query', serviceOpeningOverrideConflicts: Array<{ __typename?: 'ScheduleConflict', weekday?: Weekday | null, source: ConflictSource, conflictingId: string, conflictingDateStart: string, conflictingDateEnd: string, conflictingWeekday?: Weekday | null }> };

export type ServiceClosingConflictsQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input: ConflictCheckInput;
}>;


export type ServiceClosingConflictsQuery = { __typename?: 'Query', serviceClosingConflicts: Array<{ __typename?: 'ScheduleConflict', weekday?: Weekday | null, source: ConflictSource, conflictingId: string, conflictingDateStart: string, conflictingDateEnd: string, conflictingWeekday?: Weekday | null }> };

export type CapacityOverrideConflictsQueryVariables = Exact<{
  serviceId: Scalars['ID']['input'];
  input: ConflictCheckInput;
}>;


export type CapacityOverrideConflictsQuery = { __typename?: 'Query', serviceCapacityOverrideConflicts: Array<{ __typename?: 'ScheduleConflict', weekday?: Weekday | null, source: ConflictSource, conflictingId: string, conflictingDateStart: string, conflictingDateEnd: string, conflictingWeekday?: Weekday | null }> };

export type VenueClosingConflictsQueryVariables = Exact<{
  venueId: Scalars['ID']['input'];
  input: ConflictCheckInput;
}>;


export type VenueClosingConflictsQuery = { __typename?: 'Query', venueClosingConflicts: Array<{ __typename?: 'ScheduleConflict', weekday?: Weekday | null, source: ConflictSource, conflictingId: string, conflictingDateStart: string, conflictingDateEnd: string, conflictingWeekday?: Weekday | null }> };

export type GetServiceQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetServiceQuery = { __typename?: 'Query', service: { __typename?: 'Service', id: string, name: string, description?: string | null, turnTimeM: number, advanceNoticeM: number, slotIntervalM: number, gracePeriodM: number, deletedAt?: string | null, createdAt: string, updatedAt: string, venue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } } };

export type ListServicesQueryVariables = Exact<{
  venueId: Scalars['ID']['input'];
  name?: InputMaybe<Scalars['String']['input']>;
  includeDeleted?: InputMaybe<Scalars['Boolean']['input']>;
}>;


export type ListServicesQuery = { __typename?: 'Query', listServices: Array<{ __typename?: 'Service', id: string, name: string, description?: string | null, turnTimeM: number, advanceNoticeM: number, slotIntervalM: number, gracePeriodM: number, deletedAt?: string | null, createdAt: string, updatedAt: string }> };

export type CreateServiceMutationVariables = Exact<{
  input: CreateServiceInput;
}>;


export type CreateServiceMutation = { __typename?: 'Mutation', createService: { __typename?: 'Service', id: string, name: string, description?: string | null, turnTimeM: number, advanceNoticeM: number, slotIntervalM: number, gracePeriodM: number, deletedAt?: string | null, createdAt: string, updatedAt: string, venue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, status: VenueStatus, createdAt: string, updatedAt: string } } };

export type UpdateServiceMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: UpdateServiceInput;
}>;


export type UpdateServiceMutation = { __typename?: 'Mutation', updateService: { __typename?: 'Service', id: string, name: string, description?: string | null, turnTimeM: number, advanceNoticeM: number, slotIntervalM: number, gracePeriodM: number, deletedAt?: string | null, createdAt: string, updatedAt: string } };

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


export const ListMyGrantsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListMyGrants"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ListGrantsInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"myGrants"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"grants"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resource"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resourceId"}},{"kind":"Field","name":{"kind":"Name","value":"resourceType"}}]}},{"kind":"Field","name":{"kind":"Name","value":"role"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}}]}}]}}]}}]}}]} as unknown as DocumentNode<ListMyGrantsQuery, ListMyGrantsQueryVariables>;
export const ListRolesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListRoles"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ListRolesInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listRoles"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"roles"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]}}]} as unknown as DocumentNode<ListRolesQuery, ListRolesQueryVariables>;
export const ListPermissionsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListPermissions"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"query"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listPermissions"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"query"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]} as unknown as DocumentNode<ListPermissionsQuery, ListPermissionsQueryVariables>;
export const SearchResourceGrantsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchResourceGrants"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"SearchResourceGrantsInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchResourceGrants"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"user"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}}]}},{"kind":"Field","name":{"kind":"Name","value":"grants"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"role"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}}]}},{"kind":"Field","name":{"kind":"Name","value":"resource"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resourceId"}},{"kind":"Field","name":{"kind":"Name","value":"resourceType"}}]}},{"kind":"Field","name":{"kind":"Name","value":"assignedAt"}},{"kind":"Field","name":{"kind":"Name","value":"expiresAt"}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchResourceGrantsQuery, SearchResourceGrantsQueryVariables>;
export const SearchMembersDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchMembers"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"MemberSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchMembers"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchMembersQuery, SearchMembersQueryVariables>;
export const GrantAccessDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"GrantAccess"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"GrantAccessInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"grantAccess"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<GrantAccessMutation, GrantAccessMutationVariables>;
export const RevokeAccessDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"RevokeAccess"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"RevokeAccessInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"revokeAccess"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}]}]}}]} as unknown as DocumentNode<RevokeAccessMutation, RevokeAccessMutationVariables>;
export const GetMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetMe"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"me"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetMeQuery, GetMeQueryVariables>;
export const UpdateMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateMe"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateUserInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateMe"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateMeMutation, UpdateMeMutationVariables>;
export const ListServiceOpeningsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListServiceOpenings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"includeDeleted"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Boolean"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceOpenings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"includeDeleted"},"value":{"kind":"Variable","name":{"kind":"Name","value":"includeDeleted"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<ListServiceOpeningsQuery, ListServiceOpeningsQueryVariables>;
export const UpsertServiceOpeningsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpsertServiceOpenings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"openings"}},"type":{"kind":"NonNullType","type":{"kind":"ListType","type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"OpeningUpsertInput"}}}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"upsertServiceOpenings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"openings"},"value":{"kind":"Variable","name":{"kind":"Name","value":"openings"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpsertServiceOpeningsMutation, UpsertServiceOpeningsMutationVariables>;
export const SearchOpeningOverridesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchOpeningOverrides"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"OpeningOverrideSearchInput"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceOpeningOverrides"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"dateStart"}},{"kind":"Field","name":{"kind":"Name","value":"dateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"capacity"}},{"kind":"Field","name":{"kind":"Name","value":"startTime"}},{"kind":"Field","name":{"kind":"Name","value":"endTime"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchOpeningOverridesQuery, SearchOpeningOverridesQueryVariables>;
export const CreateOpeningOverrideDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateOpeningOverride"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"OpeningOverrideCreateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createOpeningOverride"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<CreateOpeningOverrideMutation, CreateOpeningOverrideMutationVariables>;
export const UpdateOpeningOverrideDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateOpeningOverride"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"overrideId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"OpeningOverrideUpdateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateOpeningOverride"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"overrideId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"overrideId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<UpdateOpeningOverrideMutation, UpdateOpeningOverrideMutationVariables>;
export const DeleteOpeningOverrideDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteOpeningOverride"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"overrideId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteOpeningOverride"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"overrideId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"overrideId"}}}]}]}}]} as unknown as DocumentNode<DeleteOpeningOverrideMutation, DeleteOpeningOverrideMutationVariables>;
export const SearchServiceClosingsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchServiceClosings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"ServiceClosingSearchInput"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceClosings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"dateStart"}},{"kind":"Field","name":{"kind":"Name","value":"dateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchServiceClosingsQuery, SearchServiceClosingsQueryVariables>;
export const CreateServiceClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateServiceClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ServiceClosingCreateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createServiceClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<CreateServiceClosingMutation, CreateServiceClosingMutationVariables>;
export const UpdateServiceClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateServiceClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ServiceClosingUpdateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateServiceClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"closingId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<UpdateServiceClosingMutation, UpdateServiceClosingMutationVariables>;
export const DeleteServiceClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteServiceClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteServiceClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"closingId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}}}]}]}}]} as unknown as DocumentNode<DeleteServiceClosingMutation, DeleteServiceClosingMutationVariables>;
export const SearchCapacityOverridesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchCapacityOverrides"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"CapacityOverrideSearchInput"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceCapacityOverrides"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"serviceId"}},{"kind":"Field","name":{"kind":"Name","value":"dateStart"}},{"kind":"Field","name":{"kind":"Name","value":"dateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"capacityDelta"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchCapacityOverridesQuery, SearchCapacityOverridesQueryVariables>;
export const CreateCapacityOverrideDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateCapacityOverride"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CapacityOverrideCreateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createCapacityOverride"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<CreateCapacityOverrideMutation, CreateCapacityOverrideMutationVariables>;
export const UpdateCapacityOverrideDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateCapacityOverride"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"capacityOverrideId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CapacityOverrideUpdateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateCapacityOverride"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"capacityOverrideId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"capacityOverrideId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<UpdateCapacityOverrideMutation, UpdateCapacityOverrideMutationVariables>;
export const DeleteCapacityOverrideDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteCapacityOverride"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"capacityOverrideId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteCapacityOverride"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"capacityOverrideId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"capacityOverrideId"}}}]}]}}]} as unknown as DocumentNode<DeleteCapacityOverrideMutation, DeleteCapacityOverrideMutationVariables>;
export const SearchVenueClosingsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchVenueClosings"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"VenueClosingSearchInput"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"venueClosings"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"venueId"}},{"kind":"Field","name":{"kind":"Name","value":"dateStart"}},{"kind":"Field","name":{"kind":"Name","value":"dateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchVenueClosingsQuery, SearchVenueClosingsQueryVariables>;
export const CreateVenueClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateVenueClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"VenueClosingCreateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createVenueClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<CreateVenueClosingMutation, CreateVenueClosingMutationVariables>;
export const UpdateVenueClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateVenueClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"VenueClosingUpdateInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateVenueClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"closingId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<UpdateVenueClosingMutation, UpdateVenueClosingMutationVariables>;
export const DeleteVenueClosingDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteVenueClosing"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteVenueClosing"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"closingId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"closingId"}}}]}]}}]} as unknown as DocumentNode<DeleteVenueClosingMutation, DeleteVenueClosingMutationVariables>;
export const OpeningOverrideConflictsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"OpeningOverrideConflicts"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ConflictCheckInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceOpeningOverrideConflicts"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingId"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateStart"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingWeekday"}}]}}]}}]} as unknown as DocumentNode<OpeningOverrideConflictsQuery, OpeningOverrideConflictsQueryVariables>;
export const ServiceClosingConflictsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ServiceClosingConflicts"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ConflictCheckInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceClosingConflicts"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingId"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateStart"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingWeekday"}}]}}]}}]} as unknown as DocumentNode<ServiceClosingConflictsQuery, ServiceClosingConflictsQueryVariables>;
export const CapacityOverrideConflictsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"CapacityOverrideConflicts"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ConflictCheckInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"serviceCapacityOverrideConflicts"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"serviceId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingId"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateStart"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingWeekday"}}]}}]}}]} as unknown as DocumentNode<CapacityOverrideConflictsQuery, CapacityOverrideConflictsQueryVariables>;
export const VenueClosingConflictsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"VenueClosingConflicts"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ConflictCheckInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"venueClosingConflicts"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"weekday"}},{"kind":"Field","name":{"kind":"Name","value":"source"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingId"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateStart"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingDateEnd"}},{"kind":"Field","name":{"kind":"Name","value":"conflictingWeekday"}}]}}]}}]} as unknown as DocumentNode<VenueClosingConflictsQuery, VenueClosingConflictsQueryVariables>;
export const GetServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"service"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"turnTimeM"}},{"kind":"Field","name":{"kind":"Name","value":"advanceNoticeM"}},{"kind":"Field","name":{"kind":"Name","value":"slotIntervalM"}},{"kind":"Field","name":{"kind":"Name","value":"gracePeriodM"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}},{"kind":"Field","name":{"kind":"Name","value":"venue"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]}}]} as unknown as DocumentNode<GetServiceQuery, GetServiceQueryVariables>;
export const ListServicesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListServices"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"name"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"includeDeleted"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"Boolean"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listServices"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"venueId"},"value":{"kind":"Variable","name":{"kind":"Name","value":"venueId"}}},{"kind":"Argument","name":{"kind":"Name","value":"name"},"value":{"kind":"Variable","name":{"kind":"Name","value":"name"}}},{"kind":"Argument","name":{"kind":"Name","value":"includeDeleted"},"value":{"kind":"Variable","name":{"kind":"Name","value":"includeDeleted"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"turnTimeM"}},{"kind":"Field","name":{"kind":"Name","value":"advanceNoticeM"}},{"kind":"Field","name":{"kind":"Name","value":"slotIntervalM"}},{"kind":"Field","name":{"kind":"Name","value":"gracePeriodM"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<ListServicesQuery, ListServicesQueryVariables>;
export const CreateServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CreateServiceInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createService"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"turnTimeM"}},{"kind":"Field","name":{"kind":"Name","value":"advanceNoticeM"}},{"kind":"Field","name":{"kind":"Name","value":"slotIntervalM"}},{"kind":"Field","name":{"kind":"Name","value":"gracePeriodM"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}},{"kind":"Field","name":{"kind":"Name","value":"venue"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]}}]} as unknown as DocumentNode<CreateServiceMutation, CreateServiceMutationVariables>;
export const UpdateServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateServiceInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateService"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"turnTimeM"}},{"kind":"Field","name":{"kind":"Name","value":"advanceNoticeM"}},{"kind":"Field","name":{"kind":"Name","value":"slotIntervalM"}},{"kind":"Field","name":{"kind":"Name","value":"gracePeriodM"}},{"kind":"Field","name":{"kind":"Name","value":"deletedAt"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateServiceMutation, UpdateServiceMutationVariables>;
export const DeleteServiceDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DeleteService"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"deleteService"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}]}]}}]} as unknown as DocumentNode<DeleteServiceMutation, DeleteServiceMutationVariables>;
export const SearchVenuesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchVenues"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"VenueSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchVenues"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchVenuesQuery, SearchVenuesQueryVariables>;
export const GetVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"venue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetVenueQuery, GetVenueQueryVariables>;
export const CreateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CreateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<CreateVenueMutation, CreateVenueMutationVariables>;
export const UpdateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateVenueMutation, UpdateVenueMutationVariables>;
export const ActivateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"ActivateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"activateVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<ActivateVenueMutation, ActivateVenueMutationVariables>;
export const CloseVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CloseVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"closeVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<CloseVenueMutation, CloseVenueMutationVariables>;
export const DisableVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"DisableVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"disableVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<DisableVenueMutation, DisableVenueMutationVariables>;
export const EnableVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"EnableVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"enableVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"status"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<EnableVenueMutation, EnableVenueMutationVariables>;