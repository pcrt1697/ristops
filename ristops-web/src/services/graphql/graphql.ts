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
  /** Date with time (isoformat) */
  DateTime: { input: string; output: string; }
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
  /** Create a new venue. */
  createVenue: Venue;
  /** Grant a role to a user on a resource */
  grantAccess: Acl;
  /** Revoke a role from a user on a resource */
  revokeAccess: Scalars['Boolean']['output'];
  /** Update current user data */
  updateMe: User;
  /** Update user data by ID */
  updateUser: User;
  /** Update venue data */
  updateVenue: Venue;
};


export type MutationCreateVenueArgs = {
  input: CreateVenueInput;
};


export type MutationGrantAccessArgs = {
  input: GrantAccessInput;
};


export type MutationRevokeAccessArgs = {
  input: RevokeAccessInput;
};


export type MutationUpdateMeArgs = {
  input: UpdateUserInput;
};


export type MutationUpdateUserArgs = {
  id: Scalars['ID']['input'];
  input: UpdateUserInput;
};


export type MutationUpdateVenueArgs = {
  id: Scalars['ID']['input'];
  input: UpdateVenueInput;
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
  /** Fetch user by ID */
  user: User;
  /** Fetch venue by ID */
  venue: Venue;
};


export type QueryListPermissionsArgs = {
  input?: InputMaybe<Scalars['String']['input']>;
};


export type QueryListRolesArgs = {
  input: ListRolesInput;
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


export type QueryUserArgs = {
  id: Scalars['ID']['input'];
};


export type QueryVenueArgs = {
  id: Scalars['ID']['input'];
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

/** Direction of a sort clause. */
export const SortDirection = {
  Asc: 'ASC',
  Desc: 'DESC'
} as const;

export type SortDirection = typeof SortDirection[keyof typeof SortDirection];
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

export type ListMyGrantsQueryVariables = Exact<{
  input: ListGrantsInput;
}>;


export type ListMyGrantsQuery = { __typename?: 'Query', myGrants: { __typename?: 'UserRoleGrants', grants: Array<{ __typename?: 'UserRoleGrant', resource: { __typename?: 'AuthorizationResource', resourceId: string, resourceType: ResourceType }, role: { __typename?: 'Role', id: string, name: string, description: string, permissions: Array<string> } }> } };

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


export type SearchResourceGrantsQuery = { __typename?: 'Query', searchResourceGrants: { __typename?: 'ResourceUserGrantsPage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'ResourceUserGrants', user: { __typename?: 'Member', id: string, username: string, displayName?: string | null }, grants: Array<{ __typename?: 'RoleGrant', assignedAt: string, expiresAt?: string | null, role: { __typename?: 'Role', id: string, name: string }, resource: { __typename?: 'AuthorizationResource', resourceId: string, resourceType: ResourceType } }> }> } };

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

export type SearchVenuesQueryVariables = Exact<{
  input: VenueSearchInput;
}>;


export type SearchVenuesQuery = { __typename?: 'Query', searchVenues: { __typename?: 'VenuePage', total: number, page: number, pageSize: number, totalPages: number, items: Array<{ __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, createdAt: string, updatedAt: string }> } };

export type GetVenueQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetVenueQuery = { __typename?: 'Query', venue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, createdAt: string, updatedAt: string } };

export type CreateVenueMutationVariables = Exact<{
  input: CreateVenueInput;
}>;


export type CreateVenueMutation = { __typename?: 'Mutation', createVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, createdAt: string, updatedAt: string } };

export type UpdateVenueMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: UpdateVenueInput;
}>;


export type UpdateVenueMutation = { __typename?: 'Mutation', updateVenue: { __typename?: 'Venue', id: string, name: string, address: string, description?: string | null, createdAt: string, updatedAt: string } };


export const ListMyGrantsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListMyGrants"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ListGrantsInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"myGrants"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"grants"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resource"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resourceId"}},{"kind":"Field","name":{"kind":"Name","value":"resourceType"}}]}},{"kind":"Field","name":{"kind":"Name","value":"role"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]}}]}}]} as unknown as DocumentNode<ListMyGrantsQuery, ListMyGrantsQueryVariables>;
export const ListRolesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListRoles"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ListRolesInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listRoles"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"roles"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"scope"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]}}]} as unknown as DocumentNode<ListRolesQuery, ListRolesQueryVariables>;
export const ListPermissionsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListPermissions"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"query"}},"type":{"kind":"NamedType","name":{"kind":"Name","value":"String"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"listPermissions"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"query"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]} as unknown as DocumentNode<ListPermissionsQuery, ListPermissionsQueryVariables>;
export const SearchResourceGrantsDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchResourceGrants"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"SearchResourceGrantsInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchResourceGrants"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"user"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}}]}},{"kind":"Field","name":{"kind":"Name","value":"grants"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"role"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}}]}},{"kind":"Field","name":{"kind":"Name","value":"resource"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resourceId"}},{"kind":"Field","name":{"kind":"Name","value":"resourceType"}}]}},{"kind":"Field","name":{"kind":"Name","value":"assignedAt"}},{"kind":"Field","name":{"kind":"Name","value":"expiresAt"}}]}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchResourceGrantsQuery, SearchResourceGrantsQueryVariables>;
export const SearchMembersDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchMembers"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"MemberSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchMembers"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchMembersQuery, SearchMembersQueryVariables>;
export const GrantAccessDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"GrantAccess"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"GrantAccessInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"grantAccess"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}}]}}]}}]} as unknown as DocumentNode<GrantAccessMutation, GrantAccessMutationVariables>;
export const RevokeAccessDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"RevokeAccess"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"RevokeAccessInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"revokeAccess"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}]}]}}]} as unknown as DocumentNode<RevokeAccessMutation, RevokeAccessMutationVariables>;
export const GetMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetMe"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"me"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetMeQuery, GetMeQueryVariables>;
export const UpdateMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateMe"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateUserInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateMe"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateMeMutation, UpdateMeMutationVariables>;
export const SearchVenuesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchVenues"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"VenueSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchVenues"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchVenuesQuery, SearchVenuesQueryVariables>;
export const GetVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"venue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetVenueQuery, GetVenueQueryVariables>;
export const CreateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CreateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<CreateVenueMutation, CreateVenueMutationVariables>;
export const UpdateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateVenueMutation, UpdateVenueMutationVariables>;