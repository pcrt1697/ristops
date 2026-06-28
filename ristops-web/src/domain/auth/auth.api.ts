import { restClient } from '../../services/rest.ts';
import type { LoginInput, LoginResponse, RegisterInput } from './auth.types.ts';
import { gqlRequest } from '../../services/graphql/client.ts';
import {
  GetMeDocument,
  type GrantAccessInput,
  GrantAccessDocument,
  ListMyGrantsDocument,
  ListPermissionsDocument,
  ListRolesDocument,
  type ListRolesInput,
  type MemberSearchInput,
  type ResourceType,
  type RevokeAccessInput,
  RevokeAccessDocument,
  type SearchResourceGrantsInput,
  SearchMembersDocument,
  SearchResourceGrantsDocument,
  UpdateMeDocument,
  type UpdateUserInput,
} from '../../services/graphql/graphql.ts';

const BASE_PATH = '/auth';

export const authNApi = {
  login: (input: LoginInput) =>
    restClient<LoginResponse>(BASE_PATH + '/login', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  logout: () => restClient<void>(BASE_PATH + '/logout', { method: 'POST' }),

  register: (input: RegisterInput) =>
    restClient<LoginResponse>(BASE_PATH + '/register', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
};

export const userApi = {
  getMe: () => gqlRequest(GetMeDocument),
  updateMe: (input: UpdateUserInput) => gqlRequest(UpdateMeDocument, { input }),
};

export const authZApi = {
  listMyGrants: (resourceType: ResourceType, resourceId: string) =>
    gqlRequest(ListMyGrantsDocument, { input: { resourceType, resourceId } }),

  listRoles: (input: ListRolesInput) =>
    gqlRequest(ListRolesDocument, { input }),

  listPermissions: (query: string | null) =>
    gqlRequest(ListPermissionsDocument, { query }),

  searchResourceGrants: (input: SearchResourceGrantsInput) =>
    gqlRequest(SearchResourceGrantsDocument, { input }),

  searchMembers: (input: MemberSearchInput) =>
    gqlRequest(SearchMembersDocument, { input }),

  grantAccess: (input: GrantAccessInput) =>
    gqlRequest(GrantAccessDocument, { input }),

  revokeAccess: (input: RevokeAccessInput) =>
    gqlRequest(RevokeAccessDocument, { input }),
};
