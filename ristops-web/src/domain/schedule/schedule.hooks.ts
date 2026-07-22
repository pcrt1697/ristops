import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import type {
  CapacityOverrideCreateInput,
  CapacityOverrideUpdateInput,
  ServiceClosingCreateInput,
  ServiceClosingUpdateInput,
  OpeningOverrideCreateInput,
  OpeningOverrideUpdateInput,
  OpeningUpsertInput,
  ScheduleDateFilter,
  VenueClosingCreateInput,
  VenueClosingUpdateInput,
} from '../../services/graphql/graphql.ts';
import { scheduleApi } from './schedule.api.ts';

export function useServiceOpenings(
  serviceId: string,
  includeDeleted?: boolean,
) {
  return useQuery({
    queryKey: ['schedule.openings', serviceId, includeDeleted],
    queryFn: () => scheduleApi.listServiceOpenings(serviceId, includeDeleted),
    enabled: !!serviceId,
  });
}

export function useUpsertServiceOpenings(serviceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (openings: OpeningUpsertInput[]) =>
      scheduleApi.upsertServiceOpenings(serviceId, openings),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.openings', serviceId],
      });
      void message.success('Weekly hours saved');
    },
    onError: () => {
      void message.error('Could not save the weekly hours');
    },
  });
}

// --- Opening overrides -------------------------------------------------------

export function useServiceOpeningOverrides(
  serviceId: string,
  dateFrom: string,
  dateTo: string,
) {
  return useQuery({
    queryKey: ['schedule.overrides', serviceId, dateFrom, dateTo],
    queryFn: () =>
      scheduleApi.searchAllOpeningOverrides(serviceId, { dateFrom, dateTo }),
    enabled: !!serviceId,
  });
}

export function useCreateOpeningOverride(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: OpeningOverrideCreateInput) =>
      scheduleApi.createOpeningOverride(serviceId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.overrides', serviceId],
      });
    },
    onError: () => void message.error('Could not create the override'),
  });
}

export function useUpdateOpeningOverride(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      overrideId,
      input,
    }: {
      overrideId: string;
      input: OpeningOverrideUpdateInput;
    }) => scheduleApi.updateOpeningOverride(serviceId, overrideId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.overrides', serviceId],
      });
    },
    onError: () => void message.error('Could not update the override'),
  });
}

export function useDeleteOpeningOverride(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (overrideId: string) =>
      scheduleApi.deleteOpeningOverride(serviceId, overrideId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.overrides', serviceId],
      });
    },
    onError: () => void message.error('Could not delete the override'),
  });
}

// --- Service closings ---------------------------------------------------------

export function useServiceClosings(
  serviceId: string,
  dateFrom: string,
  dateTo: string,
) {
  return useQuery({
    queryKey: ['schedule.closings', serviceId, dateFrom, dateTo],
    queryFn: () =>
      scheduleApi.searchAllServiceClosings(serviceId, { dateFrom, dateTo }),
    enabled: !!serviceId,
  });
}

export function useCreateServiceClosing(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ServiceClosingCreateInput) =>
      scheduleApi.createServiceClosing(serviceId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.closings', serviceId],
      });
    },
    onError: () => void message.error('Could not create the closing'),
  });
}

export function useUpdateServiceClosing(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      closingId,
      input,
    }: {
      closingId: string;
      input: ServiceClosingUpdateInput;
    }) => scheduleApi.updateServiceClosing(serviceId, closingId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.closings', serviceId],
      });
    },
    onError: () => void message.error('Could not update the closing'),
  });
}

export function useDeleteServiceClosing(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (closingId: string) =>
      scheduleApi.deleteServiceClosing(serviceId, closingId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.closings', serviceId],
      });
    },
    onError: () => void message.error('Could not delete the closing'),
  });
}

// --- Capacity overrides ------------------------------------------------------

export function useServiceCapacityOverrides(
  serviceId: string,
  dateFrom: string,
  dateTo: string,
) {
  return useQuery({
    queryKey: ['schedule.capacityOverrides', serviceId, dateFrom, dateTo],
    queryFn: () =>
      scheduleApi.searchAllCapacityOverrides(serviceId, { dateFrom, dateTo }),
    enabled: !!serviceId,
  });
}

