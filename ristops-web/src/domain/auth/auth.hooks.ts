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
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['auth.getMe'] });
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
      queryClient.setQueryData(['auth.getMe'], null);
      void navigate('/login');
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
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['auth.getMe'] });
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
    staleTime: Infinity,
  });

  const isAllowed =
    !!data && permissions.some((p) => hasPermission(data.myGrants.grants, p));

  return { isAllowed, isLoading };
}
