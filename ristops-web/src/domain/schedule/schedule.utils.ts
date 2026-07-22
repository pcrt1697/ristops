import dayjs, { type Dayjs } from 'dayjs';
import { Weekday } from '../../services/graphql/graphql.ts';

/**
 * Parse a "HH:mm:ss" wire value into a Dayjs without the customParseFormat
 * plugin: split and set the fields on a base day (the date part is irrelevant).
 */
export function parseTime(value: string): Dayjs {
  const [h, m, s] = value.split(':').map(Number);
  return dayjs().hour(h).minute(m).second(s ?? 0).millisecond(0);
}

/** Weekday enum indexed by `dayjs().day()` (0 = Sunday … 6 = Saturday). */
export const WEEKDAY_BY_DAY_INDEX: Weekday[] = [
  Weekday.Sunday,
  Weekday.Monday,
  Weekday.Tuesday,
  Weekday.Wednesday,
  Weekday.Thursday,
  Weekday.Friday,
  Weekday.Saturday,
];

/** Weekdays in Monday-first order, for selectors. */
export const WEEKDAY_ORDER: Weekday[] = [
  Weekday.Monday,
  Weekday.Tuesday,
  Weekday.Wednesday,
  Weekday.Thursday,
  Weekday.Friday,
  Weekday.Saturday,
  Weekday.Sunday,
];

/** Human label for a weekday enum value, e.g. `MONDAY` → "Monday". */
export function weekdayLabel(weekday: Weekday): string {
  const lower = weekday.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

/**
 * Normalize a bulk-create weekday selection: empty means every day (`undefined`, so the field
 * is omitted from the request), and selecting all seven collapses to the same "every day"
 * behavior rather than sending a redundant full list. Mirrors the backend's normalization
 * (`normalize_weekdays`) so the payload already reflects what the server would produce.
 */
export function normalizeWeekdays(selected: Weekday[]): Weekday[] | undefined {
  if (selected.length === 0) return undefined;
  const unique = new Set(selected);
  if (unique.size === WEEKDAY_ORDER.length) return undefined;
  return WEEKDAY_ORDER.filter((weekday) => unique.has(weekday));
}

/** Format a "HH:mm:ss" range as "HH:mm–HH:mm". */
export function formatTimeRange(start: string, end: string): string {
  return `${parseTime(start).format('HH:mm')}–${parseTime(end).format('HH:mm')}`;
}

/** Format a signed seat delta, e.g. `30` → "+30", `-10` → "−10". */
export function formatCapacityDelta(delta: number): string {
  return delta >= 0 ? `+${delta}` : `−${Math.abs(delta)}`;
}

/** Format an inclusive ISO date range compactly, e.g. "Aug 10 – 12", "Aug 30 – Sep 1". */
export function formatDateRange(start: string, end: string): string {
  const s = dayjs(start);
  const e = dayjs(end);
  if (s.isSame(e, 'day')) return s.format('MMM D');
  if (s.isSame(e, 'month')) return `${s.format('MMM D')} – ${e.format('D')}`;
  return `${s.format('MMM D')} – ${e.format('MMM D')}`;
}
