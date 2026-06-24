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

/** User information to update. */
export type ListRolesInput = {
  /** Resource identifier. */
  resourceId: Scalars['String']['input'];
  /** Resource type. */
  resourceType: ResourceType;
};

export type Mutation = {
  __typename?: 'Mutation';
  /** Create a new venue. */
  createVenue: Venue;
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

export type Query = {
  __typename?: 'Query';
  /** Fetch authenticated user */
  me: User;
  /** Fetch roles assigned to the authenticated user on a resource */
  myRoles: UserRoleGrants;
  /** Fetch role by ID */
  role: Role;
  /** Search venues the user has access to. */
  searchVenues: VenuePage;
  /** Fetch user by ID */
  user: User;
  /** Fetch venue by ID */
  venue: Venue;
};


export type QueryMyRolesArgs = {
  input: ListRolesInput;
};


export type QueryRoleArgs = {
  roleId: Scalars['String']['input'];
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

export const ResourceType = {
  Acl: 'ACL',
  App: 'APP',
  Permission: 'PERMISSION',
  Role: 'ROLE',
  User: 'USER',
  Venue: 'VENUE'
} as const;

export type ResourceType = typeof ResourceType[keyof typeof ResourceType];
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

export type ListMyRolesQueryVariables = Exact<{
  input: ListRolesInput;
}>;


export type ListMyRolesQuery = { __typename?: 'Query', myRoles: { __typename?: 'UserRoleGrants', grants: Array<{ __typename?: 'UserRoleGrant', resource: { __typename?: 'AuthorizationResource', resourceId: string, resourceType: ResourceType }, role: { __typename?: 'Role', id: string, name: string, description: string, permissions: Array<string> } }> } };

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


export const ListMyRolesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"ListMyRoles"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ListRolesInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"myRoles"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"grants"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resource"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"resourceId"}},{"kind":"Field","name":{"kind":"Name","value":"resourceType"}}]}},{"kind":"Field","name":{"kind":"Name","value":"role"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"permissions"}}]}}]}}]}}]}}]} as unknown as DocumentNode<ListMyRolesQuery, ListMyRolesQueryVariables>;
export const GetMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetMe"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"me"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetMeQuery, GetMeQueryVariables>;
export const UpdateMeDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateMe"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateUserInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateMe"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"username"}},{"kind":"Field","name":{"kind":"Name","value":"displayName"}},{"kind":"Field","name":{"kind":"Name","value":"email"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateMeMutation, UpdateMeMutationVariables>;
export const SearchVenuesDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"SearchVenues"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"VenueSearchInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"searchVenues"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"items"},"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}},{"kind":"Field","name":{"kind":"Name","value":"total"}},{"kind":"Field","name":{"kind":"Name","value":"page"}},{"kind":"Field","name":{"kind":"Name","value":"pageSize"}},{"kind":"Field","name":{"kind":"Name","value":"totalPages"}}]}}]}}]} as unknown as DocumentNode<SearchVenuesQuery, SearchVenuesQueryVariables>;
export const GetVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"query","name":{"kind":"Name","value":"GetVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"venue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<GetVenueQuery, GetVenueQueryVariables>;
export const CreateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"CreateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"CreateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"createVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<CreateVenueMutation, CreateVenueMutationVariables>;
export const UpdateVenueDocument = {"kind":"Document","definitions":[{"kind":"OperationDefinition","operation":"mutation","name":{"kind":"Name","value":"UpdateVenue"},"variableDefinitions":[{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"id"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"ID"}}}},{"kind":"VariableDefinition","variable":{"kind":"Variable","name":{"kind":"Name","value":"input"}},"type":{"kind":"NonNullType","type":{"kind":"NamedType","name":{"kind":"Name","value":"UpdateVenueInput"}}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"updateVenue"},"arguments":[{"kind":"Argument","name":{"kind":"Name","value":"id"},"value":{"kind":"Variable","name":{"kind":"Name","value":"id"}}},{"kind":"Argument","name":{"kind":"Name","value":"input"},"value":{"kind":"Variable","name":{"kind":"Name","value":"input"}}}],"selectionSet":{"kind":"SelectionSet","selections":[{"kind":"Field","name":{"kind":"Name","value":"id"}},{"kind":"Field","name":{"kind":"Name","value":"name"}},{"kind":"Field","name":{"kind":"Name","value":"address"}},{"kind":"Field","name":{"kind":"Name","value":"description"}},{"kind":"Field","name":{"kind":"Name","value":"createdAt"}},{"kind":"Field","name":{"kind":"Name","value":"updatedAt"}}]}}]}}]} as unknown as DocumentNode<UpdateVenueMutation, UpdateVenueMutationVariables>;