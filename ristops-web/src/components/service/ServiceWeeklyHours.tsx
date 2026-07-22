import { useMemo, useState } from 'react';
import {
  Button,
  Flex,
  Input,
  InputNumber,
  Space,
  Switch,
  Table,
  TimePicker,
  Typography,
} from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import {
  type ListServiceOpeningsQuery,
  type OpeningUpsertInput,
  Weekday,
} from '../../services/graphql/graphql.ts';
import { useUpsertServiceOpenings } from '../../domain/schedule/schedule.hooks.ts';

const { Text } = Typography;

const TIME_FORMAT = 'HH:mm';

const WEEKDAYS: { key: Weekday; label: string }[] = [
  { key: Weekday.Monday, label: 'Monday' },
  { key: Weekday.Tuesday, label: 'Tuesday' },
  { key: Weekday.Wednesday, label: 'Wednesday' },
  { key: Weekday.Thursday, label: 'Thursday' },
  { key: Weekday.Friday, label: 'Friday' },
  { key: Weekday.Saturday, label: 'Saturday' },
  { key: Weekday.Sunday, label: 'Sunday' },
];

type Opening = ListServiceOpeningsQuery['serviceOpenings'][number];

interface DayState {
  open: boolean;
  start: Dayjs | null;
  end: Dayjs | null;
  capacity: number | null;
  notes: string;
}

type WeekState = Record<Weekday, DayState>;

const EMPTY_DAY: DayState = {
  open: false,
  start: null,
  end: null,
  capacity: null,
  notes: '',
};

// Parse a "HH:mm:ss" wire value without relying on the dayjs customParseFormat
// plugin: split and set the fields on a base day (the date part is irrelevant).
function parseTime(value: string): Dayjs {
  const [h, m, s] = value.split(':').map(Number);
  return dayjs().hour(h).minute(m).second(s ?? 0).millisecond(0);
}

function buildState(openings: Opening[]): WeekState {
  const state = {} as WeekState;
  for (const { key } of WEEKDAYS) state[key] = { ...EMPTY_DAY };
  for (const opening of openings) {
    state[opening.weekday] = {
      open: true,
      start: parseTime(opening.startTime),
      end: parseTime(opening.endTime),
      capacity: opening.capacity,
      notes: opening.description ?? '',
    };
  }
  return state;
}

function serialize(state: WeekState): string {
  return WEEKDAYS.map(({ key }) => {
    const d = state[key];
    return [
      key,
      d.open,
      d.start?.format(TIME_FORMAT) ?? '',
      d.end?.format(TIME_FORMAT) ?? '',
      d.capacity ?? '',
      d.notes,
    ].join('|');
  }).join(';');
}

interface ServiceWeeklyHoursProps {
  serviceId: string;
  openings: Opening[];
  canEdit: boolean;
}

export default function ServiceWeeklyHours({
  serviceId,
  openings,
  canEdit,
}: ServiceWeeklyHoursProps) {
  const baseline = useMemo(() => buildState(openings), [openings]);
  const [state, setState] = useState<WeekState>(baseline);
  const upsert = useUpsertServiceOpenings(serviceId);

  // Re-sync the editable copy whenever the persisted openings change (initial
  // load or after a successful save refetch), discarding any stale local edits.
  // Adjusting state during render (rather than in an effect) avoids a cascading
  // re-render — the React-recommended pattern for "reset state on prop change".
  const [syncedFrom, setSyncedFrom] = useState(openings);
  if (openings !== syncedFrom) {
    setSyncedFrom(openings);
    setState(baseline);
  }

  const patchDay = (key: Weekday, patch: Partial<DayState>) =>
    setState((prev) => ({ ...prev, [key]: { ...prev[key], ...patch } }));

  const dirty = serialize(state) !== serialize(baseline);
  // Every open day needs a full time range and a capacity before it can be saved.
  const valid = WEEKDAYS.every(({ key }) => {
    const d = state[key];
    return !d.open || (d.start && d.end && d.capacity);
  });

  const handleSave = () => {
    const payload: OpeningUpsertInput[] = WEEKDAYS.filter(
      ({ key }) => state[key].open,
    ).map(({ key }) => {
      const d = state[key];
      return {
        weekday: key,
        capacity: d.capacity as number,
        startTime: (d.start as Dayjs).format('HH:mm:ss'),
        endTime: (d.end as Dayjs).format('HH:mm:ss'),
        description: d.notes || null,
      };
    });
    upsert.mutate(payload);
  };

  return (
    <>
      <Table<{ key: Weekday; label: string }>
        rowKey="key"
        dataSource={WEEKDAYS}
        pagination={false}
        columns={[
          {
            title: 'Open',
            width: 80,
            render: (_, { key }) => (
              <Switch
                checked={state[key].open}
                disabled={!canEdit}
                onChange={(open) => patchDay(key, { open })}
              />
            ),
          },
          {
            title: 'Day',
            width: 140,
            render: (_, { key, label }) => (
              <Text type={state[key].open ? undefined : 'secondary'}>
                {label}
              </Text>
            ),
          },
          {
            title: 'Hours',
            render: (_, { key }) => {
              const d = state[key];
              return (
                <Space>
                  <TimePicker
                    value={d.start}
                    format={TIME_FORMAT}
                    minuteStep={5}
                    disabled={!canEdit || !d.open}
                    allowClear={false}
                    needConfirm={false}
                    onChange={(start) => patchDay(key, { start })}
                  />
                  <Text type="secondary">–</Text>
                  <TimePicker
                    value={d.end}
                    format={TIME_FORMAT}
                    minuteStep={5}
                    disabled={!canEdit || !d.open}
                    allowClear={false}
                    needConfirm={false}
                    onChange={(end) => patchDay(key, { end })}
                  />
                </Space>
              );
            },
          },
          {
            title: 'Capacity',
            width: 120,
            render: (_, { key }) => {
              const d = state[key];
              return (
                <InputNumber
                  value={d.capacity}
                  min={1}
                  disabled={!canEdit || !d.open}
                  style={{ width: '100%' }}
                  onChange={(capacity) => patchDay(key, { capacity })}
                />
              );
            },
          },
          {
            title: 'Notes',
            render: (_, { key }) => {
              const d = state[key];
              return (
                <Input
                  value={d.notes}
                  disabled={!canEdit || !d.open}
                  onChange={(e) => patchDay(key, { notes: e.target.value })}
                />
              );
            },
          },
        ]}
      />

      {canEdit && (
        <Flex justify="space-between" align="center" style={{ marginTop: 16 }}>
          <Text type="secondary">{dirty ? 'Unsaved changes' : ''}</Text>
          <Space>
            <Button disabled={!dirty} onClick={() => setState(baseline)}>
              Discard
            </Button>
            <Button
              type="primary"
              loading={upsert.isPending}
              disabled={!dirty || !valid}
              onClick={handleSave}
            >
              Save hours
            </Button>
          </Space>
        </Flex>
      )}
    </>
  );
}
