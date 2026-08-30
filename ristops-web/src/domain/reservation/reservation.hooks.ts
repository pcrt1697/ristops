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

/** Invalidate every reservation-derived query (detail, lists, over-capacity) after a mutation. */
function invalidateReservations(queryClient: QueryClient) {
  void queryClient.invalidateQueries({ queryKey: ['reservation'] });
  void queryClient.invalidateQueries({ queryKey: ['reservations'] });
  void queryClient.invalidateQueries({ queryKey: ['reservations.overCapacity'] });
  void queryClient.invalidateQueries({ queryKey: ['reservations.calendar'] });
  void queryClient.invalidateQueries({ queryKey: ['reservations.availability'] });
}

export function useReservation(id: string) {
  return useQuery({
    queryKey: ['reservation', id],
    queryFn: () => reservationApi.getReservation(id),
    enabled: !!id,
  });
}

export function useSearchReservations(input: ReservationSearchInput) {
  return useQuery({
    queryKey: ['reservations', input],
    queryFn: () => reservationApi.searchReservations(input),
    enabled: !!input.filter.venueId,
  });
}

export function useReservationOverCapacity(venueId: string) {
  return useQuery({
    queryKey: ['reservations.overCapacity', venueId],
    queryFn: () => reservationApi.reservationOverCapacity(venueId),
    enabled: !!venueId,
  });
}

/** Per-day, per-service occupancy over a window — the month grid. */
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

/**
 * Slots a party could be booked into on a date. Disabled until a date and party size are
 * entered, so the booking form doesn't query while the user is still filling it in.
 */
export function useReservationAvailability(
  venueId: string,
  businessDate: string | undefined,
  partySize: number | undefined,
  excludeReservationId?: string | null,
) {
  return useQuery({
    queryKey: [
      'reservations.availability',
      venueId,
      businessDate,
      partySize,
      excludeReservationId,
    ],
    queryFn: () =>
      reservationApi.reservationAvailability(
        venueId,
        businessDate!,
        partySize!,
        excludeReservationId,
      ),
    enabled: !!venueId && !!businessDate && !!partySize,
  });
}

export function useCreateReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateReservationInput) => reservationApi.createReservation(input),
    onSuccess: () => invalidateReservations(queryClient),
    onError: () => void message.error('Could not create the reservation'),
  });
}

export function useUpdateReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UpdateReservationInput }) =>
      reservationApi.updateReservation(id, input),
    onSuccess: () => invalidateReservations(queryClient),
    onError: () => void message.error('Could not update the reservation'),
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
