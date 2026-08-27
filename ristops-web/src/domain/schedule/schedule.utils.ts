import dayjs, { type Dayjs } from 'dayjs';
import { ConflictSource, Weekday } from '../../services/graphql/graphql.ts';

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

export interface WeeklyOpeningCandidate {
  weekday: Weekday;
  start: Dayjs;
  end: Dayjs;
}

/**
 * Mirrors the backend's same-service overnight self-overlap validator
 * (`OpeningsUpsertRequest._validate_no_overnight_self_overlap`): the whole week is edited as one
 * set, so if an overnight opening (`end <= start`) spills past midnight into the next weekday's
 * own opening, this returns a message describing the clash; otherwise `null`. Client-side mirror
 * only — override self-overlap needs the service's existing DB schedule and has no live preview,
 * surfaced instead via the backend's 422 on submit.
 */
export function findOvernightSelfOverlap(
  candidates: WeeklyOpeningCandidate[],
): string | null {
  const byWeekday = new Map(candidates.map((c) => [c.weekday, c]));
  for (const candidate of candidates) {
    const startMin = candidate.start.hour() * 60 + candidate.start.minute();
    const endMin = candidate.end.hour() * 60 + candidate.end.minute();
    if (endMin > startMin || endMin === 0) continue; // same-day, or ends exactly at midnight
    const index = WEEKDAY_ORDER.indexOf(candidate.weekday);
    const nextWeekday = WEEKDAY_ORDER[(index + 1) % WEEKDAY_ORDER.length];
    const next = byWeekday.get(nextWeekday);
    if (!next) continue;
    const nextStartMin = next.start.hour() * 60 + next.start.minute();
    if (nextStartMin < endMin) {
      return `${weekdayLabel(candidate.weekday)}'s overnight hours overlap ${weekdayLabel(nextWeekday)}'s opening`;
    }
  }
  return null;
}

/** Human label for the kind of exception a conflicting row belongs to. */
export function conflictSourceLabel(source: ConflictSource): string {
  switch (source) {
    case ConflictSource.VenueClosing:
      return 'venue closure';
    case ConflictSource.ServiceClosing:
      return 'closing';
    case ConflictSource.OpeningOverride:
      return 'opening override';
    case ConflictSource.CapacityOverride:
      return 'capacity change';
    case ConflictSource.ServiceOpening:
      return 'another service';
  }
}
