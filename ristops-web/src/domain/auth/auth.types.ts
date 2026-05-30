import type { UserProfileModel } from '../../services/graphql/graphql.ts';

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserProfileModel | undefined;
}

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
