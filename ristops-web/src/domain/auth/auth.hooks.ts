import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authnApi, userApi } from './auth.api.ts';
import { useNavigate } from 'react-router-dom';
import type { AuthState } from './auth.types.ts';

export function useAuth(): AuthState {
  const { data, isLoading } = useQuery({
    queryKey: ['auth.getMe'],
    queryFn: userApi.getMe,
    retry: false,
  });

  return {
    isAuthenticated: !!data,
    isLoading,
    user: data?.me,
  };
}

export function useLogin() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authnApi.login,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['auth.getMe'] });
      void navigate('/');
    },
  });
}

export function useLogout() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: authnApi.logout,
    onSuccess: () => {
      void navigate('/login');
      void queryClient.invalidateQueries({ queryKey: ['auth.getMe'] });
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
    mutationFn: authnApi.register,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['auth.getMe'] });
      void navigate('/');
    },
  });
}
