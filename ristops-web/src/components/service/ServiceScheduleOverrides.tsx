import { useState } from 'react';
import {
  Button,
  DatePicker,
  Empty,
  Flex,
  Modal,
  Space,
  Spin,
  Tag,
  theme,
  Tooltip,
  Typography,
} from 'antd';
import {
  DeleteOutlined,
  DownOutlined,
  EditOutlined,
  ExclamationCircleFilled,
  LeftOutlined,
  PlusOutlined,
  RightOutlined,
  UpOutlined,
} from '@ant-design/icons';
import dayjs, { type Dayjs } from 'dayjs';
import {
  useDeleteCapacityOverride,
  useDeleteServiceClosing,
  useDeleteOpeningOverride,
  useServiceCapacityOverrides,
  useServiceClosings,
  useServiceOpeningOverrides,
  useVenueClosings,
} from '../../domain/schedule/schedule.hooks.ts';
import {
  formatCapacityDelta,
  formatDateRange,
  formatTimeRange,
  WEEKDAY_BY_DAY_INDEX,
  weekdayLabel,
} from '../../domain/schedule/schedule.utils.ts';
import type {
  ListServiceOpeningsQuery,
  SearchCapacityOverridesQuery,
  SearchServiceClosingsQuery,
  SearchOpeningOverridesQuery,
  SearchVenueClosingsQuery,
  Weekday,
} from '../../services/graphql/graphql.ts';
import OverrideFormModal from './OverrideFormModal.tsx';
import ServiceClosingFormModal from './ServiceClosingFormModal.tsx';
import CapacityFormModal from './CapacityFormModal.tsx';
import ServiceExceptionsDrawer from './ServiceExceptionsDrawer.tsx';

const { Text } = Typography;

type Opening = ListServiceOpeningsQuery['serviceOpenings'][number];
type Override =
  SearchOpeningOverridesQuery['serviceOpeningOverrides']['items'][number];
type ServiceClosing =
  SearchServiceClosingsQuery['serviceClosings']['items'][number];
type CapacityOverride =
  SearchCapacityOverridesQuery['serviceCapacityOverrides']['items'][number];
type VenueClosing = SearchVenueClosingsQuery['venueClosings']['items'][number];

const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const EXCEPTIONS_PER_PAGE = 8;

/**
 * Resolve which exception applies to a given day. An item matches when the day falls in its
 * inclusive date range (ISO strings compare lexicographically) and its weekday is either unset
 * (every day) or equal to the day's weekday. A weekday-specific match wins over a blanket one.
 */
function matchForDay<
  T extends { dateStart: string; dateEnd: string; weekday?: Weekday | null },
>(items: T[], dayIso: string, dayWeekday: Weekday): T | undefined {
  const inRange = (item: T) => item.dateStart <= dayIso && dayIso <= item.dateEnd;
  return (
    items.find((item) => inRange(item) && item.weekday === dayWeekday) ??
    items.find((item) => inRange(item) && item.weekday == null)
  );
}

interface ServiceScheduleOverridesProps {
  venueId: string;
  serviceId: string;
  openings: Opening[];
  canEdit: boolean;
}

