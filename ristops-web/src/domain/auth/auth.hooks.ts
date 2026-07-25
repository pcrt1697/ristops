import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authNApi, authZApi, userApi } from './auth.api.ts';
import { useNavigate } from 'react-router-dom';
import type { AuthState } from './auth.types.ts';
import type { ServiceError } from '../../services/common.ts';
import { message } from 'antd';
import type {
  GetMeQuery,
  ListRolesInput,
  MemberSearchInput,
  ResourceType,
  SearchResourceGrantsInput,
} from '../../services/graphql/graphql.ts';
import { hasPermission } from './authz.utils.ts';
import { useCurrentVenue } from '../venue/venue.hooks.ts';

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
  const { setCurrentVenueId } = useCurrentVenue();

  return useMutation({
    mutationFn: authNApi.logout,
    onSuccess: () => {
      // Clear first: CurrentVenueProvider lives above the routes and outlives this tab's
      // session, so a stale venue (from this login, a since-deleted/reseeded venue, or one
      // the next login's user can't access) would otherwise leak into the next login and
      // surface as an error the moment TopBar mounts and re-fetches it.
      setCurrentVenueId(null);
      // Write (not remove/invalidate) auth state synchronously and network-free. getMe has
      // no `enabled` gate — it's what *defines* isAuthenticated, so it can't gate on itself
      // — so ProtectedRoute's useAuth() must see "logged out" without any fetch being
      // possible. This is what actually unmounts the authenticated tree (ProtectedRoute
      // renders <Navigate> on its very next render); `me: null` deliberately violates
      // GetMeQuery's non-null `me` since this value never comes from the server.
      queryClient.setQueryData(
        ['auth.getMe'],
        { me: null } as unknown as GetMeQuery,
      );
      void navigate('/login');
      // Deferred so it runs after the redirect above has unmounted the authenticated tree
      // (ProtectedRoute, TopBar, VenueDrawer, ...) — by then there are no observers left on
      // getMe/myRoles/venue-scoped queries, so clearing can't trigger a refetch against the
      // now-invalidated session. Previously `clear()` itself was the only "you're logged
      // out" signal, racing an active observer's auto-refetch against React's unmount.
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
  const { isAuthenticated } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: ['auth.myRoles', resource.type, resource.id],
    queryFn: () => authZApi.listMyGrants(resource.type, resource.id),
    // Not Infinity: grants can change server-side (e.g. an admin assigns a new
    // role). A finite window lets the default focus/mount refetch pick up new
    // permissions without forcing the user to log in again.
    staleTime: 5 * 60 * 1000,
    // Only ever meaningful for a logged-in user; also guards against firing during the
    // logout race (session invalidated server-side before the authenticated tree unmounts).
    enabled: isAuthenticated,
  });

  const isAllowed =
    !!data && permissions.some((p) => hasPermission(data.myGrants.grants, p));

  return { isAllowed, isLoading };
}
