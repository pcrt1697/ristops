import { useState } from 'react';
import { Alert, Button, Empty, Flex, Segmented, Select, Space, Spin, Switch, theme, Tooltip, Typography, } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useSearchParamFilters } from '../../commons/hooks.ts';
import { useSearchReservations } from '../../domain/reservation/reservation.hooks.ts';
import { serviceForReservation, statusLabel, } from '../../domain/reservation/reservation.utils.ts';
import {
  type ReservationCalendarQuery,
  ReservationStatus,
  type SearchReservationsQuery,
} from '../../services/graphql/graphql.ts';
import ReservationFormModal from './ReservationFormModal.tsx';
import ReservationTable from './ReservationTable.tsx';

const { Text, Title } = Typography;

type CalendarDay = ReservationCalendarQuery['reservationCalendar'][number];
type ServiceSummary = CalendarDay['services'][number];
type Reservation = SearchReservationsQuery['reservations']['items'][number];

// The backend caps a page at 100 (`PaginationParams.page_size`). The whole day is loaded in one
// request because the service filter runs client-side: a reservation has no service reference,
// so the backend cannot filter by it.
const PAGE_SIZE = 100;

const ALL_SERVICES = 'all';

interface ReservationDaySectionProps {
  venueId: string;
  /** Selected business date, `YYYY-MM-DD`. */
  date: string;
  /** The calendar's entry for that date; absent when nothing is scheduled. */
  day?: CalendarDay;
  canBook: boolean;
}