export default function ServiceScheduleOverrides({
  venueId,
  serviceId,
  openings,
  canEdit,
}: ServiceScheduleOverridesProps) {
  const { token } = theme.useToken();
  const [month, setMonth] = useState<Dayjs>(dayjs().startOf('month'));

  const dateFrom = month.startOf('month').format('YYYY-MM-DD');
  const dateTo = month.endOf('month').format('YYYY-MM-DD');

  const { data: overridesData, isLoading: loadingOverrides } =
    useServiceOpeningOverrides(serviceId, dateFrom, dateTo);
  const { data: closingsData, isLoading: loadingClosings } = useServiceClosings(
    serviceId,
    dateFrom,
    dateTo,
  );
  const { data: capacityData, isLoading: loadingCapacity } =
    useServiceCapacityOverrides(serviceId, dateFrom, dateTo);
  const { data: venueClosingsData, isLoading: loadingVenueClosings } =
    useVenueClosings(venueId, dateFrom, dateTo);
  const overrides = overridesData ?? [];
  const closings = closingsData ?? [];
  const capacityOverrides = capacityData ?? [];
  const venueClosings = venueClosingsData ?? [];

  const openingByWeekday = new Map<Weekday, Opening>(
    openings.map((o) => [o.weekday, o]),
  );

  const [overrideOpen, setOverrideOpen] = useState(false);
  const [editingOverride, setEditingOverride] = useState<Override>();
  const [closingOpen, setClosingOpen] = useState(false);
  const [editingClosing, setEditingClosing] = useState<ServiceClosing>();
  const [capacityOpen, setCapacityOpen] = useState(false);
  const [editingCapacity, setEditingCapacity] = useState<CapacityOverride>();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const deleteOverride = useDeleteOpeningOverride(serviceId);
  const deleteClosing = useDeleteServiceClosing(serviceId);
  const deleteCapacity = useDeleteCapacityOverride(serviceId);

  const openAddOverride = () => {
    setEditingOverride(undefined);
    setOverrideOpen(true);
  };
  const openEditOverride = (o: Override) => {
    setEditingOverride(o);
    setOverrideOpen(true);
  };
  const openAddClosing = () => {
    setEditingClosing(undefined);
    setClosingOpen(true);
  };
  const openEditClosing = (c: ServiceClosing) => {
    setEditingClosing(c);
    setClosingOpen(true);
  };
  const openAddCapacity = () => {
    setEditingCapacity(undefined);
    setCapacityOpen(true);
  };
  const openEditCapacity = (c: CapacityOverride) => {
    setEditingCapacity(c);
    setCapacityOpen(true);
  };

  const confirmDeleteOverride = (o: Override) =>
    Modal.confirm({
      title: 'Delete override',
      icon: <ExclamationCircleFilled />,
      content: `Delete this override (${formatDateRange(o.dateStart, o.dateEnd)})?`,
      okText: 'Delete',
      okButtonProps: { danger: true },
      onOk: () => deleteOverride.mutateAsync(o.id),
    });
  const confirmDeleteClosing = (c: ServiceClosing) =>
    Modal.confirm({
      title: 'Delete closing',
      icon: <ExclamationCircleFilled />,
      content: `Delete this closing (${formatDateRange(c.dateStart, c.dateEnd)})?`,
      okText: 'Delete',
      okButtonProps: { danger: true },
      onOk: () => deleteClosing.mutateAsync(c.id),
    });
  const confirmDeleteCapacity = (c: CapacityOverride) =>
    Modal.confirm({
      title: 'Delete capacity change',
      icon: <ExclamationCircleFilled />,
      content: `Delete this capacity change (${formatDateRange(c.dateStart, c.dateEnd)})?`,
      okText: 'Delete',
      okButtonProps: { danger: true },
      onOk: () => deleteCapacity.mutateAsync(c.id),
    });

  // --- Build the Monday-first month grid ---
  const monthStart = month.startOf('month');
  const monthEnd = month.endOf('month');
  const gridStart = monthStart.subtract((monthStart.day() + 6) % 7, 'day');
  const gridEnd = monthEnd.add(6 - ((monthEnd.day() + 6) % 7), 'day');
  const days: Dayjs[] = [];
  for (let d = gridStart; !d.isAfter(gridEnd, 'day'); d = d.add(1, 'day')) {
    days.push(d);
  }

  function dayCell(day: Dayjs) {
    const dStr = day.format('YYYY-MM-DD');
    const inMonth = day.isSame(month, 'month');
    const dow = WEEKDAY_BY_DAY_INDEX[day.day()];
    const venueClosing = matchForDay(venueClosings, dStr, dow);
    const closing = matchForDay(closings, dStr, dow);
    const override = matchForDay(overrides, dStr, dow);
    const capacity = matchForDay(capacityOverrides, dStr, dow);
    const base = openingByWeekday.get(dow);

    let label = '—';
    let color: string | undefined = token.colorTextSecondary;
    let background: string | undefined;
    if (venueClosing) {
      // A venue-wide closing shuts every service; it wins over service-level config.
      label = 'Venue closed';
      color = token.colorError;
      background = token.colorErrorBg;
    } else if (closing) {
      label = 'Closed';
      color = token.colorError;
      background = token.colorErrorBg;
    } else if (override) {
      label = formatTimeRange(override.startTime, override.endTime);
      color = token.colorWarning;
      background = token.colorWarningBg;
    } else if (base) {
      label = formatTimeRange(base.startTime, base.endTime);
      color = token.colorText;
    }

    return (
      <div
        key={dStr}
        style={{
          border: `1px solid ${token.colorBorderSecondary}`,
          minHeight: 76,
          padding: 8,
          background,
          opacity: day.isSame(month, 'month') ? 1 : 0.4,
        }}
      >
        <Text strong={inMonth} type={inMonth ? undefined : 'secondary'}>
          {day.date()}
        </Text>
        <div style={{ marginTop: 4, fontSize: 13, color }}>{label}</div>
        {/* Capacity is a seat-count adjustment, shown only on affected open days. */}
        {capacity && !closing && !venueClosing && (
          <div style={{ fontSize: 12, color: token.colorInfo }}>
            {formatCapacityDelta(capacity.capacityDelta)} seats
          </div>
        )}
      </div>
    );
  }

  const exceptions: (
    | { kind: 'override'; item: Override }
    | { kind: 'closing'; item: ServiceClosing }
    | { kind: 'capacity'; item: CapacityOverride }
    | { kind: 'venueClosing'; item: VenueClosing }
  )[] = [
    ...overrides.map((item) => ({ kind: 'override' as const, item })),
    ...closings.map((item) => ({ kind: 'closing' as const, item })),
    ...capacityOverrides.map((item) => ({ kind: 'capacity' as const, item })),
    ...venueClosings.map((item) => ({ kind: 'venueClosing' as const, item })),
  ].sort((a, b) => a.item.dateStart.localeCompare(b.item.dateStart));

  // Client-side paging of the (fully-loaded) month exceptions. Reset to the first page when
  // the month changes; clamp so shrinking the list never strands you on an empty page.
  const [exceptionsPage, setExceptionsPage] = useState(0);
  const [pagedMonth, setPagedMonth] = useState(month);
  if (!pagedMonth.isSame(month, 'month')) {
    setPagedMonth(month);
    setExceptionsPage(0);
  }
  const pageCount = Math.ceil(exceptions.length / EXCEPTIONS_PER_PAGE);
  const currentPage = Math.min(exceptionsPage, Math.max(0, pageCount - 1));
  const pagedExceptions = exceptions.slice(
    currentPage * EXCEPTIONS_PER_PAGE,
    (currentPage + 1) * EXCEPTIONS_PER_PAGE,
  );

  return (
    <>
      <Flex justify="space-between" align="center" wrap gap={12}>
        <Space>
          <Tooltip title="Previous month">
            <Button
              icon={<LeftOutlined />}
              onClick={() => setMonth(month.subtract(1, 'month'))}
            />
          </Tooltip>
          <DatePicker
            picker="month"
            value={month}
            onChange={(m) => m && setMonth(m.startOf('month'))}
            allowClear={false}
            format="MMMM YYYY"
          />
          <Tooltip title="Next month">
            <Button
              icon={<RightOutlined />}
              onClick={() => setMonth(month.add(1, 'month'))}
            />
          </Tooltip>
        </Space>
        <Space wrap>
          <Button onClick={() => setDrawerOpen(true)}>View all</Button>
          {canEdit && (
            <>
              <Button icon={<PlusOutlined />} onClick={openAddOverride}>
                Add override
              </Button>
              <Button icon={<PlusOutlined />} onClick={openAddClosing}>
                Add closing
              </Button>
              <Button icon={<PlusOutlined />} onClick={openAddCapacity}>
                Add capacity change
              </Button>
            </>
          )}
        </Space>
      </Flex>

      <Space size="large" style={{ margin: '12px 0' }}>
        <LegendSwatch color={token.colorFillSecondary} label="Base hours" />
        <LegendSwatch color={token.colorWarning} label="Override" />
        <LegendSwatch color={token.colorError} label="Closing" />
        <LegendSwatch color={token.colorInfo} label="Capacity" />
      </Space>

      <Spin
        spinning={
          loadingOverrides ||
          loadingClosings ||
          loadingCapacity ||
          loadingVenueClosings
        }
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(7, 1fr)',
            marginBottom: 4,
          }}
        >
          {WEEKDAY_LABELS.map((label) => (
            <Text key={label} type="secondary" style={{ padding: '4px 8px' }}>
              {label}
            </Text>
          ))}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)' }}>
          {days.map(dayCell)}
        </div>
      </Spin>

      <Flex
        align="center"
        justify="space-between"
        gap={8}
        style={{ marginTop: 32 }}
      >
        <Text strong>Exceptions in {month.format('MMMM')}</Text>
        {pageCount > 1 && (
          <Flex align="center" gap={8}>
            <Text type="secondary">
              {currentPage * EXCEPTIONS_PER_PAGE + 1}–
              {Math.min((currentPage + 1) * EXCEPTIONS_PER_PAGE, exceptions.length)}{' '}
              of {exceptions.length}
            </Text>
            <Button
              type="text"
              size="small"
              icon={<UpOutlined />}
              disabled={currentPage === 0}
              onClick={() => setExceptionsPage(currentPage - 1)}
            />
            <Button
              type="text"
              size="small"
              icon={<DownOutlined />}
              disabled={currentPage >= pageCount - 1}
              onClick={() => setExceptionsPage(currentPage + 1)}
            />
          </Flex>
        )}
      </Flex>
      {exceptions.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No overrides, closings, or capacity changes this month."
          style={{ marginTop: 16 }}
        />
      ) : (
        <div style={{ marginTop: 8 }}>
          {pagedExceptions.map((ex) => {
            const { item } = ex;
            const meta = [
              item.weekday ? `Every ${weekdayLabel(item.weekday)}` : null,
              formatDateRange(item.dateStart, item.dateEnd),
              ex.kind === 'override'
                ? `${formatTimeRange(ex.item.startTime, ex.item.endTime)} · ${ex.item.capacity} seats`
                : null,
              ex.kind === 'capacity'
                ? `${formatCapacityDelta(ex.item.capacityDelta)} seats`
                : null,
            ]
              .filter(Boolean)
              .join(' · ');
            const dotColor =
              ex.kind === 'closing' || ex.kind === 'venueClosing'
                ? token.colorError
                : ex.kind === 'capacity'
                  ? token.colorInfo
                  : token.colorWarning;
            const title =
              item.description ??
              (ex.kind === 'closing'
                ? 'Closing'
                : ex.kind === 'capacity'
                  ? 'Capacity change'
                  : ex.kind === 'venueClosing'
                    ? 'Venue closure'
                    : 'Override');
            return (
              <Flex
                key={`${ex.kind}:${item.id}`}
                align="center"
                justify="space-between"
                gap={12}
                style={{
                  padding: '10px 0',
                  borderTop: `1px solid ${token.colorBorderSecondary}`,
                }}
              >
                <Flex align="center" gap={10} style={{ minWidth: 0 }}>
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: '50%',
                      flexShrink: 0,
                      background: dotColor,
                    }}
                  />
                  <Text strong>{title}</Text>
                  {ex.kind === 'venueClosing' && (
                    <Tooltip title="Managed in venue settings">
                      <Tag color="default">Venue</Tag>
                    </Tooltip>
                  )}
                  <Text type="secondary">{meta}</Text>
                </Flex>
                {canEdit && ex.kind !== 'venueClosing' && (
                  <Space>
                    <Tooltip title="Edit">
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() =>
                          ex.kind === 'override'
                            ? openEditOverride(ex.item)
                            : ex.kind === 'closing'
                              ? openEditClosing(ex.item)
                              : openEditCapacity(ex.item)
                        }
                      />
                    </Tooltip>
                    <Tooltip title="Delete">
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() =>
                          ex.kind === 'override'
                            ? confirmDeleteOverride(ex.item)
                            : ex.kind === 'closing'
                              ? confirmDeleteClosing(ex.item)
                              : confirmDeleteCapacity(ex.item)
                        }
                      />
                    </Tooltip>
                  </Space>
                )}
              </Flex>
            );
          })}
        </div>
      )}

      <OverrideFormModal
        serviceId={serviceId}
        override={editingOverride}
        open={overrideOpen}
        onClose={() => setOverrideOpen(false)}
      />
      <ServiceClosingFormModal
        serviceId={serviceId}
        closing={editingClosing}
        open={closingOpen}
        onClose={() => setClosingOpen(false)}
      />
      <CapacityFormModal
        serviceId={serviceId}
        capacityOverride={editingCapacity}
        open={capacityOpen}
        onClose={() => setCapacityOpen(false)}
      />
      <ServiceExceptionsDrawer
        serviceId={serviceId}
        canEdit={canEdit}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </>
  );
}

function LegendSwatch({ color, label }: { color: string; label: string }) {
  return (
    <Flex align="center" gap={6}>
      <span
        style={{
          width: 12,
          height: 12,
          borderRadius: 3,
          background: color,
          display: 'inline-block',
        }}
      />
      <Text type="secondary">{label}</Text>
    </Flex>
  );
}
