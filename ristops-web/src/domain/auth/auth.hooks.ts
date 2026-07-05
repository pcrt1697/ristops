import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authNApi, authZApi, userApi } from './auth.api.ts';
import { useNavigate } from 'react-router-dom';
import type { AuthState } from './auth.types.ts';
import type { ServiceError } from '../../services/common.ts';
import { message } from 'antd';
import type {
  ListRolesInput,
  MemberSearchInput,
  ResourceType,
  SearchResourceGrantsInput,
} from '../../services/graphql/graphql.ts';
import { hasPermission } from './authz.utils.ts';

export function useAuth(): AuthState {
  const { data, isLoading } = useQuery({
    queryKey: ['auth.getMe'],
    queryFn: userApi.getMe,
    retry: false,
    staleTime: Infinity,
  });

  return {
    isAuthenticated: !!data?.me,
    isLoading,
    user: data?.me,
  };
}

export function useLogin() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authNApi.login,
    onSuccess: async () => {
      // Await a real refetch (the query is inactive on /login, so the default
      // active-only invalidate wouldn't refetch it): navigating before getMe is
      // authenticated makes ProtectedRoute read stale state and bounce to /login.
      await queryClient.invalidateQueries({
        queryKey: ['auth.getMe'],
        refetchType: 'all',
      });
      void navigate('/');
    },
    onError(error: ServiceError) {
      const errorMessage =
        error?.status == 401 || error?.status == 403
          ? 'Invalid username or password'
          : 'Oops! Something went wrong';
      void message.error(errorMessage);
    },
  });
}

export function useLogout() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authNApi.logout,
    onSuccess: () => {
      void navigate('/login');
      // Drop all cached data (getMe, myRoles/permissions, venue-scoped queries)
      // so the next user to log in on this tab never reads the previous session.
      // Deferred until after the redirect unmounts the authenticated layout:
      // clearing while its queries (e.g. the current venue) are still active
      // would retrigger them, firing a wasted backend call at logout.
      setTimeout(() => queryClient.clear(), 0);
    },
    onError: (error) => {
      console.log('logout error', error);
    },
  });
}

export function useUpdateMe() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: userApi.updateMe,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['auth.getMe'] });
    },
  });
}

export function useRegister() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authNApi.register,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ['auth.getMe'],
        refetchType: 'all',
      });
      void navigate('/');
    },
  });
}

export function useListRoles(input: ListRolesInput, enabled = true) {
  return useQuery({
    queryKey: ['authz.listRoles', input],
    queryFn: () => authZApi.listRoles(input),
    enabled,
  });
}

export function useListPermissions(input: string | null = null, enabled = true) {
  return useQuery({
    queryKey: ['authz.listPermissions', input],
    queryFn: () => authZApi.listPermissions(input),
    enabled,
  });
}

export function useSearchResourceGrants(
  input: SearchResourceGrantsInput,
  enabled = true,
) {
  return useQuery({
    queryKey: ['authz.searchResourceGrants', input],
    queryFn: () => authZApi.searchResourceGrants(input),
    enabled,
  });
}

export function useSearchMembers(input: MemberSearchInput, enabled = true) {
  return useQuery({
    queryKey: ['authz.searchMembers', input],
    queryFn: () => authZApi.searchMembers(input),
    enabled,
  });
}

export function useGrantAccess() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authZApi.grantAccess,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['authz.searchResourceGrants'],
      });
    },
  });
}

export function useRevokeAccess() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authZApi.revokeAccess,
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['authz.searchResourceGrants'],
      });
    },
  });
}

export function useCan(
  resource: { type: ResourceType; id: string },
  ...permissions: string[]
) {
  const { data, isLoading } = useQuery({
    queryKey: ['auth.myRoles', resource.type, resource.id],
    queryFn: () => authZApi.listMyGrants(resource.type, resource.id),
    // Not Infinity: grants can change server-side (e.g. an admin assigns a new
    // role). A finite window lets the default focus/mount refetch pick up new
    // permissions without forcing the user to log in again.
    staleTime: 5 * 60 * 1000,
  });

  const isAllowed =
    !!data && permissions.some((p) => hasPermission(data.myGrants.grants, p));

  return { isAllowed, isLoading };
}