/** One service's occupancy, from the calendar summary rather than the loaded rows. */
function ServiceCapacity({ service }: { service: ServiceSummary }) {
  const { token } = theme.useToken();
  const fill =
    service.capacity > 0
      ? Math.min(1, service.peakBooked / service.capacity)
      : 0;
  const color = service.overCapacity ? token.colorError : token.colorPrimary;

  return (
    <div style={{ minWidth: 200 }}>
      <Flex justify="space-between" gap={12}>
        <Text style={{ fontSize: 13 }}>
          {service.serviceName}{' '}
          <Text type="secondary" style={{ fontSize: 12 }}>
            {dayjs(service.opensAt).format('HH:mm')}–
            {dayjs(service.closesAt).format('HH:mm')}
          </Text>
        </Text>
        <Text
          style={{
            fontSize: 13,
            color: service.overCapacity ? color : undefined,
          }}
        >
          {service.peakBooked}/{service.capacity} seats
        </Text>
      </Flex>
      <div
        style={{
          height: 4,
          marginTop: 4,
          borderRadius: 2,
          background: token.colorFillSecondary,
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${fill * 100}%`,
            borderRadius: 2,
            background: color,
          }}
        />
      </div>
    </div>
  );
}

/**
 * The selected day's bookings: one time-ordered table across every service, with the service
 * shown per row and selectable through the segmented control above it.
 *
 * The search spans two days because an overnight service closes after midnight; rows that fall
 * in none of the day's service windows are dropped by `serviceForReservation`.
 */
export default function ReservationDaySection({
  venueId,
  date,
  day,
  canBook,
}: ReservationDaySectionProps) {
  const { token } = theme.useToken();
  const filters = useSearchParamFilters();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Reservation>();
  const [selectedService, setSelectedService] = useState<string>(ALL_SERVICES);

  // Services differ from day to day, so a selection made on one day may name a service that
  // does not run on the next. Reset it when the day changes, following the same
  // derived-state-on-render idiom as ServiceScheduleOverrides' month paging.
  const [serviceDate, setServiceDate] = useState(date);
  if (serviceDate !== date) {
    setServiceDate(date);
    setSelectedService(ALL_SERVICES);
  }

  const statusFilter = filters.get('status');
  const violationsOnly = filters.get('violations') === '1';

  const { data, isLoading } = useSearchReservations({
    filter: {
      venueId,
      dateFrom: date,
      dateTo: dayjs(date).add(1, 'day').format('YYYY-MM-DD'),
      status: statusFilter ? [statusFilter as ReservationStatus] : undefined,
      violationsOnly,
    },
    pagination: { page: 0, pageSize: PAGE_SIZE },
    sort: [],
  });

  const isPast = dayjs(date).isBefore(dayjs(), 'day');
  const services = day?.services ?? [];
  const items = data?.items ?? [];
  const truncated = (data?.total ?? 0) > items.length;

  // Resolve each booking's service once, dropping any that no longer fits a window.
  const rows = items
    .map((reservation) => ({
      reservation,
      service: serviceForReservation(reservation.reservationDate, services),
    }))
    .filter(
      (row) =>
        row.service !== undefined &&
        (selectedService === ALL_SERVICES ||
          row.service.serviceId === selectedService),
    )
    .sort((a, b) =>
      a.reservation.reservationDate.localeCompare(
        b.reservation.reservationDate,
      ),
    );

  const shownServices =
    selectedService === ALL_SERVICES
      ? services
      : services.filter((service) => service.serviceId === selectedService);

  function openCreate() {
    setEditing(undefined);
    setFormOpen(true);
  }

  function openEdit(reservation: Reservation) {
    setEditing(reservation);
    setFormOpen(true);
  }

  return (
    <Flex vertical gap={12}>
      <Flex justify="space-between" align="center" wrap gap={12}>
        <Title level={5} style={{ margin: 0 }}>
          {dayjs(date).format('dddd D MMMM YYYY')}
        </Title>
        {canBook && (
          <Tooltip
            title={
              isPast
                ? 'A booking can only be made from now onwards.'
                : undefined
            }
          >
            <Button
              type="primary"
              icon={<PlusOutlined />}
              disabled={isPast}
              onClick={openCreate}
            >
              New reservation
            </Button>
          </Tooltip>
        )}
      </Flex>

      {day?.closed && (
        <Alert
          type="info"
          showIcon
          message="The venue is closed on this date."
        />
      )}

      {services.length === 0 && !day?.closed ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No service is scheduled on this date."
          style={{ marginTop: 24 }}
        />
      ) : (
        <>
          <Flex justify="space-between" align="center" wrap gap={12}>
            {services.length > 1 && (
              <Segmented
                value={selectedService}
                onChange={setSelectedService}
                options={[
                  { value: ALL_SERVICES, label: 'All' },
                  ...services.map((service) => ({
                    value: service.serviceId,
                    label: service.serviceName,
                  })),
                ]}
              />
            )}
            <Space wrap>
              <Select
                allowClear
                placeholder="Any status"
                style={{ width: 150 }}
                value={statusFilter || undefined}
                onChange={(value) => filters.setFilter('status')(value ?? '')}
                options={Object.values(ReservationStatus).map((status) => ({
                  value: status,
                  label: statusLabel(status),
                }))}
              />
              <Tooltip title="Show only bookings that no longer fit the current schedule — the venue is now closed that day, no service is open at that time any more, or the booking no longer fits within the opening hours. Editing the schedule never cancels a booking, so these are flagged for staff to resolve.">
                <Space size={4}>
                  <Switch
                    size="small"
                    checked={violationsOnly}
                    onChange={(checked) =>
                      filters.setFilter('violations')(checked ? '1' : '')
                    }
                  />
                  <Text type="secondary" style={{ cursor: 'help' }}>
                    Needs attention
                  </Text>
                </Space>
              </Tooltip>
            </Space>
          </Flex>

          {/* Its own band, so the summary reads as belonging to the table below rather than
              trailing off the segmented control above it. */}
          <div
            style={{
              padding: '12px 16px',
              background: token.colorFillQuaternary,
              borderRadius: token.borderRadiusLG,
            }}
          >
            <Flex wrap gap={32}>
              {shownServices.map((service) => (
                <ServiceCapacity key={service.serviceId} service={service} />
              ))}
            </Flex>
          </div>

          {truncated && (
            <Alert
              type="warning"
              showIcon
              message={`Showing the first ${items.length} of ${data?.total} bookings for this day.`}
            />
          )}

          <Spin spinning={isLoading}>
            {rows.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No bookings match the current filters."
              />
            ) : (
              <ReservationTable
                venueId={venueId}
                rows={rows}
                showService={
                  selectedService === ALL_SERVICES && services.length > 1
                }
                canEdit={canBook}
                onEdit={openEdit}
              />
            )}
          </Spin>
        </>
      )}

      <ReservationFormModal
        venueId={venueId}
        reservation={editing}
        defaultDate={date}
        open={formOpen}
        onClose={() => setFormOpen(false)}
      />
    </Flex>
  );
}
