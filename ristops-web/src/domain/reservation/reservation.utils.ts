import dayjs from 'dayjs';
import {
  ReservationStatus,
  ReservationViolation,
} from '../../services/graphql/graphql.ts';

/** Human label for a reservation status, e.g. `CHECKED_IN` → "Checked in". */
export function statusLabel(status: ReservationStatus): string {
  const lower = status.toLowerCase().replace(/_/g, ' ');
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** antd Tag colour per status: live bookings are informative, resolved ones muted or negative. */
export const STATUS_COLOR: Record<ReservationStatus, string> = {
  [ReservationStatus.Pending]: 'gold',
  [ReservationStatus.Confirmed]: 'blue',
  [ReservationStatus.CheckedIn]: 'green',
  [ReservationStatus.Rejected]: 'red',
  [ReservationStatus.Canceled]: 'default',
  [ReservationStatus.NoShow]: 'volcano',
  [ReservationStatus.Withdrawn]: 'purple',
};

/** Why a booking no longer fits the schedule, phrased for staff. */
export const VIOLATION_LABEL: Record<ReservationViolation, string> = {
  [ReservationViolation.NoService]: 'No service is open at this time anymore',
  [ReservationViolation.Closed]: 'The venue is now closed on this date',
  [ReservationViolation.OutsideHours]: 'No longer fits within the opening hours',
};

/**
 * Statuses whose details can still be changed. An edit re-runs the availability check, so it
 * only makes sense while the booking is still ahead of the party's arrival — moving the time
 * of an already-seated or resolved booking would be rejected anyway.
 */
export const EDITABLE_STATUSES: ReservationStatus[] = [
  ReservationStatus.Pending,
  ReservationStatus.Confirmed,
];

interface ServiceWindow {
  serviceId: string;
  serviceName: string;
  opensAt: string;
  closesAt: string;
}

/**
 * The service window a booking falls in, or undefined when it matches none.
 *
 * A reservation carries no service reference — the service is derived from venue + datetime —
 * so this matches the booking's local wall-clock against `[opensAt, closesAt)`. An overnight
 * service closes on the following calendar day, which is why callers search a two-day span;
 * a booking matching no window belongs to a service that has since changed, and is dropped
 * rather than shown under an arbitrary one.
 */
export function serviceForReservation<S extends ServiceWindow>(
  reservationDate: string,
  services: S[],
): S | undefined {
  const at = dayjs(reservationDate);
  return services.find(
    (service) =>
      !at.isBefore(dayjs(service.opensAt)) && at.isBefore(dayjs(service.closesAt)),
  );
}
