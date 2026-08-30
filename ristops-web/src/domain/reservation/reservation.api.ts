import { gqlRequest } from '../../services/graphql/client.ts';
import {
  type CreateReservationInput,
  type ReservationSearchInput,
  type UpdateReservationInput,
  CancelReservationDocument,
  CheckInReservationDocument,
  ConfirmReservationDocument,
  CreateReservationDocument,
  GetReservationDocument,
  NoShowReservationDocument,
  RejectReservationDocument,
  ReservationAvailabilityDocument,
  ReservationCalendarDocument,
  ReservationOverCapacityDocument,
  SearchReservationsDocument,
  UpdateReservationDocument,
  WithdrawReservationDocument,
} from '../../services/graphql/graphql.ts';

export const reservationApi = {
  getReservation: (id: string) =>
    gqlRequest(GetReservationDocument, { id }).then((r) => r.reservation),
  searchReservations: (input: ReservationSearchInput) =>
    gqlRequest(SearchReservationsDocument, { input }).then((r) => r.reservations),
  reservationOverCapacity: (venueId: string) =>
    gqlRequest(ReservationOverCapacityDocument, { venueId }).then(
      (r) => r.reservationOverCapacity,
    ),
  reservationCalendar: (venueId: string, dateFrom: string, dateTo: string) =>
    gqlRequest(ReservationCalendarDocument, { venueId, dateFrom, dateTo }).then(
      (r) => r.reservationCalendar,
    ),
  reservationAvailability: (
    venueId: string,
    businessDate: string,
    partySize: number,
    excludeReservationId?: string | null,
  ) =>
    gqlRequest(ReservationAvailabilityDocument, {
      venueId,
      businessDate,
      partySize,
      excludeReservationId,
    }).then((r) => r.reservationAvailability),

  createReservation: (input: CreateReservationInput) =>
    gqlRequest(CreateReservationDocument, { input }).then((r) => r.createReservation),
  updateReservation: (id: string, input: UpdateReservationInput) =>
    gqlRequest(UpdateReservationDocument, { id, input }).then((r) => r.updateReservation),

  confirmReservation: (id: string, notes?: string | null) =>
    gqlRequest(ConfirmReservationDocument, { id, notes }).then((r) => r.confirmReservation),
  rejectReservation: (id: string, notes?: string | null) =>
    gqlRequest(RejectReservationDocument, { id, notes }).then((r) => r.rejectReservation),
  cancelReservation: (id: string, notes?: string | null) =>
    gqlRequest(CancelReservationDocument, { id, notes }).then((r) => r.cancelReservation),
  checkInReservation: (id: string, arrivalTime?: string | null, notes?: string | null) =>
    gqlRequest(CheckInReservationDocument, { id, arrivalTime, notes }).then(
      (r) => r.checkInReservation,
    ),
  noShowReservation: (id: string, notes?: string | null) =>
    gqlRequest(NoShowReservationDocument, { id, notes }).then((r) => r.noShowReservation),
  withdrawReservation: (id: string, notes?: string | null) =>
    gqlRequest(WithdrawReservationDocument, { id, notes }).then((r) => r.withdrawReservation),
};
