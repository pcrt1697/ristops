import { Alert, Button, Typography } from 'antd';
import {
  conflictSourceLabel,
  formatDateRange,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import type { ScheduleConflict } from '../../services/graphql/graphql.ts';

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
              {conflictSourceLabel(conflict.source)} on{' '}
              {formatDateRange(
                conflict.conflictingDateStart,
                conflict.conflictingDateEnd,
              )}
              {conflict.conflictingWeekday
                ? ` (${weekdayLabel(conflict.conflictingWeekday)}s)`
                : ''}
            </li>
          ))}
        </ul>
      }
      style={{ marginBottom: 16 }}
    />
  );
}
