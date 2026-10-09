import {
  type QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { message } from 'antd';
import type {
  ClosingCreateInput,
  ClosingSearchInput,
  ClosingUpdateInput,
  OpeningUpsertInput,
} from '../../services/graphql/graphql.ts';
import { scheduleApi } from './schedule.api.ts';

/**
 * Error text for a failed schedule write. The backend returns 409 with the specific conflict —
 * which service overlaps, or that a closing is what keeps two services apart — and that is far
 * more actionable than a generic message.
 */
function scheduleWriteError(error: unknown, fallback: string): string {
  const status = (error as { status?: number })?.status;
  const detail = (error as { message?: string })?.message;
  return status === 409 && detail ? detail : fallback;
}

/** Invalidate every schedule-derived query after a write, plus the calendar it feeds. */
function invalidateSchedule(queryClient: QueryClient) {
  void queryClient.invalidateQueries({ queryKey: ['schedule.openings'] });
  void queryClient.invalidateQueries({ queryKey: ['schedule.closings'] });
  void queryClient.invalidateQueries({ queryKey: ['reservations.calendar'] });
}

export function useServiceOpenings(serviceId: string | null | undefined) {
  return useQuery({
    queryKey: ['schedule.openings', serviceId],
    queryFn: () => scheduleApi.listServiceOpenings(serviceId as string),
    enabled: !!serviceId,
  });
}

export function useUpsertServiceOpenings(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: OpeningUpsertInput[]) =>
      scheduleApi.upsertServiceOpenings(serviceId, input),
    onSuccess: () => {
      invalidateSchedule(queryClient);
      void message.success('Weekly hours saved');
    },
    onError: (error) => {
      void message.error(scheduleWriteError(error, 'Could not save the weekly hours'));
    },
  });
}

export function useSearchClosings(venueId: string, input?: ClosingSearchInput) {
  return useQuery({
    queryKey: ['schedule.closings', venueId, input],
    queryFn: () => scheduleApi.searchClosings(venueId, input),
    enabled: !!venueId,
  });
}

/** Every closing matching the filter, paged to completion — for a whole-month overlay. */
export function useAllClosings(venueId: string, input?: ClosingSearchInput) {
  return useQuery({
    queryKey: ['schedule.closings', venueId, 'all', input],
    queryFn: () => scheduleApi.searchAllClosings(venueId, input),
    enabled: !!venueId,
  });
}

export function useCreateClosing(venueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ClosingCreateInput) => scheduleApi.createClosing(venueId, input),
    onSuccess: () => {
      invalidateSchedule(queryClient);
      void message.success('Closure created');
    },
    onError: (error) => {
      void message.error(scheduleWriteError(error, 'Could not create the closure'));
    },
  });
}

export function useUpdateClosing(venueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ClosingUpdateInput }) =>
      scheduleApi.updateClosing(venueId, id, input),
    onSuccess: () => {
      invalidateSchedule(queryClient);
      void message.success('Closure updated');
    },
    onError: (error) => {
      void message.error(scheduleWriteError(error, 'Could not update the closure'));
    },
  });
}

export function useDeleteClosing(venueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => scheduleApi.deleteClosing(venueId, id),
    onSuccess: () => {
      invalidateSchedule(queryClient);
      void message.success('Closure deleted');
    },
    onError: (error) => {
      void message.error(scheduleWriteError(error, 'Could not delete the closure'));
    },
  });
}
