import { restClient } from '../../services/rest.ts';
import type { LoginInput, LoginResponse, RegisterInput } from './auth.types.ts';
import { gqlRequest } from '../../services/graphql/client.ts';
import {
  GetMeDocument,
  UpdateMeDocument,
  type UpdateMeMutationVariables,
} from '../../services/graphql/graphql.ts';

const BASE_PATH = '/auth';

export const authnApi = {
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
  updateMe: (variables: UpdateMeMutationVariables) =>
    gqlRequest(UpdateMeDocument, variables),
};
