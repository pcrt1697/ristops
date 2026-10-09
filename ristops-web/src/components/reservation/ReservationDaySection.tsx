import { useState } from 'react';
import { Alert, Button, Empty, Flex, Segmented, Select, Space, Spin, Switch, theme, Tooltip, Typography, } from 'antd';
import { ExclamationCircleFilled, PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useSearchParamFilters } from '../../commons/hooks.ts';
import { useSearchReservations } from '../../domain/reservation/reservation.hooks.ts';
import { statusLabel } from '../../domain/reservation/reservation.utils.ts';
import {
  type ReservationCalendarQuery,
  ReservationStatus,
  type SearchReservationsQuery,
} from '../../services/graphql/graphql.ts';
import ReservationFormModal from './ReservationFormModal.tsx';
import ReservationTable from './ReservationTable.tsx';
import ServiceCapacity, { UnavailableServiceNotice } from './ServiceCapacity.tsx';

const { Text, Title } = Typography;

type CalendarDay = ReservationCalendarQuery['reservationCalendar'][number];
type Reservation = SearchReservationsQuery['reservations']['items'][number];

// The backend caps a page at 100 (`PaginationParams.page_size`). A day rarely holds more, and
// the warning below says so when it does.
const PAGE_SIZE = 100;

interface ReservationDaySectionProps {
  venueId: string;
  /** Selected business date, `YYYY-MM-DD`. */
  date: string;
  /** The calendar's entry for that date; absent when nothing is scheduled. */
  day?: CalendarDay;
  canBook: boolean;
}

/**
 * The selected day's bookings, one service at a time: the segmented control picks the service,
 * and the table and capacity band below follow it. A service that no longer runs that day, being
 * closed or deleted, but which still holds bookings, stays selectable and is marked, so those
 * bookings can be reached.
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
  const [selectedService, setSelectedService] = useState<string>();

  const runningServices = [...(day?.services ?? [])].sort((a, b) =>
    a.opensAt.localeCompare(b.opensAt),
  );
  const closedServices = day?.closedServices ?? [];
  const deletedServices = day?.deletedServices ?? [];
  const serviceIds = [
    ...runningServices.map((service) => service.serviceId),
    ...closedServices.map((service) => service.serviceId),
    ...deletedServices.map((service) => service.serviceId),
  ];
  // A selection made on another day may name a service that is not offered on this one, in which
  // case the first service stands in for it. The choice is kept as the user moves between days.
  const activeServiceId =
    selectedService && serviceIds.includes(selectedService)
      ? selectedService
      : serviceIds[0];
  const activeRunning = runningServices.find(
    (service) => service.serviceId === activeServiceId,
  );
  const activeClosed = closedServices.find(
    (service) => service.serviceId === activeServiceId,
  );
  const activeDeleted = deletedServices.find(
    (service) => service.serviceId === activeServiceId,
  );

  const statusFilter = filters.get('status');
  const violationsOnly = filters.get('violations') === '1';

  const { data, isLoading } = useSearchReservations(
    {
      filter: {
        venueId,
        serviceId: activeServiceId,
        dateFrom: date,
        dateTo: date,
        status: statusFilter ? [statusFilter as ReservationStatus] : undefined,
        violationsOnly,
      },
      pagination: { page: 0, pageSize: PAGE_SIZE },
      sort: [],
    },
    activeServiceId !== undefined,
  );

  const isPast = dayjs(date).isBefore(dayjs(), 'day');
  const items = data?.items ?? [];
  const truncated = (data?.total ?? 0) > items.length;
  const reservations = [...items].sort((a, b) =>
    a.reservationDate.localeCompare(b.reservationDate),
  );

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
          message="Every service is closed on this date."
        />
      )}

      {serviceIds.length === 0 ? (
        !day?.closed && (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No service is scheduled on this date."
            style={{ marginTop: 24 }}
          />
        )
      ) : (
        <>
          <Flex justify="space-between" align="center" wrap gap={12}>
            {serviceIds.length > 1 && (
              <Segmented
                value={activeServiceId}
                onChange={(value) => setSelectedService(String(value))}
                options={[
                  ...runningServices.map((service) => ({
                    value: service.serviceId,
                    label: service.serviceName,
                  })),
                  ...closedServices.map((service) => ({
                    value: service.serviceId,
                    label: (
                      <Space size={4}>
                        <ExclamationCircleFilled style={{ color: token.colorWarning }} />
                        {service.serviceName}
                      </Space>
                    ),
                  })),
                  ...deletedServices.map((service) => ({
                    value: service.serviceId,
                    label: (
                      <Space size={4}>
                        <ExclamationCircleFilled style={{ color: token.colorError }} />
                        <Text delete>{service.serviceName}</Text>
                      </Space>
                    ),
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
              <Tooltip title="Show only bookings that no longer fit the current schedule — their service is now closed that date, no longer runs it, or no longer opens at that time. Editing the schedule never cancels a booking, so these are flagged for staff to resolve.">
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
            {activeRunning && <ServiceCapacity service={activeRunning} />}
            {activeClosed && (
              <UnavailableServiceNotice service={activeClosed} reason="closed" />
            )}
            {activeDeleted && (
              <UnavailableServiceNotice service={activeDeleted} reason="deleted" />
            )}
          </div>

          {truncated && (
            <Alert
              type="warning"
              showIcon
              message={`Showing the first ${items.length} of ${data?.total} bookings for this day.`}
            />
          )}

          <Spin spinning={isLoading}>
            {reservations.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="No bookings match the current filters."
              />
            ) : (
              <ReservationTable
                venueId={venueId}
                reservations={reservations}
                serviceUnavailable={activeClosed !== undefined || activeDeleted !== undefined}
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
