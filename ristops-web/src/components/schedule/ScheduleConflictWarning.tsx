import { Alert, Button, Typography } from 'antd';
import {
  conflictSourceLabel,
  formatDateRange,
  formatTimeRange,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import {
  ConflictSource,
  type ScheduleConflict,
} from '../../services/graphql/graphql.ts';

interface ScheduleConflictWarningProps {
  conflicts: ScheduleConflict[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}

/**
 * Inline preview of conflicts for the period+weekdays currently entered in a schedule form.
 * Shown in the opening-override, closing, capacity-override, and venue-closing modals so the
 * user learns about a clash before submitting, not only from the backend's 409 on save.
 */
export default function ScheduleConflictWarning({
  conflicts,
  isLoading,
  isError,
  onRetry,
}: ScheduleConflictWarningProps) {
  if (isError) {
    return (
      <Alert
        type="warning"
        showIcon
        message="Couldn't check for conflicts"
        action={
          <Button size="small" onClick={onRetry}>
            Retry
          </Button>
        }
        style={{ marginBottom: 16 }}
      />
    );
  }

  if (isLoading) {
    return (
      <Typography.Text
        type="secondary"
        style={{ display: 'block', marginBottom: 16 }}
      >
        Checking for conflicts…
      </Typography.Text>
    );
  }

  if (!conflicts || conflicts.length === 0) return null;

  return (
    <Alert
      type="error"
      showIcon
      message="This conflicts with an existing schedule entry"
      description={
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          {conflicts.map((conflict) => (
            <li
              key={`${conflict.source}-${conflict.conflictingId}-${conflict.weekday ?? 'all'}`}
            >
              {conflict.source === ConflictSource.ServiceOpening
                ? renderServiceOpening(conflict)
                : renderException(conflict)}
            </li>
          ))}
        </ul>
      }
      style={{ marginBottom: 16 }}
    />
  );
}

/** A same-service exception conflict: "<kind> on <date range> (<weekday>s)". */
function renderException(conflict: ScheduleConflict) {
  return (
    <>
      {conflictSourceLabel(conflict.source)} on{' '}
      {formatDateRange(
        conflict.conflictingDateStart ?? '',
        conflict.conflictingDateEnd ?? '',
      )}
      {conflict.conflictingWeekday
        ? ` (${weekdayLabel(conflict.conflictingWeekday)}s)`
        : ''}
    </>
  );
}

/** A cross-service opening overlap: "<service> is open <HH:mm–HH:mm> on <weekday>s". */
function renderServiceOpening(conflict: ScheduleConflict) {
  const service = conflict.conflictingServiceName ?? 'another service';
  const window =
    conflict.conflictingStartTime && conflict.conflictingEndTime
      ? ` (${formatTimeRange(conflict.conflictingStartTime, conflict.conflictingEndTime)})`
      : '';
  const on = conflict.conflictingWeekday
    ? ` on ${weekdayLabel(conflict.conflictingWeekday)}s`
    : '';
  return (
    <>
      {service} is open{window}
      {on}
    </>
  );
}
