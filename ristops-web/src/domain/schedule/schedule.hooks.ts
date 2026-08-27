import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { Form, type FormInstance, message } from 'antd';
import type { Dayjs } from 'dayjs';
import { useMemo } from 'react';
import { useDebounced } from '../../commons/hooks.ts';
import type { ServiceError } from '../../services/common.ts';
import type {
  CapacityOverrideCreateInput,
  CapacityOverrideUpdateInput,
  ConflictCheckInput,
  OpeningConflictCheckInput,
  OpeningOverrideCreateInput,
  OpeningOverrideUpdateInput,
  OpeningUpsertInput,
  ScheduleDateFilter,
  ServiceClosingCreateInput,
  ServiceClosingUpdateInput,
  VenueClosingCreateInput,
  VenueClosingUpdateInput,
  Weekday,
} from '../../services/graphql/graphql.ts';
import { scheduleApi } from './schedule.api.ts';
import { normalizeWeekdays } from './schedule.utils.ts';

/** Only toast non-conflict failures — a 409 is shown inline in the modal by the live check. */
function toastUnlessConflict(msg: string) {
  return (error: unknown) => {
    if ((error as ServiceError).status !== 409) void message.error(msg);
  };
}

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
    onError: toastUnlessConflict('Could not save the weekly hours'),
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
    onError: toastUnlessConflict('Could not create the override'),
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
    onError: toastUnlessConflict('Could not update the override'),
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
    onError: toastUnlessConflict('Could not create the closing'),
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
    onError: toastUnlessConflict('Could not update the closing'),
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
    onError: toastUnlessConflict('Could not create the capacity change'),
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
    onError: toastUnlessConflict('Could not update the capacity change'),
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
    queryKey: [
      'schedule.venueClosings',
      venueId,
      'page',
      filter,
      page,
      pageSize,
    ],
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
    onError: toastUnlessConflict('Could not create the venue closure'),
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
    onError: toastUnlessConflict('Could not update the venue closure'),
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

// --- Conflict previews (live, pre-submit check in the creation/edit modals) ----
// Each query is keyed under the same base as its kind's calendar/page queries, so a
// create/update mutation (which invalidates that base key) also refreshes any open preview.

interface ConflictFormFields {
  dates?: [Dayjs, Dayjs];
  // Single value when editing one row; multiple when bulk-creating one row per weekday.
  weekday?: Weekday | Weekday[];
}

/**
 * Derive a debounced `ConflictCheckInput` from a schedule form's `dates`/`weekday` fields, or
 * `undefined` while the date range isn't complete yet (nothing to check). `excludeId` should be
 * the row's own id when editing, so it doesn't conflict with itself.
 */
export function useConflictCandidate<T extends ConflictFormFields>(
  form: FormInstance<T>,
  excludeId?: string,
): ConflictCheckInput | undefined {
  const dates = Form.useWatch('dates', form) as [Dayjs, Dayjs] | undefined;
  const weekday = Form.useWatch('weekday', form) as
    | Weekday
    | Weekday[]
    | undefined;
  // Only opening-override forms have hours; other schedule forms leave these undefined, and the
  // backend only uses them for the cross-service opening-overlap check.
  const startTime = Form.useWatch('startTime', form) as Dayjs | undefined;
  const endTime = Form.useWatch('endTime', form) as Dayjs | undefined;

  const candidate = useMemo<ConflictCheckInput | undefined>(() => {
    if (!dates?.[0] || !dates[1]) return undefined;
    const weekdays = Array.isArray(weekday)
      ? normalizeWeekdays(weekday)
      : weekday
        ? [weekday]
        : undefined;
    return {
      dateStart: dates[0].format('YYYY-MM-DD'),
      dateEnd: dates[1].format('YYYY-MM-DD'),
      weekdays,
      excludeId,
      startTime: startTime ? startTime.format('HH:mm:ss') : undefined,
      endTime: endTime ? endTime.format('HH:mm:ss') : undefined,
    };
  }, [dates, weekday, startTime, endTime, excludeId]);

  return useDebounced(candidate);
}

/**
 * Preview cross-service opening overlaps for a set of candidate weekly openings (the weekly-hours
 * editor edits up to seven days at once). One query per candidate via `useQueries`; results are
 * flattened into a single conflict list with combined loading/error state.
 */
export function useServiceOpeningConflictsForCandidates(
  serviceId: string,
  candidates: OpeningConflictCheckInput[],
) {
  const results = useQueries({
    queries: candidates.map((candidate) => ({
      queryKey: ['schedule.openings', serviceId, 'conflicts', candidate],
      queryFn: () => scheduleApi.serviceOpeningConflicts(serviceId, candidate),
      enabled: !!serviceId,
    })),
  });
  return {
    conflicts: results.flatMap((result) => result.data ?? []),
    isFetching: results.some((result) => result.isFetching),
    isError: results.some((result) => result.isError),
    refetch: () => results.forEach((result) => void result.refetch()),
  };
}

export function useOpeningOverrideConflicts(
  serviceId: string,
  candidate: ConflictCheckInput | undefined,
) {
  return useQuery({
    queryKey: ['schedule.overrides', serviceId, 'conflicts', candidate],
    queryFn: () => scheduleApi.openingOverrideConflicts(serviceId, candidate!),
    enabled: !!serviceId && !!candidate,
  });
}

export function useServiceClosingConflicts(
  serviceId: string,
  candidate: ConflictCheckInput | undefined,
) {
  return useQuery({
    queryKey: ['schedule.closings', serviceId, 'conflicts', candidate],
    queryFn: () => scheduleApi.serviceClosingConflicts(serviceId, candidate!),
    enabled: !!serviceId && !!candidate,
  });
}

export function useCapacityOverrideConflicts(
  serviceId: string,
  candidate: ConflictCheckInput | undefined,
) {
  return useQuery({
    queryKey: ['schedule.capacityOverrides', serviceId, 'conflicts', candidate],
    queryFn: () => scheduleApi.capacityOverrideConflicts(serviceId, candidate!),
    enabled: !!serviceId && !!candidate,
  });
}

export function useVenueClosingConflicts(
  venueId: string,
  candidate: ConflictCheckInput | undefined,
) {
  return useQuery({
    queryKey: ['schedule.venueClosings', venueId, 'conflicts', candidate],
    queryFn: () => scheduleApi.venueClosingConflicts(venueId, candidate!),
    enabled: !!venueId && !!candidate,
  });
}
