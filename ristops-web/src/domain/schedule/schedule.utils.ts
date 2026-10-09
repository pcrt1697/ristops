import dayjs from 'dayjs';
import { Weekday } from '../../services/graphql/graphql.ts';

/**
 * Parse an `HH:mm` / `HH:mm:ss` wire time into a dayjs on today's date. dayjs is loaded without
 * `customParseFormat`, so a bare time string cannot be parsed directly.
 */
export function parseTime(value: string): dayjs.Dayjs {
  const [hour, minute] = value.split(':');
  return dayjs().hour(Number(hour)).minute(Number(minute)).second(0);
}

/** Weekdays in display order, Monday first — matching the backend's enum order. */
export const WEEKDAY_ORDER: Weekday[] = [
  Weekday.Monday,
  Weekday.Tuesday,
  Weekday.Wednesday,
  Weekday.Thursday,
  Weekday.Friday,
  Weekday.Saturday,
  Weekday.Sunday,
];

/** The `Weekday` a dayjs date falls on (dayjs counts Sunday as 0). */
export const WEEKDAY_BY_DAY_INDEX: Record<number, Weekday> = {
  0: Weekday.Sunday,
  1: Weekday.Monday,
  2: Weekday.Tuesday,
  3: Weekday.Wednesday,
  4: Weekday.Thursday,
  5: Weekday.Friday,
  6: Weekday.Saturday,
};

/** Human label for a weekday, e.g. `MONDAY` → "Monday". */
export function weekdayLabel(weekday: Weekday): string {
  const lower = weekday.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/** Format an opening as "19:00 – 01:00", marking a window that closes the next day. */
export function formatTimeRange(startTime: string, endTime: string): string {
  const start = startTime.slice(0, 5);
  const end = endTime.slice(0, 5);
  const overnight = end <= start;
  return `${start} – ${end}${overnight ? ' (next day)' : ''}`;
}

/** Format a closing period as a single date, or "from – to" when it spans several days. */
export function formatDateRange(dateFrom: string, dateTo: string): string {
  const from = dayjs(dateFrom).format('D MMM YYYY');
  if (dateFrom === dateTo) {
    return from;
  }
  return `${from} – ${dayjs(dateTo).format('D MMM YYYY')}`;
}

/** Format a service's validity period, leaving an open-ended one without a closing date. */
export function formatValidity(dateFrom: string, dateTo?: string | null): string {
  const from = dayjs(dateFrom).format('D MMM YYYY');
  if (!dateTo) {
    return `From ${from}`;
  }
  if (dateFrom === dateTo) {
    return `${from} only`;
  }
  return `${from} – ${dayjs(dateTo).format('D MMM YYYY')}`;
}
