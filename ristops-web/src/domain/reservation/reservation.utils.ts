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

/** Why a booking no longer fits its service's schedule, phrased for staff. */
export const VIOLATION_LABEL: Record<ReservationViolation, string> = {
  [ReservationViolation.NoService]: 'The service no longer runs on this date',
  [ReservationViolation.Closed]: 'The service is now closed on this date',
  [ReservationViolation.OutsideHours]: 'Outside the service opening hours',
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
