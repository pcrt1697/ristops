import type { GetMeQuery } from '../../services/graphql/graphql.ts';

export type User = GetMeQuery['me'];

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | undefined;
}

export type ProfileFormValues = {
  username?: string;
  displayName?: string;
  email?: string;
  password?: string;
};

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  username: string;
  displayName: string;
  email: string;
  password: string;
}

export interface LoginResponse {
  id: string;
  email: string;
  username: string;
  displayName: string;
}
