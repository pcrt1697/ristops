import {
  type QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { message } from 'antd';
import type {
  CreateReservationInput,
  ReservationSearchInput,
  UpdateReservationInput,
} from '../../services/graphql/graphql.ts';
import { reservationApi } from './reservation.api.ts';

/**
 * Error text for a failed booking write. A 409 says exactly why — the service is not open then,
 * it is closed that date, or the seats are gone — which the form should show verbatim.
 */
function bookingError(error: unknown, fallback: string): string {
  const status = (error as { status?: number })?.status;
  const detail = (error as { message?: string })?.message;
  return status === 409 && detail ? detail : fallback;
}

/** Invalidate every reservation-derived query (detail, lists, calendar) after a mutation. */
function invalidateReservations(queryClient: QueryClient) {
  void queryClient.invalidateQueries({ queryKey: ['reservation'] });
  void queryClient.invalidateQueries({ queryKey: ['reservations'] });
  void queryClient.invalidateQueries({ queryKey: ['reservations.calendar'] });
}

export function useReservation(id: string) {
  return useQuery({
    queryKey: ['reservation', id],
    queryFn: () => reservationApi.getReservation(id),
    enabled: !!id,
  });
}

export function useSearchReservations(input: ReservationSearchInput, enabled = true) {
  return useQuery({
    queryKey: ['reservations', input],
    queryFn: () => reservationApi.searchReservations(input),
    enabled: enabled && !!input.filter.venueId,
  });
}

/**
 * Per-day, per-service occupancy over a window — the month grid, and the source of a day's
 * services and remaining seats for the booking form.
 */
export function useReservationCalendar(
  venueId: string,
  dateFrom: string,
  dateTo: string,
  // The scrolling calendar mounts many months at once and only fetches those actually
  // scrolled into view; months share a query key, so a visible month is fetched once.
  enabled = true,
) {
  return useQuery({
    queryKey: ['reservations.calendar', venueId, dateFrom, dateTo],
    queryFn: () => reservationApi.reservationCalendar(venueId, dateFrom, dateTo),
    enabled: enabled && !!venueId && !!dateFrom && !!dateTo,
  });
}

export function useCreateReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateReservationInput) => reservationApi.createReservation(input),
    onSuccess: () => invalidateReservations(queryClient),
    onError: (error) =>
      void message.error(bookingError(error, 'Could not create the reservation')),
  });
}

export function useUpdateReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateReservationInput }) =>
      reservationApi.updateReservation(id, input),
    onSuccess: () => invalidateReservations(queryClient),
    onError: (error) =>
      void message.error(bookingError(error, 'Could not update the reservation')),
  });
}

/** Shared shape for the notes-only status actions (confirm/reject/cancel/no-show/withdraw). */
function useReservationStatusAction(
  action: (id: string, notes?: string | null) => Promise<unknown>,
  errorMessage: string,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string | null }) => action(id, notes),
    onSuccess: () => invalidateReservations(queryClient),
    onError: () => void message.error(errorMessage),
  });
}

export const useConfirmReservation = () =>
  useReservationStatusAction(reservationApi.confirmReservation, 'Could not confirm the reservation');

export const useRejectReservation = () =>
  useReservationStatusAction(reservationApi.rejectReservation, 'Could not reject the reservation');

export const useCancelReservation = () =>
  useReservationStatusAction(reservationApi.cancelReservation, 'Could not cancel the reservation');

export const useNoShowReservation = () =>
  useReservationStatusAction(
    reservationApi.noShowReservation,
    'Could not mark the reservation as a no-show',
  );

export const useWithdrawReservation = () =>
  useReservationStatusAction(
    reservationApi.withdrawReservation,
    'Could not withdraw the reservation',
  );

export function useCheckInReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      arrivalTime,
      notes,
    }: {
      id: string;
      arrivalTime?: string | null;
      notes?: string | null;
    }) => reservationApi.checkInReservation(id, arrivalTime, notes),
    onSuccess: () => invalidateReservations(queryClient),
    onError: () => void message.error('Could not check the reservation in'),
  });
}
