import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import type {
  CreateServiceInput,
  UpdateServiceInput,
} from '../../services/graphql/graphql.ts';
import { serviceApi } from './service.api.ts';

/**
 * Error text for a failed service write. A 409 means the hours or validity period would put the
 * service on top of another one — the backend names which, so its message is more useful than
 * anything generic.
 */
function serviceWriteError(error: unknown, fallback: string): string {
  const status = (error as { status?: number })?.status;
  const detail = (error as { message?: string })?.message;
  return status === 409 && detail ? detail : fallback;
}

export function useService(id: string | null | undefined) {
  return useQuery({
    queryKey: ['service.get', id],
    queryFn: () => serviceApi.getService(id as string),
    enabled: !!id,
  });
}

export function useListVenueServices(
  venueId: string,
  name?: string,
  includeDeleted?: boolean,
) {
  return useQuery({
    queryKey: ['service.list', venueId, name, includeDeleted],
    queryFn: () => serviceApi.listServices(venueId, name, includeDeleted),
  });
}

export function useCreateService(venueId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateServiceInput) =>
      serviceApi.createService(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['service.list', venueId],
      });
    },
    onError: (error) => {
      void message.error(serviceWriteError(error, 'Could not create the service'));
    },
  });
}

export function useUpdateService(venueId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateServiceInput }) =>
      serviceApi.updateService(id, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['service.list', venueId],
      });
    },
    onError: (error) => {
      void message.error(serviceWriteError(error, 'Could not update the service'));
    },
  });
}

export function useDeleteService(venueId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => serviceApi.deleteService(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['service.list', venueId],
      });
    },
    onError: () => {
      void message.error('Could not delete the service');
    },
  });
}