export function useCreateCapacityOverride(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CapacityOverrideCreateInput) =>
      scheduleApi.createCapacityOverride(serviceId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.capacityOverrides', serviceId],
      });
    },
    onError: () => void message.error('Could not create the capacity change'),
  });
}

export function useUpdateCapacityOverride(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      capacityOverrideId,
      input,
    }: {
      capacityOverrideId: string;
      input: CapacityOverrideUpdateInput;
    }) =>
      scheduleApi.updateCapacityOverride(serviceId, capacityOverrideId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.capacityOverrides', serviceId],
      });
    },
    onError: () => void message.error('Could not update the capacity change'),
  });
}

export function useDeleteCapacityOverride(serviceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (capacityOverrideId: string) =>
      scheduleApi.deleteCapacityOverride(serviceId, capacityOverrideId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.capacityOverrides', serviceId],
      });
    },
    onError: () => void message.error('Could not delete the capacity change'),
  });
}

// --- Paginated searches (the "all exceptions" drawer) ------------------------
// Keyed under the same base as the calendar month queries, so a create/update/delete
// invalidation (which targets the base key) refetches both the calendar and the drawer.

export function useSearchOpeningOverridesPage(
  serviceId: string,
  filter: ScheduleDateFilter,
  page: number,
  pageSize: number,
) {
  return useQuery({
    queryKey: ['schedule.overrides', serviceId, 'page', filter, page, pageSize],
    queryFn: () =>
      scheduleApi.searchOpeningOverrides(serviceId, filter, { page, pageSize }),
    enabled: !!serviceId,
  });
}

export function useSearchServiceClosingsPage(
  serviceId: string,
  filter: ScheduleDateFilter,
  page: number,
  pageSize: number,
) {
  return useQuery({
    queryKey: ['schedule.closings', serviceId, 'page', filter, page, pageSize],
    queryFn: () =>
      scheduleApi.searchServiceClosings(serviceId, filter, { page, pageSize }),
    enabled: !!serviceId,
  });
}

export function useSearchCapacityOverridesPage(
  serviceId: string,
  filter: ScheduleDateFilter,
  page: number,
  pageSize: number,
) {
  return useQuery({
    queryKey: [
      'schedule.capacityOverrides',
      serviceId,
      'page',
      filter,
      page,
      pageSize,
    ],
    queryFn: () =>
      scheduleApi.searchCapacityOverrides(serviceId, filter, {
        page,
        pageSize,
      }),
    enabled: !!serviceId,
  });
}

// --- Venue-wide closings -----------------------------------------------------
// Keyed by venue, so venue-closing mutations invalidate both the venue-settings management
// list and the per-service calendar overlay (both live under ['schedule.venueClosings', venueId]).

export function useVenueClosings(
  venueId: string,
  dateFrom: string,
  dateTo: string,
) {
  return useQuery({
    queryKey: ['schedule.venueClosings', venueId, dateFrom, dateTo],
    queryFn: () =>
      scheduleApi.searchAllVenueClosings(venueId, { dateFrom, dateTo }),
    enabled: !!venueId,
  });
}

export function useSearchVenueClosingsPage(
  venueId: string,
  filter: ScheduleDateFilter,
  page: number,
  pageSize: number,
) {
  return useQuery({
    queryKey: ['schedule.venueClosings', venueId, 'page', filter, page, pageSize],
    queryFn: () =>
      scheduleApi.searchVenueClosings(venueId, filter, { page, pageSize }),
    enabled: !!venueId,
  });
}

export function useCreateVenueClosing(venueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: VenueClosingCreateInput) =>
      scheduleApi.createVenueClosing(venueId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.venueClosings', venueId],
      });
    },
    onError: () => void message.error('Could not create the venue closure'),
  });
}

export function useUpdateVenueClosing(venueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      closingId,
      input,
    }: {
      closingId: string;
      input: VenueClosingUpdateInput;
    }) => scheduleApi.updateVenueClosing(venueId, closingId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.venueClosings', venueId],
      });
    },
    onError: () => void message.error('Could not update the venue closure'),
  });
}

export function useDeleteVenueClosing(venueId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (closingId: string) =>
      scheduleApi.deleteVenueClosing(venueId, closingId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['schedule.venueClosings', venueId],
      });
    },
    onError: () => void message.error('Could not delete the venue closure'),
  });
}
